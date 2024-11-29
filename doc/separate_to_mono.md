# ステレオの音源をモノラルに分割する

```bash
~/GitHub/sound_command/separate_to_mono.py -i input.wav -ol output_left.wav -or output_right.wav
```

## 目的

- ステレオの音源をモノラルに分割する
- ffmpegのラッパーである

## 仕様

- 入力オプション：
  - --help, -h: ヘルプを表示
  - --input-file, -i: 入力ファイル名
  - --output-left, -ol: 左モノラル出力ファイル名
  - --output-right, -or: 右モノラル出力ファイル名
  - --debug, -d: デバッグ情報を出力する


- データ準備の例：
```bash
```