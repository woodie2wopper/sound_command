import os
import sys
import subprocess
from datetime import datetime, timedelta
import time  # 追加

def usage():
    print("使用方法: python merge_sounds_same_birth_time.py [オプション] <ディレクトリ>")
    print("ディレクトリ内のファイルを読み込み、ModifyTimeが同じファイルをマージします。")
    print("注意：ギャップレス録音でない限り、マージしたファイルの時間が合わない可能性があります。")
    print("オプション:")
    print("  -S: 開始時刻をタイムスタンプとして使用 (デフォルト)")
    print("  -E: 終了時刻をタイムスタンプとして使用")
    print("  -h: ヘルプを表示")
    print("  -d: デバッグモードを有効化")

def get_mtime(file_path):
    stat = os.stat(file_path)
    mtime = datetime.fromtimestamp(stat.st_mtime)  # ここで変換
    return mtime

def get_duration(file_path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return float(result.stdout)

def merge_files(files, output_file):
    input_files = '|'.join(files)
    command = f"ffmpeg -i 'concat:{input_files}' -acodec copy {output_file}"
    return command

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

def create_filelist(files, filelist_path):
    with open(filelist_path, 'w') as f:
        for file in files:
            f.write(f"file '{file}'\n")

def main():
    global debug_mode
    if len(sys.argv) < 2:
        usage()
        sys.exit(0)

    mode = "-S"
    debug_mode = False
    directory = None

    for arg in sys.argv[1:]:
        if arg == "-h":
            usage()
            sys.exit(0)
        elif arg == "-d":
            debug_mode = True
        elif arg in ["-S", "-E"]:
            mode = arg
        else:
            directory = arg

    if directory is None or not os.path.isdir(directory):
        print("エラー: 有効なディレクトリを指定する必要があります。")
        usage()
        sys.exit(1)

    sound_files = [f for f in os.listdir(directory) if f.endswith(('.wav', '.mp3', 'WAV', 'MP3'))]
    mtime_dict = {}
    original_names = ""
    ext_parts = []
    total_duration = 0
    # sound_filesをソートする
    sound_files.sort()
    # ソートされたsound_filesからファイル名を取り出す
    sorted_sound_files = [os.path.normpath(os.path.join(directory, file)) for file in sound_files]

    for file in sorted_sound_files:
        file_path = os.path.join(directory, file)
        mtime = get_mtime(file_path)
        
        # mtime_dictにキーが存在しない場合、新しいリストを作成
        if mtime not in mtime_dict:
            mtime_dict[mtime] = []
        
        mtime_dict[mtime].append(file_path)

        duration = get_duration(file_path)
        total_duration += duration
        if debug_mode:
            duration_str = f"{int(duration // 3600)}:{int(duration % 3600 // 60)}:{duration % 60}"
            total_duration_str = f"{int(total_duration // 3600)}:{int(total_duration % 3600 // 60)}:{total_duration % 60}"
            print(f"デバッグ: filepath=\"{file_path}\" ModifyTime=\"{mtime.strftime('%Y-%m-%d %H:%M:%S')}\" duration=\"{duration_str}\" total_duration=\"{total_duration_str}\"")
        _, remaining_name, ext = parse_filename(file_path)
        original_names += f"_{remaining_name}"
        ext_parts.append(ext)
        
    # すべての拡張子が同じかチェック
    if len(set(ext_parts)) != 1:
        print("エラー: すべてのファイルの拡張子が同じではありません。")
        sys.exit(1)
    # 共通の拡張子を取得
    common_ext = ext_parts[0]
    # すべてのbirth_timeが同じかチェック
    if len(mtime_dict) != 1:
        print("エラー: すべてのファイルのModifyTimeが同じではありません。")
        sys.exit(1)
        
    # 唯一のbirth_timeを取得
    mtime = list(mtime_dict.keys())[0]
    
    # mtimeに対応するファイルリストを取得
    files = mtime_dict[mtime]
    
    # ファイルリストを作成
    filelist_path = os.path.join(directory, "filelist.txt")
    create_filelist(files, filelist_path)
    
    # 合計時間を計算（秒単位）
    duration = int(total_duration)
        
    # remaining_nameを結合
    combined_remaining = "".join(original_names)
    if mode == "-S":
        start_time = mtime
        end_time = mtime + timedelta(seconds=duration)
    else:
        end_time = mtime
        start_time = mtime - timedelta(seconds=duration)

    timestamp = f"{start_time.strftime('%y%m%d_%H%M%S')}_{end_time.strftime('%H%M%S')}"

    # 新しい出力ファイル名を作成
    output_file = f"{timestamp}{combined_remaining}{common_ext}"
    
    # ffmpegコマンドを変更
    command = f"ffmpeg -f concat -safe 0 -i {filelist_path} -c copy {output_file}"
    if debug_mode:
        print(f"コマンド: {command}")
    else:
        subprocess.run(command, shell=True)
    print(f"マージ数：{len(files)}, マージファイル：{output_file}")

if __name__ == "__main__":
    main()
