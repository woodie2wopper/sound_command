# アンテナパターンのプロット

```bash
./plot_microphone_pattern.py -i microphone_pattern.txt
```

## 目的

- アンテナパターンをプロットする

## 仕様

1. ピーク強度とSN比をあらかじめ求めておく(serach_Peak_from_toneset.py)
2. 角度毎のピーク強度とSN比を表にする
3. ピーク強度とSN比を極座標でプロットする

- 入力オプション：
  - --help, -h: ヘルプを表示
  - --input-file, -i: ピーク強度とSN比の表のファイル
  - --output-file, -o: 出力ファイル名（デフォルトはplot_anntena_pattern.png）
  - --max-freq, -mf: プロットする最大周波数
  - --min-freq, -mnf: プロットする最小周波数
  - --max, -mx 数値: プロットする最大値（デフォルトは最大値）
  - --min, -mn 数値: プロットする最小値（デフォルトは0）
  - --column, -c: ピーク強度かSN比か（デフォルトはp）
  - --toneset, -t: トーンセットの周波数のマイクパターンをプロットする
  - --serch-range, -sr: ピークサーチ範囲（デフォルト：50）
  - --debug, -d: デバッグ情報を出力する

- 出力
  - 極座標でプロットする
  - 0度はXY平面のY軸方向を極座標の0度とする。
  - 角度は時計回りに増加する。
  - tonesetの周波数毎にプロットする。

- 入力ファイルフォーマット
  - 1行目：ヘッダー行
  - 2行目以降：角度,周波数,ピーク強度,SN比
  - `#` コメント行は読み飛ばす

- データ準備の例：
```bash
# tonesetの周波数の録音ピーク強度とSNRを角度毎に出力する
$ ls *deg*WAV | xargs -I@ serach_Peak_from_toneset.py -t toneset -ia @ -nf background_noise.txt -sr 10
# ファイル名から角度を取得してピーク強度とSN比を出力する
$  ls *deg*_cut.txt | xargs -I@ awk -F, '!/^#/{match(FILENAME, /^[0-9]+/);deg = substr(FILENAME, RSTART, RLENGTH); printf "%d,%s,%s,%s,%s\n",deg,$1,$2,$3,$4}' @ |sort -n >| microphone_pattern.txt 
# マイクパターンをプロットする
$ ./plot_microphone_pattern.py -i microphone_pattern.txt -o plot_microphone_pattern.png -t toneset -sr 10
```
