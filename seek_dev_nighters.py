import requests
import requests_cache
import logging
import argparse
import os
from datetime import datetime
from pytz import timezone
import pytz
from collections import defaultdict


logging.basicConfig(level=logging.INFO)


def get_solution_attempts_page_json(page_number, url='http://devman.org/api/challenges/solution_attempts/'):
    headers = {'User-agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'}
    try:
        page_url = '{}?page={}'.format(url, page_number)
        response = requests.get(page_url, headers=headers)
        logging.info('The page: {} get from {}'.format(page_url, 'cache' if response.from_cache else 'download online'))
        return response.json()
    except (ConnectionError, requests.exceptions.ConnectionError) as exc:
        logging.error(exc)
        return None


def get_number_of_pages(url='http://devman.org/api/challenges/solution_attempts/'):
    headers = {'User-agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'}
    try:
        response = requests.get(url, headers=headers)
        return response.json()['number_of_pages']
    except (ConnectionError, requests.exceptions.ConnectionError) as exc:
        logging.error(exc)
        return None


def load_attempts(url='http://devman.org/api/challenges/solution_attempts/'):
    pages = get_number_of_pages(url)
    for page_number in range(1, pages+1):
        for solution_attempt in get_solution_attempts_page_json(page_number, url)['records']:
            yield solution_attempt


def get_midnighter_name_and_attempt_time(solution_attempt, midnighters_time_seconds_duration=18000):
    # solution_attempt like this {'username': 'noc0st51', 'timestamp': 1513068516.112667, 'timezone': 'Europe/Moscow'}
    # midnighters time duration is 3 hours or
    utc = pytz.utc
    utc_dt = utc.localize(datetime.utcfromtimestamp(solution_attempt['timestamp']))
    local_dt = utc_dt.astimezone(timezone(solution_attempt['timezone']))
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    midnight = local_dt.replace(hour=0, minute=0, second=0)

    if 0 < (local_dt - midnight).seconds < midnighters_time_seconds_duration:
        return {'username': solution_attempt['username'], 'attempt_time': local_dt}


def get_midnighters():
    midnighters = defaultdict(list)
    for attempt in load_attempts():
        # midnighter_name, attempt_time = (None, None)
        midnighter = get_midnighter_name_and_attempt_time(attempt)
        if midnighter is not None:
            midnighters[midnighter['username']].append(midnighter['attempt_time'].strftime('%d.%m.%Y %H:%M:%S %Z%z'))
            print(midnighter['username'], midnighter['attempt_time'].strftime('%d.%m.%Y %H:%M:%S %Z%z'))


def print_midnighters():
    pass


def set_cli_argument_parse():
    parser = argparse.ArgumentParser(description="Displays 20 the most popular repositories")
    parser.add_argument("-cachetime", "--cache_time", default=600, type=int,
                        dest="cache_time", help="Set cache time interval")
    parser.add_argument('-clearcache', '--clear_cache', action='store_true', help='Clear cache file')
    return parser.parse_args()

if __name__ == '__main__':
    cli_args = set_cli_argument_parse()

    if not os.path.exists('_cache'):
        os.mkdir('_cache')
    requests_cache.install_cache('_cache/page_cache', backend='sqlite',
                                 expire_after=cli_args.cache_time)
    if cli_args.clear_cache:
        requests_cache.clear()

    print(get_number_of_pages())
    att = get_solution_attempts_page_json(3)['records']
    print(load_attempts())

    midnighters = defaultdict(list)
    for i in load_attempts():
        # midnighter_name, attempt_time = (None, None)
        midnighter = get_midnighter_name_and_attempt_time(i)
        if midnighter is not None:
            midnighters[midnighter['username']].append(midnighter['attempt_time'].strftime('%d.%m.%Y %H:%M:%S %Z%z'))
            print(midnighter['username'], midnighter['attempt_time'].strftime('%d.%m.%Y %H:%M:%S %Z%z'))
        # print(get_midnighters(i))
    # print(att[1]['records'])

    print(midnighters)