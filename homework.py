import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv

from exceptions import APIResponseCodeError


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

LAST_PROJECT = 0
RETRY_PERIOD = 600
ONE_MONTH_TIME = 2629743
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Check tokens exists."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logging.debug('all token in place')
        return True
    return False


def send_message(bot, message):
    """Send message."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'send message {message}')
        return True
    except telegram.error.TelegramError as error:
        logging.error(f'Sending message failed error: {error}')
        return False


def get_api_answer(timestamp):
    """Get request status."""
    try:
        response = requests.get(ENDPOINT,
                                headers=HEADERS,
                                params={'from_date': timestamp})
        logging.debug(f'status {response}. Ok')
    except requests.RequestException as error:
        raise ConnectionError(f'request error: {error}')

    if response.status_code != 200:
        raise APIResponseCodeError('Failed get answer from API.')

    return response.json()


def check_response(response):
    """Return endpoint."""
    if not response:
        raise APIResponseCodeError('Никаких обновлений в статусе нет')

    if not isinstance(response, dict):
        raise TypeError(f'response not dict, {type(response)}')
    try:
        response['homeworks']
        logging.debug('key homework excess')
    except Exception as error:
        raise KeyError(f'Dict dont have a key "homeworks" {error}')

    if not isinstance(response['homeworks'], list):
        raise TypeError(f'homeworks not list, {type(response["homeworks"])}')

    return response['homeworks']


def parse_status(homework):
    """Проверка, что данные пришли ввиде словаря и на наличие ключей."""
    if not homework['status']:
        raise KeyError('Missing key status')

    if homework['status'] not in HOMEWORK_VERDICTS:
        raise KeyError('Missing key in HOMEWORK_VERDICTS')

    status = homework['status']
    verdict = HOMEWORK_VERDICTS[status]
    logging.debug(f'Response status is correct {status}')

    try:
        homework_name = homework['homework_name']
        logging.debug(f'Name homework {homework_name}')
    except Exception as error:
        logging.error(f'lesson_name is incorrect, {error}')
        raise f'The data "lesson_name" is not correct, {error}'

    if homework.get('homework_name') is None:
        logging.error('Key "homework_name" not exists')
        raise KeyError('Key "homework_name" not exists')

    try:
        message = (f'Изменился статус проверки работы "{homework_name}". '
                   f'{verdict}')
        logging.debug(type(message))
        return message
    except Exception as error:
        logging.error(f'return not string {error}, {type(message)}')
        raise f'return not string {error}, {status}, {type(message)}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('One or more Token not found')
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - ONE_MONTH_TIME
    anti_spam_check = ''

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            sending_message = parse_status(homeworks[LAST_PROJECT])
            if sending_message != anti_spam_check:
                logging.debug(f'New status аvailable {sending_message}')

                if send_message(bot, sending_message):
                    logging.debug(f'message send {sending_message}')
                    anti_spam_check = sending_message
                    timestamp = response.get('current_date', timestamp)
            else:
                logging.debug('No changes')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != anti_spam_check:
                if send_message(bot, message):
                    anti_spam_check = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.FileHandler(filename='main.log', mode='w',
                                encoding='utf-8'),
            logging.StreamHandler(stream=sys.stdout)
        ],
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
