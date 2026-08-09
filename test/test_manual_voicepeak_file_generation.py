# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

"""VOICEPEAK integration tests that create output files.

These tests require a local VOICEPEAK installation and are marked xfail with
``run=False``, so they are reported as NOTRUN without launching VOICEPEAK. Run
them with pytest's built-in ``--runxfail`` option when file-generation coverage
is needed:

    uv run --group dev --with-editable . pytest --runxfail

Or run just this module:

    uv run --group dev --with-editable . pytest \\
        test/test_manual_voicepeak_file_generation.py --runxfail
"""

import asyncio
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.xfail(run=False, reason="requires a local VOICEPEAK installation; pass --runxfail to run")

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


@pytest.mark.asyncio
async def test_say_text_overwrites_existing_output_wav():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    output_path = Path(OUTPUT_PATH) / "test_overwrite.wav"
    await asyncio.to_thread(output_path.write_bytes, b"previous generation")

    await client.say_text("本日は晴天なり", output_path=output_path)

    content = await asyncio.to_thread(output_path.read_bytes)
    assert len(content) > 0
    assert content != b"previous generation"
    assert content[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_say_text_with_pathlib_output_narrator_and_emotions():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    narrators = await client.get_narrator_list()
    assert len(narrators) > 0
    narrator = narrators[0]

    output_path = Path(OUTPUT_PATH) / "test_narrator_emotions.wav"
    emotions = {narrator.emotions[0]: 100} if narrator.emotions else None
    await client.say_text(
        "本日は晴天なり",
        output_path=output_path,
        narrator=narrator.name,
        emotions=emotions,
    )

    content = await asyncio.to_thread(output_path.read_bytes)
    assert len(content) > 0
    assert content[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_say_textfile_with_pathlib_input_and_output():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    text_file = Path(TEST_DIRECTORY) / "sample.txt"
    output_path = Path(OUTPUT_PATH) / "test_textfile_path.wav"

    await client.say_textfile(text_file, output_path=output_path, speed=120, pitch=-50)

    content = await asyncio.to_thread(output_path.read_bytes)
    assert len(content) > 0
    assert content[:4] == b"RIFF"
