# coding:utf-8
import datetime
import re
import os
import sys

from retrying import retry

# sys.path.append(os.path.realpath(os.path.dirname(__file__)) + './../')
# sys.path.append('./..')
sys.path.append(os.path.realpath(os.path.dirname(__file__)) + '/../')
sys.path.append(os.path.dirname('..'))

import time
import traceback
import hashlib
import requests
from lxml import etree
import redis
import json
from conf.conf import *
from urllib.parse import urlencode
import urllib.request as urllib2
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
channel = 'cnstock'


def md5(Str):
    MD5 = hashlib.md5()
    MD5.update(Str.encode(encoding='utf-8'))
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
    headers['Referer'] = refer
    res = requests.get(url, headers=headers)
    return res


def getdetail(url):
    res = getpage(url)
    if res.status_code == 404: return 0, 0
    page = res.content

    tree = etree.HTML(page)
    post_content = ''.join([_.strip() for _ in tree.xpath('//div[@class="content"]/p/text()')])
    source = ''.join([_.strip() for _ in tree.xpath('//span[@class="source"]//text()')]).replace('来源：', '').replace(
        '\n', '')
    return source, post_content


def crawl(keyword, startime, endtime, industry):
    if isinstance(startime, str):
        startime = datetime.datetime.strptime(startime, '%Y-%m-%d')
    if isinstance(endtime, str):
        endtime = datetime.datetime.strptime(endtime, '%Y-%m-%d')

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
    }
    pn = 0
    while 1:
        url = 'http://search.cnstock.com/search/result/%s?t=1&k=%s' % (pn, keyword)
        print(url)
        refer = 'http://search.cnstock.com'
        res = getpage(url, headers=headers, refer=refer)
        if res.status_code == 500:
            print('500服务器错误')
            break
        if '找不到和您的查询' in res.content.decode():
            print('找不到结果')
            break
        page = res.content.decode()
        tree = etree.HTML(page)
        for each in tree.xpath('//div[@class="result-left"]/div[@class="result-article"]'):

            url = each.xpath('./h3/a/@href')[0]
            title = ''.join(each.xpath('./h3/a//text()'))
            print(title)
            # source = each['source']
            creationDate = each.xpath('./p[@class="link"]/span/text()')[0].split(' ', 1)[-1]
            creationDate = datetime.datetime.strptime(creationDate, '%Y-%m-%d %H:%M')
            if creationDate < startime:
                return
            source, post_content = getdetail(url)
            if source == 0: continue
            print(source)
            if keyword not in title and keyword not in post_content:
                continue
            sentiment, score = sentiment_score(title + post_content)
            check = MD5(industry + keyword + title)
            sensitivity = 0
            for i in sen:
                if i in post_content: sensitivity += 1
            insert = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            try:
                mysql.insertOne(insert, (
                    keyword, industry, channel, source, datetime.datetime.now().date(), title, post_content,
                    creationDate.date(), sentiment, score, url, sensitivity, check))
                mysql.end()
            except Exception as e:
                print(e)

        pn += 1


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    # channelname = 'cnstock'
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
    # crawl('银行', '2018-07-27', '2018-08-27')

    # getdetail('http://news.cnstock.com/news,bwkx-201808-4263148.htm')
