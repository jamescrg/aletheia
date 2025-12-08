"""
Views for AI chat within case analysis.
"""

import logging
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from apps.case.documents.get_document_data import get_selected_matter
from apps.case.models import Fact, Highlight
from apps.outlines.models import Outline

from .anthropic_client import send_to_claude
from .context import assemble_matter_context
from .gemini_client import send_to_gemini
from .models import Conversation, Message


def send_to_llm(llm: str, system_context: str, messages: list[dict]):
    """Route to the appropriate LLM based on conversation setting."""
    if llm == "gemini-flash":
        return send_to_gemini(system_context, messages, model="gemini-2.5-flash")
    elif llm == "gemini-pro":
        return send_to_gemini(system_context, messages, model="gemini-2.5-pro")
    return send_to_claude(system_context, messages)


logger = logging.getLogger(__name__)


@login_required
def ai_index(request):
    """Main AI view - list of conversations."""
    matter, matters = get_selected_matter(request)

    if not matter:
        return render(
            request,
            "case/ai/main.html",
            {
                "app": "documents",
                "subapp": "ai",
                "matter": None,
                "matters": matters,
                "conversations": [],
            },
        )

    conversations = Conversation.objects.filter(matter=matter, user=request.user)

    context = {
        "app": "documents",
        "subapp": "ai",
        "matter": matter,
        "matters": matters,
        "conversations": conversations,
    }

    return render(request, "case/ai/main.html", context)


@login_required
def ai_list(request):
    """Return conversation list partial (for HTMX refresh)."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return render(request, "case/ai/list.html", {"conversations": []})

    conversations = Conversation.objects.filter(matter=matter, user=request.user)

    return render(
        request,
        "case/ai/list.html",
        {
            "conversations": conversations,
            "matter": matter,
        },
    )


@login_required
def conversation_view(request, conv_id):
    """Standalone full-height view for a single conversation."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return redirect("case:ai-index")

    conversation = get_object_or_404(
        Conversation, pk=conv_id, matter=matter, user=request.user
    )

    messages = conversation.messages.all()

    context = {
        "matter": matter,
        "conversation": conversation,
        "messages": messages,
    }

    return render(request, "case/ai/conversation-standalone.html", context)


@login_required
def new_conversation_view(request):
    """Standalone view for a new (unsaved) conversation."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return redirect("case:ai-index")

    # Get LLM from query parameter
    llm = request.GET.get("llm", "claude")
    if llm not in ["claude", "gemini-flash", "gemini-pro"]:
        llm = "claude"

    # Create a dummy conversation object for template (not saved)
    conversation = Conversation(
        matter=matter,
        user=request.user,
        title="New Conversation",
        llm=llm,
    )

    context = {
        "matter": matter,
        "conversation": conversation,
        "messages": [],
        "is_new": True,
        "llm": llm,
    }

    return render(request, "case/ai/conversation-standalone.html", context)


@login_required
def message_list(request):
    """Return message list partial (for HTMX refresh)."""
    matter, _ = get_selected_matter(request)
    conversation_id = request.GET.get("conversation_id")

    if not matter:
        return render(request, "case/ai/messages.html", {"messages": []})

    if conversation_id:
        conversation = get_object_or_404(
            Conversation, pk=conversation_id, matter=matter, user=request.user
        )
    else:
        conversation = Conversation.objects.filter(
            matter=matter, user=request.user
        ).first()

    messages = conversation.messages.all() if conversation else []

    return render(
        request,
        "case/ai/messages.html",
        {
            "messages": messages,
            "conversation": conversation,
            "matter": matter,
        },
    )


@login_required
def send_message(request):
    """Handle user message submission and get AI response."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return HttpResponse(status=400)

    if request.method != "POST":
        return HttpResponse(status=405)

    user_message = request.POST.get("message", "").strip()
    conversation_id = request.POST.get("conversation_id")
    llm = request.POST.get("llm", "claude")

    if not user_message:
        return HttpResponse(status=400)

    # Validate llm
    if llm not in ["claude", "gemini-flash", "gemini-pro"]:
        llm = "claude"

    # Get or create conversation
    is_new = False
    if conversation_id:
        conversation = get_object_or_404(
            Conversation, pk=conversation_id, matter=matter, user=request.user
        )
    else:
        # Create conversation on first message
        title = user_message[:50]
        if len(user_message) > 50:
            title += "..."
        conversation = Conversation.objects.create(
            matter=matter, user=request.user, title=title, llm=llm
        )
        is_new = True

    # Update title if this is first message and title is default
    if not is_new and conversation.title == "New Conversation":
        conversation.title = user_message[:50]
        if len(user_message) > 50:
            conversation.title += "..."
        conversation.save()

    # Save user message
    Message.objects.create(conversation=conversation, role="user", content=user_message)

    # Assemble context and get AI response
    context_text = assemble_matter_context(matter, user=request.user)
    chat_history = list(conversation.messages.values("role", "content"))

    try:
        response_text, input_tokens, output_tokens = send_to_llm(
            conversation.llm, context_text, chat_history
        )

        # Save assistant message
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        # Update conversation timestamp
        conversation.save()

    except Exception as e:
        logger.exception("Error calling %s API", conversation.llm)
        # Save error as assistant message
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=f"Error: Unable to get response. {str(e)}",
        )

    # Return updated message list
    response = render(
        request,
        "case/ai/messages.html",
        {
            "messages": conversation.messages.all(),
            "conversation": conversation,
            "matter": matter,
        },
    )

    # If new conversation, trigger update of hidden field and list refresh
    if is_new:
        response["HX-Trigger"] = "conversationCreated"
        response["X-Conversation-Id"] = str(conversation.id)

    return response


