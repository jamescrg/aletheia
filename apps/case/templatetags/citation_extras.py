"""
Template tags for enhancing legal citations in AI responses.
"""

import logging
import re

from django import template
from django.urls import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)
register = template.Library()


VETTING_ICON = {
    "supports": ("icon-check", "citation-vetted-supports", "Case supports claim"),
    "partial": (
        "icon-minus",
        "citation-vetted-partial",
        "Case partially supports claim",
    ),
    "contradicts": (
        "icon-triangle-alert",
        "citation-vetted-contradicts",
        "Case contradicts claim",
    ),
    "unclear": ("icon-help-circle", "citation-vetted-unclear", "Case support unclear"),
}


def _vetting_modal_link(message_id, citation_index, icon_html):
    """Render an HTMX anchor that loads the per-citation vetting modal."""
    detail_url = reverse(
        "case:ai-citation-vetting-detail",
        args=[message_id, citation_index],
    )
    return (
        f'<a href="#" '
        f'hx-get="{escape(detail_url)}" '
        f'hx-target="#htmx-modal-container" hx-swap="innerHTML" '
        f"onclick=\"window.dispatchEvent(new CustomEvent('open-modal'));\">"
        f"{icon_html}"
        f"</a>"
    )


def create_vetting_badge(vetting, message_id, citation_index):
    """Render a badge for substantive Flash vetting of a single citation.

    Every state is a clickable chip that opens the vetting modal. The
    modal itself renders the current state (in-progress / completed /
    failed), so re-clicking a pending badge after the response updates
    shows the latest verdict.

    Returns an empty string if vetting hasn't been run (no vetting dict).
    """
    if not vetting:
        return ""

    status = vetting.get("status")

    if status in ("pending", "running"):
        title = "Checking whether the case supports the claim…"
        link = _vetting_modal_link(
            message_id, citation_index, '<i class="icon-loader spinning"></i>'
        )
        return (
            '<span class="citation-vetting citation-vetted-pending" '
            f'title="{escape(title)}">{link}</span>'
        )

    if status == "failed":
        err = vetting.get("error") or "Vetting failed"
        link = _vetting_modal_link(
            message_id, citation_index, '<i class="icon-circle-off"></i>'
        )
        return (
            '<span class="citation-vetting citation-vetted-failed" '
            f'title="{escape(err)}">{link}</span>'
        )

    if status == "completed":
        verdict = vetting.get("verdict") or "unclear"
        icon_class, badge_class, default_title = VETTING_ICON.get(
            verdict, VETTING_ICON["unclear"]
        )
        explanation = vetting.get("explanation") or default_title
        link = _vetting_modal_link(
            message_id, citation_index, f'<i class="{icon_class}"></i>'
        )
        return (
            f'<span class="citation-vetting {badge_class}" '
            f'title="{escape(explanation)}">{link}</span>'
        )

    return ""


def build_citation_lookup(citations):
    """
    Build a lookup dict from citation text to citation data.
    Normalizes citation text for matching.
    """
    lookup = {}
    for cit in citations:
        # Store by original text
        text = cit.get("original_text", "")
        if text:
            lookup[text.lower()] = cit
            # Also store normalized version if different
            normalized = cit.get("normalized")
            if normalized and normalized.lower() != text.lower():
                lookup[normalized.lower()] = cit
    return lookup


