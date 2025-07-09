#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import subprocess
import logging
from datetime import datetime, timedelta

# ロギング設定
LOG_DIR = "/var/data/sound-command"
LOG_FILE = os.path.join(LOG_DIR, "divide_1_hour.log")

def setup_logging():
    # ログディレクトリが存在しない場合は作成
    if not os.path.exists(LOG_DIR):
        try:
            os.makedirs(LOG_DIR)
        except Exception as e:
            print(f"警告: ログディレクトリの作成に失敗しました: {e}")
            print(f"カレントディレクトリにログを出力します。")
            global LOG_FILE
            LOG_FILE = "divide_1_hour.log"
    
    # ロガーの設定
    logger = logging.getLogger('divide_1_hour')
    logger.setLevel(logging.INFO)
    
    # ファイルハンドラを追加
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setLevel(logging.INFO)
    
    # コンソールハンドラも追加
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.ERROR)  # エラーのみコンソールに表示
    
    # フォーマッタを設定
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # ハンドラをロガーに追加
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def usage():
    print("使用方法: python3 divide_1_hour.py [--debug|-d] [--dry-run|-dry] [--force|-f] [--check|-c] [--split-by-time|-t] [--separate-channel|-sc] [--help|-h] 入力ファイル")
    print("  -S, --split-by-hour: 時刻を毎時0分0秒に分割する（デフォルト・省略可）")
    print("  -t, --split-by-time: 先頭から1時間毎に分割する")
    print("  -sc, --separate-channel: 音源をチャンネル毎に分割する（デフォルトはモノラル化）")
    print("  -d, --debug: デバッグモード")
    print("  -dry, --dry-run: 実際にファイルを生成せず、何が行われるかを表示するだけのモード")
    print("  -f, --force: 既存のファイルを強制的に上書きする（デフォルトはスキップ）")
    print("  -c, --check: 生成されたファイルの時間が666形式と一致するか検証する")
    print("  -h, --help: ヘルプ")
    print("入力ファイルは666形式のみ受け付けます。")
    print("注意: デフォルトでは毎時0分0秒に分割する(-S)モードが適用されるため、-Sオプションは省略可能です。")
    sys.exit(1)

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffprobe", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        logger.error("ffmpeg/ffprobeがインストールされていません。インストールしてください。")
        print("エラー: ffmpeg/ffprobeがインストールされていません。インストールしてください。")
        sys.exit(1)

def parse_666_filename(filename):
    # 修正済みの正規表現パターン: その他情報は省略可能
    pattern = r"(\d{6})_(\d{6})_(\d{6})(.*)\.(.*)"
    match = re.match(pattern, filename)
    if not match:
        logger.error(f"入力ファイル '{filename}' は666形式ではありません。")
        print(f"エラー: 入力ファイル '{filename}' は666形式ではありません。")
        sys.exit(1)
    
    date, start_time, end_time, other, ext = match.groups()
    start_datetime = datetime.strptime(f"20{date}_{start_time}", "%Y%m%d_%H%M%S")
    # end_timeがstart_timeより小さい場合、end_timeの日付を1日進める
    end_datetime = datetime.strptime(f"20{date}_{end_time}", "%Y%m%d_%H%M%S")
    if end_time < start_time:
        end_datetime = end_datetime + timedelta(days=1)
    
    if debug_mode:
        logger.debug(f"修正後のend_datetime: {end_datetime}")
    
    return start_datetime, end_datetime, other, ext

def get_audio_duration(filepath):
    """ffprobeを使って音声ファイルの長さを秒単位で取得"""
    try:
        cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filepath]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            duration = float(result.stdout.strip())
            return duration
        else:
            logger.error(f"ファイル '{filepath}' の長さ取得に失敗しました: {result.stderr}")
            return None
    except Exception as e:
        logger.error(f"ファイル '{filepath}' の長さ取得に失敗しました: {str(e)}")
        return None

def check_file_duration(filepath, expected_duration, tolerance=1.0):
    """ファイルの実際の長さと期待される長さを比較"""
    actual_duration = get_audio_duration(filepath)
    if actual_duration is None:
        return False, None
    
    # 許容範囲内かチェック
    duration_diff = abs(actual_duration - expected_duration)
    is_valid = duration_diff <= tolerance
    
    return is_valid, actual_duration

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
        logger.error(f"音声チャンネル数の取得に失敗しました: {e}")
        print(f"エラー: 音声チャンネル数の取得に失敗しました: {e}")
        return 1  # デフォルトは1チャンネルとして扱う

