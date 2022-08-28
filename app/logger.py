import logging
import os
import sys
from colorlog import ColoredFormatter


log = logging.getLogger(__name__)
log.setLevel(
    logging.DEBUG if os.environ.get("FLASK_DEBUG") == "True" else logging.INFO
)
sh = logging.StreamHandler(stream=sys.stdout)
sh.setFormatter(
    ColoredFormatter(
        "%(log_color)s[%(asctime)s] %(levelname)s [%(filename)s.%(funcName)s:"
        + "%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "light_black",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
)
log.addHandler(sh)


log.debug("EOF")
