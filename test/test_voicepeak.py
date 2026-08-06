# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import os
from unittest.mock import AsyncMock

import pytest

TEST_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(TEST_DIRECTORY, "output")
SKIP_FILE_GENERATION_IN_CI = pytest.mark.skipif(
    os.environ.get("CI") == "true",
    reason="VOICEPEAK file-generation tests require a local installation and are skipped in CI",
)


def create_client():
    import voicepeak_wrapper

    # The executable itself is mocked in unit tests; an existing path satisfies
    # the constructor without requiring VOICEPEAK to be installed.
    return voicepeak_wrapper.Voicepeak(exe_path=__file__)


@pytest.mark.asyncio
async def test_get_narrator_list(monkeypatch):
    import voicepeak_wrapper

    client = create_client()
    terminal_outputs = iter(["Japanese Female 1\nJapanese Male 1\n", "happy\nsad\n", "happy\nangry\n"])
    run = AsyncMock(side_effect=lambda _args: next(terminal_outputs))
    monkeypatch.setattr(client, "_Voicepeak__async_run", run)

    assert await client.get_narrator_list() == (
        voicepeak_wrapper.Narrator("Japanese Female 1", ("happy", "sad")),
        voicepeak_wrapper.Narrator("Japanese Male 1", ("happy", "angry")),
    )


@pytest.mark.asyncio
async def test_get_narrator_name_list(monkeypatch):
    client = create_client()
    run = AsyncMock(return_value="Japanese Female 1\nJapanese Male 1\n")
    monkeypatch.setattr(client, "_Voicepeak__async_run", run)

    assert await client.get_narrator_name_list() == ("Japanese Female 1", "Japanese Male 1")
    run.assert_awaited_once_with(["--list-narrator"])


@pytest.mark.asyncio
async def test_get_emotion_list(monkeypatch):
    client = create_client()
    run = AsyncMock(return_value="happy\nsad\n")
    monkeypatch.setattr(client, "_Voicepeak__async_run", run)

    assert await client.get_emotion_list("Japanese Female 1") == ("happy", "sad")
    run.assert_awaited_once_with(["--list-emotion", "Japanese Female 1"])


@pytest.mark.asyncio
async def test_say_text_returns_terminal_output(monkeypatch):
    client = create_client()
    run = AsyncMock(return_value="completed\n")
    monkeypatch.setattr(client, "_Voicepeak__async_run", run)

    assert await client.say_text("本日は晴天なり") == "completed\n"
    run.assert_awaited_once_with(["-s", "本日は晴天なり"])


@SKIP_FILE_GENERATION_IN_CI
@pytest.mark.asyncio
async def test_say_text_file_generation():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    await client.say_text("本日は晴天なり", output_path=os.path.join(OUTPUT_PATH, "test_say_text.wav"))
    await client.say_text(
        "本日は晴天なり", output_path=os.path.join(OUTPUT_PATH, "test_say_text_upper.wav"), speed=200, pitch=300
    )
    await client.say_text(
        "本日は晴天なり", output_path=os.path.join(OUTPUT_PATH, "test_say_text_lower.wav"), speed=50, pitch=-300
    )

    with pytest.raises(ValueError):
        await client.say_text("エラー", output_path=os.path.join(OUTPUT_PATH, "error.wav"), speed=201)
    with pytest.raises(ValueError):
        await client.say_text("エラー", output_path=os.path.join(OUTPUT_PATH, "error.wav"), speed=49)
    with pytest.raises(ValueError):
        await client.say_text("エラー", output_path=os.path.join(OUTPUT_PATH, "error.wav"), pitch=-301)
    with pytest.raises(ValueError):
        await client.say_text("エラー", output_path=os.path.join(OUTPUT_PATH, "error.wav"), pitch=301)

    with pytest.raises(RuntimeError):
        await client.say_text("1" * 141, output_path=os.path.join(OUTPUT_PATH, "error.wav"))


@SKIP_FILE_GENERATION_IN_CI
@pytest.mark.asyncio
async def test_say_textfile_file_generation():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    text_file = os.path.join(TEST_DIRECTORY, "sample.txt")

    await client.say_textfile(text_file, output_path=os.path.join(OUTPUT_PATH, "say_text.wav"))
