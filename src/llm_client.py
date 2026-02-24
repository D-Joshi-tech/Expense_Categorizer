import requests
import json
from typing import Dict, Any

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def classify_json(self, prompt: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        }
        r = requests.post(url, json=payload, timeout=90)
        r.raise_for_status()
        text = r.json().get("response", "").strip()

        # Parse JSON. If model adds text, extract JSON substring.
        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(text[start:end+1])
            raise ValueError(f"LLM did not return valid JSON. First 300 chars: {text[:300]}")

class DisabledLLMClient:
    """Fallback when user disables LLM. Always returns minimal output."""
    def classify_json(self, prompt: str) -> Dict[str, Any]:
        return {"category": "Other", "confidence": 0.2, "reason": "LLM disabled"}