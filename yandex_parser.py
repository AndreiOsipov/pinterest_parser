import os
import json
import time
import csv
import requests
import io


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement

from PIL import Image

class Size:
    def __init__(self):
        self.large = 'large'
        self.medium = 'medium'
        self.small = 'small'


class Preview:
    def __init__(self, url: str,
                 width: int,
                 height: int):
        self.url = url
        self.width = width
        self.height = height
        self.size = str(width) + '*' + str(height)


class Result:
    def __init__(self, title: (str, None),
                 description: (str, None),
                 domain: str,
                 url: str,
                 width: int,
                 height: int,
                 preview: Preview):
        self.title = title
        self.description = description
        self.domain = domain
        self.url = url
        self.width = width
        self.height = height
        self.size = str(width) + '*' + str(height)
        self.preview = preview


class YandexImage:
    def __init__(self):
        self.size = Size()
        self.version = '1.0-release'
        self.about = 'Yandex Images Parser'
        self.driver = webdriver.Chrome()
        self.waiter = WebDriverWait(self.driver,timeout=5)

    def _start_search(self, query: str):
        search_bar = self.waiter.until(EC.element_to_be_clickable((By.NAME, 'text')))
        for i in range(40):
            search_bar.send_keys(Keys.BACK_SPACE)
        search_bar.send_keys(query+'\n')#вводит запрос + начинает поиск      
    
    def _find_more_pictures_button(self):
        btns = self.driver.find_elements(By.XPATH, "//button[@CLASS='Button2 Button2_size_l Button2_view_action Button2_width_max SerpList-LoadButton']")
        if len(btns)>0:
            return btns[0]
    
    def search(self, query: str, sizes: Size = 'large') -> list:
        
        self.driver.get('https://yandex.ru/images/search')
        self._start_search(query)
        time.sleep(5)
        items_place = self.driver.find_element(By.CLASS_NAME, "serp-list")
        
        output = list()
        start_time = time.time()
        while len(output) < 100 and (time.time() - start_time < 600):
            more_pictures_button = self._find_more_pictures_button()
            if more_pictures_button:
                more_pictures_button.click()
            try:
                items = self.waiter.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "serp-item")))
                # items = items_place.find_elements(By.CLASS_NAME, "serp-item")
            except AttributeError:
                return output
            
            for item in items:
                data = json.loads(item.get_attribute("data-bem"))
                image = data['serp-item']['img_href']
                image_width = data['serp-item']['preview'][0]['w']
                image_height = data['serp-item']['preview'][0]['h']

                snippet = data['serp-item']['snippet']
                try:
                    title = snippet['title']
                except KeyError:
                    title = None
                try:
                    description = snippet['text']
                except KeyError:
                    description = None
                domain = snippet['domain']

                preview = 'https:' + data['serp-item']['thumb']['url']
                preview_width = data['serp-item']['thumb']['size']['width']
                preview_height = data['serp-item']['thumb']['size']['height']

                res = Result(title, description, domain, image,
                                    image_width, image_height,
                                    Preview(preview, preview_width, preview_height))
                if not(res.url in output): 
                    output.append(res.url)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # time.sleep(1)
            print(f'текущая длинна: {len(output)}')
        return output
    

class ImgeDownloader:
    def makedir_if_not_exist(self, dir_name):
        if not(os.path.exists(dir_name)):
            os.makedirs(dir_name)

    def download_image_from_links(self, person_dir_name:str, link_list):

        this_dir = os.path.dirname(os.path.abspath(__file__))
        yandex_images_path = os.path.join(this_dir, 'yandex_downloads')
        persond_path = os.path.join(yandex_images_path, person_dir_name)

        images_path = os.path.join(persond_path, 'images')
        links_path = os.path.join(persond_path, 'links.csv')

        self.makedir_if_not_exist(yandex_images_path)
        self.makedir_if_not_exist(persond_path)
        self.makedir_if_not_exist(images_path)

        with open(links_path, 'a',newline='') as file:
            writter = csv.writer(file)
            writter.writerow(['src'])

            for ind, src in enumerate(link_list):
                try:
                    resp = requests.get(src)
                
                    # img:Image.Image = Image.open(io.BytesIO(resp.content))
                    # width, height = img.size
                    # if height > 720:
                    with open(os.path.join(images_path, f'img_{ind}.jpg'), mode='wb') as image_file:
                        image_file.write(resp.content)
                    writter.writerow([src])
                except:
                    print(f'невалидный url: {src}')

def prepare_name(raw_name: str):
    return raw_name.replace('\n', '').replace('_', ' ')

def main():
    file_name = input(f'введи путь файла, в котором лежат имена людей (по умолчанию ищет в names.txt) ')
    if file_name == '':
        file_name = 'names.txt'

    parser = YandexImage()
    downloader = ImgeDownloader()
    with open(file_name, 'r') as file:
        for raw_name in file:
            prepared_name = prepare_name(raw_name)
            links = parser.search(prepared_name)
            downloader.download_image_from_links(prepared_name, links)
main()
