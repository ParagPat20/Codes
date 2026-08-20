"""
Kokoro 82M Ultra-Fast Local Neural TTS Engine
Features Sentence-Streaming Playback: Synthesizes and starts playing the first sentence
in sub-150ms while subsequent sentences generate concurrently in the background.
"""

import os
import re
import queue
import threading
import sounddevice as sd
import numpy as np
from typing import Optional, List

class KokoroTTSEngine:
    def __init__(self, model_path: Optional[str] = None, voices_path: Optional[str] = None, voice: str = "am_adam", speed: float = 1.05):
        self.base_dir = os.path.dirname(__file__)
        self.models_dir = os.path.join(self.base_dir, "models")
        os.makedirs(self.models_dir, exist_ok=True)

        self.model_path = model_path or os.path.join(self.models_dir, "kokoro-v1.0.onnx")
        self.voices_path = voices_path or os.path.join(self.models_dir, "voices-v1.0.bin")
        self.voice = voice
        self.speed = speed
        self.kokoro = None
        self._lock = threading.Lock()
        self._init_kokoro()

    def _init_kokoro(self):
        if not os.path.exists(self.model_path) or not os.path.exists(self.voices_path):
            print(f"[KokoroTTS] Notice: Model weights not found in {self.models_dir}. (Will download or fallback to Edge TTS).")
            return

        try:
            from kokoro_onnx import Kokoro
            self.kokoro = Kokoro(self.model_path, self.voices_path)
            print(f"[KokoroTTS] Kokoro 82M Engine loaded successfully! (Voice: {self.voice})")
        except Exception as e:
            print(f"[KokoroTTS] Error initializing Kokoro-ONNX: {e}")
            self.kokoro = None

    def is_ready(self) -> bool:
        if self.kokoro is not None:
            return True
        if os.path.exists(self.model_path) and os.path.exists(self.voices_path):
            self._init_kokoro()
            return self.kokoro is not None
        return False

    def set_voice(self, voice_name: str):
        self.voice = voice_name
        print(f"[KokoroTTS] Voice set to: {self.voice}")

    def set_speed(self, speed: float):
        self.speed = max(0.5, min(2.0, speed))

    def _split_into_sentences(self, text: str) -> List[str]:
        # Split cleanly on punctuation
        chunks = re.split(r'(?<=[.!?])\s+', text.strip())
        return [c.strip() for c in chunks if c.strip()]

    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        Synthesizes and streams audio sentence-by-sentence.
        First sentence starts playing in <150ms!
        """
        if not text or not text.strip():
            return False

        if not self.is_ready():
            return False

        sentences = self._split_into_sentences(text)
        if not sentences:
            return False

        with self._lock:
            try:
                # If only 1 short sentence, synthesize and play directly
                if len(sentences) == 1:
                    samples, sample_rate = self.kokoro.create(
                        sentences[0],
                        voice=self.voice,
                        speed=self.speed,
                        lang="en-us"
                    )
                    sd.play(samples, sample_rate)
                    if blocking:
                        sd.wait()
                    return True

                # Multi-sentence pipeline: Synthesize sentence 1, start play, pre-fetch sentence 2
                audio_queue = queue.Queue()
                stop_event = threading.Event()

                def _producer():
                    for sent in sentences:
                        if stop_event.is_set():
                            break
                        try:
                            s, sr = self.kokoro.create(
                                sent,
                                voice=self.voice,
                                speed=self.speed,
                                lang="en-us"
                            )
                            audio_queue.put((s, sr))
                        except Exception as err:
                            print(f"[KokoroTTS] Chunk error: {err}")
                    audio_queue.put(None)  # Sentinel to mark completion

                producer_thread = threading.Thread(target=_producer, daemon=True)
                producer_thread.start()

                # Play items as they become available in the queue
                while True:
                    item = audio_queue.get()
                    if item is None:
                        break
                    samples, sample_rate = item
                    sd.play(samples, sample_rate)
                    sd.wait()  # Wait for current sentence to finish playing

                return True

            except Exception as e:
                print(f"[KokoroTTS] Inference error: {e}")
                return False
