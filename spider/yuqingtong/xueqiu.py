import datetime
import json
import os
import random
import time
import traceback
from multiprocessing.dummy import Pool
from queue import Queue

import emoji
import redis
import requests
from lxml import etree
from retrying import retry

from conf.conf import redisdb, brandq_db_brand, sen, brandq_db_basic
from tools.check import IsInSpiderConf, update
from tools.conn import Mysql
from tools.dict_main_tm import sentiment_score
from tools.md5 import MD5

channel = '雪球网'

mysql = Mysql(brandq_db_basic)


def get_random_proxy():
    '''随机从文件中读取proxy'''
    while 1:
        file_path = os.path.join(os.path.dirname(__file__) + '/../tools/ip_pool/proxies.txt')
        with open(file_path, 'r') as f:
            proxies = f.readlines()
            if proxies:
                break
            else:
                time.sleep(1)
    proxy = random.choice(proxies).strip()
    return proxy


def get_random_cookie():
    '''随机从文件中读取cookie'''
    while 1:
        file_path = os.path.join(os.path.dirname(__file__) + '/../tools/cookie_pool/cookies.txt')
        with open(file_path, 'r') as f:
            proxies = f.readlines()
            if proxies:
                break
            else:
                time.sleep(1)
    cookie = random.choice(proxies).strip()
    return cookie


class Spider(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
            'Cookie': 'aliyungf_tc=AQAAAB1VLnsuwwUAf37dcmIvfegmNADD; _ga=GA1.2.1599621184.1555307494; _gid=GA1.2.1564713762.1555307494; device_id=202a148ed89a5d9d6feaec2346749fe4; s=eb15qbmq5z; Hm_lvt_1db88642e346389874251b5a1eded6e3=1555307495,1555318687; remember=1; remember.sig=K4F3faYzmVuqC0iXIERCQf55g2Y; xq_a_token=ec6fe9bed8f1cd2c04ff71fd20fec90c7c33e81c; xq_a_token.sig=5WTqbBl92eWKpw8DX5CjQzHyudc; xqat=ec6fe9bed8f1cd2c04ff71fd20fec90c7c33e81c; xqat.sig=dH6auv69onVxyTPTQLlHEYnPbEI; xq_r_token=5836c31f751d3628194758daa86ed2e445894a09; xq_r_token.sig=oUPd12OxUjR-KpWKNJNvSpwmIC4; xq_is_login=1; xq_is_login.sig=J3LxgPVPUzbBg3Kee_PquUfih7Q; u=4072231381; u.sig=PAGDqmU6cw4TfjC2qKa2XM-uu-8; _gat=1; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1555321386'
        }
        self.search_url = 'https://xueqiu.com/statuses/search.json?sort=time&source=user&q={}&count=20&page={}'
        self.queue = Queue()
        self.pool = Pool(5)
        self.is_running = True
        self.total_requests_num = 0
        self.total_response_num = 0
        pass

    @retry
    def get_page(self, search_url, starttime, endtime):

        cookie = get_random_cookie()

        self.headers['Cookie'] = cookie
        resp = requests.get(search_url, headers=self.headers)
        if resp.status_code == 400:
            raise Exception('状态码错误')
        try:
            if json.loads(resp.content.decode())['error_code'] == 21306:
                return None
        except Exception:
            pass
        obj_list = json.loads(resp.content.decode())['list']
        print(len(obj_list))
        for o in obj_list:
            ctime = int(o['created_at'] / 1000)
            if ctime > endtime:
                continue
            if ctime < starttime:
                return None
            url = 'https://xueqiu.com' + o['target']
            self.queue.put(url)
            self.total_requests_num += 1
        return 1

    def get_search_page(self, wd, starttime, endtime):

        starttime = int(time.mktime(time.strptime(starttime, '%Y-%m-%d')))
        endtime = int(time.mktime(time.strptime(endtime, '%Y-%m-%d')))
        page = 1

        self.headers['Referer'] = 'https://xueqiu.com/k?q={}'.format(wd.encode('utf-8'))

        while 1:
            search_url = self.search_url.format(wd, page)
            ret = self.get_page(search_url, starttime, endtime)
            if ret == None:
                break
            page += 1

    def _callback(self, temp):
        if self.is_running:
            self.pool.apply_async(self.save_detail, callback=self._callback)

    def run(self, keyword, starttime, endtime):
        self.get_search_page(keyword, starttime, endtime)

        for i in range(5):
            self.pool.apply_async(self.save_detail, callback=self._callback)

        while True:  # 防止主线程结束
            time.sleep(0.0001)  # 避免cpu空转，浪费资源
            if self.total_response_num >= self.total_requests_num:
                self.is_running = False
                break

        self.pool.close()  # 关闭线程池防止新线程开启

    def save_detail(self):
        item = {}
        url = self.queue.get()
        self.total_response_num += 1
        proxies = get_random_proxy()
        resp = requests.get(url, proxies=proxies, headers=self.headers)
        ele = etree.HTML(resp.content.decode())
        content = ''.join(ele.xpath('//div[@class="article__bd__detail"]//text()'))
        item['content'] = emoji.demojize(content)
        item['url'] = url
        item['post_date'] = ele.xpath('//a[@class="time"]/@data-created_at')[0]
        item['user'] = ele.xpath('//a[@class="name"]//text()')[0]
        item['title'] = ele.xpath('//h1[@class="article__bd__title"]//text()')[0]
        sentiment, score = sentiment_score(item['title'] + item['content'])
        check = MD5(channel + keyword + item['content'] + item['title'])
        sensitivity = 0
        for i in sen:
            if i in item['content']: sensitivity += 1
        insert = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        try:
            mysql.insertOne(insert, (
                keyword, industry, channel, item['user'][:100], datetime.datetime.now().date(), item['title'],
                item['content'],
                item['post_date'],
                sentiment, score, item['url'], sensitivity, check))
            mysql.end()
        except Exception as e:
            with open('xueqiuerror.txt', 'a+') as f:
                f.write('%s,%s\n' % (str(datetime.datetime.now()), traceback.format_exc()))
            print(e)
            pass


