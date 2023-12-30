import os
import json
from datetime import datetime
from time import sleep

try: from selenium import webdriver
except ImportError:
    os.system(f'pip install selenium')
    from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try: from fake_useragent import UserAgent
except ImportError:
    os.system(f'pip install fake_useragent')
    from fake_useragent import UserAgent

class GetBuffSteamData():
    def __init__(self):
        '''
        Инициализация и первичная настройка параметров.
        '''
        self.ua = UserAgent()

        # Настройка вебдрайвера
        self.options = webdriver.ChromeOptions()
        self.options.add_argument(f"--{'User-Agent'}={self.ua.random}")
        #self.options.add_argument('--headless') # По желанию, если не хотите, чтобы был виден весь процесс.
        self.options.add_argument('--lang=en-US')
        # Отключение функций обнаружения автоматизации браузера.
        self.options.add_argument('--disable-blink-features=AutomationControlled') 
        self.options.add_experimental_option("excludeSwitches", ['enable-automation']) 
        self.options.add_experimental_option('useAutomationExtension', False) 

        self.driver = webdriver.Chrome(options=self.options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', { 
            'source': '''
                window.cdc_adoQpoasnfa76pfcZLmcfl_Array
                window.cdc_adoQpoasnfa76pfcZLmcfl_JSON
                window.cdc_adoQpoasnfa76pfcZLmcfl_Object
                window.cdc_adoQpoasnfa76pfcZLmcfl_Promise
                window.cdc_adoQpoasnfa76pfcZLmcfl_Proxy
                window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol
                '''
        })
        #self.driver.maximize_window()
        
        self.timeout_time = 15
        self.wait = WebDriverWait(self.driver, self.timeout_time)

        # Инициализация файла с buffid предметов для дальнейшей работы по нему.
        self.id_data = []
        with open('data\\buffids.txt', 'r', encoding='utf-8') as file: 
            for line in file:
                parts = line.strip().split(';') # [BUFF_ID, ITEM_NAME]
                self.id_data.append(parts) 
        
        self.start_time = datetime.now()
    
    def write_json(self, data: list[dict[str : str or None]]) -> None:
        '''
        Универсальная функция для записи json файла.
        '''
        with open(f'data\\buff_steam_parsed_data.json', "w", encoding="utf-8") as json_file: 
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print('\n[INFO] Json frited.\n')
        
    def close_driver(self) -> None:
        '''
        Функция завершения работы и отключения процессов вебдрайвера.
        '''
        self.driver.close()
        self.driver.quit()

    def get_item_data(self, item_id: int, item_name: str, item_buff_url: str, retry: int = 5) -> dict[str : str or None]:
        '''
        Функция отправки запроса на индивидуальную страницу buff163 предмета и cбopa соответсвующих данных.
        Реализована обработка ошибок. Данные будут возвращены в любом случае. 
        '''
        item_data_dict = { 
            'item_id': item_id + 1,
            'item_name': item_name,
            'item_BUFF_default_price': None,
            'item_buff_url': item_buff_url,
            'item_STEAM_price': None,
            'item_steam_url': None
        }
        
        try:
            item_buff_url = item_data_dict['item_buff_url']
            self.driver.get(item_buff_url)
            
            # Поиск элементов на странице и сбор их данных.
            item_buff_price = WebDriverWait(self.driver, self.timeout_time).until(
                EC.presence_of_element_located (
                    (By.XPATH, '//tbody[@class="list_tb_csgo"]//td[.//div[@style="display: table-cell;"] and @class="t_Left"]//strong[@class="f_Strong"]')
                )).text

            item_steam_price = WebDriverWait(self.driver, self.timeout_time).until(
                EC.presence_of_element_located (
                    (By.XPATH, '//div[@class="detail-summ"]//strong[@class="f_Strong"]//big')
                )).text

            item_steam_url = WebDriverWait(self.driver, self.timeout_time).until(
                EC.presence_of_element_located (
                    (By.XPATH, '//a[@target="_blank" and (i[@class="icon icon_arr_right_small"] or contains(text(), "View Steam market"))]')
                )).get_attribute('href')

            # Изменение ключей начального словаря, если данные были собраны успешно.
            item_data_dict['item_BUFF_default_price'] = float(item_buff_price[2:])
            item_data_dict['item_STEAM_price'] = float(item_steam_price)
            item_data_dict['item_steam_url'] = item_steam_url

        except NoSuchElementException or TimeoutException as exception:
            '''
            Примечание: реализована обработка основных ошибок, к которым может привести: 
            - Отсутствие интернет-соединения 
            - Блокировка доступа к странице 
            - Долгая подгрузка веб-элементов.
            '''
            sleep(self.timeout_time) 
            self.driver.refresh()
            if retry:  
                print(f'[INFO] retry={retry} => {item_buff_url}')
                return self.get_item_data(item_id=item_id, item_name=item_name, item_buff_url=item_buff_url, retry=(retry - 1)) # Повторный запуск функции.
            else:
                sleep(self.timeout_time*5)
                print(f'[INFO] Finaly got an error with parsing {item_name} item. [ERROR] {exception}')
                
        finally: return item_data_dict  # Окончательное возвращение данных, вне зависимости от успешности сбора.
        
    def fetch_main_data(self) -> list[dict[str : str or None]]:
        '''
        Главная функция cбopa данных.
        Скрипт проходится по скачанной базе id для предметов cs2 на buff163
        (если вы пропустили этот момент, скачать файл buffids.txt вы можете по ссылке: https://github.com/ModestSerhat/buff163-ids).
        Далее, для каждого предмета вызывается функция get_item_data c передачей основных аргументов 
        (id предмета, имя предмета, ссылка на buff163 c уникальным иденефикатором)
        для cбopa индивидуальных данных.
        '''
        main_data = []
        for item_id, item in enumerate(self.id_data): 
            # [BUFF_ID, ITEM_NAME]
            item_buff_url = f'https://buff.163.com/goods/{item[0]}?from=market#tab=selling'
            item_name = item[1]
            item_data_dict = self.get_item_data(item_id=item_id, item_name=item_name, item_buff_url=item_buff_url)
            main_data.append(item_data_dict)
            print(f'[PROCESSED] id {item_id + 1} [NAME] {item_name} [TIME] {str(datetime.now() - self.start_time)[:7]}')
            
            if (item_id + 1) % 100 == 0: self.write_json(data=main_data) # Резервное сохранение уже собранных данных через каждые 100 предметов.
        return main_data
    
operator = GetBuffSteamData()

if __name__ == '__main__':
    try: 
        main_data = operator.fetch_main_data() # Сбор данных.
        operator.write_json(data=main_data) # Сохранение данных
    finally: operator.close_driver()

