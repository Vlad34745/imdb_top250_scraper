# IMDb Top 250 Scraper

![CI](https://github.com/Vlad34745/imdb_top250_scraper/actions/workflows/ci.yml/badge.svg)

A Python web scraper that collects the IMDb Top 250 movies (rank, title, year, rating, and IMDb ID) and exports the results to a styled Excel report.

## 🛠 Tech Stack
- **Browser automation:** Selenium (headless Chrome) — used because the target page returns an empty response to plain HTTP requests (anti-bot protection), so a real browser engine is required to render and retrieve the page
- **HTML parsing:** BeautifulSoup4
- **Data handling & export:** Pandas, OpenPyXL
- **Driver management:** webdriver-manager (automatically downloads the correct ChromeDriver version)
- **Testing:** pytest, pytest-cov
- **CI:** GitHub Actions (runs the test suite on every push/PR across Python 3.12–3.13 — the pinned `numpy` version in `requirements.txt` requires Python 3.12+)

## ✨ Features
- Bypasses basic anti-bot blocking by rendering the page through a real (headless) Chrome instance instead of raw HTTP requests
- Retries the page fetch automatically (with backoff) on transient network/driver failures instead of crashing on the first hiccup
- Uses incremental scrolling to reliably trigger the site's lazy-loaded content, ensuring all 250 entries are captured consistently on every run instead of relying on a fixed wait time
- Robust parsing using semantic CSS classes rather than auto-generated ones where possible, to reduce breakage when the site's styling changes
- Automatically filters out non-movie navigation links that share the same markup as movie entries (e.g. "Popular charts", "Movie news")
- Exports a clean, styled Excel report with a formatted header row, proper numeric types for year/rating, and auto-sized columns
- Configurable via CLI flags — no code edits needed to change the limit, output path, or timing

## 📋 Output columns
| Column | Description |
|---|---|
| Rank | Position in the Top 250 list |
| Title | Movie title |
| Year | Release year |
| Rating | IMDb rating (out of 10) |
| IMDb ID | Unique IMDb identifier (e.g. `tt0111161`), usable to build a direct link: `https://www.imdb.com/title/{IMDb ID}/` |

## 🚀 How to Run Locally

1. **Clone the repository:**
```bash
   git clone https://github.com/Vlad34745/imdb_top250_scraper.git
   cd imdb_top250_scraper
```

2. **Create and activate a virtual environment:**
```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
```

3. **Install dependencies:**
```bash
   pip install -r requirements.txt
```

4. **Run the scraper:**
```bash
   python main.py
```

5. **Output:**
   A file named `imdb_top250_<date>.xlsx` will be created in the `output/` folder.

### CLI options
```bash
python main.py --limit 50 --output output/top50.xlsx --wait-seconds 5 --max-retries 5
```
| Flag | Default | Description |
|---|---|---|
| `--url` | IMDb Top 250 URL | Chart URL to scrape |
| `--limit` | `250` | Max number of movies to keep |
| `--output` | `output/imdb_top250_<date>.xlsx` | Output file path |
| `--wait-seconds` | `3` | Initial wait after page load |
| `--scroll-pause` | `1.0` | Pause between scroll steps |
| `--max-retries` | `3` | Retries on fetch failure |

## 🧪 Testing
Unit tests cover the parsing logic (using a local HTML fixture — no live IMDb request needed) and the Excel export.
```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=core --cov-report=term-missing
```

## 📐 Project Structure
```text
imdb_top250_scraper/
│
├── core/
│   ├── parser.py         # Selenium page fetching (with retries) + BeautifulSoup parsing
│   └── exporter.py       # Styled Excel export
├── tests/
│   ├── fixtures/
│   │   └── sample_imdb.html
│   ├── test_parser.py
│   └── test_exporter.py
├── .github/workflows/ci.yml
├── main.py               # CLI entry point: orchestrates fetching, parsing, export
├── requirements.txt
├── requirements-dev.txt
└── output/               # Generated Excel reports (not committed to git)
```

## ⚠️ Notes on scope and reliability
This project was built for educational and portfolio purposes to demonstrate a real, working scraping workflow — including handling anti-bot protection, JavaScript-driven lazy loading, and adapting parsing logic when a site's markup changes. It scrapes a single public chart page and does not perform bulk or continuous scraping. As with any scraper, the parsing logic is tied to IMDb's current page structure (in particular the auto-generated `sc-a96da33f-0` container class) and may need adjustment if the site's layout changes in the future.