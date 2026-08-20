# 🤖 Rollopod Voice AI & Operator System

This directory contains the Python Voice AI and Robot Controller for the **Rollopod Tech Expo Project**.

## Features

1. **Speech-to-Text (STT)**: Listens for visitors speaking near the Rollopod booth.
2. **Instant Pre-known Facts**: Matches Expo FAQs & documentation instantly without latency.
3. **Firebase Realtime Sync**: Pushes visitor questions in real-time to the **Flutter Android Companion App**.
4. **Human Operator Override (Wizard of Oz)**: If you type or tap an answer from the phone app, Rollopod prioritizes your human response immediately!
5. **Gemini 2.0 / 1.5 Flash AI Fallback**: If no human intervenes within 3.5s and question is outside pre-known facts, Gemini Flash answers in character.
6. **Child Neural Voice (TTS)**: High-quality, friendly child voice synthesis using `edge-tts` (`en-US-AnaNeural` / `en-US-MaisieNeural`).

---

## Installation

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Add your `GEMINI_API_KEY` and Firebase Database URL:
     ```env
     FIREBASE_DB_URL=https://your-project-default-rtdb.firebaseio.com/
     GEMINI_API_KEY=your_gemini_api_key_here
     TTS_VOICE=en-US-AnaNeural
     ```

---

## Running Rollopod Brain

### 1. Interactive Voice Mode (Microphone at Expo Booth)
```bash
python rollopod_brain.py
```

### 2. CLI Text Testing Mode (Test without microphone)
```bash
python rollopod_brain.py --cli
```

### 3. Custom Voice Options
To switch to British child voice or bilingual:
```bash
python rollopod_brain.py --voice en-US-MaisieNeural
```
Or for Indian English child voice:
```bash
python rollopod_brain.py --voice en-IN-NeerjaNeural
```
