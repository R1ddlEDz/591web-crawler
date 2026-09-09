from crawler.utils import *
from time import sleep
import random
import json

max_pages = get_max_pages()
all_house_id = []
all_house = []
failed_house_id = []

for page in range(1, max_pages+1):
    house_id_list = find_house(page)
    all_house_id.extend(house_id_list)
    sleep_time = random.uniform(0.5, 1)
    print(f"等待{sleep_time:.2f} 秒...")
    sleep(sleep_time)

with open("all_house_id.json", "w", encoding="utf-8") as f:
    json.dump(all_house_id, f, ensure_ascii=False)

with open("all_house_id.json", "r", encoding="utf-8") as f:
    loaded_id_list = json.load(f)

for house_id in loaded_id_list:
    house = find_houseID(house_id)
    if house is not None:
        all_house.append(house)
    else:
        failed_house_id.append(house_id)
    sleep_time = random.uniform(0.5, 1)
    print(f"等待{sleep_time:.2f} 秒...")
    sleep(sleep_time)

with open("all_house_data.json", "w", encoding="utf-8") as f:
    json.dump(all_house, f, ensure_ascii=False)

with open("failed_house_id.json", "w", encoding="utf-8") as f:
    json.dump(failed_house_id, f, ensure_ascii=False)

print(f"總共取得 {len(all_house)}間房屋")
