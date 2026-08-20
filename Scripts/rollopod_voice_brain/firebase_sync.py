"""
Rollopod Firebase Realtime Database Synchronizer (Ultra-Lightweight Edition)
Transfers only the current active question, reply, and settings.
No heavy history transfers across the network.
"""

import os
import json
import time
import threading
import requests
from typing import Optional, Callable, Dict, Any

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
except Exception:
    pass

class RollopodFirebaseSync:
    def __init__(self, database_url: Optional[str] = None):
        self.database_url = (database_url or os.getenv("FIREBASE_DB_URL", "")).rstrip("/")
        self.is_listening = False
        self._listener_thread = None
        self.current_q_timestamp = 0

    def publish_question(self, question: str):
        """Pushes only the active question to Firebase."""
        if not self.database_url:
            return

        self.current_q_timestamp = int(time.time() * 1000)
        data = {
            "q": question,
            "reply": "",
            "reply_source": "pending",
            "timestamp": self.current_q_timestamp
        }

        try:
            url = f"{self.database_url}/rollopod/interaction.json"
            requests.put(url, json=data, timeout=2)
        except Exception as e:
            print(f"[FirebaseSync] Notice: {e}")

    def update_reply(self, reply_text: str, reply_source: str):
        """Updates the active interaction with the final spoken reply."""
        if not self.database_url:
            return

        data = {
            "reply": reply_text,
            "reply_source": reply_source,
            "answered_at": int(time.time() * 1000)
        }

        try:
            url = f"{self.database_url}/rollopod/interaction.json"
            requests.patch(url, json=data, timeout=2)
        except Exception:
            pass

    def wait_for_operator_reply(self, timeout_seconds: float = 3.5) -> Optional[str]:
        """Checks for human operator reply during the grace period."""
        if not self.database_url:
            return None

        start_time = time.time()
        url = f"{self.database_url}/rollopod/interaction.json"

        while (time.time() - start_time) < timeout_seconds:
            try:
                res = requests.get(url, timeout=1.5)
                if res.status_code == 200 and res.json():
                    data = res.json()
                    if data.get("reply_source") == "human" and data.get("reply"):
                        return data["reply"]
            except Exception:
                pass
            time.sleep(0.4)

        return None

    def start_background_listener(self, on_direct_speak: Optional[Callable[[str], None]] = None,
                                  on_voice_change: Optional[Callable[[str], None]] = None,
                                  on_pitch_change: Optional[Callable[[str], None]] = None,
                                  on_mode_change: Optional[Callable[[str], None]] = None):
        """Lightweight listener for soundboard triggers, voice profile, pitch, or mode changes."""
        if not self.database_url:
            return

        def _worker():
            self.is_listening = True
            # Ignore any stale commands from previous runs
            last_speak_time = int(time.time() * 1000) + 2000
            url = f"{self.database_url}/rollopod/command.json"
            
            while self.is_listening:
                try:
                    res = requests.get(url, timeout=3)
                    if res.status_code == 200 and res.json():
                        data = res.json()
                        cmd_time = data.get("timestamp", 0)
                        text = data.get("speak", "").strip()
                        voice = data.get("voice_profile", "").strip()
                        pitch = data.get("pitch", "").strip()
                        mode = data.get("mode", "").strip()

                        if cmd_time > last_speak_time:
                            last_speak_time = cmd_time
                            if text and on_direct_speak:
                                on_direct_speak(text)
                            if voice and on_voice_change:
                                on_voice_change(voice)
                            if pitch and on_pitch_change:
                                on_pitch_change(pitch)
                            if mode and on_mode_change:
                                on_mode_change(mode)
                except Exception:
                    pass
                time.sleep(1.2)  # Low-frequency poll to avoid any RTDB burden

        self._listener_thread = threading.Thread(target=_worker, daemon=True)
        self._listener_thread.start()

    def update_robot_status(self, state: str, extra: Optional[Dict[str, Any]] = None):
        """No-op or minimal update to prevent spamming RTDB."""
        pass

    def stop(self):
        self.is_listening = False
