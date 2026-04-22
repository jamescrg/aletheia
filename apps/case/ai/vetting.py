"""
Substantive citation vetting for AI chat responses.

After citations are verified (case-name + CourtListener match), this module
launches a Gemini Flash job per cited case to evaluate whether the case
actually supports what the AI claims. Each job receives the full AI response,
the specific case being evaluated, and the case's opinion text, and returns a
structured verdict that is written back into Message.verified_citations.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from django.db import transaction

from apps.case.courtlistener import fetch_case_by_citation

from .gemini_client import send_to_gemini

logger = logging.getLogger(__name__)

# How many citations to vet in parallel. Each job makes one Flash call plus
# one CourtListener opinion fetch, both of which spend most of their time
# waiting on network, so a small thread pool is fine.
VETTING_MAX_WORKERS = 4

# Cap the opinion text fed to Flash. Most opinions fit comfortably; extremely
# long ones (50k+ words) just get truncated. Flash still judges the start of
# the opinion which usually contains the holding.
OPINION_TEXT_LIMIT = 120_000  # characters

# Terminal and non-terminal vetting status values used across the app.
TERMINAL_STATUSES = {"completed", "failed"}

VETTING_SYSTEM_PROMPT = """\
You vet legal citations. Given (1) an AI-generated legal response, \
(2) a specific case the AI cites, and (3) the opinion text of that case, \
determine what the AI is using the case for and whether the opinion \
supports that use.

Return ONLY a JSON object with this exact shape:
{
  "claim": "<what the AI is using this case for, <= 200 chars>",
  "verdict": "supports" | "partial" | "contradicts" | "unclear",
  "explanation": "<1-2 sentence rationale, <= 200 chars>",
  "quote": "<verbatim pull-quote from the opinion, <= 400 chars, or empty string>"
}

Rules:
- "supports": the opinion clearly backs the AI's use of the case.
- "partial": the opinion supports part of the claim but not all, or supports
  it only with qualifications the AI omitted.
- "contradicts": the opinion says the opposite, or was overruled/limited
  in a way that undermines the AI's use.
- "unclear": the opinion does not clearly address the claim either way, or
  the opinion text is insufficient to tell.
- The pull-quote must be copied verbatim from the opinion text. If no
  suitable quote exists, return an empty string.
- Return ONLY the JSON object, no other text, no markdown fences."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_case_citation(entry: dict) -> bool:
    return entry.get("citation_type") == "case"


def _build_user_prompt(response_text: str, citation: dict, opinion_text: str) -> str:
    case_name = citation.get("case_name") or citation.get("case_name_ai") or "(unknown)"
    cite_str = citation.get("normalized") or citation.get("original_text") or ""
    return (
        f"## Response being evaluated\n{response_text}\n\n"
        f"## Case to evaluate\n{case_name} — {cite_str}\n\n"
        f"## Opinion text\n{opinion_text}"
    )


