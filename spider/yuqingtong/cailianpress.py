# coding:utf-8
import datetime
import re
import os
import sys

# sys.path.append(os.path.realpath(os.path.dirname(__file__)) + './../')
# sys.path.append('./..')
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
channel = '财联社'


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
    # 去掉header
    res = requests.get(url)
    return res


def getdetail(url):
    print(url)
    page = getpage(url).content.decode()
    data = re.findall('__NEXT_DATA__ = (.*)\n', page)[0]
    data = json.loads(data)
    content = data['props']['initialState']['details']['content']['content']
    title = data['props']['initialState']['details']['content']['title']
    reading_num = data['props']['initialState']['details']['content']['reading_num']
    comment_num = data['props']['initialState']['details']['content']['comment_num']
    if len(content) > 0:
        tree = etree.HTML(content)
        content = ''.join(tree.xpath('//text()'))
        return content.replace('\n', ''), title, reading_num, comment_num
    else:
        return 0, 0, 0, 0, 0


def crawl(keyword, startime, endtime, industry):
    if isinstance(startime, str):
        startime = datetime.datetime.strptime(startime, '%Y-%m-%d')
    if isinstance(endtime, str):
        endtime = datetime.datetime.strptime(endtime, '%Y-%m-%d')
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
    }
    pn = 0
    Type = ['telegram', 'depth']
    Types = Type.pop()
    while 1:
        url = 'https://www.cailianpress.com/api/search/get_all_list?type=%s&keyword=%s&page=%s&rn=20' % (
            Types, keyword, pn)
        print(url)
        refer = 'https://www.cailianpress.com/searchPage?keyword={}&type=telegram'.format(keyword)
        res = getpage(url, headers=headers, refer=refer)
        if res.status_code == 500:
            break
        data = res.json()['data'].get(Types)
        numFound = data.get('total_num')
        for each in data['data']:
            if len(each.get('descr')) == 0: continue
            url = 'https://www.cailianpress.com/roll/' + str(each['id'])
            times = each['time']
            creationDate = datetime.datetime.fromtimestamp(times)
            if creationDate < startime: return
            source = '电报'
            print(creationDate, startime)
            if creationDate < startime:
                return
            post_content, title, reading_num, comment_num = getdetail(url)
            title = post_content[:20]
            if keyword not in title and keyword not in post_content:
                continue
            sentiment, score = sentiment_score(post_content)
            if Types == 'telegram':
                check = MD5(channel + keyword + post_content)
            elif Types == 'depth':
                check = MD5(channel + keyword + title)
            sensitivity = 0
            for i in sen:
                if i in post_content: sensitivity += 1
            insert = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            try:
                mysql.insertOne(insert, (
                    keyword, industry, '财联社', source, datetime.datetime.now().date(), title, post_content,
                    creationDate.date(), sentiment, score, url, sensitivity, check))
                mysql.end()
            except:
                pass
        if (pn + 1) * 20 >= numFound:
            if len(Type) == 0:
                return
            Types = Type.pop()

            pn = 0
        pn += 1


# def run():
#     global industry
#     pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
#     r = redis.Redis(connection_pool=pool)
#
#     pool_2 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
#     r_2 = redis.Redis(connection_pool=pool_2)
#     while 1:
#         datas = r.spop(channel)
#         print('等待中')
#         if datas:
#             try:
#                 try:
#                     data = json.loads(datas.decode())
#                 except:
#                     pass
#                 industry = data.get('industry', '')
#                 keyword = data['keyword']
#                 starttime = data['starttime']
#                 starttime = IsInSpiderConf(keyword, channel, starttime, industry)
#                 endtime = data.get('endtime', starttime)
#                 if starttime:
#                     r_2.sadd('crawling', datas)
#                     crawl(keyword, starttime, endtime)
#                     r_2.srem('crawling', datas)
#                 kid = data.get('kid')
#                 if kid:
#
#                     data = {"keyword": keyword,
#                             "kid": kid,
#                             "website": channel,
#                             "industry": industry,
#                             "starttime": data['starttime'],
#                             "endtime": data.get('endtime', starttime)}
#                     print(data)
#                     res = requests.post('http://datamining.comratings.com/api/split', data=data)
#                     print(res.status_code)
#                 else:
#                     mysql = Mysql(brandq_db_brand)
#                     query = 'update KEYWORD_CONFIGURATION set ENDTIME=%s where KEYWORD=%s and PLATFORM like  %s'
#                     mysql.update(query, (endtime, keyword, '%{}%'.format(channel)))
#                     mysql.end()
#                     print(keyword, 'ok')
#                     update(keyword, channel)
#             except Exception as e:
#                 print(traceback.format_exc())
#                 with open('calilianerror.txt', 'a+') as f:
#                     f.write('%s,%s,%s\n' % (str(datetime.datetime.now()), datas, traceback.format_exc()))
#                 r.sadd(channel, datas)
#                 r_2.srem('crawling', datas)
#
#         else:
#             time.sleep(2)


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    # channelname = '财联社'
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
    # crawl('银行', '2018-08-20', '2018-08-20')
