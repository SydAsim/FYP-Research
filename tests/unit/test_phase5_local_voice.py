"""Safety checks for local voice endpointing and typed intent grounding."""

import asyncio
import struct
from datetime import UTC, datetime, timedelta, tzinfo
from typing import Self
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest

from apps.voice_worker import offline_adapters
from apps.voice_worker.live_agent import TurnSegmenter, pcm_wav
from apps.voice_worker.offline_adapters import AppointmentContext, LocalLlamaIntent, NeedDetails


def _context(start: datetime | None = None) -> AppointmentContext:
    return AppointmentContext(
        ticket_id=uuid4(),
        appointment_id=uuid4() if start else None,
        timezone="Asia/Karachi",
        current_start=start,
        current_end=start + timedelta(hours=1) if start else None,
    )


def test_segmenter_waits_for_speech_then_closes_on_silence() -> None:
    segmenter = TurnSegmenter()
    voiced = struct.pack("<320h", *([2500] * 320))
    silent = bytes(640)
    for _ in range(15):
        assert segmenter.push(voiced) is None
    final: bytes | None = None
    for _ in range(35):
        final = segmenter.push(silent)
    assert final is not None
    assert pcm_wav(final).startswith(b"RIFF")
    assert segmenter.finish() is None


def test_initial_time_without_date_never_reaches_model() -> None:
    intent = LocalLlamaIntent("http://local-model", _context())

    async def check() -> None:
        with pytest.raises(NeedDetails, match="appointment date"):
            await intent.propose("book maintenance at three pm")

    asyncio.run(check())


def test_typed_initial_proposal_binds_server_ticket(monkeypatch: pytest.MonkeyPatch) -> None:
    context = _context()
    intent = LocalLlamaIntent("http://local-model", context)
    future = datetime.now(ZoneInfo(context.timezone)) + timedelta(days=30)
    start = future.replace(hour=15, minute=0, second=0, microsecond=0)

    def complete(_self: LocalLlamaIntent, _transcript: str, _grounded: datetime) -> tuple[str, str]:
        return "prompt", f'{{"status":"READY","requested_start":"{start.isoformat()}"}}'

    monkeypatch.setattr(LocalLlamaIntent, "_complete", complete)
    proposal = asyncio.run(intent.propose(f"book maintenance on {start.date()} at three pm"))
    assert proposal.desired_state["ticket_id"] == str(context.ticket_id)
    assert proposal.desired_state["appointment_id"] is None
    assert proposal.desired_state["requested_start"] == start.isoformat()
    assert proposal.raw_output is not None


def test_time_only_correction_retains_current_date(monkeypatch: pytest.MonkeyPatch) -> None:
    zone = ZoneInfo("Asia/Karachi")
    current = (datetime.now(zone) + timedelta(days=30)).replace(
        hour=15, minute=0, second=0, microsecond=0
    )
    context = _context(current)
    intent = LocalLlamaIntent("http://local-model", context)
    corrected_start = current.replace(hour=16)

    def complete(_self: LocalLlamaIntent, _transcript: str, _grounded: datetime) -> tuple[str, str]:
        return "prompt", f'{{"status":"READY","requested_start":"{corrected_start.isoformat()}"}}'

    monkeypatch.setattr(LocalLlamaIntent, "_complete", complete)
    proposal = asyncio.run(intent.propose("actually make that four pm"))
    corrected = datetime.fromisoformat(proposal.desired_state["requested_start"])
    assert corrected.date() == current.date()
    assert corrected.hour == 16
    assert proposal.desired_state["appointment_id"] == str(context.appointment_id)


def test_model_hallucinated_date_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: tzinfo | None = None) -> Self:
            fixed = cls(2026, 10, 1, 12, tzinfo=UTC)
            return fixed.astimezone(tz) if tz is not None else fixed.replace(tzinfo=None)

    monkeypatch.setattr(offline_adapters, "datetime", FrozenDateTime)
    context = _context()
    intent = LocalLlamaIntent("http://local-model", context)

    def complete(_self: LocalLlamaIntent, _transcript: str, _grounded: datetime) -> tuple[str, str]:
        return "prompt", '{"status":"READY","requested_start":"2024-01-01T15:00:00+05:00"}'

    monkeypatch.setattr(LocalLlamaIntent, "_complete", complete)
    with pytest.raises(NeedDetails, match="model disagreed"):
        asyncio.run(
            intent.propose("book maintenance on October third twenty twenty six at three pm")
        )
