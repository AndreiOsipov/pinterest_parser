import time
import os
import io
import requests
import csv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from PIL import Image

def makedir_if_not_exist(dir_name):
    if not(os.path.exists(dir_name)):
        os.makedirs(dir_name)

class Downloader:
    def __init__(self) -> None:
        self.url = 'https://ru.pinterest.com/search/pins/?q=q&rs=typed'
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        self.waiter = WebDriverWait(self.driver,timeout=5)
        self.this_dir = os.path.abspath(os.path.dirname(__file__))
        self.download_dir = os.path.join(self.this_dir, 'image_downloads')
        
    def _get_image_src_from_container(self, image_container:WebElement):
        for i in range(2):
            try:
                return image_container.find_element(by=By.TAG_NAME, value='img').get_attribute('src')
            except:
                time.sleep(2)
        return None

    def _find_image_containers(self):
        return self.waiter.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='listitem']")))
    
    def _make_dirs(self, person_dir_name, person_dir_name_images):
        makedir_if_not_exist(self.download_dir)
        makedir_if_not_exist(person_dir_name)
        makedir_if_not_exist(person_dir_name_images)
    
    def _start_search(self, person_name):
        search_bar: WebElement = self.waiter.until(EC.element_to_be_clickable((By.TAG_NAME,'input')))
        
        #убирает последний введенный запрос из строки ввода(по уму надо делать обертку над search-bar, но похуй)
        for i in range(40):
            search_bar.send_keys(Keys.BACK_SPACE)
        
        search_bar.send_keys(person_name+'\n')#вводит запрос + начинает поиск

    def _get_images_src(self, person_name, number_of_photos):
        self._start_search(person_name)

        image_links = []

        while len(image_links) <= number_of_photos:
        
            found_image_containers = self._find_image_containers()
            for found_container in found_image_containers:
                image_src = self._get_image_src_from_container(found_container)
                if not(image_src is None) and not(image_src in image_links):
                    image_links.append(image_src)
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        return image_links
    

    def download_person_images(self, person_name: str, number_of_photos=150):

        person_dir_name = os.path.join(self.download_dir, person_name) 
        person_dir_name_images = os.path.join(person_dir_name,'images')
        self._make_dirs(person_dir_name, person_dir_name_images)

        image_srcs = self._get_images_src(person_name, number_of_photos)

        with open(os.path.join(person_dir_name, 'srcs.csv'),mode='a',newline='') as srcs_file:
            writter = csv.writer(srcs_file)
            writter.writerow(['src','height', 'width'])
            for ind, src in enumerate(image_srcs):
                try:
                    resp = requests.get(src)
                
                    img:Image.Image = Image.open(io.BytesIO(resp.content))
                    width, height = img.size
                    # if height > 720:
                    with open(os.path.join(person_dir_name_images, f'img_{ind}.jpg'), mode='wb') as image_file:
                        image_file.write(resp.content)
                        writter.writerow([src, str(height), str(width)])
                except:
                    print(f'невалидный url: {src}')

def prepare_name(raw_name: str):
    return raw_name.replace('\n', '').replace('_', ' ')

def main():
    file_name = input(f'введи путь файла, в котором лежат имена людей (по умолчанию ищет в names.txt) ')
    if file_name == '':
        file_name = 'names.txt'
    downloader = Downloader()
    with open('names.txt', 'r') as file:
        for raw_name in file:
            prepared_name = prepare_name(raw_name)
            downloader.download_person_images(prepared_name)

if __name__ == '__main__':
    main()