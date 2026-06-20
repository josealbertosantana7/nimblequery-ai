"""Aviation data-source tools tested with mocked HTTP (no real network calls)."""
import httpx

from app.tools.aviation import airports, faa, tracking, weather


class FakeResp:
    def __init__(self, text="", json_data=None, status=200):
        self.text = text
        self._json = json_data
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


def test_fetch_metar(monkeypatch):
    raw = "KAUS 010151Z 18010KT 10SM CLR 30/18 A2992"
    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp(text=raw))
    assert "KAUS" in weather.fetch_metar("kaus")


def test_fetch_metar_empty(monkeypatch):
    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp(text=""))
    assert "No current METAR" in weather.fetch_metar("ZZZZ")


def test_traffic_near(monkeypatch):
    states = [["abc", "UAL1   ", "US", 0, 0, -97.0, 30.0, 3000.0, False, 200.0]]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp(json_data={"states": states}))
    out = tracking.traffic_near(30.0, -97.0, 30)
    assert "UAL1" in out


def test_airport_info(monkeypatch):
    rows = [{
        "ident": "KAUS", "iata_code": "AUS", "name": "Austin-Bergstrom Intl",
        "type": "large_airport", "elevation_ft": "542", "municipality": "Austin",
        "iso_country": "US", "latitude_deg": "30.19", "longitude_deg": "-97.66",
    }]
    monkeypatch.setattr(airports, "_load", lambda: rows)
    assert "Austin-Bergstrom" in airports.airport_info("kaus")
    assert "No airport found" in airports.airport_info("ZZZZ")


def test_search_far(monkeypatch):
    data = {"results": [{
        "hierarchy_headings": {"section": "§ 61.89"},
        "full_text_excerpt": "A student pilot may not act as pilot in command ...",
    }]}
    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp(json_data=data))
    assert "61.89" in faa.search_far("student pilot privileges")


def test_notams_not_configured(monkeypatch):
    monkeypatch.setattr(faa.settings, "faa_notam_client_id", None)
    monkeypatch.setattr(faa.settings, "faa_notam_client_secret", None)
    assert "not configured" in faa.get_notams("KAUS")
