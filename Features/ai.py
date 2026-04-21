import logging
from google import genai

import config

logger = logging.getLogger(__name__)


class AIClient:
    """
    Thin wrapper around the Gemini API.

    Keeps all AI-related concerns (model name, system prompt, error handling,
    response parsing) in one place. If you ever swap Gemini for another
    provider, only this file changes.

    Usage:
        ai = AIClient()
        reply = ai.ask("What is the capital of France?")
        # reply → "Paris."
    """

    def __init__(self):
        self._client = genai.Client(api_key=config.GEMINI_API_KEY)
        self._model  = config.GEMINI_MODEL
        self._system = config.GEMINI_SYSTEM_PROMPT
        logger.info("AIClient ready (model: %s).", self._model)

    def ask(self, prompt: str) -> str:
        """
        Send a prompt to Gemini and return the text response.

        Args:
            prompt: The user's spoken command or question.

        Returns:
            The model's reply as a plain string.
            Returns a safe fallback message if the API call fails.
        """
        if not prompt or not prompt.strip():
            return "I didn't receive a question."

        logger.debug("AIClient.ask → '%s'", prompt)

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[self._system, prompt],
            )
            reply = response.text.strip()
            logger.debug("AIClient reply ← '%s'", reply[:80])
            return reply

        except Exception as e:
            logger.error("Gemini API error: %s", e)
            return "I'm having trouble reaching the AI service right now."