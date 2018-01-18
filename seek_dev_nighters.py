import requests
import logging
from datetime import datetime
from pytz import timezone
from collections import defaultdict

logging.basicConfig(level=logging.ERROR)


def get_solution_attempts_page_json(page_number, url):
    try:
        response = requests.get(url, params={'page': page_number})
        if response.ok:
            return response.json()
    except (ConnectionError, requests.exceptions.ConnectionError) as exc:
        logging.error(exc)
        return None


def load_solution_attempts(url):
    page_number = 1
    while page_number:
        response = get_solution_attempts_page_json(page_number, url)
        for solution_attempt in response['records']:
            yield solution_attempt
        page_number += 1
        if page_number > response['number_of_pages']:
            break


def get_midnighter_name_and_attempt_time(
        solution_attempt, midnighters_time_seconds_duration=18000):
    local_dt = datetime.fromtimestamp(solution_attempt['timestamp'],
                                      timezone(solution_attempt['timezone']))
    midnight = local_dt.replace(
        hour=0,
        minute=0,
        second=0
    )
    if 0 < (local_dt - midnight).seconds < midnighters_time_seconds_duration:
        return {
            'username': solution_attempt['username'],
            'attempt_time': local_dt
        }


def get_midnighters_dict(solution_attempts):
    midnighters = defaultdict(list)
    for attempt in solution_attempts:
        attempt_dict = get_midnighter_name_and_attempt_time(attempt)
        if attempt_dict is not None:
            attempt_time = attempt_dict['attempt_time'].strftime(
                '%d.%m.%Y %H:%M:%S %Z%z')
            midnighters[attempt_dict['username']].append(attempt_time)
    return midnighters


def print_midnighters(midnighters_dict):
    print("\nDevman midnighters who uploaded homeworks "
          "to devman between 0am and 5am:")
    for midnighter_name, midnighter_attemps_list in midnighters_dict.items():
        print('\n{}'.format(midnighter_name))
        for attempt in midnighter_attemps_list:
            print('\t{}'.format(attempt))


if __name__ == '__main__':
    solution_attempts = load_solution_attempts(
        url='http://devman.org/api/challenges/solution_attempts/', )
    midnighters_dict = get_midnighters_dict(solution_attempts)
    print_midnighters(midnighters_dict)
