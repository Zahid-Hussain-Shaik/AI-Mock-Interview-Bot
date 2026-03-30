"""
Anthropic Claude API client with retry logic and structured response parsing.
"""

import json
import time
import logging
from anthropic import Anthropic, APIError, RateLimitError, APIConnectionError

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Wrapper around the Anthropic API with retry and error handling."""

    def __init__(self, api_key, model, max_retries=3, timeout=45, max_tokens=4096):
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Please set it in your .env file or environment variables."
            )
        self._client = Anthropic(api_key=api_key, timeout=timeout)
        self._model = model
        self._max_retries = max_retries
        self._max_tokens = max_tokens

    def call(self, system_prompt, user_message, max_tokens=None):
        """
        Send a message to Claude and return the raw text response.
        Implements exponential backoff retry for transient errors.
        """
        tokens = max_tokens or self._max_tokens
        last_error = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.info(
                    "Claude API call attempt %d/%d (model=%s)",
                    attempt, self._max_retries, self._model,
                )
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                text = response.content[0].text
                logger.info("Claude API call succeeded on attempt %d", attempt)
                return text

            except RateLimitError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(
                    "Rate limited on attempt %d. Retrying in %ds...", attempt, wait
                )
                time.sleep(wait)

            except APIConnectionError as e:
                last_error = e
                wait = 2 ** attempt
                logger.warning(
                    "Connection error on attempt %d: %s. Retrying in %ds...",
                    attempt, str(e), wait,
                )
                time.sleep(wait)

            except APIError as e:
                last_error = e
                if e.status_code and e.status_code >= 500:
                    wait = 2 ** attempt
                    logger.warning(
                        "Server error %d on attempt %d. Retrying in %ds...",
                        e.status_code, attempt, wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error("Non-retryable API error: %s", str(e))
                    raise

        raise RuntimeError(
            f"Claude API call failed after {self._max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def call_json(self, system_prompt, user_message, max_tokens=None):
        """
        Send a message to Claude and parse the response as JSON.
        Handles markdown-wrapped JSON blocks.
        """
        raw = self.call(system_prompt, user_message, max_tokens)
        return self._parse_json(raw)

    @staticmethod
    def _parse_json(text):
        """
        Parse JSON from Claude's response, handling common wrapping patterns.
        """
        cleaned = text.strip()

        # Try direct parse first
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code block
        if "```" in cleaned:
            # Find the JSON block
            lines = cleaned.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.strip().startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            if json_lines:
                try:
                    return json.loads("\n".join(json_lines))
                except json.JSONDecodeError:
                    pass

        # Try finding JSON array or object boundaries
        for start_char, end_char in [("[", "]"), ("{", "}")]:
            start = cleaned.find(start_char)
            end = cleaned.rfind(end_char)
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(cleaned[start : end + 1])
                except json.JSONDecodeError:
                    pass

        raise ValueError(f"Could not parse JSON from Claude response:\n{text[:500]}")
