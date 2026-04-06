import typer

app = typer.Typer(help="Analyze one A-share stock code and produce beginner-friendly output.")


@app.callback()
def main() -> None:
    """Shuoha CLI."""
