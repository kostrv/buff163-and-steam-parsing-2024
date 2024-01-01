import os
import json
from datetime import datetime
import asyncio

try: import aiohttp
except ImportError:
    os.system('pip install aiohttp')
    import aiohttp

try: from fake_useragent import UserAgent
except ImportError:
    os.system('pip install fake_useragent')
    from fake_useragent import UserAgent

try: import urllib.parse
except ImportError:
    os.system('pip install urllib')
    import urllib.parse

class GetBuffSteamData():
    def __init__(self):
        '''
        Инициализация и первичная настройка параметров.
        '''
        self.ua = UserAgent()
        self.timeout_time = 5

        # Инициализация файла с buffid предметов для дальнейшей работы по нему.
        self.buff_id_data = []
        with open('data\\buffids.txt', 'r', encoding='utf-8') as file: 
            for line in file:
                parts = line.strip().split(';') # [BUFF_ID, ITEM_NAME]
                self.buff_id_data.append(parts) 
        
        self.start_time = datetime.now()
    
    async def write_json(self, data: list[dict[str, str or None]]) -> None:
        '''
        Универсальная функция для записи json файла.
        '''
        with open(f'data\\buff_steam_parsed_data.json', "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=4)
        print(f'[INFO] Json written.\n')

    def create_parse_blocks(self, values_range: int = 150) -> list[list[str]]:
        '''
        Функция для разбития имеющейся базы предметов по блокам
        и тем самым, уменьшения одновременной нагрузки на buff163 частыми запросами.
        '''
        number_of_values: int = len(self.buff_id_data)
        main_block: list[list] = [[] for _ in range(number_of_values // values_range)]

        for block_index in range(len(main_block)): 
            start: int = block_index * values_range
            end: int = start + values_range
            main_block[block_index] = self.buff_id_data[start:end]
        
        # Обработка остатка значений
        remaining_items = number_of_values % values_range
        if remaining_items: 
            main_block.append(self.buff_id_data[-remaining_items:])
        
        return main_block
    
    async def get_item_data(self, session, item_name: str, item_buff_id: int, block_id: int, page: int = 1) -> dict[str, str or None]:
        '''
        Функция ассинхроной отправки запроса на индивидуальную страницу 
        API buff163 предмета и cбopa соответсвующих данных.
        Реализована обработка ошибок. 
        Данные будут возвращены в любом случае. 
        '''
        item_buff_api_url = f'https://buff.163.com/api/market/goods/sell_order?game=csgo&goods_id={item_buff_id}&page_num={page}&sort_by=default&mode=&allow_tradable_cooldown=1&_=1701713959228'
        item_buff_url = f'https://buff.163.com/goods/{item_buff_id}'

        item_data_dict = {
            'item_name': item_name,
            'item_BUFF_default_price': None,
            'item_BUFF_autobuy_price': None,
            'item_buff_url': item_buff_url,
            'item_STEAM_price': None,
            'item_steam_url': None
        }

        try:
            async with session.get(url=item_buff_api_url, headers=self.user_agent) as response:
                item_buff_data = await response.json()
               
            if item_buff_data.get("data").get("items") and item_buff_data.get("data").get("goods_infos"): 
                ''' 
                Учитываются только для значения, для которых доступна информация. 
                Простыми словами, если у предмета есть хотя бы один лот на продаже.
                '''
                # Поиск элементов на странице и сбор их данных.
                # Buff 
                item_data_dict['item_BUFF_default_price'] = float(item_buff_data.get("data").get("items")[0].get('price'))
                item_data_dict['item_BUFF_autobuy_price'] = float(item_buff_data.get("data").get("items")[0].get('lowest_bargain_price'))
                # Steam
                item_data_dict['item_STEAM_price'] = float(item_buff_data.get("data").get("goods_infos").get(str(item_buff_id)).get("steam_price_cny"))
                item_data_dict['item_steam_url'] = 'https://steamcommunity.com/market/listings/730/' + urllib.parse.quote(item_name)

                print(f'[INFO] PROCESSED [ITEM] {item_name}') 
                return item_data_dict
                
        except Exception as exception: 
            await asyncio.sleep(self.timeout_time)
            return await self.get_item_data(session=session, item_name=item_name, item_buff_id=item_buff_id, block_id=block_id) # Повторный запуск функции.
        
    async def get_block_data(self, session, block: list[str], block_id: int) -> list[dict[str: str or float]]:
        '''
        Функция для получения данных всех предметов в блоке.
        Парсинг предметов распределяется по потокам и производится ассинхронно.
        Неудачные данные не будут учитаны.
        '''
        task = [self.get_item_data(session=session, item_name=item_data[1], item_buff_id=item_data[0], block_id=block_id) for item_data in block]
        
        block_data = await asyncio.gather(*task)
        block_data = [item for item in block_data if item is not None]
        
        print(f'\n[INFO] PROCESSED BLOCK [ID] {block_id+1} [TIME] {str(datetime.now() - self.start_time)[:7]}')
        return block_data

    async def get_items_data(self) -> list[dict[str: str or float]]:
        '''
        Главная функция ассинхронного сбора данных.
        Все имеющиеся предметы разбиваются на блоки для распределения нагрузки.
        Создается единственный объект сессии и далее, производится ассинхронный парсинг 
        поочередно для всех предметов блока.
        '''
        main_data_block = self.create_parse_blocks()
        main_data = []
        
        async with aiohttp.ClientSession() as session:
            self.user_agent = {'User-Agent': self.ua.random}
            
            for block in main_data_block: 
                parsed_data_block = await self.get_block_data(session=session, block=block, block_id=main_data_block.index(block))
                for item_data in parsed_data_block:
                    main_data.append(item_data)
                await self.write_json(main_data)
            
        await session.close()
        return main_data
    
operator = GetBuffSteamData()

if __name__ == '__main__':
    main_data = asyncio.run(operator.get_items_data()) # Сбор данных.
    #operator.write_json(data=main_data) 
