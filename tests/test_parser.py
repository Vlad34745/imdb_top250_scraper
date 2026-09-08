from pathlib import Path

import pytest

from core.parser import parse_movies

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_imdb.html"


@pytest.fixture
def sample_html() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parses_correct_number_of_movies(sample_html):
    # The fixture has 3 real movies + 1 nav link that must be filtered out
    movies = parse_movies(sample_html)
    assert len(movies) == 3


def test_filters_out_non_movie_entries(sample_html):
    movies = parse_movies(sample_html)
    titles = [m["title"] for m in movies]
    assert "Popular charts" not in titles


def test_extracts_title_year_rating_and_id(sample_html):
    movies = parse_movies(sample_html)
    first = movies[0]
    assert first["title"] == "1. The Shawshank Redemption"
    assert first["year"] == 1994
    assert first["rating"] == 9.3
    assert first["movie_id"] == "tt0111161"


def test_reassigns_rank_after_filtering(sample_html):
    movies = parse_movies(sample_html)
    ranks = [m["rank"] for m in movies]
    assert ranks == [1, 2, 3]


def test_missing_rating_is_none_not_a_crash(sample_html):
    movies = parse_movies(sample_html)
    third = movies[2]
    assert third["movie_id"] == "tt0071562"
    assert third["rating"] is None


def test_respects_limit(sample_html):
    movies = parse_movies(sample_html, limit=2)
    assert len(movies) == 2


def test_empty_html_returns_empty_list():
    assert parse_movies("<html><body></body></html>") == []
