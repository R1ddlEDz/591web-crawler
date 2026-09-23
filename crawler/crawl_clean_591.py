"""591 租屋資料爬蟲：保留清洗後的網頁資料，不做特徵轉換。

執行流程：
1. 依 kind 取得 max_pages。
2. 逐頁收集房屋 ID、更新日期與租金歷史。
3. 逐筆取得房屋詳細頁，清洗文字後寫入 JSONL。
4. 將 kind 1、2、3、4 的四類 JSONL 各自合併為 JSON。

預設從專案根目錄讀寫資料，不依賴 crawler/utils.py，也不會修改該檔案。
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://rent.591.com.tw"
LIST_URL = f"{BASE_URL}/list"
TAIPEI_TZ = ZoneInfo("Asia/Taipei")
DEFAULT_KINDS = (1, 2, 3, 4)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Referer": "https://rent.591.com.tw/",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}


def now_taipei() -> datetime:
    return datetime.now(TAIPEI_TZ)


def clean_text(value: str | None) -> str | None:
    """移除不斷行空白並壓縮多餘空白。"""
    if value is None:
        return None
    cleaned = " ".join(value.replace("\xa0", " ").split())
    return cleaned or None


def element_text(element: Any) -> str | None:
    return clean_text(element.get_text(" ", strip=True)) if element else None


def select_text(soup: BeautifulSoup, selector: str) -> str | None:
    return element_text(soup.select_one(selector))


def unique_nonempty(values: Iterable[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        value = clean_text(value)
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def request_html(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: float = 20,
    retries: int = 3,
) -> requests.Response:
    """GET 請求；對 429 與伺服器錯誤採指數退避重試。"""
    last_error: requests.RequestException | None = None
    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=timeout)
            if response.status_code not in {429, 500, 502, 503, 504}:
                return response
            if attempt == retries - 1:
                return response
        except requests.RequestException as exc:
            last_error = exc
            if attempt == retries - 1:
                raise
        time.sleep((2**attempt) + random.uniform(0.2, 0.8))
    if last_error:
        raise last_error
    raise RuntimeError("無法取得網頁")


def list_params(region: int, keyword: str | None, page: int, kind: int) -> dict[str, Any]:
    params: dict[str, Any] = {"region": region, "page": page, "kind": kind}
    if keyword:
        params["keyword"] = keyword
    return params


def get_max_pages(
    session: requests.Session,
    region: int = 1,
    keyword: str | None = None,
    kind: int = 1,
) -> int:
    response = request_html(
        session,
        LIST_URL,
        params=list_params(region, keyword, 1, kind),
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")

    count_element = soup.select_one("div.list-sort > p > strong")
    if not count_element:
        count_element = soup.select_one("main div.list-sort strong")
    count_text = element_text(count_element)
    if not count_text:
        raise ValueError("找不到搜尋結果總筆數，591 網頁結構可能已變更")

    match = re.search(r"[\d,]+", count_text)
    if not match:
        raise ValueError(f"無法解析搜尋結果總筆數：{count_text}")
    total_count = int(match.group(0).replace(",", ""))
    return max(1, math.ceil(total_count / 30))


def relative_date(text: str | None, now: datetime | None = None) -> str | None:
    if not text:
        return None
    now = now or now_taipei()
    minute_match = re.search(r"(\d+)\s*分鐘(?:內|前)更新", text)
    hour_match = re.search(r"(\d+)\s*小時(?:內|前)更新", text)
    day_match = re.search(r"(\d+)\s*天前更新", text)
    if minute_match:
        value = now - timedelta(minutes=int(minute_match.group(1)))
    elif hour_match:
        value = now - timedelta(hours=int(hour_match.group(1)))
    elif day_match:
        value = now - timedelta(days=int(day_match.group(1)))
    elif "昨日更新" in text:
        value = now - timedelta(days=1)
    else:
        return None
    return value.strftime("%Y-%m-%d")


def parse_rent(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"[\d,]+", text)
    return int(match.group(0).replace(",", "")) if match else None


def find_listings(
    session: requests.Session,
    *,
    region: int,
    keyword: str | None,
    page: int,
    kind: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    response = request_html(
        session,
        LIST_URL,
        params=list_params(region, keyword, page, kind),
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    recorded_at = now_taipei().replace(microsecond=0).isoformat()
    houses: list[dict[str, Any]] = []
    histories: list[dict[str, Any]] = []

    for item in soup.select("main div.item[data-id]"):
        house_id = item.get("data-id")
        if not house_id:
            continue
        update_node = item.select_one("div.item-info-txt.role-name span.line:nth-child(2)")
        rent_node = item.select_one("strong.text-26px.font-arial div.inline-flex-row")
        if not rent_node:
            rent_node = item.select_one("strong.text-26px.font-arial")
        update_text = element_text(update_node)
        rent = parse_rent(element_text(rent_node))
        houses.append(
            {
                "house_id": str(house_id),
                "history_date": relative_date(update_text),
            }
        )
        if rent is not None:
            histories.append(
                {
                    "house_id": str(house_id),
                    "recorded_at": recorded_at,
                    "rent": rent,
                }
            )
    return houses, histories


def label_value(soup: BeautifulSoup, label_keyword: str) -> str | None:
    for item in soup.select("div.desc-item"):
        label = element_text(item.select_one("span.desc-label"))
        if label and label_keyword in label:
            return element_text(item.select_one("span.desc-value"))
    return None


def surrounding_texts(soup: BeautifulSoup, index: int, class_name: str) -> list[str]:
    block = soup.select_one(f"div.surround-list > div:nth-child({index})")
    if not block:
        return []
    main = block.select_one(f"div.surround-list-box.{class_name} p span")
    secondary = block.select("div.surround-list-text p span")
    return unique_nonempty([element_text(main), *(element_text(x) for x in secondary)])


def parse_upload_date(upload_text: str | None, now: datetime | None = None) -> str | None:
    if not upload_text:
        return None
    now = now or now_taipei()
    day_match = re.search(r"(\d+)\s*天前發佈", upload_text)
    if day_match:
        return (now - timedelta(days=int(day_match.group(1)))).strftime("%Y-%m-%d")
    date_match = re.search(r"(\d+)\s*月\s*(\d+)\s*日發佈", upload_text)
    if date_match:
        parsed = datetime(
            now.year,
            int(date_match.group(1)),
            int(date_match.group(2)),
            tzinfo=TAIPEI_TZ,
        )
        if parsed.date() > now.date():
            parsed = parsed.replace(year=now.year - 1)
        return parsed.strftime("%Y-%m-%d")
    if "小時" in upload_text or "分鐘" in upload_text or "剛剛" in upload_text:
        return now.strftime("%Y-%m-%d")
    return None


def extract_images(soup: BeautifulSoup) -> list[str]:
    script = soup.select_one("#rent-detail-structured-data")
    if not script or not script.string:
        return []
    try:
        structured = json.loads(script.string)
    except (TypeError, json.JSONDecodeError):
        return []
    graphs = structured.get("@graph", []) if isinstance(structured, dict) else []
    for item in graphs:
        images = item.get("image") if isinstance(item, dict) else None
        if isinstance(images, str):
            images = [images]
        if isinstance(images, list):
            return unique_nonempty(
                image for image in images if isinstance(image, str) and "(null)" not in image
            )
    return []


def find_house_detail(
    session: requests.Session,
    house_id: str,
    kind: int,
) -> tuple[dict[str, Any] | None, int | None, str | None]:
    url = f"{BASE_URL}/{house_id}"
    try:
        response = request_html(session, url)
    except requests.RequestException as exc:
        return None, None, str(exc)

    if response.status_code != 200:
        return None, response.status_code, f"HTTP {response.status_code}"

    try:
        soup = BeautifulSoup(response.text, "lxml")
        title = select_text(soup, ".title > h1")
        crumb_id = select_text(soup, "section.crumbs > span")
        parsed_id = re.sub(r"\D", "", crumb_id or "") or str(house_id)

        pattern_block = soup.select_one("div.pattern")
        pattern_spans = pattern_block.select("span") if pattern_block else []
        pattern_values = unique_nonempty(element_text(span) for span in pattern_spans)
        pattern_text = next(
            (x for x in pattern_values if re.search(r"房|廳|衛|開放式|套房|雅房", x)),
            None,
        )
        sqm_text = next((x for x in pattern_values if "坪" in x), None)
        floor_text = next(
            (x for x in pattern_values if re.search(r"(?:F|樓|整棟|頂樓|頂層)", x)),
            None,
        )

        rent_text = select_text(soup, "div.house-price span strong")
        rent = parse_rent(rent_text)
        address = select_text(soup, "div.block.surround div.address p span.load-map div")
        if not address:
            address = select_text(soup, "div.block.surround div.address")

        facility = soup.select_one("section.block.service div.facility")
        facility_text = (
            unique_nonempty(element_text(x) for x in facility.select(":scope > dl:not(.del)"))
            if facility
            else []
        )

        value_texts = unique_nonempty(
            element_text(span) for span in soup.select("span.desc-value")
        )
        pet_text = next((x for x in value_texts if "寵物" in x), None)
        cook_text = next((x for x in value_texts if "開伙" in x), None)
        rental_period = label_value(soup, "最短租期")
        if rental_period is None:
            rental_period = label_value(soup, "租期")

        description_node = soup.select_one("section.block.house-condition div.article.t5-rich-editor")
        description = element_text(description_node)
        upload_text = select_text(soup, "section.contact-tip div.publish-info")

        data = {
            "title": title,
            "source_listing_id": parsed_id,
            "source_url": url,
            "pattern_text": pattern_text,
            "rent": rent,
            "identity_text": label_value(soup, "身份要求"),
            "sqm_text": sqm_text,
            "floor_text": floor_text,
            "full_address": address,
            "transportation_text": surrounding_texts(soup, 1, "traffic"),
            "activity_text": surrounding_texts(soup, 2, "live"),
            "education_text": surrounding_texts(soup, 3, "education"),
            "facility_text": facility_text,
            "pet_text": pet_text,
            "cook_text": cook_text,
            "rental_period": rental_period,
            "description": description,
            "upload_text": upload_text,
            "upload_date": parse_upload_date(upload_text),
            "crawled_time": now_taipei().replace(microsecond=0).isoformat(),
            "kind": kind,
            "source": 591,
            "images": extract_images(soup),
        }
        if not title and rent is None:
            return None, response.status_code, "詳細頁必要欄位不存在，網頁結構可能已變更"
        return data, response.status_code, None
    except Exception as exc:  # 單筆解析失敗不應中斷整批爬取
        return None, response.status_code, f"{type(exc).__name__}: {exc}"


def read_jsonl(path: Path) -> list[Any]:
    rows: list[Any] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                print(f"警告：{path.name} 第 {line_number} 行不是有效 JSON，已略過：{exc}")
    return rows


def append_jsonl(handle: Any, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    handle.flush()


def crawl_kind(
    session: requests.Session,
    data_dir: Path,
    *,
    region: int,
    keyword: str | None,
    kind: int,
    limit: int | None,
    retry_failed: bool,
    min_delay: float,
    max_delay: float,
) -> None:
    id_path = data_dir / f"all_house_id_{kind}.jsonl"
    data_path = data_dir / f"all_house_data_{kind}.jsonl"
    failed_path = data_dir / f"failed_house_data_{kind}.jsonl"
    history_path = data_dir / f"rent_history_{kind}.jsonl"

    existing_ids = read_jsonl(id_path)
    known_ids = {
        str(row.get("house_id"))
        for row in existing_ids
        if isinstance(row, dict) and row.get("house_id") is not None
    }

    max_pages = get_max_pages(session, region=region, keyword=keyword, kind=kind)
    print(f"[kind={kind}] 找到 {max_pages} 頁，開始取得房屋列表")
    with id_path.open("a", encoding="utf-8") as id_file, history_path.open(
        "a", encoding="utf-8"
    ) as history_file:
        for page in range(1, max_pages + 1):
            houses, histories = find_listings(
                session,
                region=region,
                keyword=keyword,
                page=page,
                kind=kind,
            )
            for house in houses:
                house_id = house["house_id"]
                if house_id not in known_ids:
                    append_jsonl(id_file, house)
                    existing_ids.append(house)
                    known_ids.add(house_id)
            for history in histories:
                append_jsonl(history_file, history)
            print(f"[kind={kind}] 列表第 {page}/{max_pages} 頁：{len(houses)} 筆")
            if page < max_pages:
                time.sleep(random.uniform(min_delay, max_delay))

    completed_ids = {
        str(row.get("source_listing_id") or row.get("house_id"))
        for row in read_jsonl(data_path)
        if isinstance(row, dict) and (row.get("source_listing_id") or row.get("house_id"))
    }
    failed_ids = {
        str(row.get("house_id"))
        for row in read_jsonl(failed_path)
        if isinstance(row, dict) and row.get("house_id") is not None
    }
    skipped_ids = completed_ids if retry_failed else completed_ids | failed_ids

    ordered_ids: list[str] = []
    seen: set[str] = set()
    for row in existing_ids:
        house_id = str(row.get("house_id")) if isinstance(row, dict) else ""
        if house_id and house_id not in seen:
            seen.add(house_id)
            ordered_ids.append(house_id)

    pending_ids = [house_id for house_id in ordered_ids if house_id not in skipped_ids]
    if limit is not None:
        pending_ids = pending_ids[:limit]
    print(
        f"[kind={kind}] ID 共 {len(ordered_ids)} 筆；已處理 {len(skipped_ids)} 筆；"
        f"本次預計處理 {len(pending_ids)} 筆"
    )

    success_count = 0
    failed_count = 0
    with data_path.open("a", encoding="utf-8") as data_file, failed_path.open(
        "a", encoding="utf-8"
    ) as failed_file:
        for index, house_id in enumerate(pending_ids, start=1):
            detail, status_code, error = find_house_detail(session, house_id, kind)
            if detail is not None:
                append_jsonl(data_file, detail)
                success_count += 1
                outcome = "成功"
            else:
                append_jsonl(
                    failed_file,
                    {
                        "house_id": house_id,
                        "status_code": status_code,
                        "failed_time": now_taipei().replace(microsecond=0).isoformat(),
                        "error": error,
                    },
                )
                failed_count += 1
                outcome = f"失敗（{error}）"
            print(f"[kind={kind}] 詳細資料 {index}/{len(pending_ids)}，ID {house_id}：{outcome}")
            if index < len(pending_ids):
                time.sleep(random.uniform(min_delay, max_delay))
    print(f"[kind={kind}] 完成：成功 {success_count} 筆，失敗 {failed_count} 筆")


def dedupe_key(prefix: str, row: Any) -> str:
    if not isinstance(row, dict):
        return json.dumps(row, ensure_ascii=False, sort_keys=True)
    if prefix == "all_house_id":
        return str(row.get("house_id"))
    if prefix == "all_house_data":
        return str(row.get("source_listing_id") or row.get("house_id"))
    if prefix == "failed_house_data":
        return str(row.get("house_id"))
    if prefix == "rent_history":
        return "|".join(
            str(row.get(field)) for field in ("house_id", "recorded_at", "rent")
        )
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def merge_jsonl_groups(data_dir: Path, output_dir: Path) -> dict[str, Path]:
    """將 1、2、3、4 四種 kind 合併；重複鍵保留最後一筆。"""
    output_dir.mkdir(parents=True, exist_ok=True)
    outputs: dict[str, Path] = {}
    for prefix in (
        "all_house_id",
        "all_house_data",
        "failed_house_data",
        "rent_history",
    ):
        merged: dict[str, Any] = {}
        for kind in DEFAULT_KINDS:
            source_path = data_dir / f"{prefix}_{kind}.jsonl"
            if not source_path.exists():
                print(f"警告：找不到 {source_path.name}，該檔案視為空資料")
                continue
            for row in read_jsonl(source_path):
                merged[dedupe_key(prefix, row)] = row
        output_path = output_dir / f"{prefix}_merged.json"
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(list(merged.values()), handle, ensure_ascii=False, indent=2)
        outputs[prefix] = output_path
        print(f"已合併 {len(merged)} 筆 -> {output_path}")
    return outputs


def parse_args() -> argparse.Namespace:
    project_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region", type=int, default=1, help="縣市代碼，預設 1（台北市）")
    parser.add_argument("--keyword", default=None, help="搜尋關鍵字")
    parser.add_argument(
        "--kinds",
        type=int,
        nargs="+",
        default=list(DEFAULT_KINDS),
        help="房屋類型，預設 1 2 3 4",
    )
    parser.add_argument("--limit", type=int, default=None, help="每個 kind 最多抓取幾筆詳細資料")
    parser.add_argument("--retry-failed", action="store_true", help="重新嘗試 failed JSONL 內的 ID")
    parser.add_argument("--merge-only", action="store_true", help="不爬網，只合併既有 JSONL")
    parser.add_argument("--data-dir", type=Path, default=project_dir, help="JSONL 所在目錄")
    parser.add_argument("--output-dir", type=Path, default=project_dir / "output", help="JSON 輸出目錄")
    parser.add_argument("--min-delay", type=float, default=1.0, help="請求間最短等待秒數")
    parser.add_argument("--max-delay", type=float, default=2.5, help="請求間最長等待秒數")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.data_dir = args.data_dir.resolve()
    args.output_dir = args.output_dir.resolve()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    if args.min_delay < 0 or args.max_delay < args.min_delay:
        raise ValueError("等待秒數必須符合 0 <= min-delay <= max-delay")
    invalid_kinds = sorted(set(args.kinds) - set(DEFAULT_KINDS))
    if invalid_kinds:
        raise ValueError(f"本程式的合併流程只支援 kind 1、2、3、4：{invalid_kinds}")

    if not args.merge_only:
        session = requests.Session()
        session.headers.update(HEADERS)
        for kind in args.kinds:
            crawl_kind(
                session,
                args.data_dir,
                region=args.region,
                keyword=args.keyword,
                kind=kind,
                limit=args.limit,
                retry_failed=args.retry_failed,
                min_delay=args.min_delay,
                max_delay=args.max_delay,
            )

    outputs = merge_jsonl_groups(args.data_dir, args.output_dir)
    print("全部完成：")
    for path in outputs.values():
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n使用者中止；已寫入的 JSONL 可供下次續跑。", file=sys.stderr)
        raise SystemExit(130)
