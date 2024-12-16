#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='マイクパターンをプロットする')
    parser.add_argument('--input-file', '-i', type=str, help='ピーク強度とSN比の表のファイル')
    parser.add_argument('--output-file', '-o', type=str, help='出力ファイル名')
    parser.add_argument('--max', '-mx', type=float, default=100, help='プロットする最大値')
    parser.add_argument('--min', '-mn', type=float, default=0, help='プロットする最小値')
    parser.add_argument('--column', '-c', choices=['p', 's'], default='s', help='ピーク強度かSN比か')
    parser.add_argument('--high-freq', '-hf', type=float, default=22000, help='プロットする最大周波数')
    parser.add_argument('--low-freq', '-lf', type=float, default=0, help='プロットする最小周波数')
    parser.add_argument('--toneset', '-t', type=str, help='トーンセットの周波数のマイクパターンをプロットする')
    parser.add_argument('--serch-range', '-sr', type=int, default=50, help='ピークサーチ範囲（デフォルト：50）')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグ情報を出力する')
    parser.add_argument('--average', '-a', action='store_true', help='角度毎にデータを平均化してプロットする')
    return parser.parse_args()

def load_data(file_path, column, toneset_file=None, search_range=50):
    angles = []
    freqs = set()  # 周波数を一意にするためにセットを使用
    values_dict = {}  # 角度をキーにして値を保存する辞書
    column_index = 4 if column == 'p' else 2  # 'p'の場合は4列目、's'の場合は3列目を選択

    # トーンセットファイルから周波数を読み込む
    toneset_freqs = set()
    if toneset_file:
        with open(toneset_file, 'r') as file:
            for line in file:
                if line.startswith('#') or line.strip() == '':
                    continue
                toneset_freqs.add(float(line.strip()))

    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#') or line.strip() == '':
                continue
            parts = line.strip().split(',')
            angle = float(parts[0])
            freq = int(float(parts[1]))
            value = float(parts[column_index])

            # サーチ範囲内の周波数のみを考慮
            if toneset_file:
                # トーンセットの周波数にアライメントする
                matched_freq = None
                for t_freq in toneset_freqs:
                    if abs(freq - t_freq) <= search_range:
                        matched_freq = t_freq
                        break
                if matched_freq is None:
                    continue
                freq = matched_freq  # 周波数をトーンセットの値に置き換え
            if angle not in values_dict:
                values_dict[angle] = []
            values_dict[angle].append(value)
            freqs.add(freq)

    angles = np.array(list(values_dict.keys()))
    freqs = np.array(sorted(freqs))
    values = np.array([values_dict[angle] for angle in angles])
    # デバッグモードの場合、読み込んだデータの一覧を表示
    if args.debug:
        print("\n読み込んだデータの一覧:")
        print(f"角度: {angles}")
        print(f"周波数: {freqs}")
        print(f"値の形状: {values.shape}")
        print("各角度での値:")
        for i, angle in enumerate(angles):
            print(f"角度 {angle}度: {values[i]}")
    # デバッグモードの場合、周波数毎の各角度の値を表示
    if args.debug:
        print("\n周波数毎の各角度の値:")
        for i, freq in enumerate(freqs):
            print(f"\n周波数 {freq}Hz での値:")
            for j, angle in enumerate(angles):
                print(f"角度 {angle}度: {values[j][i]}")

    return angles, freqs, values

def plot_polar(angles, freqs, values):
    # 日本語フォントを設定
    font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'  # ヒラギノ角ゴシックのパス
    font_prop = font_manager.FontProperties(fname=font_path)
    
    # 平均化オプションが指定されている場合、データを平均化
    if args.average:
        values = np.mean(values, axis=1, keepdims=True)
        if args.output_file is None:
            args.output_file = 'plot_microphone_pattern_SNR_avrg.png' if args.column == 's' else 'plot_microphone_pattern_Peak_avrg.png'
        else:
            base, ext = os.path.splitext(args.output_file)
            args.output_file = f"{base}_avrg{ext}"

    # ここでoutput_fileがNoneでないことを確認
    if args.output_file is None:
        args.output_file = f'plot_microphone_pattern_SNR.png' if args.column == 's' else 'plot_microphone_pattern_Peak.png'  # デフォルトのファイル名を設定

    output_file = args.output_file
    min_value = args.min
    max_value = args.max
    low_freq = args.low_freq
    high_freq = args.high_freq

    plt.figure()
    ax = plt.subplot(111, polar=True)
    ax.set_ylim(min_value, max_value)
    ax.set_theta_direction(-1)
    ax.set_theta_zero_location('N')
    
    # 色のリストを用意 (虹色のカラーマップを使用)
    colors = plt.cm.rainbow(np.linspace(0, 1, len(freqs)))
    
    # デバッグ情報を出力
    if args.debug:
        print(f"周波数の数: {len(freqs)}, マイクパターンの数: {values.shape[1]}")
    
    for i, freq in enumerate(freqs):
        # 指定された周波数範囲内のみプロット
        if (low_freq is None or freq >= low_freq) and (high_freq is None or freq <= high_freq):
            if i < values.shape[1]:  # インデックスが範囲内か確認
                label = 'average' if args.average else f'{int(freq)} Hz'
                ax.plot(np.radians(angles), values[:, i], color=colors[i], label=label)
            else:
                print(f"Skipping index {i} as it is out of bounds for values with shape {values.shape}")
    
    ax.legend(prop=font_prop)  # 凡例にもフォントを適用
    # 入力ファイルからファイ���ボディを取得
    output_file_body = os.path.splitext(os.path.basename(args.output_file))[0]
    ax.set_title(f'マイクパターン {output_file_body}', fontproperties=font_prop)  # タイトルにフォントを適用
    plt.savefig(output_file)
    plt.close()

def main():
    global args  # ここでグローバル変数として宣言
    args = parse_arguments()  # argsに代入
    if args.input_file is None:
        print("入力ファイルが指定されていません。--input-fileオプションを使用してファイルを指定してください。")
        parser = argparse.ArgumentParser(description='マイクパターンをプロットする')
        parser.print_help()  # ヘルプメッセージを表示
        return  # プログラムを終了
    angles, freqs, values = load_data(args.input_file, args.column, args.toneset, args.serch_range)
    plot_polar(angles, freqs, values)

if __name__ == "__main__":
    main() 