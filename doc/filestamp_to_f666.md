# filestamp_to_f666.py 仕様書

## 概要
音声・動画ファイルのタイムスタンプを利用して、666フォーマット（YYMMDD_HHMMSS_HHMMSS）のファイル名を生成するツール。
タイムスタンプと録音時間から、録音開始時刻と終了時刻を含むファイル名を生成します。

## 基本情報
- スクリプト名: filestamp_to_f666.py
- 動作環境: Python3
- 依存関係: ffprobe（音声・動画ファイルの長さ取得用）

## 重要な注意事項
- 既に666フォーマット（YYMMDD_HHMMSS_HHMMSS_*）のファイル名を持つファイルは処理をスキップします
- ファイル名が666フォーマットかどうかは以下の条件で判定します：
  - 最初の部分が6桁の数字（YYMMDD）
  - 2番目と3番目の部分が6桁の数字（HHMMSS）
  - アンダースコア（_）で区切られている
- ファイル名に含まれるスペースは自動的にハイフン（-）に置換されます
  - 録音機器名（-i/--item）のスペース
  - 森下フォーマットの鳥の種類（-b/--bird-type）のスペース
  - 森下フォーマットの場所（-l/--location）のスペース
  - 森下フォーマットの観察者名（-n/--observer）のスペース

## タイムスタンプ処理
- 使用するタイムスタンプ: ファイルの最終更新時刻（Last Modified Time）
- 取得方法: `os.path.getmtime()`を使用
- 時刻の扱い：
  - `-s/--start-time`指定時: 最終更新時刻を録音開始時刻として扱う
  - `-e/--end-time`指定時: 最終更新時刻を録音終了時刻として扱う
  - `-T/--timestamp`指定時: 指定された時刻を使用（最終更新時刻は無視）
  - `-t/--timediff`指定時: 指定された時差を適用

## オプション
| オプション | 引数 | 説明 | デフォルト |
|------------|------|------|------------|
| -s, --start-time | なし | ファイルスタンプを録音開始時間として扱う | - |
| -e, --end-time | なし | ファイルスタンプを録音終了時間として扱う | - |
| -T, --timestamp | date time | 録音時刻を指定（例: 241031 123345） | - |
| -i, --item | item | 録音機器の指定（DR05, DR05X等） | none |
| -f, --format | mf | 出力フォーマット指定（mf: 森下フォーマット） | - |
| -t, --timediff | ±HHMMSS | 時差指定（例: +090000） | +000000 |
| -d, --output-dir | dir | 出力ディレクトリ指定 | 入力と同じ |
| -o, --output | mv/cp | 出力コマンド | mv |
| -b, --bird-type | name | 鳥の種類（森下フォーマット用） | - |
| -l, --location | place | 場所（森下フォーマット用） | - |
| -n, --observer | name | 観察者名（森下フォーマット用） | - |

## 使用例
```bash
# タイムスタンプを録音終了時刻として扱う
filestamp_to_f666.py -e input.wav
# 出力例: mv input.wav 240305_172500_183000_none_input.wav

# タイムスタンプを録音開始時刻として扱う
filestamp_to_f666.py -s input.wav
# 出力例: mv input.wav 240305_183000_193500_none_input.wav

# 録音時刻を直接指定（終了時刻として扱う）
filestamp_to_f666.py -e -T 240305 183000 input.wav
# 出力例: mv input.wav 240305_172500_183000_none_input.wav

# 時差を指定（UTC→日本時間への変換など）
filestamp_to_f666.py -e -t +090000 input.wav
# 出力例: mv input.wav 240306_033000_043500_none_input.wav

# 録音機器を指定
filestamp_to_f666.py -e -i DR05 input.wav
# 出力例: mv input.wav 240305_183000_193500_DR05_input.wav

# 森下フォーマットで出力
filestamp_to_f666.py -s -f mf -b "モズ高鳴き" -l "東京都国分寺市" -n "観察者名" input.wav
# 出力例: mv input.wav モズ高鳴き_20240305183000_東京都国分寺市_観察者名.wav

# 複数ファイルの一括処理
filestamp_to_f666.py -e -i DR05 *.wav

# コピーして処理
filestamp_to_f666.py -e -o cp -d output_dir input.wav
# 出力例: cp input.wav output_dir/240305_183000_193500_none_input.wav

# 年を修正する例（2024年→2023年）
filestamp_to_f666.py -e -T 230305 183000 input.wav
# 出力例: mv input.wav 230305_183000_193500_none_input.wav

# 年を修正する例（2024年→2025年）
filestamp_to_f666.py -e -T 250305 183000 input.wav
# 出力例: mv input.wav 250305_183000_193500_none_input.wav
```

## 出力形式
1. 666フォーマット（デフォルト）:
   - 形式: `YYMMDD_HHMMSS_HHMMSS_ITEM_ORIGINAL.EXT`
   - 例: `240305_183000_193500_DR05_input.wav`

2. 森下フォーマット（-f mf指定時）:
   - 形式: `[鳥の種類]_[YYYYMMDDHHMMSS]_[場所]_[観察者名].EXT`
   - 例: `モズ高鳴き_20240305183000_東京都国分寺市_観察者名.wav`

## 注意事項
1. ffprobeコマンドが必要です（音声・動画ファイルの長さ取得用）
2. -s/--start-time または -e/--end-time のいずれかを必ず指定してください
3. 時差指定は必ず±HHMMSS形式で指定してください
4. 森下フォーマット使用時は -b, -l, -n オプションが必須です
5. ファイル名の変更前に、生成される名前を確認することを推奨します
6. 年の修正は -T オプションを使用してください（時差指定ではなく）