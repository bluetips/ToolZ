# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
from pymongo import MongoClient
from redis import StrictRedis

client = MongoClient('139.196.91.125', 27017)
c1 = client['jd']['jd_goods']
c2 = client['jd']['jd_comments']
sr = StrictRedis(host='139.196.91.125', port=6379, db=0)


class JdSpiderPipeline(object):
    def process_item(self, item, spider):
        print(item)
        try:
            c2.insert(item)
            # sr.sadd('skus_pipe', item['sku'])
        except Exception:
            pass
        # print(item)
        return item
