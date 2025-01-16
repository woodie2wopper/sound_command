#!/usr/bin/env python3

__version__ = 'v0.0.2'
__last_updated__ = '2025-01-16 18:53:40'

import argparse
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import scipy.signal
import os

# グローバル変数
args = None

def parse_arguments():
    parser = argparse.ArgumentParser(description="Find bird calls in an audio file")
    parser.add_argument("-i", "--input_file", required=True, help="Path to input audio file")
    parser.add_argument("-o", "--output_file", help="Path to output text file")
    parser.add_argument("-th", "--threshold", type=float, default=0.1, help="Detection threshold")
    parser.add_argument("-mf", "--method", choices=["freq", "time", "both"], default="both", help="Detection method")
    parser.add_argument("-D", "--Duration", type=float, default=0.1, help="Detection duration limit(sec)")
    parser.add_argument("-lf", "--low_freq", type=int, default=2000, help="Lower frequency limit (Hz)")
    parser.add_argument("-hf", "--high_freq", type=int, default=10000, help="Upper frequency limit (Hz)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # 出力ファイル名のデフォルト設定
    if args.output_file is None:
        input_base = os.path.splitext(args.input_file)[0]
        args.output_file = f"{input_base}_calls.txt"
    
    return args

def process_audio():
    """音声データの読み込みと前処理"""
    y, sr = librosa.load(args.input_file, sr=None)
    base_name = os.path.splitext(os.path.basename(args.input_file))[0]
    output_spectrogram = f"{base_name}_spectrogram.png"
    return y, sr, output_spectrogram

def detect_calls():
    """鳴き声の検出処理"""
    y, sr, output_spectrogram = process_audio()
    
    # 時間領域での検出
    if args.method in ["time", "both"]:
        time_calls = detect_calls_time(y, sr, args.threshold, args.Duration)
    else:
        time_calls = []
    
    # 周波数領域での検出
    if args.method in ["freq", "both"]:
        freq_calls = detect_calls_freq(y, sr, args.threshold, args.Duration)
    else:
        freq_calls = []
    
    # 結果の統合とソート
    calls = time_calls + freq_calls
    calls.sort(key=lambda x: x[0])
    
    return calls, y, sr, output_spectrogram

def save_results(calls, y, sr, output_spectrogram):
    """結果の保存処理"""
    # CSVファイルに結果を保存
    with open(args.output_file, "w") as f:
        f.write("No.,time(s),method,duration(s),call_value\n")
        for i, (t, method, duration, value) in enumerate(calls):
            f.write(f"{i+1},{t:.2f},{method},{duration:.2f},{value:.2f}\n")
    
    # 検出時刻の前後区間を指定
    time_ranges = []
    for i, (t, _, duration, _) in enumerate(calls):
        start_time = max(0, t - duration)
        end_time = t + duration
        time_ranges.append((start_time, end_time, i+1))
    
    # スペクトログラムを保存
    save_spectrogram(y, sr, output_spectrogram, time_ranges)
    
    if args.debug:
        print(f"Detected {len(calls)} calls. Results saved in {args.output_file}")
        print(f"Spectrograms saved as {os.path.splitext(output_spectrogram)[0]}_no*.png")

def main():
    global args
    args = parse_arguments()
    
    # 鳴き声の検出
    calls, y, sr, output_spectrogram = detect_calls()
    
    # 結果の保存
    save_results(calls, y, sr, output_spectrogram)

def detect_calls_time(y, sr, threshold, duration):
    # frame_length = 2048 (46.4ms @ 44.1kHz)
    frame_length = 2048
    # hop_length = 512 (11.6ms @ 44.1kHz)
    hop_length = 512
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    peaks, _ = scipy.signal.find_peaks(rms, height=threshold, distance=int(duration * sr / hop_length))
    
    return [(times[p], "time", duration, rms[p]) for p in peaks]

def detect_calls_freq(y, sr, threshold, duration):
    fft_size = 256
    hop_length = fft_size // 4  # 64サンプル（75%オーバーラップ）
    D = np.abs(librosa.stft(y, n_fft=fft_size, hop_length=hop_length))
    D_db = librosa.amplitude_to_db(D, ref=np.max)
    
    freqs = librosa.fft_frequencies(sr=sr, n_fft=fft_size)
    freq_mask = (freqs >= args.low_freq) & (freqs <= args.high_freq)  # 周波数範囲を引数から設定
    
    bird_energy = np.mean(D_db[freq_mask, :], axis=0)
    times = librosa.frames_to_time(np.arange(len(bird_energy)), sr=sr, hop_length=hop_length)
    
    peaks, _ = scipy.signal.find_peaks(bird_energy, height=threshold, distance=int(duration * sr / hop_length))
    
    return [(times[p], "freq", duration, bird_energy[p]) for p in peaks]

def save_spectrogram(y, sr, output_path, time_ranges=None):
    """スペクトログラムを生成して保存する"""
    def create_spectrogram(data, title, output_file):
        plt.figure(figsize=(10, 4))
        D = librosa.amplitude_to_db(np.abs(librosa.stft(data, n_fft=256)), ref=np.max)
        librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='linear', cmap='viridis',
                               fmin=args.low_freq, fmax=args.high_freq)
        plt.colorbar(format='%+2.0f dB')
        plt.title(title)
        plt.savefig(output_file)
        plt.close()

    if time_ranges is None:
        # 全体のスペクトログラム
        create_spectrogram(y, "Spectrogram", output_path)
        return

    # 各検出区間のスペクトログラム
    output_base = os.path.splitext(output_path)[0]
    for start_time, end_time, call_no in time_ranges:
        start_sample = max(0, int(start_time * sr))
        end_sample = min(len(y), int(end_time * sr))
        y_segment = y[start_sample:end_sample]
        
        title = f"Call No.{call_no} (Time: {start_time:.2f}-{end_time:.2f}s)"
        output_file = f"{output_base}_no{call_no}.png"
        create_spectrogram(y_segment, title, output_file)

if __name__ == "__main__":
    main()
