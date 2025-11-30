import logging
import sys
from src.core.config import settings

def setup_logger():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True
    )

    # --- SILENCE NOISY LIBRARIES ---
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)  # <--- Add this
    logging.getLogger("watchfiles").setLevel(logging.WARNING) # <--- Add this
    # -------------------------------

    logger = logging.getLogger("chronos")
    logger.info(f"Logger initialized. Level: {logging.getLevelName(level)}")