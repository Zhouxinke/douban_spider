from bs4 import BeautifulSoup
import CommenSetting
import requests
import time
import xlwt
import random

import multiprocessing
import os

# 初始化excel表格
def InitailizeWorkbook():
    """
    初始化表头
    :return: workbook 和 table表
    """
    workbook = xlwt.Workbook(encoding='utf-8')
    table = workbook.add_sheet('douban')
    table.write(0, 0, '书名')
    table.write(0, 1, '出版社')
    table.write(0, 2, '出版时间')
    table.write(0, 3, '价格')
    table.write(0, 4, '作者')
    table.write(0, 5, 'ISBN')
    return workbook, table

def FileTag():
    """
    从txt文件中读取所有的tag
    :return:
    """
    filename = 'AllTag.txt'
    f = open(filename, 'r')
    str_all_tag = f.read()
    # all_tag_list 表示的是包含所有标签的list
    all_tag_list = str_all_tag.strip().split(' ')
    f.close()
    print(all_tag_list)

    return all_tag_list

def GenerateAgent():
    """
    生成代理
    ps：url是我花20买的生成的，想用自己买，免费的没有效果
    :return:list类型 的代理 如['123.123.123.123:8888',...]
    """
    url = 'http://120.79.85.144/index.php/api/entry?method=proxyServer.tiqu_api_url&packid=0&fa=0&dt=0&groupid=0&fetch_key=&qty=200&time=101&port=1&format=txt&ss=1&css=&dt=0&pro=&city=&usertype=6'
    # 返回可用的agent
    req = requests.get(url, headers={'user-agent':random.choice(CommenSetting.user_agent)})
    html = req.text
    proxy_list = html.split('\n')
    return proxy_list


def CrawlAllInfo(tag):
    """
    爬取一个标签的信息，并保存到一个excel表格中
    :param tag: 传入参数 标签，爬取每个标签的信息
    :return:
    """
    print("标签：", tag)
    workbook, table = InitailizeWorkbook()

    # 记录书籍的数量，方便写入excel表格
    book_num = 0
    # 记录 爬取标签的当前页数，从第0页开始爬取，直到爬取到不一样的页面
    page_num = 0
    # 让页数page_num一直增长，直到超时 × 这个思路过时了
    while True:
        print("page_num", page_num, "   ", tag)
        # 睡一会
        # time.sleep(random.random()*4)

        url = 'https://book.douban.com/tag/' + tag + '?start=' + str(page_num*20) + '&type=T'
        # print(url)
        proxies = GenerateAgent()
        user_agent = random.choice(CommenSetting.user_agent)
        # print("proxies : ", proxies)
        # print("user_agent : ", user_agent)

        try:
            # 这里使用post会出现问题， url中的60、40、20 最后得到的都是0的效果
            req = requests.get(url=url, proxies={'http' : random.choice(proxies)}, headers={'user-agent':user_agent})
            bid = req.cookies['bid']
            if req.status_code == 403:
                print("爬取不到页面，请重试！")
            html = req.text
            soup = BeautifulSoup(html, 'lxml')
        except Exception as e:
            print(e)
        # 如果有两个这个东西说明标签找完了，退出去爬下一个标签
        over = soup.find_all(attrs={'class':'pl2'})
        if len(over) == 2:
            print("over")
            break

        re = soup.find_all(attrs={'class':'info'})
        # 循环爬取一个页面中每一本书的信息（最多20本书）
        # re是一个列表
        for i in range(len(re)):
            print("i:", i)
            book_name = re[i].h2.text.strip()
            # 判断书名是否是中文，不是的就跳过了
            if not IsChineseName(book_name):
                continue
            # 进入详细信息页面提取详细信息
            info_url = re[i].a['href']
            req = requests.get(url=info_url, proxies={'http': random.choice(proxies)}, headers={'user-agent': user_agent, "cookie": 'bid='+bid})
            html = req.text
            soup = BeautifulSoup(html, 'lxml')

            info = soup.find_all(id='info')
            # 如果info没有这个标签就退出
            if len(info[0].find_all('a')) == 0:
                continue
            author = info[0].find_all('a')[0].text
            info_list = info[0].text.strip().split('\n')
            dic = {}
            for i in info_list:
                if ':' in i:
                    k, v = i.split(':', 1)
                    dic[k] = v
            info_list = [0, 0, 0, 0, 0, 0]
            info_list[4] = author.replace("\n", "")
            info_list[1] = dic['出版社'] if dic.__contains__('出版社') else ''
            info_list[2] = dic['出版年'] if dic.__contains__('出版年') else ''
            info_list[3] = dic['定价'] if dic.__contains__('定价') else ''
            info_list[0] = book_name.replace("\n", "")
            info_list[5] = dic['ISBN'] if dic.__contains__('ISBN') else ''
            #author, press, publish_date, price = info_list[0], info_list[1], info_list[2], info_list[3]

            # 如果更新成功， 书籍的数量加一
            book_num += 1
            # 爬取信息之后 将信息保存在csv里面
            SolveInfoToCSV(table, info_list, book_num)

        page_num += 1

    workbook.save('result/'+tag+'.xlsx')
    time.sleep(10)

def IsChineseName(string):
    """
    判断书名是否是中文名
    :param string: 书名
    :return: 是/否
    """
    for ch in string:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def SolveInfoToCSV(table, info_list, book_num):
    """
    将信息写进excel表格
    :param table: 上面定义的 表
    :param info_list: 保存的信息列表
    :param book_num: 在excel中表示哪一行
    :return:
    """
    for i in range(6):
        table.write(book_num, i, str(info_list[i]).strip())

def timer(function):
    """
    装饰器函数timer，虽然没怎么用上
    :param function:想要计时的函数
    :return:
    """

    def wrapper(*args, **kwargs):
        time_start = time.time()
        res = function(*args, **kwargs)
        cost_time = time.time() - time_start
        print("【%s】运行时间：【%s】秒" % (function.__name__, cost_time))
        return res

    return wrapper

@timer
def main():
    # multiprocessing.cpu_count() = 12
    tag_list = FileTag()
    #多进程爬取
    pool = multiprocessing.Pool(multiprocessing.cpu_count()*2)
    for solo_tag in tag_list:
        # 因为ip被封了需要重新跑程序，那么需要判断这个tag有没有爬完
        if not os.path.exists('result/'+solo_tag+'.xlsx'):
            pool.apply_async(CrawlAllInfo, (solo_tag,))
    # pool.map(detailPage, urls)
    pool.close()
    pool.join()

    # 一个一个的爬取
    # tag_list = FileTag()
    # for solo_tag in tag_list:
    #     CrawlAllInfo(solo_tag)

if __name__ == '__main__':
    # print(GenerateAgent())
    main()