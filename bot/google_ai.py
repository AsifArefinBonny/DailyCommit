"""
Google AI Studio client with retries and error classification.
"""
import os
import time
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from telegram_notify import notify_admin

try:
    import google.generativeai as genai
except ImportError:
    genai = None

T = TypeVar('T', bound=BaseModel)


class GoogleAIError(Exception):
    """Base exception for Google AI errors."""
    pass


class GoogleAIClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash-exp",
                 max_retries: int = 3, timeout: int = 30):
        if genai is None:
            raise GoogleAIError("google-generativeai package not installed")

        self.api_key = api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout

        # Configure the client
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, response_model: Type[T],
                 system_prompt: Optional[str] = None) -> Optional[T]:
        """
        Generate and validate LLM output.
        Returns None if all retries fail (after alerting admin).
        """
        print(f"🤖 Calling Google AI API with model: {self.model_name}", flush=True)

        # Combine system prompt and user prompt
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        for attempt in range(self.max_retries):
            try:
                print(f"  → Attempt {attempt + 1}/{self.max_retries}", flush=True)

                # Generate content
                response = self.model.generate_content(
                    full_prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=8192,
                    )
                )

                # Check if response was blocked
                if not response.text:
                    reason = f"Response blocked: {response.prompt_feedback}"
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    notify_admin("Google AI", "⚠️ Response blocked", reason,
                               {"model": self.model_name, "attempt": attempt + 1})
                    raise GoogleAIError(reason)

                content = response.text
                print(f"  ✓ Got response ({len(content)} chars)", flush=True)

                # Validate with Pydantic
                try:
                    import json
                    # Try to extract JSON from markdown code blocks if present
                    if "```json" in content:
                        start = content.find("```json") + 7
                        end = content.find("```", start)
                        content = content[start:end].strip()
                    elif "```" in content:
                        start = content.find("```") + 3
                        end = content.find("```", start)
                        content = content[start:end].strip()

                    parsed = json.loads(content)
                    validated = response_model.model_validate(parsed)
                    print(f"  ✓ Validation successful", flush=True)
                    return validated

                except (json.JSONDecodeError, ValidationError) as e:
                    reason = f"Invalid output format: {str(e)[:200]}"
                    if attempt < self.max_retries - 1:
                        print(f"  ✗ Validation failed, retrying... ({str(e)[:100]})", flush=True)
                        time.sleep(2 ** attempt)
                        continue
                    notify_admin("Google AI", "⚠️ Validation failed", reason,
                               {"model": self.model_name, "content_preview": content[:200]})
                    raise GoogleAIError(reason)

            except Exception as e:
                if "quota" in str(e).lower() or "rate" in str(e).lower():
                    reason = f"Rate limit or quota exceeded: {str(e)}"
                    if attempt < self.max_retries - 1:
                        retry_after = 60  # Wait 1 minute for quota issues
                        print(f"  ⏱️ Rate limited, waiting {retry_after}s...", flush=True)
                        time.sleep(retry_after)
                        continue
                    notify_admin("Google AI", "⏱️ Rate limited", reason,
                               {"model": self.model_name, "attempt": attempt + 1})
                    raise GoogleAIError(reason)
                elif "API key" in str(e):
                    reason = f"Invalid API key: {str(e)}"
                    notify_admin("Google AI", "❌ Auth failed", reason,
                               {"model": self.model_name})
                    raise GoogleAIError(reason)
                else:
                    reason = f"Error: {str(e)}"
                    if attempt < self.max_retries - 1:
                        print(f"  ✗ Error, retrying... ({str(e)[:100]})", flush=True)
                        time.sleep(2 ** attempt)
                        continue
                    notify_admin("Google AI", "❌ Error", reason,
                               {"model": self.model_name, "attempt": attempt + 1})
                    raise GoogleAIError(reason)

        # All retries failed
        notify_admin(
            service="Google AI",
            status="❌ All retries failed",
            reason=f"Failed after {self.max_retries} attempts",
            context={"model": self.model_name}
        )
        return None
