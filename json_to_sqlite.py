#!/usr/bin/env python3

import json
import sqlite3
import sys
import argparse
import os

def create_database():
    # データベースに接続（存在しない場合は新規作成）
    conn = sqlite3.connect('/var/www/data/call-database/call-database.db')
    cursor = conn.cursor()

    # sound_metadataテーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sound_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT NOT NULL,
            recording_id INTEGER NOT NULL,
            page INTEGER NOT NULL,
            num_recordings INTEGER NOT NULL,
            num_species INTEGER NOT NULL,
            num_pages INTEGER NOT NULL,
            gen TEXT NOT NULL,
            sp TEXT NOT NULL,
            ssp TEXT,
            group_name TEXT,
            en TEXT,
            rec TEXT,
            cnt TEXT,
            loc TEXT,
            lat TEXT,
            lng TEXT,
            alt TEXT,
            type TEXT,
            sex TEXT,
            stage TEXT,
            method TEXT,
            url TEXT,
            file TEXT,
            file_name TEXT,
            sono_small TEXT,
            sono_med TEXT,
            sono_large TEXT,
            sono_full TEXT,
            osci_small TEXT,
            osci_med TEXT,
            osci_large TEXT,
            lic TEXT,
            quality TEXT,
            length TEXT,
            time TEXT,
            date TEXT,
            uploaded TEXT,
            remarks TEXT,
            bird_seen TEXT,
            animal_seen TEXT,
            playback_used TEXT,
            temp TEXT,
            regnr TEXT,
            auto TEXT,
            dvc TEXT,
            mic TEXT,
            smp TEXT,
            UNIQUE(origin, recording_id),
            UNIQUE(origin, gen, sp, recording_id)
        )
    ''')

    # annotation_statusテーブルの作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS annotation_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sound_metadata_id INTEGER NOT NULL,
            is_annotated BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (sound_metadata_id) REFERENCES sound_metadata(id),
            UNIQUE(sound_metadata_id)
        )
    ''')
    
    conn.commit()
    return conn, cursor

def verify_data(cursor, data, origin, verbose=False):
    """データベースに保存されたデータの検証を行う"""
    print("\n=== データ検証開始 ===")
    
    # 処理対象のrecording_idリストを作成
    recording_ids = [rec['id'] for rec in data['recordings']]
    recording_ids_str = ','.join(f"'{rid}'" for rid in recording_ids)
    
    # originとrecording_idに基づいて保存されたレコード数を確認
    cursor.execute(f"""
        SELECT COUNT(*) FROM sound_metadata 
        WHERE origin = ? AND recording_id IN ({recording_ids_str})
    """, (origin,))
    
    saved_count = cursor.fetchone()[0]
    expected_count = len(data['recordings'])
    
    print(f"期待されるレコード数: {expected_count}")
    print(f"保存されたレコード数（origin={origin}のみ）: {saved_count}")
    
    if saved_count != expected_count:
        print("⚠️ レコード数が一致しません")
        if verbose:
            # 詳細な不一致情報を表示
            cursor.execute(f"""
                SELECT recording_id, gen, sp FROM sound_metadata 
                WHERE origin = ? AND recording_id IN ({recording_ids_str})
            """, (origin,))
            saved_records = cursor.fetchall()
            print("\n保存されているレコード:")
            for rec in saved_records:
                print(f"- {rec[0]} ({rec[1]} {rec[2]})")
        return False
    
    return True

