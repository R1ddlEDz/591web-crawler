import requests
from bs4 import BeautifulSoup as bs
import json
from datetime import datetime, timedelta
import re
from time import sleep
import random
import os


def get_text(soup, selector):
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else None


def find_house(region=1, keyword=None, page=1, kind=(1, 2, 3, 4)):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = "https://rent.591.com.tw/list?"
    job_params = {
        "region": 1,
        "page": 1,
        "kind": (1, 2, 3, 4)
        # keyword : "",
    }

    if keyword is not None:
        job_params['keyword'] = keyword
    if region != 1:
        job_params['region'] = region
    if page != 1:
        job_params['page'] = page
    if kind != "1,2,3,4":
        job_params['kind'] = kind

    res = requests.get(url, headers=custom_headers, params=job_params)
    if res.status_code == 200:
        try:
            # print("成功取得房屋列表")
            soup = bs(res.text, 'lxml')
            house_list = soup.select("main > div > div.item[data-id]")
            update_date = soup.select(
                "div.item-info-txt.role-name >span.line:nth-child(2)")
            update_list = [tag.get_text(strip=True) for tag in update_date]
            update_house_list = []
            now = datetime.now()
            for date in update_list:
                if "小時內更新" in date:
                    filtered_update_time = re.search(
                        r'(\d+)\s*小時內更新', date)
                    if filtered_update_time:
                        hours = int(filtered_update_time.group(1))
                        updat_date = (now - timedelta(hours=hours)
                                      ).strftime("%Y-%m-%d")
                        update_house_list.append(updat_date)
                    else:
                        None
                elif "天前更新" in date:
                    filtered_update_time = re.search(
                        r'(\d+)\s*天前更新', date)
                    if filtered_update_time:
                        days = int(filtered_update_time.group(1))
                        updat_date = (now - timedelta(days=days)
                                      ).strftime("%Y-%m-%d")
                        update_house_list.append(updat_date)
                    else:
                        None
                elif "昨日更新" in date:
                    updat_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
                    update_house_list.append(updat_date)

                elif "分鐘內更新" in date:
                    filtered_update_time = re.search(
                        r'(\d+)\s*分鐘內更新', date)
                    if filtered_update_time:
                        min = int(filtered_update_time.group(1))
                        updat_date = (now - timedelta(minutes=min)
                                      ).strftime("%Y-%m-%d")
                        update_house_list.append(updat_date)
            house_id_list = [
                item.get("data-id")
                for item in house_list
            ]
            house_zip = []

            for house_id_1, update_list_1 in zip(house_id_list, update_house_list):
                house_zip.append({
                    "house_id": house_id_1,
                    "history_date": update_list_1
                })
            # return house_id_list
            # return update_house_list
            return house_zip
            # print(type(main_content))
        except Exception as e:
            print(e)
            print(res.text[:200])
    # print(res.status_code)
    # print(data)

# find_house(region=1)


def get_max_pages(region=1, keyword=None, page=1, kind=(1, 2, 3, 4)):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = "https://rent.591.com.tw/list?"
    job_params = {
        "region": 1,
        "page": 1,
        # keyword : "",
        "kind": (1, 2, 3, 4)
    }
    max_pages = 99999

    if keyword is not None:
        job_params['keyword'] = keyword
    if region != 1:
        job_params['region'] = region
    if page != 1:
        job_params['page'] = page
    if kind != "1,2,3,4":
        job_params['kind'] = kind

    res = requests.get(url, headers=custom_headers, params=job_params)
    soup = bs(res.text, 'lxml')

    if max_pages == 99999:
        max_pages = round(int(soup.select_one(
            "#__nuxt > div:nth-child(4) > div.list-wrapper > main > div.list-sort > p > strong").get_text(strip=True).replace(",", "")) / 30)
        max_pages_bp = soup.select_one(
            "#__nuxt > div:nth-child(4) > div.list-wrapper > main > div.list-sort > p > strong").get_text(strip=True).replace(",", "")
    # print(f"region, keyword, page, kind")
    # print(max_pages_bp)
    return max_pages


