#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.io import wavfile
from scipy.fft import fft
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='トーンセットのピーク強度とSN比を求める')
    parser.add_argument('--cut', '-c', type=int, help='先頭と最後を指定数値(秒)削除する')
    parser.add_argument('--no-img', '-n', action='store_true', help='スペクトログラムの出力なし')
    parser.add_argument('--toneset', '-t', type=str, help='トーンセットの入っているテキストファイル')
    parser.add_argument('--serch-range', '-sr', type=int, default=50, help='サーチ範囲（デフォルト：50）')
    parser.add_argument('--noise-floor', '-nf', type=str, help='トーンセット周波数毎のノイズフロアファイル。指定がない場合、指定された周波数範囲の平均を使用。')
    parser.add_argument('--input-audio', '-i', type=str, help='入力音源')
    parser.add_argument('--max', '-mx', type=float, help='ピーク強度の最大値（デフォルト：自動）')
    parser.add_argument('--min', '-mn', type=float, help='ピーク強度の最小値（デフォルト：自動）')
    parser.add_argument('--low-freq', '-lf', type=float, default=0, help='最低周波数（デフォルト：0）')
    parser.add_argument('--high-freq', '-hf', type=float, default=12000, help='最高周波数（デフォルト：12000）')
    parser.add_argument('--fft-size', '-fs', type=int, default=2048, help='FFTサイズ（デフォルト：2048）')
    parser.add_argument('--moving-average', '-ma', type=int, default=0, help='ノイズフロア推定のための移動平均ウィンドウサイズ（デフォルト：0）')
    parser.add_argument('--fit-curve', '-fc', action='store_true', help='ノイズフロア推定のためのフィッティング曲線を使用する')
    parser.add_argument('--remove-signals', '-rs', action='store_true', help='ノイズフロア推定のための信号のピークをフィッティング曲線で除去する')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグモード')

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

def process_audio(args):
    sample_rate, data = wavfile.read(args.input_audio)
    if args.cut:
        cut_samples = args.cut * sample_rate
        data = data[cut_samples:-cut_samples]
    return sample_rate, data

