# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import asyncio
from dataclasses import dataclass
import os


@dataclass
class Narrator(object):
    name: str
    emotions: tuple[str, ...]


class Voicepeak:
    def __init__(
        self,
        exe_path: str = os.path.join(os.environ["ProgramFiles"], "VOICEPEAK", "voicepeak.exe"),
    ):
        """
        標準のインストール先ではない場所にVOICEPEAKインストールした場合はexe_pathを指定してください。

        Args:
            exe_path (str, optional): voicepeak.exeへのパス。Defaultは標準のインストール先。
        """

        if not os.path.exists(exe_path):
            raise FileNotFoundError("VOICEPEAKの実行ファイルが見つかりません")
        self.__exe_path = exe_path

    async def __async_run(self, cmd: str) -> str:
        proc = await asyncio.create_subprocess_shell(
            f'"{self.__exe_path}" {cmd}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await proc.communicate()

        if len(stderr) != 0:
            error_message = stderr.decode()
            raise RuntimeError(error_message)

        return stdout.decode()

    def __make_say_command(
        self,
        text: str | None = None,
        text_file: str | None = None,
        output_path: str | None = None,
        narrator: Narrator | str | None = None,
        emotions: dict[str, int] | None = None,
        speed: int | None = None,
        pitch: int | None = None,
    ) -> str:
        command = list()

        match text, text_file:
            case str(), str():
                raise ValueError("textかtext_fileの一方のみ指定してください")
            case str(), None:
                command.append(f'-s "{text}"')
            case None, str():
                command.append(f'-t "{text_file}"')
            case None, None:
                raise ValueError("textまたはtext_fileが設定されている必要があります。")
            case _:
                raise ValueError("textまたはtext_fileが不正な値です。")

        if output_path is not None:
            command.append(f'-o "{output_path}"')

        match narrator:
            case Narrator():
                command.append(f'-n "{narrator.name}"')
            case str():
                command.append(f'-n "{narrator}"')
            case None:
                pass

        if emotions is not None:
            command.append(f'-e {",".join(f"{param}={value}" for param, value in emotions.items())}')

        SPEED_RANGE = (50, 200)
        if isinstance(speed, int) and (SPEED_RANGE[0] <= speed <= SPEED_RANGE[1]):
            command.append(f"--speed {speed}")
        elif speed is None:
            pass
        else:
            raise ValueError(f"speedは{SPEED_RANGE[0]} - {SPEED_RANGE[1]}の範囲内の整数")

        PITCH_RANGE = (-300, 300)
        if isinstance(pitch, int) and (PITCH_RANGE[0] <= pitch <= PITCH_RANGE[1]):
            command.append(f"--pitch {pitch}")
        elif pitch is None:
            pass
        else:
            raise ValueError(f"pitchは{PITCH_RANGE[0]} - {PITCH_RANGE[1]}の範囲内の整数")

        return " ".join(command)

    async def say_text(
        self,
        text: str,
        *,
        output_path: str | None = None,
        narrator: Narrator | str | None = None,
        emotions: dict[str, int] | None = None,
        speed: int | None = None,
        pitch: int | None = None,
    ):
        """
        テキストを読み上げたwavファイルを保存する。

        Args:
            text (str): 読み上げるテキスト

            output_path (str | None, optional): wavファイル出力先。指定しないとvoicepeak.exeと同じ階層にoutput.wavが生成される。 Defaults to None.

            narrator (Narrator | str | None, optional): 読み上げを行うナレータの種類。Narrator型またはstr型の名前で指定する。 Defaults to None.

            emotions (dict[str, int] | None, optional): 読み上げ時の感情の指示。形式は{"感情名","値"}の辞書型。 Defaults to None.

            speed (int | None, optional): 読み上げのスピード。100が等倍。50~200の範囲。 Defaults to None.

            pitch (int | None, optional): 読み上げのピッチ。0が通常。-300~300の範囲。 Defaults to None.
        """
        return await self.__async_run(
            self.__make_say_command(
                text=text,
                output_path=output_path,
                narrator=narrator,
                emotions=emotions,
                speed=speed,
                pitch=pitch,
            )
        )

    async def say_textfile(
        self,
        text_path: str,
        *,
        output_path: str = "./output.wav",
        narrator: Narrator | str | None = None,
        emotions: dict[str, int] | None = None,
        speed: int | None = None,
        pitch: int | None = None,
    ):
        """
        テキストファイル内のテキストを読み上げたwavファイルを保存する。

        Args:
            text_path (str): 読み上げるテキストファイルのパス

            output_path (str , optional): wavファイル出力先。Defaultはoutput.wavが生成される。

            narrator (Narrator | str | None, optional): 読み上げを行うナレータの種類。Narrator型またはstr型の名前で指定する。 Defaults to None.

            emotions (dict[str, int] | None, optional): 読み上げ時の感情の指示。形式は{"感情名","値"}の辞書型。 Defaults to None.

            speed (int | None, optional): 読み上げのスピード。100が等倍。50~200の範囲。 Defaults to None.

            pitch (int | None, optional): 読み上げのピッチ。0が通常。-300~300の範囲。 Defaults to None.
        """
        return await self.__async_run(
            self.__make_say_command(
                text_file=text_path,
                output_path=output_path,
                narrator=narrator,
                emotions=emotions,
                speed=speed,
                pitch=pitch,
            )
        )

    async def get_narrator_list(self) -> tuple[Narrator, ...]:
        """
        ナレーターとその感情名一覧を取得します。

        Returns:
            tuple[Narrator]: ナレーター一覧
        """
        narrators = await self.get_narrator_name_list()
        narrator_list = list()
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
        return tuple(tmp for tmp in (await self.__async_run("--list-narrator")).splitlines())

    async def get_emotion_list(self, name: str) -> tuple[str, ...]:
        """
        ナレーターの感情名一覧を取得する。

        Args:
            name (str): ナレーターの名前

        Returns:
            tuple[str]: ナレーターの感情名一覧
        """
        return tuple(tmp for tmp in (await self.__async_run(f'--list-emotion "{name}"')).splitlines())
