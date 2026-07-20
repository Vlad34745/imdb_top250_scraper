from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


def fetch_page_html(url: str, wait_seconds: int = 3, scroll_pause: float = 1.0) -> str:
    """
    Loads a page through headless Chrome (Selenium) and returns the rendered HTML.
    Scrolls down repeatedly to force lazy-loaded content (like the full
    IMDb Top 250 list) to render before capturing the final HTML.
    """
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        logger.info(f"Fetching page: {url}")
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
    finally:
        driver.quit()


def parse_movies(html: str, limit: int = 250) -> list:
    """
    Extracts rank, title, release year, rating, and IMDb ID for each movie
    from the IMDb Top 250 page HTML.
    """
    soup = BeautifulSoup(html, "html.parser")
    title_elements = soup.find_all("h4", class_="ipc-title__text")

    logger.info(f"Found {len(title_elements)} title elements on the page")

    movies = []
    for rank, elem in enumerate(title_elements[:limit], start=1):
        title = elem.get_text(strip=True)

        parent_link = elem.find_parent("a")
        href = parent_link["href"] if parent_link else None
        movie_id_match = re.search(r"/title/(tt\d+)/", href) if href else None
        movie_id = movie_id_match.group(1) if movie_id_match else None

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

        movies.append({
            "rank": rank,
            "title": title,
            "year": year,
            "rating": rating,
            "movie_id": movie_id,
        })

    # Filter out non-movie entries without an ID (nav links like "Popular charts")
    movies = [m for m in movies if m["movie_id"] is not None]

    # Re-number the rank since some entries may have been removed
    for new_rank, movie in enumerate(movies, start=1):
        movie["rank"] = new_rank

    logger.info(f"Successfully parsed {len(movies)} movies (after filtering non-movie entries)")
    return movies