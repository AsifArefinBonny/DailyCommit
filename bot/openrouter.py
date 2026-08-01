"""
OpenRouter client with retries, fallback models, error classification, and alerts.
"""
import os
import time
import requests
from typing import Optional, Type, TypeVar, List
from pydantic import BaseModel, ValidationError
from telegram_notify import notify_admin

T = TypeVar('T', bound=BaseModel)


class OpenRouterError(Exception):
    """Base exception for OpenRouter errors."""
    pass


class OpenRouterClient:
    def __init__(self, api_key: str, primary_model: str, fallback_models: List[str],
                 max_retries: int = 3, timeout: int = 30):
        self.api_key = api_key
        self.primary_model = primary_model
        self.fallback_models = fallback_models
        self.max_retries = max_retries
        self.timeout = timeout
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate(self, prompt: str, response_model: Type[T],
                 system_prompt: Optional[str] = None) -> Optional[T]:
        """
        Generate and validate LLM output.
        Returns None if all models fail (after alerting admin).
        """
        models_to_try = [self.primary_model] + self.fallback_models
        print(f"🔄 Trying {len(models_to_try)} models: {models_to_try}", flush=True)

        for model_id in models_to_try:
            try:
                print(f"  → Trying model: {model_id}", flush=True)
                result = self._try_model(model_id, prompt, response_model, system_prompt)
                if result:
                    print(f"  ✓ Success with {model_id}", flush=True)
                    return result
                else:
                    print(f"  ✗ Failed with {model_id} (returned None)", flush=True)
            except OpenRouterError as e:
                # Already logged and notified inside _try_model
                print(f"  ✗ Error with {model_id}: {str(e)}", flush=True)
                continue

        # All models failed
        notify_admin(
            service="OpenRouter",
            status="❌ All models failed",
            reason=f"Tried {len(models_to_try)} models, none succeeded",
            context={"models": models_to_try}
        )
        return None

    def _try_model(self, model_id: str, prompt: str, response_model: Type[T],
                   system_prompt: Optional[str]) -> Optional[T]:
        """Try a single model with retries."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(self.max_retries):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": model_id,
                    "messages": messages,
                    "temperature": 0.7,
                }

                response = requests.post(
                    self.base_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                # Classify error
                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", 30))
                    reason = f"Rate limited (retry after {retry_after}s)"
                    if attempt < self.max_retries - 1:
                        time.sleep(retry_after)
                        continue
                    else:
                        notify_admin("OpenRouter", f"HTTP {response.status_code}",
                                   reason, {"model": model_id, "attempt": attempt + 1})
                        raise OpenRouterError(reason)

                elif response.status_code == 401:
                    reason = "Invalid API key"
                    notify_admin("OpenRouter", "❌ Auth failed", reason, {"model": model_id})
                    raise OpenRouterError(reason)

                elif response.status_code >= 500:
                    reason = f"Server error (HTTP {response.status_code})"
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    notify_admin("OpenRouter", f"HTTP {response.status_code}", reason, {"model": model_id})
                    raise OpenRouterError(reason)

                elif not response.ok:
                    reason = f"HTTP {response.status_code}: {response.text[:200]}"
                    notify_admin("OpenRouter", f"HTTP {response.status_code}", reason, {"model": model_id})
                    raise OpenRouterError(reason)

                # Parse response
                data = response.json()
                content = data["choices"][0]["message"]["content"]

                # Validate with Pydantic
                try:
                    # Attempt to parse as JSON first
                    import json
                    parsed = json.loads(content)
                    validated = response_model.model_validate(parsed)
                    return validated
                except (json.JSONDecodeError, ValidationError) as e:
                    reason = f"Invalid output format: {str(e)[:200]}"
                    if attempt < self.max_retries - 1:
                        # Retry with stricter prompt
                        continue
                    notify_admin("OpenRouter", "⚠️ Validation failed", reason,
                               {"model": model_id, "content_preview": content[:200]})
                    raise OpenRouterError(reason)

            except requests.Timeout:
                reason = f"Request timeout ({self.timeout}s)"
                if attempt < self.max_retries - 1:
                    continue
                notify_admin("OpenRouter", "⏱️ Timeout", reason, {"model": model_id})
                raise OpenRouterError(reason)

            except requests.RequestException as e:
                reason = f"Network error: {str(e)}"
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                notify_admin("OpenRouter", "❌ Network error", reason, {"model": model_id})
                raise OpenRouterError(reason)

        return None
