"""將 cleaned_house_data 轉成 processed_house_data（僅需 Python 標準函式庫）。

把本檔與 all_house_data.json 放在同一資料夾，執行：
    python convert_house_data.py
或指定路徑：
    python convert_house_data.py input.json -o output.json

輸入：房屋物件陣列、單一房屋物件，或 {"cleaned_house_data": [...]}。
輸出：processed_house_data 物件陣列。預設不覆寫既有檔案。
sqm 沿用原程式命名，單位實際為「坪」；rps 為租金／坪。
捷運站名沿用 utils.py 的清單，不會上網更新或爬取資料。
"""
import argparse
import json
import math
import re
import sys
from pathlib import Path


def text_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        raise ValueError("文字列表必須是字串陣列、字串或 null")
    return value


def number(value):
    if value is None or isinstance(value, bool):
        return None
    match = re.search(r"-?\d+(?:\.\d+)?", str(value).replace(",", ""))
    result = float(match.group()) if match else None
    return result if result is not None and math.isfinite(result) else None


def permission(text, positive, negative):
    text = text or ""
    return 0 if negative in text else 1 if positive in text else None


def chinese_to_number(text):
    chinese_num = {
        "零": 0,
        "一": 1,
        "二": 2,
        "兩": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9
    }

    if text == "十":
        return 10

    if text.startswith("十"):
        return 10 + chinese_num.get(text[1], 0)

    if text.endswith("十"):
        return chinese_num.get(text[0], 0) * 10

    if "十" in text:
        left, right = text.split("十", 1)
        tens = chinese_num.get(left, 0) * 10
        ones = chinese_num.get(right, 0) if right else 0

        return tens + ones

    return chinese_num.get(text)


def parse_rental_period(rental_period):
    if not rental_period:
        return None
    text = rental_period.strip()
    if "半年" in text:
        return 6

    year_match = re.search(r"(\d+)\s*年", text)
    if year_match:
        return int(year_match.group(1))*12

    month_match = re.search(r"(\d+)\s*個?月", text)
    if month_match:
        return int(month_match.group(1))

    chinese_year_match = re.search(r"([零一二兩三四五六七八九十]+)\s*年", text)
    if chinese_year_match:
        year = chinese_to_number(chinese_year_match.group(1))
        if year is not None:
            return year * 12

    chinese_month_match = re.search(r"([零一二兩三四五六七八九十]+)\s*個?月", text)
    if chinese_month_match:
        month = chinese_to_number(chinese_month_match.group(1))
        if month is not None:
            return month

    return None
