import logging
import os
from logging.handlers import TimedRotatingFileHandler


class CustomFormatter(logging.Formatter):
    white = "\x1b[37m"
    grey = "\x1b[38m"
    green = "\x1b[32m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    FORMATS = {
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


log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

TRACE_LEVEL_NUM = 5  # Ниже, чем DEBUG (10)


def trace(self, message, *args, **kws):
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        # Мы вызываем метод _log напрямую, чтобы передать свой уровень
        self._log(TRACE_LEVEL_NUM, message, args, **kws)


# Добавляем уровень и функцию к логгеру
logging.addLevelName(TRACE_LEVEL_NUM, 'TRACE')
logging.Logger.trace = trace

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Устанавливаем уровень логирования

# Создаем хэндлер, который будет писать логи в файл и разделять их по дням
handler = TimedRotatingFileHandler(
    filename=f'logs/daily',
    when="midnight",
    interval=1,
    backupCount=30,
    encoding='utf-8'
)

handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
handler.suffix = "-%Y-%m-%d.log"

# Создаем Handler для вывода логов в консоль
consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(CustomFormatter())
consoleHandler.setLevel(logging.DEBUG)

logger.addHandler(handler)
logger.addHandler(consoleHandler)

__all__ = ["logger"]
