# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import asyncio
import os
from dataclasses import dataclass
from os import PathLike
from pathlib import Path


@dataclass
class Narrator:
    name: str
    emotions: tuple[str, ...]


@dataclass(frozen=True)
class _SayRequest:
    text: str | None = None
    text_file: str | PathLike[str] | None = None
    output_path: str | PathLike[str] | None = None
    narrator: Narrator | str | None = None
    emotions: dict[str, int] | None = None
    speed: int | None = None
    pitch: int | None = None


_SPEED_RANGE = (50, 200)
_PITCH_RANGE = (-300, 300)
_DEFAULT_EXE_PATH = os.path.join(  # noqa: PTH118
    os.environ["ProgramFiles"],  # noqa: SIM112
    "VOICEPEAK",
    "voicepeak.exe",
)


def _append_range(args: list[str], option: str, label: str, value: int | None, value_range: tuple[int, int]) -> None:
    if value is None:
        return
    if isinstance(value, int) and value_range[0] <= value <= value_range[1]:
        args += [option, str(value)]
        return
    raise ValueError(f"{label}は{value_range[0]} - {value_range[1]}の範囲内の整数")


class Voicepeak:
    def __init__(
        self,
        exe_path: str | PathLike[str] = _DEFAULT_EXE_PATH,
    ) -> None:
        """
        標準のインストール先ではない場所にVOICEPEAKインストールした場合はexe_pathを指定してください。

        Args:
            exe_path (str | os.PathLike[str], optional): voicepeak.exeへのパス。strまたはpathlib.Pathで指定できる。
                Defaultは標準のインストール先。
        """
        if not Path(exe_path).exists():
            raise FileNotFoundError("VOICEPEAKの実行ファイルが見つかりません")
        self.__exe_path = exe_path

    async def __async_run(self, args: list[str]) -> str:
        proc = await asyncio.create_subprocess_exec(
            os.fspath(self.__exe_path),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if len(stderr) != 0:
            error_message = stderr.decode()
            raise RuntimeError(error_message)

        return stdout.decode()

    @staticmethod
    def __append_text_args(args: list[str], request: _SayRequest) -> None:
        text = request.text
        text_file = os.fspath(request.text_file) if request.text_file is not None else None
        match text, text_file:
            case str(), str():
                raise ValueError("textかtext_fileの一方のみ指定してください")
            case str(), None:
                args += ["-s", text]
            case None, str():
                args += ["-t", text_file]
            case None, None:
                raise ValueError("textまたはtext_fileが設定されている必要があります。")
            case _:
                raise ValueError("textまたはtext_fileが不正な値です。")

    @staticmethod
    def __append_narrator(args: list[str], narrator: Narrator | str | None) -> None:
        match narrator:
            case Narrator():
                args += ["-n", narrator.name]
            case str():
                args += ["-n", narrator]
            case None:
                pass

    @staticmethod
    def __append_emotions(args: list[str], emotions: dict[str, int] | None) -> None:
        if emotions is not None:
            args += ["-e", ",".join(f"{param}={value}" for param, value in emotions.items())]

    def __make_say_command(self, request: _SayRequest) -> list[str]:
        args: list[str] = []
        self.__append_text_args(args, request)
        if request.output_path is not None:
            args += ["-o", os.fspath(request.output_path)]
        self.__append_narrator(args, request.narrator)
        self.__append_emotions(args, request.emotions)
        _append_range(args, "--speed", "speed", request.speed, _SPEED_RANGE)
        _append_range(args, "--pitch", "pitch", request.pitch, _PITCH_RANGE)
        return args

    async def say_text(  # noqa: PLR0913
        self,
        text: str,
        *,
        output_path: str | PathLike[str] | None = None,
        narrator: Narrator | str | None = None,
        emotions: dict[str, int] | None = None,
        speed: int | None = None,
        pitch: int | None = None,
    ) -> str:
        """
        テキストを読み上げたwavファイルを保存する。

        Args:
            text (str): 読み上げるテキスト

            output_path (str | os.PathLike[str] | None, optional): wavファイル出力先。strまたはpathlib.Pathで指定可。
                指定しないとvoicepeak.exeと同じ階層にoutput.wavが生成される。 Defaults to None.

            narrator (Narrator | str | None, optional): 読み上げを行うナレータの種類。
                Narrator型またはstr型の名前で指定する。 Defaults to None.

            emotions (dict[str, int] | None, optional): 読み上げ時の感情の指示。
                形式は{"感情名","値"}の辞書型。 Defaults to None.

            speed (int | None, optional): 読み上げのスピード。100が等倍。50~200の範囲。 Defaults to None.

            pitch (int | None, optional): 読み上げのピッチ。0が通常。-300~300の範囲。 Defaults to None.
        """
        return await self.__async_run(
            self.__make_say_command(
                _SayRequest(
                    text=text,
                    output_path=output_path,
                    narrator=narrator,
                    emotions=emotions,
                    speed=speed,
                    pitch=pitch,
                )
            )
        )

    async def say_textfile(  # noqa: PLR0913
        self,
        text_path: str | PathLike[str],
        *,
        output_path: str | PathLike[str] = "./output.wav",
        narrator: Narrator | str | None = None,
        emotions: dict[str, int] | None = None,
        speed: int | None = None,
        pitch: int | None = None,
    ) -> str:
        """
        テキストファイル内のテキストを読み上げたwavファイルを保存する。

        Args:
            text_path (str | os.PathLike[str]): 読み上げるテキストファイルのパス。strまたはpathlib.Pathで指定できる。

            output_path (str | os.PathLike[str], optional): wavファイル出力先。strまたはpathlib.Pathで指定できる。
                Defaultはoutput.wavが生成される。

            narrator (Narrator | str | None, optional): 読み上げを行うナレータの種類。
                Narrator型またはstr型の名前で指定する。 Defaults to None.

            emotions (dict[str, int] | None, optional): 読み上げ時の感情の指示。
                形式は{"感情名","値"}の辞書型。 Defaults to None.

            speed (int | None, optional): 読み上げのスピード。100が等倍。50~200の範囲。 Defaults to None.

            pitch (int | None, optional): 読み上げのピッチ。0が通常。-300~300の範囲。 Defaults to None.
        """
        return await self.__async_run(
            self.__make_say_command(
                _SayRequest(
                    text_file=text_path,
                    output_path=output_path,
                    narrator=narrator,
                    emotions=emotions,
                    speed=speed,
                    pitch=pitch,
                )
            )
        )

    async def get_narrator_list(self) -> tuple[Narrator, ...]:
        """
        ナレーターとその感情名一覧を取得します。

        Returns:
            tuple[Narrator]: ナレーター一覧
        """
        narrators = await self.get_narrator_name_list()
        narrator_list = []
        for name in narrators:
            emotions = await self.get_emotion_list(name)
            narrator_list.append(Narrator(name, emotions))
        return tuple(narrator_list)

    async def get_narrator_name_list(self) -> tuple[str, ...]:
        """
        使用可能なナレーターを取得します。

        Returns:
            tuple[str]: ナレーターの名前一覧
        """
        return tuple(tmp for tmp in (await self.__async_run(["--list-narrator"])).splitlines())

    async def get_emotion_list(self, name: str) -> tuple[str, ...]:
        """
        ナレーターの感情名一覧を取得する。

        Args:
            name (str): ナレーターの名前

        Returns:
            tuple[str]: ナレーターの感情名一覧
        """
        return tuple(tmp for tmp in (await self.__async_run(["--list-emotion", name])).splitlines())
