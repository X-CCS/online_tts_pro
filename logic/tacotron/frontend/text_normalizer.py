#!/usr/bin/env python3
#-*- coding: utf8 -*-

import re

from frontend.chinese_normalizer import num2chn as num2cn


CN_KEY = [u'[\u4e00-\u9fff]+']
EN_KEY = ['[a-zA-Z]+']
MUM_KEY = ['\d+\.\d+', '\d+']

PRE_UNITS = {
    "%": "百分之",
}

POST_UNITS = {
    # 科学符号
    "cm": "厘米",
    "km": "公里",
    "kg": "公斤",
    "g": "克",

    # 货币符号
    "$": "美元",
    "¥": "人民币",

    # 其他
    "——": "",
    "张三/李四": "张三跟李四",
    "……": "",
    "拨110": "拨幺幺零",
    "XX": "某某",
    "××": "某某",
    "华纳-兄弟": "华纳兄弟",
    "666": "六六六",
    "「": "",
    "」": "",
    "广州-北京": "广州到北京",
    "985": "九八五",
    "211": "二幺幺",
}

units_key = list(PRE_UNITS.keys()) + list(POST_UNITS.keys())
regex_str = '('+"|".join(CN_KEY + EN_KEY + MUM_KEY + units_key)+')'
keys_regex = re.compile(regex_str)


def w2s(in_str):
    results = []
    i = 0

    strings = keys_regex.split(in_str)
    strings = list(filter(None, strings))

    while i < len(strings):
        # 处理数字串
        if strings[i].replace('.', '', 1).isdecimal():
            # 处理其后有符号情况
            if i+1 < len(strings):
                # 处理发音前置符号：
                if strings[i+1] in PRE_UNITS:
                    results.append(PRE_UNITS[strings[i+1]])
                    results.append(num2cn(strings[i]))
                    i += 2
                    continue
                # 处理发音后置符号：
                elif strings[i+1] in POST_UNITS:
                    results.append(num2cn(strings[i]))
                    results.append(POST_UNITS[strings[i+1]])
                    i += 2
                    continue

            # 整数：以“年”结尾或长度大于等于8，则拼读
            if (strings[i].isdecimal() and ((i+1 < len(strings) and 
                strings[i+1].startswith("年")) or len(strings[i]) >= 8)):
                results.append(num2cn(strings[i], use_units=False))
            else:
                results.append(num2cn(strings[i]))
        else:
            results.append(strings[i])
        i += 1

    return "".join(results)


if __name__ == '__main__':
    # raw_text = "小王的身高是153.5cm,梦想是打篮球!我觉得有0.1%的可能性。"
    # raw_text = "固话：0595-23865596或23880880。"
    # raw_text = "分数：32477/76391。"
    # raw_text = "有62％的概率"
    # raw_text= "https://ai.aliyun.com/nls/tts"
    # raw_text= "CCS_6951467@163.com"
    # raw_text= "9*1=9"
    # raw_text= "周××交通肇事一案"
    raw_text= "二〇一七年十月"
    res = w2s(raw_text)
    print("res:",res)
