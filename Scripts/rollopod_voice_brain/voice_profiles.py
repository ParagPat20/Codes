"""
Rollopod Heavy Robot Voice Profiles (Kokoro 82M Ultra-Fast + Edge Neural)
Curated presets for heavy transformable robot presence.
"""

VOICE_PROFILES = {
    "kokoro_adam": {
        "name": "Kokoro 82M Adam (Ultra-Fast <100ms, Authoritative)",
        "engine": "kokoro",
        "voice": "am_adam",
        "speed": 1.05,
        "description": "Ultra-fast neural robotics voice with natural cadence and low latency."
    },
    "kokoro_michael": {
        "name": "Kokoro 82M Michael (Ultra-Fast <100ms, Mech Titan)",
        "engine": "kokoro",
        "voice": "am_michael",
        "speed": 1.05,
        "description": "Deep, assertive, high-performance offline neural robot voice."
    },
    "kokoro_george": {
        "name": "Kokoro 82M George (Deep Resonant British Mech)",
        "engine": "kokoro",
        "voice": "bm_george",
        "speed": 1.0,
        "description": "Deep British robotics voice with crisp articulation."
    },
    "kokoro_bella": {
        "name": "Kokoro 82M Bella (Articulate AI Assistant)",
        "engine": "kokoro",
        "voice": "af_bella",
        "speed": 1.05,
        "description": "Warm, expressive, high-speed neural AI voice."
    },
    "iron_crush": {
        "name": "Iron Core (Rugged Mech - Edge Neural)",
        "engine": "edge",
        "voice": "en-US-EricNeural",
        "pitch": "-7Hz",
        "rate": "-2%",
        "description": "Strong mechanical authority without being monotonic."
    },
    "mech_titan": {
        "name": "Mech Titan (Cinematic Transformer - Edge Neural)",
        "engine": "edge",
        "voice": "en-US-ChristopherNeural",
        "pitch": "-6Hz",
        "rate": "-2%",
        "description": "Deep, powerful, cinematic transformer-style presence."
    },
    "cyber_sentinel": {
        "name": "Cyber Sentinel (Jarvis / High-Tech Mech)",
        "engine": "edge",
        "voice": "en-US-GuyNeural",
        "pitch": "-5Hz",
        "rate": "+0%",
        "description": "Resonant, clear, intelligent heavy robotics voice."
    },
    "indo_titan": {
        "name": "Indo Titan (Indian Accent Heavy Bot)",
        "engine": "edge",
        "voice": "en-IN-PrabhatNeural",
        "pitch": "-5Hz",
        "rate": "-2%",
        "description": "Deep, articulate Indian English robotics voice."
    }
}
