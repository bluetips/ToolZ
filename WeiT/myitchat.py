import datetime
import time

import itchat
import requests
from redis import StrictRedis
from pymongo import MongoClient
import json
import threading

KEY = 'xxxxxxx'

T = 0


def get_response(msg, UserId):
    # 这里我们就像在“3. 实现最简单的与图灵机器人的交互”中做的一样
    # 构造了要发送给服务器的数据
    apiUrl = 'http://openapi.tuling123.com/openapi/api/v2'

    data = {
        "reqType": 0,
        "perception": {
            "inputText": {
                "text": msg
            },
            "inputImage": {
                "url": ""
            },
            "selfInfo": {
                "location": {
                    "city": "",
                    "province": "",
                    "street": ""
                }
            }
        },
        "userInfo": {
            "apiKey": "42afd1a6112f4a93bbaa83022d980132",
            "userId": str(UserId)[1:33]
        }
    }

    print(data)
    try:
        r = requests.post(apiUrl, data=json.dumps(data)).json()
        # 字典的get方法在字典没有'text'值的时候会返回None而不会抛出异常

        r = r['results']
        r = r[0]
        r = r['values']
        return r['text']
    # 为了防止服务器没有正常响应导致程序异常退出，这里用try-except捕获了异常
    # 如果服务器没能正常交互（返回非json或无法连接），那么就会进入下面的return
    except:
        # 将会返回一个None
        return


id = ''


@itchat.msg_register(itchat.content.TEXT)
def print_content(msg):
    # print(msg)
    global id
    print('id = |' + id)
    print(msg['Text'] == '修改配置')
    print(id == msg['FromUserName'])
    # if msg['Text'] == '开启监控' and (id == '' or id == None):
    if msg['Text'] == '开启监控':
        # 引用全局变量
        id = msg['FromUserName']
        itchat.send_msg('已经开启监控~', toUserName=id)
        return

    if msg['Text'] == '添加监控' and id == msg['FromUserName']:
        s = {
            'industry': '舆情监控',
            'keyword': 'btc',
            'starttime': '2019-01-01',
            'end_time': '2019-05-05',
            'channael_date': '第一财经_2019-05-18'
        }
        itchat.send_msg('修改以下列信息，并且将修改后的信息复制发送', toUserName=id)

        itchat.send_msg(str(s), toUserName=id)
        return

    if '舆情监控' in msg['Text'] and id == msg['FromUserName']:
        # 添加到redis
        sr = StrictRedis(host='139.196.91.125', port=6379, db=1)
        json_data = json.loads(msg['Text'].replace("'", '"'))
        sr.sadd(json_data['channel_date'], msg['Text'])
        itchat.send_msg('添加成功', toUserName=id)
        return

    if msg['Text'] == '查看监控列表' and id == msg['FromUserName']:
        # sr_1 = StrictRedis(host='139.196.91.125', port=6379, db=1)
        sr_5 = StrictRedis(host='139.196.91.125', port=6379, db=5)
        curday = datetime.datetime.now().date()
        ret_1 = list(sr_5.smembers(f'{curday}_running'))
        ret_5 = list(sr_5.smembers(f'{curday}_finsh'))
        s = ''
        num = 1

        for i in ret_1:
            s = '正在爬取平台,编号{}：'.format(str(num)) + s + i.decode() + '\n'
            num += 1
        for i in ret_5:
            s = '爬取完成平台,编号{}：'.format(str(num)) + s + i.decode() + '\n'
            num += 1
        if num == 1:
            s = '没有监控哦'
        itchat.send_msg(s, toUserName=id)
        return

    if msg['Text'] == '获取监控结果' and id == msg['FromUserName']:
        s = '输入关键词，以@开头，我会尝试查询返回所有结果，例如 @btc'
        itchat.send_msg(s, toUserName=id)
        return

    if msg['Text'].startswith('取消报警') and id == msg['FromUserName']:
        cancel = msg['Text'].replace('取消报警', '')
        sr = StrictRedis(host='139.196.91.125', port=6379, db=1)
        sr.sadd('cancel_list', cancel)
        itchat.send_msg('取消成功', toUserName=id)
        return

    if msg['Text'].startswith('@') and id == msg['FromUserName']:
        c1 = client['news']['yuqing']
        pn = msg['Text'].replace('@', '').split(':')[1]
        ret = c1.find({'keyword': msg['Text'].replace('@', '').split(':')[0]}).limit(10 * int(pn))
        count = c1.count_documents({'keyword': msg['Text'].replace('@', '').split(':')[0]})
        s = '共抓取舆情{}条'.format(str(count)) + '返回第一页标题,共10条，详情进入后台查看'
        itchat.send_msg(s, toUserName=id)
        s = ''
        num = 1
        for i in ret:
            s = s + '第{}篇:'.format(str(10 * int(pn) + 1)) + i['title'] + '\n' + '    '
            num += 1
        itchat.send_msg(s, toUserName=id)
        return

    if msg['Text'].startswith('#') and id == msg['FromUserName']:
        c1 = client['news']['yuqing']
        pn = int(msg['Text'].replace('#', '').split(':')[1])
        ret = c1.find({'keyword': msg['Text'].replace('#', '').split(':')[0]}).skip(pn - 1).limit(1)
        for i in ret:
            itchat.send_msg(i['post_content'], toUserName=id)
        return

    return get_response(msg['Text'], msg['FromUserName'])


def check_yuqing():
    sr = StrictRedis(host='139.196.91.125', port=6379, db=1)
    while 1:
        cancel_list = sr.smembers('cancel_list')
        if id != '':
            c1 = client['news']['yuqing']
            pipe = [{'$match': {'sentiment': '负面'}}, {'$group': {'_id': '$keyword', 'counter': {'$sum': 1}}}]
            ret = c1.aggregate(pipe)
            for i in ret:
                if i['counter'] > 10:
                    if i['_id'].encode() in cancel_list:
                        continue
                    itchat.send_msg('关键词"{}"的负面舆情已经有{}条，请登录后台查看！'.format(i['_id'], str(i['counter'])), toUserName=id)
        time.sleep(60)


if __name__ == '__main__':
    itchat.auto_login(hotReload=True)
    client = MongoClient('139.196.91.125', 27017)
    # blockThread=False 启用解除block
    itchat.run(blockThread=False)
    # 舆情报警
    check_yuqing()