def find_houseID(id):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = f"https://rent.591.com.tw/{id}"

    # print(res.status_code)

    try:
        res = requests.get(url, headers=custom_headers)
        status_code = res.status_code
        # main_content = soup.select_one("#__nuxt > div:nth-child(4) > div.list-wrapper > main > div:nth-child(5) > div")
        if res.status_code == 200:
            print(f"成功取得{id}的資料")
            soup = bs(res.text, 'lxml')
            title = get_text(soup, ".title > h1")
            house_id = get_text(
                soup, "#__nuxt > section:nth-child(1) > section > section.crumbs > span")[1:]

            pattern = get_text(soup, ".pattern > span[data-v-b5702979]")
            rent = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.house-price > span > strong")

            identity_requirement = None
            for item in soup.select("div.desc-item"):
                label_span = item.select_one("span.desc-label")
                label = label_span.get_text(strip=True) if label_span else None
                # print(label)
                if label and "身份要求" in label:
                    value = item.select_one("span.desc-value")

                    if value:
                        identity_requirement = value.get_text(strip=True)
                    break

            # sqm = get_text(soup, "div.pattern > span.inline-flex-row")

            sqm_span = next((span for span in soup.select(
                            "div.pattern > span.inline-flex-row") if "坪" in span.get_text(strip=True)), None)
            sqm = sqm_span.get_text(strip=True) if sqm_span else None
            floor = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.pattern > span:nth-child(5)")

            address = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.address > p:nth-child(1) > span.load-map > div")
            facility = soup.select_one(
                "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div.facility")
            if facility:
                facility_list = [
                    x.get_text(strip=True)
                    for x in facility.select(":scope > dl:not(.del)")
                ]
            else:
                facility_list = []
            rental_period = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div:nth-child(2) > div > div > div:nth-child(1) > span.desc-value")
            # pet = get_text(
            #     soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div:nth-child(2) > div > div > div:nth-child(4) > span.desc-value")
            pet_span = next((span for span in soup.select(
                "span.desc-value") if "寵物" in span.get_text(strip=True)), None)
            pet = pet_span.get_text(strip=True) if pet_span else None

            cook_span = next((span for span in soup.select(
                "span.desc-value") if "開伙" in span.get_text(strip=True)), None)
            cook = cook_span.get_text(strip=True) if cook_span else None

            transportation_list = []
            # rent = soup.select_one("#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.house-price > span > strong")
            transportation_main = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(1) > div.surround-list-box.traffic > p > span")
            transportation_sup1 = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(1) > div.surround-list-text > p:nth-child(1) > span")
            transportation_sup2 = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(1) > div.surround-list-text > p:nth-child(2) > span")
            for value in [
                transportation_main, transportation_sup1, transportation_sup2
            ]:
                if value is not None:
                    transportation_list.append(value)

            activity_list = []
            activity_main = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(2) > div.surround-list-box.live > p > span")
            activity_sup1 = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(2) > div.surround-list-text > p.icon-restaurant > span")
            activity_sup2 = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(2) > div.surround-list-text > p.icon- > span")
            for value in [
                activity_main, activity_sup1, activity_sup2
            ]:
                if value is not None:
                    activity_list.append(value)

            education_list = []
            education_main = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(3) > div.surround-list-box.education > p > span")
            education_sup1 = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(3) > div.surround-list-text > p.icon-secondary > span")
            education_sup2 = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(3) > div.surround-list-text > p.icon- > span")
            for value in [
                education_main, education_sup1, education_sup2
            ]:
                if value is not None:
                    education_list.append(value)

            description_unfiltered = soup.select_one(
                "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.house-condition > div.house-condition-content > div.article.t5-rich-editor")
            if description_unfiltered:
                description = " ".join(
                    description_unfiltered.get_text().replace("\xa0", " ").split())
            else:
                description = None

            upload_text = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.aside > section.contact-tip > div.publish-info")
            # update_time_unfiltered = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.aside > section.contact-tip > div.grey.publish-info")
            now = datetime.now()
            if "天前發佈" in upload_text:
                filtered_update_time = re.search(r'(\d+)\s*天前', upload_text)
                if filtered_update_time:
                    days = int(filtered_update_time.group(1))
                    upload_date = (now - timedelta(days=days)
                                   ).strftime("%Y-%m-%d")

            elif "日發佈" in upload_text:
                filtered_update_time = re.search(
                    r'(\d+)\s*月\s*(\d+)\s*日', upload_text)
                if filtered_update_time:
                    month = int(filtered_update_time.group(1))
                    day = int(filtered_update_time.group(2))
                    current_year = now.year
                    upload_date = datetime(
                        year=current_year, month=month, day=day).strftime("%Y-%m-%d")

            else:
                upload_date = now.strftime("%Y-%m-%d")

            # if "小時內更新" in upload_text:
            #     filtered_update_time = re.search(r'(\d+)\s*小時(?:內|前)更新', upload_text)
            #     if filtered_update_time:
            #         hours = int(filtered_update_time.group(1))
            #         update_time = (now - timedelta(hours=hours)).strftime("%Y-%m-%d")

            script = soup.select_one("#rent-detail-structured-data")

            if script:
                data = json.loads(script.string)

                image_list = []

                for item in data.get("@graph", []):
                    if "image" in item:
                        image_list = [
                            img
                            for img in item["image"]
                            if "(null)" not in img and ".jpg" in img
                        ]
                        break
            else:
                image_list = []

            house_data = {
                "title": title,
                "house_id": house_id,
                "pattern": pattern,
                "rent": rent,
                "identity_requirement": identity_requirement,
                "sqm": sqm,
                "floor": floor,
                "address": address,
                "transportation": transportation_list,
                "activity": activity_list,
                "education": education_list,
                "facility": facility_list,
                "rental_period": rental_period,
                "pet": pet,
                "cook": cook,
                "description": description,
                "upload_text": upload_text,
                "upload_date": upload_date,
                # "update_time": update_time,
                "crawled_time": datetime.now().strftime("%Y-%m-%d"),
                "images": image_list
            }
            return house_data, id, status_code

        elif res.status_code in (403, 404):

            # print(f"{id}錯誤，已寫入failed_house_data.jsonl")
            return None, id, status_code
    except Exception as e:
        print(f"網頁請求失敗: {e}")
        return None, id, status_code


