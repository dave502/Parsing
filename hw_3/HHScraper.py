import requests
from bs4 import BeautifulSoup as bs
import re
import urllib.parse as urlparse
from urllib.parse import parse_qs
import pandas as pd
from hh_mongo import HHmongo

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
#<string>:1: DeprecationWarning: count is deprecated. Use Collection.count_documents instead.
#D:/DEV/PythonUdemy/PychermProjects/Parsing/hw_1/hw_2/hh.py:129: DeprecationWarning: count is deprecated. Use Collection.count_documents instead.
#  из них новых - {db.get_new_documents().count()}

class HHScraper:
    __headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'}
    __url = 'https://hh.ru/'
    __params = {}

    def __init__(self, db):
        self.__db = db

    def __input_vacancy_text(self):
        return input('Please enter vacancy key word: ')

    def __get_employer(self, employer_text: str):
        """returns valid employer name"""
        if employer_text:
            return employer_text.replace(u'\xa0', ' ')
        else:
            return None

    def __get_location(self, location_text: str):
        """returns valid location name"""
        if location_text:
            return location_text.split()[0]
        else:
            return None

    def __get_salary_min_max(self, salary_text: str) -> list:
        """returns the list with min and max salaries"""
        salary_min = salary_max = None
        if salary_text:
            salary_text = re.sub(r'\s', '', salary_text)
            start_max = salary_text.find('до')
            start_min = salary_text.find('от')
            # если сначала 'до' - salary_max присваиваем всё число из строки
            if start_max > start_min:
                salary_max = int(salary_text[start_max + len('до'):re.search(r'\d+', salary_text).end()])
            else:  # в остальных слуаях ищем все числа, первое - минимальная зарплата, второе - максимальная
                digits = re.findall(r'\d+', salary_text)
                salary_min = int(digits[0]) if len(digits) > 0 else None
                salary_max = int(digits[1]) if len(digits) == 2 else None
        return [salary_min, salary_max]

    def __get_salary_currency(self, salary_text: str) -> str:
        salary_currency = None
        if salary_text:
            # получаем последнее "слово" в строке
            salary_currency_text = re.split('\s+', salary_text)[-1]
            # если "слово" начинается не с цифр - верояно это - валюта
            if re.match(r'\D+', salary_currency_text).end():
                salary_currency = salary_currency_text
        return salary_currency


    def __scrape_one_page(self, url: str) -> dict:
        """returns dictionary {
            'jobs': dictionary with jobs from the webpage,
            'next_url': int with next page url link
            }
        """
        response = requests.get(url, params=self.__params, headers=self.__headers)
        soup = bs(response.text, 'html.parser')

        job_div_list = soup.findAll('div', {'class': "vacancy-serp-item"})

        job_data_list = []
        for job_div in job_div_list:
            job_data = {}
            job_title_link = job_div.find('a', {'data-qa': 'vacancy-serp__vacancy-title'})
            job_data['title'] = job_title_link.getText() if job_title_link else None
            job_data['link'] = job_title_link.get('href') if job_title_link else None
            job_data['employer'] = self.__get_employer(
                job_div.find('a', {'data-qa': 'vacancy-serp__vacancy-employer'}).getText())
            job_data['location'] = self.__get_location(
                job_div.find('span', {'data-qa': "vacancy-serp__vacancy-address"}).getText())
            span_salary = job_div.find('span', {'data-qa': "vacancy-serp__vacancy-compensation"})
            job_data['salary_min'], job_data['salary_max'] = self.__get_salary_min_max(span_salary.getText()) \
                if span_salary else [None, None]
            job_data['salary_currency'] = self.__get_salary_currency(span_salary.getText()) if span_salary else None
            job_data['source_vacancy_id'] = re.findall(r'vacancy/([^/?]+)?', job_data['link'])[0]
            job_data['source'] = self.__url
            job_data_list.append(job_data)

            #**************************** запись вакансии в базу данных ******************************
            db.insert_unique_document(job_data, 'source_vacancy_id')

        # get Next button and next page number from its link
        next_page = None
        button_next = soup.findAll('a', {'data-qa': "pager-next"})
        if button_next:
            parsed = urlparse.urlparse(button_next[0].get('href'))
            next_page = parse_qs(parsed.query)['page'][0]
        return {'jobs': job_data_list, 'next_page': next_page}

    def get_jobs_list(self):
        """Gets jobs with inputted keyword from the site"""
        job_data_list = []
        self.__params = {'text': self.__input_vacancy_text(), 'items_on_page': 20}
        scraped_page_url = self.__url + 'search/vacancy'
        # убрать все признаки новых документов перед записью в базу данных
        self.__db.reset_new_flags()
        while True:
            scraped_page_data = self.__scrape_one_page(scraped_page_url)
            job_data_list.extend(scraped_page_data['jobs'])
            if scraped_page_data['next_page']:
                self.__params['page'] = scraped_page_data['next_page']
            else:
                break

        job_df = pd.DataFrame(job_data_list)
        job_df.to_json("job_list.json", default_handler=str)
        return job_data_list


# получаем ссылку на БД
db = HHmongo()
scraper = HHScraper(db)
#scraper.get_jobs_list()

print(f'Всего в базе данных {len(db.get_all_documents_list())} ваканcий, \
из них новых - {db.get_new_documents().count()}')

# вывести на экран вакансии с зарплатой больше указанной
needed_salary = int(input('Введите желаемую зарплату: '))
db.print_table(db.get_documents_with_higher_salary(needed_salary))

# вывести на экран новые вакансии
#db.print_table(db.get_new_documents())


