# Sample RAG UI

業務上の質問に回答する AI エージェントの WebUI アプリケーションです。Streamlit と FastAPI を使用して構築されています。

## 機能

- チャット形式で AI エージェントと対話
- RAG（Retrieval-Augmented Generation）システムによる回答生成
- 会話履歴の表示
- リアルタイムでの API サーバー接続状況確認

## 環境要件

- Python 3.12 以上
- uv

## セットアップ

### 1. Git 設定

リポジトリをクローンした後、以下のコマンドを実行してください：

```bash
git config --global core.autocrlf false
```

※上記は、チェックアウト時、コミット時に改行コードを変更しない設定です（.gitattributes のままになります）

### 2. 仮想環境（.venv）の作成

仮想環境（`.venv`ディレクトリ）は GitHub リポジトリに登録されていないため、pull した後に仮想環境を作成する必要がある。

```コマンド（Windows Power Shell）
uv venv --python 3.12
```

※ `uv init`コマンドの実行は不要（pyproject.toml の作成などは作成済みのものが GitHub にプッシュされている）

### 3. .python-version の更新

```コマンド（Windows Power Shell）
uv python pin 3.12
```

※ `.python-version`が更新される。GitHub に登録されていない場合は新規作成される。

### 4. 依存関係のインストール

pyproject.toml に定義された依存関係をインストール：

```bash
uv sync
```

### 5. API サーバーの起動

API サーバーを起動してください（詳細は省略）。

## UI アプリケーションの起動

新しいターミナルを開いて以下のコマンドを実行：

```bash
streamlit run ui.py
```

## アクセス方法

UI アプリケーションが起動すると、ブラウザが自動的に開き、以下の URL でアクセスできます：

```
http://localhost:8501
```

## 使用方法

1. ブラウザでアプリケーションにアクセス
2. サイドバーで API サーバーの接続状況を確認
3. チャット入力欄に質問を入力
4. AI エージェントからの回答を確認

## ファイル構成

- `ui.py`: Streamlit ベースの WebUI アプリケーション
- `logger.py`: ログ設定
- `pyproject.toml`: プロジェクト設定と依存関係
- `test.py`: テストファイル
- `log/`: ログファイル格納ディレクトリ
