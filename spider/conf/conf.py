import os

path = os.path.abspath(__file__)
path = os.path.dirname(path)
host = '139.196.91.125'
redisport = 6379
user = 'admin'
password = 'admin'

redisdb = {
    'host': host,
    'port': redisport,
}

# replyapi = 'http://test.ad-rating.com/brandquest/updateKeywordById.do'
# with open(path + '/sen', encoding='utf-8') as f:
#     sen = [_.strip() for _ in f]
