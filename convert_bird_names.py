#!/usr/bin/env python3

import os
import sys
from pathlib import Path

# 英語名から学名への変換辞書
NAME_MAPPING = {
    'Black-facedBunting': 'Emberiza_spodocephala',
    'Black-headedBunting': 'Emberiza_melanocephala',
    'Black-throatedThrush': 'Turdus_atrogularis',
    'Brown-headedThrush': 'Turdus_chrysolaus',
    'Chestnut-earedBunting': 'Emberiza_fucata',
    'ChestnutBunting': 'Emberiza_rutila',
    'ChineseBlackbird': 'Turdus_mandarinus',
    'CommonReedBunting': 'Emberiza_schoeniclus',
    'DuskyThrush': 'Turdus_eunomus',
    'EyebrowedThrush': 'Turdus_obscurus',
    'Fieldfare': 'Turdus_pilaris',
    'Grey-backedThrush': 'Turdus_hortulorum',
    'Grey-cheekedThrush': 'Catharus_minimus',
    'Grey-neckedBunting': 'Emberiza_buchanani',
    'GreyBunting': 'Emberiza_variabilis',
    'IzuThrush': 'Turdus_celaenops',
    'JapaneseReedBunting': 'Emberiza_yessoensis',
    'JapaneseThrush': 'Turdus_cardis',
    'LittleBunting': 'Emberiza_pusilla',
    'MeadowBunting': 'Emberiza_cioides',
    'MistleThrush': 'Turdus_viscivorus',
    'Naumann\'sThrush': 'Turdus_naumanni',
    'Orange-headedThrush': 'Geokichla_citrina',
    'OrtolanBunting': 'Emberiza_hortulana',
    'PaleThrush': 'Turdus_pallidus',
    'Pallas\'sReedBunting': 'Emberiza_pallasi',
    'PineBunting': 'Emberiza_leucocephalos',
    'Red-headedBunting': 'Emberiza_bruniceps',
    'Redwing': 'Turdus_iliacus',
    'RusticBunting': 'Emberiza_rustica',
    'ScalyThrush': 'Zoothera_dauma',
    'SiberianThrush': 'Geokichla_sibirica',
    'SongThrush': 'Turdus_philomelos',
    'Tristram\'sBunting': 'Emberiza_tristrami',
    'White\'sThrush': 'Zoothera_aurea',
    'Yellow-breastedBunting': 'Emberiza_aureola',
    'Yellow-browedBunting': 'Emberiza_chrysophrys',
    'Yellow-throatedBunting': 'Emberiza_elegans',
    'YellowBunting': 'Emberiza_sulphurata',
    'Yellowhammer': 'Emberiza_citrinella'
}

def load_name_mapping(mapping_file=None):
    """
    マッピング辞書を読み込む。ファイルが指定されていない場合はデフォルトの辞書を使用
    
    Args:
        mapping_file (str, optional): 英名と学名のマッピングを含むファイルパス
        
    Returns:
        dict: 英名から学名へのマッピング辞書
    """
    if mapping_file is None:
        return NAME_MAPPING
        
    mapping = {}
    with open(mapping_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                en_name, scientific_name = line.split('\t')
                mapping[en_name] = scientific_name
    return mapping

def normalize_name(name):
    """
    鳥の名前を正規化する（アンダースコアの有無を吸収）
    
    Args:
        name (str): 正規化する鳥の名前
        
    Returns:
        str: 正規化された名前（アンダースコアと空白を削除）
    """
    return name.replace('_', '').replace(' ', '')

def create_directional_mapping(direction='both'):
    """
    指定された方向の変換マッピングを作成
    
    Args:
        direction (str): 変換の方向 ('en2sci': 英名→学名, 'sci2en': 学名→英名, 'both': 両方向)
        
    Returns:
        dict: 指定された方向の変換マッピング
    """
    if direction == 'sci2en':
        # 学名から英名への変換
        return {v: k for k, v in NAME_MAPPING.items()}
    elif direction == 'en2sci':
        # 英名から学名への変換
        return NAME_MAPPING.copy()
    else:  # 'both'
        # 両方向の変換
        bidirectional = NAME_MAPPING.copy()
        reverse_mapping = {v: k for k, v in NAME_MAPPING.items()}
        bidirectional.update(reverse_mapping)
        return bidirectional

def escape_name(name):
    """
    シェルコマンド用にファイル名をエスケープ
    """
    return name.replace("'", "'\\''")

def rename_directories(base_dir, mapping_file=None, direction='both'):
    """
    ディレクトリ名を英名⇔学名で変換し、mvコマンドの形式で出力
    
    Args:
        base_dir (str): 処理対象のベースディレクトリ
        mapping_file (str, optional): マッピングファイルのパス
        direction (str): 変換の方向 ('en2sci', 'sci2en', 'both')
    """
    mapping = create_directional_mapping(direction)
    base_path = Path(base_dir)
    
    # ディレクトリ一覧を取得してソート
    dirs = sorted([d for d in base_path.iterdir() if d.is_dir()])
    
    for dir_path in dirs:
        old_name = dir_path.name
        
        # 学名形式（アンダースコア含む）かどうかを判定
        is_scientific = '_' in old_name
        
        # 方向に応じて処理をスキップ
        if direction == 'en2sci' and is_scientific:
            continue
        if direction == 'sci2en' and not is_scientific:
            continue
            
        # 正規化して検索
        normalized_old_name = normalize_name(old_name)
        found = False
        
        # マッピングを探索
        for k, v in mapping.items():
            if normalize_name(k) == normalized_old_name:
                new_name = v
                found = True
                break
            elif direction == 'both' and normalize_name(v) == normalized_old_name:
                new_name = k
                found = True
                break
        
        if found:
            # ファイル名のエスケープ処理
            escaped_old = escape_name(old_name)
            escaped_new = escape_name(new_name)
            print(f"mv '{escaped_old}' '{escaped_new}'")
        else:
            print(f"# Warning: No mapping found for {old_name}", file=sys.stderr)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='鳥の英名ディレクトリを学名に変換')
    parser.add_argument('directory', help='処理対象のディレクトリ')
    parser.add_argument('-m', '--mapping', help='英名と学名のマッピングファイル')
    parser.add_argument('-d', '--direction', choices=['en2sci', 'sci2en', 'both'],
                      default='both', help='変換の方向 (デフォルト: both)')
    
    args = parser.parse_args()
    
    # 標準出力をバッファリングなしモードに設定
    if sys.stdout.isatty():
        sys.stdout.reconfigure(line_buffering=True)
    
    rename_directories(args.directory, args.mapping, args.direction)

if __name__ == "__main__":
    main() 