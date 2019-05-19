# -*- coding: utf-8 -*-
__author__ = 'Daisy Wang'

import numpy as np
import pandas as pd
import redis
import os
import text_process as tp
#sentiment.save('D:/pyscript/sentiment.marshal')

redisdb = {
    'host':'10.0.1.13',
    'port':6379,
    'pwd':'shaoqiang'
}

path = os.path.dirname(__file__)
# 1.txt.读取情感词典和待处理文件
# 情感词典
print "reading..."
#posdict = tp.read_lines(path+'emotion_dict/pos_all_dict.txt')
#negdict = tp.read_lines(path+'emotion_dict/neg_all_dict.txt')
# 程度副词词典
mostdict = tp.read_lines(path + '/degree_dict_new/most.txt')  # 权值为1.75
verydict = tp.read_lines(path + '/degree_dict_new/very.txt')  # 权值为1.5
moredict = tp.read_lines(path + '/degree_dict_new/more.txt')  # 权值为1.25
ishdict = tp.read_lines(path + '/degree_dict_new/ish.txt')  # 权值为0.75
overdict = tp.read_lines(path + '/degree_dict_new/over.txt')  # 权值为2
insufficientdict = tp.read_lines(path + '/degree_dict_new/insufficiently.txt')  # 权值为0.5
inversedict = tp.read_lines(path + '/degree_dict_new/inverse.txt')  # 权值为-1.txt

# 情感级别
emotion_level1 = "悲伤。"
emotion_level2 = "愤怒。"
emotion_level3 = "淡定。"
emotion_level4 = "平和。"
emotion_level5 = "喜悦。"
# 情感波动级别
emotion_level6 = "情感波动很小"
emotion_level7 = "情感波动较大"


# 2.程度副词处理，根据程度副词的种类不同乘以不同的权值
def match(word, sentiment_value):
    if word in mostdict:
        sentiment_value *= 1.75
    elif word in verydict:
        sentiment_value *= 1.5
    elif word in moredict:
        sentiment_value *= 1.25
    elif word in ishdict:
        sentiment_value *= 0.75
    elif word in insufficientdict:
        sentiment_value *= 0.5
    # elif word in overdict:
    #     sentiment_value *= 2
    elif word in inversedict:
        # print "inversedict", word
        sentiment_value *= -1
    return sentiment_value


# 3.情感得分的最后处理，防止出现负数
# Example: [5, -2] →  [7, 0]; [-4, 8] →  [0, 12]
def transform_to_positive_num(poscount, negcount):
    pos_count = 0
    neg_count = 0
    if poscount < 0 and negcount >= 0:
        neg_count += negcount - poscount
        pos_count = 0
    elif negcount < 0 and poscount >= 0:
        pos_count = poscount - negcount
        neg_count = 0
    elif poscount < 0 and negcount < 0:
        neg_count = -poscount
        pos_count = -negcount
    else:
        pos_count = poscount
        neg_count = negcount
    return (pos_count, neg_count)


# 求单条微博语句的情感倾向总得分
def single_review_sentiment_score(weibo_sent):
    r = redis.Redis(host=redisdb['host'], port=redisdb['port'], password=redisdb['pwd'], db=0)
    posdict = r.smembers('pos')
    negdict = r.smembers('neg')
    # posdict=tp.read_lines(path + '/emotion_dict_new/pos_all_dict.txt')
    # negdict = tp.read_lines(path + '/emotion_dict_new/neg_all_dict.txt')
    stopwords = r.smembers('stop')
    single_review_senti_score = []

    cuted_review = tp.cut_sentence(weibo_sent)  # 句子切分，单独对每个句子进行分析
    for sent in cuted_review:
        seg_sent = tp.segmentation(sent)  # 分词
        seg_sent = tp.del_stopwords(seg_sent,stopwords)[:]

        i = 0  # 记录扫描到的词的位置
        s = 0  # 记录情感词的位置

        poscount = 0  # 记录该分句中的积极情感得分
        negcount = 0  # 记录该分句中的消极情感得分
        for word in seg_sent:  # 逐词分析
            word = word.encode('utf-8','ignore')
            if word in posdict:  # 如果是积极情感词
                #print "posword:", word
                poscount += 50  # 积极得分+1.txt
                for w in seg_sent[s:i]:
                    poscount = match(w, poscount)
                s = i + 1  # 记录情感词的位置变化

            elif word in negdict:  # 如果是消极情感词
                #print "negword:", word
                negcount += 50
                for w in seg_sent[s:i]:
                    negcount = match(w, negcount)
                # print "negcount:", negcount
                s = i + 1

            # 如果是感叹号，表示已经到本句句尾
            elif word == "！".decode("utf-8") or word == "!".decode('utf-8'):
                for w2 in seg_sent[::-1]:  # 倒序扫描感叹号前的情感词，发现后权值+2，然后退出循环
                    if w2 in posdict:
                        poscount += 4
                        break
                    elif w2 in negdict:
                        negcount += 4
                        break
            i += 1
        single_review_senti_score.append(transform_to_positive_num(poscount, negcount))  # 对得分做最后处理
    pos_result, neg_result = 0, 0  # 分别记录积极情感总得分和消极情感总得分
    for res1, res2 in single_review_senti_score:  # 每个分句循环累加
        pos_result += res1
        neg_result += res2
    #print pos_result, neg_result
    result = pos_result - neg_result  # 该条微博情感的最终得分
    result = round(result, 0)

    if pos_result==0 and neg_result==0:
        return 0.5
    elif pos_result==0:
        return 0
    else:
        return float(pos_result)/(pos_result+neg_result)


