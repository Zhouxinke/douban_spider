import urllib
import urllib.request, urllib.error, urllib.parse
from bs4 import BeautifulSoup
import CommenSetting
import requests


def CrawlAllTag():
    """
    爬取所有的Tag，并保存成txt
    :return: 无
    """

    url = 'https://book.douban.com/tag/?view=type&icn=index-sorttags-all'

    # 给指定的url发送request请求
    req = requests.post(url, headers=CommenSetting.header)
    html = req.text


    result_str = ''
    soup = BeautifulSoup(html)
    re = soup.find_all('td')
    for i in re:
        result_str += i.a.string + ' '
    print(result_str)
    filename = 'AllTag.txt'
    f = open(filename, 'r+')
    f.write(result_str)
    f.close()

if __name__=='__main__':
    CrawlAllTag()