#!/usr/bin/env python3

import os
import subprocess
import argparse
import time
from datetime import datetime, timedelta
from collections import defaultdict

def is_valid_timestamp_format(filename):
    # ファイル名から日付と時刻を抽出
    basename = os.path.basename(filename)
    parts = []
    
    # ファイル名に'-'が含まれている場合は'_'に置換して分割
    if '-' in basename:
        parts = basename.replace('-', '_').split('_')
    else:
        parts = basename.split('_')
    
    if len(parts) >= 3:
        try:
            # 各パーツが6桁の数字であることを確認
            if not (len(parts[0]) == 6 and len(parts[1]) == 6 and len(parts[2]) == 6):
                return False
            # 日付と時刻を結合して解析
            start_datetime = datetime.strptime(f"{parts[0]}_{parts[1]}", "%y%m%d_%H%M%S")
            end_datetime = datetime.strptime(f"{parts[0]}_{parts[2]}", "%y%m%d_%H%M%S")
            return True
        except ValueError:
            return False
    return False

def get_audio_duration(filepath):
    try:
        # ffprobeで音声ファイルの長さを取得
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return timedelta(seconds=duration)
    except Exception as e:
        print(f"Warning: ファイル '{filepath}' の長さ取得に失敗しました: {str(e)}")
    return None

def parse_filename(filename):
    # ファイル名から日付と時刻を抽出
    # まず'-'を'_'に置換して統一
    basename = os.path.basename(filename)
    parts = []
    
    # ファイル名に'-'が含まれている場合は'_'に置換して分割
    if '-' in basename:
        parts = basename.replace('-', '_').split('_')
    else:
        parts = basename.split('_')
    
    if len(parts) >= 3:
        try:
            date_str = parts[0]
            start_time = parts[1]
            end_time = parts[2]
            
            # 日付と時刻を結合して解析
            start_datetime = datetime.strptime(f"{date_str}_{start_time}", "%y%m%d_%H%M%S")
            end_datetime = datetime.strptime(f"{date_str}_{end_time}", "%y%m%d_%H%M%S")
            
            # 終了時刻が開始時刻より前の場合は翌日として扱う
            if end_datetime < start_datetime:
                end_datetime += timedelta(days=1)
                
            return start_datetime, end_datetime, None
        except ValueError:
            return None, None, f"Warning: ファイル '{filename}' の日時形式が不正です"
    return None, None, f"Warning: ファイル '{filename}' の形式が不正です（パーツ数不足）"

def get_directory_name(filepath, root_dir):
    # ファイルパスから直下のディレクトリ名を取得
    rel_path = os.path.relpath(filepath, root_dir)
    return rel_path.split(os.sep)[0]

def should_exclude(path, exclude_pattern):
    # パスに除外パターンが含まれているかチェック
    return exclude_pattern in path

def get_file_size(filepath):
    try:
        return os.path.getsize(filepath)
    except Exception:
        return 0

def format_size(size_bytes):
    # バイト数を読みやすい形式に変換
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_file_mtime(filepath):
    try:
        return os.path.getmtime(filepath)
    except Exception:
        return 0

def format_datetime(timestamp):
    if timestamp == 0:
        return "未更新"
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")

def calculate_recording_times(root_dir, verbose=False, check_filename=False, exclude_pattern=None, only_666=False):
    # ディレクトリごとの録音時間を格納する辞書
    dir_times = defaultdict(timedelta)
    file_count = defaultdict(int)
    dir_sizes = defaultdict(int)  # ディレクトリごとのファイルサイズ
    dir_last_update = defaultdict(float)  # ディレクトリごとの最終更新時刻
    warnings = []
    invalid_files = []
    
    # 指定ディレクトリの直下のディレクトリのみを対象とする
    try:
        # 直下のディレクトリを取得
        subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
        
        # すべての直下のディレクトリを初期化
        for subdir in subdirs:
            dir_path = os.path.join(root_dir, subdir)
            if not exclude_pattern or not should_exclude(dir_path, exclude_pattern):
                dir_times[subdir] = timedelta()
                file_count[subdir] = 0
                dir_sizes[subdir] = 0
                dir_last_update[subdir] = 0
        
        for subdir in subdirs:
            dir_path = os.path.join(root_dir, subdir)
            
            # ディレクトリが除外パターンに一致する場合はスキップ
            if exclude_pattern and should_exclude(dir_path, exclude_pattern):
                if verbose:
                    warnings.append(f"Info: 除外パターン '{exclude_pattern}' に一致するため、ディレクトリ '{dir_path}' をスキップしました")
                continue
            
            # 音声ファイルを検索
            for root, _, files in os.walk(dir_path):
                for file in files:
                    if file.lower().endswith(('.wav', '.mp3')):
                        filepath = os.path.join(root, file)
                        
                        # ファイルが除外パターンに一致する場合はスキップ
                        if exclude_pattern and should_exclude(filepath, exclude_pattern):
                            if verbose:
                                warnings.append(f"Info: 除外パターン '{exclude_pattern}' に一致するため、ファイル '{filepath}' をスキップしました")
                            continue
                        
                        # 666形式のチェック
                        if only_666 and not is_valid_timestamp_format(file):
                            if verbose:
                                warnings.append(f"Info: 666形式でないため、ファイル '{filepath}' をスキップしました")
                            continue
                        
                        # ファイル名の形式チェック
                        if check_filename and not is_valid_timestamp_format(file):
                            invalid_files.append(filepath)
                            continue
                        
                        # ファイル名チェックモードの場合は、ffprobeを実行しない
                        if check_filename:
                            continue
                        
                        # ファイルサイズを加算
                        dir_sizes[subdir] += get_file_size(filepath)
                        
                        # 最終更新時刻を更新
                        mtime = get_file_mtime(filepath)
                        if mtime > dir_last_update[subdir]:
                            dir_last_update[subdir] = mtime
                        
                        start_time, end_time, warning = parse_filename(file)
                        
                        if warning:
                            # ファイル名から時間を取得できない場合はffprobeで長さを取得
                            duration = get_audio_duration(filepath)
                            if duration:
                                dir_times[subdir] += duration
                                file_count[subdir] += 1
                                if verbose:
                                    warnings.append(f"Info: ファイル '{file}' の長さをffprobeで取得しました: {format_timedelta(duration)}")
                            else:
                                warnings.append(f"{warning} (場所: {filepath})")
                            continue
                        
                        if start_time and end_time:
                            # 録音時間を計算
                            duration = end_time - start_time
                            dir_times[subdir] += duration
                            file_count[subdir] += 1
    except Exception as e:
        warnings.append(f"Error: ディレクトリ '{root_dir}' の処理中にエラーが発生しました: {str(e)}")
    
    return dir_times, file_count, dir_sizes, dir_last_update, warnings, invalid_files

