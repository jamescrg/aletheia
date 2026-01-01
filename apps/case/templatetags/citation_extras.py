"""
Template tags for enhancing legal citations in AI responses.
"""

import logging
import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)
register = template.Library()


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
def enhance_citations(html_content, citations_list):
    """
    Post-process rendered HTML to add verification badges to citations.

    Only adds badges to citations within the "Table of Authorities" section,
    which could be formatted as:
    - A <table> element
    - A list (<ul>/<ol>) after a "Table of Authorities" heading
    - Any content after a heading containing "authorities" or "citations"

    Args:
        html_content: The rendered HTML from markdown
        citations_list: List of citation dicts from verification

    Returns:
        Enhanced HTML with citation badges and links in the authorities section only
    """
    if not html_content or not citations_list:
        return html_content

    result = str(html_content)

    # Build a lookup of citations
    citation_lookup = {}
    for cit in citations_list:
        text = cit.get("original_text", "")
        if text:
            citation_lookup[text] = cit

    def enhance_section(section_html):
        """Add badges to citations within a section."""
        for original_text, citation_data in citation_lookup.items():
            if original_text not in section_html:
                continue

            badge = create_citation_badge(citation_data)
            if not badge:
                continue

            escaped_text = re.escape(original_text)
            pattern = f"({escaped_text})"
            section_html = re.sub(
                pattern, lambda m: f"{m.group(1)} {badge}", section_html, count=1
            )

        return section_html

    # Strategy 1: Look for a heading containing "authorities" or "citations"
    # and enhance everything after it
    heading_pattern = (
        r"(<h[1-6][^>]*>.*?"
        r"(?:table\s+of\s+)?(?:authorities|citations)"
        r".*?</h[1-6]>)"
        r"(.*?)(?=<h[1-6]|$)"
    )
    heading_match = re.search(heading_pattern, result, flags=re.IGNORECASE | re.DOTALL)

    if heading_match:
        # Found an authorities heading - enhance the content after it
        before = result[: heading_match.start(2)]
        section = heading_match.group(2)
        after = result[heading_match.end(2) :]

        enhanced_section = enhance_section(section)
        result = before + enhanced_section + after
    else:
        # Strategy 2: Fall back to enhancing within <table> elements only
        result = re.sub(
            r"(<table[^>]*>.*?</table>)",
            lambda m: enhance_section(m.group(1)),
            result,
            flags=re.DOTALL,
        )

    return mark_safe(result)


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
