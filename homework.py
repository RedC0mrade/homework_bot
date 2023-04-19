import logging
import requests
import telegram
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()


class APIResponseCodeError(Exception):
    """Api error"""
    pass


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
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        logging.debug('all token in place')
        return True
    else:
        logging.critical('One or more Token not found')
        return False


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
        logging.debug(f'status {response}. Ok')
    except Exception as error:
        logging.error(f'request error: {error}')
        raise ValueError(f'request error: {error}')

    if response.status_code != 200:
        logging.error(f'Failed get answer from API. Status code = '
                      f'{response.status_code}')
        raise ConnectionError('Failed get answer from API.')
    try:
        if type(response.json()) == dict:
            logging.debug('response type dict')
            return response.json()
    except Exception as error:
        logging.error(f'Type of homework_statuses not dict {error}')
        raise KeyError('Type of homework_statuses not dict')


def check_response(response):
    """Return endpoint"""
    if type(response) != dict:
        logging.error(f'response not dict, {type(response)}')
        raise TypeError(f'response not dict, {type(response)}')
    try:
        response['homeworks']
        logging.debug('key homework excess')
    except Exception as error:
        logging.error(f'Dict dont have a key "homeworks" {error}')
        raise KeyError(f'Dict dont have a key "homeworks" {error}')

    if type(response['homeworks']) != list:
        logging.error(f'homeworks not list, {type(response["homeworks"])}')
        raise TypeError(f'homeworks not list, {type(response["homeworks"])}')
    else:
        logging.debug('type of "homeworks" is list')
        return response['homeworks']


def parse_status(homeworks):
    """Проверка статуса работы"""

    try:
        status = homeworks.get('status')
        verdict = HOMEWORK_VERDICTS[status]
        logging.debug(f'Response status is correct {status}')
    except KeyError as error:
        logging.error(f'status of homeworks is incorrect, {error}')
        raise f'The data "status" is not correct, {error}'

    try:
        homework_name = homeworks.get('homework_name')
        logging.debug(f'Name homework {homework_name}')
    except Exception as error:
        logging.error(f'lesson_name is incorrect, {error}')
        raise f'The data "lesson_name" is not correct, {error}'

    if homeworks.get('homework_name') is None:
        logging.error(f'Key "homework_name" not exists')
        raise KeyError(f'Key "homework_name" not exists')

    try:
        message = f'Изменился статус проверки работы "{homework_name}". ' \
                  f'{verdict}'
        if type(message) == str:
            logging.debug(type(message))
            return message
    except Exception as error:
        logging.error(f'return not string {error}, {type(message)}')
        raise f'return not string {error}, {status}, {homework_name}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
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
                send_message(bot, sending_message)
                anti_spam_check = sending_message
            else:
                logging.debug('No changes')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != anti_spam_check:
                send_message(bot, message)
                anti_spam_check = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
