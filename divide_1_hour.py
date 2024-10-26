#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import subprocess
from datetime import datetime, timedelta

def usage():
    print("使用方法: python3 divide_1_hour.py [-d] [-S|-t] 入力ファイル")
    print("  -S: 時刻を毎時0分0秒に分割する（デフォルト）")
    print("  -t: 先頭から1時間毎に分割する")
    print("  -d: デバッグモード")
    print("  -h: ヘルプ")
    print("入力ファイルは666形式のみ受け付けます。")
    sys.exit(1)

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        print("エラー: ffmpegがインストールされていません。インストールしてください。")
        sys.exit(1)

def parse_666_filename(filename):
    pattern = r"(\d{6})_(\d{6})_(\d{6})(.+)\.(.+)"
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

def divide_file(input_file, start_time, duration, output_file):
    cmd = [
        "ffmpeg",
        "-i", input_file,
        "-ss", start_time,
        "-t", duration,
        "-c", "copy",
        "-y",
            output_file
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    global debug_mode
    if len(sys.argv) < 2:
        usage()
    
    check_ffmpeg()
    
    mode = "-S"  # デフォルトのモードを設定
    debug_mode = False
    input_file = None  # 入力ファイルを初期化
    
    # 引数を解析
    for arg in sys.argv[1:]:
        print(f"arg: {arg}")
        if arg == "-h":
            usage()
            sys.exit(0)  # ここでプログラムを終了
        elif arg == "-d":
            debug_mode = True
        elif arg in ["-S", "-t"]:
            mode = arg
        else:
            input_file = arg  # 入力ファイルを設定
    
    # 入力ファイルの存在確認
    if input_file is None:
        print("エラー: 入力ファイルが指定されていません。")
        sys.exit(1)
    if not debug_mode and not os.path.exists(input_file):
        print(f"エラー: 入力ファイル '{input_file}' が見つかりません。")
        sys.exit(1)
    
    start_datetime, end_datetime, other, ext = parse_666_filename(input_file)
    
    if debug_mode:
        print(f"デバッグ情報:")
        print(f"  開始日時: {start_datetime}")
        print(f"  終了日時: {end_datetime}")
        print(f"  その他情報: {other}")
        print(f"  拡張子: {ext}")
        print(f"  入力ファイル: {input_file}")
        print(f"  モード: {mode}")
    
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
        
        if not debug_mode:
            divide_file(input_file, f"{start_time:.3f}", f"{duration:.3f}", output_file)
        print(f"分割ファイルを作成しました: {output_file}")
        
        current_time = next_time
        chunk_number += 1

if __name__ == "__main__":
    main()
