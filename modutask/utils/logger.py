from typing import NoReturn
import logging

def setup_logger(logfile: str):
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s.%(funcName)s(): %(message)s'
    )

    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # コンソール出力
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # ファイル出力
    file_handler = logging.FileHandler(logfile)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 重複登録を避けるために既存のハンドラーをクリア
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

def raise_with_log(exc_type: type[Exception], message: str) -> NoReturn:
    logger = logging.getLogger(__name__)
    logger.error(f"[{exc_type.__name__}] {message}")
    raise exc_type(message)
