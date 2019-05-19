# coding:utf-8
import datetime
import re
import os
import sys

import emoji

sys.path.append(os.path.dirname('..'))
sys.path.append(os.path.realpath(os.path.dirname(__file__)) + '/../')
import time
import traceback
import hashlib
import requests
from lxml import etree
import redis
import json
from conf.conf import *
from urllib.parse import urlencode
import urllib.parse as urllib2
from tools.md5 import MD5
from tools.conn import Mysql
from tools.dict_main_tm import sentiment_score
from tools.check import IsInSpiderConf, update
from conf.conf import sen

dic = {}
mysql = Mysql(brandq_db_basic)
header = {
    'Host': 'mp.weixin.qq.com',
    'Origin': 'https://mp.weixin.qq.com',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
}
data = {
    'is_only_read': 1,
    'req_id': '2515lQuLQfC4QV5VH7j0aZYR',
    'pass_ticket': None,
    'is_temp_url': 0
}
s = requests.session()
channel = '证券时报网'


def md5(Str):
    MD5 = hashlib.md5()
    MD5.update(Str)
    return MD5.hexdigest()


def getpage(url, headers={}, refer=''):
    headers['referer'] = refer
    res = requests.get(url, headers=headers)
    return res


def crawl(keyword, startime, endtime, industry):
    # starttime = int(time.mktime(time.strptime(startime, '%Y-%m-%d')))
    # endtime = int(time.mktime(time.strptime(endtime, '%Y-%m-%d')))

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
        'Accept': '*/*',
    }
    pn = 1

    while 1:
        search_url = 'http://app.stcn.com/?app=search&controller=index&action=search&type=article&wd={}&advanced=1&catid=&before={}&after={}&order=time&page={}&order=time'.format(
            keyword, startime, endtime, pn)
        resp = getpage(search_url, headers)
        obj_list = etree.HTML(resp.content.decode()).xpath('//div[@id="search_list"]/dl')
        if len(obj_list) == 0:
            break
        print(len(obj_list))
        for o in obj_list:
            ctime = o.xpath('./dd/span/text()')[0]
            url = o.xpath('./dt/a/@href')[0]
            resp = getpage(url)
            item = {}
            ele = etree.HTML(resp.content.decode())
            content = ''.join(ele.xpath('//div[@class="txt_con"]//text()'))
            item['content'] = emoji.demojize(content).strip()
            item['url'] = url
            try:
                item['post_date'] = ele.xpath('//div[@class="info"]/text()')[0]
                item['user'] = ''.join(ele.xpath('//div[@class="info"]/span[1]/text()')).replace('来源',
                                                                                                 '').strip()

            except Exception:
                try:
                    item['post_date'] = ele.xpath('//div[@class="xiangxi"]//span/text()')[0][:16]
                    item['user'] = re.findall(r'来源：(\w+)', ele.xpath('//div[@class="xiangxi"]//span/text()')[0])[0]
                except Exception:
                    continue

            item['user'] = re.sub(r'[\s\r\n]', '', item['user'])
            item['title'] = ele.xpath('//h2//text()')[0]
            sentiment, score = sentiment_score(item['title'] + item['content'])
            check = MD5(channel + keyword + item['content'] + item['title'])
            sensitivity = 0
            for i in sen:
                if i in item['content']: sensitivity += 1
            insert = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            try:
                mysql.insertOne(insert, (
                    keyword, industry, '证券时报网', item['user'], datetime.datetime.now().date(), item['title'],
                    item['content'],
                    item['post_date'], sentiment, score, url, sensitivity, check))
                mysql.end()
                print(item['title'],item['user'],item['post_date'],item['content'][:10])
            except Exception as e:
                print(e)
                pass
        pn += 1


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    # channelname = '21财经'
    while 1:
        curday = datetime.datetime.now().date()
        channel_date = f'{channel}_{curday}'
        print(channel)
        datas = r.spop(channel_date)
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
                    r5.sadd(f'{curday}_running', f"{keyword}||{channel}")
                    crawl(keyword, starttime, endtime, industry)
                    r5.srem(f'{curday}_running', f"{keyword}||{channel}")
                    r5.sadd(f'{curday}_finsh', f"{keyword}||{channel}")
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
                r5.srem(f'{curday}_running', f"{keyword}||{channel}")
                r.sadd(channel_date, datas)

        else:
            time.sleep(2)


if __name__ == '__main__':
    run()
    # crawl('南京', '2019-04-16', '2019-04-26', 'aa')
