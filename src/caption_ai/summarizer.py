"""Rolling summarizer loop."""

import asyncio
from datetime import datetime, timedelta

from caption_ai.bus import Segment, SegmentBus
from caption_ai.llm.router import get_llm_client
from caption_ai.prompts import build_rolling_summary_prompt
from caption_ai.storage import Storage
from caption_ai.config import config
from caption_ai.web import get_summarizer_running
from rich.console import Console

console = Console()

# Try to import web broadcast function if available
try:
    from caption_ai.web import broadcast_summary
    _web_available = True
except ImportError:
    _web_available = False


class Summarizer:
    """Rolling summarizer that processes segments and generates summaries."""

    def __init__(
        self,
        bus: SegmentBus,
        storage: Storage,
        summary_interval_seconds: int = 30,
    ) -> None:
        """Initialize summarizer."""
        self.bus = bus
        self.storage = storage
        self.summary_interval = summary_interval_seconds
        self.llm_client = get_llm_client(config.llm_provider)
        self.current_summary: str | None = None
        self.last_summary_time = datetime.now()

    async def run(self) -> None:
        """Run the summarizer loop."""
        console.print("[bold red]✓ Neural processing units online[/bold red]")
        console.print("[dim]Awaiting conversation data...[/dim]\n")
        accumulated_segments: list[Segment] = []

        while True:
            try:
                # Wait for segment with timeout
                try:
                    segment = await asyncio.wait_for(
                        self.bus.get(), timeout=1.0
                    )
                    accumulated_segments.append(segment)
                    await self.storage.append(segment)
                    self.bus.task_done()
                except asyncio.TimeoutError:
                    pass

                # Check if summarizer is running (can be paused via UI)
                if not get_summarizer_running():
                    await asyncio.sleep(0.5)
                    continue

                # Check if it's time to summarize
                now = datetime.now()
                if (
                    accumulated_segments
                    and (now - self.last_summary_time).total_seconds()
                    >= self.summary_interval
                ):
                    await self._summarize(accumulated_segments)
                    accumulated_segments.clear()
                    self.last_summary_time = now

            except KeyboardInterrupt:
                console.print("[yellow]Summarizer stopping...[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Error in summarizer: {e}[/red]")
                await asyncio.sleep(1)

    async def _summarize(self, segments: list[Segment]) -> None:
        """Generate summary from accumulated segments."""
        if not segments:
            return

        console.print(
            f"[yellow]Analyzing {len(segments)} conversation segments...[/yellow]"
        )
        prompt = build_rolling_summary_prompt(
            self.current_summary, segments
        )

        try:
            reply = await self.llm_client.complete(prompt)
            self.current_summary = reply.content
            await self.storage.append_summary(reply.content)
            if _web_available:
                try:
                    await broadcast_summary(reply.content)
                except Exception:
                    pass  # Web not available or no connections
            console.print(f"[bold green]Glup Analysis:[/bold green] {reply.content}\n")
        except Exception as e:
            console.print(f"[red]LLM error: {e}[/red]")

