import os
import json
from datetime import datetime
from time import sleep

try: import requests
except ImportError:
    os.system(f'pip install requests')
    import requests

try: from fake_useragent import UserAgent
except ImportError:
    os.system(f'pip install fake_useragent')
    from fake_useragent import UserAgent

try: import urllib.parse
except ImportError:
    os.system(f'pip install urllib')
    import urllib.parse

class GetBuffSteamData():
    def __init__(self):
        '''
        Инициализация и первичная настройка параметров.
        '''
        self.ua = UserAgent()
        self.header = {'User-Agent': self.ua.random}
        self.timeout_time = 15

        # Инициализация файла с buffid предметов для дальнейшей работы по нему.
        self.id_data = []
        with open('data\\buffids.txt', 'r', encoding='utf-8') as file: 
            for line in file:
                parts = line.strip().split(';') # [BUFF_ID, ITEM_NAME]
                self.id_data.append(parts) 
        
        self.start_time = datetime.now()
    
    def write_json(self, data: list[dict[str : str | float | None]]) -> None:
        '''
        Универсальная функция для записи json файла.
        '''
        with open(f'data\\buff_steam_parsed_data.json', "w", encoding="utf-8") as json_file: 
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print('\n[INFO] Json frited.\n')

    def get_item_data(self, item_id: int, item_name: str, item_buff_id: int, page: int = 1, retry: int = 5) -> dict[str : str | float | None]:
        '''
        Функция отправки запроса на индивидуальную страницу API buff163 предмета и cбopa соответсвующих данных.
        Реализована обработка ошибок. Данные будут возвращены в любом случае. 
        '''
        item_buff_api_url = f'https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id={item_buff_id}&page_num={page}&sort_by=default&mode=&allow_tradable_cooldown=1&_=1701713959228'
        item_buff_url = f'https://buff.163.com/goods/{item_buff_id}' 
        
        item_data_dict = { 
            'item_id': item_id + 1,
            'item_name': item_name,
            'item_BUFF_default_price': None,
            'item_BUFF_autobuy_price': None,
            'item_buff_url': item_buff_url,
            'item_STEAM_price': None,
            'item_steam_url': None
        }
        
        try:
            request = requests.get(url=item_buff_api_url, headers=self.header)
            item_buff_data = json.loads(request.text)
            
            # Поиск элементов на странице и сбор их данных.
            # Buff 
            item_data_dict['item_BUFF_default_price'] = float(item_buff_data.get("data").get("items")[0].get('price'))
            item_data_dict['item_BUFF_autobuy_price'] = float(item_buff_data.get("data").get("items")[0].get('lowest_bargain_price'))
            
            # Steam 
            item_data_dict['item_STEAM_price'] = float(item_buff_data.get("data").get("goods_infos").get(str(item_buff_id)).get("steam_price_cny"))
            item_data_dict['item_steam_url'] = 'https://steamcommunity.com/market/listings/730/' + urllib.parse.quote(item_name)
            
        except Exception as exception:
            sleep(self.timeout_time) 
            if retry:  
                print(f'[INFO] retry={retry} => {item_buff_api_url}')
                return self.get_item_data(item_id=item_id, item_name=item_name, item_buff_id=item_buff_id, retry=(retry - 1)) # Повторный запуск функции.
            else:
                sleep(self.timeout_time*4)
                print(f'[INFO] Finaly got an error with parsing {item_name} item. [ERROR] {exception}')
                
        finally: return item_data_dict  # Окончательное возвращение данных, вне зависимости от успешности сбора.
        
    def fetch_main_data(self) -> list[dict[str : str | float | None]]:
        '''
        Главная функция cбopa данных.
        Скрипт проходится по скачанной базе id для предметов cs2 на buff163
        (если вы пропустили этот момент, скачать файл buffids.txt вы можете по ссылке: https://github.com/ModestSerhat/buff163-ids).
        Далее, для каждого предмета вызывается функция get_item_data c передачей основных аргументов 
        (id предмета, имя предмета, уникальный идентефикатор buff163) для cбopa индивидуальных данных.
        '''
        main_data = []
        for item_id, item in enumerate(self.id_data): 
            # [BUFF_ID, ITEM_NAME]
            item_data_dict = self.get_item_data(item_id=item_id, item_name=item[1], item_buff_id=item[0])
            main_data.append(item_data_dict)
            print(f'[PROCESSED] id {item_id + 1} [NAME] {item[1]} [TIME] {str(datetime.now() - self.start_time)[:7]}')
            
            if (item_id + 1) % 100 == 0: self.write_json(data=main_data) # Резервное сохранение уже собранных данных через каждые 100 предметов.
        return main_data

operator = GetBuffSteamData()

if __name__ == '__main__':
    main_data = operator.fetch_main_data() # Сбор данных.
    operator.write_json(data=main_data) # Сохранение данных.