def start_591crawler(region=1, keyword=None, page=1, kind=(1, 2, 3, 4)):
    region = region
    keyword = keyword
    page = page
    kind = kind
    loaded_id_list = []
    # 嘗試讀取all_house_id.jsonl
    if os.path.exists("all_house_id.jsonl"):

        with open("all_house_id.jsonl", "r", encoding="utf-8") as f:

            for line in f:

                if line.strip():

                    loaded_id_list.append(
                        json.loads(line.strip())
                    )

        # 如果沒有all_house_id.jsonl是空的就開始排ID列表
        if len(loaded_id_list) == 0:

            print("目前沒有房屋 ID")
            print("開始爬取房屋 ID...")

            max_pages = get_max_pages(region=region,
                                      keyword=keyword,

                                      kind=kind)

            with open("all_house_id.jsonl", "a", encoding="utf-8") as f:
                print(f"找到{max_pages}頁")
                for page in range(1, max_pages + 1):
                    print(f"正在爬取房屋列表第{page}頁")

                    house_id_list = find_house(
                        region=region,
                        keyword=keyword,
                        page=page,
                        kind=kind
                    )

                    if not house_id_list:
                        print(f"第 {page} 頁沒有取得 ID")
                        continue

                    # 寫入 JSONL
                    for house_id in house_id_list:
                        f.write(json.dumps(house_id, ensure_ascii=False) + "\n")
                        loaded_id_list.append(house_id)

                    f.flush()

                    print(f"取得 {len(house_id_list)} 筆 ID")
                    sleep_time = random.uniform(1.0, 2.5)
                    print(f"還有{(max_pages)-(page)}頁,等待 {sleep_time:.2f} 秒...")
                    sleep(sleep_time)

            print(f"房屋 ID 取得完成，總共 {len(loaded_id_list)} 筆")

        else:
            print(f"已存在房屋 ID，共 {len(loaded_id_list)} 筆")

    else:  # all_house_id.jsonl 不存在 -> 開始獲取房屋ID列表
        print("找不到all_house_id.jsonl")
        print("開始取得房屋ID...")
        max_pages = get_max_pages(region=region,
                                  keyword=keyword,
                                  kind=kind)
        with open("all_house_id.jsonl", "a", encoding="utf-8") as f:
            for page in range(1, max_pages + 1):
                print(f"正在取得第{page}頁房屋ID")

                house_id_list = find_house(
                    region=region,
                    keyword=keyword,
                    page=page,
                    kind=kind
                )
                for house_id in house_id_list:
                    f.write(json.dumps(house_id, ensure_ascii=False) + "\n")
                    loaded_id_list.append(house_id)
                f.flush()
                sleep_time = random.uniform(0.8, 1.5)
                print(f"第{page}頁完成")
                print(f"等待{sleep_time} 秒...")
                sleep(sleep_time)

    print("開始取得房屋詳細資料")

    crawled_ids = set()
    if os.path.exists("all_house_data.jsonl"):
        with open("all_house_data.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())

                    if isinstance(data, dict):

                        if "house_id" in data:
                            crawled_ids.add(data["house_id"])
    if os.path.exists("failed_house_id.jsonl"):
        with open("failed_house_id.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    house_id = json.loads(line.strip())
                    crawled_ids.add(house_id)
    print(f"共有{len(loaded_id_list)}筆房屋ID, 其中{len(crawled_ids)}筆已經處理過")

    success_count = 0
    fail_count = 0
    remaining_count = sum(
        1 for house in loaded_id_list if house["house_id"] not in crawled_ids)

    print()
    with open("all_house_data.jsonl", "a", encoding="utf-8") as f_success, \
            open("failed_house_id.jsonl", "a", encoding="utf-8") as f_fail:
        for house in loaded_id_list:
            house_id = house['house_id']
            if house_id in crawled_ids:
                print(f"ID: {house_id}已處理過,跳過")
                continue

            print(f"開始取得ID: {house_id}的詳細資料...")
            house_data, id, status_code = find_houseID(house_id)

            if house_data is not None:
                f_success.write(json.dumps(
                    house_data, ensure_ascii=False) + "\n")
                f_success.flush()
                success_count += 1
                print(f"爬取成功")

            else:
                failed_data = {
                    "house_id": id,
                    "status_code": status_code,
                    "failed_time": datetime.now().replace(microsecond=0).isoformat(" ")}

                with open("failed_house_data.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(failed_data, ensure_ascii=False) + "\n")
                f_fail.write(json.dumps(id, ensure_ascii=False) + "\n")
                f_fail.flush()

                fail_count += 1
                print(f"ID: {id} 爬取失敗, 詳細資料已存入failed_house_data.jsonl")
                print(f"將ID: {id} 存入failed_hose_id.jsonl ID列表中")

            remaining_count -= 1
            sleep_time = random.uniform(1.0, 2.5)
            print(f"剩餘{remaining_count}筆資料,等待{sleep_time:.2f}秒...")
            sleep(sleep_time)

    print("房屋詳細資料爬取完成")
    print(f"本次成功:{success_count}筆")
    print(f"失敗:{fail_count}筆")


if __name__ == '__main__':
    # print(find_houseID(21941368))
    # print(find_house())
    start_591crawler()
