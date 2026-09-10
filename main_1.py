from crawler.utils import *
from time import sleep
import random
import json
import os

loaded_id_list = []

# 嘗試讀取存在的房屋ID
if os.path.exists("all_house_id.jsonl"):

    with open("all_house_id.jsonl", "r", encoding="utf-8") as f:

        for line in f:

            if line.strip():

                loaded_id_list.append(
                    json.loads(line.strip())
                )

# 如果沒有ID則開始爬取
if len(loaded_id_list) == 0:

    print("目前沒有房屋 ID")
    print("開始爬取房屋 ID...")

    max_pages = get_max_pages()

    with open("all_house_id.jsonl", "a", encoding="utf-8") as f:

        for page in range(1, max_pages + 1):

            print(f"正在爬取房屋列表第{page}頁")

            house_id_list = find_house(
                region=1,
                keyword=None,
                page=page,
                kind=(1, 2, 3, 4)
            )

            if not house_id_list:
                print(f"第 {page} 頁沒有取得 ID")
                continue

            # 寫入 JSONL
            for house_id in house_id_list:
                f.write(json.dumps(house_id, ensure_ascii=False) + "\n")
                loaded_id_list.append(house_id)

            f.flush()

            print(f"第 {page} 頁取得 "f"{len(house_id_list)} 筆 ID")
            sleep_time = random.uniform(1.0, 2.5)
            print(f"等待 {sleep_time:.2f} 秒...")
            sleep(sleep_time)

    print(f"房屋 ID 取得完成，總共 {len(loaded_id_list)} 筆")

else:

    print(f"已存在房屋 ID，共 {len(loaded_id_list)} 筆")
