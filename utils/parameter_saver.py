__version__ = 'v0.0.2'
__last_updated__ = '2024-12-27 11:47:39'

import os
import sys
import random
import string

def save_parameters(args, output_file=None, version=None, last_updated=None):
    """
    コマンドライン引数とバージョン情報をファイルに保存する関数
    
    Parameters
    ----------
    args : argparse.Namespace
        コマンドライン引数
    output_file : str, optional
        出力ファイルのパス。Noneの場合は入力ファイル名から自動生成
    version : str, optional
        バージョン情報
    last_updated : str, optional
        最終更新日時
    """
    # 出力ファイル名を生成
    if output_file:
        param_file = os.path.splitext(output_file)[0] + '_param.txt'
    else:
        base_name = os.path.splitext(os.path.basename(args.input_file))[0]
        param_file = f"{base_name}_param.txt"
    
    # パラメータを出力
    with open(param_file, 'w', encoding='utf-8') as f:
        f.write("Parameters:\n")
        f.write(f"Command: {os.path.basename(sys.argv[0])}\n")
        if version:
            f.write(f"Version: {version}\n")
        if last_updated:
            f.write(f"Last Updated: {last_updated}\n")
        f.write("\n")
        for arg, value in sorted(vars(args).items()):
            f.write(f"{arg}: {value}\n") 

def generate_toriR_hash_tag():
    """
    ランダムなハッシュタグを生成する関数
    重複の検査は行わない。例えばファイル書き込みに失敗するなど、OS側で担保が必要。
    出力はTR_から始まる5桁のランダムな文字列。
    例: 1つのハッシュタグを生成して表示
    >>> print(generate_toriR_hash_tag()) 
    """
    # 使用する文字のセットを定義（数字と小文字の英文字）
    characters = string.digits + string.ascii_lowercase
    
    # 'TR_'というプレフィックスに続けて、5桁のランダムな文字列を生成
    hash_tag = 'TR_' + ''.join(random.choice(characters) for _ in range(5))
    
    # 生成されたハッシュタグを返す
    return hash_tag
