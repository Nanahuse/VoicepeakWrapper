"""VOICEPEAK integration tests that create output files.

These tests require a local VOICEPEAK installation. Pytest does not collect this
module by default; run it explicitly when file-generation coverage is needed:

    uv run --extra dev --with-editable . pytest test/manual_voicepeak_file_generation.py
"""

import asyncio
import os
from pathlib import Path

import pytest

TEST_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(TEST_DIRECTORY, "output")


@pytest.mark.asyncio
async def test_get_narrator_list():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    narrators = await client.get_narrator_list()
    lines = []
    for narrator in narrators:
        lines.append(f"{narrator.name} : {', '.join(narrator.emotions)}\n")

        await client.say_text(
            "本日は晴天なり",
            output_path=os.path.join(OUTPUT_PATH, f"narrator_{narrator.name}.wav"),
            narrator=narrator,
            emotions={narrator.emotions[1]: 100},
        )

    await asyncio.to_thread(Path(OUTPUT_PATH, "narrators.txt").write_text, "".join(lines), encoding="UTF-8")


@pytest.mark.asyncio
async def test_get_narrator_name_list():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    narrator_names = await client.get_narrator_name_list()
    await asyncio.to_thread(
        Path(OUTPUT_PATH, "narrator_names.txt").write_text,
        "".join(f"{name}\n" for name in narrator_names),
        encoding="UTF-8",
    )


@pytest.mark.asyncio
async def test_get_emotion_list():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()

    narrator_names = await client.get_narrator_name_list()
    lines = []
    for name in narrator_names:
        emotion_list = await client.get_emotion_list(name)
        lines.append(f"{name} : {', '.join(emotion_list)}\n")

    await asyncio.to_thread(Path(OUTPUT_PATH, "emotions.txt").write_text, "".join(lines), encoding="UTF-8")

    with pytest.raises(RuntimeError):
        await client.get_emotion_list("hogehoge")


@pytest.mark.asyncio
async def test_say_text():
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


@pytest.mark.asyncio
async def test_say_testfile():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()

    text_file = os.path.join(TEST_DIRECTORY, "sample.txt")

    await client.say_textfile(text_file, output_path=os.path.join(OUTPUT_PATH, "say_text.wav"))
