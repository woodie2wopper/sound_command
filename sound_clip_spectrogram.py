#!/usr/bin/env python3

import argparse
import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import os
import sys
from tqdm import tqdm
import soundfile as sf

def parse_arguments():
    parser = argparse.ArgumentParser(description='音源から指定時刻の音のスペクトログラムと音を出力する')
    parser.add_argument('-i', '--input-file', type=str, required=True, help='入力ファイル')
    parser.add_argument('-t', '--time', type=float, help='指定時刻（秒）')
    parser.add_argument('-D', '--Duration', type=float, default=5.0, help='切り出し時間（秒、デフォルト5秒）')
    parser.add_argument('-f', '--time-file', type=str, help='切り出し時間が入ったテキストファイル')
    parser.add_argument('-Bi', '--begin-time-index', type=int, help='切り出し時刻の入った列数（1オリジン）')
    parser.add_argument('-Bh', '--begin-time-header', type=str, help='切り出し時刻のヘッダ')
    parser.add_argument('-ci', '--channel-index', type=int, help='チャンネル番号の入った列数（1オリジン）')
    parser.add_argument('-ch', '--channel-header', type=str, help='チャンネルのヘッダ')
    parser.add_argument('-c', '--channel', type=str, choices=['m', 'l', 'r'], default='m', help='チャンネル選択（m:モノラル、l:左チャンネル、r:右チャンネル、デフォルト:モノラル）')
    parser.add_argument('-of', '--output-file', type=str, help='出力ファイル')
    parser.add_argument('-fs', '--fft-size', type=int, default=512, help='FFTサイズ')
    parser.add_argument('-ov', '--overlap', type=float, default=0.5, help='overlap (default 50%%)')
    parser.add_argument('-w', '--width', type=int, default=600, help='スペクトログラムの横幅：600px')
    parser.add_argument('-ht', '--height', type=int, default=400, help='スペクトログラムの縦幅：400px')
    parser.add_argument('-cm', '--colormap', type=str, default='viridis', help='スペクトログラムの色調：Viridis')
    parser.add_argument('-lf', '--low-freq', type=float, default=0.0, help='スペクトログラムの最低周波数')
    parser.add_argument('-hf', '--high-freq', type=float, default=22100.0, help='スペクトログラムの最高周波数')
    parser.add_argument('-mx', '--max', type=float, help='スペクトログラムの強度の最大値')
    parser.add_argument('-mn', '--min', type=float, help='スペクトログラムの強度の最小値')
    parser.add_argument('-d', '--debug', action='store_true', help='デバッグモード')
    parser.add_argument('-xa', '--x-axis-meaning', type=str, choices=['e', 'c'], default='c', 
                       help='スペクトログラムの横軸の意味')
    parser.add_argument('--no-x-label', action='store_true', help='x軸のラベルを非表示')
    parser.add_argument('--no-y-label', action='store_true', help='y軸のラベルを非表示')
    parser.add_argument('--no-x-axis', action='store_true', help='x軸を非表示')
    parser.add_argument('--no-y-axis', action='store_true', help='y軸を非表示')
    parser.add_argument('--no-title', action='store_true', help='タイトルを非表示')
    parser.add_argument('--no-legend', action='store_true', help='カラーバー（凡例）を非表示')
    parser.add_argument('-s', '--show-scale', type=float, default=0,
                       help='スケールバーの時間幅（秒）を表示（デフォルト：切り出し時間の1/10）')
    return parser.parse_args()

def print_debug_info():
    print("デバッグ情報:")
    for arg, value in vars(args).items():
        print(f"{arg}: {value}")

def load_audio_segment():
    total_duration = librosa.get_duration(path=args.input_file)
    
    # 最初にサンプリングレートを取得
    with sf.SoundFile(args.input_file) as f:
        sr = f.samplerate
    
    # 読み込み開始位置を指定時刻の前後半分ずつに変更
    start_pos = max(args.time - args.Duration/2, 0)
    end_pos = min(args.time + args.Duration/2, total_duration)
    
    # 一度に全体を読み込む
    data, _ = sf.read(args.input_file, 
                     start=int(start_pos * sr), 
                     stop=int(end_pos * sr))
    
    # チャンネルの選択
    if data.ndim > 1:  # ステレオの場合
        if args.channel == 'r':
            data = data[:, 1]  # 右チャネル
        elif args.channel == 'l':
            data = data[:, 0]  # 左チャネル
        else:  # モノラル（'m'）の場合は平均を取る
            data = np.mean(data, axis=1)
    
    return data, sr, start_pos

