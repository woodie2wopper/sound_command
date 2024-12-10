# -*- coding: utf-8 -*-
import argparse
import os
import subprocess
import sys
import shutil

# グローバル定数として定義
NOISE_FILENAME = "noise.wav"
NOISE_IMAGE_FILENAME = "noise.png"
MICROPHONE_PATTERN_FILENAME = "microphone_pattern.txt"
FIT_CURVE_COEFF_FILENAME = "_fit_coeff.txt"
# 音声ファイルの拡張子を定義
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.WAV', '.MP3'}

# グローバル変数としてargsを定義
args = None

def parse_arguments():
    parser = argparse.ArgumentParser(description='マイクパターンを求めるバッチ処理')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグ情報を出力する')
    parser.add_argument('--toneset', '-t', type=str, help='トーンセットの周波数のマイクパターンをプロットする')
    parser.add_argument('--serch-range', '-sr', type=int, default=50, help='ピークサーチ範囲')
    parser.add_argument('--low-freq', '-lf', type=int, default=2500, help='ピークサーチの下限周波数')
    parser.add_argument('--high-freq', '-hf', type=int, default=22000, help='ピークサーチの上限周波数')
    parser.add_argument('--max', '-mx', type=int, default=45, help='マイクパターンの最大値')
    parser.add_argument('--min', '-mn', type=int, default=-20, help='マイクパターンの最小値')
    parser.add_argument('--input-dir', '-id', type=str, default='./', help='入力ディレクトリ')
    parser.add_argument('--output-file', '-o', type=str, default='microphone_pattern.txt', help='マイクパターンの出力ファイル名')
    parser.add_argument('--fft-size', '-fs', type=int, default=2048, help='FFTサイズ')
    parser.add_argument('--overlap', '-ov', type=int, default=0, help='オーバーラップ率')
    parser.add_argument('--moving-average', '-ma', type=int, default=0, help='移動平均ウィンドウサイズ')
    parser.add_argument('--fit-curve', '-fc', action='store_true', help='ノイズフロア推定のためのフィッティング曲線を使用する')
    parser.add_argument('--remove-signals', '-rs', action='store_true', help='ノイズフロア推定のための信号のピークをフィッティング線で除去する')
    parser.add_argument('--peak-floor', '-pf', type=int, default=50, help='ピーク削除のためのノイズフロアの範囲')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグ情報を出力する')
    parser.add_argument('--yes', '-y', action='store_true', help='ユーザーの入力を省略する')
    return parser.parse_args()

def is_stereo(file_path):
    command = "ffprobe -v error -show_entries stream=channels -of default=noprint_wrappers=1:nokey=1 {}".format(file_path)
    result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
    return result.stdout.strip() == '2'

def separate_stereo(input_file, left_output, right_output):
    # 既存のファイルを削除
    if os.path.exists(left_output):
        os.remove(left_output)
    if os.path.exists(right_output):
        os.remove(right_output)
    
    command = f"separate_to_mono.py -i {input_file} -ol {left_output} -or {right_output}"
    subprocess.run(command, shell=True, check=True)

