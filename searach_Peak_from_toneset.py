#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from scipy.io import wavfile
from scipy.fft import fft
import os

# グローバル変数としてargsを定義
args = None
FIT_CURVE_COEFF_FILENAME = "_fit_coeff.txt"

def parse_arguments():
    parser = argparse.ArgumentParser(description='トーンセットのピーク強度とSN比を求める',
                                   epilog='使用例: serach_Peak_from_toneset.py -t toneset -i 45_deg_ZOOM0293_cut.WAV -sp -fc -rs -pf 100 -lf 3000 -hf 18000 -d -fs 8196 -ov 50')
    parser.add_argument('--no-img', '-n', action='store_true', help='スペクトログラムの出力なし')
    parser.add_argument('--toneset', '-t', type=str, help='トーンセットの入っているテキストファイル')
    parser.add_argument('--serch-range', '-sr', type=int, default=50, help='ピークサーチ範囲（デフォルト：50）')
    parser.add_argument('--noise-floor', '-nf', type=str, help='トーンセットのノイズフロアファイル指定値。')
    parser.add_argument('--input-audio', '-i', type=str, help='入力音源')
    parser.add_argument('--max', '-mx', type=float, help='ピーク強度の最大値（デフォルト：自動）')
    parser.add_argument('--min', '-mn', type=float, help='ピーク強度の最小値（デフォルト：自動）')
    parser.add_argument('--low-freq', '-lf', type=float, default=0, help='最低周波数（デフォルト：0）')
    parser.add_argument('--high-freq', '-hf', type=float, default=20000, help='最高周波数（デフォルト：20000）')
    parser.add_argument('--fft-size', '-fs', type=int, default=2048, help='FFTサイズ（デフォルト：2048）')
    parser.add_argument('--overlap', '-ov', type=int, default=0, help='オーバーラップ率（デフォルト：0）')
    parser.add_argument('--moving-average', '-ma', type=int, default=0, help='ノイズフロア推定のための移動平均ウィンドウサイズ（デフォルト：0）')
    parser.add_argument('--fit-curve', '-fc', action='store_true', help='ノイズフロア推定のためのフィッティング曲線を使用する')
    parser.add_argument('--input-fit-curve-coeff', '-ifc', type=str, help='ノイズフロア推定のためのフィッティング曲線の２次係数ファイル')
    parser.add_argument('--remove-signals', '-rs', action='store_true', help='ノイズフロア推定のための信号のピークをフィッティング曲線で除去する')
    parser.add_argument('--peak-floor', '-pf', type=int, default=50, help='ピーク削除のためのノイズフロアの範囲（デフォルト：50）、---remove-signalsと一緒に指定する。')
    parser.add_argument('--spectrogram', '-sp', action='store_true', help='スペクトログラムの出力')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグモード')
    parser.add_argument('--stereo', '-st', action='store_true', help='ステレオファイルを自動的に左右に分割して処理')

    return parser.parse_args()

def load_toneset(file_path):
    with open(file_path, 'r') as file:
        return [int(line.strip()) for line in file if line.strip()]

def load_noise_floor(file_path):
    noise_floor = {}
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#'):
                continue  # コメント行をスキップ
            try:
                freq, linear_level, db_level = line.strip().split(',')
                noise_floor[int(float(freq))] = float(db_level)
                print(f"Loaded noise floor: Frequency = {freq}, Linear Level = {linear_level}, dB Level = {db_level}")
            except ValueError as e:
                print(f"Error processing line: {line.strip()} - {e}")
    return noise_floor

def process_audio():
    sample_rate, data = wavfile.read(args.input_audio)
    if data.ndim == 2:  # ステレオの場合
        left_channel = data[:, 0]
        right_channel = data[:, 1]
        return sample_rate, left_channel, right_channel
    return sample_rate, data, None

