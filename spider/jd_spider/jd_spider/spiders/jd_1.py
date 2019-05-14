# -*- coding: utf-8 -*-
import json
import re
from copy import deepcopy

import requests
import scrapy
from lxml import etree


class Jd1Spider(scrapy.Spider):
    name = 'jd_1'
    allowed_domains = ['jd.com']

    start_urls = ['https://www.jd.com']

    def parse(self, response):
        url = 'https://search.jd.com/Search?keyword=%E7%B2%BE%E5%8D%8E%E6%B6%B2&enc=utf-8&qrst=1&rt=1&stop=1&vt=2&wq=%E7%B2%BE%E5%8D%8E%E6%B6%B2&stock=1&page={}&s=56&click=0'
        for i in range(100):
            yield scrapy.Request(url.format(i * 2 + 1), callback=self.parse_jd)

    def parse_jd(self, response):
        # 获取商品url列表再次请求
        obj_list = etree.HTML(response.body.decode()).xpath('//ul[@class="gl-warp clearfix"]/li')
        for obj in obj_list:
            item = {}
            item['title'] = ''.join(obj.xpath('.//div[@class="p-name p-name-type-2"]//em//text()'))
            try:
                item['price'] = float(obj.xpath('.//div[@class="p-price"]/strong/i/text()')[0])
            except Exception:
                item['price'] = float(obj.xpath('.//div[@class="p-price"]/strong/@data-price')[0])
            item['url'] = 'https:' + obj.xpath('.//div[@class="p-img"]/a/@href')[0]
            item['sku'] = obj.xpath('./@data-sku')[0]
            item['shop'] = ''.join(obj.xpath('.//div[@class="p-shop"]//text()')).strip()
            item['tags'] = re.sub('\s','',''.join(obj.xpath('.//div[@class="p-icons"]//text()')))
            yield scrapy.Request(item['url'], callback=self.parse_detail, meta=deepcopy(item))
        # url = response.url
        # pn = int(re.findall('page=(\d+)', url)[0])
        # next_url = re.sub('page=(\d+)', 'page={}'.format(str(pn + 2)), url)
        # yield scrapy.Request(next_url, callback=self.parse)

    def parse_detail(self, response):
        item = response.meta
        comment_url = 'https://club.jd.com/comment/productCommentSummaries.action?referenceIds={}'
        try:
            comment_data = json.loads(requests.get(comment_url.format(item['sku'])).content.decode())['CommentsCount'][
                0]
        except Exception:
            comment_data = \
                json.loads(requests.get(comment_url.format(item['sku'])).content.decode('gbk'))['CommentsCount'][
                    0]
        item['comment_data'] = comment_data
        ele = etree.HTML(response.text)
        try:
            item['brand'] = ele.xpath('.//ul[@id="parameter-brand"]/li/@title')[0]
        except Exception:
            try:
                item['brand'] = ele.xpath('.//li[contains(text(),"品牌")]/a/text()')[0]
            except Exception:
                item['brand'] = '无品牌'
        yield item

    def parse_comment(self, response):
        # https://sclub.jd.com/comment/productPageComments.action?callback=fetchJSON_comment98vv656&productId=7293538&score=0&sortType=5&page=0&pageSize=10&isShadowSku=0&fold=1
        pass
