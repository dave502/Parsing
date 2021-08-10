from pymongo import MongoClient


class HHmongo:

    def __init__(self):
        self.__client = MongoClient('localhost', 27017)
        self.__db = self.__client['jobs']
        self.hh_jobs = self.__db.hh_jobs

    # ************************* 1.Развернуть у себя на компьютере/виртуальной машине/хостинге MongoDB и реализовать функцию, записывающую собранные вакансии в созданную БД.
    
    def insert_many(self, list_of_jobs: list):
        """внести все документы из списка в базу данных"""
        return self.hh_jobs.insert_many(list_of_jobs)

    # ************************* 3. Написать функцию, которая будет добавлять в вашу базу данных только новые вакансии с сайта *********************
    
    def insert_unique_document(self, document: dict, unique_key: str):
        """внести в базу данных документ при условии, что в базе данных
        отсутвует документ с таким же значением указанного поля unique_key
        """
        # можно, конечно, сравнивать все поля документов, но сравнивать одно поле рациональнее
        if self.hh_jobs.find({unique_key: document[unique_key]}).count() == 0:
            document['new'] = 1
            self.hh_jobs.insert_one(document)
            
   # ************************* Написать функцию, которая производит поиск и выводит на экран вакансии с заработной платой больше введённой суммы. *********************

    def get_documents_with_higher_salary(self, salary: int):
        """
        """
        return self.hh_jobs.find({'$or': [{'salary_min': {'$ne': None, '$gte': salary}},
                                          {'salary_min': {'$eq': None}, 'salary_max': {'$gte': salary}}]})

    def get_all_documents_list(self) -> list:
        """вернуть всё содержимое базы данных в виде списка"""
        return list(self.hh_jobs.find({}))

    def reset_new_flags(self):
        """Сбросить признак новой записи у всех документов"""
        self.hh_jobs.update_many({}, {'$set': {'new': 0}})

    def get_new_documents(self):
        """Получить все новые документы"""
        return self.hh_jobs.find({'new': 1})

    def print_table(self, cursor):
        """вывести таблицу курсора на экран"""
        # частично позаимствованная мною идея печати словарей

        #col_list = self.hh_jobs.find_one().keys()
        # нерациональное получение заголовков!
        col_list = self.get_all_documents_list()[1].keys()  # 1st row = header
        table = [col_list]
        for item in cursor:
            table.append([str(item[col] if item[col] is not None else '') for col in col_list])
        col_size = [max(map(len, col)) for col in zip(*table)]
        format_str = ' | '.join(["{{:<{}}}".format(i) for i in col_size])
        table.insert(1, ['-' * i for i in col_size])
        for item in table:
            print(format_str.format(*item))