def convert_house(cleaned_house_data):
    """轉換一筆房屋；不修改輸入物件。"""
    d = cleaned_house_data
    if not isinstance(d, dict):
        raise ValueError("房屋資料必須是 JSON 物件")
    if "cleaned_house_data" in d:
        d = d["cleaned_house_data"]
    if not isinstance(d, dict) or "source_listing_id" not in d:
        raise ValueError("房屋資料缺少 source_listing_id，請確認輸入是 cleaned_house_data")
    kind = d.get("kind")
    if isinstance(kind, str) and kind.isdigit():
        kind = int(kind)
    pattern_text = d.get("pattern_text") or ""
    pattern = dict(layout_type=None, bedrooms=0, living_rooms=0, bathrooms=0)
    if "開放式" in pattern_text:
        pattern = dict(layout_type="open_plan", bedrooms=None, living_rooms=None, bathrooms=None)
    elif "獨立套房" in pattern_text:
        pattern = dict(layout_type="suite", bedrooms=1, living_rooms=0, bathrooms=1)
    else:
        for key, unit in [("bedrooms", "房"), ("living_rooms", "廳"), ("bathrooms", "衛")]:
            match = re.search(r"(\d+)\s*" + unit, pattern_text)
            if match:
                pattern[key] = int(match.group(1))
                pattern["layout_type"] = "standard"
        if pattern["layout_type"] is None:
            pattern["layout_type"] = {3: "shared_suite", 4: "shared_room"}.get(kind)
    rent = number(d.get("rent"))
    if rent is not None and rent.is_integer():
        rent = int(rent)
    sqm = number(d.get("sqm_text"))
    rps = rent / sqm if rent is not None and sqm is not None and sqm > 0 else None
    identity_text = d.get("identity_text")
    identity = None if identity_text is None else {
        key: int(label in identity_text) for key, label in
        [("student", "學生"), ("worker", "上班族"), ("family", "家庭")]
    }
    floor_text = re.sub(r"\s+", "", d.get("floor_text") or "")
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
    address_text = d.get("full_address") or ""
    address_result = {"district": None, "road": None}
    district_match = re.search(r"([^縣市]+區)", address_text)
    if district_match:
        address_result["district"] = district_match.group(1)
        address_text = address_text[district_match.end():]
    road_match = re.search(r"([^區]+?(?:路|街|大道)(?:[一二三四五六七八九十0-9]+段)?)", address_text)
    if road_match:
        address_result["road"] = road_match.group(1)
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
    all_mrt_stations = {name if name.endswith("站") else name + "站" for name in all_mrt_stations}
    transportation_list = [re.sub(r"\s+", "", x).replace(",", "") for x in text_list(d.get("transportation_text"))]
    transportation_data = {"mrt": [], "bus": []}
    for text in transportation_list:
        match = re.search(r"距(.+?站)(\d+)公尺", text)

        if not match:
            continue

        station_name = match.group(1).strip()
        distance = int(match.group(2))
        normalized_station_name = re.sub(r"^捷運", "", station_name)

        if normalized_station_name in all_mrt_stations or station_name.startswith("捷運"):
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
    activity_data = {"shopping_center_count": None, "restaurant_count": None}
    for text in text_list(d.get("activity_text")):
        for key, label in [("shopping_center_count", "購物中心"), ("restaurant_count", "餐廳")]:
            match = re.search(r"(\d+)\s*家\s*" + label, text.replace(",", ""))
            if match:
                activity_data[key] = int(match.group(1))
    elementary_keywords = ["國民小學", "國小"]
    middle_keywords = ["國民中學", "國中", "高級中學"]
    college_keywords = ["大學", "學院", "科技大學", "技術學院", "社區大學"]
    education_data = {key: None for key in ["elementary", "middle", "college",
        "nearest_elementary_distance_m", "nearest_middle_distance_m", "nearest_college_distance_m"]}
    education_list = [re.sub(r"\s+", "", x).replace(",", "") for x in text_list(d.get("education_text"))]
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
    facility_list = text_list(d.get("facility_text"))
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
    balcony_count = 0

    for facility in facility_list:
        if "陽台" in facility:
            match = re.search(r"(\d+)陽台", facility)
            if match:
                balcony_count = int(match.group(1))
                break

            else:
                balcony_count = 1

            break

    facility_result['balcony_count'] = balcony_count
    issues = []
    if pattern["bedrooms"] is not None and pattern["bedrooms"] > 10:
        issues.append("bedroom_count")
    if rent is not None and rent > 1_000_000:
        issues.append("extreme_rent")
    if sqm is not None and sqm > 500:
        issues.append("extreme_sqm")
    if sqm is not None and sqm <= 0:
        issues.append("invalid_sqm")
    if rps is not None and rps > 10_000:
        issues.append("extreme_rps")
    return {
        "source": d.get("source", 591), "house_id": d.get("source_listing_id"),
        "pattern": pattern, "rent": rent, "identity_requirement": identity,
        "sqm": sqm, "rps": rps, "floor": floor_data, "address": address_result,
        "transportation": transportation_data, "activity": activity_data,
        "education": education_data, "facility": facility_result,
        "pet": permission(d.get("pet_text"), "可養寵物", "不可養寵物"),
        "cook": permission(d.get("cook_text"), "可開伙", "不可開伙"),
        "rental_period_months": parse_rental_period(d.get("rental_period")),
        "upload_date": d.get("upload_date"), "kind": kind,
        "data_quality": {"is_suspicious": bool(issues), "issues": issues},
    }


def convert_file(input_path, output_path):
    input_path, output_path = Path(input_path), Path(output_path)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("輸入與輸出不能是同一個檔案")
    with input_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)
    if isinstance(data, dict) and "cleaned_house_data" in data:
        data = data["cleaned_house_data"]
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON 最外層必須是房屋陣列或房屋物件")
    result = []
    for index, house in enumerate(data, 1):
        try:
            result.append(convert_house(house))
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError(f"第 {index} 筆資料轉換失敗：{error}") from error
    # 先完成轉換與序列化；失敗時不產生不完整的 JSON。
    content = json.dumps(result, ensure_ascii=False, indent=4, allow_nan=False)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as file:
        file.write(content + "\n")
    return len(result)


def main():
    folder = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="將 cleaned_house_data 轉換成新的 processed JSON")
    parser.add_argument("input", nargs="?", type=Path, default=folder / "all_house_data.json")
    parser.add_argument("-o", "--output", type=Path, help="輸出路徑（預設在輸入資料夾建立 processed_house_data.json）")
    args = parser.parse_args()
    output = args.output or args.input.with_name("processed_house_data.json")
    try:
        count = convert_file(args.input, output)
    except (OSError, ValueError) as error:
        print(f"轉換失敗：{error}", file=sys.stderr)
        return 1
    print(f"轉換完成，共 {count} 筆。輸出：{output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
