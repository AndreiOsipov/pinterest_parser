import time
import os

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys


from selenium.webdriver.remote.webelement import WebElement


class Downloader:
    def __init__(self) -> None:
        self.url = 'https://ru.pinterest.com/search/pins/?q=q&rs=typed'
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        self.waiter = WebDriverWait(self.driver,timeout=500)
        self.this_dir = os.path.abspath(os.path.dirname(__file__))
        
    def _get_image_src_from_container(self, image_container:WebElement):
        for i in range(3):
            try:
                return image_container.find_element(by=By.TAG_NAME, value='img').get_attribute('src')
            except:
                time.sleep(2)
        return None

    def _find_image_containers(self):
        return self.waiter.until(EC.presence_of_all_elements_located((By.XPATH, "//div[@role='listitem']")))
    
    def _makedir_if_not_exist(self, dir_name):
        if not(os.path.exists(dir_name)):
            os.makedirs(dir_name)
    
    def _get_images_src(self, person_name, number_of_photos):
        search_bar = self.waiter.until(EC.element_to_be_clickable((By.TAG_NAME,'input')))
        search_bar.send_keys(Keys.BACK_SPACE)
        search_bar.send_keys(person_name+'\n')
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

        download_dir = os.path.join(self.this_dir, 'image_downloads')
        self._makedir_if_not_exist(download_dir)
        person_dir_name = os.path.join(download_dir, person_name) 
        self._makedir_if_not_exist(person_dir_name)
        
        image_srcs = self._get_images_src(person_name, number_of_photos)
        person_dir_name_images = os.path.join(person_dir_name,'images')
        self._makedir_if_not_exist(person_dir_name_images)

        for ind, src in enumerate(image_srcs):
            try:
                resp = requests.get(src)
                with open(os.path.join(person_dir_name_images, f'img_{ind}.jpg'), mode='wb') as image_file:
                    image_file.write(resp.content)
                with open(os.path.join(person_dir_name, 'srcs.txt'),mode='a') as srcs_file:
                    srcs_file.write(src+'\n')
            except:
                print(f'невалидный url: {src}')
def main():
    file_name = input(f'введи путь файла, в котором лежат имена людей (по умолчанию ищет в names.txt) ')
    if file_name == '':
        file_name = 'names.txt'
    downloader = Downloader()
    with open('names.txt', 'r') as file:
        for name in file:
            downloader.download_person_images(name[0:-2], 100)

if __name__ == '__main__':
    main()