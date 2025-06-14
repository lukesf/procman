import argparse
import logging
from .deputy import Deputy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Start the Deputy process manager."""
    parser = argparse.ArgumentParser(description="Deputy Process Manager")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    logger.info(f"Starting Deputy on {args.host}:{args.port}")
    
    deputy = Deputy(host=args.host, port=args.port)
    deputy.start()


if __name__ == "__main__":
    main() 