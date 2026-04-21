import logging
import webbrowser

import requests
import wikipedia
import pywhatkit

import config

logger = logging.getLogger(__name__)


class WebHandler:
    """
    Handles all outbound web interactions:
      - Opening websites
      - Fetching news headlines
      - Playing YouTube videos
      - Wikipedia summaries
      - Google searches

    No GUI or speech calls are made here — this class only does the
    network / browser work and returns data or raises descriptive
    exceptions. Speaking the result is the caller's responsibility.
    """

    # ------------------------------------------------------------------ #
    #  Websites                                                            #
    # ------------------------------------------------------------------ #

    def open_site(self, name: str) -> bool:
        """
        Open a website by its short name (e.g. 'google', 'youtube').
        Returns True on success, False if the name is unknown.
        """
        url = config.WEBSITES.get(name.lower())
        if url:
            webbrowser.open(url)
            logger.info("Opened website: %s → %s", name, url)
            return True
        logger.warning("Unknown site name: '%s'", name)
        return False

    def open_url(self, url: str) -> None:
        """Open any arbitrary URL in the default browser."""
        webbrowser.open(url)
        logger.info("Opened URL: %s", url)

    # ------------------------------------------------------------------ #
    #  News                                                                #
    # ------------------------------------------------------------------ #

    def get_headlines(self, country: str = "in", language: str = "en", count: int = 5) -> list[str]:
        """
        Fetch top news headlines from NewsData.io.

        Args:
            country:  2-letter country code (default: 'in' for India).
            language: Language code (default: 'en').
            count:    Maximum number of headlines to return.

        Returns:
            List of headline strings.

        Raises:
            ConnectionError: On network failure or bad API response.
            ValueError:      If the API returns no articles.
        """
        url = (
            f"{config.NEWS_URL}"
            f"?apikey={config.NEWS_API_KEY}"
            f"&country={country}&language={language}"
        )

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("News API request failed: %s", e)
            raise ConnectionError("Could not reach the news service.") from e

        articles = response.json().get("results", [])
        if not articles:
            raise ValueError("No news articles available right now.")

        headlines = [a.get("title", "No title") for a in articles[:count]]
        logger.info("Fetched %d headlines.", len(headlines))
        return headlines

    # ------------------------------------------------------------------ #
    #  YouTube                                                             #
    # ------------------------------------------------------------------ #

    def play_on_youtube(self, query: str) -> None:
        """
        Search for and play a video on YouTube using pywhatkit.

        Args:
            query: Song or video name to search for.
        """
        if not query:
            raise ValueError("No search query provided.")
        logger.info("Playing on YouTube: '%s'", query)
        pywhatkit.playonyt(query)

    # ------------------------------------------------------------------ #
    #  Wikipedia                                                           #
    # ------------------------------------------------------------------ #

    def wikipedia_summary(self, query: str, sentences: int = 2) -> str:
        """
        Return a short Wikipedia summary for the given query.

        Args:
            query:     The topic to look up.
            sentences: Number of sentences to return.

        Returns:
            Summary string.

        Raises:
            ValueError:  On disambiguation or page-not-found errors.
            RuntimeError: On unexpected Wikipedia errors.
        """
        try:
            summary = wikipedia.summary(query, sentences=sentences)
            logger.info("Wikipedia summary fetched for: '%s'", query)
            return summary

        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning("Wikipedia disambiguation for '%s': %s", query, e.options[:3])
            raise ValueError(
                f"That topic is ambiguous. Did you mean: {', '.join(e.options[:3])}?"
            ) from e

        except wikipedia.exceptions.PageError:
            logger.warning("Wikipedia page not found: '%s'", query)
            raise ValueError(f"No Wikipedia page found for '{query}'.") from None

        except Exception as e:
            logger.error("Wikipedia error: %s", e)
            raise RuntimeError("Something went wrong while searching Wikipedia.") from e

    # ------------------------------------------------------------------ #
    #  Google search                                                       #
    # ------------------------------------------------------------------ #

    def google_search(self, query: str) -> None:
        """Open a Google search results page for the given query."""
        if not query:
            raise ValueError("No search query provided.")
        url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
        self.open_url(url)
        logger.info("Google search opened for: '%s'", query)