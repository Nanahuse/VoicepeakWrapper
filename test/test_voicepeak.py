# Copyright (c) 2023 Nanahuse
# This software is released under the MIT License
# https://opensource.org/license/mit/

import pytest
import os


OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")


def clear_output():
    files = os.listdir(OUTPUT_PATH)

    for file in files:
        if file == ".gitignore":
            continue
        file_path = os.path.join(OUTPUT_PATH, file)
        if os.path.isfile(file_path):
            os.remove(file_path)


clear_output()


@pytest.mark.asyncio
async def test_get_narrator_list():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()
    narrators = await client.get_narrator_list()
    for narrator in narrators:
        with open(os.path.join(OUTPUT_PATH, "narrators.txt"), mode="w", encoding="UTF-8") as f:
            f.write(narrator.name)
            f.write(" : ")
            f.write(",".join(narrator.emotions))

    await client.say_text(
        "本日は快晴なり",
        output_path=os.path.join(OUTPUT_PATH, "narrator.wav"),
        narrator=narrators[0],
        emotions={narrators[0].emotions[1]: "100"},
    )


@pytest.mark.asyncio
async def test_say_test():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()

    await client.say_text("本日は快晴なり", output_path=os.path.join(OUTPUT_PATH, "test1.wav"))
    await client.say_text("本日は快晴なり", output_path=os.path.join(OUTPUT_PATH, "test2.wav"), speed=200, pitch=300)
    await client.say_text("本日は快晴なり", output_path=os.path.join(OUTPUT_PATH, "test3.wav"), speed=50, pitch=-300)


@pytest.mark.asyncio
async def test_error():
    import voicepeak_wrapper

    client = voicepeak_wrapper.Voicepeak()

    with pytest.raises(ValueError):
        await client.say_text("本日は快晴なり", output_path=os.path.join(OUTPUT_PATH, "error.wav"), speed=201)
    with pytest.raises(ValueError):
        await client.say_text("本日は快晴なり", output_path=os.path.join(OUTPUT_PATH, "error.wav"), speed=49)
    with pytest.raises(ValueError):
        await client.say_text("本日は快晴なり", output_path=os.path.join(OUTPUT_PATH, "error.wav"), pitch=-301)
    with pytest.raises(ValueError):
        await client.say_text("本日は快晴なり", output_path=os.path.join(OUTPUT_PATH, "error.wav"), pitch=301)

    with pytest.raises(RuntimeError):
        await client.say_text("1" * 141, output_path=os.path.join(OUTPUT_PATH, "error.wav"))
