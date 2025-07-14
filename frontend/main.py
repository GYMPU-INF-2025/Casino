from __future__ import annotations

import json
import logging.config
import pathlib

import arcade

from frontend.window import MainWindow

ROOT_PATH = pathlib.Path(__file__).parent


def main() -> None:
    with (ROOT_PATH / "logging.json").open() as f:
        logging.config.dictConfig(json.load(f))
    MainWindow(ROOT_PATH)
    arcade.run()


if __name__ == "__main__":
    main()
