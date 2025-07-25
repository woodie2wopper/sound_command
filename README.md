# 1. README(sound_command)



- NFC関連のlinux/pythonツールです。
- MacOSのterminalで作っているので、そのほかのプラットフォームは検証されていません

## 1.1. 前提

- python3, ffmpegが入っていること

## 1.2. コマンド一覧

| command name                    | function                                                     | note                                                         |
| ------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| calculate_recording_times.py    | 音声ファイルの録音時間を集計します。ディレクトリごとの総録音時間、ファイル数、総容量、最終更新日時を表示します。 | ファイル名は666形式（YYMMDD_HHMMSS_HHMMSS）を想定しています。 |
| merge_sounds_same_birth_time.py | ICレコーダで分割された音声ファイル(WAV/MP3)をファイル名のシリアル順にマージします。 | 同じタイムスタンプのファイルのみ入っていることを前提としています。またファイル間にギャップがあってもパディングはしていません。 |
| divide_1_hour.py                | 長時間録音を１時間毎に分割します。オプションで録音開始時間から１時間毎にするのか、xx:00:00と区切りのいい時間毎にするか選べます。 | ファイル名は６６６形式にしてください。666形式とは6桁の3つの数字が"_"で区切られており、それぞれ、年月日、録音開始時刻、録音終了時刻です。録音開始時刻を使っています。 |
| serach_Peak_from_toneset.py     | 倍音関係にない複数の純音の組み（トーンセット）が同時に再生された10秒の音源を録音したときの、トーンセットの周波数毎に録音からピーク強度とSN比を求める。 | README_generate_noisefloor.mdをご覧ください                  |
| generate_noise_floor.py         | 背景録音音源からトーンセットに応じたノイズフロアを生成する. 背景ノイズを録音してください。search_Peak_from_toneset.pyの各周波数のノイズフロアを定義します。移動平均量は40ぐらいが良さそうです。 | README_serach_Peak_from_toneset.md                           |
| batch.py                       | マイクパターンを求めるバッチ処理。マイクパターンを求めるためには、serach_Peak_from_toneset.pyを実行してください。 |                            |
| make_histdata_each_time.py     | データを時間毎に分割してヒストグラムを作成します。 | RavenProのannotation TableDataの編集を想定しています． |
| show_hist.py                   | ヒストグラムを表示します。 | make_histdata_each_time.pyで生成されたヒストグラムデータを入力に想定しています． |
| sound_clip_spectrogram.py      | 音源から指定時刻の音のスペクトログラムと音を出力します。 |  |
| xeno-canto_to_HTML_table.py     | xeno-cantoからダウンロードしたデータ（音声、メタデータ、ソナグラム）をHTML形式の表にまとめるスクリプトです。 | doc/xeno-canto_to_HTML_table.md |
| convert_bird_names.py           | 指定のディレクトリ名を学名から英語名に、またその逆に変換するコマンドを発行します。 | 例） `convert_bird_names.py . -d en2sci | sh -C` |
| json_to_sqlite.py              | 音声メタデータのJSONファイルをSQLiteデータベースに変換します。xeno-cantoやeBirdなどの音声データベースに対応。 | オプション: --origin (音源の種類), --debug (データベースの初期化), --verbose (詳細な出力) |

## 1.3. ドキュメント

各コマンドの詳細な使用方法や仕様については、以下のドキュメントを参照してください：

### 音声処理・分析
- [calculate_recording_times.md](doc/calculate_recording_times.md) - 録音時間集計スクリプトの詳細仕様
- [divide_1_hour.md](doc/divide_1_hour.md) - 長時間録音の1時間分割スクリプトの詳細仕様
- [sound_clip_spectrogram.md](doc/sound_clip_spectrogram.md) - 音声クリップとスペクトログラム生成

### 音声分析・測定
- [searach_Peak_from_toneset.md](doc/searach_Peak_from_toneset.md) - トーンセットからのピーク検出とSN比測定
- [generate_noisefloor.md](doc/generate_noisefloor.md) - ノイズフロア生成
- [batch.md](doc/batch.md) - マイクパターン測定のバッチ処理

### データ処理・変換
- [xeno-canto_to_HTML_table.md](doc/xeno-canto_to_HTML_table.md) - xeno-cantoデータのHTML表変換
- [make_histdata_each_time.md](doc/make_histdata_each_time.md) - 時間別ヒストグラムデータ生成

### ユーティリティ
- [filestamp_to_f666.md](doc/filestamp_to_f666.md) - ファイルスタンプから666形式への変換
- [change_filestamp.md](doc/change_filestamp.md) - ファイルスタンプ変更
- [find_calls.md](doc/find_calls.md) - コール検索
- [auto-versioning.md](doc/auto-versioning.md) - 自動バージョニング
- [time_voice_match.md](doc/time_voice_match.md) - 時間と音声のマッチング
- [add_epoch.md](doc/add_epoch.md) - エポック時間追加
- [plot_microphone_pattern.md](doc/plot_microphone_pattern.md) - マイクパターンプロット
- [separate_to_mono.md](doc/separate_to_mono.md) - ステレオからモノラル分離
- [cut_sound.md](doc/cut_sound.md) - 音声カット

## 1.4. 使い方

- python <command.py> -hでhelpが表示されます。
## 1.5. 共通のオプション

| ショートオプション | ロングオプション | 説明 | デフォルト |
| --- | --- | --- | --- |
| -d | --debug | デバッグモード |  |
| -i | --input-file | 入力ファイル |  |
| -o | --output-file | 出力ファイル |  |
| -fs | --fft-size | FFTサイズ | 2048 |
| -ov | --overlap | overlap | 0.5 |
| -w | --width | スペクトログラムの横幅 | 200 |
| -ht | --height | スペクトログラムの縦幅 | 100 |
| -cm | --colormap | スペクトログラムの色調 | viridis |
| -lf | --low-freq | スペクトログラムの最低周波数 | 0.0 |
| -hf | --high-freq | スペクトログラムの最高周波数 | 22100.0 |
| -mx | --max | スペクトログラムの強度の最大値 |  |
| -mn | --min | スペクトログラムの強度の最小値 |  |

## 1.6. ライセンス

このプロジェクトはPublicリポジトリとして公開されています。

- MIT
