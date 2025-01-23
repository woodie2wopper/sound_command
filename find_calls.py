#!/usr/bin/env python3

__version__ = 'v0.0.6'
__last_updated__ = '2025-01-23 20:50:18'

import argparse
import numpy as np
import librosa
import librosa.display
import matplotlib.pyplot as plt
import scipy.signal
import os
import soundfile as sf

# グローバル変数
args = None

# 定数の定義
CONST = {
    # FFTパラメータ
    'FFT_SIZE': 256,  # FFTのウィンドウサイズ（5.8ms @ 44.1kHz）
    'HOP_LENGTH': 128,  # 50%オーバーラップ（2.9ms @ 44.1kHz）
    
    # 時間領域の検出パラメータ
    'TIME_FRAME_LENGTH': 2048,  # 46.4ms @ 44.1kHz
    'TIME_HOP_LENGTH': 512,    # 11.6ms @ 44.1kHz
    
    # フィルタパラメータ
    'FILTER_ORDER': 4,  # バターワースフィルタの次数
    
    # プロット設定
    'FIGURE_DPI': 100,                  # 解像度 (dots per inch)
    'FIGURE_WIDTH': 800,                # 図の幅 (pixels)
    'FIGURE_HEIGHT': 500,               # 図の高さ (pixels) - 16:10に近い黄金比
    
    # スペクトログラム設定
    'SPCTRGRM_POSITION': [0.12, 0.15, 0.75, 0.65],  # [left, bottom, width, height]
    
    # バージョン情報
    'VERSION': __version__,
    'LAST_UPDATED': __last_updated__
}

# 計算が必要な定数を追加
CONST['FIGURE_SIZE'] = (CONST['FIGURE_WIDTH'] / CONST['FIGURE_DPI'], 
                       CONST['FIGURE_HEIGHT'] / CONST['FIGURE_DPI'])

def process_audio():
    """音声データの読み込みと前処理"""
    waveform, sampling_rate = librosa.load(args.input_file, sr=None, mono=False)
    
    # ステレオかモノラルかを判定
    if waveform.ndim > 1:
        waveform = np.mean(waveform, axis=0)
        if args.debug:
            print("Stereo audio detected - channels averaged")
    
    base_name = os.path.splitext(os.path.basename(args.input_file))[0]
    
    # ローカットフィルタの適用
    if args.freq_low_cut_filter > 0:
        # バターワースフィルタの設計
        nyquist = sampling_rate / 2
        norm_cutoff = args.freq_low_cut_filter / nyquist
        b, a = scipy.signal.butter(N=CONST['FILTER_ORDER'], Wn=norm_cutoff, btype='high')
        
        # フィルタの適用
        waveform = scipy.signal.filtfilt(b, a, waveform)
        
        # フィルタ適用後の音声を保存
        lcf_file = f"{base_name}_LCF.mp3"
        # 音声データを-1から1の範囲に正規化
        waveform_normalized = librosa.util.normalize(waveform)
        # MP3として保存
        sf.write(lcf_file, waveform_normalized, sampling_rate)
        
        if args.debug:
            print(f"Applied low-cut filter at {args.freq_low_cut_filter} Hz")
            print(f"Filtered audio saved as {lcf_file}")
    
    return {'waveform': waveform, 'sampling_rate': sampling_rate}

def detect_calls():
    """鳴き声の検出処理"""
    audio_data = process_audio()
    waveform = audio_data['waveform']
    sampling_rate = audio_data['sampling_rate']
    
    # 時間領域での検出
    detections = detect_calls_time(waveform, sampling_rate)
    
    if args.debug:
        print(f"検出された鳴き声数: {len(detections)}")
    
    # 結果をまとめる
    detection_results = {
        'detections': detections,
        'waveform': waveform,
        'sampling_rate': sampling_rate,
        'audio_file': args.input_file
    }
    
    return detection_results

def detect_calls_time(waveform, sampling_rate):
    rms = librosa.feature.rms(y=waveform, frame_length=CONST['TIME_FRAME_LENGTH'], 
                            hop_length=CONST['TIME_HOP_LENGTH'])[0]
    
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sampling_rate, 
                                 hop_length=CONST['TIME_HOP_LENGTH'])
    
    # ピークの検出と幅の計測
    peaks, properties = scipy.signal.find_peaks(rms, height=args.threshold, 
                                              distance=int(args.max_call_duration * sampling_rate / CONST['TIME_HOP_LENGTH']),
                                              width=1)  # 最小幅を1サンプルに設定
    
    # 検出情報を構造化
    detections = []
    for i, peak in enumerate(peaks):
        detection = {
            'time': times[peak],                    # 検出時刻
            'method': "time",                       # 検出方法
            'peak_index': peak,                     # ピークのインデックス
            'left_ips': properties['left_ips'][i],  # 左端のインデックス
            'right_ips': properties['right_ips'][i],# 右端のインデックス
            'width': properties['widths'][i],       # 幅（サンプル数）
            'height': properties['peak_heights'][i], # ピーク値
            'width_sec': properties['widths'][i] * CONST['TIME_HOP_LENGTH'] / sampling_rate  # 幅（秒）
        }
        detections.append(detection)
    
    return detections