def create_citation_badge(citation_data):
    """
    Create HTML badge for a citation based on verification status.
    """
    is_valid = citation_data.get("is_valid")
    url = citation_data.get("url")
    source = citation_data.get("source", "")
    confidence = citation_data.get("confidence")
    case_name = citation_data.get("case_name")
    error = citation_data.get("error", "")

    # Check if this is a case name mismatch (hallucination)
    is_name_mismatch = is_valid is False and "mismatch" in error.lower()

    if is_valid is True and url:
        # Verified with link
        icon = '<i class="icon-check"></i>'
        badge_class = "citation-verified"
        if confidence is not None:
            title = f"Verified ({confidence:.0%} match) - {case_name}"
        else:
            title = f"Verified - {source}"
        link = (
            f'<a href="{escape(url)}" target="_blank" '
            f'rel="noopener" title="{escape(title)}">{icon}</a>'
        )
        return f'<span class="{badge_class}">{link}</span>'
    elif is_valid is True:
        # Verified but no link (shouldn't happen often)
        icon = '<i class="icon-check"></i>'
        badge_class = "citation-verified"
        return f'<span class="{badge_class}" title="Verified">{icon}</span>'
    elif is_name_mismatch and url:
        # Case name mismatch - likely hallucination, but link to actual case
        icon = '<i class="icon-triangle-alert"></i>'
        badge_class = "citation-unverified"
        title = error if error else "Case name mismatch"
        link = (
            f'<a href="{escape(url)}" target="_blank" '
            f'rel="noopener" title="{escape(title)}">{icon}</a>'
        )
        return f'<span class="{badge_class}">{link}</span>'
    elif is_valid is False and url:
        # Not verified but has search link
        icon = '<i class="icon-external-link"></i>'
        badge_class = "citation-search"
        title = f"{error} - Click to search" if error else "Click to search"
        link = (
            f'<a href="{escape(url)}" target="_blank" '
            f'rel="noopener" title="{escape(title)}">{icon}</a>'
        )
        return f'<span class="{badge_class}">{link}</span>'
    elif is_valid is False:
        # Not found / possibly hallucinated, no link
        icon = '<i class="icon-triangle-alert"></i>'
        badge_class = "citation-unverified"
        title = error if error else "Not verified"
        return f'<span class="{badge_class}" title="{escape(title)}">{icon}</span>'
    elif is_valid is None and url:
        # Unknown status but has search link (no API token configured)
        icon = '<i class="icon-external-link"></i>'
        badge_class = "citation-search"
        title = f"Search on {source}" if source else "Search citation"
        link = (
            f'<a href="{escape(url)}" target="_blank" '
            f'rel="noopener" title="{escape(title)}">{icon}</a>'
        )
        return f'<span class="{badge_class}">{link}</span>'
    else:
        # Unknown / not checked, no link
        return ""


@register.filter
def has_pending_vetting(message):
    """True if any case citation on this message is still being vetted."""
    from apps.case.ai.vetting import has_pending_vetting as _has_pending

    citations = getattr(message, "verified_citations", None) or []
    return _has_pending(citations)


@register.filter
def enhance_citations(html_content, message):
    """
    Post-process rendered HTML to add verification badges next to each
    inline citation occurrence.

    For every case citation on the message, find every occurrence of the
    citation's matched text (e.g. "410 U.S. 113") in the rendered HTML
    and inject a badge `<span>` immediately after it. The badge is the
    same shape used elsewhere — a Flash-vetting chip when vetting data
    is present, otherwise a plain verification badge.

    Args:
        html_content: The rendered HTML from markdown
        message: The Message object (supplies .verified_citations and .id
            so vetting badges can link to the detail modal)

    Returns:
        Enhanced HTML with inline citation badges
    """
    citations_list = getattr(message, "verified_citations", None) or []
    if not html_content or not citations_list:
        return html_content

    result = str(html_content)
    message_id = getattr(message, "id", None)

    # Walk citations in original order so we badge each one we have data
    # for. Only case citations get badges in this pass — statute badging
    # is intentionally out of scope for now.
    for idx, citation_data in enumerate(citations_list):
        if citation_data.get("citation_type") != "case":
            continue
        original_text = citation_data.get("original_text") or ""
        if not original_text:
            continue

        vetting = citation_data.get("vetting") or {}
        if vetting and message_id is not None:
            badge = create_vetting_badge(vetting, message_id, idx)
        else:
            badge = create_citation_badge(citation_data)

        if not badge:
            continue

        # Insert the badge after each occurrence of the citation text in
        # the HTML. The negative lookbehind for `="` keeps us out of
        # attribute values; in normal markdown-rendered prose citations
        # only appear in text nodes, so a regex pass over the full HTML
        # is safe and simple.
        pattern = re.compile(
            r'(?<![="\'])' + re.escape(original_text),
            flags=re.IGNORECASE,
        )

        def _insert(match, badge=badge):
            return match.group(0) + badge

        result = pattern.sub(_insert, result)

    return mark_safe(result)


