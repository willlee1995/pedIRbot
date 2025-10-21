"""Script to start the FastAPI server."""
import sys
from pathlib import Path

# Add parent directory to path FIRST (before other imports)
sys.path.insert(0, str(Path(__file__).parent.parent))

# isort: off  - Don't reorder imports below this line
import uvicorn
from loguru import logger
# isort: on


def main(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the FastAPI server.

    Args:
        host: Host to bind to
        port: Port to bind to
        reload: Enable auto-reload on code changes
    """
    logger.info(f"Starting PedIR RAG API server on {host}:{port}")
    logger.info(f"Auto-reload: {reload}")

    uvicorn.run(
        "src.api:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start FastAPI server")
    parser.add_argument("--host", type=str,
                        default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000,
                        help="Port to bind to")
    parser.add_argument("--reload", action="store_true",
                        help="Enable auto-reload")

    args = parser.parse_args()

    main(args.host, args.port, args.reload)
