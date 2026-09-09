from crawler.utils import *
from time import sleep
import random
import json

max_pages = get_max_pages()
all_house_id = []
all_house = []
failed_house_id = []

region = 1


loaded_id_list = []


print("開始收集房屋ID...")
with open("all_house_id.jsonl", "w", encoding="utf-8") as f:
    for page in range(1, max_pages+1):
        house_id_list = find_house(page=page, region=region)
        for house_id in house_id_list:
            f.write(json.dumps(house_id, ensure_ascii=False) + "\n")

        sleep_time = random.uniform(0.5, 1)
        print(f"等待{sleep_time:.2f} 秒...")
        sleep(sleep_time)

print("\n開始讀取ID 並爬取房屋詳細資料...")


with open("all_house_id.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            line_data = json.loads(line.strip())
            loaded_id_list.append(line_data)

with open("all_house_data.jsonl", "a", encoding="utf-8") as f_success, \
        open("failed_house_id.jsonl", "a", encoding="utf-8") as f_fail:
    for house_id in loaded_id_list:
        house = find_houseID(house_id)

        if house is not None:
            all_house.append(house)
            f_success.write(json.dumps(house, ensure_ascii=False) + "\n")
        else:
            failed_house_id.append(house_id)
            f.write(json.dumps(failed_house_id, ensure_ascii=False) + "\n")
            f_fail.flush()

        sleep_time = random.uniform(0.5, 1)
        print(f"等待{sleep_time:.2f} 秒...")
        sleep(sleep_time)

print("爬蟲完成!!")


# with open("failed_house_id.json", "w", encoding="utf-8") as f:
#     json.dump(failed_house_id, f, ensure_ascii=False)

print(f"總共取得 {len(all_house)}間房屋")
