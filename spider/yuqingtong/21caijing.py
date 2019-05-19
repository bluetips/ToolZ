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

mysql = Mysql(brandq_db_basic)


class Spider(object):
    def __init__(self, keyword, industry, channel):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
            'Cookie': 'SRV=jj01; acw_tc=6525b79815553932027396357ebdc03a46b277fbf495e590f0385cc07d; PHPSESSID=fuvjn3avjk8jfarsr4f9qlcen7; Hm_lvt_ab984c6961d35319708c19c75e093eee=1555393203,1555393349; Hm_lpvt_ab984c6961d35319708c19c75e093eee=1555393404'}
        self.search_url = 'http://www.21jingji.com/dynamic/content/search/index/{}/{}'
        self.keyword = keyword
        self.industry = industry
        self.channel = channel
        pass


    def get_page(self, search_url, starttime, endtime):

        resp = requests.get(search_url, headers=self.headers)
        if resp.status_code == 400:
            raise Exception('状态码错误')
        try:
            if json.loads(resp.content.decode())['status'] == 0:
                return None
        except Exception:
            pass
        obj_list = json.loads(resp.content.decode())
        print(len(obj_list))
        for o in obj_list:
            ctime = int(o['inputtime'])
            if ctime > endtime:
                continue
            if ctime < starttime:
                return None
            url = o['url']
            self.save_detail(url)
        return 1

    def get_search_page(self, wd, starttime, endtime):

        starttime = int(time.mktime(time.strptime(starttime, '%Y-%m-%d')))
        endtime = int(time.mktime(time.strptime(endtime, '%Y-%m-%d')))
        page = 1

        self.headers['Referer'] = 'http://www.21jingji.com/channel/search/?s={}'.format(wd.encode('utf-8'))

        while 1:
            search_url = self.search_url.format(wd, page)
            ret = self.get_page(search_url, starttime, endtime)
            if ret == 1:
                page += 1
                continue
            else:
                break

    def save_detail(self, url):
        item = {}
        resp = requests.get(url, headers=self.headers)
        ele = etree.HTML(resp.content.decode())
        content = ''.join(ele.xpath('//div[@class="detailCont"]//text()'))
        item['content'] = emoji.demojize(content)
        item['url'] = url
        item['post_date'] = ele.xpath('//p[@class="Wh"]/span[1]/text()')[0].replace('年', '-').replace('月', '-').replace(
            '日', '-')
        try:
            item['user'] = ele.xpath('//span[@class="Wh1"]//text()')[0]
        except Exception as e:
            item['user'] = ''
        item['title'] = ele.xpath('//h2[@class="titl"]//text()')[0]
        sentiment, score = sentiment_score(item['title'] + item['content'])
        check = MD5(self.channel + self.keyword + item['content'] + item['title'])
        sensitivity = 0
        for i in sen:
            if i in item['content']: sensitivity += 1
        insert = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        try:
            mysql.insertOne(insert, (
                self.keyword, self.industry, self.channel, item['user'][:100], datetime.datetime.now().date(), item['title'],
                item['content'],
                item['post_date'],
                sentiment, score, item['url'], sensitivity, check))
            mysql.end()
            print(item['title'])
        except Exception as e:
            with open('21caijingerror.txt', 'a+') as f:
                f.write('%s,%s\n' % (str(datetime.datetime.now()), traceback.format_exc()))
            print(e)
            pass


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    channelname = '21财经'
    while 1:
        curday = datetime.datetime.now().date()
        channel = f'{channelname}_{curday}'
        print(channel)
        datas = r.spop(channel)
        print('等待中')
        if datas:
            try:
                try:
                    data = json.loads(datas.decode())
                except:
                    pass

                print(data)
                industry = data.get('industry', '金融垂直网站')
                keyword = data['keyword']
                starttime = data['starttime']
                starttime = IsInSpiderConf(keyword, channel, starttime, industry)
                endtime = data.get('endtime', starttime)

                if starttime:
                    r5.sadd(f'{curday}_running', f"{keyword}||{channelname}")
                    spider = Spider(keyword, industry, channel)
                    spider.get_search_page(keyword, starttime, endtime)
                    r5.srem(f'{curday}_running', f"{keyword}||{channelname}")
                    r5.sadd(f'{curday}_finsh', f"{keyword}||{channelname}")
                kid = data.get('kid')
                if kid:

                    data = {"keyword": keyword,
                            "kid": kid,
                            "website": channel,
                            "industry": industry,
                            "starttime": data['starttime'],
                            "endtime": data.get('endtime', starttime)}

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
                r5.srem(f'{curday}_running', f"{keyword}||{channelname}")
                r.sadd(channel, datas)

        else:
            time.sleep(2)


if __name__ == '__main__':
    # spider = Spider()
    # spider.get_search_page('北京', 1554080583, 1554966983)
    run()
