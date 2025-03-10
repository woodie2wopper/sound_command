#!/usr/bin/env python3

import argparse
import os
import sys
from datetime import datetime, timedelta
import subprocess
from pathlib import Path
import json

def get_duration(file_path):
    """ffprobeを使用してメディアファイルの長さを取得"""
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', file_path],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError):
        print(f"エラー: ファイル '{file_path}' の長さを取得できません", file=sys.stderr)
        sys.exit(1)

def format_timestamp(dt):
    """datetimeオブジェクトを666フォーマットの日時文字列に変換"""
    return dt.strftime('%y%m%d_%H%M%S')

def format_mf(bird_type, dt, location, observer, ext):
    """森下フォーマットでファイル名を生成"""
    timestamp = dt.strftime('%Y%m%d%H%M%S')
    # Replace spaces with hyphens in each component
    bird_type = bird_type.replace(' ', '-')
    location = location.replace(' ', '-')
    observer = observer.replace(' ', '-')
    return f"{bird_type}_{timestamp}_{location}_{observer}{ext}"

def get_audio_info(file_path):
    """Get detailed information about the audio file"""
    try:
        # Get file information
        file_stat = os.stat(file_path)
        file_time = datetime.fromtimestamp(file_stat.st_mtime)
        
        # Get audio information using ffprobe
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
             '-show_entries', 'format=duration,size : stream=channels,sample_rate,codec_name',
             '-of', 'json', file_path],
            capture_output=True, text=True, check=True
        )
        info = json.loads(result.stdout)
        
        # Calculate duration in HH:MM:SS format
        duration_seconds = float(info['format']['duration'])
        hours = int(duration_seconds // 3600)
        minutes = int((duration_seconds % 3600) // 60)
        seconds = duration_seconds % 60
        duration_hhmmss = f"{hours:02d}:{minutes:02d}:{seconds:05.2f}"
        
        # Format information
        details = {
            'Filename': os.path.basename(file_path),
            'File size': f"{int(info['format']['size']) / 1024 / 1024:.1f} MB",
            'Timestamp': file_time.strftime('%Y-%m-%d %H:%M:%S'),
            'Duration': f"{duration_seconds:.1f} seconds ({duration_hhmmss})",
            'Codec': info['streams'][0]['codec_name'],
            'Channels': info['streams'][0]['channels'],
            'Sample rate': f"{int(info['streams'][0]['sample_rate'])/1000:.1f} kHz",
        }
        return details
    
    except (subprocess.CalledProcessError, KeyError, ValueError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to get file information - {e}", file=sys.stderr)
        return None

def get_stat_info(file_path):
    """Get file stat information based on OS"""
    try:
        if sys.platform == 'darwin':  # macOS
            result = subprocess.run(['stat', file_path], capture_output=True, text=True, check=True)
            return result.stdout
        elif sys.platform == 'win32':  # Windows
            # Windows format
            file_stat = os.stat(file_path)
            file_time = datetime.fromtimestamp(file_stat.st_mtime)
            access_time = datetime.fromtimestamp(file_stat.st_atime)
            create_time = datetime.fromtimestamp(file_stat.st_ctime)
            return (f"  Size: {file_stat.st_size} bytes\n"
                   f"  Access: {access_time.strftime('%Y-%m-%d %H:%M:%S.%f')} +0900\n"
                   f"  Modify: {file_time.strftime('%Y-%m-%d %H:%M:%S.%f')} +0900\n"
                   f"  Create: {create_time.strftime('%Y-%m-%d %H:%M:%S.%f')} +0900")
        else:  # Linux and others
            result = subprocess.run(['stat', file_path], capture_output=True, text=True, check=True)
            return result.stdout
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"Warning: Failed to get stat information - {e}", file=sys.stderr)
        return None

def is_666_format(filename):
    """Check if the filename is already in 666 format"""
    # 666 format: YYMMDD_HHMMSS_HHMMSS_ITEM_ORIGINAL.EXT
    parts = Path(filename).stem.split('_')
    if len(parts) < 3:
        return False
    
    try:
        # Check date format (YYMMDD)
        if not (len(parts[0]) == 6 and parts[0].isdigit()):
            return False
        
        # Check time formats (HHMMSS)
        if not (len(parts[1]) == 6 and parts[1].isdigit() and
                len(parts[2]) == 6 and parts[2].isdigit()):
            return False
        
        return True
    except (IndexError, ValueError):
        return False

def parse_666_format(filename):
    """666フォーマットのファイル名を解析し、タイムスタンプと元のファイル名を取得"""
    try:
        parts = Path(filename).stem.split('_')
        if len(parts) < 5:  # YYMMDD_HHMMSS_HHMMSS_ITEM_ORIGINAL
            return None
        
        # タイムスタンプを解析
        date_str = parts[0]
        time_str = parts[1]  # 開始時刻を使用
        
        year = 2000 + int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:])
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:])
        
        timestamp = datetime(year, month, day, hour, minute, second)
        
        # オリジナルのファイル名を再構築
        original_name = '_'.join(parts[4:])  # ITEM以降を結合
        
        return timestamp, original_name
    except (IndexError, ValueError):
        return None

