"""
Rollopod Voice AI Brain & Expo Controller
Coordinates Microphone STT, Preknown Facts, Flutter Operator Override via Firebase, Gemini Flash, and Child TTS.
"""

import os
import sys
import time
import argparse
from typing import Optional

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from knowledge_base import RollopodKnowledgeBase
from tts_engine import RollopodTTSEngine
from gemini_engine import RollopodGeminiEngine
from firebase_sync import RollopodFirebaseSync

class RollopodBrain:
    def __init__(self, 
                 firebase_url: Optional[str] = None,
                 gemini_api_key: Optional[str] = None,
                 voice_profile: str = "iron_crush",
                 operator_timeout: float = 3.5):
        print("=" * 60)
        print("[ROLLOPOD] INITIALIZING HEAVY ROBOT BRAIN (TECH EXPO EDITION)")
        print("=" * 60)

        # 1. Knowledge Base
        self.kb = RollopodKnowledgeBase()
        print(f"[OK] Loaded Knowledge Base ({len(self.kb.faqs)} curated FAQs + docs indexed).")

        # 2. Heavy Robot Voice TTS
        self.tts = RollopodTTSEngine(profile_name=voice_profile)
        print(f"[OK] Initialized Heavy Robot Voice Engine (Profile: {voice_profile} / {self.tts.voice}).")

        # 3. Gemini Flash
        system_instruction = self.kb.get_system_prompt_context()
        self.gemini = RollopodGeminiEngine(api_key=gemini_api_key, system_instruction=system_instruction)

        # 4. Firebase Sync (Lightweight zero-burden edition)
        self.firebase = RollopodFirebaseSync(database_url=firebase_url)
        self.operator_timeout = operator_timeout
        self.operational_mode = "ai"  # Default: Pure AI Mode (0s wait for human)

        # Start direct-speak, voice-change, pitch-change, and mode-change listener
        self.firebase.start_background_listener(
            on_direct_speak=self._handle_direct_speak,
            on_voice_change=self._handle_voice_change,
            on_pitch_change=self._handle_pitch_change,
            on_mode_change=self._handle_mode_change
        )
        print("[OK] Rollopod Brain ready for interactions! (Mode: Instant AI)\n")

    def _handle_mode_change(self, new_mode: str):
        mode_clean = new_mode.lower().strip()
        if mode_clean in ["ai", "manual", "hybrid"]:
            self.operational_mode = mode_clean
            print(f"[Brain] Operational Mode set to: {self.operational_mode.upper()}")

    def _handle_voice_change(self, profile_name: str):
        self.tts.set_profile(profile_name)

    def _handle_pitch_change(self, pitch_str: str):
        self.tts.set_pitch(pitch_str)

    def _handle_direct_speak(self, text: str):
        """Called when operator triggers soundboard or direct speech from Flutter app."""
        self.tts.speak(text, blocking=True)

    def process_query(self, question: str):
        """
        Mode-Aware Decision Pipeline:
        - Mode 'ai' (Default): Preknown facts OR Instant Gemini Flash AI (0.0s wait for human).
        - Mode 'manual': Waits for human typing from Flutter operator app.
        - Mode 'hybrid': Checks human override while concurrently fetching Gemini.
        """
        question = question.strip()
        if not question:
            return

        start_t = time.time()
        print(f"\n[Visitor]: \"{question}\"")
        self.firebase.publish_question(question)

        # Step 1: Check Pre-known FAQ (Instant Match in all modes)
        fact_match = self.kb.find_preknown_fact(question)
        if fact_match:
            final_answer, conf = fact_match
            source = "preknown_fact"
            print(f"[Knowledge Base]: Instant Match ({conf:.2f}) in {(time.time() - start_t)*1000:.0f}ms")
        else:
            # Step 2: Handle according to active operational mode
            if self.operational_mode == "manual":
                # Manual / Wizard-of-Oz: Wait for operator
                print(f"[Manual Mode]: Waiting up to 6.0s for operator reply from app...")
                human_reply = self.firebase.wait_for_operator_reply(timeout_seconds=6.0)
                if human_reply:
                    print(f"[Operator Override]: \"{human_reply}\"")
                    final_answer = human_reply
                    source = "human"
                else:
                    print("[Manual Mode Timeout]: Falling back to Gemini Flash...")
                    final_answer = self.gemini.generate_response(question)
                    source = "gemini_flash"

            elif self.operational_mode == "ai":
                # Pure AI Mode: Zero human waiting (Instant response)
                print("[AI Mode]: Instant Gemini Flash AI (0s human wait)...")
                final_answer = self.gemini.generate_response(question)
                source = "gemini_flash"

            else:
                # Hybrid Mode: Concurrent execution
                import concurrent.futures
                print("[Hybrid Mode]: Concurrent Gemini Flash AI + Operator check...")
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    gemini_future = executor.submit(self.gemini.generate_response, question)
                    human_reply = self.firebase.wait_for_operator_reply(timeout_seconds=1.0)
                    if human_reply:
                        final_answer = human_reply
                        source = "human"
                    else:
                        try:
                            final_answer = gemini_future.result(timeout=4.0)
                            source = "gemini_flash"
                        except Exception:
                            final_answer = "I am Rollopod! Ask me about how I walk, roll, and transform!"
                            source = "fallback"

        # Update Firebase with final answer
        self.firebase.update_reply(final_answer, source)

        # Step 3: Fast Neural Voice TTS (Kokoro 82M / Edge Neural)
        total_latency = time.time() - start_t
        print(f"[Speaking in {total_latency:.2f}s]: \"{final_answer}\"")
        self.tts.speak(final_answer, blocking=True)

    def run_microphone_listener(self):
        """
        Adaptive Voice Activity Detection (VAD) Microphone Listener.
        Calibrates ambient room noise, uses RMS energy for robust speech detection,
        and cleanly cuts off 0.9s after user finishes speaking (preventing long hangs).
        """
        try:
            import sounddevice as sd
            import speech_recognition as sr
            import numpy as np
        except ImportError as err:
            print(f"[Brain] Microphone dependencies missing ({err}). Falling back to CLI mode.")
            self.run_cli_loop()
            return

        recognizer = sr.Recognizer()
        sample_rate = 16000
        chunk_duration = 0.2  # 200ms chunks for rapid response
        chunk_samples = int(chunk_duration * sample_rate)
        silence_timeout = 0.9  # 0.9s of pause finishes recording cleanly
        max_question_duration = 14.0  # max seconds allowed for a question

        print("\n" + "=" * 60)
        print("[MICROPHONE ACTIVE] Rollopod is listening! Speak into the mic...")
        print("Features: RMS Voice Detection | Snappy 0.9s Auto-Cutoff")
        print("Tip: Press Ctrl+C to switch or exit.")
        print("=" * 60 + "\n")

        # Step 1: Quick 0.6s Ambient Baseline Calibration
        print("[Calibrating ambient room noise...]")
        try:
            calib_record = sd.rec(int(0.6 * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
            sd.wait()
            ambient_rms = float(np.sqrt(np.mean(calib_record**2)))
        except Exception:
            ambient_rms = 0.01

        # Clamp thresholds to guaranteed human vocal range (0.022 - 0.045)
        # Prevents high startup noise or greetings from locking out the microphone
        speech_start_threshold = min(0.045, max(0.022, ambient_rms * 1.5))
        silence_threshold = max(0.012, speech_start_threshold * 0.60)
        print(f"[Noise Floor: {ambient_rms:.4f} | Trigger: {speech_start_threshold:.4f} | Silence: {silence_threshold:.4f}]")
        print("[Ready - listening for visitors!]")

        while True:
            try:
                # Don't listen while robot is speaking its own voice
                if getattr(self.tts, 'is_speaking', False):
                    time.sleep(0.1)
                    continue

                self.firebase.update_robot_status("listening")
                
                audio_buffer = []
                pre_roll_buffer = []
                is_speaking = False
                silence_chunks = 0
                max_silence_chunks = int(silence_timeout / chunk_duration)
                max_total_chunks = int(max_question_duration / chunk_duration)

                # Open microphone input stream
                with sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32') as stream:
                    while True:
                        if getattr(self.tts, 'is_speaking', False):
                            break

                        chunk, overflow = stream.read(chunk_samples)
                        rms = float(np.sqrt(np.mean(chunk**2)))

                        if not is_speaking:
                            # Keep last 2 chunks (400ms pre-roll) to capture first word smoothly
                            pre_roll_buffer.append(chunk)
                            if len(pre_roll_buffer) > 2:
                                pre_roll_buffer.pop(0)

                            # Trigger when RMS exceeds speech threshold
                            if rms >= speech_start_threshold:
                                is_speaking = True
                                audio_buffer.extend(pre_roll_buffer)
                                audio_buffer.append(chunk)
                                silence_chunks = 0
                                print(f"\n[Speech detected (Level: {rms:.3f})! Listening...]")
                                self.firebase.update_robot_status("listening")
                        else:
                            # Speech is in progress
                            audio_buffer.append(chunk)
                            if rms < silence_threshold:
                                silence_chunks += 1
                            else:
                                silence_chunks = 0  # Still speaking

                            # Stop cleanly when user pauses for 0.9s or reaches max length
                            if silence_chunks >= max_silence_chunks or len(audio_buffer) >= max_total_chunks:
                                break

                # If speech was captured, process it
                if is_speaking and len(audio_buffer) > 0:
                    total_audio = np.concatenate(audio_buffer, axis=0)
                    total_duration = len(total_audio) / sample_rate
                    print(f"[Speech ended. Processing {total_duration:.1f}s question...]")
                    self.firebase.update_robot_status("thinking")

                    # Convert to 16-bit PCM in-memory
                    pcm_int16 = (total_audio * 32767.0).clip(-32768, 32767).astype(np.int16)
                    audio_data = sr.AudioData(pcm_int16.tobytes(), sample_rate, 2)

                    try:
                        text = recognizer.recognize_google(audio_data)
                        if text and text.strip():
                            self.process_query(text)
                    except sr.UnknownValueError:
                        print("[Speech not clearly recognized, ready for next question...]")
                    except sr.RequestError as e:
                        print(f"[STT Error] Speech API error: {e}")
                    finally:
                        self.firebase.update_robot_status("idle")

            except KeyboardInterrupt:
                print("\n[Brain] Microphone stopped by operator.")
                break
            except Exception as e:
                print(f"[Brain] Microphone error: {e}")
                time.sleep(1)

    def run_cli_loop(self):
        """CLI text interaction loop for testing without microphone."""
        print("\n⌨️ [CLI Test Mode Active]")
        print("Type a question and press Enter. Type 'exit' to quit.\n")

        # Announce greeting
        self.tts.speak("Hello! I am Rollopod! Welcome to our Tech Expo booth!", blocking=False)

        while True:
            try:
                user_input = input("\nEnter Question for Rollopod: ")
                if user_input.lower().strip() in ["exit", "quit", "q"]:
                    break
                self.process_query(user_input)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Rollopod Voice AI Brain (Heavy Robot Edition)")
    parser.add_argument("--cli", action="store_true", help="Run in CLI test mode instead of microphone")
    parser.add_argument("--profile", type=str, default="iron_crush", help="Voice profile: iron_crush, mech_titan, cyber_sentinel, atlas_heavy, indo_titan")
    parser.add_argument("--firebase-url", type=str, default=None, help="Firebase Realtime Database URL")
    parser.add_argument("--gemini-key", type=str, default=None, help="Gemini API Key")
    parser.add_argument("--timeout", type=float, default=3.5, help="Operator reply wait timeout in seconds")
    args = parser.parse_args()

    # Load environment variables if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    brain = RollopodBrain(
        firebase_url=args.firebase_url or os.getenv("FIREBASE_DB_URL"),
        gemini_api_key=args.gemini_key or os.getenv("GEMINI_API_KEY"),
        voice_profile=args.profile or os.getenv("VOICE_PROFILE", "iron_crush"),
        operator_timeout=args.timeout
    )

    if args.cli:
        brain.run_cli_loop()
    else:
        # If pyaudio or microphone fails, graceful fallback to CLI
        try:
            brain.run_microphone_listener()
        except Exception as e:
            print(f"[Brain] Microphone failed ({e}). Falling back to CLI mode...")
            brain.run_cli_loop()

if __name__ == "__main__":
    main()