def calculate_fft(data, sample_rate):
    step_size = int(args.fft_size * (1 - args.overlap / 100))
    num_segments = (len(data) - args.fft_size) // step_size + 1
    spectrum_sum = np.zeros(args.fft_size // 2)
    
    if args.debug:
        print(f"Number of segments: {num_segments}")
        print(f"FFT size: {args.fft_size}")
        print(f"Step size: {step_size}")
    for i in range(num_segments):
        start_index = i * step_size
        segment = data[start_index:start_index + args.fft_size]
        spectrum = np.abs(fft(segment, n=args.fft_size)) ** 2  # パワースペクトルに変換
        spectrum_sum += spectrum[:args.fft_size // 2]
    
    # 平均化
    averaged_spectrum = spectrum_sum / num_segments
    
    # パワースペクトル密度に変換
    psd = averaged_spectrum / (sample_rate * args.fft_size)
    
    # dBに変換
    spectrum_db = 10 * np.log10(psd + np.finfo(float).eps)  # ゼロ除算を防ぐために微小値を加算
    
    # FFTの周波数軸を計算
    freqs = np.fft.fftfreq(args.fft_size, 1/sample_rate)
    
    return freqs[:args.fft_size // 2], spectrum_db

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
            snr = intensity - noise_floor[freq]
        else:
            # search_range内の最も近い周波数を探す
            closest_freq = min(noise_floor.keys(), key=lambda x: abs(x - freq) if abs(x - freq) <= search_range else float('inf'))
            if abs(closest_freq - freq) <= search_range:
                snr = intensity - noise_floor[closest_freq]
                if args.debug:
                    print(f"最も近い周波数 {closest_freq} を {freq} に使用しています")
            else:
                snr = float('nan')  # 例としてNaNを使用
                print(f"Warning: No suitable frequency found for {freq} within search range.")
        
        # ifc オプションが指定されている場合の処理
        if args.input_fit_curve_coeff:
            coefficients = load_fit_curve_coeff(args.input_fit_curve_coeff)
            fitted_noise_floor = np.polyval(coefficients, freq)
            snr = intensity - fitted_noise_floor
            if args.debug:
                print(f"Fitted noise floor for {freq}: {fitted_noise_floor}, SNR: {snr}")

        results.append((closest_freq, intensity, snr, noise_floor.get(closest_freq, float('nan'))))
    return results

def set_japanese_font():
    # 日本語フォントを指定
    font_path = '/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'  # ヒラギノ角ゴシックのパス
    font_prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = font_prop.get_name()

def moving_average_noise_floor(spectrum, window_size):
    noise_floor_spectrum = apply_moving_average(spectrum, window_size)
    return noise_floor_spectrum

def plot_spectrum(freqs, spectrum, peaks, noise_floor_spectrum, noise_floor, output_file):
    set_japanese_font()  # 日本語フォントを設定
    freqs_org=freqs.copy()
    freq_mask = (freqs >= args.low_freq) & (freqs <= args.high_freq)
    freqs = freqs[freq_mask]
    spectrum_org=spectrum.copy()
    spectrum = spectrum[freq_mask]
    plt.figure()
    plt.plot(freqs, spectrum, 'black', linestyle='-', label='信号スペクトル')
    # 移動平均によるノイズフロア推定
    if args.moving_average > 0:
        noise_floor_spectrum = moving_average_noise_floor(spectrum_org, args.moving_average)
        noise_floor_spectrum = noise_floor_spectrum[freq_mask]
        plt.plot(freqs, noise_floor_spectrum, 'orange', linestyle='-', label='ノイズフロア(移動平均)')
    # 信号のピークを除去するオプョンが指定された場合
    if args.remove_signals:
        noise_floor_spectrum = remove_signal_peaks(noise_floor_spectrum, peaks, freqs, args.peak_floor)
        plt.plot(freqs, noise_floor_spectrum, 'green', linestyle='--', label='ノイズフロア(ピーク削除)')
    # ノイズフロアの表示
    if args.noise_floor:
        plt.plot(list(noise_floor.keys()), [v for v in noise_floor.values()], 'orange', linestyle='--', label='ノイズフロア(指定値)')
    # フィッティング曲線の表示
    if args.fit_curve:
        # フィッティング曲線の計算
        if args.input_fit_curve_coeff:
            coefficients = load_fit_curve_coeff(args.input_fit_curve_coeff)
        else:
            coefficients = fit_quadratic_least_squares(freqs, noise_floor_spectrum)
            # 係数をファイル出力
            coeff_file = os.path.splitext(output_file)[0] + FIT_CURVE_COEFF_FILENAME
            np.savetxt(coeff_file, coefficients, fmt='%.6e')
            if args.debug:
                print(f"フィッティング係数をファイル {coeff_file} に保存しました")
        fitted_curve = np.polyval(coefficients, freqs)
        # dBに変換して表示
        plt.plot(freqs, fitted_curve, 'blue', linestyle='--', label='フィッティング曲線')
    
    # ピークポイントの表示
    for freq, intensity in peaks:
        plt.plot(freq, intensity, 'ro', markersize=3)  # 'ro'は赤色の点を表します
    # ピークポイントの凡例を追加
    plt.plot([], [], 'ro', label='ピーク')
    
    plt.ylim(args.min, args.max)
    plt.xlim(args.low_freq, args.high_freq)
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Intensity [dB]')
    plt.title(os.path.splitext(os.path.basename(output_file))[0])
    plt.legend()  # 全ての凡例を表示
    plt.savefig(output_file)

def apply_moving_average(spectrum, window_size):
    if window_size <= 0:
        return spectrum
    return np.convolve(spectrum, np.ones(window_size)/window_size, mode='same')

def fit_quadratic_least_squares(freqs, spectrum):
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

def plot_spectrogram(data, sample_rate, output_file):
    plt.figure()
    plt.specgram(data, NFFT=args.fft_size, Fs=sample_rate, cmap='viridis')
    plt.xlabel('Time [s]')
    plt.ylabel('Frequency [Hz]')
    plt.title(os.path.splitext(os.path.basename(output_file))[0])
    plt.colorbar(label='Intensity [dB]')
    plt.ylim(args.low_freq, args.high_freq)  # 周波数範囲をオプション指定に合わせる
    plt.savefig(output_file)
    plt.close()

def load_fit_curve_coeff(file_path):
    with open(file_path, 'r') as file:
        return [float(coeff.strip()) for coeff in file if coeff.strip()]

def main():
    global args
    args = parse_arguments()
    
    if not args.input_audio:
        print("オーディオファイルが指定されていません。")
        parser = argparse.ArgumentParser(description='トーンセットのピーク強度とSN比を求める')
        parser.print_help()
        return
    
    toneset = load_toneset(args.toneset) if args.toneset else [100, 800, 1000, 3400, 4800, 5800, 6400, 7800, 9000, 9400, 9500]

    if args.debug:
        print(f"Toneset: {toneset}")

    sample_rate, left_data, right_data = process_audio()

    # モノラルかステレオかを判定
    is_stereo = right_data is not None

    for channel, data in zip(['_left', '_right'], [left_data, right_data]):
        if data is None:
            continue

        freqs, spectrum = calculate_fft(data, sample_rate)
        freqs_org = freqs.copy()
        freq_mask = (freqs >= args.low_freq) & (freqs <= args.high_freq)
        freqs = freqs[freq_mask]
        spectrum_org = spectrum.copy()
        spectrum = spectrum[freq_mask]
        peaks = find_peaks(freqs, spectrum, toneset, args.serch_range)
        
        if args.moving_average > 0:
            noise_floor_spectrum = moving_average_noise_floor(spectrum_org, args.moving_average)
            noise_floor_spectrum = noise_floor_spectrum[freq_mask]
        else:
            noise_floor_spectrum = spectrum.copy()
        if args.remove_signals:
            noise_floor_spectrum = remove_signal_peaks(noise_floor_spectrum, peaks, freqs, args.peak_floor)
        
        if args.noise_floor:
            noise_floor = load_noise_floor(args.noise_floor)
        else:
            noise_floor = {int(freq): noise_floor_spectrum[i] for i, freq in enumerate(freqs)}
        
        results = calculate_snr(peaks, noise_floor, args.serch_range)
        
        # モノラルの場合、出力ファイル名にチャネル名を追加しない
        output_file_suffix = channel if is_stereo else ""
        output_file = os.path.splitext(args.input_audio)[0] + output_file_suffix + ".txt"
        with open(output_file, 'w') as f:
            f.write("# Frequency [Hz],Intensity [dB],Noise_floor [dB],SNR [dB]\n")
            for freq, intensity, snr, noise_floor_value in results:
                f.write(f"{freq},{intensity},{noise_floor_value},{snr}\n")
        
        if not args.no_img:
            output_file = os.path.splitext(args.input_audio)[0] + output_file_suffix + ".png"
            plot_spectrum(freqs_org, spectrum_org, peaks, noise_floor_spectrum, noise_floor, output_file)
            if args.spectrogram:
                spectrogram_output_file = os.path.splitext(args.input_audio)[0] + output_file_suffix + "_spectrogram.png"
                plot_spectrogram(data, sample_rate, spectrogram_output_file)

if __name__ == "__main__":
    main()
