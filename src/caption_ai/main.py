"""CLI entrypoint."""

import asyncio
import signal
from datetime import datetime, timedelta

from rich.console import Console

from caption_ai.bus import Segment, SegmentBus
from caption_ai.config import config
from caption_ai.storage import Storage
from caption_ai.summarizer import Summarizer
from caption_ai.web import app, set_storage, broadcast_segment, broadcast_summary, set_summarizer

console = Console()


async def generate_fake_segments(bus: SegmentBus, count: int = 20, web_mode: bool = False) -> None:
    """Generate fake transcript segments for testing."""
    base_time = datetime.now()
    fake_segments = [
        ("Alice", "Let's start by reviewing the Q4 results."),
        ("Bob", "I've prepared the financial overview."),
        ("Alice", "Great, can you walk us through the key metrics?"),
        ("Bob", "Revenue is up 15% compared to last quarter."),
        ("Charlie", "That's excellent news. What about expenses?"),
        ("Bob", "Expenses are well controlled, only up 3%."),
        ("Alice", "So we're looking at a strong profit margin."),
        ("Charlie", "Yes, this positions us well for next year."),
        ("Alice", "Let's discuss the roadmap for Q1."),
        ("Bob", "I think we should focus on the new product launch."),
        ("Charlie", "Agreed, but we also need to address technical debt."),
        ("Alice", "Let's prioritize both. Bob, can you draft a plan?"),
        ("Bob", "I'll have something ready by Friday."),
        ("Alice", "Perfect. Any other items to discuss?"),
        ("Charlie", "I think we're good. Let's wrap up."),
        ("Alice", "Sounds good. Meeting adjourned."),
    ]

    for i, (speaker, text) in enumerate(fake_segments[:count]):
        segment = Segment(
            timestamp=base_time + timedelta(seconds=i * 3),
            text=text,
            speaker=speaker,
        )
        await bus.put(segment)
        if not web_mode:
            console.print(
                f"[dim][{segment.timestamp.strftime('%H:%M:%S')}] "
                f"{speaker}: {text}[/dim]"
            )
        if web_mode:
            await broadcast_segment(segment)
        await asyncio.sleep(0.5)  # Simulate real-time arrival


async def main(web_mode: bool = False, web_port: int = 8000) -> None:
    """Main entrypoint."""
    console.print("[bold red]╔════════════════════════════════════════╗[/bold red]")
    console.print("[bold red]║[/bold red] [bold white]Glup - Advanced Meeting Intelligence[/bold white] [bold red]║[/bold red]")
    console.print("[bold red]╚════════════════════════════════════════╝[/bold red]")
    console.print("[dim]Initializing neural pathways...[/dim]")
    console.print(f"[dim]LLM Provider: {config.llm_provider}[/dim]")
    console.print(f"[dim]Model: {config.ollama_model if config.llm_provider == 'local' else 'API'}[/dim]")
    
    if web_mode:
        console.print(f"[dim]Web UI: http://127.0.0.1:{web_port}[/dim]")
    
    console.print("[dim]Analyzing conversation patterns...[/dim]\n")

    # Initialize components
    bus = SegmentBus()
    storage = Storage()
    await storage.init()

    # Setup web server if in web mode
    if web_mode:
        set_storage(storage)
        import uvicorn
        from threading import Thread
        
        def run_server():
            uvicorn.run(app, host="127.0.0.1", port=web_port, log_level="warning")
        
        server_thread = Thread(target=run_server, daemon=True)
        server_thread.start()
        console.print(f"[green]✓ Web server started on http://127.0.0.1:{web_port}[/green]\n")

    # Custom summarizer that broadcasts to web
    class WebSummarizer(Summarizer):
        async def _summarize(self, segments: list[Segment]) -> None:
            await super()._summarize(segments)
            if web_mode and self.current_summary:
                await broadcast_summary(self.current_summary)

    summarizer = WebSummarizer(bus, storage, summary_interval_seconds=15)
    
    # Register summarizer with web server for control
    if web_mode:
        set_summarizer(summarizer)

    # Start summarizer in background
    summarizer_task = asyncio.create_task(summarizer.run())

    # Generate fake segments
    await generate_fake_segments(bus, count=16, web_mode=web_mode)

    if web_mode:
        console.print("[green]✓ Glup is running. Open http://127.0.0.1:{web_port} in your browser.[/green]")
        console.print("[dim]Press Ctrl+C to stop...[/dim]\n")
        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Shutting down...[/yellow]")
            summarizer_task.cancel()
            try:
                await summarizer_task
            except asyncio.CancelledError:
                pass
            console.print("[green]Done![/green]")
    else:
        # Wait a bit for final summary
        await asyncio.sleep(5)

        # Stop summarizer
        summarizer_task.cancel()
        try:
            await summarizer_task
        except asyncio.CancelledError:
            pass

        console.print("[green]Done![/green]")


def cli() -> None:
    """CLI entrypoint."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Glup - Advanced Meeting Intelligence")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Start web UI server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Web server port (default: 8000)",
    )
    
    args = parser.parse_args()
    asyncio.run(main(web_mode=args.web, web_port=args.port))


if __name__ == "__main__":
    cli()

