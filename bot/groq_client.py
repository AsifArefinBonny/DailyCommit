"""
Groq API client with retries and error classification.
Groq provides free, ultra-fast LLM inference - no credit card required.
"""
import os
import time
import requests
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, ValidationError
from bot.telegram_notify import notify_admin

T = TypeVar('T', bound=BaseModel)


class GroqError(Exception):
    """Base exception for Groq errors."""
    pass


class GroqClient:
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile",
                 max_retries: int = 3, timeout: int = 30):
        self.api_key = api_key
        self.model_name = model_name
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate(self, prompt: str, response_model: Type[T],
                 system_prompt: Optional[str] = None) -> Optional[T]:
        """
        Generate and validate LLM output.
        Returns None if all retries fail (after alerting admin).
        """
        print(f"🤖 Calling Groq API with model: {self.model_name}", flush=True)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.max_retries):
            try:
                print(f"  → Attempt {attempt + 1}/{self.max_retries}", flush=True)

                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 8192,
                }

                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                # Classify error
                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", 60))
                    reason = f"Rate limited (retry after {retry_after}s)"
                    if attempt < self.max_retries - 1:
                        print(f"  ⏱️ Rate limited, waiting {retry_after}s...", flush=True)
                        time.sleep(retry_after)
                        continue
                    else:
                        notify_admin("Groq", f"⏱️ Rate limited",
                                   reason, {"model": self.model_name, "attempt": attempt + 1})
                        raise GroqError(reason)

                elif response.status_code == 401:
                    reason = "Invalid API key"
                    notify_admin("Groq", "❌ Auth failed", reason, {"model": self.model_name})
                    raise GroqError(reason)

                elif response.status_code >= 500:
                    reason = f"Server error (HTTP {response.status_code})"
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        print(f"  ⏱️ Server error, waiting {wait_time}s...", flush=True)
                        time.sleep(wait_time)
                        continue
                    notify_admin("Groq", f"❌ Server error", reason, {"model": self.model_name})
                    raise GroqError(reason)

                elif not response.ok:
                    reason = f"HTTP {response.status_code}: {response.text[:200]}"
                    notify_admin("Groq", f"❌ HTTP {response.status_code}", reason, {"model": self.model_name})
                    raise GroqError(reason)

                # Parse response
                data = response.json()
                content = data["choices"][0]["message"]["content"]
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
                    notify_admin("Groq", "⚠️ Validation failed", reason,
                               {"model": self.model_name, "content_preview": content[:200]})
                    raise GroqError(reason)

            except requests.Timeout:
                reason = f"Request timeout ({self.timeout}s)"
                if attempt < self.max_retries - 1:
                    print(f"  ⏱️ Timeout, retrying...", flush=True)
                    continue
                notify_admin("Groq", "⏱️ Timeout", reason, {"model": self.model_name})
                raise GroqError(reason)

            except requests.RequestException as e:
                reason = f"Network error: {str(e)}"
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt
                    print(f"  ⏱️ Network error, waiting {wait_time}s...", flush=True)
                    time.sleep(wait_time)
                    continue
                notify_admin("Groq", "❌ Network error", reason, {"model": self.model_name})
                raise GroqError(reason)

        # All retries failed
        notify_admin(
            service="Groq",
            status="❌ All retries failed",
            reason=f"Failed after {self.max_retries} attempts",
            context={"model": self.model_name}
        )
        return None
