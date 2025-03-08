#!/usr/bin/env python3
__version__ = 'v0.0.4'
__last_updated__ = '2025-03-08 13:57:08'

"""
v0.0.3の変更点：
1. タイムスタンプのマイクロ秒対応
   - 絶対時刻指定（-t）でマイクロ秒まで指定可能に
   - 相対時間指定（-r）でもマイクロ秒まで指定可能に
   - 時刻形式を 'HHMMSS[.xxxxxx]' に変更（xxxxxx は最大6桁）
   - 小数点以下の桁数が6桁未満の場合は0で埋める

2. 全角文字対応
   - コマンドライン引数をUnicodeで正規化（全角英数字を半角に変換）
   - 全角オプション（-ｒ、-Ｔなど）にも対応
   - 長いオプション名の全角バージョン（--ｒｅｌａｔｉｖｅなど）も追加

使用例：
  $ change_timestamp.py -t 240305 183000.123456 -e file.wav    # 絶対時刻（マイクロ秒あり）
  $ change_timestamp.py -r +010000 023000.123456 -e file.wav   # 相対時間（マイクロ秒あり）
  $ change_timestamp.py -ｒ +010000 023000.123456 -e file.wav  # 全角オプション
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
import unicodedata

def validate_absolute_timestamp(date_str, time_str):
    """絶対時刻の形式を検証し、datetimeオブジェクトを返す"""
    try:
        if not (len(date_str) == 6):
            raise ValueError("日付は'YYMMDD'形式で指定してください")
        
        # 時刻は'HHMMSS[.xxxxxx]'形式を受け付ける
        time_parts = time_str.split('.')
        if len(time_parts) > 2 or len(time_parts[0]) != 6:
            raise ValueError("時刻は'HHMMSS[.xxxxxx]'形式で指定してください")
        
        year = int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:])
        hour = int(time_parts[0][:2])
        minute = int(time_parts[0][2:4])
        second = int(time_parts[0][4:])
        
        # マイクロ秒の処理
        microsecond = 0
        if len(time_parts) == 2:
            # 小数点以下の桁数を6桁（マイクロ秒）に調整
            frac = time_parts[1][:6]  # 最大6桁まで使用
            frac = frac.ljust(6, '0')  # 6桁未満の場合は0で埋める
            microsecond = int(frac)
        
        # 2000年代として解釈
        year += 2000
        
        # 日付の妥当性チェック
        timestamp = datetime(year, month, day, hour, minute, second, microsecond)
        return timestamp
    
    except ValueError as e:
        print(f"エラー: 不正な日付または時刻形式です - {e}", file=sys.stderr)
        sys.exit(1)

def validate_relative_timestamp(date_str, time_str):
    """相対時間の形式を検証し、年月日時分秒の差分を返す"""
    try:
        if not (len(date_str) == 7):  # 符号を含むので7文字
            raise ValueError("日付は'±YYMMDD'形式で指定してください")
        
        # 時刻は'HHMMSS[.xxxxxx]'形式を受け付ける
        time_parts = time_str.split('.')
        if len(time_parts) > 2 or len(time_parts[0]) != 6:
            raise ValueError("時刻は'HHMMSS[.xxxxxx]'形式で指定してください")
        
        if date_str[0] not in ['+', '-']:
            raise ValueError("日付の先頭に符号（+/-）が必要です")
            
        sign = 1 if date_str[0] == '+' else -1
        years = int(date_str[1:3])
        months = int(date_str[3:5])
        days = int(date_str[5:])
        hours = int(time_parts[0][:2])
        minutes = int(time_parts[0][2:4])
        seconds = int(time_parts[0][4:])
        
        # マイクロ秒の処理
        microseconds = 0
        if len(time_parts) == 2:
            # 小数点以下の桁数を6桁（マイクロ秒）に調整
            frac = time_parts[1][:6]  # 最大6桁まで使用
            frac = frac.ljust(6, '0')  # 6桁未満の場合は0で埋める
            microseconds = int(frac)
        
        # 基本的な範囲チェック
        if not (0 <= months <= 12 and 0 <= days <= 31 and
               0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59):
            raise ValueError("時間の範囲が不正です")
        
        return (sign, years, months, days, hours, minutes, seconds, microseconds)
    
    except ValueError as e:
        print(f"エラー: 不正な相対時間形式です - {e}", file=sys.stderr)
        sys.exit(1)

def get_file_info(file_path):
    """ファイルの詳細情報を取得（プラットフォーム非依存）"""
    try:
        stat_info = os.stat(file_path)
        access_time = datetime.fromtimestamp(stat_info.st_atime)
        modify_time = datetime.fromtimestamp(stat_info.st_mtime)
        create_time = datetime.fromtimestamp(stat_info.st_ctime)
        
        # ファイルのパーミッションを8進数で表示
        mode = stat_info.st_mode
        permission = oct(mode)[-3:]  # 最後の3桁が通常のパーミッション
        
        details = {
            'File': os.path.basename(file_path),
            'Size': f"{stat_info.st_size:,} bytes",
            'Permission': f"({permission}/{mode:o})",
            'Access time': access_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'Modify time': modify_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'Create time': create_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'Device': f"{os.major(stat_info.st_dev)},{os.minor(stat_info.st_dev)}",
            'Inode': stat_info.st_ino,
            'Links': stat_info.st_nlink,
            'UID': stat_info.st_uid,
            'GID': stat_info.st_gid
        }
        return details
    except (OSError, ValueError) as e:
        print(f"Warning: Failed to get file information - {e}", file=sys.stderr)
        return None

def change_timestamp(args):
    """タイムスタンプを変更する"""
    # 入力ファイルの存在確認
    if not os.path.exists(args.file):
        print(f"エラー: ファイル '{args.file}' が見つかりません", file=sys.stderr)
        sys.exit(1)
    
    # 詳細情報の表示
    if args.verbose:
        print("\n=== File Information ===")
        details = get_file_info(args.file)
        if details:
            max_key_length = max(len(key) for key in details.keys())
            for key, value in details.items():
                print(f"{key:<{max_key_length}}: {value}")
        print("==================\n")
    
    # 現在のタイムスタンプを取得（小数点以下の精度を保持）
    current_mtime = os.path.getmtime(args.file)
    current_timestamp = datetime.fromtimestamp(current_mtime)
    
    # 新しいタイムスタンプを計算
    if args.timestamp:
        new_timestamp = validate_absolute_timestamp(args.timestamp[0], args.timestamp[1])
        new_timestamp_sec = new_timestamp.timestamp()
    else:  # relative
        sign, years, months, days, hours, minutes, seconds, microseconds = validate_relative_timestamp(args.relative[0], args.relative[1])
        # 年月日を個別に計算（閏年を考慮しない）
        new_year = current_timestamp.year + (sign * years)
        new_month = current_timestamp.month + (sign * months)
        new_day = current_timestamp.day + (sign * days)
        
        # 月の繰り上げ/繰り下げ
        while new_month > 12:
            new_month -= 12
            new_year += 1
        while new_month < 1:
            new_month += 12
            new_year -= 1
            
        # 時分秒とマイクロ秒を計算
        time_diff = timedelta(hours=sign * hours, minutes=sign * minutes, 
                            seconds=sign * seconds, microseconds=sign * microseconds)
        try:
            new_timestamp = datetime(new_year, new_month, new_day,
                                   current_timestamp.hour, current_timestamp.minute,
                                   current_timestamp.second, current_timestamp.microsecond) + time_diff
            new_timestamp_sec = new_timestamp.timestamp()
        except ValueError as e:
            # 無効な日付の場合（例：2月30日など）は月末に調整
            if new_day > 28:  # 28日を超える場合のみ調整
                while True:
                    try:
                        new_timestamp = datetime(new_year, new_month, new_day,
                                               current_timestamp.hour, current_timestamp.minute,
                                               current_timestamp.second, current_timestamp.microsecond) + time_diff
                        new_timestamp_sec = new_timestamp.timestamp()
                        break
                    except ValueError:
                        new_day -= 1
                        if new_day < 1:  # 念のためのチェック
                            raise ValueError("Invalid date adjustment") from e
    
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
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='詳細情報を表示')
    
    # 時刻指定方法のグループ
    time_group = parser.add_mutually_exclusive_group(required=True)
    time_group.add_argument('-t', '--timestamp', nargs=2, metavar=('YYMMDD', 'HHMMSS[.xxxxxx]'),
                         help='絶対時刻を指定（例: 240305 183000.123456）')
    time_group.add_argument('-r', '--relative', nargs=2, metavar=('±YYMMDD', 'HHMMSS[.xxxxxx]'),
                         help='相対時間を指定（例: +010000 023000.123456）')
    
    parser.add_argument('file', help='対象ファイル')
    
    args = parser.parse_args()
    
    change_timestamp(args)

if __name__ == '__main__':
    main() 