def save_results(detection_results):
    """結果の保存処理"""
    if detection_results is None:
        raise ValueError("No detection results available. Run detect_calls() first.")
    
    detections = detection_results['detections']
    waveform = detection_results['waveform']
    sampling_rate = detection_results['sampling_rate']
    
    # CSVファイルに結果を保存
    with open(args.output_file, "w") as f:
        f.write("No.,time(s),method,duration(s),call_value\n")
        for i, detection in enumerate(detections, 1):
            f.write(f"{i},{detection['time']:.2f},{detection['method']},"
                   f"{detection['width_sec']:.3f},{detection['height']:.2f}\n")
    
    # スペクトログラムの生成をスキップ
    if not args.no_spectrogram:
        # スペクトログラムのファイル名を生成
        base_name = os.path.splitext(os.path.basename(detection_results['audio_file']))[0]
        output_spectrogram = f"{base_name}_spectrogram.png"
        
        # スペクトログラムを保存
        save_spectrogram(detection_results, output_spectrogram)
    
    if args.debug:
        print(f"Detected {len(detections)} calls")
        if not args.no_spectrogram:
            print(f"Spectrograms saved as {os.path.splitext(output_spectrogram)[0]}_no*.png")
        print(f"Spectrogram time window: {args.spectrogram_time} seconds")
        # 検出された鳴き声の継続時間の統計を表示
        if detections:
            durations = [d['width_sec'] for d in detections]
            print(f"Call durations - min: {min(durations):.3f}s, max: {max(durations):.3f}s, "
                  f"mean: {np.mean(durations):.3f}s")
    
    return

def save_spectrogram(detection_results, output_path):
    """スペクトログラムを生成して保存する"""
    waveform = detection_results['waveform']
    sampling_rate = detection_results['sampling_rate']
    detections = detection_results['detections']
    
    def create_spectrogram(waveform_segment, start_index, title, output_file):
        """スペクトログラムを生成して保存する
        
        Args:
            waveform_segment: 切り出された波形データ（指定時間分のセグメント）
            start_index: セグメントの開始位置（サンプル）
            title: グラフのタイトル
            output_file: 出力ファイル名
        """
        plt.figure(figsize=CONST['FIGURE_SIZE'], dpi=CONST['FIGURE_DPI'])
        ax = plt.axes(CONST['SPCTRGRM_POSITION'])
        
        # スペクトログラムを描画
        D = librosa.amplitude_to_db(
            np.abs(librosa.stft(waveform_segment, 
                               n_fft=CONST['FFT_SIZE'],
                               hop_length=CONST['HOP_LENGTH'])),
            ref=np.max)
        
        img = librosa.display.specshow(D, sr=sampling_rate, x_axis='time', y_axis='hz',
                                     hop_length=CONST['HOP_LENGTH'],
                                     cmap='viridis', ax=ax)
        
        # 周波数範囲を設定
        ax.set_ylim([args.low_freq, args.high_freq])
        ax.set_xlim([0, args.spectrogram_time])
        
        if not args.spectrogram_only:
            # 通常の表示設定
            ax.tick_params(axis='both', which='both', direction='in',
                          labelbottom=True, labelleft=True,
                          bottom=True, left=True)
            ax.grid(True, which='major', axis='both',
                    alpha=0.8, linestyle='--',
                    linewidth=0.6, color='black')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Frequency (Hz)')
            plt.colorbar(img, format='%+2.0f dB', ax=ax)
            ax.set_title(title)
        else:
            # スペクトログラムのみ表示
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_xticklabels([])
            ax.set_yticklabels([])
            ax.grid(False)
            ax.set_xlabel('')
            ax.set_ylabel('')
            ax.set_title('')
        
        plt.savefig(output_file, bbox_inches='tight', pad_inches=0)
        plt.close()

    if detections is None:
        # 全体のスペクトログラム
        print("スペクトログラムなし")
        return

    # 各検出区間のスペクトログラム
    output_base = os.path.splitext(output_path)[0]
    for i, detection in enumerate(detections, 1):
        # 検出時刻を中心に指定時間分の区間を切り出し
        center_time = detection['time']
        half_window = args.spectrogram_time / 2
        
        # 時間→サンプル変換（端点処理付き）
        window_start = max(0, int((center_time - half_window) * sampling_rate))
        window_end = min(len(waveform), int((center_time + half_window) * sampling_rate))
        waveform_segment = waveform[window_start:window_end]
        
        if args.debug:
            print(f"Call No.{i} (Time: {center_time:.2f}s, Duration: {detection['width_sec']:.3f}s)")
            print(f"   Window Start: {window_start/sampling_rate:.2f}s, Window End: {window_end/sampling_rate:.2f}s")
            print(f"   Waveform Segment Length: {len(waveform_segment)} samples")
            print(f"   Waveform Segment Start: {window_start:}, End: {window_end:}")
        
        title = f"Call No.{i} (Time: {center_time:.2f}s, Duration: {detection['width_sec']:.3f}s)"
        output_file = f"{output_base}_no{i}.png"
        
        create_spectrogram(waveform_segment, window_start, title, output_file)

