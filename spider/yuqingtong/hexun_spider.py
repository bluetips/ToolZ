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
channel = '和讯网'


def md5(Str):
    MD5 = hashlib.md5()
    MD5.update(Str)
    return MD5.hexdigest()




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
    search_url = 'https://www.baidu.com/s?wd={}&oq={}&ct=2097152&ie=utf-8&si=(hexun.com)&gpc=stf={},{}|stftype=2'.format(
        keyword, keyword, startime, endtime)
    while 1:
        refer = 'https://xueqiu.com/k?q={}'.format(keyword.encode('utf-8'))
        search_resp = getpage(search_url, headers, refer)
        obj_list = etree.HTML(search_resp.content.decode()).xpath('//div[@class="result c-container "]')
        print(len(obj_list))
        for o in obj_list:
            item = {}
            url = o.xpath('./h3/a/@href')[0]
            hexun_headers = {
                'Cookie': 'UM_distinctid=16a10f7f2f071b-0cec410a82246c-366e7e04-fa000-16a10f7f2f1263; HexunTrack=SID=20190220202020146d9cf59de9cad4d799cfd7a9fe7440cbf&CITY=32&TOWN=320100; vjuids=-9bb13583.16a10f7fad3.0.99dde42fe1f0a; __jsluid=d3e488149954f7410b8d46ad6625547f; vjlast=1555062848.1555482689.13; gr_user_id=4b8487bb-013b-47f7-9939-338d71b6a344; _ga=GA1.2.434004608.1555482807; _gid=GA1.2.984144784.1555482807; cn_1261777628_dplus=%7B%22distinct_id%22%3A%20%2216a10f7f2f071b-0cec410a82246c-366e7e04-fa000-16a10f7f2f1263%22%2C%22userFirstDate%22%3A%20%2220190417%22%2C%22userID%22%3A%20%22%22%2C%22userName%22%3A%20%22%22%2C%22userType%22%3A%20%22nologinuser%22%2C%22%24_sessionid%22%3A%200%2C%22%24_sessionTime%22%3A%201555482817%2C%22%24dp%22%3A%200%2C%22%24_sessionPVTime%22%3A%201555482817%2C%22initial_view_time%22%3A%20%221555480193%22%2C%22initial_referrer%22%3A%20%22http%3A%2F%2Fso.hexun.com%2Flist.do%3Ftype%3DALL%26stype%3DARTICLE%26key%3D%25C4%25CF%25BE%25A9%26page%3D5%22%2C%22initial_referrer_domain%22%3A%20%22so.hexun.com%22%7D; ADHOC_MEMBERSHIP_CLIENT_ID1.0=481634ef-ec19-0cca-bfd6-68a788181571; appToken=pc%2Cother%2Cchrome%2ChxAppSignId73410887398208651555482989574%2CHXGG20190415; trc_cookie_storage=taboola%2520global%253Auser-id%3D6460e699-358f-42d8-9572-5568fb1d5832-tuct3a9e5c6; hxwapcookieid=mioyip1dx6lt1we1s; HEXUN_COM_MEDIA_PLAYSTATE=1; hxck_sq_common=LoginStateCookie=; CNZZDATA1263247791=1949547637-1555480084-http%253A%252F%252Fnews.search.hexun.com%252F%7C1555550284; CNZZDATA1262135292=135290045-1555482697-http%253A%252F%252Fnews.search.hexun.com%252F%7C1555552932; Hm_lvt_970837596767b9a62d45b21ef2515938=1555493498,1555493801,1555495090,1555554812; Hm_lpvt_970837596767b9a62d45b21ef2515938=1555554961; cn_1263247791_dplus=%7B%22distinct_id%22%3A%20%2216a10f7f2f071b-0cec410a82246c-366e7e04-fa000-16a10f7f2f1263%22%2C%22userFirstDate%22%3A%20%2220190412%22%2C%22userID%22%3A%20%22%22%2C%22userName%22%3A%20%22%22%2C%22userType%22%3A%20%22nologinuser%22%2C%22userLoginDate%22%3A%20%2220190418%22%2C%22%24_sessionid%22%3A%200%2C%22%24_sessionTime%22%3A%201555555010%2C%22%24dp%22%3A%200%2C%22%24_sessionPVTime%22%3A%201555555010%2C%22initial_view_time%22%3A%20%221555058868%22%2C%22initial_referrer%22%3A%20%22https%3A%2F%2Fwww.baidu.com%2Flink%3Furl%3DDAy0n6K1KYA8p4wotS_wASyt-zh1Os5quph091-WOQatI-xGewX4pcIEh2key13xcVi4LHEfFmZItWEkR2i39a%26wd%3D%26eqid%3Df472174f000d1be4000000045cb06030%22%2C%22initial_referrer_domain%22%3A%20%22www.baidu.com%22%2C%22%24recent_outside_referrer%22%3A%20%22%24direct%22%7D',
                'Host': 'news.hexun.com',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36'
            }
            resp = getpage(url)
            hexun_headers['Host'] = re.findall('http.*://(.*hexun.com)', resp.url)[0]
            resp = getpage(resp.url, headers=hexun_headers)
            try:
                ele = etree.HTML(resp.content.decode('gbk'))
            except Exception:
                ele = etree.HTML(resp.content.decode())

            if 'm.' in resp.url:
                # https://m.hexun.com/nj/2019-04-16/196845234.html?from=groupmessage&isappinstalled=0
                item['content'] = ''.join(ele.xpath('//div[@class="pbox"]//text()'))
                item['url'] = resp.url
                item['post_date'] = ele.xpath('//div[@class="dettime"]/span[1]//text()')[0].strip()[:10]
                item['user'] = ''.join(ele.xpath('//div[@class="dettime"]/span[2]/text()'))[3:].strip()
                item['title'] = ele.xpath('//h2[@class="deth2"]/text()')[0].strip()
            else:
                try:
                    content = ''.join(ele.xpath('//div[@class="art_contextBox"]//text()'))
                except Exception:
                    # blog
                    print(resp.url)
                    print(traceback.format_exc())
                    continue
                item['content'] = emoji.demojize(content)
                item['url'] = resp.url
                try:
                    item['post_date'] = ele.xpath('//div[@class="tip fl"]/span//text()')[0].strip()[:10]
                except Exception:
                    continue
                item['user'] = ''.join(ele.xpath('//div[@class="tip fl"]/a//text()')).strip()
                item['title'] = ele.xpath('//div[@class="layout mg articleName"]/h1/text()')[0].strip()
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
            print(search_url)
        except Exception:
            # 不存在了没有下一页
            break


def run():
    pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=1)
    pool5 = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=5)
    r = redis.Redis(connection_pool=pool)
    r5 = redis.Redis(connection_pool=pool5)
    channelname = '和讯网'
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
                    crawl(keyword, starttime, endtime, industry)
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
    # crawl('南京', '2019-04-16', '2019-04-17', 'aa')
    run()