def divide_file(input_file, start_time, duration, output_file, separate_channels=False, force=False, check=False):
    # 出力ファイルが存在し、かつforce=Falseの場合はスキップ
    if os.path.exists(output_file) and not force:
        logger.info(f"skipped: {output_file}")
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
            logger.debug(f"cmd: {cmd}")
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"created: {output_file}")
            
            # チェックモードが有効の場合、ファイルの長さを検証
            if check:
                # 期待される時間（秒）
                expected_duration = float(duration)
                is_valid, actual_duration = check_file_duration(output_file, expected_duration)
                
                if is_valid:
                    logger.info(f"duration check passed: {output_file}, expected: {expected_duration:.3f}s, actual: {actual_duration:.3f}s")
                else:
                    if actual_duration is not None:
                        logger.warning(f"duration check failed: {output_file}, expected: {expected_duration:.3f}s, actual: {actual_duration:.3f}s, difference: {abs(expected_duration - actual_duration):.3f}s")
                    else:
                        logger.warning(f"duration check failed: {output_file}, expected: {expected_duration:.3f}s, actual: unknown")
            
            return True
        except Exception as e:
            logger.error(f"ファイル '{output_file}' の作成に失敗しました: {str(e)}")
            print(f"エラー: ファイル '{output_file}' の作成に失敗しました: {str(e)}")
            return False
    else:
        # チャンネル数を取得
        channels = get_audio_channels(input_file)
        if debug_mode:
            logger.debug(f"チャンネル数: {channels}")
        
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
                logger.debug(f"cmd: {cmd}")
            
            try:
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                logger.info(f"created: {output_file}")
                
                # チェックモードが有効の場合、ファイルの長さを検証
                if check:
                    expected_duration = float(duration)
                    is_valid, actual_duration = check_file_duration(output_file, expected_duration)
                    
                    if is_valid:
                        logger.info(f"duration check passed: {output_file}, expected: {expected_duration:.3f}s, actual: {actual_duration:.3f}s")
                    else:
                        if actual_duration is not None:
                            logger.warning(f"duration check failed: {output_file}, expected: {expected_duration:.3f}s, actual: {actual_duration:.3f}s, difference: {abs(expected_duration - actual_duration):.3f}s")
                        else:
                            logger.warning(f"duration check failed: {output_file}, expected: {expected_duration:.3f}s, actual: unknown")
                
                return True
            except Exception as e:
                logger.error(f"ファイル '{output_file}' の作成に失敗しました: {str(e)}")
                print(f"エラー: ファイル '{output_file}' の作成に失敗しました: {str(e)}")
                return False
        else:
            # 複数チャンネルの場合、各チャンネルごとに分割
            base_name, ext = os.path.splitext(output_file)
            any_created = False
            for ch in range(1, channels + 1):
                ch_output = f"{base_name}-ch-{ch}{ext}"
                # チャンネル別ファイルが存在する場合はスキップ
                if os.path.exists(ch_output) and not force:
                    logger.info(f"skipped: {ch_output}")
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
                    logger.debug(f"cmd: {cmd}")
                
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    logger.info(f"created: {ch_output}")
                    print(f"created: {ch_output}")
                    
                    # チェックモードが有効の場合、ファイルの長さを検証
                    if check:
                        expected_duration = float(duration)
                        is_valid, actual_duration = check_file_duration(ch_output, expected_duration)
                        
                        if is_valid:
                            logger.info(f"duration check passed: {ch_output}, expected: {expected_duration:.3f}s, actual: {actual_duration:.3f}s")
                        else:
                            if actual_duration is not None:
                                logger.warning(f"duration check failed: {ch_output}, expected: {expected_duration:.3f}s, actual: {actual_duration:.3f}s, difference: {abs(expected_duration - actual_duration):.3f}s")
                            else:
                                logger.warning(f"duration check failed: {ch_output}, expected: {expected_duration:.3f}s, actual: unknown")
                    
                    any_created = True
                except Exception as e:
                    logger.error(f"ファイル '{ch_output}' の作成に失敗しました: {str(e)}")
                    print(f"エラー: ファイル '{ch_output}' の作成に失敗しました: {str(e)}")
            
            return any_created

def is_option(arg):
    """引数がオプションかどうかを判定する"""
    return arg.startswith('-')

def is_audio_file(filename):
    """ファイルが音声ファイルかどうかを判定する"""
    return filename.lower().endswith(('.wav', '.mp3', '.aiff', '.flac', '.ogg'))

