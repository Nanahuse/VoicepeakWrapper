# VoicepeakWrapper
VOICEPEAKの非公式ラッパーです。  
操作のたびにCUIからプロセスを起動必要があるため実行には時間がかかります。  
とくにget_narrator_listは再帰的に操作を行う必要があるため遅いです。

# install
```
pip install voicepeak-wrapper
```

# sample
```python
import asyncio
import voicepeak_wrapper

async def main():
    client = voicepeak_wrapper.Voicepeak()

    await client.say_text("本日は快晴なり", output_path="./test.wav") # 出力のサンプル

    narrators = await client.get_narrator_list() # ナレーターのリスト取得。時間がかかります。

asyncio.run(main())
```

パスを引数に取る箇所（`exe_path`、`output_path`、`text_path`）には、`str`の代わりに`pathlib.Path`も渡すことができます。

```python
import asyncio
from pathlib import Path

import voicepeak_wrapper

async def main():
    client = voicepeak_wrapper.Voicepeak(exe_path=Path(r"C:\Program Files\VOICEPEAK\voicepeak.exe"))

    await client.say_textfile(Path("./input.txt"), output_path=Path("./output.wav"))

asyncio.run(main())
```

# License
MITライセンス  
詳しくは[LICENSE](./LICENSE)を確認ください。