"""
# 测试
weibo_sent = "这手机的画面挺好，操作也比较流畅。不过拍照真的太烂了！系统也不好。"
score = single_review_sentiment_score(weibo_sent)
print score
"""


# 分析test_data.txt 中的所有微博，返回一个列表，列表中元素为（分值，微博）元组
def run_score_file():
    fp_test = open('test.txt', 'r')  # 待处理数据
    contents = []
    for content in fp_test.readlines():
        content = content.strip()
        content = content.decode("utf-8")
        contents.append(content)
    fp_test.close()
    results = []
    for content in contents:
        score = single_review_sentiment_score(content)  # 对每条微博调用函数求得打分
        results.append((score, content))  # 形成（分数，微博）元组
    return results


def sentiment_score(content):
    score = single_review_sentiment_score(content)  # 对每条微博调用函数求得打分
    if score >= 0.58:
        score = int((score-0.58)/0.42*100)
    elif score < 0.5:
        score = -int((0.5-score)/0.5*100)
    elif score>=0.5 and score<=0.52:
        score=0
    else:
        score=-int((score-0.5)/0.5*100)

    if score == 0:
        sentiment = '中立'
    if score < 0:
        sentiment = '负面'
    if score > 0:
        sentiment = '正面'
    return [sentiment, score]


# 将（分值，句子）元组按行写入结果文件test_result.txt中
def write_results(results):
    fp_result = open('test_result.txt', 'w')
    '''
    for result in results:
        fp_result.write(str(result[0]))
        fp_result.write(' ')
        fp_result.write(result[1])
        fp_result.write('\n')
    '''
    for result in results.keys():
        fp_result.writelines("%s:%s\n"%(result,results[result]))
    fp_result.close()


