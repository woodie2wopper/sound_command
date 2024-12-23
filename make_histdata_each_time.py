#!/usr/bin/env python3
# coding: utf-8

import argparse
import pandas as pd
import os

def parse_arguments():
    parser = argparse.ArgumentParser(description='時間毎のヒストグラムデータを生成するスクリプト')
    parser.add_argument('--input', '-i', required=True, help='データのファイル名（タブ区切りファイルを前提としている）')
    parser.add_argument('--output', '-o', help='ヒストグラムのファイル名（デフォルトでは"入力ファイルのボディー_hist_each_time.csv"）')
    parser.add_argument('--separator', '-s', default='\t', help='データの区切り文字（デフォルトはタブ）')
    parser.add_argument('--type', '-t', choices=['all', 'zeep', 'call', 'top5'], default='all', help='指定のtypeのヒストグラムを作成する')
    parser.add_argument('--start_time', '-st', default='18:00', help='ヒストグラムの開始時間（デフォルトは18:00）')
    parser.add_argument('--end_time', '-et', default='06:00', help='ヒストグラムの終了時間（デフォルトは06:00）')
    parser.add_argument('--bin_size', '-b', type=int, default=60, help='ヒストグラムのビンサイズ（単位は分でデフォルトは60分）')
    parser.add_argument('--title', '-ti', default='Histogram of data', help='ヒストグラムのタイトル')
    parser.add_argument('--debug', '-d', action='store_true', help='デバッグモードを有効にする')
    return parser.parse_args()

def filter_data_by_type(data, data_type):
    if data_type == 'all':
        return data
    elif data_type == 'top5':
        if 'type' in data.columns:
            data['type'] = data['type'].str.strip()
            type_counts = data['type'].value_counts().nlargest(5).index
            return data[data['type'].isin(type_counts)]
        else:
            print("データに'type'列が存在しません。")
            return pd.DataFrame()  # 空のデータフレームを返す
    else:
        return data[data['type'].str.contains(data_type, na=False)]

def create_histogram_data(data):
    data['Begin Clock Time'] = pd.to_datetime(data['Begin Clock Time'], format='%H:%M:%S.%f')
    start_time = pd.to_datetime(args.start_time, format='%H:%M').time()
    end_time = pd.to_datetime(args.end_time, format='%H:%M').time()

    # フィルタリング
    if start_time < end_time:
        data = data[(data['Begin Clock Time'].dt.time >= start_time) & (data['Begin Clock Time'].dt.time <= end_time)]
    else:
        data = data[(data['Begin Clock Time'].dt.time >= start_time) | (data['Begin Clock Time'].dt.time <= end_time)]

    # データが空でないか確認
    if data.empty:
        print("指定された条件に一致するデータがありません。")
        return None

    # 時間毎のtype別個数を集計
    hourly_counts = data.groupby([data['Begin Clock Time'].dt.hour, 'type']).size().unstack(fill_value=0)
    # 18時から翌6時までの全時間帯を含むインデックスを作成
    start_hour = pd.to_datetime(args.start_time, format='%H:%M').hour
    end_hour = pd.to_datetime(args.end_time, format='%H:%M').hour
    
    if start_hour < end_hour:
        all_hours = list(range(start_hour, end_hour + 1))
    else:
        all_hours = list(range(start_hour, 24)) + list(range(0, end_hour + 1))
        
    # 存在しない時間帯のデータを0で補完
    hourly_counts = hourly_counts.reindex(all_hours, fill_value=0)

    return hourly_counts

def main():
    global args
    args = parse_arguments()
    data = pd.read_csv(args.input, sep=args.separator)
    filtered_data = filter_data_by_type(data, args.type)
    
    # 出力ファイル名が指定されていない場合、inputファイルに_hist_each_time.csvを追加
    if not args.output:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}_hist_each_time.csv"
    
    # ヒストグラムデータを生成
    histogram_data = create_histogram_data(filtered_data)
    
    # ヒストグラムデータを出力
    if histogram_data is not None and not histogram_data.empty:
        if args.debug:
            print(histogram_data)  # デバッグ用に出力を確認
        histogram_data.to_csv(args.output)
        print(f"ヒストグラムデータを{args.output}に出力しました。")
    else:
        print("指定された条件に一致するデータがありません。")

if __name__ == '__main__':
    main()
