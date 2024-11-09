import os
import sys
import subprocess
from datetime import datetime, timedelta
import time  # 追加

def usage():
    print("使用方法: python merge_sounds.py [オプション] <file1> <file2> ...")
    print("音声ファイルをソートして結合します。ファイル名は666形式である必要があります。")
    print("注意：ギャップレス録音でない限り、結合したファイルの時間が合わない可能性があります。")
    print("注意：ffmpegとffprobeを先にインストールしてください。")
    print("オプション:")
    print("  -h ヘルプを表示")
    print("  -d デバッグモードを有効化")

def is_installed_ffmpeg():
    result = subprocess.run(
        ["ffmpeg", "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.returncode == 0

def is_installed_ffprobe():
    result = subprocess.run(
        ["ffprobe", "-version"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.returncode == 0

def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return float(result.stdout)

def parse_filename(file_path):
    filename = os.path.basename(file_path)
    base_name, ext = os.path.splitext(filename)
    
    parts = base_name.split('_')
    
    # 666形式は最初の2つの要素を結合したもの
    # format_666は先頭から6桁の数字が"_"で３つつながったもの
    if len(parts) >= 3 and all(part.isdigit() and len(part) == 6 for part in parts[:3]):
        format_666 = '_'.join(parts[:3])
    else:
        format_666 = ''  # 条件を満たさない場合は空文字列を設定
    # 残りのファイル名はformat_666以降のもので""なら拡張子を除いた全部である
    if format_666 == '':
        remaining_name = base_name
    else:
        remaining_name = '_'.join(parts[3:])
    
    return format_666, remaining_name, ext

# ファイル名で一番最初のファイルの時間を取得
def get_start_time(file_path):
    format_666, _, _ = parse_filename(file_path)
    if format_666:
        # format_666から最初の2つの6桁の数字を取得
        date_str, time_str = format_666.split('_')[:2]
        # 日付と時刻を組み合わせて datetime オブジェクトを作成
        start_time = datetime.strptime(f"20{date_str}_{time_str}", "%Y%m%d_%H%M%S")
    else:
        # format_666が空の場合は"0"を返す
        start_time = 0

    return start_time

def create_filelist(files, filelist_path):
    with open(filelist_path, 'w') as f:
        for file in files:
            f.write(f"file '{file}'\n")

def main():
    global debug_mode
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    debug_mode = False

    if not is_installed_ffmpeg():
        print("エラー: ffmpegがインストールされていません。")
        sys.exit(1)
    if not is_installed_ffprobe():
        print("エラー: ffprobeがインストールされていません。")
        sys.exit(1)

    files=[]
    for arg in sys.argv[1:]:
        if arg == "-h":
            usage()
            sys.exit(0)
        elif arg == "-d":
            debug_mode = True
        else:
            files.append(arg)

    if len(files) < 2:
        print("エラー: 2つ以上のファイルを指定する必要があります。")
        usage()
        sys.exit(1)

    original_names = ""
    ext_parts = []
    total_duration = 0

    # ファイルをソート
    sorted_files = sorted(files)
    for file in sorted_files:
        duration = get_duration(file)
        total_duration += duration
        if debug_mode:
            duration_str = f"{int(duration // 3600)}:{int(duration % 3600 // 60)}:{duration % 60}"
            total_duration_str = f"{int(total_duration // 3600)}:{int(total_duration % 3600 // 60)}:{total_duration % 60}"
            print(f"デバッグ: filepath=\"{file}\" duration=\"{duration_str}\" total_duration=\"{total_duration_str}\"")
        _, remaining_name, ext = parse_filename(file)
        original_names += f"_{remaining_name}"
        ext_parts.append(ext)
        
    # すべての拡張子が同じかチェック
    if len(set(ext_parts)) != 1:
        print("エラー: すべてのファイルの拡張子が同じではありません。")
        sys.exit(1)
    # 共通の拡張子を取得
    common_ext = ext_parts[0]
        
    # 現在のディレクトリを取得
    current_directory = os.getcwd()
    # ファイルリストを作成
    filelist_path = os.path.join(current_directory, "filelist.txt")
    create_filelist(files, filelist_path)
    
        
    # remaining_nameを結合
    combined_remaining = "".join(original_names)

    # 開始時間を取得
    start_time = get_start_time(files[0])
    # 合計時間を計算（秒単位）
    duration = int(total_duration)
    # 終了時間を計算
    end_time = start_time + timedelta(seconds=duration)

    file_start_time = f"{start_time.strftime('%y%m%d_%H%M%S')}_{end_time.strftime('%H%M%S')}"

    # 新しい出力ファイル名を作成
    output_file = f"{current_directory}/{file_start_time}{combined_remaining}{common_ext}"
    
    # ffmpegコマンドを変更
    command = f"ffmpeg -f concat -safe 0 -i {filelist_path} -c copy {output_file}"
    if debug_mode:
        print(f"コマンド: {command}")
    else:
        subprocess.run(command, shell=True)
    print(f"マージ数：{len(files)}, マージファイル：{output_file}")

if __name__ == "__main__":
    main()
