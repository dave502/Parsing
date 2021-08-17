from selenium import webdriver
driver = webdriver.Chrome(executable_path='chromedriver.exe')
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from pymongo import MongoClient
import pandas as pd
pd.set_option('display.max_columns', 5)
pd.set_option('display.max_rows', 100)
pd.set_option('display.width', 1000)

def get_id_from_url(url: str) -> str:
    """
    get id from url string:
    https://e.mail.ru/inbox/0:16286890521186820940:0/?back=1  ->  '0:16286890521186820940:0'
    """
    id_start = url.find('inbox/') + len('inbox/')
    id_end = url.find('/?')
    return url[id_start:id_end]

# инициализация Mongo
db_client = MongoClient('localhost', 27017)
db = db_client['mail_ru']
db_inbox = db.inbox
# очистка БД
db_inbox.drop()

# получение страницы авторизации
url = 'https://mail.ru/'
login = 'study.ai_172@mail.ru'
password = 'NextPassword172!?'
driver.get(url)

# авторизация
input_login = driver.find_element_by_class_name('email-input')
button_login = driver.find_element_by_xpath("//button[@*='enter-password']")
input_login.send_keys(login)
button_login.click()

# после логина ждём появления поля ввода пароля
wait = WebDriverWait(driver, 120)
input_password_wait = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'password-input')))
button_password_wait = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@*='login-to-mail']")))
input_password_wait.send_keys(password)
button_password_wait.click()

letters_list = []
new_letters_found = True

# пока есть новые письма скроллим вниз
while new_letters_found:
  # ждём пока на странице появятся все элементы писем с классом  js-letter-list-item
  letters_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-letter-list-item'))) 
  new_letters_found = False # полагаем, что новых писем нет
  # для всех отображаемых элементов писем цикл
  for letter_element in letters_elements:

      # получаем id письма из ссылки
      letter_href = letter_element.get_attribute('href')
      letter_id = get_id_from_url(letter_href)

      # если в полученых письмах этого id нет, значит письмо новое
      ## вероятно, правильнее было бы брать последние 7(?) новых элементов из letters_elements,
      ## это бы ускорило работу и отпала бы необходимость проверять уникальность letter_id
      if letter_id in [letter['_id'] for letter in letters_list]: #[-20:]
        continue
      else:
        new_letters_found = True

      # получаем состояние открытых окон
      windows_before = driver.window_handles
      # открываем письмо в новой вкладке
      driver.execute_script(f'window.open("{letter_href}","_blank");')
      # ждём пока вкладка с письмом откроется
      # ожидалось, что WebDriverWait будет ждать полной загрузки страницы, но всё равно элементы в новой вкладке не успевают загрузиться
      WebDriverWait(driver, 120).until(EC.new_window_is_opened(windows_before))
      # хендлер новой вкладки
      window_after = driver.window_handles[1]
      # переключаемся на новую вкладку
      driver.switch_to.window(window_after)
      # читаем необходимы данные, ожидая пока они загрузятся
      letter_data = {}
      letter_data['_id'] = letter_id
      subject_wait = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'thread__subject')))
      letter_data['subject'] = subject_wait.text
      sender_wait = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'letter-contact')))
      letter_data['sender_name'] = sender_wait.text
      date_wait = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'letter__date')))
      letter_data['date'] = date_wait.text
      body_wait = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'letter-body__body')))
      letter_data['body'] = body_wait.get_attribute('innerHTML')
      print(f'прочитано письмо {letter_data["subject"]}')
      # записываем данные письма в список писем
      letters_list.append(letter_data)

      # запись в БД
      try:
        db_inbox.update_one({'_id': letter_id}, {"$set": letter_data}, upsert=True)
      except Exception as e:
        print(f"Ошибка записи в базу данных: {e}")

      # закрываем вкладку с письмом
      driver.close()
      # переключаемся на вкладку со списком писем
      driver.switch_to.window(windows_before[0])

  # скроллим до последнего элемента и переходим в начало цикла для обработки новых загруженных писем
  action_scroll_down = ActionChains(driver)
  action_scroll_down.move_to_element(letters_elements[-1])
  action_scroll_down.perform()

print(f'All {len(letters_list)} letters are saved')

# показать
df = pd.DataFrame(db_inbox.find())
print(df)
