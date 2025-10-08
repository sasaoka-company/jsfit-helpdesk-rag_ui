**Web UI 機能を提供する Web サーバー**

このプロジェクトは、API サーバ（AI エージェント機能を提供）と連携する Web UI アプリケーションです。
Streamlit によって構築されています。

# 1. 機能

- **チャット**: チャット形式で AI エージェントと対話

# 2. 前提条件

- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/) (Python パッケージマネージャー)
- 仮想環境（`.venv`）が作成されていること

# 3. 開発環境セットアップ

## 3-1. Git 設定

以下コマンドにより、チェックアウト時、コミット時に改行コードを変更しないようにします。（`.gitattributes` のままになります）

```powershell
git config --global core.autocrlf false
```

## 3-2. 依存関係のインストール

以下コマンドにより、`pyproject.toml`で定義されているライブラリをインストールします。

```powershell
uv sync
```

# 4. サーバ起動

```powershell
streamlit run ui.py
```

## （参考）UI アプリケーションが起動すると、ブラウザが自動的に開き、以下の URL でアクセスできます：

http://localhost:8501