if __name__ == '__main__':
    # spider = Spider()
    # spider.get_search_page('北京', 1554080583, 1554966983)

    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    r = redis.Redis(connection_pool=pool)

    pool_2 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r_2 = redis.Redis(connection_pool=pool_2)

    while 1:
        datas = r.spop(channel)
        print(datas)
        print('等待中')
        if datas:
            try:
                data = json.loads(datas.decode())
                industry = data.get('industry', '')
                keyword = data['keyword']
                starttime = data['starttime']
                starttime = IsInSpiderConf(keyword, channel, starttime, industry)
                endtime = data.get('endtime', starttime)
                if starttime:
                    r_2.sadd('crawling', datas)
                    spider = Spider()
                    spider.run(keyword, starttime, endtime)
                    r_2.srem('crawling', datas)
                kid = data.get('kid')
                if kid:
                    data = {"keyword": keyword,
                            "kid": kid,
                            "website": channel,
                            "industry": industry,
                            "starttime": data['starttime'],
                            "endtime": data.get('endtime', starttime)}
                    print(data)
                    res = requests.post('http://datamining.comratings.com/api/split', data=data)
                    print(res.status_code)
                else:
                    mysql = Mysql(brandq_db_brand)
                    query = 'update KEYWORD_CONFIGURATION set ENDTIME=%s where KEYWORD=%s and PLATFORM like  %s'
                    mysql.update(query, (endtime, keyword, '%{}%'.format(channel)))
                    mysql.end()
                    print(keyword, 'ok')
                    update(keyword, channel)
            except Exception as e:
                print(traceback.format_exc())
                with open('xueqiuerror.txt', 'a+') as f:
                    f.write('%s,%s,%s\n' % (str(datetime.datetime.now()), datas, e))
                r.sadd(channel, datas)
                r_2.srem('crawling', datas)

        else:
            time.sleep(2)
