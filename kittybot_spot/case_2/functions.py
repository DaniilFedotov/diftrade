import sys

import logging


def get_logger(name):
    """Создает логгер с заданными параметрами и возвращает его."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Назначается минимальный уровень, имея который сообщение идет в лог
    handler = logging.StreamHandler(stream=sys.stdout)
    file_handler = logging.FileHandler(f"log_{name}.log", mode='a')  # Обработчик для логирования в файл
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")  # Формат сообщения в лог
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(file_handler)
    return logger
