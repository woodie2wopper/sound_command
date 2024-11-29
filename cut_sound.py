#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import sys
import json

def parse_arguments():
    parser = argparse.ArgumentParser(description='音源の指定時刻から継続時間を指定して音源を切り取る')
    parser.add_argument('--input', '-i', type=str, help='入力ファイル名')
    parser.add_argument('--start', '-s', type=float, help='切り取る開始時刻（秒）')
    parser.add_argument('--duration', '-D', type=float, help='切り取る継続時間（秒）')
    parser.add_argument('--output', '-o', type=str, help='出力ファイル名（指定されない場合は入力ファイル名+"_cut.WAV"）')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細モード（切り取りは行わず音源情報を出力する）')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグモード')
    args = parser.parse_args()
    
    # 出力ファイル名が指定されていない場合、デフォルト名を設定
    if args.output is None and args.input is not None:
        args.output = args.input.rsplit('.', 1)[0] + '_cut.WAV'
    
    # -v オプションが指定されていない場合、--start と --duration を必須とする
    if not args.verbose:
        if args.start is None or args.duration is None:
            parser.error('the following arguments are required: --start/-s, --duration/-D')
        
    return args

def check_ffmpeg(verbose):
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, check=True)
        if verbose:
            print(result.stdout.splitlines()[0])  # ffmpegのバージョン情報を表示
    except FileNotFoundError:
        print("Error: ffmpegがインストールされていません。")
        sys.exit(1)

def cut_audio(input_file, start_time, duration, output_file, verbose, debug):
    command = ['ffmpeg', '-i', input_file, '-ss', str(start_time), '-t', str(duration), output_file]
    if not verbose:
        command.insert(1, '-v')
        command.insert(2, 'error')
    
    if verbose:
        # ffprobeを使用して音源情報をJSON形式で取得
        command = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration:stream=codec_name,channels',
            '-of', 'json',
            input_file
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        # JSON出力をパース
        info = json.loads(result.stdout)
        
        # 整形して出力
        print("File information:")
        print(f"  File name: {input_file}")
        print(f"  Duration: {info['format']['duration']} seconds")
        for stream in info['streams']:
            print(f"  Codec: {stream['codec_name']}")
            print(f"  Channels: {stream['channels']}")
        
        return  # ここで関数を終了

    if debug:
        print("Executing command:", ' '.join(command))
    
    subprocess.run(command, check=True)

def main():
    args = parse_arguments()
    
    # 入力ファイルが指定されていない場合はヘルプを表示して終了
    if not args.input:
        print("Error: 入力ファイルが指定されていません。")
        print()
        parser = argparse.ArgumentParser(description='音源の指定時刻から継続時間を指定して音源を切り取る')
        parser.print_help()
        sys.exit(1)
    
    check_ffmpeg(args.verbose)  # ffmpegの存在を確認し、-vモードでバージョンを表示
    cut_audio(args.input, args.start, args.duration, args.output, args.verbose, args.debug)

if __name__ == "__main__":
    main()