def parse_arguments():
    parser = argparse.ArgumentParser(description="音声ファイルから鳥の鳴き声を検出するプログラム")
    parser.add_argument("-i", "--input_file", required=True, help="Path to input audio file")
    parser.add_argument("-o", "--output_file", help="Path to output text file")
    parser.add_argument("-th", "--threshold", type=float, default=0.1, help="Detection threshold")
    parser.add_argument("-D", "--max_call_duration", type=float, default=0.2,
                       help="Maximum duration of a bird call (sec)")
    parser.add_argument("-st", "--spectrogram_time", type=float, default=1.0, help="Spectrogram time in seconds")
    parser.add_argument("-lf", "--low_freq", type=int, default=4000, help="Spectrogram low frequency limit (Hz)")
    parser.add_argument("-hf", "--high_freq", type=int, default=10000, help="Spectrogram high frequency limit (Hz)")
    parser.add_argument("-flcf", "--freq_low_cut_filter", type=int, default=0, help="Low cut filter frequency (Hz)")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-so", "--spectrogram_only", action="store_true", 
                       help="Show only spectrogram without any labels or decorations")
    parser.add_argument("-ns", "--no_spectrogram", action="store_true", 
                       help="Do not generate spectrograms")
    
    args = parser.parse_args()
    
    # 出力ファイル名のデフォルト設定
    if args.output_file is None:
        input_base = os.path.splitext(args.input_file)[0]
        args.output_file = f"{input_base}_calls.txt"
    
    # デバッグモードの場合、全ての引数を表示
    if args.debug:
        print("\n設定パラメータ:")
        print(f"入力ファイル: {args.input_file}")
        print(f"出力ファイル: {args.output_file}")
        print(f"検出閾値: {args.threshold}")
        print(f"最大鳴き声長: {args.max_call_duration} 秒")
        print(f"スペクトログラム表示時間: {args.spectrogram_time} 秒")
        print(f"周波数下限: {args.low_freq} Hz")
        print(f"周波数上限: {args.high_freq} Hz")
        print(f"ローカットフィルタ: {args.freq_low_cut_filter} Hz")
        print(f"デバッグモード: {args.debug}")
        print(f"スペクトログラムのみ表示: {args.spectrogram_only}")
        print(f"スペクトログラムを生成しない: {args.no_spectrogram}")
    return args

def main():
    global args
    args = parse_arguments()
    
    # 鳴き声の検出と結果の保存
    detection_results = detect_calls()

    if args.debug:
        print("\n検出結果:")
        print(f"音声ファイル: {detection_results['audio_file']}")
        print(f"サンプリングレート: {detection_results['sampling_rate']} Hz")
        print(f"波形データ長: {len(detection_results['waveform'])} サンプル "
              f"({len(detection_results['waveform'])/detection_results['sampling_rate']:.2f} 秒)")
        print(f"\n検出された鳴き声: {len(detection_results['detections'])} 個")
        
        for i, d in enumerate(detection_results['detections'], 1):
            print(f"\n{i}番目の鳴き声:")
            print(f"  時刻: {d['time']:.3f} 秒")
            print(f"  検出方法: {d['method']}")
            print(f"  継続時間: {d['width_sec']:.3f} 秒")
            print(f"  強度: {d['height']:.3f}")
            print(f"  ピーク位置: {d['peak_index']} ビン "
                  f"({d['peak_index'] * CONST['TIME_HOP_LENGTH']} サンプル, {d['time']:.3f} 秒)")
            print(f"  区間: {d['left_ips']:.1f} - {d['right_ips']:.1f} ビン")
            print(f"  幅: {d['width']:.1f} ビン ({d['width_sec']:.3f} 秒)")
    
    # パラメータファイルの保存
    param_file = os.path.splitext(args.input_file)[0] + "_param.txt"
    with open(param_file, "w", encoding="utf-8") as f:
        # グローバル定数を保存
        for key, value in sorted(CONST.items()):
            if isinstance(value, (list, tuple)):
                # リストや配列は要素をカンマで結合
                value_str = ";".join(str(x) for x in value)
            else:
                value_str = str(value)
            f.write(f"{key},{value_str}\n")
        
        # 解析パラメータ（args）を保存
        f.write("\n# Analysis Parameters\n")
        for key, value in sorted(vars(args).items()):
            f.write(f"{key},{value}\n")
    
    save_results(detection_results)

if __name__ == "__main__":
    main()