# 求取测试文件中的正负极性的微博比，正负极性分值的平均值比，正负分数分别的方差
def handel_result(results):
    # 正极性微博数量，负极性微博数量，中性微博数量，正负极性比值
    pos_number, neg_number, mid_number, number_ratio = 0, 0, 0, 0
    # 正极性平均得分，负极性平均得分， 比值
    pos_mean, neg_mean, mean_ratio = 0, 0, 0
    # 正极性得分方差，负极性得分方差
    pos_variance, neg_variance, var_ratio = 0, 0, 0
    pos_list, neg_list, middle_list, total_list = [], [], [], []
    for result in results:
        total_list.append(result[0])
        if result[0] > 0:
            pos_list.append(result[0])  # 正极性分值列表
        elif result[0] < 0:
            neg_list.append(result[0])  # 负极性分值列表
        else:
            middle_list.append(result[0])
    #################################各种极性微博数量统计
    pos_number = len(pos_list)
    neg_number = len(neg_list)
    mid_number = len(middle_list)
    total_number = pos_number + neg_number + mid_number
    if neg_number==0:
        number_ratio=1
    else:
        number_ratio = pos_number / neg_number
    pos_number_ratio = round(float(pos_number) / float(total_number), 2)
    neg_number_ratio = round(float(neg_number) / float(total_number), 2)
    mid_number_ratio = round(float(mid_number) / float(total_number), 2)
    text_pos_number = "积极微博条数为 " + str(pos_number) + " 条，占全部微博比例的 %" + str(pos_number_ratio * 100)
    text_neg_number = "消极微博条数为 " + str(neg_number) + " 条，占全部微博比例的 %" + str(neg_number_ratio * 100)
    text_mid_number = "中性情感微博条数为 " + str(mid_number) + " 条，占全部微博比例的 %" + str(mid_number_ratio * 100)
    ##################################正负极性平均得分统计
    pos_array = np.array(pos_list)
    neg_array = np.array(neg_list)  # 使用numpy导入，便于计算
    total_array = np.array(total_list)
    pos_mean = pos_array.mean()
    neg_mean = neg_array.mean()
    total_mean = total_array.mean()  # 求单个列表的平均值
    mean_ratio = pos_mean / neg_mean
    if pos_mean <= 6:  # 赋予不同的情感等级
        text_pos_mean = emotion_level4
    else:
        text_pos_mean = emotion_level5
    if neg_mean >= -6:
        text_neg_mean = emotion_level2
    else:
        text_neg_mean = emotion_level1
    if total_mean <= 6 and total_mean >= -6:
        text_total_mean = emotion_level3
    elif total_mean > 6:
        text_total_mean = emotion_level4
    else:
        text_total_mean = emotion_level2
    ##################################正负进行方差计算
    pos_variance = pos_array.var(axis=0)
    neg_variance = neg_array.var(axis=0)
    total_variance = total_array.var(axis=0)
    var_ratio = pos_variance / neg_variance
    # print "pos_variance:", pos_variance, "neg_variance:", neg_variance, "var_ration:", var_ratio
    if total_variance > 10:  # 赋予不同的情感波动级别
        text_total_var = emotion_level7
    else:
        text_total_var = emotion_level6
    ################################构成字典返回
    result_dict = {}
    result_dict['pos_number'] = pos_number  # 正向微博数
    result_dict['neg_number'] = neg_number  # 负向微博数
    result_dict['mid_number'] = mid_number  # 中性微博数
    result_dict['number_ratio'] = round(number_ratio, 1)  # 正负微博数之比，保留一位小数四舍五入
    result_dict['pos_mean'] = round(pos_mean, 1)  # 积极情感平均分
    result_dict['neg_mean'] = round(neg_mean, 1)  # 消极情感平均分
    result_dict['total_mean'] = round(total_mean, 1)  # 总的情感平均得分
    result_dict['mean_ratio'] = abs(round(mean_ratio, 1))  # 积极情感平均分/消极情感平均分
    result_dict['pos_variance'] = round(pos_variance, 1)  # 积极得分方差
    result_dict['neg_variance'] = round(neg_variance, 1)  # 消极得分方差
    result_dict['total_variance'] = round(total_variance, 1)  # 总的情感得分方差
    result_dict['var_ratio'] = round(var_ratio, 1)  # 积极得分方差/消极得分方差

    result_dict['text_pos_number'] = text_pos_number  # 各种情感评价
    result_dict['text_neg_number'] = text_neg_number
    result_dict['text_mid_number'] = text_mid_number
    result_dict['text_pos_mean'] = text_pos_mean
    result_dict['text_neg_mean'] = text_neg_mean
    result_dict['text_total_mean'] = text_total_mean
    result_dict['text_total_var'] = text_total_var
    """
    for key in result_dict.keys():
        print 'key = %s , value = %s ' % (key, result_dict[key])
    """

    return result_dict


#print sentiment_score('一本书，一本题，好评，相信中公金融人，剩下的就靠自己努力了。祝生意兴隆。【淘宝几年才知道原来评论85个字才会有积分。所以从今天到以后，这段话走到哪里就会复制到哪里。首先要保证质量啊，东西不赖啊。不然就用别的话来评论了。不知道这样子够不够85字。谢谢老板的认真检查。东西特别好，我不是刷评论的，我是觉得东西好我才买的，你会发现我每一家都是这么写的。因为复制一下就好了。')

if __name__ == '__main__':
    # '''
    # results=run_score_file()
    # aa=handel_result(results)
    # print aa
    # write_results(aa)
    # '''
    # data=pd.read_csv('sense.csv')
    # content=data['content'].tolist()
    # #content=content[:500]
    # score = data['score'].tolist()
    # i=0
    # diff=open('diff.csv','w')
    # for ct in content:
    #     re=sentiment_score(ct)[0]
    #     s=sentiment_score(ct)[1]
    #     diff.writelines('%d,%s,%d\n'%(i+1,re,s))
    #     i=i+1
    #     print i
    #
    a='这款面膜非常好用，补水效果很好，在苏宁上购买非常实惠，便宜非常好，赞一个。'
    print(sentiment_score(a)[1])