def main():
    global debug_mode, logger
    
    # ロギングのセットアップ
    logger = setup_logging()
    logger.info("divide_1_hour.py を開始しました")
    
    if len(sys.argv) < 2:
        usage()
    
    check_ffmpeg()
    
    mode = "-S"  # デフォルトのモードを設定
    debug_mode = False
    dry_run = False
    force = False
    check_mode = False
    separate_channels = False
    input_file = None  # 入力ファイルを初期化
    
    i = 1
    # 引数を解析
    while i < len(sys.argv):
        arg = sys.argv[i]
        if debug_mode:
            logger.debug(f"arg: {arg}")

        if arg in ["-h", "--help"]:
            usage()
            sys.exit(0)  # ここでプログラムを終了
        elif arg in ["-d", "--debug"]:
            debug_mode = True
            logger.setLevel(logging.DEBUG)
            logger.debug("デバッグモードが有効になりました")
        elif arg in ["-dry", "--dry-run"]:
            dry_run = True
            logger.info("ドライランモードが有効になりました")
        elif arg in ["-f", "--force"]:
            force = True
            logger.info("強制上書きモードが有効になりました")
        elif arg in ["-c", "--check"]:
            check_mode = True
            logger.info("チェックモードが有効になりました")
        elif arg in ["-S", "--split-by-hour"]:
            mode = "-S"
            logger.info("毎時0分0秒に分割するモードが有効になりました")
        elif arg in ["-t", "--split-by-time"]:
            mode = "-t"
            logger.info("録音開始時刻から1時間毎に分割するモードが有効になりました")
        elif arg in ["-sc", "--separate-channel"]:
            separate_channels = True
            logger.info("チャンネル分割モードが有効になりました")
        elif not is_option(arg):
            # オプションでない場合は入力ファイルと判断
            input_file = arg
            logger.info(f"入力ファイル: {input_file}")
        else:
            logger.error(f"不明なオプション '{arg}'")
            print(f"エラー: 不明なオプション '{arg}'")
            usage()
            sys.exit(1)
        i += 1
    
    # 入力ファイルの存在確認
    if input_file is None:
        logger.error("入力ファイルが指定されていません。")
        print("エラー: 入力ファイルが指定されていません。")
        usage()
        sys.exit(1)
    if not debug_mode and not dry_run and not os.path.exists(input_file):
        logger.error(f"入力ファイル '{input_file}' が見つかりません。")
        print(f"エラー: 入力ファイル '{input_file}' が見つかりません。")
        sys.exit(1)
    
    file_body_with_ext = os.path.basename(input_file)
    if debug_mode:
        logger.debug(f"file_body_with_ext: {file_body_with_ext}")
    
    try:
        start_datetime, end_datetime, other, ext = parse_666_filename(file_body_with_ext)
    except Exception as e:
        logger.error(f"入力ファイル '{input_file}' の解析に失敗しました: {str(e)}")
        print(f"エラー: 入力ファイル '{input_file}' の解析に失敗しました: {str(e)}")
        print("入力ファイルは666形式（YYMMDD_HHMMSS_HHMMSS）である必要があります。")
        sys.exit(1)
    
    if debug_mode:
        logger.debug(f"デバッグ情報:")
        logger.debug(f"  開始日時: {start_datetime}")
        logger.debug(f"  終了日時: {end_datetime}")
        logger.debug(f"  その他情報: {other}")
        logger.debug(f"  拡張子: {ext}")
        logger.debug(f"  入力ファイル: {input_file}")
        logger.debug(f"  モード: {mode}")
        logger.debug(f"  チャンネル分割: {separate_channels}")
        logger.debug(f"  ドライラン: {dry_run}")
        logger.debug(f"  強制上書き: {force}")
        logger.debug(f"  チェックモード: {check_mode}")
    
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
                    logger.info(f"dry-run: skipped: {output_file}")
                    print(f"dry-run: skipped: {output_file}")
                else:
                    logger.info(f"dry-run: {output_file}")
                    print(f"dry-run: {output_file}")
            else:
                channels = 2  # ドライランモードでは仮に2チャンネルとして表示
                base_name, ext_name = os.path.splitext(output_file)
                for ch in range(1, channels + 1):
                    ch_output = f"{base_name}-ch-{ch}{ext_name}"
                    file_exists = os.path.exists(ch_output)
                    if file_exists and not force:
                        logger.info(f"dry-run: skipped: {ch_output}")
                        print(f"dry-run: skipped: {ch_output}")
                    else:
                        logger.info(f"dry-run: {ch_output}")
                        print(f"dry-run: {ch_output}")
        elif not debug_mode:
            file_created = divide_file(input_file, f"{start_time:.3f}", f"{duration:.3f}", output_file, separate_channels, force, check_mode)
            if file_created and not separate_channels:
                print(f"created: {output_file}")
        
        current_time = next_time
        chunk_number += 1
    
    logger.info("divide_1_hour.py を終了しました")

if __name__ == "__main__":
    main()
