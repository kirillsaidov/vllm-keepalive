# module main
import os
import sys
import time
import signal
import logging

# llm
from openai import OpenAI


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class GracefulShutdown:
    """Handle graceful shutdown on SIGTERM/SIGINT."""

    def __init__(self):
        self.shutdown_requested = False
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown_requested = True


def keep_alive(
    client: OpenAI,
    model: str,
    interval: int,
    shutdown: GracefulShutdown,
) -> None:
    """Send periodic dummy requests to keep GPU warm."""
    logger.info(f"Starting keep-alive loop (interval: {interval}s, model: {model})")
    request_count = 0

    while not shutdown.shutdown_requested:
        for _ in range(interval):
            if shutdown.shutdown_requested:
                break
            time.sleep(1)

        if shutdown.shutdown_requested:
            break

        try:
            response = client.completions.create(
                model=model,
                prompt="hi",
                max_tokens=1,
                temperature=0,
            )
            request_count += 1
            tokens = response.usage.total_tokens if response.usage else "N/A"
            logger.info(f"Keep-alive #{request_count} OK (tokens: {tokens})")
        except Exception as e:
            logger.warning(f"Keep-alive failed: {e}")


def wait_for_server(client: OpenAI, max_retries: int = 60, retry_interval: int = 5) -> bool:
    """Wait for VLLM server to become available."""
    logger.info("Waiting for VLLM server...")

    for attempt in range(1, max_retries + 1):
        try:
            client.models.list()
            logger.info(f"VLLM server ready (attempt {attempt})")
            return True
        except Exception as e:
            logger.info(f"Not ready, retrying in {retry_interval}s ({attempt}/{max_retries})")
            time.sleep(retry_interval)

    logger.error("Server did not become available")
    return False


def main():
    """Main entry point."""
    vllm_host = os.getenv("VLLM_HOST", "localhost")
    vllm_port = os.getenv("VLLM_PORT", "8081")
    model = os.getenv("VLLM_MODEL", "Qwen/Qwen3-4B-Instruct-2507-FP8")
    interval = int(os.getenv("KEEPALIVE_INTERVAL", "60"))

    base_url = f"http://{vllm_host}:{vllm_port}/v1"

    logger.info(f"VLLM Keep-Alive Service")
    logger.info(f"Target: {base_url}")
    logger.info(f"Model: {model}")
    logger.info(f"Interval: {interval}s")

    shutdown = GracefulShutdown()
    client = OpenAI(base_url=base_url, api_key="not-needed")

    if not wait_for_server(client):
        sys.exit(1)

    keep_alive(client, model, interval, shutdown)
    logger.info("Service stopped")


if __name__ == "__main__":
    main()



