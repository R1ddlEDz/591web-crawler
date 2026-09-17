import requests
from bs4 import BeautifulSoup as bs
import json
from datetime import datetime, timedelta
import re
from time import sleep
import random
import os
from pathlib import Path
from bs4.element import Tag
import math

random_id = random.randint(10000, 99999)
# print(random_id)


def get_text(soup, selector):
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else None


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
            date_now_withseconds = datetime.now().replace(microsecond=0).isoformat(" ")
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
    # print(res.status_code)
    # print(data)

# find_house(region=1)


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


def find_houseID(id, kind):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = f"https://rent.591.com.tw/{id}"

    # print(res.status_code)
    status_code = None

    try:
        res = requests.get(url, headers=custom_headers)
        status_code = res.status_code
        # main_content = soup.select_one("#__nuxt > div:nth-child(4) > div.list-wrapper > main > div:nth-child(5) > div")
        if res.status_code == 200:
            # print(f"成功取得{id}的資料")
            soup = bs(res.text, 'lxml')
            title = get_text(soup, ".title > h1")
            house_id = get_text(
                soup, "#__nuxt > section:nth-child(1) > section > section.crumbs > span")[1:]

            pattern_span = get_text(soup, ".pattern > span[data-v-b5702979]")

            pattern_list = {
                "layout_type": None,
                "bedrooms": 0,
                "living_rooms": 0,
                "bathrooms": 0
            }
            if "開放式" in pattern_span:
                pattern_list["layout_type"] = "open_plan"
                pattern_list["bedrooms"] = None
                pattern_list["living_rooms"] = None
                pattern_list["bathrooms"] = None

            elif "獨立套房" in pattern_span:
                pattern_list["layout_type"] = "suite"
                pattern_list["bedrooms"] = None
                pattern_list["living_rooms"] = None
                pattern_list["bathrooms"] = None

            else:

                bedroom_match = re.search(r"(\d+)房", pattern_span)
                living_room_match = re.search(r"(\d+)廳", pattern_span)
                bathroom_match = re.search(r"(\d+)衛", pattern_span)

                if bedroom_match or living_room_match or bathroom_match:
                    pattern_list["layout_type"] = "standard"

                    if bedroom_match:
                        pattern_list["bedrooms"] = int(bedroom_match.group(1))
                    if living_room_match:
                        pattern_list["living_rooms"] = int(
                            living_room_match.group(1))
                    if bathroom_match:
                        pattern_list["bathrooms"] = int(
                            bathroom_match.group(1))

            rent_text = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.house-price > span > strong")
            rent = int(rent_text.replace(",", "").strip())

            identity_text = None
            for item in soup.select("div.desc-item"):
                label_span = item.select_one("span.desc-label")
                label = label_span.get_text(strip=True) if label_span else None
                # print(label)
                if label and "身份要求" in label:
                    value = item.select_one("span.desc-value")

                    if value:
                        identity_text = value.get_text(strip=True)
                    break

            if identity_text is None:
                identity_requirement = None
            else:
                identity_requirement = {
                    "student": 1 if "學生" in identity_text else 0,
                    "worker": 1 if "上班族" in identity_text else 0,
                    "family": 1 if "家庭" in identity_text else 0
                }

            # sqm = get_text(soup, "div.pattern > span.inline-flex-row")

            sqm_span = next((span for span in soup.select(
                            "div.pattern > span.inline-flex-row") if "坪" in span.get_text(strip=True)), None)
            sqm = (float(sqm_span.get_text(strip=True).replace(
                '坪', '').strip()) if sqm_span else None)
            sqm_text = sqm_span.get_text(strip=True) if sqm_span else None

            floor_text = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.pattern > span:nth-child(5)")

            floor_data = {
                "floor_type": None,
                "current_floor_start": None,
                "current_floor_end": None,
                "total_floor": None,
                "floor_ratio": 0,
                "is_basement": 0,
                "is_rooftop_addition": 0,
                "is_whole_building": 0,
            }

            total_match = re.search(r"/(\d+)F$", floor_text)
            if total_match:
                floor_data["total_floor"] = int(total_match.group(1))

            if "頂層加蓋" in floor_text or "頂樓加蓋" in floor_text:
                floor_data['floor_type'] = "rooftop_addition"
                floor_data["is_rooftop_addition"] = 1
            if "整棟" in floor_text:
                floor_data["floor_type"] = "whole_building"
                floor_data["is_whole_building"] = 1
                floor_data["current_floor_start"] = 1
                floor_data["current_floor_end"] = floor_data["total_floor"]

            basement_range_match = re.search(
                r"^B(\d+)~(\d+)F/(\d+)F$", floor_text)
            if basement_range_match:
                floor_data["floor_type"] = "basement_range"
                basement_floor = int(basement_range_match.group(1))
                upper_floor = int(basement_range_match.group(2))
                floor_data["current_floor_start"] = -basement_floor
                floor_data["current_floor_end"] = upper_floor
                floor_data["is_basement"] = 1

            basement_match = re.search(r"^B(\d+)/(\d+)F$", floor_text)
            if basement_match:
                floor_data["floor_type"] = "basement"
                basement_floor = int(basement_match.group(1))
                total_floor = int(basement_match.group(2))
                floor_data["current_floor_start"] = -basement_floor
                floor_data["current_floor_end"] = -basement_floor
                floor_data["total_floor"] = total_floor
                floor_data["is_basement"] = 1

            range_match = re.search(r"^(\d+)F~(\d+)F/(\d+)F$", floor_text)
            if range_match:
                floor_data["floor_type"] = "range"
                floor_data["current_floor_start"] = int(range_match.group(1))
                floor_data["current_floor_end"] = int(range_match.group(2))

            single_match = re.search(r"^(\d+)F/(\d+)F$", floor_text)
            if single_match:
                floor_data["floor_type"] = "single"
                current_floor = int(single_match.group(1))
                floor_data["current_floor_start"] = current_floor
                floor_data["current_floor_end"] = current_floor

            if (
                floor_data["current_floor_start"] is not None
                and floor_data["current_floor_end"] is not None
                and floor_data["total_floor"] is not None
                and floor_data["total_floor"] > 0
                and floor_data["is_basement"] == 0
                and floor_data["is_whole_building"] == 0
            ):

                current_floor_avg = (
                    floor_data["current_floor_start"]
                    + floor_data["current_floor_end"]
                ) / 2

                floor_data["floor_ratio"] = round(
                    current_floor_avg / floor_data["total_floor"],
                    3
                )

            address_text = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.address > p:nth-child(1) > span.load-map > div")

            address_result = {
                "district": None,
                "road": None
            }
            if not address_text:
                address_result

            district_match = re.search(r"([^縣市]+區)", address_text)
            if district_match:
                address_result["district"] = district_match.group(1)

            road_match = re.search(
                r"([^區]+?(?:路|街|大道)(?:[一二三四五六七八九十0-9]+段)?)", address_text)
            if road_match:
                road = road_match.group(1)

                if address_result['district'] and road.startswith(address_result['district']):
                    road = road[len(address_result['district']):]

                address_result['road'] = road
            None
            facility = soup.select_one(
                "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div.facility")
            if facility:
                facility_list = [
                    x.get_text(strip=True)
                    for x in facility.select(":scope > dl:not(.del)")
                ]
            else:
                facility_list = None

            rental_period = get_text(
                soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div:nth-child(2) > div > div > div:nth-child(1) > span.desc-value")
            # pet = get_text(
            #     soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div:nth-child(2) > div > div > div:nth-child(4) > span.desc-value")

            pet_text = None
            pet = None
            cook_text = None
            cook = None

            pet_span = next((span for span in soup.select(
                "span.desc-value") if "寵物" in span.get_text(strip=True)), None)
            if pet_span:
                pet_text = pet_span.get_text(strip=True)
                if "不可養寵物" in pet_text:
                    pet = 0
                elif "可養寵物" in pet_text:
                    pet = 1
                else:
                    pet = None

            cook_span = next((span for span in soup.select(
                "span.desc-value") if "開伙" in span.get_text(strip=True)), None)
            cook_text = cook_span.get_text(strip=True) if cook_span else None
            if cook_text:
                if "不可開伙" in cook_text:
                    cook = 0
                elif "可開伙" in cook_text:
                    cook = 1
                else:
                    cook = None

            taipei_metro_lines = {
                "南港展覽館",
                "南港軟體園區",
                "東湖",
                "葫洲",
                "大湖公園",
                "內湖",
                "文德",
                "港墘",
                "西湖",
                "劍南路",
                "大直",
                "松山機場",
                "中山國中",
                "南京復興",
                "忠孝復興",
                "大安",
                "科技大樓",
                "六張犁",
                "麟光",
                "辛亥",
                "萬芳醫院",
                "萬芳社區",
                "木柵",
                "動物園",
                "新北投",
                "淡水",
                "紅樹林",
                "竹圍",
                "關渡",
                "忠義",
                "復興崗",
                "北投",
                "奇岩",
                "唭哩岸",

            }

            # 文湖線
            wenhu_line = [
                "動物園",
                "木柵",
                "萬芳社區",
                "萬芳醫院",
                "辛亥",
                "麟光",
                "六張犁",
                "科技大樓",
                "大安",
                "忠孝復興",
                "南京復興",
                "中山國中",
                "松山機場",
                "大直",
                "劍南路",
                "西湖",
                "港墘",
                "文德",
                "內湖",
                "大湖公園",
                "葫洲",
                "東湖",
                "南港軟體園區",
                "南港展覽館"
            ]

            # 淡水信義線
            tamsui_xinyi_line = [
                "淡水站",
                "紅樹林站",
                "竹圍站",
                "關渡站",
                "忠義站",
                "復興崗站",
                "北投站",
                "奇岩站",
                "唭哩岸站",
                "石牌站",
                "明德站",
                "芝山站",
                "士林站",
                "劍潭站",
                "圓山站",
                "民權西路站",
                "雙連站",
                "中山站",
                "台北車站",
                "台大醫院站",
                "中正紀念堂站",
                "東門站",
                "大安森林公園站",
                "大安站",
                "信義安和站",
                "台北101/世貿站",
                "象山站",
                "廣慈/奉天宮站"
            ]

            xinbeitou_branch = [
                "北投站",
                "新北投站"
            ]

            # 松山新店線
            songshan_xindian_line = [
                "新店站",
                "新店區公所站",
                "七張站",
                "大坪林站",
                "景美站",
                "萬隆站",
                "公館站",
                "台電大樓站",
                "古亭站",
                "中正紀念堂站",
                "小南門站",
                "西門站",
                "北門站",
                "中山站",
                "松江南京站",
                "南京復興站",
                "台北小巨蛋站",
                "南京三民站",
                "松山站"
            ]

            # 小碧潭支線
            xiaobitan_branch = [
                "七張站",
                "小碧潭站"
            ]

            # 中和新蘆線
            zhonghe_xinlu_line = [
                "南勢角站",
                "景安站",
                "永安市場站",
                "頂溪站",
                "古亭站",
                "東門站",
                "忠孝新生站",
                "松江南京站",
                "行天宮站",
                "中山國小站",
                "民權西路站",
                "大橋頭站",

                # 新莊線方向
                "台北橋站",
                "菜寮站",
                "三重站",
                "先嗇宮站",
                "頭前庄站",
                "新莊站",
                "輔大站",
                "丹鳳站",
                "迴龍站",

                # 蘆洲線方向
                "三重國小站",
                "三和國中站",
                "徐匯中學站",
                "三民高中站",
                "蘆洲站"
            ]

            # 板南線
            bannan_line = [
                "頂埔站",
                "永寧站",
                "土城站",
                "海山站",
                "亞東醫院站",
                "府中站",
                "板橋站",
                "新埔站",
                "江子翠站",
                "龍山寺站",
                "西門站",
                "台北車站",
                "善導寺站",
                "忠孝新生站",
                "忠孝復興站",
                "忠孝敦化站",
                "國父紀念館站",
                "市政府站",
                "永春站",
                "後山埤站",
                "昆陽站",
                "南港站",
                "南港展覽館站"
            ]

            # 環狀線
            circular_line = [
                "大坪林站",
                "十四張站",
                "秀朗橋站",
                "景平站",
                "景安站",
                "中和站",
                "橋和站",
                "中原站",
                "板新站",
                "板橋站",
                "新埔民生站",
                "頭前庄站",
                "幸福站",
                "新北產業園區站"
            ]
            all_mrt_stations = set(wenhu_line + tamsui_xinyi_line + xinbeitou_branch +
                                   songshan_xindian_line + xiaobitan_branch + zhonghe_xinlu_line + bannan_line + circular_line)
            transportation_list = []
            transportation_data = {
                "mrt": [],
                "bus": []
            }

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

            for text in transportation_list:
                match = re.search(r"距(.+?站)(\d+)公尺", text)

                if not match:
                    continue

                station_name = match.group(1).strip()
                distance = int(match.group(2))
                normalized_station_name = re.sub(r"^捷運", "", station_name)

                if normalized_station_name in all_mrt_stations:
                    transportation_data['mrt'].append(
                        {"name": normalized_station_name, 'distance_m': distance})
                else:
                    transportation_data['bus'].append(
                        {'name': station_name, 'distance_m': distance})

            transportation_data['nearest_mrt_distance_m'] = (min(
                x['distance_m'] for x in transportation_data['mrt']) if transportation_data['mrt'] else None)
            transportation_data['nearest_bus_distance_m'] = (min(
                x['distance_m'] for x in transportation_data['bus']) if transportation_data['bus'] else None)

            if transportation_data["nearest_mrt_distance_m"] is not None:
                transportation_data["has_mrt"] = 1
            else:
                transportation_data["has_mrt"] = 0

            mrt_distance = transportation_data['nearest_mrt_distance_m']
            if mrt_distance is None:
                transportation_data['mrt_distance_bucket'] = "no_mrt"

            elif mrt_distance < 300:
                transportation_data["mrt_distance_bucket"] = "<300"

            elif mrt_distance < 500:
                transportation_data["mrt_distance_bucket"] = "300-500"

            elif mrt_distance < 800:
                transportation_data["mrt_distance_bucket"] = "500-800"

            else:
                transportation_data["mrt_distance_bucket"] = "800+"

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
            activity_data = {
                "shopping_center_count": None,
                "restaurant_count": None
            }

            shopping_count = None
            restaurant_count = None

            for text in activity_list:
                shopping_match = re.search(r"(\d+)家購物中心", text)
                if not shopping_match:
                    continue
                resturant_match = re.search(r"(\d+)家餐廳", text)
                if not resturant_match:
                    continue

                if shopping_match:
                    activity_data["shopping_center_count"] = int(
                        shopping_match.group(1))

                if resturant_match:
                    activity_data["restaurant_count"] = int(
                        resturant_match.group(1))

            education_list = []
            elementary_keywords = [
                "國民小學",
                "國小"
            ]

            middle_keywords = [
                "國民中學",
                "國中",
                "高級中學"
            ]

            college_keywords = [
                "大學",
                "學院",
                "科技大學",
                "技術學院",
                "社區大學"
            ]
            education_data = {
                "elementary": None,
                "middle": None,
                "college": None,
                "nearest_elementary_distance_m": None,
                "nearest_middle_distance_m": None,
                "nearest_college_distance_m": None
            }
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

            for text in education_list:

                ele_total_text = re.search(r"(\d+)所國小", text)
                mid_total_text = re.search(r"(\d+)所國中", text)
                col_total_text = re.search(r"(\d+)所大學", text)

                if ele_total_text:
                    education_data['elementary'] = int(ele_total_text.group(1))
                if mid_total_text:
                    education_data['middle'] = int(mid_total_text.group(1))
                if col_total_text:
                    education_data['college'] = int(col_total_text.group(1))

                distance_match = re.search(r"(\d+)公尺", text)
                if not distance_match:
                    continue

                distance = int(distance_match.group(1))

                if any(keyword in text for keyword in elementary_keywords):
                    current = education_data['nearest_elementary_distance_m']
                    if current is None or distance < current:
                        education_data["nearest_elementary_distance_m"] = distance

                elif any(keyword in text for keyword in middle_keywords):
                    current = education_data["nearest_middle_distance_m"]
                    if current is None or distance < current:
                        education_data["nearest_middle_distance_m"] = distance
                elif any(keyword in text for keyword in college_keywords):
                    current = education_data["nearest_college_distance_m"]
                    if current is None or distance < current:
                        education_data["nearest_college_distance_m"] = distance

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
                            if "(null)" not in img]
                        break
            else:
                image_list = []

            facility_mapping = {
                "refrigerator": ["冰箱"],
                "washing_machine": ["洗衣機"],
                "tv": ["電視"],
                "air_conditioner": ["冷氣"],
                "water_heater": ["熱水器"],
                "bed": ["床"],
                "wardrobe": ["衣櫃"],
                "cable": ["第四台"],
                "internet": ["網路"],
                "gas": ["天然瓦斯"],
                "sofa": ["沙發"],
                "table": ["桌椅"],
                "balcony": ["陽台"],
                "elevator": ["電梯"],
                "parking": ["平面車位",
                            "機械車位",
                            "平面+機械車位",
                            "其他車位"]
            }
            facility_result = {
                eng_name: int(any(keyword in facility for facility in facility_list for keyword in keywords)) for eng_name, keywords in facility_mapping.items()}

            balcony_count = 0

            facility_score_fields = [
                "refrigerator",
                "washing_machine",
                "tv",
                "air_conditioner",
                "water_heater",
                "bed",
                "wardrobe",
                "cable",
                "internet",
                "gas",
                "sofa",
                "table",
                "balcony",
                "elevator",
                "parking"
            ]

            facility_result["facility_score"] = sum(
                facility_result[field]
                for field in facility_score_fields
            )

            for facility in facility_list:
                match = re.search(r"(\d+)陽台", facility)
                if match:
                    balcony_count = int(match.group(1))
                    break
            facility_result['balcony_count'] = balcony_count

            cleaned_house_data = {
                "title": title,
                "house_id": house_id,
                "pattern_text": pattern_span,
                "rent": rent,
                "identity_text": identity_text,
                "sqm_text": sqm_text,
                "floor_text": floor_text,
                "full_address": address_text,
                "transportation_text": transportation_list,
                "activity_text": activity_list,
                "education_text": education_list,
                "facility_text": facility_list,
                "pet_text": pet_text,
                "cook_text": cook_text,
                "rental_period": rental_period,
                "description": description,
                "upload_text": upload_text,
                "upload_date": upload_date,
                # "update_time": update_time,
                "crawled_time": datetime.now().strftime("%Y-%m-%d"),
                "kind": kind,
                "images": image_list
            }
            processed_house_data = {
                "house_id": house_id,
                "pattern": pattern_list,
                "rent": rent,
                "identity_requirement": identity_requirement,
                "sqm": sqm,
                "rps": rent / sqm,
                "floor": floor_data,
                "address": address_result,
                "transportation": transportation_data,
                "activity": activity_data,
                "education": education_data,
                "facility": facility_result,
                "pet": pet,
                "cook": cook,
                "upload_date": upload_date,
                "kind": kind
            }
            # house_data['facility'].append(facility_result)
            return processed_house_data, cleaned_house_data, id, status_code

        elif res.status_code in (403, 404):

            # print(f"{id}錯誤，已寫入failed_house_data.jsonl")
            return None, None, id, status_code
    except Exception as e:
        print(f"網頁請求失敗: {e}")
        return None, None, id, status_code


