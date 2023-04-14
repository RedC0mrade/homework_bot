import logging
import os
import requests


import telegram


from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    filemode='w'
)


def check_tokens():
    """Check tokens exists"""
    try:
        PRACTICUM_TOKEN
        logging.debug('Токен PRACTICUM_TOKEN в порядке')
        try:
            TELEGRAM_TOKEN
            logging.debug('Токен TELEGRAM_TOKEN в порядке')
            try:
                TELEGRAM_CHAT_ID
                logging.debug('Токен TELEGRAM_CHAT_ID в порядке')
                return True
            except Exception as error:
                logging.critical(f'ошибка TELEGRAM_CHAT_ID {error}')
                return False
        except Exception as error:
            logging.critical(f'ошибка TELEGRAM_TOKEN {error}')
            return False
    except Exception as error:
        logging.critical(f'ошибка PRACTICUM_TOKEN {error}')
        return False


def send_message(bot, message):
    """Send message"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Отправка сообщения')
    except Exception as error:
        logging.error(f'Отправка сообщения не удалась ошибка: {error}')


def get_api_answer(timestamp):
    homework_statuses = requests.get(ENDPOINT,
                                     headers=HEADERS,
                                     params=timestamp)
    if homework_statuses == 200:
        logging.debug('Эндпоинт существует')
        return requests.get(ENDPOINT, headers=HEADERS, params=timestamp).json()
    else:
        logging.error(f'Эндпоинт возвращает статус {homework_statuses}')


def check_response(response):
    try:
        type(response) == dict
        logging.debug('Эндпоинт существует')
        try:
            response['homework']
            logging.debug('ключ homework существует')
            return True
        except Exception as error:
            logging.error(f'No correct response {error}')
            return False
    except Exception as error:
        logging.error(f'No correct response {error}')
        return False


def parse_status(homework):
    try:
        verdict = homework['homeworks'][0]['status']
        logging.debug('Response status is correct')
        try:
            homework_name = homework['homeworks'][0]['lesson_name']
            logging.debug('Response lesson name is correct')
            return f'Изменился статус проверки работы ' \
                   f'"{homework_name}". {verdict}'
        except Exception as error:
            logging.error(f'Response lesson name is incorrect, {error}')
    except Exception as error:
        logging.error(f'Response lesson name is incorrect, {error}')


def main():
    """Основная логика работы бота."""



    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    ...

    while True:
        try:

            ...

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
        ...


if __name__ == '__main__':
    main()
