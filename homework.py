import logging
import requests
import telegram
import os
import sys
import time


class APIResponseCodeError(Exception):
    """Api error"""
    pass


from dotenv import load_dotenv

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ONE_MONTH_TIME = 2629743
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[
        logging.FileHandler(filename='main.log', mode='w', encoding='utf-8'),
        logging.StreamHandler(stream=sys.stdout)
    ],
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
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
                raise ValueError(f'missing token "TELEGRAM_CHAT_ID"')
        except Exception as error:
            logging.critical(f'ошибка TELEGRAM_TOKEN {error}')
            raise ValueError(f'missing token "TELEGRAM_TOKEN"')
    except Exception as error:
        logging.critical(f'ошибка PRACTICUM_TOKEN {error}')
        raise ValueError(f'missing token "PRACTICUM_TOKEN"')


def send_message(bot, message):
    """Send message"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('send message')
    except Exception as error:
        logging.error(f'Sending message failed error: {error}')
        raise ValueError(f'Message not send')


def get_api_answer(timestamp):
    """Get request status"""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
    except Exception as error:
        logging.error(f'request error: {error}')
        raise ValueError(f'request error: {error}')

    if response.status_code != 200:
        logging.error(f'Failed get answer from API. Status code = '
                      f'{response.status_code}')
        raise ConnectionError('Failed get answer from API.')
    try:
        if type(response.json()) == dict:
            print(response.json())
            return response.json()
    except Exception as error:
        logging.error(f'Type of homework_statuses not dict {error}')
        raise KeyError('Type of homework_statuses not dict')


def check_response(response):
    """Return endpoint"""

    try:
        response['homeworks']
        logging.debug('key homework excess')
        return response['homeworks']
    except Exception as error:
        logging.error(f'No correct response {error}')
        raise KeyError('Dict dont have a key "homeworks"')


def parse_status(homeworks):
    """Проверка статуса работы"""
    try:
        homeworks[0]['status']
        logging.debug('Response status is correct')
    except KeyError as error:
        raise logging.error(f'Response lesson name is incorrect, {error}')
    try:
        homeworks[0]['lesson_name']
    except Exception as error:
        raise logging.error(f'Response status is incorrect, {error}')
    try:
        if type(f'Изменился статус проверки работы' 
                f'"{homeworks["lesson_name"]}". '
                f'{HOMEWORK_VERDICTS[homeworks["status"]]}') == str:
            return f'Изменился статус проверки работыf "{homeworks["lesson_name"]}". {HOMEWORK_VERDICTS[homeworks["status"]]}'
    except Exception as error:
        raise logging.error(f'return not string {error}')


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('missing token or chat id')
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - ONE_MONTH_TIME
    anti_spam_check = []

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks and homeworks != anti_spam_check:
                send_message(bot, parse_status(homeworks))
                anti_spam_check = homeworks
            else:
                logging.debug('No changes')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
