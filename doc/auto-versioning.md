# `auto-versioning.yml` 仕様書

## 概要
- `auto-versioning.yml` は、GitHub Actionsを使用してリポジトリ内のファイルのバージョンを自動的に管理するためのワークフローファイルです。セマンティックバージョニングに基づき、各ファイルの__version__を更新または追加します。
- ファイル名: auto-versioning.yml
- 配置場所: .github/workflows/
- トリガー: push
- ブランチ: main

## バージョンの決定方法
- pythonコードのバージョン情報は、`__version__`として管理します。
- pythonコードの最終更新日は、`__last_updated__`として管理します。日本時間で表示されます。
- pythonコードに`__version__`と`__last_updated__`が存在しない場合は、リモートリポジトリにpushされたタイミングで自動的に追加します。
- バージョン更新の対象は`python`と`bash`、`sh`,`awk`のファイルで、拡張子は`.py`、`.sh`、`.bash`、`.awk`です。
- それぞれのコードはグローバル変数として`__version__`と`__last_updated__`を持ちます。
- `.sh`, `.bash`, `.awk`のコードでは`__version__`と`__last_updated__`はシバンの行に続いて追加します。
- `.py`のコードでは`__version__`と`__last_updated__`はシバンの行の後に追加します。
- `git add .`のように複数のファイルが追加された場合でも自動でバージョン更新を行います。
- tagの追加は行いません。

### versionの更新方法
- コミットメッセージを使用
1. ローカルでコミット:
  - コミットメッセージに[MAJOR]や[MINOR]を含めます。
  - 例）`git commit -m "feat: 新機能を追加 [MAJOR]"`
  - 例）`git commit -m "feat: 新機能を追加 [MINOR]"`
  - 例）`git commit -m "バグを修正"` PATCHレベルは自動的に更新されます。

2. GitHub Actionsでメッセージを解析:
  - コミットメッセージを解析してバージョンを更新します。
  - コミットメッセージに`[MAJOR]`が含まれている場合は、メジャーバージョンを更新します。
  - コミットメッセージに`[MINOR]`が含まれている場合は、マイナーバージョンを更新します。
  - コミットメッセージに`[MAJOR],[MINOR]`が含まれていない場合は、パッチバージョンを更新します。

## 使い方
1. ローカルでコミット:
  - コミットメッセージに[MAJOR]や[MINOR]を含めます。
  - 初期のバージョンは'v0.0.1'に自動で設定される。
  - 例）`git add . && git commit -m "feat: 新機能を追加 [MAJOR]"`
  - 例）`git add . && git commit -m "feat: 新機能を追加 [MINOR]"`
  - 例）`git add . && git commit -m "バグを修正"` PATCHレベルは自動的に更新されます。
  - コミットメッセージで"v.*.*"と指定されていれば、バージョンを更新します。
  - 例）`git add . && git commit -m "v1.0.0"`

2. リモートリポジトリにpush:
  - 例）`git push origin main` もしくは `git push`

3. バージョンが更新されたコードの取得
  - 例）`git pull origin main` もしくは `git pull`

以上