def revert_to_original(args, input_file):
    """666フォーマットのファイルを元に戻す"""
    path = Path(input_file)
    
    # 666フォーマットかチェック
    if not is_666_format(path.name):
        print(f"# Warning: {path.name} is not in 666 format, skipping", file=sys.stderr)
        return None
    
    # 666フォーマットを解析
    result = parse_666_format(path.name)
    if result is None:
        print(f"# Error: Failed to parse 666 format filename: {path.name}", file=sys.stderr)
        return None
    
    timestamp, original_name = result
    new_name = f"{original_name}{path.suffix}"
    
    # 詳細情報の表示
    if args.verbose:
        print("\n# === File Information (ffprobe) ===")
        details = get_audio_info(input_file)
        if details:
            for key, value in details.items():
                print(f"# {key}: {value}")
        
        print("\n# === File Information (stat) ===")
        stat_info = get_stat_info(input_file)
        if stat_info:
            for line in stat_info.splitlines():
                print(f"# {line}")
        print("# ==================")
    
    # 現在のタイムスタンプと666フォーマットの時刻を比較
    current_mtime = datetime.fromtimestamp(os.path.getmtime(input_file))
    time_diff = abs((current_mtime - timestamp).total_seconds())
    if time_diff > 1:  # 1秒以上の差がある場合
        print(f"# Warning: Current timestamp ({current_mtime.strftime('%Y-%m-%d %H:%M:%S')}) "
              f"differs from 666 format timestamp ({timestamp.strftime('%Y-%m-%d %H:%M:%S')})", 
              file=sys.stderr)
    
    return new_name, timestamp

def generate_filename(args, input_file):
    """Generate filename in 666 format or Morishita format"""
    # Parse input file path
    path = Path(input_file)
    original_name = path.stem.replace(' ', '-')  # Replace spaces in original name
    ext = path.suffix

    # Check if already in 666 format
    if is_666_format(path.name):
        if args.verbose:
            print(f"# Skipping {path.name} - already in 666 format")
        return None

    # Display detailed information
    if args.verbose:
        print("# === File Information (ffprobe) ===")
        details = get_audio_info(input_file)
        if details:
            for key, value in details.items():
                print(f"# {key}: {value}")
        
        print("\n# === File Information (stat) ===")
        stat_info = get_stat_info(input_file)
        if stat_info:
            for line in stat_info.splitlines():
                print(f"# {line}")
        print("# ==================")

    # Get timestamp
    timestamp = datetime.fromtimestamp(os.path.getmtime(input_file))
    
    # Time difference adjustment
    if args.timediff:
        h = int(args.timediff[1:3])
        m = int(args.timediff[3:5])
        s = int(args.timediff[5:])
        delta = timedelta(hours=h, minutes=m, seconds=s)
        if args.timediff[0] == '+':
            timestamp += delta
        else:
            timestamp -= delta

    # Direct specification of recording time
    if args.timestamp:
        date_str, time_str = args.timestamp
        year = 2000 + int(date_str[:2])
        month = int(date_str[2:4])
        day = int(date_str[4:])
        hour = int(time_str[:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:])
        timestamp = datetime(year, month, day, hour, minute, second)

    # Get recording duration
    duration = get_duration(input_file)
    duration_td = timedelta(seconds=duration)

    # Calculate start and end times
    if args.start_time:
        start_time = timestamp
        end_time = timestamp + duration_td
    elif args.end_time:
        end_time = timestamp
        start_time = timestamp - duration_td
    else:
        print("Warning: -s/--start-time or -e/--end-time must be specified", file=sys.stderr)
        sys.exit(1)

    # Morishita format
    if args.format == 'mf':
        if not all([args.bird_type, args.location, args.observer]):
            print("Error: -b, -l, -n options are required for Morishita format", file=sys.stderr)
            sys.exit(1)
        return format_mf(args.bird_type, start_time, args.location, args.observer, ext)

    # 666 format
    item = args.item.replace(' ', '-') if args.item else 'none'  # Replace spaces in item name
    date_str = start_time.strftime('%y%m%d')  # Date is taken from start time
    start_str = start_time.strftime('%H%M%S')
    end_str = end_time.strftime('%H%M%S')
    return f"{date_str}_{start_str}_{end_str}_{item}_{original_name}{ext}"

