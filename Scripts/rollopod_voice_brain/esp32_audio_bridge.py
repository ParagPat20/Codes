"""
Rollopod ESP32-S3 Audio Bridge Server (runs on RPi5)
=====================================================
Receives mic audio from ESP32-S3 via UDP → feeds into existing RollopodBrain STT pipeline
Synthesizes TTS response → sends raw PCM audio back to ESP32-S3 speaker via UDP

Audio format: 16kHz, 16-bit signed mono PCM
Ports:
  :7778 — receive mic audio from ESP32-S3
  :7779 — send speaker audio to ESP32-S3

Usage:
    python esp32_audio_bridge.py

Or with custom RPi5 IP and brain options:
    python esp32_audio_bridge.py --profile iron_crush --cli-fallback
"""

import os
import sys
import time
import socket
import struct
import threading
import tempfile
import subprocess
import numpy as np

# Add brain script path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# CONFIG
# ============================================================
MIC_RX_PORT       = 7778      # Receive mic audio from ESP32-S3
SPK_TX_PORT       = 7779      # Send speaker audio to ESP32-S3
DISCOVERY_PORT    = 7777      # Broadcast ROLLOPOD_HELLO here so ESP32 finds us
DISCOVERY_MAGIC   = b"ROLLOPOD_HELLO"  # Must match ESP32 firmware
DISCOVERY_INTERVAL = 2.0     # seconds between beacon broadcasts
SAMPLE_RATE       = 16000     # Must match ESP32 firmware
CHUNK_SAMPLES     = 512       # Must match ESP32 firmware
CHUNK_BYTES       = CHUNK_SAMPLES * 2

# Voice Activity Detection
VAD_SILENCE_THRESHOLD = 300   # RMS below this = silence (0-32767 scale)
VAD_SPEECH_TRIGGER    = 800   # RMS above this = speech detected
VAD_SILENCE_CHUNKS    = 24    # ~24 × 32ms = ~0.75s silence to end utterance
VAD_MAX_CHUNKS        = 500   # ~500 × 32ms = ~16s max recording


