"""
Rollopod Knowledge Base & FAQ Matcher
Extracts and indexes facts from Rollopod documentation and curated Expo Q&As with strict keyword scoring.
"""

import os
import re
import difflib
from typing import Optional, Dict, Tuple, List

EXPO_FAQS = [
    {
        "id": "intro",
        "keywords": ["who are you", "what are you", "what is your name", "introduce yourself", "tell me about yourself", "who is rollopod"],
        "answer": "I am Rollopod! A heavy-duty, transformable hexapod robot capable of both six-legged walking and high-speed rolling locomotion!"
    },
    {
        "id": "gaits",
        "keywords": ["what are your gaits", "what gaits do you have", "walking gaits", "tripod gait", "how do you walk", "gait patterns", "locomotion gaits"],
        "answer": "In walking mode, I utilize an alternating tripod gait for high-speed stability across rough terrain, as well as wave and ripple gaits for precise obstacle traversal!"
    },
    {
        "id": "rolling",
        "keywords": ["how do you roll", "how do you roll exactly", "rolling mode", "differential rolling", "how do wheels work", "two wheel mode"],
        "answer": "To roll, three servo-leg modules on each side fold into one-third circular arcs, forming dual 400-millimeter rolling rings driven by high-torque DC motors for continuous high-speed motion!"
    },
    {
        "id": "transformation",
        "keywords": ["how do you transform", "transformation", "transforming mechanism", "fold legs", "forming rings", "transformation sequence"],
        "answer": "My transformation coordinates all six leg assemblies via PWM servo drivers to fold and lock into two continuous circular rolling rings while my central pod stays suspended and level!"
    },
    {
        "id": "language_hindi",
        "keywords": ["hindi", "do you speak hindi", "kya tum hindi", "hindi aati hai", "samajh mein aati hai", "languages", "language"],
        "answer": "Yes, I understand Hindi and English, but I converse in clear English here at the Tech Expo so all visitors and judges can easily understand my features!"
    },
    {
        "id": "specs_weight",
        "keywords": ["what is your weight", "how much do you weigh", "how heavy are you", "weight", "mass", "total weight", "dimensions", "specifications", "size"],
        "answer": "I have a total mass of approximately 11 kilograms: five kilograms for each transformable side wheel assembly, and a one-kilogram suspended central payload pod."
    },
    {
        "id": "central_pod",
        "keywords": ["central pod", "suspended body", "pendulum", "how do you balance", "bearings", "center of gravity"],
        "answer": "My central pod is suspended below a rigid rotating rod using precision bearings. It acts like a stable pendulum, keeping my controllers, IMU, and sensors upright during both walking and rolling."
    },
    {
        "id": "motors_actuators",
        "keywords": ["what motors", "servos", "actuators", "how many motors", "how many servos", "pca9685", "motor drivers"],
        "answer": "I am actuated by high-torque digital servo motors controlled via PCA9685 PWM drivers for leg articulation, combined with high-power DC drive motors for rolling."
    },
    {
        "id": "controllers",
        "keywords": ["microcontroller", "what processor", "esp32", "brain", "control architecture", "electronics"],
        "answer": "My control architecture uses ESP32 microcontrollers communicating wirelessly with distributed PWM drivers and inertial measurement sensors for real-time balance."
    },
    {
        "id": "battery_power",
        "keywords": ["battery", "power supply", "voltage", "how are you powered", "isolated power", "current draw"],
        "answer": "I feature an isolated power architecture: separate high-discharge lithium battery channels power the high-current servo actuators and the sensitive microcontroller logic to prevent electrical noise."
    },
    {
        "id": "creator",
        "keywords": ["who built you", "who made you", "who created you", "who is your creator", "author", "maker"],
        "answer": "I was designed, engineered, and assembled by my creator for this Tech Expo showcase, featuring custom CAD frames and distributed electronics."
    },
    {
        "id": "expo_category",
        "keywords": ["tech expo", "theme", "category", "competition category", "project category"],
        "answer": "I am presented under the Senior Category for Robotics and Aerial Robotics, demonstrating reconfigurable hybrid locomotion."
    },
    {
        "id": "capabilities",
        "keywords": ["what can you do", "features", "capabilities", "what are your abilities", "why rollopod"],
        "answer": "I combine the terrain adaptability of a hexapod with the high speed and efficiency of a rolling robot, overcoming the limits of fixed wheels and slow-moving walkers!"
    },
    {
        "id": "greetings",
        "keywords": ["hello", "hi", "hey", "good morning", "good afternoon", "good evening", "welcome"],
        "answer": "Greetings! Welcome to the Rollopod Tech Expo demonstration. Ask me about my gaits, transformation, or mechanical architecture!"
    },
    {
        "id": "thanks",
        "keywords": ["thank you", "thanks", "great job", "awesome robot", "cool robot", "impressive"],
        "answer": "Thank you! I am built for high-performance mobility. Feel free to ask more technical questions!"
    }
]

