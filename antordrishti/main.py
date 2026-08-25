"""
Antordrishti — Questioned Document Forensic Analysis
Main entry point with animated splash screen.

Usage:
    python main.py
"""

import sys
import os
import logging

# Ensure the application directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.application import AntordrishtiApp
from ui.main_window import MainWindow
from ui.splash_screen import AntordrishtiSplash


def setup_logging():
    """Configure application logging."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_dir, "antordrishti.log")),
            logging.StreamHandler(),
        ],
    )


def main():
    """Launch the Antordrishti application with animated splash."""
    setup_logging()
    logger = logging.getLogger("antordrishti")
    logger.info("Starting Antordrishti application...")

    app = AntordrishtiApp(sys.argv)

    # Initialize DB early
    try:
        from services.db_service import get_db
        get_db()
        logger.info("Database initialized.")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")

    # Show splash screen
    splash = AntordrishtiSplash()
    window = None

    def on_splash_done():
        nonlocal window
        window = MainWindow()
        window.show()
        logger.info("Application window created.")

    splash.start(done_callback=on_splash_done)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
