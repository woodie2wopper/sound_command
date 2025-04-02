#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import subprocess
from datetime import datetime, timedelta

def usage():
    print("使用方法: python3 divide_1_hour.py [--debug|-d] [--dry-run|-dry] [--force|-f] [--split-by-time|-t] [--separate-channel|-sc] [--help|-h] 入力ファイル")
    print("  -S, --split-by-hour: 時刻を毎時0分0秒に分割する（デフォルト・省略可）")
    print("  -t, --split-by-time: 先頭から1時間毎に分割する")
    print("  -sc, --separate-channel: 音源をチャンネル毎に分割する（デフォルトはモノラル化）")
    print("  -d, --debug: デバッグモード")
    print("  -dry, --dry-run: 実際にファイルを生成せず、何が行われるかを表示するだけのモード")
    print("  -f, --force: 既存のファイルを強制的に上書きする（デフォルトはスキップ）")
    print("  -h, --help: ヘルプ")
    print("入力ファイルは666形式のみ受け付けます。")
    print("注意: デフォルトでは毎時0分0秒に分割する(-S)モードが適用されるため、-Sオプションは省略可能です。")
    sys.exit(1)

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("エラー: ffmpegがインストールされていません。インストールしてください。")
        sys.exit(1)

def parse_666_filename(filename):
    # 修正済みの正規表現パターン: その他情報は省略可能
    pattern = r"(\d{6})_(\d{6})_(\d{6})(.*)\.(.*)"
    match = re.match(pattern, filename)
    if not match:
        print(f"エラー: 入力ファイル '{filename}' は666形式ではありません。")
        sys.exit(1)
    
    date, start_time, end_time, other, ext = match.groups()
    start_datetime = datetime.strptime(f"20{date}_{start_time}", "%Y%m%d_%H%M%S")
    # end_timeがstart_timeより小さい場合、end_timeの日付を1日進める
    end_datetime = datetime.strptime(f"20{date}_{end_time}", "%Y%m%d_%H%M%S")
    if end_time < start_time:
        end_datetime = end_datetime + timedelta(days=1)
    
    if debug_mode:
        print(f"修正後のend_datetime: {end_datetime}")
    
    return start_datetime, end_datetime, other, ext

def get_audio_channels(input_file):
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=channels",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        channels = int(result.stdout.strip())
        return channels
    except Exception as e:
        print(f"エラー: 音声チャンネル数の取得に失敗しました: {e}")
        return 1  # デフォルトは1チャンネルとして扱う

def divide_file(input_file, start_time, duration, output_file, separate_channels=False, force=False):
    # 出力ファイルが存在し、かつforce=Falseの場合はスキップ
    if os.path.exists(output_file) and not force:
        print(f"skipped: {output_file}")
        return False
    
    if not separate_channels:
        cmd = [
            "ffmpeg",
            "-i", input_file,
            "-ss", start_time,
            "-t", duration,
            "-c", "copy",
            "-y",
            output_file
        ]
        if debug_mode:
            print(f"cmd: {cmd}")
        else:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    else:
        # チャンネル数を取得
        channels = get_audio_channels(input_file)
        if debug_mode:
            print(f"チャンネル数: {channels}")
        
        # チャンネルが1つの場合は通常の処理
        if channels == 1:
            cmd = [
                "ffmpeg",
                "-i", input_file,
                "-ss", start_time,
                "-t", duration,
                "-c", "copy",
                "-y",
                output_file
            ]
            if debug_mode:
                print(f"cmd: {cmd}")
            else:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        else:
            # 複数チャンネルの場合、各チャンネルごとに分割
            base_name, ext = os.path.splitext(output_file)
            any_created = False
            for ch in range(1, channels + 1):
                ch_output = f"{base_name}-ch-{ch}{ext}"
                # チャンネル別ファイルが存在する場合はスキップ
                if os.path.exists(ch_output) and not force:
                    print(f"skipped: {ch_output}")
                    continue
                
                cmd = [
                    "ffmpeg",
                    "-i", input_file,
                    "-ss", start_time,
                    "-t", duration,
                    "-map_channel", f"0.0.{ch-1}",
                    "-ac", "1",
                    "-y",
                    ch_output
                ]
                if debug_mode:
                    print(f"cmd: {cmd}")
                else:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"created: {ch_output}")
                any_created = True
            return any_created

def is_option(arg):
    """引数がオプションかどうかを判定する"""
    return arg.startswith('-')

