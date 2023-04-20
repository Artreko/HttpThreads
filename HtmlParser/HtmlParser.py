import requests
import cv2
import numpy as np
import sys
import urllib.parse
from bs4 import BeautifulSoup
from pprint import pprint
import json


def get_ip(url):
    parse_res = urllib.parse.urlparse(url)
    return parse_res.netloc


def parse_ips_from_page(url, page):
    header = {'User-agent': 'Mozilla/5.0'}
    response = requests.get(url, params={'page': page}, headers=header)
    if response.status_code != 200:
        return None
    soup = BeautifulSoup(response.text, features="html.parser")
    images = soup.find_all('img', class_='img-responsive')
    ips = {}
    for img in images:
        ip = get_ip(img.get('src'))
        ips[ip] = img.get('title')
    return ips


def parse_pages(url):
    header = {'User-agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=header)
        if response.status_code != 200:
            return None
        soup = BeautifulSoup(response.text, features="html.parser")
        num_pages = soup.find('ul', class_='pagination').find('script').text.strip()
        idx1 = num_pages.find(',') + 2
        idx2 = num_pages.find(',', idx1)
        return int(num_pages[idx1:idx2])
    except requests.exceptions.ConnectionError:
        print('Нет подключения')
        return None

def get_img(ip):
    response = requests.get(f'http://{ip}/axis-cgi/jpg/image.cgi', params={'resolution': '640x480'})
    if response.status_code != 200:
        return None
    img = cv2.imdecode(np.frombuffer(response.content, np.uint8), 1)
    return img


def main():
    url = 'http://insecam.org/ru/bytype/Axis/'
    pages = parse_pages(url)
    ip_dict = {}
    # if pages > 10:
    #     pages = 10
    for page in range(1, pages + 1):
        ip_dict.update(parse_ips_from_page(url, page))
    print('dict\n', ip_dict)
    js = json.dumps(ip_dict, ensure_ascii=False)
    print('json\n', js)
    with open('images.json', 'w', encoding='utf-8') as jf:
        jf.write(js)
    # images_path = os.path.join(os.getcwd(), 'images')
    # ips = list(ip_dict.keys())[:10]
    # images = list(map(get_img, ips))
    # for img, ip in zip(images, ips):
    #     if img is not None:
    #         img_name = f'img({ip.replace(":","_")}).jpg'
    #         img_path = os.path.join(images_path, img_name)
    #         cv2.imwrite(img_path, img)


if __name__ == '__main__':
    main()
