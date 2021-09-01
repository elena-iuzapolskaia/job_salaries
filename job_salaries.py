import os
from itertools import count

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / 2
    if salary_from:
        multiplier_coef = 1.2
        return salary_from * multiplier_coef
    if salary_to:
        multiplier_coef = 0.8
        return salary_to * multiplier_coef


def predict_rub_salary_hh(vacancy):
    salary = vacancy.get('salary')
    if not salary or salary['currency'] != 'RUR':
        return None
    return predict_salary(salary['from'], salary['to'])


def predict_rub_salary_sj(vacancy):
    salary_from = vacancy['payment_from']
    salary_to = vacancy['payment_to']
    currency = vacancy['currency']
    is_payment_filled = salary_from or salary_to
    if not is_payment_filled or currency != 'rub':
        return None
    return predict_salary(salary_from, salary_to)


def process_stats_params(vacancies, site='hh'):
    vacancy_salaries = []
    for vacancy in vacancies:
        if site == 'HeadHunter':
            salary_func = predict_rub_salary_hh
        if site == 'SuperJob':
            salary_func = predict_rub_salary_sj
        salary = salary_func(vacancy)
        vacancy_salaries.append(salary)

    found_vacancies = len(vacancy_salaries)
    vacancy_salaries = list(filter(lambda salary: salary, vacancy_salaries))
    if len(vacancy_salaries) != 0:
        average_salary = sum(vacancy_salaries) / len(vacancy_salaries)
    else:
        average_salary = 0
    vacancies_processed = len(vacancy_salaries)
    return average_salary, vacancies_processed, found_vacancies


def get_site_stats(site='HeadHunter', language='Python'):
    if site == 'HeadHunter':
        url = 'https://api.hh.ru/vacancies'

        vacancies = []
        for page in count(0):

            payload = {
                'text': 'программист {0}'.format(language),
                'area': 1,
                'period': 3,
                'page': page,
                'per_page': 100,
            }

            response = requests.get(url, params=payload)
            response.raise_for_status()
            vacancies.extend(response.json()['items'])

            max_page_number = 19
            if page >= response.json()['pages'] or page >= max_page_number:
                break

    if site == 'SuperJob':
        api_url = 'https://api.superjob.ru/2.0/vacancies/'
        load_dotenv()
        vacancies = []
        for page in count(0):

            headers = {
                'X-Api-App-Id': os.environ['SJ_SECRET_KEY'],
            }

            payload = {
                'period': 30,
                'catalogues[0]': 48,
                't[0]': 4,
                'page': page,
                'count': 100,
                'keywords[0][keys]': language,
                'keywords[0][skwc]': 'particular',
                'keywords[0][srws]': 60,
            }

            response = requests.get(api_url, headers=headers, params=payload)
            response.raise_for_status()

            vacancies.extend(response.json()['objects'])

            if not response.json()['more']:
                break
    return process_stats_params(vacancies, site)


def create_stats():
    languages = [
        'Ruby', 'Swift', 'C', 'C#',
        'Java', 'JavaScript', 'PHP',
        'R', 'Python', 'C++',
        ]

    jobs_stats = {}
    for site in ('HeadHunter', 'SuperJob'):
        languages_stats = {}
        for language in languages:
            average_salary, vacancies_processed, found_vacancies = get_site_stats(site, language)
            languages_stats[language] = {
                'vacancies_found': found_vacancies,
                'vacancies_processed': vacancies_processed,
                'average_salary': int(average_salary),
            }
        jobs_stats[site] = languages_stats

    return jobs_stats


def create_ascii_table(site, stats):
    table_rows = []
    table_rows.append([
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата',
        ])
    for language in stats.keys():
        table_row = [
            language,
            stats[language]['vacancies_found'],
            stats[language]['vacancies_processed'],
            stats[language]['average_salary'],
        ]
        table_rows.append(table_row)
    table = AsciiTable(table_rows)
    table.title = '{0} Moscow'.format(site)
    return table.table


def main():
    sites_stats = create_stats()
    for site in sites_stats.keys():
        ascii_table = create_ascii_table(site, sites_stats[site])
        print(ascii_table, end='\n\n')


if __name__ == '__init__':
    main()