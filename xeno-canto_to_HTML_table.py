#!/usr/bin/env python3

__version__ = 'v0.0.2'
__last_updated__ = '2025-01-16 13:11:55'

import argparse
import json
import os
from pathlib import Path
import sys

# グローバル変数の定義
args = None

# 定数の定義
SONO_SIZE = 'small'  # ソナグラムのサイズ（'small', 'med', 'large', 'full'）
AUDIO_ROOT = '../dataset/audio'  # オーディオファイルのルートディレクトリ（HTMLからの相対パス）
METADATA_ROOT = './dataset/metadata'  # メタデータのルートディレクトリ

def parse_arguments():
    parser = argparse.ArgumentParser(description='xeno-cantoのデータからHTML表を生成する')
    parser.add_argument('-bn', '--bird_name', type=str, default='all',
                       help='学名 (例: "Pale Thrush")')
    parser.add_argument('-od', '--output_dir', type=str, default='./html',
                       help='出力ディレクトリ (デフォルト: ./html)')
    parser.add_argument('-fi', '--file_items', type=str, default='',
                       help='メタデータの表示項目ファイル（指定がなければ全項目を表示）')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='デバッグモードを有効にする')
    return parser.parse_args()

def load_metadata(bird_name, debug=False):
    """JSONファイルからメタデータを読み込む"""
    recordings = []
    metadata_root = Path(METADATA_ROOT)
    
    if not metadata_root.exists():
        print(f"Error: Metadata root directory not found: {metadata_root}")
        sys.exit(1)
    
    if bird_name == 'all':
        # メタデータディレクトリ内のpage*.jsonファイルを再帰的に検索
        metadata_files = list(metadata_root.rglob('page*.json'))
        if not metadata_files:
            print(f"Error: No page*.json files found in {metadata_root}")
            sys.exit(1)
    else:
        # 特定の種のJSONファイルのみ処理
        formatted_name = bird_name.replace(' ', '') + 'type_call'
        species_dir = metadata_root / formatted_name
        if not species_dir.exists():
            print(f"Error: Species directory not found: {species_dir}")
            sys.exit(1)
        
        metadata_files = list(species_dir.glob('page*.json'))
        if not metadata_files:
            print(f"Error: No page*.json files found for {bird_name}")
            sys.exit(1)
    
    # 各JSONファイルからデータを読み込む
    for json_file in metadata_files:
        if debug:
            print(f"Reading metadata from: {json_file}")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'recordings' in data:
                recordings.extend(data['recordings'])
    
    if debug:
        print(f"Found {len(recordings)} recordings in total")
    
    return recordings

def generate_html_table(recordings, items, output_dir):
    """HTMLテーブルを生成"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Xeno-canto Recordings</title>
        <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid black; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            img { max-width: 300px; }
            audio { width: 300px; }
        </style>
    </head>
    <body>
        <table>
            <tr>
    """
    
    # ヘッダー行を生成
    html += ''.join([f"<th>{item}</th>" for item in items])
    html += "<th>Sonogram</th><th>Audio</th></tr>"
    
    # データ行を生成
    for rec in recordings:
        html += "<tr>"
        html += ''.join([f"<td>{rec.get(item, '')}</td>" for item in items])
        
        audio_path = f"{AUDIO_ROOT}/{rec['en'].replace(' ', '')}/{rec['id']}.mp3"
        sono_url = "https:" + rec['sono'][SONO_SIZE]
        
        html += f"""
                <td><img src="{sono_url}" alt="Sonogram {rec['id']}"></td>
                <td><audio controls><source src="{audio_path}" type="audio/mpeg">Your browser does not support the audio element.</audio></td>
            </tr>
        """
    
    html += "</table></body></html>"
    
    # 出力ファイル名の決定
    if args.bird_name == 'all':
        output_file = output_dir / "all_table.html"
    else:
        output_file = output_dir / f"{recordings[0]['gen']}_{recordings[0]['sp']}_table.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file

def main():
    global args  # グローバル変数として宣言
    args = parse_arguments()
    
    if args.debug:
        print(f"Bird name: {args.bird_name}")
        print(f"Output directory: {args.output_dir}")
    
    # メタデータを読み込む
    recordings = load_metadata(args.bird_name, args.debug)
    if not recordings:
        print(f"No recordings found for {args.bird_name}")
        sys.exit(1)
    
    # 利用可能な項目を保存
    with open('items.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(recordings[0].keys()))
    
    # 表示項目の読み込み
    if args.file_items:
        with open(args.file_items, 'r', encoding='utf-8') as f:
            items = f.read().splitlines()
    else:
        items = list(recordings[0].keys())
    
    # HTMLテーブルを生成
    output_file = generate_html_table(recordings, items, args.output_dir)
    print(f"HTML table generated: {output_file}")

if __name__ == "__main__":
    main()
