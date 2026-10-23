#!/usr/bin/env python3
"""
SaaSOptimizer AI — Single Runner Script
Spins up FastAPI backend, WebSocket streaming, and serves the Google Antigravity UI.
"""

from __future__ import annotations

import os
import sys
import webbrowser
import uvicorn

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from rich.console import Console
    from rich.panel import Panel
    console = Console(safe_box=True)
    HAS_RICH = True
except Exception:
    HAS_RICH = False
    console = None


def print_banner(host: str, port: int) -> None:
    url = f"http://{host}:{port}"
    banner_text = (
        "[bold cyan]SaaSOptimizer AI -- Autonomous SaaS Renewal & Rightsizing Agent[/bold cyan]\n"
        "[bold yellow]Agentic AI Hackathon 2026 -- Powered by Ziro.Digital[/bold yellow]\n\n"
        f"  [bold green]* Web UI (Google Antigravity Dashboard):[/bold green] [underline]{url}[/underline]\n"
        f"  [bold blue]* Interactive REST API Docs:[/bold blue]          [underline]{url}/docs[/underline]\n"
        f"  [bold magenta]* WebSocket Live Stream:[/bold magenta]              [underline]ws://{host}:{port}/ws[/underline]\n\n"
        "  [dim]Test Scenarios: TC1 (Slack 14d) | TC2 (dev_user_04 94d) | TC3 (Google Lock) | TC4 (Jira 50->45 HITL)[/dim]\n"
        "  [dim]Press Ctrl+C to terminate the server.[/dim]"
    )
    try:
        if HAS_RICH and console:
            console.print(Panel(banner_text, border_style="bright_blue", expand=False))
            return
    except Exception:
        pass

    print("=" * 76)
    print(" SaaSOptimizer AI -- Autonomous SaaS Renewal & Rightsizing Agent")
    print(" Agentic AI Hackathon 2026 -- Powered by Ziro.Digital")
    print(f" URL: {url}")
    print("=" * 76)


def main() -> None:
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print_banner(host, port)

    # Automatically launch browser if not in CI/test mode
    if os.getenv("NO_BROWSER") != "1":
        try:
            webbrowser.open_new_tab(f"http://{host}:{port}")
        except Exception:
            pass

    uvicorn.run(
        "backend.api:app",
        host=host,
        port=port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
