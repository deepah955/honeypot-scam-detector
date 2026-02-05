"""
Prompt templates for LLM interactions
"""

from pathlib import Path


def load_prompt(prompt_name: str) -> str:
    """Load a prompt template from file"""
    prompt_dir = Path(__file__).parent
    prompt_file = prompt_dir / f"{prompt_name}.txt"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    
    return prompt_file.read_text(encoding="utf-8")


# Pre-load prompts
DETECTION_PROMPT = load_prompt("detection_prompt")
AGENT_PERSONA_PROMPT = load_prompt("agent_persona_prompt")
EXTRACTION_PROMPT = load_prompt("extraction_prompt")
STRATEGY_PROMPT = load_prompt("strategy_prompt")

__all__ = [
    "load_prompt",
    "DETECTION_PROMPT",
    "AGENT_PERSONA_PROMPT",
    "EXTRACTION_PROMPT",
    "STRATEGY_PROMPT",
]
