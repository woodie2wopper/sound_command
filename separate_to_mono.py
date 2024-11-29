#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
import os
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='ステレオの音源をモノラルに分割する')
    parser.add_argument('--input-file', '-i', type=str, help='入力ファイル名')
    parser.add_argument('--output-left', '-ol', type=str, help='左モノラル出力ファイル名')
    parser.add_argument('--output-right', '-or', type=str, help='右モノラル出力ファイル名')
    parser.add_argument('--force', '-f', action='store_true', help='強制的に上書きする')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグ情報を出力する')
    return parser.parse_args()

def separate_to_mono(args):
    # output_leftが設定されていない場合、入力ファイル名から生成
    if args.output_left is None:
        # 入力ファイルの拡張子とボディを分離
        input_body = args.input_file.rsplit('.', 1)[0]  
        input_ext = args.input_file.rsplit('.', 1)[1]
        # 新しいファイル名を生成
        args.output_left = f"{input_body}_left.{input_ext}"
        
        if args.debug:
            print(f"出力ファイル名(左)を生成: {args.output_left}")

    # output_rightが設定されていない場合、入力ファイル名から生成
    if args.output_right is None:
        args.output_right = f"{input_body}_right.{input_ext}"
        if args.debug:
            print(f"出力ファイル名(右)を生成: {args.output_right}")
    # -fオプションが指定されていない場合、既存ファイルの確認
    if not args.force:
        # 左チャンネル出力ファイルの存在確認
        if os.path.exists(args.output_left):
            print(f"エラー: 出力ファイル {args.output_left} が既に存在します。上書きする場合は -f オプションを指定してください。", file=sys.stderr)
            sys.exit(1)
            
        # 右チャンネル出力ファイルの存在確認 
        if os.path.exists(args.output_right):
            print(f"エラー: 出力ファイル {args.output_right} が既に存在します。上書きする場合は -f オプションを指定してください。", file=sys.stderr)
            sys.exit(1)

    # ffmpegコマンドを構築
    command_left = [
        'ffmpeg', '-loglevel', 'quiet', '-i', args.input_file, '-filter_complex', 'channelsplit=channel_layout=stereo:channels=FL[left]', '-map', '[left]', args.output_left
    ]
    command_right = [
        'ffmpeg', '-loglevel', 'quiet', '-i', args.input_file, '-filter_complex', 'channelsplit=channel_layout=stereo:channels=FR[right]', '-map', '[right]', args.output_right
    ]

    # --forceオプションが指定された場合、-yを追加
    if args.force:
        command_left.insert(1, '-y')
        command_right.insert(1, '-y')

    if args.debug:
        print("左チャンネル分割コマンド:", ' '.join(command_left))
        print("右チャンネル分割コマンド:", ' '.join(command_right))

    # 左チャンネルを抽出
    subprocess.run(command_left, check=True)
    # 右チャンネルを抽出
    subprocess.run(command_right, check=True)

def main():
    global args
    args = parse_arguments()
    separate_to_mono(args)

if __name__ == "__main__":
    main()