def import_json_to_sqlite(json_file_path, origin, debug=False, verbose=False):
    # JSONファイルの拡張子チェック
    if not json_file_path.endswith('.json'):
        print(f"エラー: JSONファイルではありません: {json_file_path}")
        sys.exit(1)

    try:
        # データベースに接続
        conn, cursor = create_database()
        
        # デバッグモードの場合、テーブルを削除して再作成
        if debug:
            if verbose:
                print("デバッグモード: テーブルを初期化します")
            cursor.execute("DROP TABLE IF EXISTS annotation_status")
            cursor.execute("DROP TABLE IF EXISTS sound_metadata")
            conn, cursor = create_database()

        # JSONファイルを読み込む
        if verbose:
            print(f"JSONファイル読み込み中: {json_file_path}")
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # データ構造の検証
        if verbose:
            print("データ構造:", list(data.keys()))
        
        # ページ情報の取得（存在しない場合はデフォルト値を使用）
        page = data.get('page', 1)
        num_recordings = int(data.get('numRecordings', len(data.get('recordings', []))))
        num_species = int(data.get('numSpecies', 1))
        num_pages = data.get('numPages', 1)
        
        if verbose:
            print(f"ページ情報: page={page}, recordings={num_recordings}, species={num_species}, pages={num_pages}")
        
        # recordingsの各アイテムを処理
        recordings = data.get('recordings', [])
        if not recordings:
            print(f"警告: {json_file_path} に録音データが見つかりません")
            return

        # カラム名を明示的に指定
        columns = '''(
            origin, page, num_recordings, num_species, num_pages,
            recording_id, gen, sp, ssp, group_name, en,
            rec, cnt, loc, lat, lng, alt, type, sex,
            stage, method, url, file, file_name,
            sono_small, sono_med, sono_large, sono_full,
            osci_small, osci_med, osci_large,
            lic, quality, length, time, date, uploaded,
            remarks, bird_seen, animal_seen, playback_used,
            temp, regnr, auto, dvc, mic, smp
        )'''

        skipped_count = 0
        inserted_count = 0
        
        for recording in recordings:
            if verbose:
                print(f"\n処理中のレコード: {recording['id']}")
            
            # 重複チェック
            cursor.execute('''
                SELECT COUNT(*) FROM sound_metadata 
                WHERE recording_id = ? AND gen = ? AND sp = ?
            ''', (recording['id'], recording['gen'], recording['sp']))
            
            if cursor.fetchone()[0] > 0:
                if verbose:
                    print(f"スキップ: レコード {recording['id']} ({recording['gen']} {recording['sp']}) は既に存在します")
                skipped_count += 1
                continue
            
            values = [
                origin,
                page, num_recordings, num_species, num_pages,
                recording['id'], recording['gen'], recording['sp'], recording.get('ssp', ''),
                recording.get('group', ''), recording['en'], recording['rec'], recording['cnt'],
                recording['loc'], recording['lat'], recording['lng'], recording.get('alt', ''),
                recording.get('type', ''), recording.get('sex', ''), recording.get('stage', ''),
                recording.get('method', ''),
                recording.get('url', ''), recording.get('file', ''), recording.get('file-name', ''),
                recording.get('sono', {}).get('small', ''),
                recording.get('sono', {}).get('med', ''),
                recording.get('sono', {}).get('large', ''),
                recording.get('sono', {}).get('full', ''),
                recording.get('osci', {}).get('small', ''),
                recording.get('osci', {}).get('med', ''),
                recording.get('osci', {}).get('large', ''),
                recording.get('lic', ''), recording.get('q', ''),
                recording.get('length', ''), recording.get('time', ''),
                recording.get('date', ''), recording.get('uploaded', ''),
                recording.get('rmk', ''),
                recording.get('bird-seen', ''), recording.get('animal-seen', ''),
                recording.get('playback-used', ''), recording.get('temp', ''),
                recording.get('regnr', ''), recording.get('auto', ''),
                recording.get('dvc', ''), recording.get('mic', ''),
                recording.get('smp', '')
            ]

            # 値の数をチェック
            if verbose:
                print(f"挿入する値の数: {len(values)}")
                
            placeholders = ','.join(['?' for _ in values])
            
            try:
                cursor.execute(f'''
                    INSERT INTO sound_metadata {columns}
                    VALUES ({placeholders})
                ''', values)
                
                # sound_metadataの挿入後、対応するannotation_statusレコードを作成
                cursor.execute('''
                    INSERT INTO annotation_status (sound_metadata_id, is_annotated)
                    VALUES (?, ?)
                ''', (cursor.lastrowid, False))
                
                inserted_count += 1
                if verbose:
                    print(f"✓ レコード {recording['id']} ({recording['gen']} {recording['sp']}) を挿入しました")
                    
            except sqlite3.IntegrityError:
                if verbose:
                    print(f"スキップ: レコード {recording['id']} ({recording['gen']} {recording['sp']}) は既に存在します")
                skipped_count += 1
                continue

        # 結果サマリーの表示
        print(f"\n=== 処理結果 ===")
        print(f"処理したレコード数: {len(recordings)}")
        print(f"挿入したレコード数: {inserted_count}")
        print(f"スキップしたレコード数: {skipped_count}")

        # データの検証
        if not verify_data(cursor, data, origin, verbose):
            print("⚠️ データの検証に失敗しました")
            conn.rollback()
            return False
        else:
            print("✅ データの検証に成功しました")
            conn.commit()
            return True

    except json.JSONDecodeError:
        print(f"JSONファイルの形式が正しくありません: {json_file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        if verbose:
            import traceback
            print("\n詳細なエラー情報:")
            print(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JSONデータをSQLiteデータベースにインポートします')
    parser.add_argument('json_file', help='インポートするJSONファイルのパス (.json)')
    parser.add_argument('--origin', required=True, help='音源データの音源元（例：xeno-canto）')
    parser.add_argument('--debug', '-d', action='store_true', help='データベースを初期化して処理（デバッグ用）')
    parser.add_argument('--verbose', '-v', action='store_true', help='詳細な出力を表示')
    
    args = parser.parse_args()
    import_json_to_sqlite(args.json_file, args.origin, args.debug, args.verbose)