def plot_spectrogram(y, sr, actual_start_time):
    hop_length = int(args.fft_size * (1 - args.overlap))
    plt.figure(figsize=(args.width / 100, args.height / 100))
    
    # STFTのパラメータを調整
    n_fft = args.fft_size
    win_length = n_fft
    window = 'hann'
    center = True
    
    # STFTを計算
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop_length, 
                     win_length=win_length, window=window, center=center)
    D = librosa.amplitude_to_db(np.abs(D), ref=np.max)

    if args.x_axis_meaning == 'c':
        # スペクトログラムを表示
        librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='hz', 
                               hop_length=hop_length, cmap=args.colormap)
        
        # 時間軸を手動で設定
        num_ticks = int(args.Duration) + 1
        plt.xticks(np.linspace(0, args.Duration, num_ticks), 
                  [f"{x:.1f}" for x in np.arange(-args.Duration/2, args.Duration/2 + 0.1, 1.0)])
    else:  # 'e'の場合
        librosa.display.specshow(D, sr=sr, x_axis='time', y_axis='hz', 
                               hop_length=hop_length, cmap=args.colormap)
        num_ticks = int(args.Duration) + 1
        plt.xticks(np.linspace(0, args.Duration, num_ticks), 
                  [f"{x:.1f}" for x in np.arange(args.time - args.Duration/2, 
                                                args.time + args.Duration/2 + 0.1, 1.0)])
    
    # 軸とラ��ルの表示制御
    if args.no_x_axis:
        plt.gca().xaxis.set_visible(False)
    elif args.no_x_label:
        plt.xlabel('')
    else:
        plt.xlabel('Time (sec.)')
    
    if args.no_y_axis:
        plt.gca().yaxis.set_visible(False)
    elif args.no_y_label:
        plt.ylabel('')
    else:
        plt.ylabel('Frequency (Hz)')
    
    if args.debug:
        print(f"STFT shape: {D.shape}")
        print(f"Hop length: {hop_length}")
        print(f"Number of time points: {num_ticks}")
        
        # x軸とy軸の範囲を表示
        ax = plt.gca()
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        print(f"X-axis range: {xlim[0]:.2f} to {xlim[1]:.2f}")
        print(f"Y-axis range: {ylim[0]:.2f} to {ylim[1]:.2f}")
    
    plt.ylim(args.low_freq, args.high_freq)
    if args.min is not None and args.max is not None:
        plt.clim(args.min, args.max)
    
    # カラーバーの表示制御
    if not args.no_legend:
        plt.colorbar(format='%+2.0f dB')
    
    # タイトルの表示制御
    if not args.no_title:
        channel_str = 'Right' if args.channel == 'r' else 'Left' if args.channel == 'l' else 'Mono'
        title = f'{channel_str} channel: {args.time:.1f} sec.'
        plt.title(title)
    
    # スケールバーの表示
    if args.show_scale is not None:
        # スケールバーの色を設定
        color_scale = 'red'
        
        # スケールバーの位置とサイズを計算
        if args.show_scale == 0:
            args.show_scale = args.Duration / 10
        scale_width = args.show_scale
        
        # プロットの現在の範囲を取得
        ax = plt.gca()
        ylim = ax.get_ylim()
        total_height = ylim[1] - ylim[0]
        
        # スケールバーの位置を設定（右下）
        margin = 0.1
        bar_y = ylim[0] + total_height * margin
        bar_x_end = args.Duration * (1 - margin)
        bar_x_start = bar_x_end - scale_width
        
        # 横線を描画
        if args.debug:
            print(f"bar_x_start: {bar_x_start}, bar_x_end: {bar_x_end}, bar_y: {bar_y}")
        plt.plot([bar_x_start, bar_x_end], [bar_y, bar_y], 
                color=color_scale, linewidth=1)
        
        # 両端の縦線を描画
        tick_height = total_height * 0.02
        plt.plot([bar_x_start, bar_x_start], 
                [bar_y, bar_y + tick_height], 
                color=color_scale, linewidth=1)
        plt.plot([bar_x_end, bar_x_end], 
                [bar_y, bar_y + tick_height], 
                color=color_scale, linewidth=1)
        
        # スケールの数値を表示（位置調整）
        text_offset_x = args.show_scale * 0.7  # テキストのオフセットを調整
        text_offset_y = total_height * 0.04  # テキストのオフセットを調整
        if args.debug:
            print(f"bar_x_end: {bar_x_end}, text_offset_x: {text_offset_x}, text_offset_y: {text_offset_y}, text_y: {bar_y}")
        plt.text(bar_x_end - text_offset_x, bar_y + text_offset_y, 
                f'{scale_width:1.1f} s', 
                verticalalignment='center', 
                horizontalalignment='left',
                fontsize=12,
                color=color_scale)
    
    plt.savefig(args.output_file)
    plt.close()

def main():
    global args
    args = parse_arguments()
    
    if not args.time_file and args.time is None:
        print("エラー: --time-fileまたは--timeオプションのいずれか指定してください。")
        sys.exit(1)
    
    if args.debug:
        print_debug_info()
    
    if args.output_file is None:
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        args.output_file = f"{base_name}_spec.png"
    
    if args.time_file:
        # Implement logic to read time from file if specified
        pass
    
    y, sr, actual_start_time = load_audio_segment()
    plot_spectrogram(y, sr, actual_start_time)

if __name__ == "__main__":
    main()
