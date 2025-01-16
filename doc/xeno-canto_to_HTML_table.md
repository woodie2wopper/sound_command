# `xeno-canto_to_HTML_table.py` 仕様書

## 概要
xeno-cantoからダウンロードしたデータ（音声、メタデータ、ソナグラム）をHTML形式の表にまとめるスクリプトです。

## 前提条件
- xeno-canto APIラッパーのインストールが必要です
```bash
pip install xeno-canto
```

- データのダウンロード方法
```bash
# 例：アカハラのコールをダウンロード
xeno-canto -dl "Turdus chrysolaus" type:call
```

## ディレクトリ構造
```
.
├── dataset/
│   ├── audio/
│   │   └── PaleThrush/          # 英名のディレクトリ
│   │       ├── 282243.mp3       # ID.mp3形式の音声ファイル
│   │       └── ...
│   └── metadata/
│       └── PaleThrushtype_call/ # 種名+type_call
│           ├── page1.json       # メタデータ（ページごと）
│           └── page2.json
└── html/                        # 出力ディレクトリ
    └── all_table.html          # 生成されるHTML
```

## 入力オプション
- `-h, --help`: ヘルプの表示
- `-bn, --bird_name`: 学名（例: "Pale Thrush"）。デフォルトは'all'で全種を処理
- `-od, --output_dir`: 出力ディレクトリ（デフォルト: ./html）
- `-fi, --file_items`: メタデータの表示項目ファイル（指定がなければ全項目を表示）
- `-d, --debug`: デバッグモードを有効にする

## 使用例
```bash
# 全種のデータを処理
python xeno-canto_to_HTML_table.py

# 特定の種のデータのみ処理
python xeno-canto_to_HTML_table.py -bn "Pale Thrush"

# 特定の項目のみ表示
python xeno-canto_to_HTML_table.py -fi items.txt
```

## 出力
- HTML形式の表が生成されます
- 表には以下の情報が含まれます：
  - メタデータ（指定された項目）
  - ソナグラム画像（xeno-cantoサーバーから取得）
  - 音声プレーヤー（ローカルの音声ファイル）

## 注意事項
- メタデータは`page*.json`ファイルから読み込まれます
- 音声ファイルは英名のディレクトリ内にID.mp3形式で保存されている必要があります
- ソナグラムはxeno-cantoサーバーから直接取得されます（small サイズ）


