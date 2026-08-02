"""
Telegram notification helper for admin alerts.
Every failure calls notify_admin() with a human-readable reason.
"""
import os
import requests
from typing import Optional, Any, Dict


def notify_admin(service: str, status: str, reason: str, context: Optional[Dict[str, Any]] = None, run_url: Optional[str] = None):
    """
    Send a formatted alert to the admin's Telegram.

    Args:
        service: e.g., "OpenRouter", "Telegram Bot API", "Supabase"
        status: e.g., "HTTP 429", "❌ Failed", "⚠️ Warning"
        reason: Human-readable explanation
        context: Additional debug info (dict)
        run_url: GitHub Actions run URL (if applicable)
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")  # Your telegram user ID

    if not bot_token or not admin_chat_id:
        print(f"⚠️ Cannot send alert (missing credentials): {service} {status} - {reason}")
        return

    # Format alert message
    message = f"⚠️ **{status}**\n"
    message += f"service: {service}\n"
    message += f"reason: {reason}\n"

    if context:
        message += f"context: {context}\n"

    if run_url:
        message += f"run: {run_url}\n"

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": admin_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)

        if not response.ok:
            print(f"Failed to send Telegram alert: HTTP {response.status_code}")
            print(f"Alert content: {message}")
    except Exception as e:
        print(f"Failed to send Telegram alert: {e}")
        print(f"Alert content: {message}")


def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None) -> bool:
    """
    Send a Telegram message with error handling.
    Returns True if successful, False otherwise.
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        notify_admin("Telegram", "❌ Missing token", "TELEGRAM_BOT_TOKEN not set", {})
        return False

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 429:
            retry_after = response.json().get("parameters", {}).get("retry_after", 30)
            notify_admin("Telegram Bot API", "HTTP 429",
                       f"Rate limited (retry after {retry_after}s)",
                       {"chat_id": chat_id})
            return False

        elif response.status_code == 403:
            notify_admin("Telegram Bot API", "HTTP 403",
                       "Bot blocked by user or chat not found",
                       {"chat_id": chat_id})
            return False

        elif response.status_code == 401:
            notify_admin("Telegram Bot API", "HTTP 401",
                       "Invalid bot token",
                       {"chat_id": chat_id})
            return False

        elif response.status_code == 400:
            notify_admin("Telegram Bot API", "HTTP 400",
                       f"Bad request: {response.text[:200]}",
                       {"chat_id": chat_id, "payload": payload})
            return False

        elif not response.ok:
            notify_admin("Telegram Bot API", f"HTTP {response.status_code}",
                       response.text[:200],
                       {"chat_id": chat_id})
            return False

        return True

    except requests.Timeout:
        notify_admin("Telegram Bot API", "⏱️ Timeout",
                   "Request timed out after 10s",
                   {"chat_id": chat_id})
        return False

    except Exception as e:
        notify_admin("Telegram Bot API", "❌ Exception",
                   str(e),
                   {"chat_id": chat_id})
        return False
