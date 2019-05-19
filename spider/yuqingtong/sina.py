# coding:utf-8
import datetime
import re
import os
import sys
# sys.path.append(os.path.dirname('..'))
# print(sys.path)
# print(os.path.dirname('..'))
import urllib

import pymysql
import emoji

sys.path.append(os.path.realpath(os.path.dirname(__file__)) + '/../')
sys.path.append('./..')
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

print(sys.path)
from tools.dict_main_tm import sentiment_score
from tools.check import IsInSpiderConf, update
from conf.conf import sen

print(sys.path)

dic = {}
mysql = Mysql(brandq_db_basic)
header = {
    # 'Host': 'mp.weixin.qq.com',
    # 'Origin': 'https://mp.weixin.qq.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
}
data = {
    'is_only_read': 1,
    'req_id': '2515lQuLQfC4QV5VH7j0aZYR',
    'pass_ticket': None,
    'is_temp_url': 0
}
s = requests.session()
channel = '新浪财经'


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
    headers['referer'] = refer
    res = requests.get(url, headers=headers)
    return res


def getdetail(url):
    # print(url)
    page = getpage(url).content
    tree = etree.HTML(page)
    post_content = ''.join([_.strip() for _ in tree.xpath('//div[@id="artibody"]//p//text()')])
    return post_content


class Urlchuli():
    """Url处理类，需要传入两个实参：Urlchuli('实参','编码类型')，默认utf-8
    url编码方法：url_bm() url解码方法：url_jm()"""

    def __init__(self, can, mazhi='utf-8'):
        self.can = can
        self.mazhi = mazhi

    def url_bm(self):
        """url_bm() 将传入的中文实参转为Urlencode编码"""
        quma = str(self.can).encode(self.mazhi)
        bianma = urllib.parse.quote(quma)
        return bianma

    def url_jm(self):
        """url_jm() 将传入的url进行解码成中文"""
        quma = str(self.can)
        jiema = urllib.parse.unquote(quma, self.mazhi)
        return jiema


def crawl(keyword, startime, endtime, industry):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
    }
    s = Urlchuli(keyword, 'gbk')
    kw = s.url_bm()
    pn = 1
    while 1:
        # https://cre.dp.sina.cn/webes/simba/s2?q=%E6%AF%94%E7%89%B9%E5%B8%81&page=1&size=10&fields=title,labels,tags,stocks,stitle&qtp=match&sort=ctime%20desc&idx=simba_caitou&tp=1,2,3,8,9,10,12,13,14,15,16,17,19,20&where=(copyright==?%20or%20copyright%3C3)%20and%20published==1&check=2&_=1554189277013
        # url = 'http://search.sina.com.cn/?c=news&q=%s&range=title&time=custom&stime=%s&etime=%s&num=10&page=%s' % (
        #     kw, startime, endtime, pn)
        url = 'https://cre.dp.sina.cn/webes/simba/s2?q={}&page={}&size=10&fields=title,labels,tags,stocks,stitle&qtp=match&sort=ctime%20desc&idx=simba_caitou&tp=1,2,3,8,9,10,12,13,14,15,16,17,19,20&where=(copyright==?%20or%20copyright%3C3)%20and%20published==1&check=2'.format(
            keyword, pn)
        # print(url)
        res = getpage(url, headers=headers)
        dict = json.loads(res.content.decode())
        if dict['docs'] == []:
            return
        # tree = etree.HTML(page, etree.HTMLParser(encoding="gbk"))
        for each in dict['docs']:
            s_timeStamp = int(time.mktime(time.strptime(startime, "%Y-%m-%d")))
            d_timeStamp = int(time.mktime(time.strptime(endtime, "%Y-%m-%d")))
            if each['ctime'] > d_timeStamp:
                continue
            if each['ctime'] < s_timeStamp:
                return
            title = each['title']
            url = each['url']
            source = each.get('author','')
            try:
                post_date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(each['ctime']))
            except Exception:
                print('ctime Error')
                continue
            try:
                post_content = each['content']
                post_content = emoji.demojize(post_content)
            except Exception:
                continue
            if keyword not in title and keyword not in post_content:
                continue
            sentiment, score = sentiment_score(title + post_content)
            check = MD5(channel + keyword + title + post_content)
            sensitivity = 0
            for i in sen:
                if i in post_content: sensitivity += 1
            insert = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            print(title)
            try:
                mysql.insertOne(insert, (
                    keyword, industry, channel, source[:100], datetime.datetime.now().date(), title, post_content,
                    post_date,
                    sentiment, score, url, sensitivity, check))
                mysql.end()
            except Exception as e:
                with open('sinaerror.txt', 'a+') as f:
                    f.write('%s,%s\n' % (str(datetime.datetime.now()), traceback.format_exc()))
                print(e)
                pass
        pn += 1


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    # channelname = '新浪财经'
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
    # crawl('股票', '2018-08-01', '2019-04-01','金融垂直网站')
