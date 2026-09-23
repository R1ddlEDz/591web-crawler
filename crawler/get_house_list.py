import requests
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import math
from pathlib import Path


def clear_temp_files():
    temp_dir = Path("data/temp")

    for file in temp_dir.glob("*.jsonl"):
        file.unlink()
        print(f"已刪除: {file}")


def get_text(soup, selector):
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else None


def get_max_pages(region=1, keyword=None, page=1, kind=1):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = "https://rent.591.com.tw/list?"
    job_params = {
        "region": 1,
        "page": 1,
        # keyword : "",
        "kind": 1
    }
    max_pages = 99999

    if keyword is not None:
        job_params['keyword'] = keyword
    if region != 1:
        job_params['region'] = region
    if page != 1:
        job_params['page'] = page
    if kind != 1:
        job_params['kind'] = kind

    res = requests.get(url, headers=custom_headers, params=job_params)
    soup = bs(res.text, 'lxml')

    if max_pages == 99999:
        max_pages = math.ceil(int(soup.select_one(
            "#__nuxt > div:nth-child(4) > div.list-wrapper > main > div.list-sort > p > strong").get_text(strip=True).replace(",", "")) / 30)
        max_pages_bp = soup.select_one(
            "#__nuxt > div:nth-child(4) > div.list-wrapper > main > div.list-sort > p > strong").get_text(strip=True).replace(",", "")
    # print(f"region, keyword, page, kind")
    # print(max_pages_bp)
    return max_pages


def find_house(region=1, keyword=None, page=1, kind=1):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = "https://rent.591.com.tw/list?"
    job_params = {
        "region": 1,
        "page": 1,
        "kind": 1
        # keyword : "",
    }

    if keyword is not None:
        job_params['keyword'] = keyword
    if region != 1:
        job_params['region'] = region
    if page != 1:
        job_params['page'] = page
    if kind != 1:
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
            rent = soup.select(
                "strong.text-26px.font-arial > div.inline-flex-row")
            rent_unfil_list = [tag.get_text(strip=True) for tag in rent]
            rent_list = [int(rent_text.replace(",", ""))
                         for rent_text in rent_unfil_list]
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
            date_now_withseconds = datetime.now(
                ZoneInfo("Asia/Taipei")
            ).replace(microsecond=0).isoformat()
            history_list = []
            for house_id, rent_price in zip(
                    house_id_list,
                    rent_list):
                history_list.append({
                    "house_id": house_id,
                    "recorded_at": date_now_withseconds,
                    "rent": rent_price
                })
            # return house_id_list
            # return update_house_list
            return house_zip, history_list, kind
            # print(type(main_content))
        except Exception as e:
            print(e)
            print(res.text[:200])


if __name__ == '__main__':
