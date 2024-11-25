#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy.fft import fft
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='トーンセットのピーク強度とSN比を求める')
    parser.add_argument('--cut', '-c', type=int, help='先頭と最後を指定数値(秒)削除する')
    parser.add_argument('--no-img', '-n', action='store_true', help='スペクトログラムの出力なし')
    parser.add_argument('--toneset', '-t', type=str, help='トーンセットの入っているテキストファイル')
    parser.add_argument('--serch-range', '-sr', type=int, default=50, help='サーチ範囲')
    parser.add_argument('--noise-floor', '-nf', type=str, help='トーンセット周波数毎のノイズフロアファイル。指定がない場合、指定された周波数範囲の平均を使用します。')
    parser.add_argument('--input-audio', '-ia', type=str, help='入力音源')
    return parser.parse_args()

def load_toneset(file_path):
    with open(file_path, 'r') as file:
        return [int(line.strip()) for line in file]

def load_noise_floor(file_path):
    noise_floor = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#'):
                continue  # コメント行をスキップ
            try:
                freq, linear_level, db_level = line.strip().split(',')
                noise_floor[int(float(freq))] = float(linear_level)
                print(f"Loaded noise floor: Frequency = {freq}, Linear Level = {linear_level}, dB Level = {db_level}")
            except ValueError as e:
                print(f"Error processing line: {line.strip()} - {e}")
    return noise_floor

def process_audio(file_path, cut_seconds=None):
    sample_rate, data = wavfile.read(file_path)
    if cut_seconds:
        cut_samples = cut_seconds * sample_rate
        data = data[cut_samples:-cut_samples]
    return sample_rate, data

def calculate_fft(data, sample_rate):
    fft_size = 2048
    spectrum = np.abs(fft(data, n=fft_size))
    freqs = np.fft.fftfreq(fft_size, 1/sample_rate)
    return freqs[:fft_size // 2], spectrum[:fft_size // 2]

def find_peaks(freqs, spectrum, toneset, search_range):
    peaks = []
    for tone in toneset:
        mask = (freqs >= tone - search_range) & (freqs <= tone + search_range)
        if np.any(mask):
            peak_freq = freqs[mask][np.argmax(spectrum[mask])]
            peak_intensity = np.max(spectrum[mask])
            peaks.append((peak_freq, peak_intensity))
        else:
            print(f"Warning: No peaks found for tone {tone} within search range.")
    return peaks

def calculate_snr(peaks, noise_floor, search_range):
    results = []
    for freq, intensity in peaks:
        # noise_floorが空でないか確認
        if not noise_floor:
            print("Error: Noise floor data is empty.")
            return results
        
        # 周波数がnoise_floorに存在するか確認
        if freq in noise_floor:
            snr = 10 * np.log10(intensity / noise_floor[freq])
        else:
            # search_range内の最も近い周波数を探す
            closest_freq = min(noise_floor.keys(), key=lambda x: abs(x - freq) if abs(x - freq) <= search_range else float('inf'))
            if abs(closest_freq - freq) <= search_range:
                snr = 10 * np.log10(intensity / noise_floor[closest_freq])
                print(f"Using closest frequency {closest_freq} for {freq}")
            else:
                snr = float('nan')  # 例としてNaNを使用
                print(f"Warning: No suitable frequency found for {freq} within search range.")
        results.append((freq, 20 * np.log10(intensity), snr))
    return results

def plot_spectrum(freqs, spectrum, peaks, noise_floor, output_file):
    plt.figure()
    plt.plot(freqs, 20 * np.log10(spectrum))
    for freq, intensity in peaks:
        plt.plot(freq, 20 * np.log10(intensity), 'ro')
        plt.plot(list(noise_floor.keys()), [20 * np.log10(v) for v in noise_floor.values()], 'orange', linestyle='-')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Intensity (dB)')
    plt.title(os.path.splitext(os.path.basename(output_file))[0])
    plt.savefig(output_file)

def main():
    args = parse_arguments()
    
    # Check if input audio is provided
    if not args.input_audio:
        print("オーディオファイルが指定されていません。")
        parser = argparse.ArgumentParser(description='トーンセットのピーク強度とSN比を求める')
        parser.print_help()
        return
    
    toneset = load_toneset(args.toneset) if args.toneset else [100, 800, 1000, 3400, 4800, 5800, 6400, 7800, 9000, 9400, 9500]
    sample_rate, data = process_audio(args.input_audio, args.cut)
    freqs, spectrum = calculate_fft(data, sample_rate)
    peaks = find_peaks(freqs, spectrum, toneset, args.serch_range)
    
    # Load noise floor from file if provided, otherwise calculate it
    if args.noise_floor:
        noise_floor = load_noise_floor(args.noise_floor)
    else:
        noise_floor = np.mean(spectrum[(freqs >= args.low_freq) & (freqs <= args.high_freq)])
    
    results = calculate_snr(peaks, noise_floor, args.serch_range)
    
    # Write results to a file with header
    output_file = os.path.splitext(args.input_audio)[0] + ".txt"
    with open(output_file, 'w') as f:
        f.write("# Frequency (Hz),Intensity (dB),Signal-to-Noise Ratio (dB)\n")  # Add header
        for freq, intensity, snr in results:
            f.write(f"{freq},{intensity},{snr}\n")
    
    if not args.no_img:
        output_file = os.path.splitext(args.input_audio)[0] + ".png"
        plot_spectrum(freqs, spectrum, peaks, noise_floor, output_file)

if __name__ == "__main__":
    main()
