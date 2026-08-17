"""
services/ai/groq_provider.py

Thin wrapper around the official Groq SDK.

The Groq API key and model are loaded from backend/.env.
The API key never reaches the browser.
"""

import base64

from groq import Groq

from app.config import settings


class GroqProvider:
    """Client wrapper for the Groq Chat Completions API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL

        self.client = (
            Groq(api_key=self.api_key)
            if self.api_key
            else None
        )

    def is_configured(self) -> bool:
        """Return True when a Groq API key is configured."""
        return bool(self.client)

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        image_bytes: bytes | None = None,
        image_mime: str = "image/jpeg",
        max_tokens: int = 2000,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> str:
        """Send a chat completion to Groq and return the response text."""

        if not self.is_configured():
            raise ValueError(
                "The Groq API key is not set. Add GROQ_API_KEY to "
                "backend/.env (locally) or to Railway variables."
            )

        # ---------------------------------------------------------
        # TEXT-ONLY REQUEST
        # ---------------------------------------------------------
        if not image_bytes:
            user_content = user_message

        # ---------------------------------------------------------
        # IMAGE REQUEST
        # ---------------------------------------------------------
        else:
            encoded = base64.b64encode(image_bytes).decode("ascii")

            user_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_mime};base64,{encoded}"
                    },
                },
                {
                    "type": "text",
                    "text": user_message,
                },
            ]

        # ---------------------------------------------------------
        # LIMIT COMPLETION SIZE
        # ---------------------------------------------------------
        # Prevent callers from accidentally requesting a large
        # completion that could exceed the Groq TPM limit.
        max_tokens = min(max_tokens, 2000)

        request = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # ---------------------------------------------------------
        # JSON MODE
        # ---------------------------------------------------------
        if json_mode:
            request["response_format"] = {
                "type": "json_object"
            }

        completion = self.client.chat.completions.create(
            **request
        )

        return completion.choices[0].message.content or ""