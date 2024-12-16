#!/usr/bin/env python3
# coding: utf-8

import argparse
import pandas as pd
from datetime import datetime
import re
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='アノテーションしたデータにエポックを追加するスクリプト',
                                   epilog='使用例: ls 2*txt | xargs -I@ python ../../add_epoch.py -i @ -o epoch/@')
    parser.add_argument('--input', '-i', help='データのファイル名（デフォルトは標準入力とする．）')
    parser.add_argument('--output', '-o', help='データのファイル名（デフォルトは標準出力とする．）')
    parser.add_argument('--separator', '-s', default='\t', help='データの区切り文字（デフォルトはタブ）')
    parser.add_argument('--add-date', '-ad', help='日付を追加する（指定するのは６文字で年月日を表す．）')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグモードを有効にする')
    return parser.parse_args()

def extract_date_from_filename(filename):
    match = re.search(r'(\d{6})_\d{6}', filename)
    if match:
        return match.group(1)
    return None

def main():
    args = parse_arguments()

    # 入力デ���タの読み込み
    if args.input:
        data = pd.read_csv(args.input, sep=args.separator)
    else:
        data = pd.read_csv(sys.stdin, sep=args.separator)

    # フバッグ: データフレームの列名を表示
    if args.debug:
        print("データフレームの列名:", data.columns)

    # ファイル名から日付を抽出
    if args.add_date:
        date_str = args.add_date
    elif args.input:  # args.inputがNoneでないことを確認
        date_str = extract_date_from_filename(args.input)
        if not date_str:
            print("エラー: 日付を抽出できませんでした。-adオプションを使用してください。")
            sys.exit(1)
    else:
        print("エラー: 入力ファイル名が指定されていません。-adオプションを使用してください。")
        sys.exit(1)

    # 日付のフォーマット変換
    date_formatted = datetime.strptime(date_str, '%y%m%d').strftime('%Y-%m-%d')
    if args.debug:
        print("日付のフォーマット変換:", date_formatted)

    # 'Begin Clock Time' のインデックスを取得
    begin_time_idx = data.columns.get_loc('Begin Clock Time')

    # 日付の追加
    data.insert(begin_time_idx, 'date', date_formatted)

    # エポック秒の追加
    if 'Begin Clock Time' in data.columns:
        # 日付と時間を結合してエポック秒を計算
        data['epoch'] = pd.to_datetime(data['date'] + ' ' + data['Begin Clock Time'], format='%Y-%m-%d %H:%M:%S.%f').apply(lambda x: x.timestamp())
        # エポック秒を 'Begin Clock Time' の後に挿入
        data.insert(begin_time_idx + 2, 'epoch', data.pop('epoch'))
    else:
        print("エラー: 'Begin Clock Time' 列が存在しません。")
        sys.exit(1)

    # デバッグモード
    if args.debug:
        print(data.head())

    # 出力
    if args.output:
        data.to_csv(args.output, sep=args.separator, index=False)
    else:
        data.to_csv(sys.stdout, sep=args.separator, index=False)

if __name__ == '__main__':
    main()
