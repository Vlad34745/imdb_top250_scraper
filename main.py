import argparse
import logging
import sys
from datetime import datetime

from core.exporter import save_to_excel
from core.parser import PageFetchError, fetch_page_html, parse_movies

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

IMDB_URL = "https://www.imdb.com/chart/top/"
OUTPUT_DIR = "output"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape the IMDb Top 250 chart into an Excel file.")
    parser.add_argument("--url", default=IMDB_URL, help="IMDb chart URL to scrape (default: Top 250)")
    parser.add_argument("--limit", type=int, default=250, help="Max number of movies to keep (default: 250)")
    parser.add_argument(
        "--output",
        default=None,
        help="Output .xlsx path (default: output/imdb_top250_<date>.xlsx)",
    )
    parser.add_argument("--wait-seconds", type=int, default=3, help="Initial page-load wait (default: 3)")
    parser.add_argument("--scroll-pause", type=float, default=1.0, help="Pause between scrolls (default: 1.0)")
    parser.add_argument("--max-retries", type=int, default=3, help="Retries on fetch failure (default: 3)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        html = fetch_page_html(
            args.url,
            wait_seconds=args.wait_seconds,
            scroll_pause=args.scroll_pause,
            max_retries=args.max_retries,
        )
    except PageFetchError:
        logger.error("Could not fetch the page after retries. Aborting.", exc_info=True)
        return 1

    movies = parse_movies(html, limit=args.limit)

    if not movies:
        logger.warning("No movies were parsed. Nothing to save.")
        return 1

    if args.output:
        filepath = args.output
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filepath = f"{OUTPUT_DIR}/imdb_top250_{timestamp}.xlsx"

    try:
        save_to_excel(movies, filepath)
    except Exception:
        logger.error(f"Failed to save results to {filepath}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
