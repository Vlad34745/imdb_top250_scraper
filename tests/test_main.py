import sys

import main as main_module
from core.parser import PageFetchError

FAKE_MOVIES = [
    {"rank": 1, "title": "The Shawshank Redemption", "year": 1994, "rating": 9.3, "movie_id": "tt0111161"},
]


def test_main_success_saves_movies_and_returns_zero(monkeypatch, tmp_path):
    monkeypatch.setattr(main_module, "fetch_page_html", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(main_module, "parse_movies", lambda html, limit: FAKE_MOVIES)

    saved = {}

    def fake_save(movies, filepath):
        saved["movies"] = movies
        saved["filepath"] = filepath

    monkeypatch.setattr(main_module, "save_to_excel", fake_save)

    output_path = str(tmp_path / "out.xlsx")
    monkeypatch.setattr(sys, "argv", ["main.py", "--output", output_path])

    exit_code = main_module.main()

    assert exit_code == 0
    assert saved["filepath"] == output_path
    assert saved["movies"] == FAKE_MOVIES


def test_main_returns_one_when_fetch_fails(monkeypatch):
    def raise_error(*a, **k):
        raise PageFetchError("boom")

    monkeypatch.setattr(main_module, "fetch_page_html", raise_error)
    monkeypatch.setattr(sys, "argv", ["main.py"])

    assert main_module.main() == 1


def test_main_returns_one_when_no_movies_parsed(monkeypatch):
    monkeypatch.setattr(main_module, "fetch_page_html", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(main_module, "parse_movies", lambda html, limit: [])
    monkeypatch.setattr(sys, "argv", ["main.py"])

    assert main_module.main() == 1


def test_main_returns_one_when_save_fails(monkeypatch):
    monkeypatch.setattr(main_module, "fetch_page_html", lambda *a, **k: "<html></html>")
    monkeypatch.setattr(main_module, "parse_movies", lambda html, limit: FAKE_MOVIES)

    def fake_save(movies, filepath):
        raise OSError("disk full")

    monkeypatch.setattr(main_module, "save_to_excel", fake_save)
    monkeypatch.setattr(sys, "argv", ["main.py"])

    assert main_module.main() == 1


def test_main_passes_cli_args_through_to_fetch(monkeypatch):
    captured = {}

    def fake_fetch(url, wait_seconds, scroll_pause, max_retries):
        captured["url"] = url
        captured["wait_seconds"] = wait_seconds
        captured["scroll_pause"] = scroll_pause
        captured["max_retries"] = max_retries
        return "<html></html>"

    monkeypatch.setattr(main_module, "fetch_page_html", fake_fetch)
    monkeypatch.setattr(main_module, "parse_movies", lambda html, limit: FAKE_MOVIES)
    monkeypatch.setattr(main_module, "save_to_excel", lambda movies, filepath: None)
    monkeypatch.setattr(
        sys,
        "argv",
        ["main.py", "--url", "https://example.com/chart", "--wait-seconds", "5", "--max-retries", "7"],
    )

    main_module.main()

    assert captured["url"] == "https://example.com/chart"
    assert captured["wait_seconds"] == 5
    assert captured["max_retries"] == 7