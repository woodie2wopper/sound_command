
import os
import sys

def save_parameters(args, output_file=None, version=None, last_updated=None):
    """
    コマンドライン引数とバージョン情報をファイルに保存する
    
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