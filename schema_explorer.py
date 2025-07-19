import argparse
import re
from oci.schema import SQLiteOCITypeStore
import json
import logging
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

store = SQLiteOCITypeStore()

def main_menu():
    console = Console()
    parser = argparse.ArgumentParser(description="OCI Schema Browser")
    parser.add_argument("pattern", nargs="?", help="Regex pattern to search types")
    parser.add_argument("--kind", choices=["request", "response"], help="Filter by kind (Request or Response)")
    args = parser.parse_args()

    pattern = args.pattern
    kind = args.kind.lower() if args.kind else None
    if kind and kind not in ("request", "response"):
        console.print("[bold red]Kind must be 'request' or 'response'. Exiting.[/]")
        return

    if not pattern:
        console.print("[bold red]No pattern provided. Exiting.[/]")
        return

    names = store.types(kind=kind.title() if kind else None)
    logger.debug("Found %d types in the database.", len(names))
    logger.debug("Type names: %s", names)
    options = [name for name in names if re.search(pattern, name, re.IGNORECASE)]

    if not options:
        console.print("[bold yellow]No types found.[/]")
        return

    if len(options) > 1:
        console.print("[bold cyan]Matching Types:[/]")
        for name in options:
            console.print(f"- {name}")
        return

    selected_type = options[0]
    console.print(Panel(f"[#ffcc00]{selected_type}[/]", title="Selected Type"))

    doc = store.doc(selected_type)
    if doc:
        console.print(Panel(f"[#c8e1ff]{doc.strip()}[/]", title="Documentation"))

    schema = store.schema(selected_type)
    if schema:
        xsd_syntax = Syntax(schema.strip(), "xml", theme="github-dark", word_wrap=True)
        console.print(Panel(xsd_syntax, title="Formatted Schema", subtitle="XSD"))
        # console.print(Panel(schema.strip(), title="Raw Schema", subtitle="XML"))

    params = store.parameters(selected_type)
    if params:
        json_syntax = Syntax(json.dumps(params, indent=2), "json", theme="github-dark", word_wrap=True)
        console.print(Panel(json_syntax, title="Parameters"))

    example = store.example(selected_type)
    if example:
        example_syntax = Syntax(json.dumps(example, indent=2), "json", theme="github-dark", word_wrap=True)
        console.print(Panel(example_syntax, title="Example"))

if __name__ == "__main__":
    main_menu()
    store.close()