# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import asyncio
import os
from unittest.mock import AsyncMock

import pytest


class ProcessResult:
    def __init__(self, stdout: bytes = b"", stderr: bytes = b""):
        self.communicate = AsyncMock(return_value=(stdout, stderr))


def create_client(monkeypatch):
    monkeypatch.setenv("ProgramFiles", os.path.dirname(__file__))
    import voicepeak_wrapper

    return voicepeak_wrapper.Voicepeak(exe_path=__file__)


def mock_process(monkeypatch, *results):
    create_subprocess = AsyncMock(side_effect=results)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_subprocess)
    return create_subprocess


@pytest.mark.asyncio
async def test_get_narrator_name_list_decodes_terminal_output(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult("Japanese Female 1\nJapanese Male 1\n".encode())
    create_subprocess = mock_process(monkeypatch, process)

    assert await client.get_narrator_name_list() == ("Japanese Female 1", "Japanese Male 1")
    create_subprocess.assert_awaited_once_with(
        __file__,
        "--list-narrator",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    process.communicate.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_get_emotion_list_decodes_terminal_output(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult("happy\nsad\n".encode())
    mock_process(monkeypatch, process)

    assert await client.get_emotion_list("Japanese Female 1") == ("happy", "sad")


@pytest.mark.asyncio
async def test_get_narrator_list_uses_each_terminal_output(monkeypatch):
    client = create_client(monkeypatch)
    import voicepeak_wrapper

    processes = (
        ProcessResult("Japanese Female 1\nJapanese Male 1\n".encode()),
        ProcessResult("happy\nsad\n".encode()),
        ProcessResult("happy\nangry\n".encode()),
    )
    mock_process(monkeypatch, *processes)

    assert await client.get_narrator_list() == (
        voicepeak_wrapper.Narrator("Japanese Female 1", ("happy", "sad")),
        voicepeak_wrapper.Narrator("Japanese Male 1", ("happy", "angry")),
    )


@pytest.mark.asyncio
async def test_say_text_returns_decoded_terminal_output(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult("completed\n".encode())
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text("本日は晴天なり", output_path="output.wav")

    assert isinstance(result, str)
    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "本日は晴天なり",
        "-o",
        "output.wav",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_terminal_error_is_decoded_as_runtime_error(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(stderr="narrator not found\n".encode())
    mock_process(monkeypatch, process)

    with pytest.raises(RuntimeError, match="narrator not found"):
        await client.get_emotion_list("unknown")
