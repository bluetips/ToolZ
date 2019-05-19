import datetime
import json
import time
import traceback
import emoji
import redis
import requests
from lxml import etree

from conf.conf import redisdb, brandq_db_brand, sen, brandq_db_basic
from tools.check import IsInSpiderConf, update
from tools.conn import Mysql
from tools.dict_main_tm import sentiment_score
from tools.md5 import MD5
from twisted.enterprise import adbapi
import pymysql

pymysql.install_as_MySQLdb()

channel = '腾讯财经'

mysql = Mysql(brandq_db_basic)


class Spider(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'
        }
        self.search_url = 'https://www.baidu.com/s?ie=utf-8&f=8&rsv_bp=1&tn=baidu&wd={}&si=(finance.qq.com)&ct=2097152&rqlang=cn&rsv_enter=1&gpc=stf={},{}|stftype=1&tfflag=1'
        self.dbpool = adbapi.ConnectionPool('MySQLdb', host=brandq_db_basic['host'], db=brandq_db_basic['db'],
                                            user=brandq_db_basic['user'],
                                            passwd=brandq_db_basic['password'], charset='utf8',
                                            port=brandq_db_basic['port'])
        pass

    def close_spider(self):
        self.dbpool.close()

    def process_item(self, item):
        print(item['post_date'])
        self.dbpool.runInteraction(self.insert_db, item)

    def insert_db(self, tx, item):
        values = (
            keyword, industry, channel, item['user'][:100], datetime.datetime.now().date(), item['title'],
            item['content'],
            item['post_date'],
            item['sentiment'], item['score'], item['url'], item['sensitivity'], item['check'])
        sql = 'insert into brandq_post(keyword,channel,website,`user`,`timestamp`,post_title,post_content,post_date,sentiment,score,posturl,sensitivity,`check`)values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
        tx.execute(sql, values)

    def get_search_page(self, wd, starttime, endtime):

        starttime = int(time.mktime(time.strptime(starttime, '%Y-%m-%d')))
        endtime = int(time.mktime(time.strptime(endtime, '%Y-%m-%d')))
        search_url = self.search_url.format(wd, starttime, endtime)

        while 1:
            resp = requests.get(search_url, headers=self.headers)
            obj_list = etree.HTML(resp.content.decode()).xpath('//div[@class="result c-container "]')
            print(len(obj_list))
            for o in obj_list:
                try:
                    source_url = o.xpath('./div[@class="f13"]/a[1]/text()')[0]
                    print(source_url)
                except Exception:
                    source_url = o.xpath('//div[@class="f13"]/a[1]/text()')[0]
                    print(source_url)
                if 'finance.qq.com/a/' not in str(source_url):
                    continue
                url = o.xpath('./h3/a/@href')[0]
                self.save_detail(url)
            try:
                search_url = 'https://www.baidu.com' + \
                             etree.HTML(resp.content.decode()).xpath('//a[contains(text(),"下一页")]/@href')[0]
            except Exception:
                # 不存在了没有下一页
                self.close_spider()
                break

    def save_detail(self, url):
        item = {}
        resp = requests.get(url, headers=self.headers)
        ele = etree.HTML(resp.content.decode('gbk'))
        content = ''.join(ele.xpath('//div[@class="Cnt-Main-Article-QQ"]//text()'))
        item['content'] = emoji.demojize(content)
        item['url'] = resp.url
        try:
            item['post_date'] = ele.xpath('//span[@class="a_time"]/text()')[0]
        except Exception:
            return
        item['user'] = ele.xpath('//span[@class="a_source"]//text()')[0]
        item['title'] = ele.xpath('//div[@class="hd"]/h1/text()')[0]
        sentiment, score = sentiment_score(item['title'] + item['content'])
        check = MD5(channel + keyword + item['content'] + item['title'])
        sensitivity = 0
        for i in sen:
            if i in item['content']: sensitivity += 1

        item['sentiment'] = sentiment
        item['score'] = score
        item['check'] = check
        item['sensitivity'] = sensitivity
        try:
            self.process_item(item)
        except Exception as e:
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
                    spider.get_search_page(keyword, starttime, endtime)
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
                with open('tencenterror.txt', 'a+') as f:
                    f.write('%s,%s,%s\n' % (str(datetime.datetime.now()), datas, e))
                r.sadd(channel, datas)
                r_2.srem('crawling', datas)

        else:
            time.sleep(2)