@login_required
def conversation_list(request):
    """Return conversation list partial."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return render(request, "case/ai/conversation-list.html", {"conversations": []})

    conversations = Conversation.objects.filter(matter=matter, user=request.user)

    return render(
        request,
        "case/ai/conversation-list.html",
        {
            "conversations": conversations,
            "matter": matter,
        },
    )


@login_required
def select_conversation(request, conv_id):
    """Switch to a different conversation."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return redirect("case:ai-index")

    conversation = get_object_or_404(
        Conversation, pk=conv_id, matter=matter, user=request.user
    )

    messages = conversation.messages.all()

    return render(
        request,
        "case/ai/chat-area.html",
        {
            "messages": messages,
            "conversation": conversation,
            "matter": matter,
        },
    )


@login_required
def delete_conversation(request, conv_id):
    """Delete a conversation."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return redirect("case:ai-index")

    conversation = get_object_or_404(
        Conversation, pk=conv_id, matter=matter, user=request.user
    )

    conversation.delete()

    # Trigger refresh of conversation list
    response = HttpResponse(status=204)
    response["HX-Trigger"] = "conversationsChanged"
    return response


@login_required
def rename_conversation(request, conv_id):
    """Rename a conversation - POST saves and returns list or title."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return HttpResponse(status=400)

    conversation = get_object_or_404(
        Conversation, pk=conv_id, matter=matter, user=request.user
    )

    if request.method == "POST":
        new_title = request.POST.get("title", "").strip()
        if new_title:
            conversation.title = new_title[:255]
            conversation.save()

        # Check if request came from list view or standalone view
        if request.headers.get("HX-Target") == "conversationTitle":
            # From standalone view - return title partial
            return render(
                request,
                "case/ai/conversation-title.html",
                {
                    "conversation": conversation,
                },
            )
        else:
            # From list view - return updated list
            conversations = Conversation.objects.filter(
                matter=matter, user=request.user
            )
            return render(
                request,
                "case/ai/list.html",
                {
                    "conversations": conversations,
                    "matter": matter,
                },
            )

    # GET - return edit form for standalone view
    return render(
        request,
        "case/ai/conversation-rename-inline.html",
        {
            "conversation": conversation,
        },
    )


