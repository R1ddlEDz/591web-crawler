from crawler.utils import *

# region(縣市) 默認為台北市 1=台北市, 3=新北市, 6=桃園市, 8=台中市, 15=台南市, 17=高雄市
# keyword(關鍵字) 默認為空
# page(頁數) 默認為第一頁 一頁有30個房屋列表
# kind(類型) 默認為1 | 1=整層住家, 2=獨立套房, 3=分租套房, 4=雅房, 8=車位, 24=其他

# start_591crawler(region=1, keyword=None, page=1, kind=24)
# 只單一跑特定房屋種類的爬蟲


# export_house_data_json()
# 使用start_591crawler後會自動轉換jsnol成json檔 此函式是方便直接將all_house_data.jsonl轉換用的(不用再爬一次)

start_591crawler_all()

# 按照清單裡面的房屋類型進行爬蟲
