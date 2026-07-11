import re

def clean_llm_output(raw_output: str) -> str:
    """Cleans up the raw LLM output to extract pure JSON."""
    if not raw_output:
        return ""
        
    text = raw_output.strip()
    
    # Remove markdown formatting like ```json ... ```
    text = re.sub(r"```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"```\s*", "", text)
    
    # Sometimes models prepend text like "Here is the JSON:"
    # We'll try to find the first '{' and the last '}'
    start_idx = text.find('{')
    end_idx = text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return text[start_idx:end_idx + 1]
        
    return text
