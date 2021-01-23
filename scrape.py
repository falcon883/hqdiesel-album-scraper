import shutil
import sys
import time

from pathlib import Path
from bs4 import BeautifulSoup
from requests import Session
from tqdm.contrib.concurrent import thread_map


class Scrape(object):
    def __init__(self):
        self.package_dir = Path(__file__).parent.absolute()
        self.file_path = self.package_dir.joinpath("")
        self.session = Session()
        self.url = input("Enter hqdiesel Album Url: ")
        self.page_title = ""
        self.total_pages = 0
        self.image_urls = list()
        print("Getting Images")
        self.get_images()

    def get_images(self):
        with self.session as s:
            print("Scraping Image Urls...")
            self.get_image_urls(s, self.url, page_count=True, page_title=True)

            print(f"Found Total {self.total_pages} Pages")

            print("Scraping On Page: ", 1)
            if self.total_pages > 1:
                for i in range(2, self.total_pages + 1):
                    print("Scraping On Page: ", i)
                    self.get_image_urls(s, f"{self.url}&page={i}")
                    time.sleep(1.5)

            print(f"Found {len(self.image_urls)} Images")

            thread_map(self._download_images, range(0, len(self.image_urls)), max_workers=2)

    def get_image_urls(self, s, url, page_count=False, page_title=False):
        r = s.get(url)
        bs = BeautifulSoup(r.content, 'html5lib')
        tables = bs.find_all('table', {'class': 'maintable'})

        if page_count:
            table = tables[1].find('td', {'class': 'navmenu'})
            if table is not None:
                self.total_pages = table.find_previous_sibling('td', {'class': 'tableh1'}).text.split()[3]
                self.total_pages = int(self.total_pages)
        if page_title:
            self.page_title = bs.title.text
            self.file_path = self.package_dir.joinpath(self.page_title)

        for a in tables[1].find_all('a', href=True):
            if str(a['href']).startswith("display"):
                self.image_urls.append(f"https://www.hqdiesel.net/gallery/{a['href']}&fullsize=1")

    def _download_images(self, pos):
        if not Path.exists(self.file_path):
            Path.mkdir(self.file_path)
        with self.session as s:
            try:
                r = s.get(self.image_urls[pos])
                bs = BeautifulSoup(r.content, 'html5lib')
                image_src = bs.find('div', {'id': 'content'}).find('img')['src']
                r = s.get(f"https://www.hqdiesel.net/gallery/{image_src}", stream=True)
                r.raw.decode_content = True
                with open(f"{self.file_path}\\{self.page_title}_{pos}.jpg", 'wb+') as f:
                    shutil.copyfileobj(r.raw, f)
                time.sleep(1.5)
            except Exception as ex:
                print(ex)


try:
    Scrape()
except KeyboardInterrupt as e:
    sys.exit(1)