def run_subprocess(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if args.debug:
            print(f"コマンド: {command}")
            print(f"結果: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        if args.debug:
            print(f"コマンド失敗: {command}")
            print(f"エラー: {e}")
            print(f"エラー出力: {e.stderr}")
        print(f"サブプロセスが失敗しました。終了します。")
        sys.exit(1)
        raise

def determine_noise_floor(input_file):
    command = (
        f"searach_Peak_from_toneset.py -t {args.toneset} -i {input_file} "
        f"-lf {args.low_freq} -hf {args.high_freq} -fs {args.fft_size} "
        f"-ov {args.overlap} -mx {args.max} -mn {args.min} "
        f"-fc "
        f"-rs "
        f"-pf {args.peak_floor} "
        f"{'-d' if args.debug else ''}"
    )
    run_subprocess(command)


def search_peak_from_toneset(file):
    input_file = file
    fit_curve_coeff_file = args.input_fit_curve_coeff
    if args.debug:
        print(f"フィッティング曲線係数ファイル: {fit_curve_coeff_file}")
    command = (
        f"searach_Peak_from_toneset.py -t {args.toneset} -i {input_file} "
        f"-lf {args.low_freq} -hf {args.high_freq} -fs {args.fft_size} "
        f"-ov {args.overlap} -mx {args.max} -mn {args.min} "
        f"{'-fc' if args.fit_curve else ''} "
        f"{'-rs' if args.remove_signals else ''} "
        f"-pf {args.peak_floor} "
        f"-ifc {fit_curve_coeff_file} "
        f"{'-d' if args.debug else ''}"
    )
    run_subprocess(command)

def plot_microphone_pattern(input_file, output_file ):
    command = (
        f"plot_microphone_pattern.py -i {input_file} -o {output_file} "
        f"-t {args.toneset} -mx {args.max} -mn {args.min} "
        f"{'-d' if args.debug else ''}"
    )
    run_subprocess(command)

# チャンネルごとの処理
def process_channel():
    output_file = MICROPHONE_PATTERN_FILENAME
    # チャンネルごとにピークを検索
    for file in os.listdir("."):
        if any(file.endswith(ext) for ext in AUDIO_EXTENSIONS):
            args.input_fit_curve_coeff = f"noise{FIT_CURVE_COEFF_FILENAME}"
            search_peak_from_toneset(file)
    # マイクパターンを生成
    generate_microphone_pattern()
    # プロットをチャンネルごとに実行
    plot_microphone_pattern(output_file, "plot_microphone_pattern_SNR.png")
    plot_microphone_pattern(output_file, "plot_microphone_pattern_Peak.png")

def generate_microphone_pattern():
    command = (
        "ls *deg*.txt | "
        "xargs -I@ awk -F, '!/^#/{match(FILENAME, /^[0-9]+/);deg = substr(FILENAME, RSTART, RLENGTH); "
        "printf \"%d,%s,%s,%s,%s\\n\",deg,$1,$2,$3,$4}' @ | "
        f"sort -t, -k1,1n >| {MICROPHONE_PATTERN_FILENAME}"
    )
    run_subprocess(command)

def display_and_confirm_noise_floor(noise_file):
    # ノイズフロアを決定
    determine_noise_floor(noise_file)
    
    # ノイズフロアの画像を表示
    noise_image_path = os.path.join(os.path.dirname(noise_file), NOISE_IMAGE_FILENAME)
    subprocess.run(["open", noise_image_path])  # macOSの場合
    # Windowsの場合は以下を使用
    # subprocess.run(["start", noise_image_path], shell=True)
    
    # args.yesがTrueの場合、ユーザーの入力を省略
    while True:
        if args.yes:
            answer = "y"
        else:
            answer = input("これでいいですか？(y/n/q): ").lower()
        if answer == "n":
            # NOの場合、再度ノイズフロアを決定
            determine_noise_floor(noise_file)
        elif answer == "q":
            print("処理を中止します")
            sys.exit(0)
        elif answer == "y":
            break

def copy_toneset_to_channels():
    toneset_path = os.path.join(args.input_dir, args.toneset)
    left_toneset_path = os.path.join(args.input_dir, "left", args.toneset)
    right_toneset_path = os.path.join(args.input_dir, "right", args.toneset)
    
    shutil.copy(toneset_path, left_toneset_path)
    shutil.copy(toneset_path, right_toneset_path)

def main():
    global args
    args = parse_arguments()
    current_dir = os.getcwd()

    # 入力ディレクトリの存在確認
    if not os.path.exists(args.input_dir):
        print(f"入力ディレクトリが存在しません: {args.input_dir}")
        exit(1)
    else:
        os.chdir(args.input_dir)

    # トーンセットファイルの存在確認
    toneset_file = os.path.join(args.input_dir, args.toneset)
    if not os.path.exists(toneset_file):
        print(f"トーンセットファイルが存在しません: {toneset_file}")
        exit(1)

    # ノイズファイルの存在確認
    noise_file = os.path.join(args.input_dir, NOISE_FILENAME)
    if not os.path.exists(noise_file):
        print(f"ノイズファイルが存在しません: {noise_file}")
        exit(1)

    if is_stereo(noise_file):
        # ステレオファイルを左右に分割
        left_noise = os.path.join(args.input_dir, "left", NOISE_FILENAME)
        right_noise = os.path.join(args.input_dir, "right", NOISE_FILENAME)
        os.makedirs(os.path.dirname(left_noise), exist_ok=True)
        os.makedirs(os.path.dirname(right_noise), exist_ok=True)
        separate_stereo(noise_file, left_noise, right_noise)
        # トーンセットファイルを左右のディレクトリにコピー
        copy_toneset_to_channels()

        # 左右のノイズ���ロアを表示して確認
        if args.debug:
            print(f"左チャネルのノイズファイル: {left_noise}")
        display_and_confirm_noise_floor(left_noise)
        if args.debug:
            print(f"右チャネルのノイズファイル: {right_noise}")
        display_and_confirm_noise_floor(right_noise)


    else:
        # モノラルの場合、直接ノイズフロアを決定
        determine_noise_floor(noise_file)
        process_channel()

    # ステレオファイルを左右に分割
    for file in os.listdir(args.input_dir):
        if (file.endswith(tuple(AUDIO_EXTENSIONS)) and file != NOISE_FILENAME):
            file_path = os.path.join(args.input_dir, file)
            if is_stereo(file_path):
                left_output = os.path.join(args.input_dir, "left", file)
                right_output = os.path.join(args.input_dir, "right", file)
                os.makedirs(os.path.dirname(left_output), exist_ok=True)
                os.makedirs(os.path.dirname(right_output), exist_ok=True)
                separate_stereo(file_path, left_output, right_output)
    # 元のディレクトリに戻る
    os.chdir(current_dir)

    # 右チャネルの処理
    right_dir = os.path.join(args.input_dir, "right")
    if args.debug:
        print(f"チャンネルディレクトリ: {right_dir}")
    os.chdir(right_dir)
    process_channel()

    # 左チャネルの処理
    os.chdir(current_dir)
    left_dir = os.path.join(args.input_dir, "left")
    if args.debug:
        print(f"チャンネルディレクトリ: {left_dir}")
    os.chdir(left_dir)
    process_channel()

    os.chdir(current_dir)

if __name__ == "__main__":
    main()