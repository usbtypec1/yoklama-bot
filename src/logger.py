import logging
import pathlib
from logging.handlers import TimedRotatingFileHandler


def setup_logging() -> None:
    filename = pathlib.Path(__file__).parents[1] / "logs" / "error.log"
    filename.parent.mkdir(parents=True, exist_ok=True)
    filename.touch(exist_ok=True)
    error_handler = TimedRotatingFileHandler(
        filename=filename,
        when="D",
        interval=1,
        backupCount=3,
        encoding="utf-8",
    )

    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        ),
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        ),
    )

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(error_handler)
    root.addHandler(console_handler)