@register.filter
def normalize_linebreaks(text):
    """
    Normalize line breaks in pre-formatted legal text from CourtListener.

    CourtListener text uses \\n\\n for ALL line breaks. We distinguish:
    - Paragraph breaks: \\n\\n followed by indentation (spaces)
    - Line wraps: \\n\\n followed directly by text (no indent)
    - Page numbers: form feed + number, or centered numbers (20+ leading spaces)

    Returns HTML with paragraphs wrapped in <p> tags and page numbers styled.

    Usage: {{ case_law.text|normalize_linebreaks }}
    """
    if not text:
        return text

    # Normalize different line ending styles
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    page_placeholder = "\x00PAGE\x00"

    # Mark page numbers that follow form feed characters
    # Form feed (\x0c) is a page break indicator in many court documents
    text = re.sub(
        r"\x0c\s*(\d{1,3})\s*\n",
        page_placeholder + r"\1" + page_placeholder + "\n",
        text,
    )

    # Mark centered page numbers (20+ leading spaces = centered on page)
    text = re.sub(
        r"\n\n[ ]{20,}(\d{1,3})[ ]*(?=\n)",
        "\n\n" + page_placeholder + r"\1" + page_placeholder,
        text,
    )

    # Remove any remaining form feeds
    text = text.replace("\x0c", "\n\n")

    # Preserve paragraph breaks (double newline followed by indentation)
    # These are real paragraph starts with 4+ spaces of indentation
    para_placeholder = "\x00PARA\x00"
    text = re.sub(r"\n\n([ ]{4,})", para_placeholder + r"\1", text)

    # Also preserve breaks before centered text (like headers)
    # These have significant leading whitespace
    text = re.sub(r"\n\n([ ]{10,})", para_placeholder + r"\1", text)

    # Convert remaining double newlines (line wraps) to single space
    text = re.sub(r"\n\n", " ", text)

    # Convert any remaining single newlines to spaces
    text = text.replace("\n", " ")

    # Collapse multiple spaces into one
    text = re.sub(r"  +", " ", text)

    # Restore paragraph breaks
    text = text.replace(para_placeholder, "\n\n")

    # Restore page numbers with marker
    text = re.sub(
        page_placeholder + r"(\d{1,3})" + page_placeholder,
        r"\n\n:::PAGE:::\1:::ENDPAGE:::\n\n",
        text,
    )

    # Split into paragraphs and wrap in <p> tags
    paragraphs = text.strip().split("\n\n")
    html_parts = []

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Check if this is a page number
        page_match = re.match(r":::PAGE:::(\d{1,3}):::ENDPAGE:::", para)
        if page_match:
            page_num = page_match.group(1)
            html_parts.append(f'<p class="page-number">{escape(page_num)}</p>')
        else:
            html_parts.append(f"<p>{escape(para)}</p>")

    return mark_safe("\n".join(html_parts))


@register.inclusion_tag("case/ai/citations-summary.html")
def citations_summary(citations_list):
    """
    Render a summary of verified citations.

    Usage: {% citations_summary verified_citations %}
    """
    if not citations_list:
        return {"citations": [], "has_citations": False}

    verified = [c for c in citations_list if c.get("is_valid") is True]
    unverified = [c for c in citations_list if c.get("is_valid") is False]
    cases = [c for c in citations_list if c.get("citation_type") == "case"]
    statutes = [c for c in citations_list if c.get("citation_type") == "statute"]

    return {
        "citations": citations_list,
        "has_citations": bool(citations_list),
        "verified_count": len(verified),
        "unverified_count": len(unverified),
        "case_count": len(cases),
        "statute_count": len(statutes),
        "verified": verified,
        "unverified": unverified,
    }
