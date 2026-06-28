"""Email rendering helpers."""

from django.template.loader import render_to_string
from premailer import transform


def render_inlined(template_name, context):
    """Render an HTML email template and inline its ``<style>`` CSS onto the
    elements (premailer). Mail clients strip external stylesheets and only
    unreliably honour ``<style>`` blocks, so inline ``style=""`` is what renders
    everywhere — this lets us author emails with a normal stylesheet and inline at
    send time. The ``<style>`` block is kept too, so ``@media`` rules (which can't
    be inlined) still drive responsive behaviour where supported.
    """
    html = render_to_string(template_name, context)
    return transform(
        html,
        keep_style_tags=True,
        disable_validation=True,  # don't let cssutils drop modern CSS (gradients)
        cssutils_logging_level="CRITICAL",
    )
