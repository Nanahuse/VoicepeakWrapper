# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import pytest
import os

TEST_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(TEST_DIRECTORY, "output")


@pytest.mark.asyncio
async def test_get_narrator_list():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    narrators = await client.get_narrator_list()
    with open(os.path.join(OUTPUT_PATH, "narrators.txt"), mode="w", encoding="UTF-8") as f:
        for narrator in narrators:
            f.write(narrator.name)
            f.write(" : ")
            f.write(", ".join(narrator.emotions))
            f.write("\n")

            await client.say_text(
                "本日は晴天なり",
                output_path=os.path.join(OUTPUT_PATH, f"narrator_{narrator.name}.wav"),
                narrator=narrator,
                emotions={narrator.emotions[1]: "100"},
            )


@pytest.mark.asyncio
async def test_get_narrator_name_list():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    narrator_names = await client.get_narrator_name_list()
    with open(os.path.join(OUTPUT_PATH, "narrator_names.txt"), mode="w", encoding="UTF-8") as f:
        for name in narrator_names:
            f.write(f"{name}\n")


@pytest.mark.asyncio
async def test_get_emotion_list():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()

    narrator_names = await client.get_narrator_name_list()
    with open(os.path.join(OUTPUT_PATH, "emotions.txt"), mode="w", encoding="UTF-8") as f:
        for name in narrator_names:
            emotion_list = await client.get_emotion_list(name)

            f.write(name)
            f.write(" : ")
            f.write(", ".join(emotion_list))
            f.write("\n")

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
