import logging

# Сначала определяем новый уровень логирования
CUSTOM_LEVEL = 2  # Выбираем значение между WARNING (30) и INFO (20)
logging.addLevelName(CUSTOM_LEVEL, 'CUSTOM')

def custom(self, message, *args, **kwargs):
    if self.isEnabledFor(CUSTOM_LEVEL):
        self._log(CUSTOM_LEVEL, message, args, **kwargs)

# Добавляем метод custom к классу Logger
logging.Logger.custom = custom

# Теперь можем использовать этот уровень в наших логгерах
logger = logging.getLogger(__name__)
logger.setLevel(2)

# Настраиваем вывод логов в консоль
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Пример использования нового уровня логирования
logger.custom('Это сообщение с пользовательским уровнем логирования')