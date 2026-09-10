from crawler.utils import *
from time import sleep
import random
import json
import os

max_pages = get_max_pages()
all_house_id = []
all_house = []
failed_house_id = []

region = 1


loaded_id_list = []
with open("all_house_id.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            loaded_id_list.append(json.loads(line.strip()))

# ==============================================================
crawled_ids = set()

if os.path.exists("all_house_data.jsonl"):
    with open("all_house_data.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line.strip())
                if isinstance(data, dict) and "id" in data:
                    crawled_ids.add(data["id"])
                elif isinstance(data, dict) and "house_id" in data:
                    crawled_ids.add(data["house_id"])
                else:
                    crawled_ids.add(data)

if os.path.exists("failed_house_id.jsonl"):
    with open("failed_house_id.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                fail_id = json.loads(line.strip())
                crawled_ids.add(fail_id)

print(f"總共有 {len(loaded_id_list)}筆ID， 其中 {len(crawled_ids)}筆已經處理過")

# ==============================================================
with open("all_house_data.jsonl", "a", encoding="utf-8") as f_success, \
        open("failed_house_id.jsonl", "a", encoding="utf-8") as f_fail:

    for house_id in loaded_id_list:

        # 【斷點續爬關鍵判斷】
        if house_id in crawled_ids:

            continue

        print(f"開始爬取新ID: {house_id}")
        house = find_houseID(house_id)

        if house is not None:
            all_house.append(house)
            f_success.write(json.dumps(house, ensure_ascii=False) + "\n")
            f_success.flush()
        else:
            failed_house_id.append(house_id)
            f_fail.write(json.dumps(house_id, ensure_ascii=False) + "\n")
            f_fail.flush()

        # 隨機延時防封鎖
        sleep_time = random.uniform(1.0, 2.5)  # 591 建議間隔拉長一點比較安全
        print(f"等待 {sleep_time:.2f} 秒...")
        sleep(sleep_time)

print("所有未爬取的資料處理完畢！")

# ==============================================================
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
