import json
import os

try: import pandas as pd
except ImportError:
    os.system('pip install pandas')
    import pandas as pd
    
json_file_path = 'data\\buff_steam_parsed_data.json'
with open(json_file_path, 'r', encoding='utf-8') as file:
    data = json.load(file)

while True: 
    try: 
        usd_cny_exchange_rate = float(input('\nEnter the current exchange rate for 1 usd to cny: '))
        break
    except ValueError:
        print('The entered value is not a numeric value.')
        
df = pd.DataFrame(data)
if 'item_id' in df.columns: df.drop('item_id', axis=1, inplace=True)

def rate_usd_cny(cny_price: float, usd_cny_exchange_rate: float = usd_cny_exchange_rate) -> float:
    usd_price = round((cny_price / usd_cny_exchange_rate), 2)
    return usd_price

# Конвертация cny -> usd
df['item_BUFF_default_price'] = df['item_BUFF_default_price'].apply(rate_usd_cny)
if 'item_BUFF_autobuy_price' in df.columns: df['item_BUFF_autobuy_price'] = df['item_BUFF_autobuy_price'].apply(rate_usd_cny)
df['item_STEAM_price'] = df['item_STEAM_price'].apply(rate_usd_cny)

def return_steam_buff_price_ratio(row):
    try: return round((row['item_BUFF_default_price'] / row['item_STEAM_price']), 2)
    except ZeroDivisionError: return 

df['STEAM_BUFF_price_ratio'] = df.apply(return_steam_buff_price_ratio, axis=1)

df = df[df['item_BUFF_default_price'] >= 0.1]
df = df[df['STEAM_BUFF_price_ratio'].between(0.5, 0.75)]
df = df.sort_values(by='STEAM_BUFF_price_ratio', ascending=True)

print(df.info())

data_list = df.to_dict(orient="records")
with open(f'data\\data_to_read.json', "w", encoding="utf-8") as json_file:
    json.dump(data_list, json_file, ensure_ascii=False, indent=4)
        