def _parse_vetting_response(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = [ln for ln in stripped.split("\n") if not ln.strip().startswith("```")]
        stripped = "\n".join(lines)
    data = json.loads(stripped)
    verdict = data.get("verdict", "unclear")
    if verdict not in ("supports", "partial", "contradicts", "unclear"):
        verdict = "unclear"
    return {
        "claim": (data.get("claim") or "")[:400],
        "verdict": verdict,
        "explanation": (data.get("explanation") or "")[:400],
        "quote": (data.get("quote") or "")[:600],
    }


def vet_single_citation(response_text: str, citation: dict) -> dict:
    """Run a single Flash vetting call for one citation.

    Returns a vetting dict in the shape stored on each citation entry. Always
    returns a dict — failures produce {"status": "failed", "error": ...}
    rather than raising.
    """
    cite_str = citation.get("normalized") or citation.get("original_text") or ""
    if not cite_str:
        return {
            "status": "failed",
            "error": "Missing citation text",
            "updated_at": _now_iso(),
        }

    try:
        case = fetch_case_by_citation(cite_str)
    except Exception as exc:
        logger.exception("Vetting CourtListener fetch failed for %s", cite_str)
        return {
            "status": "failed",
            "error": f"Fetch failed: {exc}",
            "updated_at": _now_iso(),
        }

    if not case.get("found"):
        return {
            "status": "failed",
            "error": case.get("error") or "Opinion text unavailable",
            "updated_at": _now_iso(),
        }

    opinion_text = (case.get("text") or "")[:OPINION_TEXT_LIMIT]
    if not opinion_text.strip():
        return {
            "status": "failed",
            "error": "Opinion text empty",
            "updated_at": _now_iso(),
        }

    prompt = _build_user_prompt(response_text, citation, opinion_text)
    try:
        response_text_out, _, _ = send_to_gemini(
            system_context=VETTING_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            model="gemini-2.5-flash",
        )
    except Exception as exc:
        logger.exception("Vetting Flash call failed for %s", cite_str)
        return {
            "status": "failed",
            "error": f"Flash failed: {exc}",
            "updated_at": _now_iso(),
        }

    try:
        parsed = _parse_vetting_response(response_text_out)
    except Exception as exc:
        logger.warning("Could not parse vetting response for %s: %s", cite_str, exc)
        return {
            "status": "failed",
            "error": "Could not parse Flash response",
            "updated_at": _now_iso(),
        }

    return {"status": "completed", "updated_at": _now_iso(), **parsed}


def _write_vetting_result(message_id: int, index: int, result: dict) -> None:
    """Atomically merge a per-citation vetting result into Message.verified_citations."""
    from .models import Message

    with transaction.atomic():
        msg = Message.objects.select_for_update().get(pk=message_id)
        citations = list(msg.verified_citations or [])
        if 0 <= index < len(citations):
            entry = dict(citations[index])
            existing = dict(entry.get("vetting") or {})
            existing.update(result)
            entry["vetting"] = existing
            citations[index] = entry
            msg.verified_citations = citations
            msg.save(update_fields=["verified_citations"])


def seed_pending_vetting(message) -> bool:
    """Mark all case citations on a message as vetting pending.

    Returns True if any case citations were seeded (meaning vetting is worth
    running); False if the message has no case citations.
    """
    citations = list(message.verified_citations or [])
    changed = False
    for i, entry in enumerate(citations):
        if not _is_case_citation(entry):
            continue
        new_entry = dict(entry)
        new_entry["vetting"] = {
            "status": "pending",
            "verdict": None,
            "claim": None,
            "explanation": None,
            "quote": None,
            "error": None,
            "updated_at": _now_iso(),
        }
        citations[i] = new_entry
        changed = True
    if changed:
        message.verified_citations = citations
        message.save(update_fields=["verified_citations"])
    return changed


def has_pending_vetting(citations: list) -> bool:
    """True if any case citation is still in a non-terminal vetting state."""
    for entry in citations or []:
        if not _is_case_citation(entry):
            continue
        vetting = entry.get("vetting") or {}
        status = vetting.get("status")
        if status and status not in TERMINAL_STATUSES:
            return True
    return False


def process_citation_vetting(message_id: int) -> None:
    """Background entry point: vet every case citation on a message in parallel.

    Expects the message to already have pending vetting entries seeded by
    `seed_pending_vetting`. Intended to be run in a daemon thread.
    """
    from .models import Message

    try:
        message = Message.objects.get(pk=message_id)
    except Message.DoesNotExist:
        logger.error("process_citation_vetting: message %s not found", message_id)
        return

    response_text = message.content or ""
    citations = list(message.verified_citations or [])

    jobs = [
        (i, entry)
        for i, entry in enumerate(citations)
        if _is_case_citation(entry)
        and (entry.get("vetting") or {}).get("status") == "pending"
    ]

    if not jobs:
        return

    logger.info(
        "Starting citation vetting for message %s: %d case citation(s)",
        message_id,
        len(jobs),
    )

    # Mark everything as running up front so the UI shows activity even if
    # workers are queued behind the bounded pool.
    for index, _ in jobs:
        _write_vetting_result(
            message_id, index, {"status": "running", "updated_at": _now_iso()}
        )

    def _worker(index: int, entry: dict) -> None:
        try:
            result = vet_single_citation(response_text, entry)
        except Exception as exc:
            logger.exception(
                "Unhandled vetting error for message %s citation %s",
                message_id,
                index,
            )
            result = {"status": "failed", "error": str(exc), "updated_at": _now_iso()}
        _write_vetting_result(message_id, index, result)

    with ThreadPoolExecutor(max_workers=VETTING_MAX_WORKERS) as pool:
        for index, entry in jobs:
            pool.submit(_worker, index, entry)

    logger.info("Citation vetting complete for message %s", message_id)
