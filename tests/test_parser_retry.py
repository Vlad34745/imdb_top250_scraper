from unittest.mock import MagicMock

import pytest
from selenium.common.exceptions import WebDriverException

from core.parser import PageFetchError, fetch_page_html


def test_fetch_page_html_retries_then_succeeds(monkeypatch):
    failing_driver = MagicMock()
    failing_driver.get.side_effect = WebDriverException("connection refused")

    working_driver = MagicMock()
    working_driver.page_source = "<html>ok</html>"
    # execute_script returns the same mock value on every call, so the
    # "did the page height change?" check in fetch_page_html sees no
    # change and the scroll loop exits after a single iteration.

    call_count = {"n": 0}

    def fake_build_driver():
        call_count["n"] += 1
        return failing_driver if call_count["n"] == 1 else working_driver

    monkeypatch.setattr("core.parser._build_driver", fake_build_driver)
    monkeypatch.setattr("core.parser.time.sleep", lambda seconds: None)

    html = fetch_page_html("https://example.com", max_retries=3)

    assert html == "<html>ok</html>"
    assert call_count["n"] == 2  # failed once, succeeded on the second attempt


def test_fetch_page_html_raises_page_fetch_error_after_max_retries(monkeypatch):
    always_failing_driver = MagicMock()
    always_failing_driver.get.side_effect = WebDriverException("timed out")

    monkeypatch.setattr("core.parser._build_driver", lambda: always_failing_driver)
    monkeypatch.setattr("core.parser.time.sleep", lambda seconds: None)

    with pytest.raises(PageFetchError):
        fetch_page_html("https://example.com", max_retries=2)


def test_fetch_page_html_quits_driver_on_every_attempt(monkeypatch):
    failing_driver = MagicMock()
    failing_driver.get.side_effect = WebDriverException("boom")

    monkeypatch.setattr("core.parser._build_driver", lambda: failing_driver)
    monkeypatch.setattr("core.parser.time.sleep", lambda seconds: None)

    with pytest.raises(PageFetchError):
        fetch_page_html("https://example.com", max_retries=3)

    # driver.quit() must be called after every attempt to avoid leaking
    # headless Chrome processes, even when the attempt failed
    assert failing_driver.quit.call_count == 3
