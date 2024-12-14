# 時間毎のヒストグラムデータの生成

---

date: 2024-12-14

author: Hideki Osaka

aim: アノテーションしたデータからヒストグラムを書く

---

### コマンド名：

- make_histdata_each_time.py

### 入力オプション：

- --help, -h: 使い方の表示
- --input, -i: データのファイル名（タブ区切りファイルを前提としている）
- --output, -o: ヒストグラムのファイル名（デフォルトでは"入力ファイルのボディー_hist_each_time.csv"）
- --separator, -s: データの区切り文字（デフォルトはタブ）
- --type, -t [all,zeep,call]: 指定のtypeのヒストグラムを作成する(all: 全てのデータ, zeep: zeepのデータ, call: callのデータ)
- --start_time, -st: ヒストグラムの開始時間（デフォルトは18:00）
- --end_time, -et: ヒストグラムの終了時間（デフォルトは06:00）
- --bin_size, -b: ヒストグラムのビンサイズ（単位は分でデフォルトは60分）
- --title, -ti: ヒストグラムのタイトル（デフォルトは"Histogram of data")  

### 機能：

- データのファイル名を指定すると、そのデータを時間毎にヒストグラムを作成する
- データを時間毎に区別するのは，”Begin Clock Time"の列を使用している
- typeによって，データの区別を変えることができる．データの"type"の列で指定の文字列を含む行を抽出する
- separatorによって，データの区切り文字を変えることができる
- ヒストグラムは18:00~06:00の１時間毎であるが，start_timeとend_timeで指定することができる
- bin_sizeでビンサイズを指定することができる単位は分である．

### データの準備

```bash

```

- データの入っているディレクトリ
  ./Table/

- データのファイル名
  ./Table/combined_file.txt
