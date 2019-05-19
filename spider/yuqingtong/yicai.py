# coding:utf-8
import datetime
import re
import os
import sys

from pymongo import MongoClient

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

from tools.dict_main_tm import sentiment_score

dic = {}
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
channel = '第一财经'
client = MongoClient('139.196.91.125', 27017)


def MD5(Str):
    MD5 = hashlib.md5()
    MD5.update(Str.encode())
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


def getdetail(url):
    page = getpage(url).content
    tree = etree.HTML(page)
    if 'https://www.yicai.com/news' in url:
        post_content = ''.join([_.strip() for _ in tree.xpath('//div[@class="m-txt"]/p//text()')])
    elif 'https://www.yicai.com/image' in url:
        post_content = ''.join([_.strip() for _ in tree.xpath('//ul[@class="ad-thumb-list"]/li/a/img/@data-ad-desc')])
    else:
        post_content = ''
    return post_content


def crawl(keyword, startime, endtime, industry):
    if isinstance(startime, str):
        startime = datetime.datetime.strptime(startime, '%Y-%m-%d')
    if isinstance(endtime, str):
        endtime = datetime.datetime.strptime(endtime, '%Y-%m-%d')

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
    }
    pn = 0
    while 1:
        url = 'https://www.yicai.com/api/ajax/getSearchResult?page=%s&pagesize=20&keys=%s&action=0' % (pn, keyword)
        print(url)
        refer = 'https://www.yicai.com/search?keys={}'.format(keyword.encode('utf-8'))
        res = getpage(url, headers, refer)
        if res.status_code == 500:
            break
        data = res.json()['results']
        start = data['start']
        numFound = data['numFound']
        for each in data['docs']:
            url = 'https://www.yicai.com' + each['url']
            if re.search('video|topic', url): continue
            item = {}
            item['title'] = each['title']
            item['source'] = each['source']
            creationDate = each['creationDate']
            item['creationDate'] = datetime.datetime.strptime(creationDate, '%Y-%m-%d %H:%M:%S')
            if item['creationDate'] < startime:
                return
            item['post_content'] = getdetail(url)
            item['sentiment'], item['score'] = sentiment_score(item['title'] + item['post_content'])
            item['check'] = MD5(channel + keyword + item['title'])
            item['keyword'] = keyword
            c1 = client['news']['yuqing']
            # 去重
            if c1.find_one({'check': item['check']}):
                continue
            c1.insert(item)
            print(item)

        if start + 20 >= numFound:
            break
        pn += 1


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    channelname = '第一财经'
    while 1:
        curday = datetime.datetime.now().date()
        channel_date = f'{channelname}_{curday}'
        datas = r.spop(channel_date)
        print('等待中')
        if datas:
            try:
                data = json.loads(datas.decode().replace("'", '"'))
                industry = '舆情监控'
                keyword = data['keyword']
                starttime = data['starttime']
                endtime = data.get('endtime', starttime)

                if starttime:
                    r5.sadd(f'{curday}_running', f"{keyword}||{channelname}")
                    crawl(keyword, starttime, endtime, industry)
                    r5.srem(f'{curday}_running', f"{keyword}||{channelname}")
                    r5.sadd(f'{curday}_finsh', f"{keyword}||{channelname}")
                kid = data.get('kid')
            except Exception as e:
                print(traceback.format_exc())
                r5.srem(f'{curday}_running', f"{keyword}||{channelname}")
                r.sadd(channel_date, datas)

        else:
            time.sleep(2)


if __name__ == '__main__':
    run()
