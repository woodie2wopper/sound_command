#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import os
import matplotlib.font_manager as fm

# コマンドライン引数の設定
parser = argparse.ArgumentParser(description='Show histogram from CSV data.')
parser.add_argument('-i', '--input', required=True, help='Input CSV file')
parser.add_argument('-o', '--output', help='Output image file')
parser.add_argument('-t', '--title', default='Stacked Histogram of Zeep Types', help='ヒストグラムのタイトル')
parser.add_argument('-mn', '--ymin', type=float, default=None, help='y軸の最小値')
parser.add_argument('-mx', '--ymax', type=float, default=None, help='y軸の最大値')

args = parser.parse_args()

# 日本語フォントを指定
font_path = '/Library/Fonts/Arial Unicode.ttf'
# 例: font_path = '/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
font_prop = fm.FontProperties(fname=font_path)
plt.rcParams['font.family'] = font_prop.get_name()

# CSVファイルの読み込み
data = pd.read_csv(args.input)

# ヒストグラムの作成
plt.figure(figsize=(10, 6))

# 積み上げ型のヒストグラムをプロッ���
data.set_index('Begin Clock Time').plot(kind='bar', stacked=True, alpha=0.7)

# y軸の範囲を設定
if args.ymin is not None or args.ymax is not None:
    plt.ylim(args.ymin, args.ymax)

# タイトルをコマンドライン引数から取得
plt.title(args.title)
plt.xlabel('Hour of Day')
plt.ylabel('Frequency')
plt.legend()
plt.grid(True)

# カスタムのX軸ラベルを設定
custom_ticks = [18, 19, 20, 21, 22, 23, 0, 1, 2, 3, 4, 5]
plt.xticks(range(len(custom_ticks)), custom_ticks)

# 出力ファイル名の設定
if args.output is None:
    input_filename = os.path.basename(args.input)
    output_filename = os.path.splitext(input_filename)[0] + ".png"
else:
    output_filename = args.output

# 出力ファイルに保存
plt.savefig(output_filename)
print(f"ヒストグラムを {output_filename} に保存しました。")
# plt.show()