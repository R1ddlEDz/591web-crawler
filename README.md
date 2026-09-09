# 591租屋網爬蟲 (591web-crawler)
**使用前請先安裝虛擬環境以及安裝Requirement.txt**

**Before use, please install venv and requirements.txt first.** 
```bash
pip install -r requirements.txt

```

## 函式功能介紹 Functions

* get_text(soup,selector) 此函式會抓取標籤裡的文字，若裡面沒東西則會顯示 **None** (不須使用)
* find_house(region=1, keyword=None, page=1) 會回傳特定頁數的房屋ID List
    * region(縣市) 1=台北市, 3=新北市, 6=桃園市, 8=台中市, 15=台南市, 17=高雄市
    * keyword(關鍵字) 默認為空
    * page(頁數) 默認為第一頁 一頁有30個房屋列表
* get_max_pages(region=1, keyword=None, page=1) 會回傳該搜尋結果的最大頁數
* find_houseID(id) 會搜尋指定房屋ID的詳細資料
    * 標題，房型，租金，坪數，層數，地址，交通，生活，教育，設備，最短租期，養寵物，屋況介紹以及該該房屋的所有圖片URL


## 使用方法
在bash裡使用 python main.py後，將會自動開始爬蟲。默認為台北市，若需要改其他縣市請編輯第12行CODE:
```python
house_id_list = find_house(page,region=1)
```
為了避免讓伺服器負載，再加上爬蟲的資料太大量，將會花費5-15小時進行爬蟲。若要終止請在bash裡使用ctrl+c(但檔案應該不會留下來)。最後爬完後會產生出3個JSON檔案:

all_house_id.json(該篩選的所有房屋ID)

all_house_data.json(所有房屋的資料)

failed_house_id.json(所有沒獲取資料的房屋ID)