class AudioBridge:
    def __init__(self, esp32_ip: str = None, voice_profile: str = "iron_crush",
                 gemini_api_key: str = None, firebase_url: str = None):
        self.esp32_ip = esp32_ip           # ESP32-S3's IP (discovered on first packet)
        self.voice_profile = voice_profile
        self._lock = threading.Lock()
        self._speaking = False

        # UDP sockets
        self.mic_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mic_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mic_sock.bind(("0.0.0.0", MIC_RX_PORT))
        self.mic_sock.settimeout(2.0)
        print(f"[BRIDGE] Listening for ESP32-S3 mic audio on UDP :{MIC_RX_PORT}")

        self.spk_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        print(f"[BRIDGE] Speaker audio → ESP32-S3 UDP :{SPK_TX_PORT}")

        # Beacon socket — broadcasts ROLLOPOD_HELLO so ESP32 can find us automatically
        self.beacon_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.beacon_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.beacon_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._beacon_running = True
        threading.Thread(target=self._beacon_loop, daemon=True).start()
        print(f"[BRIDGE] Broadcasting ROLLOPOD_HELLO beacon on :{DISCOVERY_PORT} every {DISCOVERY_INTERVAL}s")

        # Load RollopodBrain
        print("\n[BRIDGE] Loading Rollopod Brain...")
        try:
            from rollopod_brain import RollopodBrain
            # Monkey-patch the brain to use our speaker instead of local audio
            self.brain = RollopodBrain(
                firebase_url=firebase_url,
                gemini_api_key=gemini_api_key,
                voice_profile=voice_profile,
            )
            # Override the TTS speak method to route audio to ESP32 speaker
            self._patch_tts_for_esp32()
            print("[BRIDGE] Brain loaded and TTS patched for ESP32 speaker output!")
        except Exception as e:
            print(f"[BRIDGE] Brain load failed: {e}")
            print("[BRIDGE] Running in ECHO TEST mode (no AI, just echo back)")
            self.brain = None

    def _beacon_loop(self):
        """Broadcasts ROLLOPOD_HELLO every 2s so ESP32 auto-discovers this RPi5."""
        while self._beacon_running:
            try:
                self.beacon_sock.sendto(DISCOVERY_MAGIC, ("255.255.255.255", DISCOVERY_PORT))
            except Exception as e:
                print(f"[BEACON] Send error: {e}")
            time.sleep(DISCOVERY_INTERVAL)

    def _patch_tts_for_esp32(self):
        """Monkey-patch TTS so audio goes to ESP32 speaker instead of local soundcard."""
        bridge = self

        def esp32_speak(text: str, blocking: bool = True):
            """Generate TTS audio and stream it to the ESP32 speaker over UDP."""
            if not text or not text.strip():
                return
            print(f"[TTS→ESP32] Speaking: \"{text}\"")

            def _worker():
                bridge._speaking = True
                try:
                    audio_pcm = bridge._generate_tts_pcm(text)
                    if audio_pcm is not None and bridge.esp32_ip:
                        bridge._stream_audio_to_esp32(audio_pcm)
                    else:
                        print("[TTS→ESP32] No ESP32 IP known yet or TTS failed")
                except Exception as e:
                    print(f"[TTS→ESP32] Error: {e}")
                finally:
                    bridge._speaking = False

            if blocking:
                _worker()
            else:
                t = threading.Thread(target=_worker, daemon=True)
                t.start()

        # Patch the TTS engine's speak method
        self.brain.tts.speak = esp32_speak
        self.brain.tts.is_speaking = property(lambda self_: bridge._speaking)

    def _generate_tts_pcm(self, text: str) -> np.ndarray:
        """Generate TTS audio as 16kHz 16-bit PCM numpy array."""
        # Try Kokoro first
        try:
            tts = self.brain.tts
            if tts.kokoro and tts.kokoro.is_ready():
                import io, soundfile as sf
                audio_data = tts.kokoro.synthesize(text)
                if audio_data is not None:
                    # Resample to 16kHz if needed
                    return self._ensure_16khz(audio_data, tts.kokoro.sample_rate)
        except Exception:
            pass

        # Fallback to Edge TTS → temp MP3 → decode to PCM
        try:
            import asyncio, edge_tts
            tts = self.brain.tts

            async def _gen():
                communicate = edge_tts.Communicate(
                    text=text, voice=tts.voice, pitch=tts.pitch, rate=tts.rate)
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                    tmp = f.name
                await communicate.save(tmp)
                return tmp

            loop = asyncio.new_event_loop()
            tmp_mp3 = loop.run_until_complete(_gen())
            loop.close()

            # Decode MP3 to PCM using ffmpeg (available on RPi5)
            cmd = [
                "ffmpeg", "-y", "-i", tmp_mp3,
                "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", "1",
                "-loglevel", "quiet", "pipe:1"
            ]
            result = subprocess.run(cmd, capture_output=True)
            os.remove(tmp_mp3)

            if result.returncode == 0 and result.stdout:
                return np.frombuffer(result.stdout, dtype=np.int16)
        except Exception as e:
            print(f"[TTS PCM] Edge TTS decode failed: {e}")

        return None

    def _ensure_16khz(self, audio: np.ndarray, orig_rate: int) -> np.ndarray:
        """Resample audio to 16kHz if needed."""
        if orig_rate == SAMPLE_RATE:
            return audio.astype(np.int16) if audio.dtype != np.int16 else audio
        try:
            import scipy.signal as sig
            resampled = sig.resample_poly(audio, SAMPLE_RATE, orig_rate)
            return (resampled * 32767).clip(-32768, 32767).astype(np.int16)
        except Exception:
            # Simple decimation fallback
            factor = orig_rate // SAMPLE_RATE
            return audio[::factor].astype(np.int16)

    def _stream_audio_to_esp32(self, pcm: np.ndarray):
        """Stream PCM audio to ESP32-S3 speaker in chunks."""
        if self.esp32_ip is None:
            return

        total_bytes = len(pcm) * 2
        raw = pcm.tobytes()
        offset = 0
        chunks_sent = 0

        print(f"[SPK→ESP32] Streaming {total_bytes/1024:.1f}KB audio to {self.esp32_ip}:{SPK_TX_PORT}")
        while offset < len(raw):
            chunk = raw[offset:offset + CHUNK_BYTES]
            self.spk_sock.sendto(chunk, (self.esp32_ip, SPK_TX_PORT))
            offset += CHUNK_BYTES
            chunks_sent += 1
            # Pace to match 16kHz playback rate: each 1024-byte chunk = 32ms of audio
            time.sleep(0.028)  # slightly under 32ms to avoid buffer underrun

        print(f"[SPK→ESP32] Done — sent {chunks_sent} chunks ({total_bytes} bytes)")

    def _stt(self, audio_pcm: np.ndarray) -> str:
        """Speech-to-text using Google STT (same as existing brain)."""
        try:
            import speech_recognition as sr
            audio_bytes = audio_pcm.tobytes()
            audio_data = sr.AudioData(audio_bytes, SAMPLE_RATE, 2)
            r = sr.Recognizer()
            text = r.recognize_google(audio_data)
            return text
        except Exception as e:
            print(f"[STT] Error: {e}")
            return ""

    def run(self):
        """Main loop: receive mic audio, detect speech, process with brain, speak on ESP32."""
        print("\n" + "=" * 55)
        print("  Rollopod ESP32-S3 Audio Bridge — RUNNING")
        print(f"  Waiting for ESP32-S3 on UDP :{MIC_RX_PORT}...")
        print("=" * 55 + "\n")

        audio_buffer = []
        pre_roll = []
        is_recording = False
        silence_chunks = 0

        while True:
            try:
                # Receive mic audio chunk from ESP32-S3
                try:
                    data, addr = self.mic_sock.recvfrom(CHUNK_BYTES + 64)
                except socket.timeout:
                    continue

                # Learn the ESP32's IP from first packet
                if self.esp32_ip is None:
                    self.esp32_ip = addr[0]
                    print(f"[BRIDGE] ESP32-S3 connected from {self.esp32_ip}")

                # Skip while speaking (echo cancellation)
                if self._speaking:
                    continue

                # Parse PCM
                samples = len(data) // 2
                chunk = np.frombuffer(data[:samples * 2], dtype=np.int16)
                rms = int(np.sqrt(np.mean(chunk.astype(np.int32) ** 2)))

                if not is_recording:
                    # Pre-roll: keep last 2 chunks for clean word capture
                    pre_roll.append(chunk)
                    if len(pre_roll) > 2:
                        pre_roll.pop(0)

                    if rms >= VAD_SPEECH_TRIGGER:
                        is_recording = True
                        audio_buffer = list(pre_roll) + [chunk]
                        silence_chunks = 0
                        print(f"\n[MIC] Speech detected (RMS={rms}) — recording...")
                else:
                    audio_buffer.append(chunk)

                    if rms < VAD_SILENCE_THRESHOLD:
                        silence_chunks += 1
                    else:
                        silence_chunks = 0

                    if silence_chunks >= VAD_SILENCE_CHUNKS or len(audio_buffer) >= VAD_MAX_CHUNKS:
                        # End of utterance — process
                        duration = len(audio_buffer) * CHUNK_SAMPLES / SAMPLE_RATE
                        print(f"[MIC] Speech ended ({duration:.1f}s) — transcribing...")
                        is_recording = False
                        silence_chunks = 0

                        full_audio = np.concatenate(audio_buffer)
                        audio_buffer = []

                        # Process in background so we don't block mic
                        t = threading.Thread(
                            target=self._process_utterance,
                            args=(full_audio,), daemon=True)
                        t.start()

            except KeyboardInterrupt:
                print("\n[BRIDGE] Stopped.")
                break
            except Exception as e:
                print(f"[BRIDGE] Loop error: {e}")
                time.sleep(0.1)

    def _process_utterance(self, audio: np.ndarray):
        """STT → Brain → TTS → ESP32 speaker pipeline."""
        with self._lock:
            # 1. STT
            text = self._stt(audio)
            if not text or not text.strip():
                print("[STT] Unclear speech, ignoring")
                return

            print(f"\n[Visitor→ESP32]: \"{text}\"")

            # 2. Brain processes query (includes TTS which is patched to → ESP32)
            if self.brain:
                self.brain.process_query(text)
            else:
                # Echo test mode
                echo = f"I heard you say: {text}"
                pcm = self._simple_tts_fallback(echo)
                if pcm is not None and self.esp32_ip:
                    self._stream_audio_to_esp32(pcm)

    def _simple_tts_fallback(self, text: str) -> np.ndarray:
        """Minimal fallback TTS using system espeak (always available on RPi5)."""
        try:
            cmd = ["espeak", "-v", "en", "-s", "150", "--stdout", text]
            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                # espeak outputs WAV — skip 44-byte header, resample from 22050 to 16000
                raw = np.frombuffer(result.stdout[44:], dtype=np.int16)
                return self._ensure_16khz(raw, 22050)
        except Exception as e:
            print(f"[TTS FALLBACK] espeak error: {e}")
        return None


def main():
    import argparse
    from dotenv import load_dotenv
    load_dotenv()

    parser = argparse.ArgumentParser(description="Rollopod ESP32-S3 Audio Bridge (RPi5)")
    parser.add_argument("--profile", default="iron_crush",
                        help="TTS voice profile (default: iron_crush)")
    parser.add_argument("--gemini-key", default=None,
                        help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--firebase-url", default=None,
                        help="Firebase URL (or set FIREBASE_DB_URL env var)")
    args = parser.parse_args()

    print("=" * 55)
    print("  Rollopod ESP32-S3 Audio Bridge Server (RPi5)")
    print("=" * 55)
    print(f"  Mic RX port : {MIC_RX_PORT}")
    print(f"  Speaker TX  : {SPK_TX_PORT}")
    print(f"  Sample rate : {SAMPLE_RATE}Hz, 16-bit mono")
    print(f"  Voice       : {args.profile}")
    print()

    bridge = AudioBridge(
        voice_profile=args.profile,
        gemini_api_key=args.gemini_key or os.getenv("GEMINI_API_KEY"),
        firebase_url=args.firebase_url or os.getenv("FIREBASE_DB_URL"),
    )
    bridge.run()


if __name__ == "__main__":
    main()