def calculate_fft(data, sample_rate, args):
    num_segments = len(data) // args.fft_size
    spectrum_sum = np.zeros(args.fft_size // 2)
    
    if args.debug:
        print(f"Number of segments: {num_segments}")
        print(f"FFT size: {args.fft_size}")
    for i in range(num_segments):
        segment = data[i * args.fft_size:(i + 1) * args.fft_size]
        spectrum = np.abs(fft(segment, n=args.fft_size))
        spectrum_sum += spectrum[:args.fft_size // 2]
    
    # 平均化
    averaged_spectrum = spectrum_sum / num_segments
    
    # FFTの周波数軸を計算
    freqs = np.fft.fftfreq(args.fft_size, 1/sample_rate)
    
    return freqs[:args.fft_size // 2], averaged_spectrum

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
        results.append((closest_freq, 20 * np.log10(intensity), snr))
    return results

def set_japanese_font():
    # 日本語フォントを指定
    font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'  # ヒラギノ角ゴシックのパス
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()

def plot_spectrum(freqs, spectrum, peaks, noise_floor_spectrum, noise_floor, output_file, args):
    set_japanese_font()  # 日本語フォントを設定
    plt.figure()
    plt.plot(freqs, 20 * np.log10(spectrum), 'gray', linestyle='-')
    plt.plot(freqs, 20 * np.log10(noise_floor_spectrum), 'green', linestyle='-')
    for freq, intensity in peaks:
        plt.plot(freq, 20 * np.log10(intensity), 'ro')
        plt.plot(list(noise_floor.keys()), [20 * np.log10(v) for v in noise_floor.values()], 'orange', linestyle='-')
    # フィッティング曲線の表示
    if args.fit_curve:
        # フィッティング曲線の計算
        coefficients = fit_quadratic_least_squares(freqs, noise_floor_spectrum, args)
        fitted_curve = np.polyval(coefficients, freqs)
        # dBに変換して表示
        plt.plot(freqs, 20 * np.log10(fitted_curve), 'b--', label='フィッティング曲線')
        plt.legend()
    
    plt.ylim(args.min, args.max)
    plt.xlim(args.low_freq, args.high_freq)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Intensity (dB)')
    plt.title(os.path.splitext(os.path.basename(output_file))[0])
    plt.savefig(output_file)

def apply_moving_average(spectrum, window_size):
    if window_size <= 0:
        return spectrum
    return np.convolve(spectrum, np.ones(window_size)/window_size, mode='same')

def fit_quadratic_least_squares(freqs, spectrum, args):
    """
    スペクトルデータに対して2次関数を最小二乗法でフィッティングします。

    Parameters:
    freqs (numpy.ndarray): 周波数の配列
    spectrum (numpy.ndarray): スペクトル強度の配列

    Returns:
    numpy.ndarray: フィッティングされた2次関数の係数 [a, b, c] (ax^2 + bx + c)
    """
    # 2次関数でフィッティング
    coefficients = np.polyfit(freqs, spectrum, 2)
    if args.debug:
        print(f"Fitted coefficients: {coefficients}")
    return coefficients

def remove_signal_peaks(spectrum, peaks, freqs, search_range):
    for peak_freq, _ in peaks:
        mask = (freqs >= peak_freq - search_range) & (freqs <= peak_freq + search_range)
        spectrum[mask] = np.interp(freqs[mask], [freqs[mask][0], freqs[mask][-1]], [spectrum[mask][0], spectrum[mask][-1]])
    return spectrum

def main():
    args = parse_arguments()
    
    # Check if input audio is provided
    if not args.input_audio:
        print("オーディオファイルが指定されていません。")
        parser = argparse.ArgumentParser(description='トーンセットのピーク強度とSN比を求める')
        parser.print_help()
        return
    
    toneset = load_toneset(args.toneset) if args.toneset else [100, 800, 1000, 3400, 4800, 5800, 6400, 7800, 9000, 9400, 9500]

    # トーンセットを出力する
    if args.debug:
        print(f"Toneset: {toneset}")

    sample_rate, data = process_audio(args)
    freqs, spectrum = calculate_fft(data, sample_rate, args)
    
    peaks = find_peaks(freqs, spectrum, toneset, args.serch_range)
    # フィッティングによるノイズフロア推定
    noise_floor_spectrum = None  # デフォルト値を設定
    # 信号のピークを除去するオプションが指定された場合
    if args.remove_signals:
        spectrum_copy = spectrum.copy()
        noise_floor_spectrum = remove_signal_peaks(spectrum_copy, peaks, freqs, args.serch_range)
    
    # 移動平均によるノイズフロア推定
    if args.moving_average > 0:
        noise_floor_spectrum = apply_moving_average(noise_floor_spectrum, args.moving_average)
    
    # Load noise floor from file if provided, otherwise calculate it
    if args.noise_floor:
        noise_floor = load_noise_floor(args.noise_floor)
    else:
        # noise_floorを辞書として初期化
        noise_floor = {}
        for freq in freqs:
            noise_floor[int(freq)] = noise_floor_spectrum[freq]
    
    results = calculate_snr(peaks, noise_floor, args.serch_range)
    
    # Write results to a file with header
    output_file = os.path.splitext(args.input_audio)[0] + ".txt"
    with open(output_file, 'w') as f:
        f.write("# Frequency (Hz),Intensity (dB),Signal-to-Noise Ratio (dB)\n")  # Add header
        for freq, intensity, snr in results:
            f.write(f"{freq},{intensity},{snr}\n")
    
    if not args.no_img:
        output_file = os.path.splitext(args.input_audio)[0] + ".png"
        if noise_floor_spectrum is not None:  # noise_floor_spectrumが定義されている場合のみプロット
            plot_spectrum(freqs, spectrum, peaks, noise_floor_spectrum, noise_floor, output_file, args)

if __name__ == "__main__":
    main()
