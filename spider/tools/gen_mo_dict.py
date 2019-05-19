import redis

from conf.conf import redisdb


class Tool(object):
    def __init__(self, path):
        self.f = open(path, 'r', encoding='gbk').read()
        pool = redis.ConnectionPool(host=redisdb['host'], port=redisdb['port'], db=0)
        # self.r = redis.Redis(host=redisdb['host'], port=redisdb['port'], db=0)
        self.r = redis.Redis(connection_pool=pool)

    def run(self):
        list = self.f.split('\n')
        # posdict = self.r.smembers('pos')
        # negdict = self.r.smembers('neg')
        # stopwords = self.r.smembers('stop')
        for i in list:
            self.r.sadd('stop', i)
        print('end')


if __name__ == '__main__':
    path = '/Users/keith/Downloads/stop.txt'
    t = Tool(path)
    t.run()
    pass