def is_audio_file(filename):
    """ファイルが音声ファイルかどうかを判定する"""
    return filename.lower().endswith(('.wav', '.mp3', '.aiff', '.flac', '.ogg'))

def main():
    global debug_mode
    if len(sys.argv) < 2:
        usage()
    
    check_ffmpeg()
    
    mode = "-S"  # デフォルトのモードを設定
    debug_mode = False
    dry_run = False
    force = False
    separate_channels = False
    input_file = None  # 入力ファイルを初期化
    
    i = 1
    # 引数を解析
    while i < len(sys.argv):
        arg = sys.argv[i]
        if debug_mode:
            print(f"arg: {arg}")

        if arg in ["-h", "--help"]:
            usage()
            sys.exit(0)  # ここでプログラムを終了
        elif arg in ["-d", "--debug"]:
            debug_mode = True
        elif arg in ["-dry", "--dry-run"]:
            dry_run = True
        elif arg in ["-f", "--force"]:
            force = True
        elif arg in ["-S", "--split-by-hour"]:
            mode = "-S"
        elif arg in ["-t", "--split-by-time"]:
            mode = "-t"
        elif arg in ["-sc", "--separate-channel"]:
            separate_channels = True
        elif not is_option(arg):
            # オプションでない場合は入力ファイルと判断
            input_file = arg
        else:
            print(f"エラー: 不明なオプション '{arg}'")
            usage()
            sys.exit(1)
        i += 1
    
    # 入力ファイルの存在確認
    if input_file is None:
        print("エラー: 入力ファイルが指定されていません。")
        usage()
        sys.exit(1)
    if not debug_mode and not dry_run and not os.path.exists(input_file):
        print(f"エラー: 入力ファイル '{input_file}' が見つかりません。")
        sys.exit(1)
    
    file_body_with_ext = os.path.basename(input_file)
    if debug_mode:
        print(f"file_body_with_ext: {file_body_with_ext}")
    
    try:
        start_datetime, end_datetime, other, ext = parse_666_filename(file_body_with_ext)
    except Exception as e:
        print(f"エラー: 入力ファイル '{input_file}' の解析に失敗しました: {str(e)}")
        print("入力ファイルは666形式（YYMMDD_HHMMSS_HHMMSS）である必要があります。")
        sys.exit(1)
    
    if debug_mode:
        print(f"デバッグ情報:")
        print(f"  開始日時: {start_datetime}")
        print(f"  終了日時: {end_datetime}")
        print(f"  その他情報: {other}")
        print(f"  拡張子: {ext}")
        print(f"  入力ファイル: {input_file}")
        print(f"  モード: {mode}")
        print(f"  チャンネル分割: {separate_channels}")
        print(f"  ドライラン: {dry_run}")
        print(f"  強制上書き: {force}")
    
    current_time = start_datetime
    chunk_number = 1
    
    while current_time < end_datetime:
        if mode == "-S":
            next_time = current_time.replace(minute=0, second=0) + timedelta(hours=1)
        else:  # mode == "-t"
            next_time = current_time + timedelta(hours=1)
        
        if next_time > end_datetime:
            next_time = end_datetime
        
        output_file = f"{current_time.strftime('%y%m%d_%H%M%S')}_{next_time.strftime('%H%M%S')}_d{chunk_number}{other}.{ext}"
        
        start_time = (current_time - start_datetime).total_seconds()
        duration = (next_time - current_time).total_seconds()
        
        if dry_run:
            file_exists = os.path.exists(output_file)
            if not separate_channels:
                if file_exists and not force:
                    print(f"dry-run: skipped: {output_file}")
                else:
                    print(f"dry-run: {output_file}")
            else:
                channels = 2  # ドライランモードでは仮に2チャンネルとして表示
                base_name, ext_name = os.path.splitext(output_file)
                for ch in range(1, channels + 1):
                    ch_output = f"{base_name}-ch-{ch}{ext_name}"
                    file_exists = os.path.exists(ch_output)
                    if file_exists and not force:
                        print(f"dry-run: skipped: {ch_output}")
                    else:
                        print(f"dry-run: {ch_output}")
        elif not debug_mode:
            file_created = divide_file(input_file, f"{start_time:.3f}", f"{duration:.3f}", output_file, separate_channels, force)
            if file_created and not separate_channels:
                print(f"created: {output_file}")
        
        current_time = next_time
        chunk_number += 1

if __name__ == "__main__":
    main()
