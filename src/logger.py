import logging
import logging.handlers
import os
from filelock import FileLock
from src.config import ROOT_DIR

# ログディレクトリ
LOG_DIR = os.path.join(ROOT_DIR, "log")

# 日付ベースのログファイル名（ローテーション用）
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# ロックファイル
LOCK_FILE = LOG_FILE + ".lock"

# 環境変数キー名: ログレベル
ENV_LOG_LEVEL = "LOG_LEVEL"

# デフォルトログレベル
DEFAULT_LOG_LEVEL = logging.INFO

os.makedirs(LOG_DIR, exist_ok=True)


# マルチプロセス対応ローテーションハンドラ
class SafeTimedRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """
    複数プロセスで安全にローテーション可能なハンドラ。
    ファイルロックを使用して、ローテーション時の競合を防止する。

    動作イメージ：
    - プロセスAが日付変更でローテーションを始める
      → .lock ファイルを取得
    - プロセスBも同時にローテーションを検知
      → .lock が解放されるまで待機
    - Aのローテーション完了後、Bが処理を再開
      → ログファイル競合なし、WinError 32発生しない

    補足：
    - .lock ファイルは一時的に生成されますが、サイズはほぼ 0バイト。
    - ローテーションは極めて短時間なので、他プロセスが「数ミリ秒〜数百ミリ秒待機」するだけ。
    - --reload 付きの Uvicorn でも安全に動作する。
    """

    def doRollover(self):
        # ファイルロックで競合を防止（他プロセスは待ち状態になる）
        with FileLock(LOCK_FILE):
            super().doRollover()


def get_logger(name: str) -> logging.Logger:
    """
    ロガーを取得する.

    環境変数 `LOG_LEVEL` でログレベルを制御できます（デフォルト: INFO）。

    Note:
        環境変数が未設定または不正な値の場合は INFO レベルになります。

        環境変数 `LOG_LEVEL` の値:
          - DEBUG
          - INFO（デフォルト）
          - WARNING
          - ERROR
    """
    logger = logging.getLogger(name)

    # 環境変数からログレベルを取得（未設定の場合は空文字列に変換）
    # 不正な値や空文字列の場合は getattr() で logging.INFO に変換
    log_level_str = (os.getenv(ENV_LOG_LEVEL) or "").upper()
    log_level = getattr(logging, log_level_str, DEFAULT_LOG_LEVEL)

    # 既にハンドラが設定されている場合は再設定せず、そのまま返す
    if logger.handlers:
        logger.setLevel(log_level)  # ロガーのレベルを更新
        for handler in logger.handlers:
            handler.setLevel(log_level)  # ハンドラーのレベルも更新
        return logger

    logger.setLevel(log_level)

    # 日付単位のローテーションハンドラーを使用
    fh = SafeTimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",  # 毎日午前0時にローテーション
        interval=1,  # 1日間隔
        backupCount=365,  # 365日分のログを保持
        encoding="utf-8",
        delay=True,  # ファイルをすぐ開かず、最初のログ出力時に開く
    )
    fh.setLevel(log_level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    # ルートロガーへの伝播を無効化（親ロガーのハンドラーによる重複出力を防止）
    logger.propagate = False

    return logger
