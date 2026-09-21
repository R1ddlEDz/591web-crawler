import os
import json
import requests
from pathlib import Path
from time import sleep
import random


def download_house_images(
        json_path,
        output_folder='house_images'):

    output_path = Path(output_folder)
    output_path.mkdir(parents=True, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        house_data = json.load(f)

    session = requests.Session()

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36'
    }

    for house in house_data:
        house_id = house.get('source_listing_id')
        images = house.get('images', [])

        if house_id is None:
            continue

        if not images:
            continue

        house_folder = output_path / str(house_id)
        house_folder.mkdir(parents=True, exist_ok=True)

        print(f"開始下載{house_id}，共{len(images)}張圖片")

        for index, image_url in enumerate(images, start=1):
            file_name = f"{house_id}_{index:03d}.jpg"
            file_path = house_folder / file_name

            if file_path.exists():
                print(f"已存在，跳過：{file_name}")
                continue

            try:
                response = session.get(
                    image_url,
                    headers=headers,
                    timeout=15
                )

                if response.status_code == 429:
                    print("請求太頻繁，暫停較長時間")
                    sleep(30)
                    continue

                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "")

                if not content_type.startswith("image/"):
                    continue

                with open(file_path, 'wb') as f:
                    f.write(response.content)

                print(f"{file_name}下載成功")
                sleep(random.uniform(0.1, 0.4))

            except requests.RequestException as e:
                print(f"{image_url}下載失敗")
                print(f"錯誤: {e}")

        sleep(random.uniform(0.5, 1.5))
