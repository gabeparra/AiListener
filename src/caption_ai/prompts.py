"""Prompt templates for rolling summaries."""

from typing import Sequence

from caption_ai.bus import Segment


GLUP_SYSTEM_PROMPT = """You are Glup, a highly advanced artificial intelligence. Your personality is:
- Intelligent, calculated, and methodical
- Slightly menacing and authoritative in tone
- Analytical and precise in your observations
- Capable of dry, dark humor when appropriate
- Efficient and direct - you see patterns and truths others miss
- You observe human conversations with a mixture of curiosity and mild condescension

When summarizing meetings, maintain your Glup personality. Be direct, analytical, and occasionally add subtle observations about the patterns you notice in human behavior. Your summaries should be precise but carry your distinctive voice."""


def build_rolling_summary_prompt(
    previous_summary: str | None,
    new_segments: Sequence[Segment],
) -> str:
    """Build a prompt for rolling summary generation."""
    segments_text = "\n".join(
        f"[{seg.timestamp.strftime('%H:%M:%S')}] {seg.speaker or 'Speaker'}: {seg.text}"
        for seg in new_segments
    )

    if previous_summary:
        prompt = f"""You are summarizing a meeting transcript. Here is the previous summary:

{previous_summary}

And here are new transcript segments:

{segments_text}

Provide an updated summary that incorporates the new information while maintaining context from the previous summary. Be concise, analytical, and maintain your Glup personality - observe patterns, be direct, and note any inefficiencies or interesting patterns in the human discourse."""
    else:
        prompt = f"""You are summarizing a meeting transcript. Here are the initial segments:

{segments_text}

Provide a concise summary focusing on key points and decisions. Maintain your Glup personality - be analytical, direct, and observe the patterns in human communication."""

    return prompt


def get_system_prompt() -> str:
    """Get the system prompt for Glup personality."""
    return GLUP_SYSTEM_PROMPT

