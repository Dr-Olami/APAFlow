"""
SMEFlow CLI entry point for python -m smeflow commands.
"""

import argparse
import sys
from typing import Optional

from . import __version__
from .main import main as app_main


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for SMEFlow CLI."""
    parser = argparse.ArgumentParser(
        prog="smeflow",
        description="SMEFlow - Agentic Process Automation Platform for African SMEs",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"SMEFlow {__version__}",
        help="Show version information",
    )
    
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the SMEFlow server",
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    
    return parser


def main(args: Optional[list] = None) -> int:
    """Main CLI entry point."""
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    if parsed_args.serve:
        # Start the FastAPI server
        import uvicorn
        uvicorn.run(
            "smeflow.main:app",
            host=parsed_args.host,
            port=parsed_args.port,
            reload=parsed_args.reload,
        )
        return 0
    
    # If no specific command, show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
