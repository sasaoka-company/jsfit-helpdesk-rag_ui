import logging
import logging.handlers
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # このファイルのある場所
LOG_DIR = os.path.join(BASE_DIR, "log")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # 既にハンドラが設定されている場合は再設定せず、そのまま返す
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # 日付ベースのローテーションハンドラーを使用
    # 毎日0時にローテーションし、30日分のログを保持
    fh = logging.handlers.TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",  # 毎日0時にローテーション
        interval=1,  # 1日間隔
        backupCount=30,  # 30日分のバックアップを保持
        encoding="utf-8",
    )
    fh.setLevel(logging.INFO)

    # ローテーション後のファイル名に日付サフィックスを追加
    fh.suffix = "%Y-%m-%d"

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    fh.setFormatter(formatter)

    logger.addHandler(fh)

    # 親ロガーに伝播しないようにして重複を防ぐ
    logger.propagate = False

    return logger