@login_required
def rename_form(request, conv_id):
    """Return rename form for list view."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return HttpResponse(status=400)

    conversation = get_object_or_404(
        Conversation, pk=conv_id, matter=matter, user=request.user
    )

    conversations = Conversation.objects.filter(matter=matter, user=request.user)

    return render(
        request,
        "case/ai/list-rename.html",
        {
            "conversations": conversations,
            "editing_conversation": conversation,
            "matter": matter,
        },
    )


@login_required
def create_prompt(request):
    """Generate a prompt stuffing document for external AI chat clients."""
    matter, _ = get_selected_matter(request)

    if not matter:
        return redirect("case:ai-index")

    # Load ai-prompt.md content
    legal_md_path = Path(settings.BASE_DIR) / "docs" / "ai-prompt.md"
    try:
        legal_guidelines = legal_md_path.read_text()
    except FileNotFoundError:
        legal_guidelines = "(Guidelines file not found)"

    # Determine user role description
    user = request.user
    if user.is_attorney:
        role_description = f"{user.get_full_name()} is an attorney"
    else:
        role_description = (
            f"{user.get_full_name()} is a paralegal supporting an attorney"
        )

    # Build case timeline from facts
    facts = Fact.objects.filter(matter=matter).order_by("date", "id")
    timeline_lines = []
    for fact in facts:
        if fact.date:
            line = f"- {fact.date}: {fact.description}"
        else:
            line = f"- (No date): {fact.description}"

        # Add source citations if available
        sources = []
        for doc in fact.documents.all()[:2]:
            if doc.citation:
                sources.append(doc.citation)
        for hl in fact.highlights.all()[:2]:
            if hl.citation:
                sources.append(hl.citation)
        if sources:
            line += f" {', '.join(sources)}"

        timeline_lines.append(line)

    timeline_section = ""
    if timeline_lines:
        timeline_section = "\n\n## Case Timeline\n\n" + "\n".join(timeline_lines)

    # Build highlights section
    highlights = (
        Highlight.objects.filter(document__matter=matter)
        .select_related("document")
        .order_by("-importance", "document__name", "page_number")
    )
    highlight_lines = []
    for hl in highlights:
        # Format: slug/title, then the text, then citation
        line = f"### {hl.slug}\n\n> {hl.text}\n\n{hl.citation}"
        highlight_lines.append(line)

    highlights_section = ""
    if highlight_lines:
        highlights_section = (
            "\n\n## Key Highlights\n\n"
            "The following are key highlights from the case documents "
            "as identified by an attorney:\n\n" + "\n\n".join(highlight_lines)
        )

    # Build outlines section
    def format_outline_items(items, depth=0):
        """Recursively format outline items with indentation."""
        lines = []
        for item in items:
            indent = "  " * depth
            content = item.content.strip() if item.content else "(empty)"
            if item.heading:
                lines.append(f"{indent}**{content}**")
            else:
                lines.append(f"{indent}- {content}")
            # Recursively add children
            children = item.get_children()
            if children:
                lines.extend(format_outline_items(children, depth + 1))
        return lines

    outlines = Outline.objects.filter(matter=matter).order_by("-importance", "-date")
    outline_blocks = []
    for outline in outlines:
        block_lines = [f"### {outline.title} ({outline.date})"]
        root_items = outline.get_root_items()
        if root_items:
            block_lines.append("")  # blank line after header
            block_lines.extend(format_outline_items(root_items))
        outline_blocks.append("\n".join(block_lines))

    outlines_section = ""
    if outline_blocks:
        outlines_section = (
            "\n\n## Attorney Notes\n\n"
            "The following are attorney notes and research outlines "
            "for this matter:\n\n" + "\n\n".join(outline_blocks)
        )

    # Build the prompt text with proper markdown formatting
    prompt_text = f"""## Request Date

{date.today().strftime("%B %d, %Y")}

## Requesting Party

- Name: {user.get_full_name()}
- Email: {user.email}
- Role: {role_description}
- Law Firm: Craig Legal, LLC

## General Guidelines for Responding

{legal_guidelines}{timeline_section}{highlights_section}{outlines_section}"""

    context = {
        "matter": matter,
        "prompt_text": prompt_text,
    }

    return render(request, "case/ai/prompt.html", context)
