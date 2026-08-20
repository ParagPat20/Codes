"""
Rollopod Heavy Robot Voice Tester
Listen to curated heavy robot voice profiles.
"""

import os
import sys
from tts_engine import RollopodTTSEngine
from voice_profiles import VOICE_PROFILES

def main():
    print("=" * 60)
    print("🤖 ROLLOPOD HEAVY ROBOT VOICE AUDITION")
    print("=" * 60)
    print("Available Voice Profiles:\n")

    sample_text = "I am Rollopod. A heavy transformable hexapod engineered for dual-mode locomotion. Initiating transformation sequence."

    for key, info in VOICE_PROFILES.items():
        print(f"[{key}]: {info['name']}")
        print(f"   Description: {info['description']}")
        print(f"   Voice: {info['voice']} | Pitch: {info['pitch']} | Rate: {info['rate']}\n")

    while True:
        choice = input("Enter profile name to listen (or 'exit'): ").strip().lower()
        if choice in ["exit", "q"]:
            break
        if choice not in VOICE_PROFILES:
            print(f"Invalid profile. Choose from: {list(VOICE_PROFILES.keys())}")
            continue

        print(f"\n▶ Playing sample for [{choice}]...")
        tts = RollopodTTSEngine(profile_name=choice)
        tts.speak(sample_text, blocking=True)
        print("Done!\n")

if __name__ == "__main__":
    main()
