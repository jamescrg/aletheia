"""Template filters for invoicing display."""

import re

from django import template
from django.utils.html import conditional_escape, format_html

register = template.Library()

# Trailing legal-entity designations, most-specific first so e.g. "PLLC" isn't
# split into "P" + "LLC". A separator (comma/space) is required before the
# suffix, so a name like "...Spa" or "Tobacco" is never mistaken for one.
_ENTITY_RE = re.compile(
    r"^(.*\S)([\s,]+)("
    r"P\.?L\.?L\.?C\.?|P\.?L\.?C\.?|L\.?L\.?C\.?|L\.?L\.?P\.?|L\.?P\.?A\.?|"
    r"P\.?C\.?|P\.?A\.?|Chartered"
    r")\s*$",
    re.IGNORECASE,
)


@register.filter
def firm_entity(name):
    """Wrap a trailing legal-entity designation (LLC, PLLC, P.C., LLP, PA, …) in
    ``<span class="firm-suffix">`` so it can be styled (e.g. smaller). The name is
    HTML-escaped; names with no recognized suffix pass straight through. Returns
    safe HTML."""
    if not name:
        return ""
    m = _ENTITY_RE.match(str(name).strip())
    if not m:
        return conditional_escape(name)
    base, sep, suffix = m.groups()
    return format_html('{}{}<span class="firm-suffix">{}</span>', base, sep, suffix)
