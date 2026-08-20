"""
Rollopod High-Speed Neural Text-to-Speech Engine
Supports Kokoro 82M (<100ms ultra-low latency) and Microsoft Edge Neural TTS.
"""

import os
import asyncio
import tempfile
import threading
import subprocess
from typing import Optional

try:
    from voice_profiles import VOICE_PROFILES
except Exception:
    VOICE_PROFILES = {}

class RollopodTTSEngine:
    """
    High-quality Text-To-Speech engine using Kokoro 82M (Fastest) with Edge Neural TTS fallback.
    """
    def __init__(self, profile_name: str = "kokoro_adam", voice: Optional[str] = None, pitch: Optional[str] = None, rate: Optional[str] = None):
        profile = VOICE_PROFILES.get(profile_name, {})
        self.profile_name = profile_name
        self.voice = voice or profile.get("voice", "am_adam")
        self.pitch = pitch or profile.get("pitch", "-7Hz")
        self.rate = rate or profile.get("rate", "-2%")
        self.is_speaking = False
        self._lock = threading.Lock()

        # Kokoro 82M Fast Engine
        self.kokoro = None
        try:
            from kokoro_tts import KokoroTTSEngine
            self.kokoro = KokoroTTSEngine(voice=self.voice if profile.get("engine") == "kokoro" else "am_adam", speed=1.05)
        except Exception as e:
            print(f"[TTS] Kokoro optional notice: {e}")

    def set_profile(self, profile_name: str):
        if profile_name in VOICE_PROFILES:
            self.profile_name = profile_name
            prof = VOICE_PROFILES[profile_name]
            engine_type = prof.get("engine", "edge")
            
            if engine_type == "kokoro" and self.kokoro:
                self.kokoro.set_voice(prof["voice"])
                if "speed" in prof:
                    self.kokoro.set_speed(prof["speed"])
                print(f"[TTS] Switched voice profile to Kokoro 82M: {prof['name']}")
            else:
                self.voice = prof.get("voice", self.voice)
                self.pitch = prof.get("pitch", self.pitch)
                self.rate = prof.get("rate", self.rate)
                print(f"[TTS] Switched voice profile to Edge Neural: {prof['name']}")

    def set_pitch(self, pitch: str):
        self.pitch = pitch.strip()
        print(f"[TTS] Updated voice pitch to: {self.pitch}")

    async def _generate_edge_tts_audio(self, text: str, output_path: str):
        import edge_tts
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            pitch=self.pitch,
            rate=self.rate
        )
        await communicate.save(output_path)

    def _play_audio_file(self, audio_path: str):
        """Plays audio without external C-compiler dependencies."""
        # Method 1: Try playsound3
        try:
            from playsound3 import playsound
            playsound(audio_path, block=True)
            return
        except Exception:
            pass

        # Method 2: Native Windows MediaPlayer COM via PowerShell
        try:
            cmd = f'powershell -c "$player = New-Object -ComObject wmplayer.ocx; $player.URL = \'{audio_path}\'; $player.controls.play(); while ($player.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }}"'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        except Exception as e:
            print(f"[TTS] Native playback notice: {e}")

    def speak(self, text: str, blocking: bool = True):
        """Synthesizes text to speech using Kokoro 82M (if ready) or Edge Neural."""
        if not text or not text.strip():
            return

        clean_text = text.replace('"', '').strip()

        def _worker():
            with self._lock:
                self.is_speaking = True
                
                # 1. Try Kokoro 82M if profile is kokoro or default
                is_kokoro_profile = VOICE_PROFILES.get(self.profile_name, {}).get("engine", "kokoro") == "kokoro"
                if is_kokoro_profile and self.kokoro and self.kokoro.is_ready():
                    try:
                        print(f"[Kokoro 82M Voice] Speaking: \"{clean_text}\"")
                        ok = self.kokoro.speak(clean_text, blocking=True)
                        if ok:
                            self.is_speaking = False
                            return
                    except Exception as e:
                        print(f"[TTS] Kokoro fallback: {e}")

                # 2. Fallback to Edge Neural TTS
                temp_path = None
                try:
                    print(f"[Edge Neural Voice] Speaking: \"{clean_text}\"")
                    temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
                    temp_path = temp_file.name
                    temp_file.close()

                    asyncio.run(self._generate_edge_tts_audio(clean_text, temp_path))
                    self._play_audio_file(temp_path)
                except Exception as err:
                    print(f"[TTS] Error during voice synthesis: {err}")
                finally:
                    if temp_path and os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    self.is_speaking = False

        if blocking:
            _worker()
        else:
            t = threading.Thread(target=_worker, daemon=True)
            t.start()
