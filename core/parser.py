from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging

from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


def fetch_page_html(url: str, wait_seconds: int = 3) -> str:
    """
    Завантажує сторінку через headless Chrome (Selenium) і повертає готовий HTML.
    Використовується замість простого requests, оскільки цільовий сайт
    блокує прості HTTP-запити антибот-захистом.
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
        html = driver.page_source
        logger.info(f"Successfully fetched {len(html)} characters")
        return html
    finally:
        driver.quit()


def parse_movies(html: str, limit: int = 250) -> list:
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

        # Батьківський контейнер, що об'єднує назву, рік і рейтинг цього фільму
        container = elem.find_parent("div", class_="sc-a96da33f-0") or elem.find_parent("li")

        year = None
        rating = None

        if container:
            metadata_div = container.find("div", class_="cli-title-metadata")
            if metadata_div:
                first_li = metadata_div.find("li")
                if first_li:
                    year = first_li.get_text(strip=True)

            rating_elem = container.find("span", class_="ipc-rating-star--rating")
            if rating_elem:
                rating = rating_elem.get_text(strip=True)

        movies.append({
            "rank": rank,
            "title": title,
            "year": year,
            "rating": rating,
            "movie_id": movie_id,
        })

    # Прибираємо "сміттєві" записи без ID фільму (навігаційні посилання типу "Popular charts")
    movies = [m for m in movies if m["movie_id"] is not None]

    # Перенумеровуємо ранг заново, оскільки частину записів могли прибрати
    for new_rank, movie in enumerate(movies, start=1):
        movie["rank"] = new_rank

    logger.info(f"Successfully parsed {len(movies)} movies (after filtering non-movie entries)")
    return movies