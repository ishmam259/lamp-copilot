"""agents/llm.py: replay, record, budget guard and image preprocessing. Never calls OpenAI."""

import asyncio
import io
import json

import pytest
from PIL import Image

from app.agents import llm

ARGS = dict(component="extraction", prompt_version="extraction_v1", instructions="Read it.", text="invoice",
            schema_name="doc", schema={"type": "object"})


@pytest.fixture(autouse=True)
def offline(monkeypatch, tmp_path):
    """Replay mode, no key, recordings and spend log in a temp folder, OpenAI unreachable."""
    monkeypatch.setattr(llm.settings, "llm_mode", "replay")
    monkeypatch.setattr(llm.settings, "openai_api_key", "")
    monkeypatch.setattr(llm.settings, "llm_daily_budget_usd", 1.00)
    monkeypatch.setattr(llm, "REPLAY_DIR", tmp_path / "replay")
    monkeypatch.setattr(llm, "SPEND_LOG", tmp_path / "spend.log")

    def no_client():
        raise AssertionError("OpenAI client built in a test")

    monkeypatch.setattr(llm, "_client", no_client)


def _jpeg(w: int, h: int, exif_orientation: int | None = None) -> bytes:
    im = Image.new("RGB", (w, h), "white")
    out = io.BytesIO()
    if exif_orientation:
        exif = Image.Exif()
        exif[0x0112] = exif_orientation
        exif[0x010F] = "PhoneCam"
        im.save(out, format="JPEG", exif=exif)
    else:
        im.save(out, format="JPEG")
    return out.getvalue()


def test_replay_missing_fails_loudly():
    with pytest.raises(llm.ReplayMissing):
        asyncio.run(llm.structured_call(**ARGS, image=b"img"))


def test_record_then_replay(monkeypatch):
    monkeypatch.setattr(llm.settings, "openai_api_key", "sk-test")
    calls = []

    async def fake_openai(*a):
        calls.append(a)
        return {"total": 60000}, 2_000, 500

    monkeypatch.setattr(llm, "_call_openai", fake_openai)
    rec = asyncio.run(llm.structured_call(**ARGS, image=b"img", mode="record"))
    assert rec.mode == "live" and rec.data == {"total": 60000}
    saved = json.loads((llm.REPLAY_DIR / "extraction" / f"{rec.key}.json").read_text())
    assert saved["output"] == {"total": 60000} and saved["usage"]["input_tokens"] == 2_000

    rep = asyncio.run(llm.structured_call(**ARGS, image=b"img"))
    assert rep.mode == "replay" and rep.data == {"total": 60000} and len(calls) == 1
    assert llm.spent_today() == pytest.approx(llm.cost_usd(2_000, 500))


def test_cache_key_changes_with_each_input():
    base = llm.cache_key("m", "v1", "t", b"a")
    assert base == llm.cache_key("m", "v1", "t", b"a")
    assert len({base, llm.cache_key("m2", "v1", "t", b"a"), llm.cache_key("m", "v2", "t", b"a"),
                llm.cache_key("m", "v1", "u", b"a"), llm.cache_key("m", "v1", "t", b"b")}) == 5


def test_live_refused_without_key():
    with pytest.raises(llm.BudgetExceeded):
        asyncio.run(llm.structured_call(**ARGS, mode="live"))


def test_budget_guard(monkeypatch):
    monkeypatch.setattr(llm.settings, "openai_api_key", "sk-test")
    monkeypatch.setattr(llm.settings, "llm_daily_budget_usd", 0.001)
    assert llm.live_allowed()
    llm.record_spend("extraction", "gpt-6-luna", 10_000, 2_000)  # 0.001 + 0.001 USD
    assert llm.spent_today() == pytest.approx(0.002)
    assert not llm.live_allowed()
    with pytest.raises(llm.BudgetExceeded):
        asyncio.run(llm.structured_call(**ARGS, mode="live"))


def test_spend_log_format_matches_chat():
    llm.record_spend("extraction", "gpt-6-luna", 1_000_000, 0)
    parts = llm.SPEND_LOG.read_text().strip().split(",")
    assert len(parts) == 6 and parts[1:4] == ["extraction", "gpt-6-luna", "1000000"] and float(parts[5]) == 0.10


def test_preprocess_resizes_and_strips_metadata():
    out = llm.preprocess_image(_jpeg(4000, 3000, exif_orientation=1))
    with Image.open(io.BytesIO(out)) as im:
        assert im.format == "JPEG" and max(im.size) == 1600 and im.size == (1600, 1200)
        assert not im.getexif()


def test_preprocess_applies_exif_rotation():
    # orientation 6 = rotate 90 degrees: a landscape file is shown as portrait
    out = llm.preprocess_image(_jpeg(2000, 1000, exif_orientation=6))
    with Image.open(io.BytesIO(out)) as im:
        assert im.size == (800, 1600)


def test_preprocess_keeps_small_images_and_converts_png():
    png = io.BytesIO()
    Image.new("RGBA", (300, 200)).save(png, format="PNG")
    with Image.open(io.BytesIO(llm.preprocess_image(png.getvalue()))) as im:
        assert im.format == "JPEG" and im.size == (300, 200)
