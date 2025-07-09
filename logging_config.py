import logging
from rich.logging import RichHandler


def set_up_logging() -> None:
    file_formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    file_handler = logging.FileHandler("repro_wrapped.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)

    rich_handler = RichHandler()
    rich_handler.setLevel(logging.INFO)

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(name)s: %(message)s",
        handlers=[
            file_handler,
            rich_handler,
        ]
    )
