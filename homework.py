import logging
import requests
import telegram
import os
import sys
import time


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
    filemode='w',
    encoding='utf-8',
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
        logging.debug('send message')
    except Exception as error:
        logging.error(f'Sending message failed error: {error}')


def get_api_answer(timestamp):
    """Get request status"""
    homework_statuses = requests.get(ENDPOINT,
                                     headers=HEADERS,
                                     params={'from_date': timestamp})
    if homework_statuses.status_code == 200:
        logging.debug('endpoint excess')
        return homework_statuses.json()
    else:
        logging.error(
            f'endpoint return status {homework_statuses.status_code}'
        )
        return False


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
    try:
        verdict = homeworks[0]['status']
        logging.debug('Response status is correct')
        try:
            homework_name = homeworks[0]['lesson_name']
            logging.debug('Response lesson name is correct')
            return f'Изменился статус проверки работы "{homework_name}". {HOMEWORK_VERDICTS[verdict]}'
        except Exception as error:
            logging.error(f'Response status is incorrect, {error}')
    except Exception as error:
        logging.error(f'Response lesson name is incorrect, {error}')


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
