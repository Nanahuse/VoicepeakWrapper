# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

"""VOICEPEAK integration tests that create output files.

These tests require a local VOICEPEAK installation. Pytest does not collect this
module by default; run it explicitly when file-generation coverage is needed:

    uv run --extra dev --with-editable . pytest test/manual_voicepeak_file_generation.py
"""

import asyncio
from pathlib import Path

import pytest

import voicepeak_wrapper

TEST_DIRECTORY = Path(__file__).resolve().parent
OUTPUT_PATH = TEST_DIRECTORY / "output"


def _write_text(path: Path, text: str) -> None:
    with path.open(mode="w", encoding="UTF-8") as f:
        f.write(text)


@pytest.mark.asyncio
async def test_get_narrator_list() -> None:
    client = voicepeak_wrapper.Voicepeak()
    narrators = await client.get_narrator_list()
    output = []
    for narrator in narrators:
        output.append(f"{narrator.name} : {', '.join(narrator.emotions)}\n")
        await client.say_text(
            "本日は晴天なり",
            output_path=OUTPUT_PATH / f"narrator_{narrator.name}.wav",
            narrator=narrator,
            emotions={narrator.emotions[1]: 100},
        )
    await asyncio.to_thread(_write_text, OUTPUT_PATH / "narrators.txt", "".join(output))


@pytest.mark.asyncio
async def test_get_narrator_name_list() -> None:
    client = voicepeak_wrapper.Voicepeak()
    narrator_names = await client.get_narrator_name_list()
    content = "".join(f"{name}\n" for name in narrator_names)
    await asyncio.to_thread(_write_text, OUTPUT_PATH / "narrator_names.txt", content)


@pytest.mark.asyncio
async def test_get_emotion_list() -> None:
    client = voicepeak_wrapper.Voicepeak()

    narrator_names = await client.get_narrator_name_list()
    output = []
    for name in narrator_names:
        emotion_list = await client.get_emotion_list(name)
        output.append(f"{name} : {', '.join(emotion_list)}\n")
    await asyncio.to_thread(_write_text, OUTPUT_PATH / "emotions.txt", "".join(output))

    with pytest.raises(RuntimeError):
        await client.get_emotion_list("hogehoge")


@pytest.mark.asyncio
async def test_say_text() -> None:
    client = voicepeak_wrapper.Voicepeak()
    await client.say_text("本日は晴天なり", output_path=OUTPUT_PATH / "test_say_text.wav")
    await client.say_text(
        "本日は晴天なり", output_path=OUTPUT_PATH / "test_say_text_upper.wav", speed=200, pitch=300
    )
    await client.say_text(
        "本日は晴天なり", output_path=OUTPUT_PATH / "test_say_text_lower.wav", speed=50, pitch=-300
    )

    with pytest.raises(ValueError, match="speed"):
        await client.say_text("エラー", output_path=OUTPUT_PATH / "error.wav", speed=201)
    with pytest.raises(ValueError, match="speed"):
        await client.say_text("エラー", output_path=OUTPUT_PATH / "error.wav", speed=49)
    with pytest.raises(ValueError, match="pitch"):
        await client.say_text("エラー", output_path=OUTPUT_PATH / "error.wav", pitch=-301)
    with pytest.raises(ValueError, match="pitch"):
        await client.say_text("エラー", output_path=OUTPUT_PATH / "error.wav", pitch=301)

    with pytest.raises(RuntimeError):
        await client.say_text("1" * 141, output_path=OUTPUT_PATH / "error.wav")


@pytest.mark.asyncio
async def test_say_testfile() -> None:
    client = voicepeak_wrapper.Voicepeak()

    text_file = TEST_DIRECTORY / "sample.txt"

    await client.say_textfile(text_file, output_path=OUTPUT_PATH / "say_text.wav")
