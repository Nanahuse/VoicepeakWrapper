# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import pytest
from _pytest.config import Config
from _pytest.config.argparsing import Parser
from _pytest.nodes import Item


def pytest_addoption(parser: Parser) -> None:
    parser.addoption(
        "--run-voicepeak-integration",
        action="store_true",
        default=False,
        help="run integration tests that require a local VOICEPEAK installation",
    )


def pytest_collection_modifyitems(config: Config, items: list[Item]) -> None:
    if config.getoption("--run-voicepeak-integration"):
        return

    skip = pytest.mark.skip(reason="requires a local VOICEPEAK installation; pass --run-voicepeak-integration to run")
    for item in items:
        if item.get_closest_marker("voicepeak"):
            item.add_marker(skip)
