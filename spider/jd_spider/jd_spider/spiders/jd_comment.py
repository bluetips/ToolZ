# -*- coding: utf-8 -*-
import json
import re
import time
from copy import deepcopy

import scrapy
from redis import StrictRedis


class JdCommentSpider(scrapy.Spider):
    name = 'jd_comment'
    allowed_domains = ['jd.com']
    start_urls = ['http://jd.com/']
    sr = StrictRedis(host='139.196.91.125', port=6379, db=0)
    url = 'https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv53&productId={}&score=0&sortType=5&page={}&pageSize=10&isShadowSku=0&fold=1'
    # url = 'https://wq.jd.com/commodity/comment/getcommentlist?callback=skuJDEvalB&pagesize=10&sceneval=2&score=0&sku={}&sorttype=5&page={}'

    def parse(self, response):
        while 1:
            sku = self.sr.spop('skus_pipe').decode()
            # url = self.url.format(sku, '0')
            h = {
                'Referer': 'https://item.jd.com/{}.html'.format(sku),
            }
            for i in range(50):
                url = self.url.format(sku, str(i))
                yield scrapy.Request(url, callback=self.parse_detail, headers=h, meta={'sku': sku})

    def parse_detail(self, response):
        sku = response.meta['sku']
        try:
            json_data = json.loads(response.body.decode('gbk').replace('fetchJSON_comment98vv53(', '')[:-2])
            # json_data = json.loads(response.body.decode('gbk').replace('skuJDEvalB(', '')[:-1])
        except Exception:
            return
            pass
        if json_data['comments'] == []:
            return
        item_list = json_data['comments']
        for item in item_list:
            item['sku'] = sku
            yield item

# todo 更换接口
# https://wq.jd.com/commodity/comment/getcommentlist?callback=skuJDEvalB&pagesize=10&sceneval=2&score=0&sku=5832461&sorttype=5&page=2&t=0.7689202619748416
