import asyncio
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
    複数プロセスで安全にローテーション可能なハンドラ.

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
        """ファイルロックを使用して安全にローテーションを実行する."""
        # ファイルロックで競合を防止（他プロセスは待ち状態になる）
        with FileLock(LOCK_FILE):
            super().doRollover()


class TaskIdFilter(logging.Filter):
    """
    ログレコードにタスクIDを追加するフィルター.

    asyncioタスクのIDを自動的にログレコードに追加します。
    asyncioタスク外で実行された場合は "NoTask" を設定します。
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        ログレコードにタスクID属性を追加する.

        Args:
            record: ログレコード

        Returns:
            常にTrue（ログを通過させる）
        """
        try:
            task = asyncio.current_task()
            if task:
                # タスクIDを16進数の短縮版（末尾8桁）で取得
                record.task_id = f"{id(task):x}"[-8:]
            else:
                record.task_id = "NoTask"
        except RuntimeError:
            # asyncioイベントループが実行されていない場合
            record.task_id = "NoTask"

        return True


def get_logger(
    name: str,
    out_process_name: bool = True,
    out_thread_name: bool = False,
    out_task_id: bool = True,
) -> logging.Logger:
    """
    ロガーを取得する.

    環境変数 `LOG_LEVEL` でログレベルを制御できます（デフォルト: INFO）。

    Args:
        name: ロガー名（通常は __name__ を指定）
        out_process_name: プロセス名を出力するか（デフォルト: True）
        out_thread_name: スレッド名を出力するか（デフォルト: False）
        out_task_id: タスクIDを出力するか（デフォルト: True）

    Returns:
        設定済みのロガーインスタンス

    Note:
        環境変数が未設定または不正な値の場合は INFO レベルになります。

        環境変数 `LOG_LEVEL` の値:
          - DEBUG
          - INFO（デフォルト）
          - WARNING
          - ERROR

    Example:
        >>> # 基本的な使用（プロセス名 + タスクID）
        >>> logger = get_logger(__name__)
        >>> logger.info("メッセージ")
        # 出力: 2025-11-13 10:00:00,000 [MainProcess][TaskID: 1a2b3c4d][module][INFO] - メッセージ

        >>> # タスクIDなし
        >>> logger = get_logger(__name__, out_task_id=False)
        >>> logger.info("メッセージ")
        # 出力: 2025-11-13 10:00:00,000 [MainProcess][module][INFO] - メッセージ

        >>> # プロセス名 + スレッド名 + タスクID
        >>> logger = get_logger(__name__, out_task_id=True, out_process_name=True, out_thread_name=True)
        >>> logger.info("メッセージ")
        # 出力: 2025-11-13 10:00:00,000 [MainProcess:MainThread][TaskID: 1a2b3c4d][module][INFO] - メッセージ

        >>> # タスクIDのみ（最小構成）
        >>> logger = get_logger(__name__, out_task_id=True, out_process_name=False, out_thread_name=False)
        >>> logger.info("メッセージ")
        # 出力: 2025-11-13 10:00:00,000 [TaskID: 1a2b3c4d][module][INFO] - メッセージ
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

    # タスクIDフィルターを追加
    if out_task_id:
        fh.addFilter(TaskIdFilter())

    # フォーマットを動的に構築
    format_parts = [
        "%(asctime)s",
    ]

    # プロセス名・スレッド名の出力を制御
    if out_process_name and out_thread_name:
        format_parts.append(" [%(processName)s:%(threadName)s]")
    elif out_process_name:
        format_parts.append(" [%(processName)s]")
    elif out_thread_name:
        format_parts.append(" [%(threadName)s]")

    # タスクIDの出力を制御
    if out_task_id:
        format_parts.append("[%(task_id)s]")

    format_parts.extend(
        [
            "[%(name)s]",
            "[%(levelname)s]",
            " %(message)s",
        ]
    )

    formatter = logging.Formatter("".join(format_parts))
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    # ルートロガーへの伝播を無効化（親ロガーのハンドラーによる重複出力を防止）
    logger.propagate = False

    return logger
