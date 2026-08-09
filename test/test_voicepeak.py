# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import asyncio
import os
from pathlib import Path
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
    process = ProcessResult(b"Japanese Female 1\nJapanese Male 1\n")
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
    process = ProcessResult(b"happy\nsad\n")
    mock_process(monkeypatch, process)

    assert await client.get_emotion_list("Japanese Female 1") == ("happy", "sad")


@pytest.mark.asyncio
async def test_get_narrator_list_uses_each_terminal_output(monkeypatch):
    client = create_client(monkeypatch)
    import voicepeak_wrapper

    processes = (
        ProcessResult(b"Japanese Female 1\nJapanese Male 1\n"),
        ProcessResult(b"happy\nsad\n"),
        ProcessResult(b"happy\nangry\n"),
    )
    mock_process(monkeypatch, *processes)

    assert await client.get_narrator_list() == (
        voicepeak_wrapper.Narrator("Japanese Female 1", ("happy", "sad")),
        voicepeak_wrapper.Narrator("Japanese Male 1", ("happy", "angry")),
    )


@pytest.mark.asyncio
async def test_say_text_returns_decoded_terminal_output(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
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
    process = ProcessResult(stderr=b"narrator not found\n")
    mock_process(monkeypatch, process)

    with pytest.raises(RuntimeError, match="narrator not found"):
        await client.get_emotion_list("unknown")


@pytest.mark.asyncio
async def test_init_accepts_path_for_exe_path(monkeypatch):
    monkeypatch.setenv("ProgramFiles", os.path.dirname(__file__))
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak(exe_path=Path(__file__))
    process = ProcessResult(b"Japanese Female 1\n")
    create_subprocess = mock_process(monkeypatch, process)

    assert await client.get_narrator_name_list() == ("Japanese Female 1",)
    create_subprocess.assert_awaited_once_with(
        __file__,
        "--list-narrator",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_say_text_accepts_path_for_output_path(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text("本日は晴天なり", output_path=Path("output.wav"))

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
async def test_say_textfile_accepts_paths(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_textfile(Path("input.txt"), output_path=Path("output.wav"))

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-t",
        "input.txt",
        "-o",
        "output.wav",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


def test_init_raises_when_exe_path_does_not_exist(monkeypatch):
    monkeypatch.setenv("ProgramFiles", os.path.dirname(__file__))
    import voicepeak_wrapper

    missing_path = os.path.join(os.path.dirname(__file__), "missing.exe")

    with pytest.raises(FileNotFoundError, match="VOICEPEAKの実行ファイルが見つかりません"):
        voicepeak_wrapper.Voicepeak(exe_path=missing_path)


@pytest.mark.asyncio
async def test_say_textfile_accepts_str_path(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_textfile("input.txt", output_path="output.wav")

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-t",
        "input.txt",
        "-o",
        "output.wav",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_say_textfile_uses_default_output_path(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_textfile("input.txt")

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-t",
        "input.txt",
        "-o",
        "./output.wav",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_say_text_accepts_narrator_name(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text("本日は晴天なり", narrator="naruko")

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "本日は晴天なり",
        "-n",
        "naruko",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_say_text_accepts_narrator_object(monkeypatch):
    client = create_client(monkeypatch)
    import voicepeak_wrapper

    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text("本日は晴天なり", narrator=voicepeak_wrapper.Narrator("naruko", ("happy",)))

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "本日は晴天なり",
        "-n",
        "naruko",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.asyncio
async def test_say_text_accepts_emotions(monkeypatch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text("本日は晴天なり", emotions={"happy": 100, "angry": 50})

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "本日は晴天なり",
        "-e",
        "happy=100,angry=50",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize("speed", [50, 200])
@pytest.mark.asyncio
async def test_say_text_accepts_valid_speed(monkeypatch, speed):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text("本日は晴天なり", speed=speed)

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "本日は晴天なり",
        "--speed",
        str(speed),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize("speed", [49, 201, 100.5, "100"])
@pytest.mark.asyncio
async def test_say_text_rejects_invalid_speed(monkeypatch, speed):
    client = create_client(monkeypatch)
    mock_process(monkeypatch, ProcessResult())

    with pytest.raises(ValueError, match="speedは50 - 200の範囲内の整数"):
        await client.say_text("本日は晴天なり", speed=speed)


@pytest.mark.parametrize("pitch", [-300, 300])
@pytest.mark.asyncio
async def test_say_text_accepts_valid_pitch(monkeypatch, pitch):
    client = create_client(monkeypatch)
    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text("本日は晴天なり", pitch=pitch)

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "本日は晴天なり",
        "--pitch",
        str(pitch),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


@pytest.mark.parametrize("pitch", [-301, 301, 0.5, "0"])
@pytest.mark.asyncio
async def test_say_text_rejects_invalid_pitch(monkeypatch, pitch):
    client = create_client(monkeypatch)
    mock_process(monkeypatch, ProcessResult())

    with pytest.raises(ValueError, match="pitchは-300 - 300の範囲内の整数"):
        await client.say_text("本日は晴天なり", pitch=pitch)


@pytest.mark.asyncio
async def test_say_text_with_all_options_builds_full_command(monkeypatch):
    client = create_client(monkeypatch)
    import voicepeak_wrapper

    process = ProcessResult(b"completed\n")
    create_subprocess = mock_process(monkeypatch, process)

    result = await client.say_text(
        "こんにちは",
        output_path="out.wav",
        narrator=voicepeak_wrapper.Narrator("Japanese Female 1", ("happy", "sad")),
        emotions={"happy": 100, "sad": 50},
        speed=120,
        pitch=-50,
    )

    assert result == "completed\n"
    create_subprocess.assert_awaited_once_with(
        __file__,
        "-s",
        "こんにちは",
        "-o",
        "out.wav",
        "-n",
        "Japanese Female 1",
        "-e",
        "happy=100,sad=50",
        "--speed",
        "120",
        "--pitch",
        "-50",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )


def test_make_say_command_rejects_text_and_text_file_together(monkeypatch):
    client = create_client(monkeypatch)

    with pytest.raises(ValueError, match="textかtext_fileの一方のみ指定してください"):
        client._Voicepeak__make_say_command(text="text", text_file="input.txt")


def test_make_say_command_requires_text_or_text_file(monkeypatch):
    client = create_client(monkeypatch)

    with pytest.raises(ValueError, match="textまたはtext_fileが設定されている必要があります"):
        client._Voicepeak__make_say_command()


def test_make_say_command_rejects_invalid_text_type(monkeypatch):
    client = create_client(monkeypatch)

    with pytest.raises(ValueError, match="textまたはtext_fileが不正な値です"):
        client._Voicepeak__make_say_command(text=123)  # type: ignore[arg-type]


def test_make_say_command_rejects_invalid_text_file_type(monkeypatch):
    client = create_client(monkeypatch)

    with pytest.raises(ValueError, match="textまたはtext_fileが不正な値です"):
        client._Voicepeak__make_say_command(text="text", text_file=123)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_get_emotion_list_returns_empty_tuple_for_empty_output(monkeypatch):
    client = create_client(monkeypatch)
    mock_process(monkeypatch, ProcessResult(b""))

    assert await client.get_emotion_list("Japanese Female 1") == ()


@pytest.mark.asyncio
async def test_get_narrator_name_list_handles_output_without_trailing_newline(monkeypatch):
    client = create_client(monkeypatch)
    mock_process(monkeypatch, ProcessResult(b"Japanese Female 1"))

    assert await client.get_narrator_name_list() == ("Japanese Female 1",)


@pytest.mark.asyncio
async def test_get_narrator_list_returns_empty_for_empty_output(monkeypatch):
    client = create_client(monkeypatch)
    mock_process(monkeypatch, ProcessResult(b""))

    assert await client.get_narrator_list() == ()
