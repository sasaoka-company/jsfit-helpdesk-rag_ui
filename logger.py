import logging
import logging.handlers
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # このファイルのある場所
LOG_DIR = os.path.join(BASE_DIR, "log")

# 日付ベースのログファイル名（ローテーション用）
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # 既にハンドラが設定されている場合は再設定せず、そのまま返す
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 日付単位のローテーションハンドラーを使用
    fh = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",  # 毎日午前0時にローテーション
        interval=1,  # 1日間隔
        backupCount=365,  # 365日分のログを保持
        encoding="utf-8",
    )
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    # ルートロガーへの伝播を無効化（親ロガーのハンドラーによる重複出力を防止）
    logger.propagate = False

    return logger
