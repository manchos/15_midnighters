import requests
import requests_cache
import logging
import argparse
import os
from datetime import datetime
from pytz import timezone
import pytz
from collections import defaultdict

logging.basicConfig(level=logging.ERROR)

SOLUTION_ATTEMPTS_URL = 'http://devman.org/api/challenges/solution_attempts/'


def get_solution_attempts_page_json(page_number, url=SOLUTION_ATTEMPTS_URL):
    headers = {'User-agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'}
    try:
        page_url = '{}?page={}'.format(url, page_number)
        response = requests.get(page_url, headers=headers)
        logging.info(
            'The page: {} get from {}'.format(
                page_url, 
                'cache' if response.from_cache else 'download online')
        )
        return response.json()
    except (ConnectionError, requests.exceptions.ConnectionError) as exc:
        logging.error(exc)
        return None


def get_pages_amount(url=SOLUTION_ATTEMPTS_URL):
    headers = {'User-agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'}
    try:
        response = requests.get(url, headers=headers)
        return response.json()['number_of_pages']
    except (ConnectionError, requests.exceptions.ConnectionError) as exc:
        logging.error(exc)
        return None


def load_solution_attempts(url=SOLUTION_ATTEMPTS_URL):
    attempts_pages_amount = get_pages_amount(url)
    for page_number in range(1, attempts_pages_amount+1):
        for solution_attempt in get_solution_attempts_page_json(page_number, url)['records']:
            yield solution_attempt


def get_midnighter_name_and_attempt_time(solution_attempt, midnighters_time_seconds_duration=18000):
    utc = pytz.utc
    utc_dt = utc.localize(datetime.utcfromtimestamp(solution_attempt['timestamp']))
    local_dt = utc_dt.astimezone(timezone(solution_attempt['timezone']))
    midnight = local_dt.replace(hour=0, minute=0, second=0)
    if 0 < (local_dt - midnight).seconds < midnighters_time_seconds_duration:
        return {'username': solution_attempt['username'], 'attempt_time': local_dt}


def get_midnighters_dict(solution_attempts):
    midnighters = defaultdict(list)
    for attempt in solution_attempts:
        midnighter = get_midnighter_name_and_attempt_time(attempt)
        if midnighter is not None:
            midnighters[midnighter['username']].append(midnighter['attempt_time'].
                                                       strftime('%d.%m.%Y %H:%M:%S %Z%z'))
    return midnighters


def print_midnighters(midnighters_dict):
    print("\nDevman midnighters who uploaded homeworks to devman between 0am and 5am:\n")
    for midnighter_name, midnighter_attemps_list in midnighters_dict.items():
        print(midnighter_name)
        for attempt in midnighter_attemps_list:
            print('\t{}'.format(attempt))


def set_cli_argument_parse():
    parser = argparse.ArgumentParser(description='Displays midnighters from devman.org')
    parser.add_argument('-cachetime', '--cache_time', default=600, type=int,
                        dest='cache_time', help='Set cache time interval')
    parser.add_argument('-clearcache', '--clear_cache', 
                        action='store_true', help='Clear cache file')
    return parser.parse_args()

if __name__ == '__main__':
    args = set_cli_argument_parse()

    if not os.path.exists('_cache'):
        os.mkdir('_cache')

    requests_cache.install_cache(
        '_cache/page_cache',
        backend='sqlite',
        expire_after=args.cache_time,
    )
    if args.clear_cache:
        requests_cache.clear()

    solution_attempts = load_solution_attempts(
        url=SOLUTION_ATTEMPTS_URL,
    )
    midnighters_dict = get_midnighters_dict(solution_attempts)
    print_midnighters(midnighters_dict)
