import sys
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from knowledge_base import RollopodKnowledgeBase

kb = RollopodKnowledgeBase()
tests = [
    "Hello, what can you do?",
    "How do you roll exactly?",
    "How do you roll?",
    "what are your gaits?",
    "what are you",
    "who built you",
    "how much do you weigh",
    "tell me about the central pod",
    "Can you dance at the expo?"
]

for q in tests:
    res = kb.find_preknown_fact(q)
    if res:
        ans, score = res
        print(f"[MATCH] Q: \"{q}\"\n   Score: {score:.2f}\n   Ans: \"{ans}\"\n")
    else:
        print(f"[FALLBACK] Q: \"{q}\" => Routes to Operator / Gemini Flash AI\n")