def format_timedelta(td):
    # timedeltaを時間:分:秒の形式に変換
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def print_help():
    print("""録音ファイルの時間を集計するスクリプト

オプション:
  -h, --help          このヘルプメッセージを表示
  -v, --verbose       詳細な情報を表示
  -d, --directory     対象ディレクトリを指定（デフォルト: "./"）
  -c, --filename-check ファイル名が666形式（6桁の時刻が3つ）になっていないファイルを表示
  -e, --exclude       指定した文字列を含むファイルまたはディレクトリを除外（例: -e ORG）
  -o6, --only-666     666形式のファイルのみを対象とする

使用例:
  python calculate_recording_times.py -v -d /path/to/directory
  python calculate_recording_times.py -c
  python calculate_recording_times.py -e ORG
  python calculate_recording_times.py -o6
  python calculate_recording_times.py -o6 -e ORG
""")

if __name__ == '__main__':
    start_time = time.time()
    
    parser = argparse.ArgumentParser(description='録音ファイルの時間を集計するスクリプト')
    parser.add_argument('-v', '--verbose', action='store_true', help='詳細な情報を表示')
    parser.add_argument('-d', '--directory', default='./', help='対象ディレクトリを指定（デフォルト: "./"）')
    parser.add_argument('-c', '--filename-check', action='store_true', help='ファイル名が666形式になっていないファイルを表示')
    parser.add_argument('-e', '--exclude', help='指定した文字列を含むファイルまたはディレクトリを除外')
    parser.add_argument('-o6', '--only-666', action='store_true', help='666形式のファイルのみを対象とする')
    args = parser.parse_args()

    # helpオプションは自動的に処理されるため、明示的なチェックは不要
    dir_times, file_count, dir_sizes, dir_last_update, warnings, invalid_files = calculate_recording_times(args.directory, args.verbose, args.filename_check, args.exclude, args.only_666)
    
    # 警告メッセージの表示
    if warnings:
        for warning in warnings:
            print(warning)
    
    # ファイル名形式チェック結果の表示
    if invalid_files:
        for filepath in invalid_files:
            print(filepath)
    
    # ファイル名チェックモードでない場合のみ、時間集計を表示
    if not args.filename_check:
        print(f"{'ディレクトリ名':<40} {'総録音時間':<15} {'ファイル数':<10} {'総容量':<15} {'最終更新':<20}")
        print("-" * 100)
        
        for dir_name in sorted(dir_times.keys()):
            if not dir_name.startswith('.'):  # 隠しディレクトリを除外
                print(f"{dir_name:<40} {format_timedelta(dir_times[dir_name]):<15} {file_count[dir_name]:<10} {format_size(dir_sizes[dir_name]):<15} {format_datetime(dir_last_update[dir_name]):<20}")
        
        # 合計を計算
        total_time = sum(dir_times.values(), timedelta())
        total_files = sum(file_count.values())
        total_size = sum(dir_sizes.values())
        print("-" * 100)
        print(f"{'合計':<40} {format_timedelta(total_time):<15} {total_files:<10} {format_size(total_size):<15} {'':<20}")
    
    # 実行時間を表示
    end_time = time.time()
    execution_time = end_time - start_time
    print(f"実行時間: {execution_time:.2f}秒") 