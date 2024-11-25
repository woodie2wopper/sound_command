#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.fft import fft
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='背景録音音源からトーンセットに応じたノイズフロアを生成する')
    parser.add_argument('--toneset', '-t', type=str, help='トーンセットの入っているテキストファイル')
    parser.add_argument('--no-img', '-n', action='store_true', help='スペクトログラムの出力なし')
    parser.add_argument('--serch-range', '-r', type=int, default=50, help='トーンセットの各周波数から±数値の周波数範囲でサーチする。デフォルトで５０Hz')
    parser.add_argument('--moving-average', '-ma', type=int, default=0, help='周波数軸の移動平均（デフォルトで０ポイント）')
    parser.add_argument('--input-audio', '-ia', type=str, help='無音の音源（1秒以上）')
    return parser.parse_args()

def load_toneset(file_path):
    with open(file_path, 'r') as file:
        return [int(line.strip()) for line in file]

def process_audio(file_path):
    sample_rate, data = wavfile.read(file_path)
    return sample_rate, data

def calculate_fft(data, sample_rate):
    fft_size = 2048
    spectrum = np.abs(fft(data, n=fft_size))
    freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
    return freqs[:fft_size // 2], spectrum[:fft_size // 2]

def calculate_noise_floor(freqs, spectrum, toneset, search_range):
    noise_floor = []
    for tone in toneset:
        mask = (freqs >= tone - search_range) & (freqs <= tone + search_range)
        avg_intensity = np.mean(spectrum[mask])
        noise_floor.append((tone, avg_intensity, 20 * np.log10(avg_intensity)))
    return noise_floor

def plot_spectrum(freqs, original_spectrum, smoothed_spectrum, toneset, output_file, moving_average):
    plt.figure()
    plt.plot(freqs, 20 * np.log10(original_spectrum), label='Original Spectrum', alpha=0.5)
    plt.plot(freqs, 20 * np.log10(smoothed_spectrum), label='Smoothed Spectrum', linestyle='--')
    
    for tone in toneset:
        plt.axvline(x=tone, color='r', linestyle='--', linewidth=0.5)
    
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Intensity (dB)')
    plt.title(f"{os.path.splitext(os.path.basename(output_file))[0]}\nMoving Average: {moving_average} points")
    plt.legend()
    plt.savefig(output_file)

def apply_moving_average(spectrum, window_size):
    if window_size <= 0:
        return spectrum
    return np.convolve(spectrum, np.ones(window_size)/window_size, mode='same')

def main():
    args = parse_arguments()
    
    # Check if input audio is provided
    if not args.input_audio:
        print("オーディオファイルが指定されていません。")
        parser = argparse.ArgumentParser(description='背景録音音源からトーンセットに応じたノイズフロアを生成する')
        parser.print_help()
        return
    
    toneset = load_toneset(args.toneset) if args.toneset else [100, 800, 1000, 3400, 4800, 5800, 6400, 7800, 9000, 9400, 9500]
    sample_rate, data = process_audio(args.input_audio)
    freqs, spectrum = calculate_fft(data, sample_rate)
    search_range = args.serch_range if args.serch_range else 50
    
    original_spectrum = spectrum.copy()  # Keep a copy of the original spectrum
    
    # Apply moving average if specified
    if args.moving_average > 0:
        spectrum = apply_moving_average(spectrum, args.moving_average)
    
    noise_floor = calculate_noise_floor(freqs, spectrum, toneset, search_range)
    
    # Write noise floor to a file
    output_file = os.path.splitext(args.input_audio)[0] + ".txt"
    with open(output_file, 'w') as f:
        f.write("# Frequency (Hz),Linear Level,dB Level\n")  # ヘッダー行を追加
        f.write(f"# Moving Average: {args.moving_average} points\n")  # 移動平均のコメント
        for tone, linear_level, db_level in noise_floor:
            f.write(f"{tone}, {linear_level}, {db_level}\n")
    
    if not args.no_img:
        plot_spectrum(freqs, original_spectrum, spectrum, toneset, os.path.splitext(args.input_audio)[0] + ".png", args.moving_average)

if __name__ == "__main__":
    main() 