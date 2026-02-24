from typing import Dict, Any, Tuple, List
from pydantic import BaseModel, Field, ValidationError
from src.utils import normalize_for_match

class LLMCategoryOut(BaseModel):
    category: str
    confidence: float = Field(..., ge=0, le=1)
    reason: str = Field(..., max_length=180)

def rule_based_category(desc_norm: str, merchant_rules: Dict[str, str]) -> Tuple[str, float, str] | None:
    for key, cat in merchant_rules.items():
        if key in desc_norm:
            return cat, 0.95, f"Matched rule: {key}"
    return None

def build_prompt(description: str, categories: List[str]) -> str:
    cats = ", ".join(categories)
    return f"""
You are an expense categorization engine.

Return ONLY valid JSON (no extra keys, no markdown) with:
- category: must be exactly one of [{cats}]
- confidence: number between 0 and 1
- reason: short explanation <= 180 chars

Transaction description: "{description}"

JSON:
""".strip()

def categorize_one(description: str, llm_client, categories: List[str], merchant_rules: Dict[str, str]) -> Dict[str, Any]:
    desc_norm = normalize_for_match(description)

    rb = rule_based_category(desc_norm, merchant_rules)
    if rb:
        cat, conf, reason = rb
        # Enforce category existence even for rules
        if cat not in categories:
            return {"category": "Other", "confidence": 0.4, "reason": "Rule mapped to unknown category; forced Other", "method": "fallback"}
        return {"category": cat, "confidence": conf, "reason": reason, "method": "rule"}

    prompt = build_prompt(description, categories)
    try:
        raw = llm_client.classify_json(prompt)
    except Exception:
        return {"category": "Other", "confidence": 0.2, "reason": "LLM call failed; defaulted to Other", "method": "fallback"}

    try:
        parsed = LLMCategoryOut(**raw)
    except ValidationError:
        return {"category": "Other", "confidence": 0.2, "reason": "Invalid LLM output; defaulted to Other", "method": "fallback"}

    if parsed.category not in categories:
        return {"category": "Other", "confidence": min(parsed.confidence, 0.4), "reason": "Category not allowed; defaulted to Other", "method": "fallback"}

    return {"category": parsed.category, "confidence": parsed.confidence, "reason": parsed.reason, "method": "llm"}