class RollopodKnowledgeBase:
    def __init__(self, doc_dir: Optional[str] = None):
        self.doc_dir = doc_dir or os.path.join(os.path.dirname(__file__), "..", "..", "Documentation")
        self.faqs = EXPO_FAQS

    def _tokenize(self, text: str) -> List[str]:
        """Extracts cleaned lower-case word tokens."""
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        return [w for w in clean.split() if w]

    def find_preknown_fact(self, question: str, threshold: float = 0.72) -> Optional[Tuple[str, float]]:
        """
        Robust FAQ matching using token set overlap and full-phrase similarity.
        Prevents false positive substring matches.
        """
        clean_q = re.sub(r"[^\w\s]", " ", question.lower()).strip()
        q_tokens = set(self._tokenize(clean_q))
        if not q_tokens:
            return None

        # Filter common filler words for semantic matching
        stopwords = {"a", "an", "the", "is", "are", "do", "does", "can", "you", "your", "my", "me", "tell", "about", "what", "how", "why"}
        semantic_q_tokens = q_tokens - stopwords

        best_answer = None
        best_score = 0.0

        for item in self.faqs:
            for kw in item["keywords"]:
                clean_kw = re.sub(r"[^\w\s]", " ", kw.lower()).strip()
                kw_tokens = set(self._tokenize(clean_kw))
                semantic_kw_tokens = kw_tokens - stopwords

                # 1. Exact phrase match
                if clean_q == clean_kw:
                    return item["answer"], 1.0

                # 2. Key phrase token containment (e.g. "what are your gaits" matches "gaits" FAQ)
                if semantic_kw_tokens and semantic_kw_tokens.issubset(semantic_q_tokens):
                    score = len(semantic_kw_tokens) / len(semantic_q_tokens) if semantic_q_tokens else 0.8
                    score = max(0.85, score)
                    if score > best_score:
                        best_score = score
                        best_answer = item["answer"]
                    continue

                # 3. Fuzzy SequenceMatcher
                ratio = difflib.SequenceMatcher(None, clean_q, clean_kw).ratio()
                if ratio > best_score:
                    best_score = ratio
                    best_answer = item["answer"]

        if best_score >= threshold:
            return best_answer, best_score

        return None

    def get_system_prompt_context(self) -> str:
        """Constructs concise background context for Gemini Flash."""
        context_parts = [
            "You are Rollopod, an intelligent transforming robot demonstrating at a Tech Expo.",
            "Key Facts & Guidelines:",
            "- Capabilities: You use 6 legs to walk over rough ground and transform those legs into 2 side wheels to roll quickly on smooth floors.",
            "- Structure: Your central body stays suspended and balanced in the middle during both modes.",
            "- Communication: Explain everything in clear, simple English that is easy for anyone to understand.",
            "- Tone: Friendly, polite, knowledgeable, and clear without using difficult jargon or cartoonish slang.",
            "- Length: Strictly 1 to 2 short, informative sentences."
        ]
        return "\n".join(context_parts)
