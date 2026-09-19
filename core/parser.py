import logging
import re
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


class PageFetchError(Exception):
    """Raised when the page could not be fetched after all retry attempts."""


def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def fetch_page_html(
    url: str,
    wait_seconds: int = 3,
    scroll_pause: float = 1.0,
    max_retries: int = 3,
) -> str:
    """Loads a page through headless Chrome (Selenium) and returns the rendered HTML.

    Scrolls down repeatedly to force lazy-loaded content (like the full
    IMDb Top 250 list) to render before capturing the final HTML. Retries
    up to `max_retries` times on WebDriver/network failures (e.g. transient
    timeouts, driver crashes) before giving up.

    Args:
        url: Page URL to fetch.
        wait_seconds: Seconds to wait after the initial page load, before
            scrolling starts, to let the first batch of content render.
        scroll_pause: Seconds to wait between each scroll step.
        max_retries: Maximum number of fetch attempts before giving up.

    Returns:
        The fully rendered page HTML (after scrolling to the bottom).

    Raises:
        PageFetchError: If the page could not be fetched after
            ``max_retries`` attempts.
    """
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        driver = None
        try:
            logger.info(f"Fetching page (attempt {attempt}/{max_retries}): {url}")
            driver = _build_driver()
            driver.set_page_load_timeout(30)
            driver.get(url)
            time.sleep(wait_seconds)

            # Scroll down repeatedly until the page height stops growing,
            # which means all lazy-loaded items have been rendered.
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            html = driver.page_source
            logger.info(f"Successfully fetched {len(html)} characters")
            return html

        except (WebDriverException, TimeoutException) as exc:
            last_error = exc
            logger.warning(f"Attempt {attempt}/{max_retries} failed: {exc}")
            if attempt < max_retries:
                time.sleep(2 * attempt)  # simple backoff before retrying
        finally:
            if driver is not None:
                driver.quit()

    raise PageFetchError(f"Failed to fetch {url} after {max_retries} attempts") from last_error


def _extract_movie(rank: int, elem) -> dict | None:
    """Extracts one movie's data from its <h4> title element. Returns None
    if the element has no IMDb ID (i.e. it's a nav link, not a real movie)."""
    title = elem.get_text(strip=True)

    parent_link = elem.find_parent("a")
    href = parent_link["href"] if parent_link else None
    movie_id_match = re.search(r"/title/(tt\d+)/", href) if href else None
    movie_id = movie_id_match.group(1) if movie_id_match else None

    if movie_id is None:
        return None

    # Parent container that groups the title, year, and rating for this movie
    container = elem.find_parent("div", class_="sc-a96da33f-0") or elem.find_parent("li")

    year = None
    rating = None

    if container:
        metadata_div = container.find("div", class_="cli-title-metadata")
        if metadata_div:
            first_li = metadata_div.find("li")
            if first_li:
                year_text = first_li.get_text(strip=True)
                year = int(year_text) if year_text.isdigit() else None

        rating_elem = container.find("span", class_="ipc-rating-star--rating")
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            try:
                rating = float(rating_text)
            except ValueError:
                rating = None

    return {
        "rank": rank,
        "title": title,
        "year": year,
        "rating": rating,
        "movie_id": movie_id,
    }


def parse_movies(html: str, limit: int = 250) -> list:
    """Extracts rank, title, release year, rating, and IMDb ID for each movie.

    Non-movie entries (nav links that share the same markup as movie titles,
    e.g. "Popular charts") are filtered out automatically.

    Args:
        html: Rendered page HTML, as returned by fetch_page_html.
        limit: Maximum number of title elements to consider (applied before
            non-movie entries are filtered out).

    Returns:
        A list of movie dicts (rank, title, year, rating, movie_id), ranked
        1..N in the order they appeared on the page after filtering.
    """
    soup = BeautifulSoup(html, "html.parser")
    title_elements = soup.find_all("h4", class_="ipc-title__text")

    logger.info(f"Found {len(title_elements)} title elements on the page")

    movies = []
    for elem in title_elements[:limit]:
        movie = _extract_movie(rank=0, elem=elem)  # rank re-assigned below
        if movie is not None:
            movies.append(movie)

    # Assign final rank only to entries that survived filtering
    for new_rank, movie in enumerate(movies, start=1):
        movie["rank"] = new_rank

    logger.info(f"Successfully parsed {len(movies)} movies (after filtering non-movie entries)")
    return movies
