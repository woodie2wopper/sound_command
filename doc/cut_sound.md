# cut_sound.pyの説明書


## コマンド名：cut_sound.py
date: 2024-11-28

version:0.1

author: Hideki Osaka(toriR. Lab)

## 1. 目的

- 音源の指定時刻から継続時間を指定して音源を切り取る。

## 2. 仕様

- 入力ファイル(input.wav)は10秒程度のwavもしくはmp3データである。
- 出力ファイルのフォーマットは拡張子で指定する。
- ffmpegのラッパーである。

- 入力オプション：
  - --help, -h：ヘルプ
  - --input, -i ファイル名：入力ファイル名
  - --verbose, -v：詳細モード(音源の長さ、サンプリングレート、チャンネル数、last modified time, ファイル名を表示する)
  - --start, -s 数値：切り取る開始時刻（秒）
  - --Duration, -D 数値：切り取る継続時間（秒）
  - --output, -o ファイル名：出力ファイル名
  - --debug, -d：デバッグモード

- コマンド例）${CMD} -s 10 -D 5 -o output.mp3 -i input.wav