def jsonl_to_json(input_path, output_path):
    data_list = []
    file_name, file_text = os.path.splitext(output_path)
    output_path = f"{file_name}_{random_id}{file_text}"
    output_dir = os.path.dirname(output_path)

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                data = json.loads(line)
                data_list.append(data)

            except json.JSONDecodeError as e:
                print(f"第{line_number}行發生錯誤，已跳過")
                print(f"錯誤:{e}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_list, f, ensure_ascii=False, indent=4)
    print(f"{output_path}轉換完成")
    return output_path


def export_house_data_json(kind):
    input_path = f"all_house_data_{kind}.jsonl"
    output_path = f"output/all_house_data_{kind}_{datetime.today().strftime('%Y_%m%d')}.json"
    return jsonl_to_json(input_path, output_path)


def export_processed_house_data_json(kind):
    input_path = f"processed_house_data_{kind}.jsonl"
    output_path = f"output/processed_all_house_data_{kind}_{datetime.today().strftime('%Y_%m%d')}.json"
    return jsonl_to_json(input_path, output_path)


def start_591crawler(region=1, keyword=None, page=1, kind=1, limit=None):
    region = region
    keyword = keyword
    page = page
    kind = kind
    limit = limit

    loaded_id_list = []

    # 嘗試讀取all_house_id.jsonl
    if os.path.exists(f"all_house_id_{kind}.jsonl"):

        with open(f"all_house_id_{kind}.jsonl", "r", encoding="utf-8") as f:

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

            with open(f"all_house_id_{kind}.jsonl", "a", encoding="utf-8") as f, \
                    open(f"rent_history_{kind}.jsonl", "a", encoding="utf-8")as f_rent:
                print(f"找到{max_pages}頁")
                for page in range(1, max_pages + 1):
                    print(f"正在爬取房屋列表第{page}頁")

                    house_id_list, history_list, kind = find_house(
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

                    for rent_history in history_list:
                        f_rent.write(json.dumps(
                            rent_history, ensure_ascii=False) + "\n")
                    f.flush()
                    f_rent.flush()

                    print(f"取得 {len(house_id_list)} 筆 ID")
                    sleep_time = random.uniform(1.0, 2.5)
                    print(f"還有{(max_pages)-(page)}頁,等待 {sleep_time:.2f} 秒...")
                    sleep(sleep_time)

            print(f"房屋 ID 取得完成，總共 {len(loaded_id_list)} 筆")

        else:
            print(f"已存在房屋 ID，共 {len(loaded_id_list)} 筆")

    else:  # all_house_id.jsonl 不存在 -> 開始獲取房屋ID列表
        print(f"找不到all_house_id_{kind}.jsonl")
        print("開始取得房屋ID...")
        max_pages = get_max_pages(region=region,
                                  keyword=keyword,
                                  kind=kind)
        with open(f"all_house_id_{kind}.jsonl", "a", encoding="utf-8") as f, \
                open(f"rent_history_{kind}.jsonl", "a", encoding="utf-8")as f_rent:
            for page in range(1, max_pages + 1):
                print(f"正在取得第{page}頁房屋ID")

                house_id_list, history_list, kind = find_house(
                    region=region,
                    keyword=keyword,
                    page=page,
                    kind=kind
                )
                # 寫入 JSONL
                for house_id in house_id_list:
                    f.write(json.dumps(house_id, ensure_ascii=False) + "\n")
                    loaded_id_list.append(house_id)

                for rent_history in history_list:
                    f_rent.write(json.dumps(
                        rent_history, ensure_ascii=False) + "\n")
                f.flush()
                f_rent.flush()
                sleep_time = random.uniform(0.8, 1.5)
                print(f"第{page}頁完成")
                print(f"等待{sleep_time:.2f} 秒...")
                sleep(sleep_time)

    print("開始取得房屋詳細資料")

    crawled_ids = set()
    if os.path.exists(f"all_house_data_{kind}.jsonl"):
        with open(f"all_house_data_{kind}.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())

                    if isinstance(data, dict):

                        if "house_id" in data:
                            crawled_ids.add(data["house_id"])
    if os.path.exists(f"failed_house_data_{kind}.jsonl"):
        with open(f"failed_house_data_{kind}.jsonl", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data = json.loads(line.strip())
                    house_id = data['house_id']
                    crawled_ids.add(house_id)
    print(f"共有{len(loaded_id_list)}筆房屋ID, 其中{len(crawled_ids)}筆已經處理過")

    process_count = 0
    success_count = 0
    fail_count = 0
    remaining_count = sum(
        1 for house in loaded_id_list if house["house_id"] not in crawled_ids)

    with open(f"all_house_data_{kind}.jsonl", "a", encoding="utf-8") as f_raw, \
        open(f"processed_house_data_{kind}.jsonl", "a", encoding='utf-8') as f_processed, \
            open(f"failed_house_data_{kind}.jsonl", "a", encoding="utf-8") as f_fail:
        for house in loaded_id_list:
            house_id = house['house_id']
            if house_id in crawled_ids:
                # print(f"ID: {house_id}已處理過,跳過")
                continue

            if limit is not None and process_count >= limit:
                print(f"已達本次測試上線: {limit}筆")
                break

            print(f"開始取得ID: {house_id}的詳細資料...")
            processed_house_data, house_data, returned_id, status_code = find_houseID(
                house_id, kind)

            if house_data is not None:
                find_tag(house_data)
                f_raw.write(json.dumps(
                    house_data, ensure_ascii=False) + "\n")
                f_raw.flush()
                success_count += 1
                print(f"爬取成功")

                if processed_house_data is not None:
                    f_processed.write(json.dumps(
                        processed_house_data, ensure_ascii=False) + "\n")
                f_processed.flush()

            else:
                failed_data = {
                    "house_id": returned_id,
                    "status_code": status_code,
                    "failed_time": datetime.now().replace(microsecond=0).isoformat(" ")}

                f_fail.write(json.dumps(
                    failed_data, ensure_ascii=False) + "\n")
                # f_fail.write(json.dumps(id, ensure_ascii=False) + "\n")
                f_fail.flush()

                fail_count += 1
                print(
                    f"ID: {returned_id} 爬取失敗, 詳細資料已存入failed_house_data_{kind}.jsonl")

            process_count += 1
            remaining_count -= 1
            sleep_time = random.uniform(1.0, 2.5)
            print(f"剩餘{remaining_count}筆資料,等待{sleep_time:.2f}秒...")
            sleep(sleep_time)

    print("房屋詳細資料爬取完成")
    print(f"本次成功:{success_count}筆")
    print(f"失敗:{fail_count}筆")
    print(f"開始將house_data_{kind}轉換成json檔")
    raw_path = export_house_data_json(kind)
    processed_path = export_processed_house_data_json(kind)

    return {
        "raw": raw_path,
        "processed": processed_path
    }


def merge_house_data_json(file_paths, output_prefix):
    merge_data = []

    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8")as f:
            data = json.load(f)

            if isinstance(data, list):
                merge_data.extend(data)
    output_path = f"output/{output_prefix}_{datetime.today().strftime('%Y_%m%d')}.json"
    with open(output_path, "w", encoding="utf-8")as f:
        json.dump(merge_data, f, ensure_ascii=False, indent=4)
    return output_path


def start_591crawler_all(limit=None):
    raw_paths = []
    processed_paths = []

    for kind in [1, 2, 3, 4]:
        result = start_591crawler(kind=kind, limit=limit)
        raw_paths.append(result["raw"])
        processed_paths.append(result["processed"])
    merge_house_data_json(raw_paths, output_prefix="all_house_data_merge")
    merge_house_data_json(
        processed_paths, output_prefix="processed_house_data_merge")


def merge_json(*file_names, folder="output"):
    merge_data = []
    # print(merge_data)
    for file_name in file_names:
        file_path = os.path.join(folder, file_name)
        with open(file_path, "r", encoding="utf-8")as f:
            data = json.load(f)

        merge_data.extend(data)
    random_id_merge = random.randint(10000, 99999)

    output_path = os.path.join(
        folder,
        (f"data_merge_{datetime.today().strftime('%Y_%m%d')}_{random_id_merge}.json"))

    with open(output_path, "w", encoding="utf-8")as f:
        json.dump(merge_data, f, ensure_ascii=False, indent=4)

    output_name = f"all_house_data_merge_{datetime.today().strftime('%Y_%m%d')}.json"

    print(f"合併完成, 輸出位置: {output_name}")
    # return output_path


def auto_merge_json(file_names):
    folder = "output"
    merged_data = []
    random_id_merge = random.randint(10000, 99999)
    for file_name in file_names:
        file_path = os.path.join(folder, file_name)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        merged_data.extend(data)
    with open(f"{folder}/select_data_merge_{datetime.today().strftime('%Y_%m%d')}_{random_id_merge}.json", "w", encoding="utf-8")as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)
    output_path = f"{folder}/select_data_merge_{datetime.today().strftime('%Y_%m%d')}_{random_id_merge}.json"
    print(f"json檔已合併完成,路徑: {output_path}")
    return merged_data


def start_591crawler_select(kinds=None, limit=None):
    if kinds is None:
        kinds = [1, 2, 3, 4]
    elif isinstance(kinds, int):
        kinds = [kinds]
    elif isinstance(kinds, str):
        kinds = [int(x.strip()) for x in kinds.split(",")]

    raw_paths = []
    processed_paths = []

    for kind in kinds:
        result = start_591crawler(kind=kind, limit=limit)
        raw_paths.append(result["raw"])
        processed_paths.append(result["processed"])

    if len(kinds) == 1:
        return {
            "raw": raw_paths[0],
            "processed": processed_paths[0]
        }
    raw_merged_path = merge_house_data_json(raw_paths, "all_house_data_merge")
    processed_merged_path = merge_house_data_json(
        processed_paths, "processed_house_data_merge")
    # print(file_paths)

    return raw_merged_path, processed_merged_path


def find_tag(obj, path="house_data"):
    if isinstance(obj, Tag):
        print(f"[Tag found] {path}")
        print(obj)
        print("-" * 50)

    elif isinstance(obj, dict):
        for key, value in obj.items():
            find_tag(value, f"{path}.{key}")

    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            find_tag(value, f"{path}[{index}]")


if __name__ == '__main__':
    # print(find_houseID(21941368))
    # print(find_house())
    start_591crawler()
