import requests
from bs4 import BeautifulSoup as bs


def get_text(soup, selector):
    element = soup.select_one(selector)
    return element.get_text(strip=True) if element else None

    

def find_house(region = 1,keyword=None,page = 1):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = "https://rent.591.com.tw/list?"
    job_params = {
        "region" : 1,
        "page" : 1,
        #keyword : "",
    }

    if keyword is not None:
        job_params['keyword']=keyword
    if region != 1:
        job_params['region']=region
    if page != 1:
        job_params['page']=page

    res = requests.get(url,headers=custom_headers,params=job_params)
    if res.status_code == 200:
        try:
            print("成功取得房屋列表")
            soup = bs(res.text, 'lxml')
            house_list = soup.select("main > div > div.item[data-id]")
            house_id_list = [
                item.get("data-id")
                for item in house_list
            ]
            return house_id_list
            #print(type(main_content))
        except Exception as e:
            print(e)
            print(res.text[:200])
    #print(res.status_code)
    #print(data)

#find_house(region=1)

def get_max_pages(region = 1,keyword=None,page = 1):
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
        "Referer": "https://rent.591.com.tw/"
    }
    url = "https://rent.591.com.tw/list?"
    job_params = {
        "region" : 1,
        "page" : 1,
        #keyword : "",
    }
    max_pages=99999

    

    if keyword is not None:
        job_params['keyword']=keyword
    if region != 1:
        job_params['region']=region
    if page != 1:
        job_params['page']=page
    
    res = requests.get(url,headers=custom_headers,params=job_params)
    soup = bs(res.text, 'lxml')

    if max_pages == 99999:
        max_pages = round(int(soup.select_one("#__nuxt > div:nth-child(4) > div.list-wrapper > main > div.list-sort > p > strong").get_text(strip=True).replace(",", ""))  / 30)
        print(max_pages)
    return max_pages


def find_houseID(id):
    custom_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36",
            "Referer": "https://rent.591.com.tw/"
        }
    url = f"https://rent.591.com.tw/{id}"
    
    #print(res.status_code)
    
    try:
        res = requests.get(url,headers=custom_headers)
        
        
        #main_content = soup.select_one("#__nuxt > div:nth-child(4) > div.list-wrapper > main > div:nth-child(5) > div")
        if res.status_code == 200:
            print(f"成功取得{id}的資料")
            soup = bs(res.text, 'lxml')
            title = get_text(soup,".title > h1")
            pattern = get_text(soup, ".pattern > span[data-v-b5702979]")
            rent = get_text(soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.house-price > span > strong")
            sqm = get_text(soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.house-detail > div > section:nth-child(1) > div.section-content > div:nth-child(2) > div:nth-child(1) > span.value")
            floor = get_text(soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.pattern > span:nth-child(5)")
            
            address = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.address > p:nth-child(1) > span.load-map > div")
            facility = soup.select_one("#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div.facility")
            facility_list = [
            x.get_text(strip=True)
            for x in facility.select(":scope > dl:not(.del)")
            ]
            rental_period = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div:nth-child(2) > div > div > div:nth-child(1) > span.desc-value")
            pet = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.service > div:nth-child(2) > div > div > div:nth-child(4) > span.desc-value")
            transportation_list = []
            #rent = soup.select_one("#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.info-board > div.house-price > span > strong")
            transportation_main = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(1) > div.surround-list-box.traffic > p > span")
            transportation_sup1 = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(1) > div.surround-list-text > p:nth-child(1) > span")
            transportation_sup2 = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(1) > div.surround-list-text > p:nth-child(2) > span")
            for value in [
                transportation_main,transportation_sup1,transportation_sup2
            ]:
                if value is not None:
                    transportation_list.append(value)
            
            activity_list =[]
            activity_main = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(2) > div.surround-list-box.live > p > span")
            activity_sup1 = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(2) > div.surround-list-text > p.icon-restaurant > span")
            activity_sup2 = get_text(soup,"#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(2) > div.surround-list-text > p.icon- > span")
            for value in [
                activity_main, activity_sup1,activity_sup2
            ]:
                if value is not None:
                    activity_list.append(value)
            
            education_list = []
            education_main = get_text(soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(3) > div.surround-list-box.education > p > span")
            education_sup1 = get_text(soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(3) > div.surround-list-text > p.icon-secondary > span")
            education_sup2 = get_text(soup, "#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.surround > div.surround-list > div:nth-child(3) > div.surround-list-text > p.icon- > span")
            for value in [
                education_main,education_sup1,education_sup2
            ]:
                if value is not None:
                    education_list.append(value)
            
            description_unfiltered = soup.select_one("#__nuxt > section:nth-child(3) > section.main-wrapper > section.main-content > section.block.house-condition > div.house-condition-content > div.article.t5-rich-editor")
            if description_unfiltered:
                description = " ".join(
                description_unfiltered.get_text().replace("\xa0", " ").split())
            else:
                description = None
            house_data = {
                "title": title,
                "pattern": pattern,
                "rent": rent,
                "sqm": sqm,
                "floor": floor,
                "address": address,
                "transportation": transportation_list,
                "activity" : activity_list,
                "education": education_list,
                "facility": facility_list,
                "rental_period": rental_period,
                "pet": pet,
                "description": description
            }
            return house_data
            

        elif res.status_code == 403:
            return None

        elif res.status_code == 404:
            return None
        
    except Exception as e:
        print(f"網頁請求失敗: {e}")
        return None

    