def main():
    parser = argparse.ArgumentParser(
        description='音声・動画ファイルのタイムスタンプから666フォーマットのファイル名を生成\n'
                   '注意：既に666フォーマット（YYMMDD_HHMMSS_HHMMSS_*）のファイルはスキップされます\n'
                   'ファイルのタイムスタンプを変更する場合はchange_filestamp.pyを使用してください',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument('files', nargs='+', help='入力ファイル')
    
    # 動作モードを指定するグループ
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument('--revert', action='store_true',
                         help='666フォーマットのファイル名を元に戻す')
    mode_group.add_argument('-s', '--start-time', action='store_true',
                         help='ファイルスタンプを録音開始時間として扱う')
    mode_group.add_argument('-e', '--end-time', action='store_true',
                         help='ファイルスタンプを録音終了時間として扱う')
    
    parser.add_argument('-T', '--timestamp', nargs=2, metavar=('YYMMDD', 'HHMMSS'),
                      help='録音時刻を指定（例: 241031 123345）')
    parser.add_argument('-i', '--item', help='録音機器の指定')
    parser.add_argument('-f', '--format', choices=['mf'],
                      help='出力フォーマット指定（mf: 森下フォーマット）')
    parser.add_argument('-t', '--timediff', default='+000000',
                      help='時差指定（±HHMMSS形式、デフォルト: +000000）')
    parser.add_argument('-d', '--output-dir',
                      help='出力ディレクトリ指定')
    parser.add_argument('-o', '--output', choices=['mv', 'cp'], default='mv',
                      help='出力コマンド（mv/cp、デフォルト: mv）')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='詳細情報を表示')
    
    # Morishita format options
    parser.add_argument('-b', '--bird-type', help='鳥の種類（森下フォーマット用）')
    parser.add_argument('-l', '--location', help='場所（森下フォーマット用）')
    parser.add_argument('-n', '--observer', help='観察者名（森下フォーマット用）')

    args = parser.parse_args()

    # Verify time difference format (only if not in revert mode)
    if not args.revert and not args.timediff.startswith(('+', '-')) or not len(args.timediff) == 7:
        print("Error: Time difference must be specified in ±HHMMSS format", file=sys.stderr)
        sys.exit(1)

    # Verify output directory
    if args.output_dir and not os.path.isdir(args.output_dir):
        print(f"Error: Output directory '{args.output_dir}' not found", file=sys.stderr)
        sys.exit(1)

    for input_file in args.files:
        if not os.path.exists(input_file):
            print(f"Error: File '{input_file}' not found", file=sys.stderr)
            continue

        if args.revert:
            # 666フォーマットから元に戻す
            result = revert_to_original(args, input_file)
            if result is None:
                continue
            
            new_name, timestamp = result
            output_dir = args.output_dir if args.output_dir else os.path.dirname(input_file)
            new_path = os.path.join(output_dir, new_name)
            
            # mvコマンドを表示
            mv_cmd = f"{args.output} {input_file} {new_path}"
            print(mv_cmd)
            
            # change_filestamp.pyコマンドを表示（マイクロ秒を含む）
            date_str = timestamp.strftime('%y%m%d')
            time_str = timestamp.strftime('%H%M%S.%f')
            ts_cmd = f"change_filestamp.py -t {date_str} {time_str} -e {new_path}"
            print(ts_cmd)
        else:
            # 通常の666フォーマット変換
            new_name = generate_filename(args, input_file)
            if new_name is None:  # Skip if already in 666 format
                continue
            
            output_dir = args.output_dir if args.output_dir else os.path.dirname(input_file)
            new_path = os.path.join(output_dir, new_name)
            
            # コマンドを表示
            cmd = f"{args.output} {input_file} {new_path}"
            print(cmd)

if __name__ == '__main__':
    main() 