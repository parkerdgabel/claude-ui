import click
import uvicorn

from claude_ui.config import settings


@click.command()
@click.option(
    "--host",
    default=settings.api_host,
    help="Host to bind to",
)
@click.option(
    "--port",
    default=settings.api_port,
    type=int,
    help="Port to bind to",
)
@click.option(
    "--reload",
    is_flag=True,
    default=settings.debug,
    help="Enable auto-reload",
)
def main(host: str, port: int, reload: bool):
    """Start the Claude UI server"""
    click.echo(f"Starting Claude UI server on {host}:{port}")
    
    uvicorn.run(
        "claude_ui.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()