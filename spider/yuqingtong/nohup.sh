#!/usr/bin/env bash
nohup python -u sina.py > sina.out 2>&1 &
nohup python -u cailianpress.py > cailianpress.out 2>&1 &
nohup python -u cnstock.py > cnstock.out 2>&1 &
nohup python -u yicai.py > yicai.out 2>&1 &
nohup python -u cnfol_spider.py > cnfol_spider.out 2>&1 &
nohup python -u ce_spider.py > ce_spider.out 2>&1 &
nohup python -u hexun_spider.py > hexun_spider.out 2>&1 &
nohup python -u tencent_spider.py > tencent_spider.out 2>&1 &
nohup python -u 21caijing_spider.py > 21caijing_spider.out 2>&1 &
nohup python -u eastmoney.py > eastmoney.out 2>&1 &
nohup python -u ifeng_spider.py > ifeng_spider.out 2>&1 &
nohup python -u stcn.py > stcn.out 2>&1 &