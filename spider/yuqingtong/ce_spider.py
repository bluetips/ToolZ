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
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1',
}
data = {
    'is_only_read': 1,
    'req_id': '2515lQuLQfC4QV5VH7j0aZYR',
    'pass_ticket': None,
    'is_temp_url': 0
}
s = requests.session()
channel = '中国经济网'


def md5(Str):
    MD5 = hashlib.md5()
    MD5.update(Str)
    return MD5.hexdigest()


emoji_pattern = re.compile(
    u"(\ud83d[\ude00-\ude4f])|"  # emoticons
    u"(\ud83c[\u0000-\uffff])|"  # symbols & pictographs (1.txt of 2)
    u"(\ud83d[\u0000-\uddff])|"  # symbols & pictographs (2 of 2)
    u"(\ud83d[\ude80-\udeff])|"  # transport & map symbols
    u"(\ud83c[\udde0-\uddff])|"
    u"\\xF0\\x9F[\\x00\\x00\\x00\\x00-\\xff\\xff\\xff\\xff]"  # flags (iOS)
    "+", flags=re.UNICODE)


def remove_emoji(text):
    return emoji_pattern.sub(r'', text)


def getpage(url, headers={}, refer=''):
    headers['referer'] = refer
    res = requests.get(url, headers=headers)
    return res


def crawl(keyword, startime, endtime, industry):
    startime = int(time.mktime(time.strptime(startime, '%Y-%m-%d')))
    endtime = int(time.mktime(time.strptime(endtime, '%Y-%m-%d')))

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
    }
    search_url = 'https://www.baidu.com/s?wd={}&oq={}&ct=2097152&ie=utf-8&si=ce.cn&rsv_idx=2&gpc=stf={},{}|stftype=1'.format(
        keyword, keyword, startime, endtime)
    while 1:
        refer = 'https://xueqiu.com/k?q={}'.format(keyword.encode('utf-8'))
        search_resp = getpage(search_url, headers, refer)
        obj_list = etree.HTML(search_resp.content.decode()).xpath('//div[@class="result c-container "]')
        for o in obj_list:
            item = {}
            try:
                source_url = o.xpath('./div[@class="f13"]/a[1]/text()')[0]
                # print(source_url)
            except Exception:
                source_url = o.xpath('//div[@class="f13"]/a[1]/text()')[0]
                # print(source_url)
            url = o.xpath('./h3/a/@href')[0]
            resp = getpage(url)
            try:
                ele = etree.HTML(resp.content.decode('gbk'))
            except Exception:
                ele = etree.HTML(resp.content.decode())
            content = ''.join(ele.xpath('//div[@class="TRS_Editor"]//text()'))
            item['content'] = emoji.demojize(content)
            item['url'] = resp.url
            try:
                item['post_date'] = ele.xpath('//span[@id="articleTime"]/text()')[0].strip()[:11].replace('年',
                                                                                                          '-').replace(
                    '月',
                    '-').replace(
                    '日', '')
            except Exception:
                print(resp.url)
                # print(traceback.format_exc())
                continue
            item['user'] = ele.xpath('//span[@id="articleSource"]//text()')[0][3:]
            item['title'] = ele.xpath('//h1[@id="articleTitle"]/text()')[0].strip()
            sentiment, score = sentiment_score(item['title'] + item['content'])
            check = MD5(channel + keyword + item['content'] + item['title'])
            sensitivity = 0
            for i in sen:
                if i in item['content']: sensitivity += 1

            item['sentiment'] = sentiment
            item['score'] = score
            item['check'] = check
            item['sensitivity'] = sensitivity
            insert = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            try:
                mysql.insertOne(insert, (
                    keyword, industry, '中国经济网', item['user'], datetime.datetime.now().date(), item['title'],
                    item['content'],
                    item['post_date'], sentiment, score, url, sensitivity, check))
                mysql.end()
                print(item['title'], item['post_date'])
            except Exception as e:
                print(traceback.format_exc())
                print(e)
                pass
        try:
            search_url = 'https://www.baidu.com' + \
                         etree.HTML(search_resp.content.decode()).xpath('//a[contains(text(),"下一页")]/@href')[0]
        except Exception:
            # 不存在了没有下一页
            break


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    # channelname = '中国经济网'
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
    # crawl('南京', '2019-04-16', '2019-04-17', 'aa')
    run()
