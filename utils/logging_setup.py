import logging
import sys

def setup_logging(level=logging.INFO):
    root = logging.getLogger()
    root.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt = "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

