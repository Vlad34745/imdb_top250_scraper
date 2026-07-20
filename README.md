# IMDb Top 250 Scraper

A Python web scraper that collects the IMDb Top 250 movies (rank, title, year, rating, and IMDb ID) and exports the results to a styled Excel report.

## 🛠 Tech Stack
- **Browser automation:** Selenium (headless Chrome) — used because the target page returns an empty response to plain HTTP requests (anti-bot protection), so a real browser engine is required to render and retrieve the page
- **HTML parsing:** BeautifulSoup4
- **Data handling & export:** Pandas, OpenPyXL
- **Driver management:** webdriver-manager (automatically downloads the correct ChromeDriver version)

## ✨ Features
- Bypasses basic anti-bot blocking by rendering the page through a real (headless) Chrome instance instead of raw HTTP requests
- Robust parsing using semantic CSS classes rather than auto-generated ones where possible, to reduce breakage when the site's styling changes
- Automatically filters out non-movie navigation links that share the same markup as movie entries (e.g. "Popular charts", "Movie news")
- Exports a clean, styled Excel report with a formatted header row and auto-sized columns

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

## 📐 Project Structure
```text
imdb_top250_scraper/
│
├── core/
│   └── parser.py     # Selenium page fetching + BeautifulSoup parsing logic
├── main.py             # Orchestrates fetching, parsing, and Excel export
├── requirements.txt
└── output/               # Generated Excel reports (not committed to git)
```

## ⚠️ Notes on scope and reliability
This project was built for educational and portfolio purposes to demonstrate a real, working scraping workflow — including handling anti-bot protection and adapting parsing logic when a site's markup changes. It scrapes a single public chart page and does not perform bulk or continuous scraping. As with any scraper, the parsing logic is tied to IMDb's current page structure and may need adjustment if the site's layout changes in the future.