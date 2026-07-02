"""Rich terminal dashboard — ASCII-safe for Windows cp1252 console."""
from __future__ import annotations

from rich import box
from rich.console import Console
from rich.table import Table

from models import Finding, PersonaReport

console = Console(width=110)

_BANNER = """
[bold cyan]AI Policy Impact Simulator[/bold cyan]  [dim]v1.0[/dim]
[dim]Stakeholder reactions grounded in real, cited regulatory text -- not free-form roleplay[/dim]
"""


def print_banner() -> None:
    console.print(_BANNER)


def _finding_line(f: Finding) -> None:
    badge = "[green]VERIFIED[/green]" if f.verified else "[bold red]UNVERIFIED -- citation could not be confirmed[/bold red]"
    revoked = " [yellow](REVOKED -- historical only)[/yellow]" if f.status and f.status != "ACTIVE" else ""
    console.print(f"  {badge}  [bold]{f.doc_title or f.doc_id}[/bold] -- {f.section_id}{revoked}")
    console.print(f"    {f.claim}")
    excerpt = f.quote if len(f.quote) <= 220 else f.quote[:217] + "..."
    console.print(f"    [dim]\"{excerpt}\"[/dim]")
    if f.source_url:
        console.print(f"    [dim]{f.source_url}[/dim]")
    console.print()


def print_persona_reports(reports: list[PersonaReport]) -> None:
    console.rule("[bold]Stakeholder Simulation[/bold]")
    for r in reports:
        console.print(f"[bold underline]{r.persona_name}[/bold underline]")
        console.print(f"[dim]{r.summary}[/dim]")
        console.print()
        if not r.findings:
            console.print("  [dim]No grounded citation found in the indexed corpus for this persona's queries.[/dim]\n")
            continue
        for f in r.findings:
            _finding_line(f)


def print_consequences(findings: list[Finding]) -> None:
    console.rule("[bold]Unintended Consequences (deterministic trigger match)[/bold]")
    if not findings:
        console.print("[dim]No trigger phrases from config.CONSEQUENCE_TRIGGERS matched this draft.[/dim]")
        return
    for f in findings:
        _finding_line(f)


def print_scoring(nist_result: dict, eu_result: dict) -> None:
    console.rule("[bold]Framework Scoring[/bold]")
    t = Table(box=box.ASCII2, title="NIST AI RMF Coverage")
    t.add_column("Function")
    t.add_column("Addressed")
    t.add_column("Evidence", overflow="fold")
    for f in nist_result["findings"]:
        addressed = "yes" if "matched keyword" in f.claim else "no"
        t.add_row(f.section_id, addressed, f.claim)
    console.print(t)
    console.print(f"[bold]NIST RMF coverage score: {nist_result['score']}/{nist_result['max_score']}[/bold]\n")

    console.print(f"EU AI Act high-risk domain match: [bold]{'YES' if eu_result['likely_high_risk'] else 'no'}[/bold]"
                  + (f" ({', '.join(eu_result['matched_domains'])})" if eu_result["matched_domains"] else ""))
    console.print(f"EU AI Act prohibited-practice match: [bold]{'YES' if eu_result['likely_prohibited_sections'] else 'no'}[/bold]"
                  + (f" ({', '.join(eu_result['likely_prohibited_sections'])})" if eu_result["likely_prohibited_sections"] else ""))
    console.print()
    for f in eu_result["findings"]:
        _finding_line(f)


def print_search_results(query: str, results: list) -> None:
    console.rule(f"[bold]Corpus Search:[/bold] \"{query}\"")
    if not results:
        console.print("[dim]No matches.[/dim]")
        return
    t = Table(box=box.ASCII2)
    t.add_column("Score", justify="right")
    t.add_column("Document")
    t.add_column("Section")
    t.add_column("Status")
    for chunk, score in results:
        t.add_row(f"{score:.2f}", chunk.title, chunk.section_id, chunk.status)
    console.print(t)
