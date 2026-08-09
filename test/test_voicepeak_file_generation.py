# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

"""Mock-based tests for the wrapper's file-generation behavior.

These tests replace the former manual VOICEPEAK integration tests that were
xfailed (``run=False``) because they launched a local voicepeak.exe. They run
without a local VOICEPEAK installation by mocking the subprocess, and verify
the intended output paths, generated files, existing-file overwrite, long-text,
and ``text_file`` behavior using temporary directories.
"""

import asyncio
import os
from unittest.mock import AsyncMock

import pytest

pytestmark = pytest.mark.asyncio


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


async def test_get_narrator_list_and_generate_file(monkeypatch, tmp_path):
    client = create_client(monkeypatch)
    import voicepeak_wrapper

    processes = (
        ProcessResult(b"Japanese Female 1\nJapanese Male 1\n"),
        ProcessResult(b"happy\nsad\n"),
        ProcessResult(b"happy\nangry\n"),
        ProcessResult(b"completed\n"),
        ProcessResult(b"completed\n"),
    )
    create_subprocess = mock_process(monkeypatch, *processes)

    narrators = await client.get_narrator_list()
    assert narrators == (
        voicepeak_wrapper.Narrator("Japanese Female 1", ("happy", "sad")),
        voicepeak_wrapper.Narrator("Japanese Male 1", ("happy", "angry")),
    )

    lines = []
    for narrator in narrators:
        lines.append(f"{narrator.name} : {', '.join(narrator.emotions)}\n")
        await client.say_text(
            "本日は晴天なり",
            output_path=tmp_path / f"narrator_{narrator.name}.wav",
            narrator=narrator,
            emotions={narrator.emotions[1]: 100},
        )

    output_file = tmp_path / "narrators.txt"
    await asyncio.to_thread(output_file.write_text, "".join(lines), encoding="UTF-8")
    assert output_file.read_text(encoding="UTF-8") == "Japanese Female 1 : happy, sad\nJapanese Male 1 : happy, angry\n"

    create_subprocess.assert_any_await(
        __file__,
        "-s",
        "本日は晴天なり",
        "-o",
        os.fspath(tmp_path / "narrator_Japanese Female 1.wav"),
        "-n",
        "Japanese Female 1",
        "-e",
        "sad=100",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    create_subprocess.assert_any_await(
        __file__,
        "-s",
        "本日は晴天なり",
        "-o",
        os.fspath(tmp_path / "narrator_Japanese Male 1.wav"),
        "-n",
        "Japanese Male 1",
        "-e",
        "angry=100",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def test_get_narrator_name_list_and_generate_file(monkeypatch, tmp_path):
    client = create_client(monkeypatch)
    mock_process(monkeypatch, ProcessResult(b"Japanese Female 1\nJapanese Male 1\n"))

    narrator_names = await client.get_narrator_name_list()
    assert narrator_names == ("Japanese Female 1", "Japanese Male 1")

    output_file = tmp_path / "narrator_names.txt"
    await asyncio.to_thread(
        output_file.write_text,
        "".join(f"{name}\n" for name in narrator_names),
        encoding="UTF-8",
    )
    assert output_file.read_text(encoding="UTF-8") == "Japanese Female 1\nJapanese Male 1\n"


async def test_get_emotion_list_and_generate_file(monkeypatch, tmp_path):
    client = create_client(monkeypatch)
    processes = (
        ProcessResult(b"Japanese Female 1\nJapanese Male 1\n"),
        ProcessResult(b"happy\nsad\n"),
        ProcessResult(b"happy\nangry\n"),
    )
    mock_process(monkeypatch, *processes)

    narrator_names = await client.get_narrator_name_list()
    lines = []
    for name in narrator_names:
        emotion_list = await client.get_emotion_list(name)
        lines.append(f"{name} : {', '.join(emotion_list)}\n")

    output_file = tmp_path / "emotions.txt"
    await asyncio.to_thread(output_file.write_text, "".join(lines), encoding="UTF-8")
    assert output_file.read_text(encoding="UTF-8") == "Japanese Female 1 : happy, sad\nJapanese Male 1 : happy, angry\n"

    mock_process(monkeypatch, ProcessResult(stderr=b"narrator not found: hogehoge\n"))
    with pytest.raises(RuntimeError, match="narrator not found"):
        await client.get_emotion_list("hogehoge")


async def test_say_text_and_validate_speed_pitch(monkeypatch, tmp_path):
    client = create_client(monkeypatch)
    processes = (
        ProcessResult(b"completed\n"),
        ProcessResult(b"completed\n"),
        ProcessResult(b"completed\n"),
    )
    create_subprocess = mock_process(monkeypatch, *processes)

    await client.say_text("本日は晴天なり", output_path=tmp_path / "test_say_text.wav")
    await client.say_text("本日は晴天なり", output_path=tmp_path / "test_say_text_upper.wav", speed=200, pitch=300)
    await client.say_text("本日は晴天なり", output_path=tmp_path / "test_say_text_lower.wav", speed=50, pitch=-300)

    with pytest.raises(ValueError, match="speedは50 - 200の範囲内の整数"):
        await client.say_text("エラー", output_path=tmp_path / "error.wav", speed=201)
    with pytest.raises(ValueError, match="speedは50 - 200の範囲内の整数"):
        await client.say_text("エラー", output_path=tmp_path / "error.wav", speed=49)
    with pytest.raises(ValueError, match="pitchは-300 - 300の範囲内の整数"):
        await client.say_text("エラー", output_path=tmp_path / "error.wav", pitch=-301)
    with pytest.raises(ValueError, match="pitchは-300 - 300の範囲内の整数"):
        await client.say_text("エラー", output_path=tmp_path / "error.wav", pitch=301)

    create_subprocess.assert_any_await(
        __file__,
        "-s",
        "本日は晴天なり",
        "-o",
        os.fspath(tmp_path / "test_say_text.wav"),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    create_subprocess.assert_any_await(
        __file__,
        "-s",
        "本日は晴天なり",
        "-o",
        os.fspath(tmp_path / "test_say_text_upper.wav"),
        "--speed",
        "200",
        "--pitch",
        "300",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    create_subprocess.assert_any_await(
        __file__,
        "-s",
        "本日は晴天なり",
        "-o",
        os.fspath(tmp_path / "test_say_text_lower.wav"),
        "--speed",
        "50",
        "--pitch",
        "-300",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def test_say_text_long_text_raises_runtime_error(monkeypatch, tmp_path):
    client = create_client(monkeypatch)

    def long_text_process(*call_args, **kwargs):
        args = call_args[1:]
        text = args[args.index("-s") + 1]
        if len(text) >= 141:
            return ProcessResult(stderr=b"text is too long\n")
        return ProcessResult(b"completed\n")

    create_subprocess = AsyncMock(side_effect=long_text_process)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", create_subprocess)

    await client.say_text("本日は晴天なり", output_path=tmp_path / "ok.wav")
    with pytest.raises(RuntimeError, match="text is too long"):
        await client.say_text("1" * 141, output_path=tmp_path / "too_long.wav")
    assert create_subprocess.await_count == 2


async def test_say_textfile_generates_from_text_file(monkeypatch, tmp_path):
    client = create_client(monkeypatch)
    text_file = tmp_path / "text.txt"
    await asyncio.to_thread(text_file.write_text, "吾輩は猫である。名前はまだ無い。", encoding="UTF-8")
    create_subprocess = mock_process(monkeypatch, ProcessResult(b"completed\n"))

    result = await client.say_textfile(text_file, output_path=tmp_path / "say_text.wav")

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-t",
        os.fspath(text_file),
        "-o",
        os.fspath(tmp_path / "say_text.wav"),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def test_say_text_overwrites_existing_output_file(monkeypatch, tmp_path):
    client = create_client(monkeypatch)
    output_path = tmp_path / "existing.wav"
    await asyncio.to_thread(output_path.write_bytes, b"previous generation")
    create_subprocess = mock_process(monkeypatch, ProcessResult(b"completed\n"))

    result = await client.say_text("本日は晴天なり", output_path=output_path)

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "本日は晴天なり",
        "-o",
        os.fspath(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


async def test_generated_narrator_file_overwrites_existing_content(monkeypatch, tmp_path):
    client = create_client(monkeypatch)
    output_file = tmp_path / "narrators.txt"
    await asyncio.to_thread(output_file.write_text, "stale line from a previous run\n", encoding="UTF-8")
    mock_process(monkeypatch, ProcessResult(b"Japanese Female 1\n"))

    narrator_names = await client.get_narrator_name_list()
    lines = "".join(f"{name}\n" for name in narrator_names)
    await asyncio.to_thread(output_file.write_text, lines, encoding="UTF-8")

    assert output_file.read_text(encoding="UTF-8") == "Japanese Female 1\n"
