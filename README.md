# sound_command



- NFC関連のlinux/pythonツールです。
- MacOSのterminalで作っているので、そのほかのプラットフォームは検証されていません

## 前提

- python3, ffmpegが入っていること

## コマンド一覧

| command name                    | function                                                     | note |
| ------------------------------- | ------------------------------------------------------------ | ---- |
| merge_sounds_same_birth_time.py | ICレコーダで分割された音声ファイル(WAV/MP3)をファイル名のシリアル順にマージします。 | -    |
| divide_1_hour.py                | 長時間録音を１時間毎に分割します。オプションで録音開始時間から１時間毎にするのか、xx:00:00と区切りのいい時間毎にするか選べます。 | -    |

## 使い方

- python <command.py> -hでhelpが表示されます。

## ライセンス

- MIT
