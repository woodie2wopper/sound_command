# 角度ごとのモノラル，もしくはステレオ音源と背景ノイズからマイクパターンを求めるバッチファイル

## マイクパターンの求め方

- 角度ごとにモノラル，もしくはステレオ音源と背景ノイズからマイクパターンを求める
- 音源がモノラルの場合は指定入力ディレクトリにある音源データをそのまま処理する
- 音源がステレオの場合はright, leftのディレクトリを作成し，それぞれのチャネルの音源をディレクトリに分けてモノラル処理を行う
- マイクパターンはピーク強度とSN比を求める
- マイクパターンは極座標でプロットする
- マイクパターンはトーンセットの周波数毎にプロットする
- マイクパターンは角度毎にプロットする
- ノイズフロアのフィッティングはファイル指定もしくは自動で求める（自動で求める場合は，ノイズフロアフィッティング曲線を表示して終了する）

## 外部コマンド

- separate_stereo.py
- searach_Peak_from_toneset.py
- plot_microphone_pattern.py
- ffprobe
- ffmpeg

## オプション
- --help, -h: ヘルプを表示する
- --debug, -d: デバッグ情報を出力する
- --toneset, -t: トーンセットの周波数のマイクパターンをプロットする
- --serch-range, -sr: ピークサーチ範囲（デフォルト：50）
- --low-freq, -lf: ピークサーチの下限周波数（デフォルト：2500）
- --high-freq, -hf: ピークサーチの上限周波数（デフォルト：22000）
- --max, -mx: マイクパターンの最大値（デフォルト：45）
- --min, -mn: マイクパターンの最小値（デフォルト：-20）
- --input-dir, -id: 入力ディレクトリ（デフォルト：./）
- --output-file, -o: マイクパターンの出力ファイル名（デフォルト：microphone_pattern.txt）
- --input-noise-floor, -in: ノイズフロアの入力ファイル名（デフォルト：noise_floor.txt）
- --input-fit-curve-coeff, -ifc: ノイズフロア推定のためのフィッティング曲線の２次係数ファイル（デフォルト：noise_cut_fit_coeff.txt）．このオプションが指定されていない場合は，ノイズフロアの録音データから自動で求める．
- --fft-size, -fs: FFTサイズ（デフォルト：2048）
- --overlap, -ov: オーバーラップ率（デフォルト：0）
- --moving-average, -ma: ノイズフロア推定のための移動平均ウィンドウサイズ（デフォルト：0）
- --fit-curve, -fc: ノイズフロア推定のためのフィッティング曲線を使用する
- --remove-signals, -rs: ノイズフロア推定のための信号のピークをフィッティング曲線で除去する
- --peak-floor, -pf: ピーク削除のためのノイズフロアの範囲（デフォルト：50）
- --spectrogram, -sp: スペクトログラムの出力
- --stereo, -st: ステレオファイルを自動的に左右に分割して処理

## 準備
- コマンドのパスが通っていること
- 入力音源データとして角度ごとの音源データが指定ディレクトリ(略されている場合は./)にあること
    - ファイル名（例）：0_deg_ZOOM0293.wav
    - ファイル名の命名規則：角度_deg_ファイル名.wav
- トーンセットのデータがあること
    - ファイル名：toneset.txt
- ノイズフロアの録音データがあること
    - ファイル名：noise.wav

## バッチ処理の内容の例（bashの場合）
```bash
$ cd /Users/osaka/Desktop/241114｜指向性実験/実験１：指向性_3つのICR/DM750/data_cut
$ mkdir right left
# 音源を左右に分ける
$ ls *wav |xargs -I@ ~/GitHub/sound_command/separate_to_mono.py -i @ -ol left/@ -or right/@

# 右チャネルの処理
$ cd right
# ノイズフロアを求める
$ searach_Peak_from_toneset.py -t toneset_noise.txt -i noise.wav -fc  -lf 2500 -hf 9800 -fs  8192 -ov 50  -mx 45 -mn -20 -rs -pf 100
# ノイズフロアの修正が必要か？
$ read -p "ノイズフロアの修正が必要か？(y/n/q): " answer
if [ "$answer" = "y" ]; then
    $ searach_Peak_from_toneset.py -t toneset_noise.txt -i noise.wav -fc  -lf 2500 -hf 9800 -fs  8192 -ov 50  -mx 45 -mn -20 -rs -pf 100
elif [ "$answer" = "q" ]; then
    exit 0
fi
# 角度ごとのtonesetピークの強度とSNRを求める
$ ls *deg*wav | xargs -I@ searach_Peak_from_toneset.py -t toneset.txt -fc -rs -pf 100 -i @  -lf 2500 -hf 9800 -fs  8192 -ov 50 -mx 45 -mn -20 -ifc noise_fit_coeff.txt 
# ch毎に角度ごとのピーク強度とSNRに表形式でまとめる
$ ls *deg*.txt | xargs -I@ awk -F, '!/^#/{match(FILENAME, /^[0-9]+/);deg = substr(FILENAME, RSTART, RLENGTH); printf "%d,%s,%s,%s,%s\n",deg,$1,$2,$3,$4}' @ |sort -t, -k1,1n >| microphone_pattern.txt
# SNRのマイクパターン
$ plot_microphone_pattern.py -i microphone_pattern.txt -o plot_microphone_pattern_SNR.png --debug -t toneset.txt -mx 45 -mn 0 -c s
# Peakのマイクパターン
$ plot_microphone_pattern.py -i microphone_pattern.txt -o plot_microphone_pattern_Peak.png --debug -t toneset.txt -mx 50 -mn 0 -c p

# 同様に左チャネルでも行う
$ cd ../left
# ノイズフロアを求める
$ searach_Peak_from_toneset.py -t toneset_noise.txt -i noise.wav -fc  -lf 2500 -hf 9800 -fs  8192 -ov 50  -mx 45 -mn -20 -rs -pf 100
# ノイズフロアの修正が必要か？
$ read -p "ノイズフロアの修正が必要か？(y/n/q): " answer
if [ "$answer" = "y" ]; then
    $ searach_Peak_from_toneset.py -t toneset_noise.txt -i noise.wav -fc  -lf 2500 -hf 9800 -fs  8192 -ov 50  -mx 45 -mn -20 -rs -pf 100
elif [ "$answer" = "q" ]; then
    exit 0
fi
# 角度ごとのtonesetピークの強度とSNRを求める
$ ls *deg*wav | xargs -I@ searach_Peak_from_toneset.py -t toneset.txt -fc -rs -pf 100 -i @  -lf 2500 -hf 9800 -fs  8192 -ov 50 -mx 45 -mn -20 -ifc noise_fit_coeff.txt 
# ch毎に角度ごとのピーク強度とSNRに表形式でまとめる
$ ls *deg*.txt | xargs -I@ awk -F, '!/^#/{match(FILENAME, /^[0-9]+/);deg = substr(FILENAME, RSTART, RLENGTH); printf "%d,%s,%s,%s,%s\n",deg,$1,$2,$3,$4}' @ |sort -t, -k1,1n >| microphone_pattern.txt
# SNRのマイクパターン
$ plot_microphone_pattern.py -i microphone_pattern.txt -o plot_microphone_pattern_SNR.png --debug -t toneset.txt -mx 45 -mn 0 -c s
# Peakのマイクパターン
$ plot_microphone_pattern.py -i microphone_pattern.txt -o plot_microphone_pattern_Peak.png --debug -t toneset.txt -mx 50 -mn 0 -c p
```
