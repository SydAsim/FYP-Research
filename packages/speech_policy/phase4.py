"""Pure playback and repair rules; client acknowledgements are exposure proxies."""

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any
from zoneinfo import ZoneInfo


class AudioState(StrEnum):
    GENERATED = "GENERATED"
    QUEUED = "QUEUED"
    PUBLISHED = "PUBLISHED"
    STARTED = "STARTED"
    STOPPED = "STOPPED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class SegmentClass(StrEnum):
    PROGRESS = "PROGRESS"
    UNCERTAINTY = "UNCERTAINTY"
    OUTCOME = "OUTCOME"
    REPAIR = "REPAIR"


@dataclass(frozen=True)
class Exposure:
    played_ms: int
    last_frame: int
    last_word_index: int

    @property
    def acknowledged(self) -> bool:
        return self.played_ms > 0 or self.last_frame > 0 or self.last_word_index > 0


def validate_progress(
    previous: Exposure, incoming: Exposure, duration_ms: int, frame_count: int, word_count: int
) -> None:
    if min(incoming.played_ms, incoming.last_frame, incoming.last_word_index) < 0:
        raise ValueError("Playback progress cannot be negative")
    if (
        incoming.played_ms < previous.played_ms
        or incoming.last_frame < previous.last_frame
        or incoming.last_word_index < previous.last_word_index
    ):
        raise ValueError("Playback progress cannot move backward")
    if (
        incoming.played_ms > duration_ms
        or incoming.last_frame > frame_count
        or incoming.last_word_index > word_count
    ):
        raise ValueError("Playback progress exceeds the generated segment")


def exposed_span(segment: dict[str, Any]) -> dict[str, Any]:
    timeline = segment["word_timeline_json"] or []
    count = min(segment["last_word_index"], len(timeline))
    return {
        "played_ms": segment["last_played_ms"],
        "last_frame": segment["last_frame"],
        "last_word_index": count,
        "words": [item["word"] for item in timeline[:count]],
        "content_hash": segment["content_hash"],
        "audio_hash": segment["audio_hash"],
    }


def repair_capable(research_arm: str | None) -> bool:
    """Product and P2 own durable repair; all declared baselines/P1 ablate it."""
    return research_arm is None or research_arm == "P2"


def decisive_word_count(text: str) -> int | None:
    """Template semantic boundary, NOT acoustic alignment or proof of hearing."""
    for index, word in enumerate(text.split(), 1):
        if word.strip(".,:;").lower() in ("confirmed", "moved", "cancelled", "compensated"):
            return index
    return None


def semantic_start(text: str) -> datetime | None:
    match = re.search(r"(\d{1,2}:\d{2}) (AM|PM) on (\d{4}-\d{2}-\d{2}) \(([^)]+)\)", text)
    if match is None:
        return None
    clock, period, day, zone = match.groups()
    return datetime.strptime(f"{day} {clock} {period}", "%Y-%m-%d %I:%M %p").replace(
        tzinfo=ZoneInfo(zone)
    )


def decisive_exposure(segment: dict[str, Any]) -> bool | None:
    timeline = segment.get("word_timeline_json") or []
    text = segment.get("segment_text") or " ".join(item["word"] for item in timeline)
    boundary = decisive_word_count(text)
    exposure = Exposure(
        segment["last_played_ms"], segment["last_frame"], segment["last_word_index"]
    )
    if not exposure.acknowledged:
        return False
    if not timeline or boundary is None or boundary > len(timeline):
        return None
    if exposure.last_word_index < boundary:
        return False
    end = timeline[boundary - 1].get("end_ms")
    if end is None:
        return None
    return bool(exposure.played_ms >= end and exposure.last_frame >= end * 16)


def incompatible_exposure(segment: dict[str, Any], desired_state: dict[str, Any]) -> bool | None:
    """Compare only semantic predicates whose words have been acknowledged."""
    text = segment.get("segment_text", "")
    old = semantic_start(text)
    target = desired_state.get("requested_start")
    if old is None or not target:
        return None
    new = datetime.fromisoformat(target).astimezone(ZoneInfo(desired_state["timezone"]))
    words = text.split()
    boundaries: list[int] = []
    if old.time() != new.time():
        boundaries.extend(i for i, w in enumerate(words, 1) if w in ("AM", "PM"))
    if old.date() != new.date():
        boundaries.extend(i for i, w in enumerate(words, 1) if w == old.date().isoformat())
    if str(old.tzinfo) != desired_state["timezone"]:
        boundaries.append(len(words))
    if not boundaries:
        return False
    timeline = segment.get("word_timeline_json") or []
    for boundary in boundaries:
        if len(timeline) < boundary or "end_ms" not in timeline[boundary - 1]:
            return None
        end = timeline[boundary - 1]["end_ms"]
        if (
            segment["last_word_index"] >= boundary
            and segment["last_played_ms"] >= end
            and segment["last_frame"] >= end * 16
        ):
            return True
    return False


def needs_repair(
    segment: dict[str, Any], triggering_revision: int, desired_state: dict[str, Any] | None = None
) -> bool:
    if desired_state is not None:
        if incompatible_exposure(segment, desired_state) is not True:
            return False
    return (
        segment["segment_class"] in (SegmentClass.OUTCOME, SegmentClass.REPAIR)
        and segment["intent_revision"] < triggering_revision
        and decisive_exposure(segment) is True
    )


def repair_text(corrected_claim_text: str) -> str:
    if not corrected_claim_text.strip():
        raise ValueError("A verified corrected claim is required")
    return "Correction: my earlier confirmation was outdated. " + corrected_claim_text
