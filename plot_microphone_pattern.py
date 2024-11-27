#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

def parse_arguments():
    parser = argparse.ArgumentParser(description='マイクパターンをプロットする')
    parser.add_argument('--input-file', '-i', type=str, help='ピーク強度とSN比の表のファイル')
    parser.add_argument('--output-file', '-o', type=str, default='plot_microphone_pattern.png', help='出力ファイル名')
    parser.add_argument('--max', '-mx', type=float, help='プロットする最大値')
    parser.add_argument('--min', '-mn', type=float, default=0, help='プロットする最小値')
    parser.add_argument('--column', '-c', choices=['p', 's'], default='p', help='ピーク強度かSN比か')
    parser.add_argument('--max-freq', '-mxf', type=float, help='プロットする最大周波数')
    parser.add_argument('--min-freq', '-mnf', type=float, help='プロットする最小周波数')
    return parser.parse_args()

def load_data(file_path, column):
    angles = []
    freqs = set()  # 周波数を一意にするためにセットを使用
    values_dict = {}  # 角度をキーにして値を保存する辞書
    column_index = 3 if column == 's' else 2  # 'p'の場合は4列目、's'の場合は3列目を選択

    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#') or line.strip() == '':
                continue
            parts = line.strip().split(',')
            angle = float(parts[0])
            freq = float(parts[1])
            value = float(parts[column_index])

            if angle not in values_dict:
                values_dict[angle] = []
            values_dict[angle].append(value)
            freqs.add(freq)

    angles = np.array(list(values_dict.keys()))
    freqs = np.array(sorted(freqs))
    values = np.array([values_dict[angle] for angle in angles])

    return angles, freqs, values

def plot_polar(angles, freqs, values, output_file, min_value, max_value, min_freq, max_freq):
    # 日本語フォントを設定
    font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'  # ヒラギノ角ゴシックのパス
    font_prop = font_manager.FontProperties(fname=font_path)
    
    plt.figure()
    ax = plt.subplot(111, polar=True)
    ax.set_ylim(min_value, max_value)
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location('N')
    
    # 色のリストを用意
    colors = plt.cm.viridis(np.linspace(0, 1, len(freqs)))
    
    for i, freq in enumerate(freqs):
        # 指定された周波数範囲内のみプロット
        if (min_freq is None or freq >= min_freq) and (max_freq is None or freq <= max_freq):
            ax.plot(np.radians(angles), values[:, i], color=colors[i], label=f'{freq} Hz')
    
    ax.legend(prop=font_prop)  # 凡例にもフォントを適用
    ax.set_title('マイクパターン', fontproperties=font_prop)  # タイトルにフォントを適用
    plt.savefig(output_file)
    plt.show()

def main():
    args = parse_arguments()
    if args.input_file is None:
        print("入力ファイルが指定されていません。--input-fileオプションを使用してファイルを指定してください。")
        parser = argparse.ArgumentParser(description='マイクパターンをプロットする')
        parser.print_help()  # ヘルプメッセージを表示
        return  # プログラムを終了
    angles, freqs, values = load_data(args.input_file, args.column)
    max_value = args.max if args.max is not None else np.max(values)
    plot_polar(angles, freqs, values, args.output_file, args.min, max_value, args.min_freq, args.max_freq)

if __name__ == "__main__":
    main() 