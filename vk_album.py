import re
import os
import sys
import time
import json
import random
import requests
import argparse
from shutil import move, rmtree
from selenium import webdriver
from collections import OrderedDict
from multiprocessing import Pool
from bs4 import BeautifulSoup as BS
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


def _get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("album_url", help="a vk album url", type=str)
    parser.add_argument("-o", help="output destination", dest="dest", type=str)
    args = parser.parse_args()

    album_url = args.album_url
    match = re.match("https?://(www\.)?(m\.)?vk\.com/(album-\d+_\d+)", album_url)
    album_url = "http://vk.com/{}".format(match[3])

    if args.dest:
        dest = args.dest
        dest = dest.replace("\\", "/")
        # For root dir
        if dest == os.path.dirname(dest):
            dest = "{}/{}".format(dest, match[3]).replace("//", "/")
        # Not root dir
        else:
            dest = re.sub("/$", "", dest)
    else:
        dest = match[3]
    print("\n------\nAlbum_url: {}".format(album_url))
    print("Destination: {}\n------\n".format(dest))
    return album_url, dest


def _requests_retry_session(retries=3, backoff_factor=0.3, status_forcelist=(500, 502, 504), session=None):
    session = requests.session()
    headers = {
        "user-agent": "mozilla/5.0 (x11; linux x86_64) applewebkit/537.36"
                      "(khtml, like gecko) "
                      "chrome/46.0.2490.86 safari/537.36"
    }
    session.headers.update(headers)
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class album_process:
    def __init__(self, album_url):
        # prepare the option for the chrome driver
        options = webdriver.ChromeOptions()
        options.add_argument('headless')

        self.driver = webdriver.Chrome(options=options)
        self.album_url = album_url

    # Bad repeat solution
    def console_status(self):
        try:
            load_more_status = self.driver.find_element_by_xpath("//div[@data-type='photos']").get_attribute("style")
        except Exception as e:
            print(e)
            print("\t{} occured. Retry later.".format(type(e).__name__))
            time.sleep(2)
            load_more_status = self.console_status()
        return load_more_status

    def console_click(self):
        try:
            element = self.driver.find_element_by_xpath("//div[@data-type='photos']")
            self.driver.execute_script("arguments[0].click();", element)
        except Exception as e:
            print(e)
            print("{} occured. Now quit.".format(type(e).__name__))
            self.driver.quit()
            sys.exit("==Please restart this script.==")

    def get_full_page(self):
        self.driver.get(self.album_url)
        print("Launch selenium...")

        full_res = self.driver.page_source
        while "photos_container_photos" not in full_res:
            time.sleep(0.5)
            full_res = self.driver.page_source

        # Trigger "ui_photos_load_more" till full page if it exists
        if "ui_photos_load_more" in full_res:
            load_more_status = self.console_status()
            while load_more_status != "display: none;":
                self.console_click()
                load_more_status = self.driver.find_element_by_id("ui_photos_load_more").get_attribute("style")
            full_res = self.driver.page_source

        # Quit selenium and del log
        self.driver.quit()
        if os.path.exists("ghostdriver.log"):
            os.remove("ghostdriver.log")
        return full_res

    def get_photo_id(self):
        # Find all elements including photo
        full_res = self.get_full_page()
        full_res = re.sub("(?<=\w) \"", "\"", full_res)
        soup = BS(full_res, features="html.parser")
        label_photo = soup.find_all(name="div", attrs={"aria-label": "Photo"})

        # Get photo ids
        photo_id_list = []
        for i in range(len(label_photo)):
            tag_id = label_photo[i].attrs["id"].replace("photo_row_", "")
            photo_id_list.append(tag_id)
        return photo_id_list


class vk_photo_download:
    def __init__(self, dest):
        self.rs = _requests_retry_session()
        self.dest = dest

    def get_photo_url(self):
        link = "http://vk.com/photo{}".format(self.photo_id)
        res = self.rs.get(link).text.replace("\\/", "/").replace("\\\"", "\"")

        # Set regex pattern for photo info
        pat_id = "".join(["({\"id\":\"", self.photo_id, ".+]},{\"id\":)"])
        pat_non_id = "".join([",{\"id\":\"(?!", self.photo_id, ")"])

        # Process photo info to json format
        part_id = re.search(pat_id, res)[0]
        part_id_select = re.split(pat_non_id, part_id)[0]
        part_js = re.sub("\"comments.+>\",", "", part_id_select)

        # Get the higher resolution url from json
        dic_js = json.loads(part_js)
        od = OrderedDict(sorted(dic_js.items()))
        js = [[key, value] for key, value in od.items()]
        img_url = js[-1][1]

        return img_url

    def save_photo(self, img_id):
        self.photo_id = img_id
        img_url = self.get_photo_url()

        # Set saving path anf filetype
        filetype = re.search(".+\.(\w+)", img_url)[1]
        img_path = "{}/photo{}.{}".format(self.dest, self.photo_id, filetype)

        # Save photo
        if not os.path.exists(img_path):
            with open(img_path, "wb") as handle:
                response = self.rs.get(img_url, stream=True)
                if not response.ok:
                    print(response)
                for block in response.iter_content(1024):
                    if not block:
                        break
                    handle.write(block)
            # saved += 1
            print("{} saved.".format(self.photo_id[1:]))
        else:
            # skip += 1
            print("== {} exists and skipped. ==".format(self.photo_id[1:]))
        time.sleep(random.uniform(0, 1.3))

    def reset_thumb(self):
        """
        On Windows OS, Some thumbnails will corrupt but full image intact.
        I'm not sure why it happened.
        This function helps solve that problem.
        """
        dest = os.path.dirname(self.dest).replace("//", "/")
        if dest:
            tmp_path = "{}/tmp/tmp".format(os.path.dirname(self.dest).replace("//", "/"))
            move(self.dest, tmp_path)
            move(tmp_path, self.dest)
            rmtree(os.path.dirname(tmp_path))


def main():
    args = _get_args()
    dest = args[1]

    album = album_process(args[0])
    vk_photo = vk_photo_download(dest)

    photo_ids = album.get_photo_id()
    total_photo = len(photo_ids)
    print("Find {} photos in album.".format(total_photo))

    if total_photo > 0:
        # Make destination folder if not exists
        if not os.path.exists(dest):
            os.makedirs(dest, mode=0o777)

        with Pool(int(os.cpu_count() / 2)) as pool:
            try:
                pool.map(vk_photo.save_photo, photo_ids)
            except Exception as e:
                print(e)

        try:
            vk_photo.reset_thumb()
            vk_photo.reset_thumb()
        except Exception as e:
            print(e)


if __name__ == '__main__':
    ts = time.time()
    main()
    te = time.time()
    print("{:2.2f} sec spent.".format(te - ts))
