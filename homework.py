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
                raise logging.critical(f'ошибка TELEGRAM_CHAT_ID {error}')
        except Exception as error:
            raise logging.critical(f'ошибка TELEGRAM_TOKEN {error}')
    except Exception as error:
        raise logging.critical(f'ошибка PRACTICUM_TOKEN {error}')



def send_message(bot, message):
    """Send message"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('send message')
    except Exception as error:
        logging.error(f'Sending message failed error: {error}')


def get_api_answer(timestamp):
    """Get request status"""
    try:
        homework_statuses = requests.get(ENDPOINT,
                                         headers=HEADERS,
                                         params={'from_date': timestamp})
    except Exception as error:
        logging.error(f'request error: {error}')

    if homework_statuses.status_code != 200:
        raise logging.error(
            f'Failed get answer from API. Status code = '
            f'{homework_statuses.status_code}'
        )
    try:
        if type(homework_statuses.json()) == dict:
            return homework_statuses.json()
    except Exception as error:
        raise logging.error(f'{error}')


def check_response(response):
    """Return endpoint"""
    try:
        type(response) == dict
        logging.debug('Endpoint is dict')
        try:
            response['homeworks']
            logging.debug('key homework excess')
            return response['homeworks']
        except Exception as error:
            logging.error(f'No correct response {error}')
    except Exception as error:
        logging.error(f'No correct type {error}')


def parse_status(homeworks):
    """Проверка статуса работы"""
    homework = homeworks[0]
    try:
        homework['status']
        logging.debug('Response status is correct')
    except KeyError as error:
        raise logging.error(f'Response lesson name is incorrect, {error}')
    try:
        homework['lesson_name']
    except Exception as error:
        raise logging.error(f'Response status is incorrect, {error}')
    try:
        if type(f'Изменился статус проверки работы' 
                f'"{homework["lesson_name"]}". '
                f'{HOMEWORK_VERDICTS[homework["status"]]}') == str:
            return f'Изменился статус проверки работыf "{homework["lesson_name"]}". {HOMEWORK_VERDICTS[homework["status"]]}'
    except Exception as error:
        raise logging.error(f'return not string {error}')

def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('missing token or chat id')
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time()) - RETRY_PERIOD
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
