#!/usr/bin/env python3

__version__ = 'v0.0.2'
__last_updated__ = '2025-01-16 13:11:55'

import argparse
import json
import os
from pathlib import Path
import sys
import requests

# グローバル変数の定義
args = None

# 定数の定義
SONO_SIZE = 'small'  # ソナグラムのサイズ（'small', 'med', 'large', 'full'）
AUDIO_ROOT = '../dataset/audio'  # オーディオファイルのルートディレクトリ（HTMLからの相対パス）
SONO_ROOT = '../dataset/spectrogram'  # スペクトログラムのルートディレクトリ（HTMLからの相対パス）
METADATA_DIR = './dataset/metadata'  # メタデータのルートディレクトリ
SPECTROGRAM_DIR = "./dataset/spectrogram"  # スペクトログラムの出力ディレクトリ
HTML_DIR = "./html"  # HTMLファイルの出力ディレクトリ

def parse_arguments():
    parser = argparse.ArgumentParser(description='xeno-cantoのデータからHTML表を生成する')
    parser.add_argument('-sn', '--science_name', type=str, default='all',
                       help='学名 (例: "Emberiza aureola")')
    parser.add_argument('-fi', '--file_items', type=str, default='',
                       help='メタデータの表示項目ファイル（指定がなければ全項目を表示）')
    parser.add_argument('-d', '--debug', action='store_true',
                       help='デバッグモードを有効にする')
    return parser.parse_args()

def load_metadata(science_name, debug=False):
    """JSONファイルからメタデータを読み込む"""
    recordings = []
    metadata_root = Path(METADATA_DIR)
    
    if not metadata_root.exists():
        print(f"Error: Metadata root directory not found: {metadata_root}")
        sys.exit(1)
    
    if science_name == 'all':
        metadata_files = list(metadata_root.rglob('page*.json'))
        if not metadata_files:
            print(f"Error: No page*.json files found in {metadata_root}")
            sys.exit(1)
    else:
        species_dir = get_species_dir(metadata_root, science_name)
        if not species_dir.exists():
            print(f"Error: Species directory not found: {species_dir}")
            sys.exit(1)
        
        metadata_files = list(species_dir.glob('page*.json'))
        if not metadata_files:
            print(f"Error: No page*.json files found for {science_name}")
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

def generate_html_table(recordings, items):
    """HTMLテーブルを生成"""
    output_dir = Path(HTML_DIR)
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
        
        # 学名を使用してパスを生成（例：'Emberiza aureola' -> 'Emberiza_aureola'）
        scientific_name = f"{rec['gen']}_{rec['sp']}"
        
        audio_path = f"{AUDIO_ROOT}/{scientific_name}/{rec['id']}.mp3"
        sono_path = f"{SONO_ROOT}/{scientific_name}/{rec['id']}.png"
        
        html += f"""
                <td><img src="{sono_path}" alt="Sonogram {rec['id']}"></td>
                <td><audio controls><source src="{audio_path}" type="audio/mpeg">Your browser does not support the audio element.</audio></td>
            </tr>
        """
    
    html += "</table></body></html>"
    
    # 出力ファイル名の決定
    if args.science_name == 'all':
        output_file = output_dir / "all.html"
    else:
        dir_name = get_recording_dir(recordings)
        output_file = output_dir / f"{dir_name}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return output_file

def download_spectrograms(metadata_dir, science_name):
    """メタデータから指定された鳥のスペクトログラムをダウンロードして保存する"""
    Path(SPECTROGRAM_DIR).mkdir(parents=True, exist_ok=True)
    
    species_dir = get_species_dir(metadata_dir, science_name)
    
    if args.debug:
        print(f"Processing species: {format_science_name(science_name)}")
        print(f"Species directory: {species_dir}")
    
    if not species_dir.exists():
        print(f"Error: Species directory not found: {species_dir}")
        return
    
    # 各ページのJSONファイルを処理
    for json_file in species_dir.glob('*.json'):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if 'recordings' not in data:
            continue
            
        # 最初のレコーディングから英名を取得してディレクトリ名を作成
        if not data['recordings']:
            continue
            
        # 学名を取得してディレクトリ名を作成
        dir_name = get_recording_dir(data['recordings'])
        if dir_name:
            species_output_dir = Path(SPECTROGRAM_DIR) / dir_name
            species_output_dir.mkdir(exist_ok=True)
            
            # 各レコーディングのスペクトログラムをダウンロード
            for recording in data['recordings']:
                if 'sono' not in recording or 'small' not in recording['sono']:
                    continue
                    
                sono_url = f"https:{recording['sono']['small']}"  # ダウンロード元のURL
                sono_path = species_output_dir / f"{recording['id']}.png"  # 保存先のパス
                
                # ファイルが存在しない場合のみダウンロード
                if not sono_path.exists():
                    try:
                        response = requests.get(sono_url)
                        response.raise_for_status()
                        
                        with open(sono_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Downloaded: {sono_path}")
                    except Exception as e:
                        print(f"Error downloading {sono_url}: {e}")

def format_science_name(science_name):
    """
    学名をファイルシステム用にフォーマット
    'Emberiza_buchanani'や'Emberiza buchanani'など、
    異なる形式の入力を受け付けて統一された形式に変換
    """
    # アンダースコアをスペースに変換してから、余分なスペースを削除
    normalized = science_name.replace('_', ' ').strip()
    # 連続するスペースを1つに
    normalized = ' '.join(normalized.split())
    # 最終的にスペースをアンダースコアに変換
    return normalized.replace(' ', '_')

def get_species_dir(base_dir, science_name):
    """種のディレクトリパスを取得"""
    return Path(base_dir) / format_science_name(science_name)

def get_recording_dir(recordings):
    """レコーディングから種のディレクトリ名を取得"""
    if not recordings:
        return None
    return f"{recordings[0]['gen']}_{recordings[0]['sp']}"

def main():
    global args
    args = parse_arguments()
    
    if args.debug:
        print(f"Scientific name: {args.science_name}")
    
    # メタデータを読み込む
    recordings = load_metadata(args.science_name, args.debug)
    if not recordings:
        print(f"No recordings found for {args.science_name}")
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
    output_file = generate_html_table(recordings, items)
    print(f"HTML table generated: {output_file}")
    
    # スペクトログラムのダウンロード
    download_spectrograms(METADATA_DIR, args.science_name)

if __name__ == "__main__":
    main()
