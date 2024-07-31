import inspect
import logging
import os
from logging.handlers import TimedRotatingFileHandler

TRACE_LEVEL_NUM = 5
LOG_LEVEL = logging.INFO
CONSOLE_LEVEL = logging.DEBUG
LOG_DIR = 'logs'


class CustomFormatter(logging.Formatter):
    white = "\x1b[37m"
    dark_white = "\x1b[90m"
    grey = "\x1b[38m"
    green = "\x1b[32m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(message)s"

    FORMATS = {
        TRACE_LEVEL_NUM: dark_white + format + reset,
        logging.DEBUG: white + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: "\x1b[33m" + format + reset,
        logging.ERROR: "\x1b[31m" + format + reset,
        logging.CRITICAL: "\x1b[41m" + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def trace(self, message, *args, **kwargs):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kwargs)


original_log = logging.Logger._log


def custom_log(self, level, msg, args, exc_info=None, extra=None, stack_info=False):
    # Используем модуль inspect для получения фрейма, откуда был сделан вызов
    caller_frame = inspect.currentframe().f_back.f_back
    caller_name = caller_frame.f_globals['__name__']
    # Выполняем поиск класса в фрейме вызова
    class_name = ''
    self_class = caller_frame.f_locals.get('self', None)
    if self_class:
        class_name = self_class.__class__.__name__

    # Добавляем имя класса к сообщению лога
    modified_msg = f"[{class_name}]{msg}"

    # Вызываем оригинальный метод _log с модифицированным сообщением
    original_log(self, level, modified_msg, args, exc_info, extra, stack_info)


# Заменяем оригинальный метод _log нашей кастомной реализацией
logging.Logger._log = custom_log
# Добавляем уровень и функцию к логгеру
logging.addLevelName(TRACE_LEVEL_NUM, 'TRACE')
logging.Logger.trace = trace

logger = logging.getLogger(__name__)
logger.setLevel(CONSOLE_LEVEL)

# Создаем хэндлер, который будет писать логи в файл и разделять их по дням
handler = TimedRotatingFileHandler(
    filename=f'logs/daily',
    when="midnight",
    interval=1,
    backupCount=30,
    encoding='utf-8'
)

handler.setLevel(LOG_LEVEL)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
handler.suffix = "-%Y-%m-%d.log"

# Создаем Handler для вывода логов в консоль
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(CustomFormatter())
consoleHandler.setLevel(CONSOLE_LEVEL)

logger.addHandler(handler)
logger.addHandler(consoleHandler)

logger.trace("TRACE asdasdasd")

__all__ = ["logger"]
