"""LLM client for OpenRouter API."""

import httpx
from typing import Optional, List, Dict, Any

from .config import get_config


class LLMClient:
    """Client for OpenRouter/LLM API operations."""
    
    def __init__(self, api_key: str, api_url: str, model: str):
        self.api_key = api_key
        self.api_url = api_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def generate_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """Generate a completion from the LLM."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = await self.client.post(
                f"{self.api_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("choices") and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            
            return ""
        
        except Exception as e:
            print(f"LLM API error: {e}")
            return f"Error generating response: {str(e)}"
    
    async def analyze_deal_compliance(
        self,
        deal_title: str,
        stage: str,
        notes: List[str],
    ) -> Dict[str, Any]:
        """Analyze deal compliance from notes."""
        system_prompt = """You are an expert at analyzing project compliance documentation.
Analyze the provided deal notes and determine:
1. Is a survey checklist present? (yes/no/unclear)
2. Are quality documents present? (yes/no/unclear)
3. Brief comment summarizing compliance status

Respond in JSON format: {"survey_checklist": bool, "quality_docs": bool, "comment": str}"""
        
        user_prompt = f"""Deal: {deal_title}
Stage: {stage}

Notes:
{chr(10).join(f"- {note}" for note in notes[:10])}

Analyze compliance documentation status."""
        
        response = await self.generate_completion(user_prompt, system_prompt, max_tokens=300)
        
        # Parse JSON response (simplified - in production use proper JSON parsing)
        try:
            import json
            result = json.loads(response)
            return result
        except:
            return {
                "survey_checklist": None,
                "quality_docs": None,
                "comment": response[:200],
            }
    
    async def analyze_order_received(
        self,
        deal_title: str,
        notes: List[str],
    ) -> Dict[str, Any]:
        """Analyze order received deal for end user identification."""
        system_prompt = """Analyze project notes to determine:
1. Has the end user been identified? (yes/no/unknown)
2. How many end-user-specific requests have been made?

Respond in JSON: {"end_user_identified": bool, "end_user_requests_count": int}"""
        
        user_prompt = f"""Deal: {deal_title}

Notes:
{chr(10).join(f"- {note}" for note in notes[:10])}

Analyze end user status."""
        
        response = await self.generate_completion(user_prompt, system_prompt, max_tokens=200)
        
        try:
            import json
            result = json.loads(response)
            return result
        except:
            return {
                "end_user_identified": None,
                "end_user_requests_count": 0,
            }
    
    async def summarize_deal(
        self,
        deal_title: str,
        stage: str,
        notes: List[str],
    ) -> Dict[str, str]:
        """Generate a summary and next action for a deal."""
        system_prompt = """Summarize the deal's current status in 1-2 sentences.
Then suggest the next action needed.

Respond in JSON: {"summary": str, "next_action": str}"""
        
        user_prompt = f"""Deal: {deal_title}
Stage: {stage}

Recent notes:
{chr(10).join(f"- {note}" for note in notes[:5])}

Provide summary and next action."""
        
        response = await self.generate_completion(user_prompt, system_prompt, max_tokens=300)
        
        try:
            import json
            result = json.loads(response)
            return result
        except:
            return {
                "summary": response[:200] if response else "No summary available",
                "next_action": "Review deal status",
            }


# Global client instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get or create LLM client singleton."""
    global _llm_client
    if _llm_client is None:
        config = get_config()
        _llm_client = LLMClient(
            api_key=config.openrouter_api_key,
            api_url=config.openrouter_api_url,
            model=config.llm_model,
        )
    return _llm_client