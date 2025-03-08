#!/usr/bin/env python3
__version__ = 'v0.0.2'
__last_updated__ = '2025-03-08 12:13:20'

#!/usr/bin/env python3

import argparse
import os
import sys
from datetime import datetime, timedelta

def validate_absolute_timestamp(date_str, time_str):
    """絶対時刻の形式を検証し、datetimeオブジェクトを返す"""
    try:
        if not (len(date_str) == 6 and len(time_str) == 6):
            raise ValueError("日付は'YYMMDD'形式、時刻は'HHMMSS'形式で指定してください")
        
        year = int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:])
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:])
        
        # 2000年代として解釈
        year += 2000
        
        # 日付の妥当性チェック
        timestamp = datetime(year, month, day, hour, minute, second)
        return timestamp
    
    except ValueError as e:
        print(f"エラー: 不正な日付または時刻形式です - {e}", file=sys.stderr)
        sys.exit(1)

def validate_relative_timestamp(date_str, time_str):
    """相対時間の形式を検証し、timedeltaオブジェクトを返す"""
    try:
        if not (len(date_str) == 7 and len(time_str) == 6):  # 符号を含むので7文字
            raise ValueError("日付は'±YYMMDD'形式、時刻は'HHMMSS'形式で指定してください")
        
        if date_str[0] not in ['+', '-']:
            raise ValueError("日付の先頭に符号（+/-）が必要です")
            
        sign = 1 if date_str[0] == '+' else -1
        years = int(date_str[1:3])
        months = int(date_str[3:5])
        days = int(date_str[5:])
        hours = int(time_str[:2])
        minutes = int(time_str[2:4])
        seconds = int(time_str[4:])
        
        # 基本的な範囲チェック
        if not (0 <= months <= 12 and 0 <= days <= 31 and
               0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
            raise ValueError("時間の範囲が不正です")
        
        # 年はtimedeltaで直接扱えないので、日数に変換（概算）
        days_total = years * 365 + months * 30 + days
        
        return timedelta(
            days=sign * days_total,
            hours=sign * hours,
            minutes=sign * minutes,
            seconds=sign * seconds
        )
    
    except ValueError as e:
        print(f"エラー: 不正な相対時間形式です - {e}", file=sys.stderr)
        sys.exit(1)

def change_timestamp(args):
    """タイムスタンプを変更する"""
    # 入力ファイルの存在確認
    if not os.path.exists(args.file):
        print(f"エラー: ファイル '{args.file}' が見つかりません", file=sys.stderr)
        sys.exit(1)
    
    # 現在のタイムスタンプを取得（小数点以下の精度を保持）
    current_mtime = os.path.getmtime(args.file)
    current_timestamp = datetime.fromtimestamp(current_mtime)
    
    # 新しいタイムスタンプを計算
    if args.timestamp:
        new_timestamp = validate_absolute_timestamp(args.timestamp[0], args.timestamp[1])
        # 小数点以下の精度を現在のタイムスタンプから継承
        subsec = current_mtime - int(current_mtime)
        new_timestamp_sec = new_timestamp.timestamp() + subsec
    else:  # relative
        time_diff = validate_relative_timestamp(args.relative[0], args.relative[1])
        new_timestamp = current_timestamp + time_diff
        new_timestamp_sec = new_timestamp.timestamp()
    
    # タイムスタンプの表示（小数点以下6桁まで表示）
    print(f"Current timestamp: {datetime.fromtimestamp(current_mtime).strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"New timestamp:     {datetime.fromtimestamp(new_timestamp_sec).strftime('%Y-%m-%d %H:%M:%S.%f')}")
    
    # 実行モードでない場合は警告を表示して終了
    if not args.execute:
        print("警告: 変更を実行するには -e/--execute オプションが必要です", file=sys.stderr)
        sys.exit(0)
    
    try:
        # タイムスタンプを変更（小数点以下の精度を保持）
        os.utime(args.file, (new_timestamp_sec, new_timestamp_sec))
        print(f"タイムスタンプを変更しました: {args.file}")
    except OSError as e:
        print(f"エラー: タイムスタンプの変更に失敗しました - {e}", file=sys.stderr)
        sys.exit(2)

def main():
    parser = argparse.ArgumentParser(
        description='ファイルのタイムスタンプを変更するツール',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('-e', '--execute', action='store_true',
                      help='実際にタイムスタンプを変更（指定がない場合は表示のみ）')
    
    # 時刻指定方法のグループ
    time_group = parser.add_mutually_exclusive_group(required=True)
    time_group.add_argument('-t', '--timestamp', nargs=2, metavar=('YYMMDD', 'HHMMSS'),
                         help='絶対時刻を指定（例: 240305 183000）')
    time_group.add_argument('-r', '--relative', nargs=2, metavar=('±YYMMDD', 'HHMMSS'),
                         help='相対時間を指定（例: +010000 023000）')
    
    parser.add_argument('file', help='対象ファイル')
    
    args = parser.parse_args()
    
    change_timestamp(args)

if __name__ == '__main__':
    main() 