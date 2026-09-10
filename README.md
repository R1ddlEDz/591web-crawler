# 591租屋網爬蟲 (591web-crawler)
**使用前請先安裝虛擬環境以及安裝Requirement.txt**

**Before use, please install venv and requirements.txt first.** 
```bash
pip install -r requirements.txt
```

## 函式功能介紹 Functions
* **start_591crawler()** 此函式會使用下方介紹的函式，並且用迴圈把所有的資料寫到該資料夾裡
    
   ```text
   括號裡可以使用以下介紹的參數來更改，默認值也跟下方一樣
   使用後會獲得3個jsonl的檔案:
   1. all_house_id.jsonl -> 裡面有房屋ID 以及當下房屋上傳/更新的日期
   2. all_house_data.jsonl -> 裡面有跟上方順序一樣的房屋詳細資料
   3. failed_house_id.jsonl -> 當上方獲得房屋詳細資料失敗時會被記錄到該文件檔，以供未來方便重新爬蟲/找BUG
   4. failed_house_data.jsonl -> 會回傳固定格式(status_code, 房子ID, 錯誤時間) 到該文件檔
   ```
   
* get_text(soup,selector) 此函式會抓取標籤裡的文字，若裡面沒東西則會顯示 **None** (不須使用)
* find_house(region=1, keyword=None, page=1, kind=(1,2,3,4)) 會回傳特定頁數的房屋ID List
    * region(縣市) 默認為台北市 1=台北市, 3=新北市, 6=桃園市, 8=台中市, 15=台南市, 17=高雄市
    * keyword(關鍵字) 默認為空
    * page(頁數) 默認為第一頁 一頁有30個房屋列表
    * kind(類型) 默認為1,2,3,4 | 1=整層住家, 2=獨立套房, 3=分租套房, 4=雅房, 8=車位, 24=其他
* get_max_pages(region=1, keyword=None, page=1) 會回傳該搜尋結果的最大頁數
* find_houseID(id) 會搜尋指定房屋ID的詳細資料
    * 標題，房型，租金，坪數，層數，地址，交通，生活，教育，設備，最短租期，養寵物，屋況介紹以及該該房屋的所有圖片URL


## 使用方法
在bash裡使用 python crawler/utils.py後，將會自動開始爬蟲。若需要改其他縣市請新建檔案並import utils.py到該Python檔:
```python
from crawler.utils import *
start_591crawler(region=1, keyword=None, page=1, kind=(1,2,3,4))
```

為了避免讓伺服器負載，再加上爬蟲的資料太大量，將會花費5-15小時進行爬蟲。若要終止請在bash裡使用ctrl+c(但檔案應該不會留下來)。

## 待新增功能
目前還少了比對ID的房屋上傳/更新日期的功能， 未來將會新增使其自動化並且記錄房租增幅的紀錄。

## 已知問題
如果網頁傳回403 / 404，會在資料裡面新增一行"null"

不將"null"寫入房屋資料裡

暫時加入if else偵測status_code 如果是403/404 則會回傳以下資料到failed_house_data.jsonl
```python
"house_id": id,
"status_code": status_code,
"failed_time": YYYY-MM-DD HH:MM:SS
```
並且還會再傳house_id到failed_hose_id.jsonl

