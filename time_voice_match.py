#!/usr/bin/env python3
# coding: utf-8

import argparse
import pandas as pd
import sys

# グローバル定数を定義
DECIMAL_PLACES = 2

def parse_arguments():
    parser = argparse.ArgumentParser(description='音声データと時間データをマッチングするスクリプト')
    parser.add_argument('file1', type=str, help='最初のデータファイル')
    parser.add_argument('file2', type=str, help='2番目のデータファイル')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグ情報を出力する')
    parser.add_argument('--column_name_time', '-t', default='Begin Clock Time', help='時間データの列名')
    parser.add_argument('--column_name_voice', '-c', default='type', help='音声データの列名')
    parser.add_argument('--allowed_time_diff', '-a', type=int, default=10, help='時間の許容誤差（秒単位）')
    parser.add_argument('--show_diff', '-s', action='store_true', help='不一致のデータを表示する')
    parser.add_argument('--separator', '-sep', default='\t', help='データの区切り文字（デフォルトはタブ）')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細な不一致のデータを表示する')
    parser.add_argument('--ignore-type', '-i', action='store_true', help='音声データの種類を無視して時刻だけを検証する')
    return parser.parse_args()

def read_data(file):
    try:
        data = pd.read_csv(file, sep=args.separator)
        if args.column_name_time not in data.columns or args.column_name_voice not in data.columns:
            raise ValueError(f"指定された列名が存在しません: {args.column_name_time}, {args.column_name_voice}")
        
        # "date"列が存在する場合、その情報を使用して時間を解析
        if 'date' in data.columns:
            data[args.column_name_time] = pd.to_datetime(
                data['date'] + ' ' + data[args.column_name_time], 
                format='%Y-%m-%d %H:%M:%S.%f'
            )
        else:
            data[args.column_name_time] = pd.to_datetime(
                data[args.column_name_time], 
                format='%H:%M:%S.%f'
            )
        
        return data
    except Exception as e:
        print(f"データの読み込みに失敗しました: {e}")
        sys.exit(1)

def compare_data(data1, data2):
    matches = 0
    mismatches_file1_only = 0
    mismatches_file2_only = 0
    results = []

    for _, row1 in data1.iterrows():
        time1 = row1[args.column_name_time]
        voice1 = row1[args.column_name_voice]
        matched = False

        for _, row2 in data2.iterrows():
            time2 = row2[args.column_name_time]
            voice2 = row2[args.column_name_voice]

            time_diff = (time1 - time2).total_seconds()

            if abs(time_diff) <= args.allowed_time_diff and (args.ignore_type or voice1 == voice2):
                matches += 1
                matched = True
                if args.show_diff:
                    sign = "+" if time_diff > 0 else "-"
                    results.append(f"= {time1} {voice1} | {time2} {voice2} | 時間差: {sign}{abs(time_diff):.{DECIMAL_PLACES}f}秒")
                break

        if not matched:
            mismatches_file1_only += 1
            if args.show_diff:
                results.append(f"- {time1} {voice1} (file1のみ)")

    for _, row2 in data2.iterrows():
        time2 = row2[args.column_name_time]
        voice2 = row2[args.column_name_voice]

        if not any(abs((row1[args.column_name_time] - time2).total_seconds()) <= args.allowed_time_diff and (args.ignore_type or row1[args.column_name_voice] == voice2) for _, row1 in data1.iterrows()):
            mismatches_file2_only += 1
            if args.show_diff and args.verbose:
                results.append(f"+ {time2} {voice2} (file2のみ)")

    if args.show_diff:
        for result in results:
            print(result)

    print(f"一致数: {matches}")
    if args.verbose:
        print(f"file1のみの不一致数: {mismatches_file1_only}")
        print(f"file2のみの不一致数: {mismatches_file2_only}")
    else:
        print(f"不一致数: {mismatches_file1_only + mismatches_file2_only}")

def main():
    global args
    args = parse_arguments()
    data1 = read_data(args.file1)
    data2 = read_data(args.file2)

    compare_data(data1, data2)

if __name__ == '__main__':
    main()
