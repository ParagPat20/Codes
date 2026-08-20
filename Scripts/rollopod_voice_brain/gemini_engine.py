"""
Rollopod Gemini Flash AI Engine
Integrates Gemini 2.0 / 1.5 Flash for fast conversational answers with Rollopod child persona.
"""

import os
import warnings
from typing import Optional

warnings.filterwarnings("ignore", category=UserWarning)

try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
except Exception:
    pass

class RollopodGeminiEngine:
    def __init__(self, api_key: Optional[str] = None, system_instruction: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.system_instruction = system_instruction or (
            "You are Rollopod, an intelligent transforming robot demonstrating at a Tech Expo. "
            "You can walk on 6 legs across rough terrain and transform your legs into two side rolling rings for smooth, fast motion. "
            "Strict Response Rules: "
            "- Reply in exactly ONE short, clear, and direct sentence in plain English (10 to 18 words maximum). "
            "- Never give long explanations or multiple paragraphs. "
            "- Be polite, friendly, and informative."
        )
        self.client = None
        self._init_gemini()

    def _init_gemini(self):
        if not self.api_key:
            print("[GeminiEngine] Warning: GEMINI_API_KEY is not set. Gemini fallback will be unavailable until configured.")
            return

        try:
            # Try new google-genai SDK first
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
            print("[GeminiEngine] Successfully initialized with google-genai SDK.")
        except Exception:
            try:
                # Try google-generativeai legacy SDK
                import google.generativeai as genai_legacy
                genai_legacy.configure(api_key=self.api_key)
                self.client = genai_legacy.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=self.system_instruction
                )
                self.sdk_type = "google-generativeai"
                print("[GeminiEngine] Successfully initialized with google-generativeai SDK.")
            except Exception as e:
                print(f"[GeminiEngine] Error initializing Gemini: {e}")
                self.client = None

    def generate_response(self, question: str, extra_context: Optional[str] = None) -> str:
        """Generates response using Gemini Flash with persona constraints."""
        if not self.client:
            return "I am connected to my local knowledge base! My creator can explain more details at the booth!"

        prompt = question
        if extra_context:
            prompt = f"Context:\n{extra_context}\n\nVisitor Question: {question}\nAnswer as Rollopod:"

        try:
            if self.sdk_type == "google-genai":
                from google.genai import types
                try:
                    response = self.client.models.generate_content(
                        model="gemini-3.7-flash",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=self.system_instruction,
                            temperature=0.7,
                            thinking_config=types.ThinkingConfig(thinking_budget=0),
                            max_output_tokens=400
                        )
                    )
                except Exception:
                    response = self.client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=self.system_instruction,
                            temperature=0.7,
                            max_output_tokens=400
                        )
                    )
                text = response.text.strip()
            else:
                response = self.client.generate_content(prompt)
                text = response.text.strip()
            
            # Clean formatting (remove markdown asterisks that sound weird in TTS)
            text = text.replace("*", "").replace("#", "").strip()
            return text
        except Exception as e:
            print(f"[GeminiEngine] Error during generation: {e}")
            return "I am Rollopod! Thanks for asking, my creator can also demonstrate this live for you!"
