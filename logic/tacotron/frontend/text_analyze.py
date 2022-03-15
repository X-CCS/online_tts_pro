#!/usr/bin/env python3
#-*- coding: utf8 -*-

import os
import time
import argparse
import re
import logging

# import pkuseg
from jieba import load_userdict
import jieba.posseg as pseg
import cn2an

from frontend.chinese_normalizer import nsw_normalizer
from frontend.word2pinyin import get_pinyin
from frontend.text_normalizer import w2s, POST_UNITS
from frontend.langconv import Converter

from frontend.prosody.inference import load_ckpt, predict


PAUSE_SYMBOLS = [r'，',r'。',r'？',r'｜',r'！',r'；',r'（',r'）',
                 r',',r'\?',r'!',r'?',r'…','\n']

PHONE_LIST = {'A':['^', 'ei1'], 'B':['b', 'i1'], 'C':['x', 'i1'], 'D':['d', 'i1'], 'E':['^', 'i1'], 'F':['EH1', 'F'],
              'G':['j', 'i1'], 'H':['EY1', 'CH'], 'I':['AY1'], 'J':['JH', 'EY1'], 'K':['K', 'EY1'], 'L':['EH1', 'L'],
              'M':['EH1', 'M'], 'N':['EH1', 'N'], 'O':['OW1'], 'P':['P', 'IY1'], 'Q':['K', 'Y', 'UW1'], 'R':['AA1', 'R'],
              'S':['EH1', 'S'], 'T':['T', 'IY1'], 'U':['Y', 'UW1'], 'V':['V', 'IY1'],
              'W':['D', 'AH1', 'B', 'AH0', 'L', 'Y', 'UW0'], 'X':['EH1', 'K', 'S'], 'Y':['W', 'AY1'], 'Z':['Z', 'IY1']
             }

pinyin_map = {"a": ["^", "a"], "ai": ["^", "ai"], "an": ["^", "an"], "ang": ["^", "ang"], "ao": ["^", "ao"], "ba": ["b", "a"], "bai": ["b", "ai"], "ban": ["b", "an"], "bang": ["b", "ang"], "bao": ["b", "ao"], "be": ["b", "e"], "bei": ["b", "ei"], "ben": ["b", "en"], "beng": ["b", "eng"], "bi": ["b", "i"], "bian": ["b", "ian"], "biao": ["b", "iao"], "bie": ["b", "ie"], "bin": ["b", "in"], "bing": ["b", "ing"], "bo": ["b", "o"], "bu": ["b", "u"], "ca": ["c", "a"], "cai": ["c", "ai"], "can": ["c", "an"], "cang": ["c", "ang"], "cao": ["c", "ao"], "ce": ["c", "e"], "cen": ["c", "en"], "ceng": ["c", "eng"], "cha": ["ch", "a"], "chai": ["ch", "ai"], "chan": ["ch", "an"], "chang": ["ch", "ang"], "chao": ["ch", "ao"], "che": ["ch", "e"], "chen": ["ch", "en"], "cheng": ["ch", "eng"], "chi": ["ch", "iii"], "chong": ["ch", "ong"], "chou": ["ch", "ou"], "chu": ["ch", "u"], "chua": ["ch", "ua"], "chuai": ["ch", "uai"], "chuan": ["ch", "uan"], "chuang": ["ch", "uang"], "chui": ["ch", "uei"], "chun": ["ch", "uen"], "chuo": ["ch", "uo"], "ci": ["c", "ii"], "cong": ["c", "ong"], "cou": ["c", "ou"], "cu": ["c", "u"], "cuan": ["c", "uan"], "cui": ["c", "uei"], "cun": ["c", "uen"], "cuo": ["c", "uo"], "da": ["d", "a"], "dai": ["d", "ai"], "dan": ["d", "an"], "dang": ["d", "ang"], "dao": ["d", "ao"], "de": ["d", "e"], "dei": ["d", "ei"], "den": ["d", "en"], "deng": ["d", "eng"], "di": ["d", "i"], "dia": ["d", "ia"], "dian": ["d", "ian"], "diao": ["d", "iao"], "die": ["d", "ie"], "ding": ["d", "ing"], "diu": ["d", "iou"], "dong": ["d", "ong"], "dou": ["d", "ou"], "du": ["d", "u"], "duan": ["d", "uan"], "dui": ["d", "uei"], "dun": ["d", "uen"], "duo": ["d", "uo"], "e": ["^", "e"], "ei": ["^", "ei"], "en": ["^", "en"], "ng": ["^", "en"], "eng": ["^", "eng"], "er": ["^", "er"], "fa": ["f", "a"], "fan": ["f", "an"], "fang": ["f", "ang"], "fei": ["f", "ei"], "fen": ["f", "en"], "feng": ["f", "eng"], "fo": ["f", "o"], "fou": ["f", "ou"], "fu": ["f", "u"], "ga": ["g", "a"], "gai": ["g", "ai"], "gan": ["g", "an"], "gang": ["g", "ang"], "gao": ["g", "ao"], "ge": ["g", "e"], "gei": ["g", "ei"], "gen": ["g", "en"], "geng": ["g", "eng"], "gong": ["g", "ong"], "gou": ["g", "ou"], "gu": ["g", "u"], "gua": ["g", "ua"], "guai": ["g", "uai"], "guan": ["g", "uan"], "guang": ["g", "uang"], "gui": ["g", "uei"], "gun": ["g", "uen"], "guo": ["g", "uo"], "ha": ["h", "a"], "hai": ["h", "ai"], "han": ["h", "an"], "hang": ["h", "ang"], "hao": ["h", "ao"], "he": ["h", "e"], "hei": ["h", "ei"], "hen": ["h", "en"], "heng": ["h", "eng"], "hong": ["h", "ong"], "hou": ["h", "ou"], "hu": ["h", "u"], "hua": ["h", "ua"], "huai": ["h", "uai"], "huan": ["h", "uan"], "huang": ["h", "uang"], "hui": ["h", "uei"], "hun": ["h", "uen"], "huo": ["h", "uo"], "ji": ["j", "i"], "jia": ["j", "ia"], "jian": ["j", "ian"], "jiang": ["j", "iang"], "jiao": ["j", "iao"], "jie": ["j", "ie"], "jin": ["j", "in"], "jing": ["j", "ing"], "jiong": ["j", "iong"], "jiu": ["j", "iou"], "ju": ["j", "v"], "juan": ["j", "van"], "jue": ["j", "ve"], "jun": ["j", "vn"], "ka": ["k", "a"], "kai": ["k", "ai"], "kan": ["k", "an"], "kang": ["k", "ang"], "kao": ["k", "ao"], "ke": ["k", "e"], "kei": ["k", "ei"], "ken": ["k", "en"], "keng": ["k", "eng"], "kong": ["k", "ong"], "kou": ["k", "ou"], "ku": ["k", "u"], "kua": ["k", "ua"], "kuai": ["k", "uai"], "kuan": ["k", "uan"], "kuang": ["k", "uang"], "kui": ["k", "uei"], "kun": ["k", "uen"], "kuo": ["k", "uo"], "la": ["l", "a"], "lai": ["l", "ai"], "lan": ["l", "an"], "lang": ["l", "ang"], "lao": ["l", "ao"], "le": ["l", "e"], "lei": ["l", "ei"], "leng": ["l", "eng"], "li": ["l", "i"], "lia": ["l", "ia"], "lian": ["l", "ian"], "liang": ["l", "iang"], "liao": ["l", "iao"], "lie": ["l", "ie"], "lin": ["l", "in"], "ling": ["l", "ing"], "liu": ["l", "iou"], "lo": ["l", "o"], "long": ["l", "ong"], "lou": ["l", "ou"], "lu": ["l", "u"], "lv": ["l", "v"], "luan": ["l", "uan"], "lve": ["l", "ve"], "lue": ["l", "ve"], "lun": ["l", "uen"], "luo": ["l", "uo"], "ma": ["m", "a"], "mai": ["m", "ai"], "man": ["m", "an"], "mang": ["m", "ang"], "mao": ["m", "ao"], "me": ["m", "e"], "mei": ["m", "ei"], "men": ["m", "en"], "meng": ["m", "eng"], "mi": ["m", "i"], "mian": ["m", "ian"], "miao": ["m", "iao"], "mie": ["m", "ie"], "min": ["m", "in"], "ming": ["m", "ing"], "miu": ["m", "iou"], "mo": ["m", "o"], "mou": ["m", "ou"], "mu": ["m", "u"], "na": ["n", "a"], "nai": ["n", "ai"], "nan": ["n", "an"], "nang": ["n", "ang"], "nao": ["n", "ao"], "ne": ["n", "e"], "nei": ["n", "ei"], "nen": ["n", "en"], "neng": ["n", "eng"], "ni": ["n", "i"], "nia": ["n", "ia"], "nian": ["n", "ian"], "niang": ["n", "iang"], "niao": ["n", "iao"], "nie": ["n", "ie"], "nin": ["n", "in"], "ning": ["n", "ing"], "niu": ["n", "iou"], "nong": ["n", "ong"], "nou": ["n", "ou"], "nu": ["n", "u"], "nv": ["n", "v"], "nuan": ["n", "uan"], "nve": ["n", "ve"], "nue": ["n", "ve"], "nuo": ["n", "uo"], "o": ["^", "o"], "ou": ["^", "ou"], "pa": ["p", "a"], "pai": ["p", "ai"], "pan": ["p", "an"], "pang": ["p", "ang"], "pao": ["p", "ao"], "pe": ["p", "e"], "pei": ["p", "ei"], "pen": ["p", "en"], "peng": ["p", "eng"], "pi": ["p", "i"], "pian": ["p", "ian"], "piao": ["p", "iao"], "pie": ["p", "ie"], "pin": ["p", "in"], "ping": ["p", "ing"], "po": ["p", "o"], "pou": ["p", "ou"], "pu": ["p", "u"], "qi": ["q", "i"], "qia": ["q", "ia"], "qian": ["q", "ian"], "qiang": ["q", "iang"], "qiao": ["q", "iao"], "qie": ["q", "ie"], "qin": ["q", "in"], "qing": ["q", "ing"], "qiong": ["q", "iong"], "qiu": ["q", "iou"], "qu": ["q", "v"], "quan": ["q", "van"], "que": ["q", "ve"], "qun": ["q", "vn"], "ran": ["r", "an"], "rang": ["r", "ang"], "rao": ["r", "ao"], "re": ["r", "e"], "ren": ["r", "en"], "reng": ["r", "eng"], "ri": ["r", "iii"], "rong": ["r", "ong"], "rou": ["r", "ou"], "ru": ["r", "u"], "rua": ["r", "ua"], "ruan": ["r", "uan"], "rui": ["r", "uei"], "run": ["r", "uen"], "ruo": ["r", "uo"], "sa": ["s", "a"], "sai": ["s", "ai"], "san": ["s", "an"], "sang": ["s", "ang"], "sao": ["s", "ao"], "se": ["s", "e"], "sen": ["s", "en"], "seng": ["s", "eng"], "sha": ["sh", "a"], "shai": ["sh", "ai"], "shan": ["sh", "an"], "shang": ["sh", "ang"], "shao": ["sh", "ao"], "she": ["sh", "e"], "shei": ["sh", "ei"], "shen": ["sh", "en"], "sheng": ["sh", "eng"], "shi": ["sh", "iii"], "shou": ["sh", "ou"], "shu": ["sh", "u"], "shua": ["sh", "ua"], "shuai": ["sh", "uai"], "shuan": ["sh", "uan"], "shuang": ["sh", "uang"], "shui": ["sh", "uei"], "shun": ["sh", "uen"], "shuo": ["sh", "uo"], "si": ["s", "ii"], "song": ["s", "ong"], "sou": ["s", "ou"], "su": ["s", "u"], "suan": ["s", "uan"], "sui": ["s", "uei"], "sun": ["s", "uen"], "suo": ["s", "uo"], "ta": ["t", "a"], "tai": ["t", "ai"], "tan": ["t", "an"], "tang": ["t", "ang"], "tao": ["t", "ao"], "te": ["t", "e"], "tei": ["t", "ei"], "teng": ["t", "eng"], "ti": ["t", "i"], "tian": ["t", "ian"], "tiao": ["t", "iao"], "tie": ["t", "ie"], "ting": ["t", "ing"], "tong": ["t", "ong"], "tou": ["t", "ou"], "tu": ["t", "u"], "tuan": ["t", "uan"], "tui": ["t", "uei"], "tun": ["t", "uen"], "tuo": ["t", "uo"], "wa": ["^", "ua"], "wai": ["^", "uai"], "wan": ["^", "uan"], "wang": ["^", "uang"], "wei": ["^", "uei"], "wen": ["^", "uen"], "weng": ["^", "ueng"], "wo": ["^", "uo"], "wu": ["^", "u"], "xi": ["x", "i"], "xia": ["x", "ia"], "xian": ["x", "ian"], "xiang": ["x", "iang"], "xiao": ["x", "iao"], "xie": ["x", "ie"], "xin": ["x", "in"], "xing": ["x", "ing"], "xiong": ["x", "iong"], "xiu": ["x", "iou"], "xu": ["x", "v"], "xuan": ["x", "van"], "xue": ["x", "ve"], "xun": ["x", "vn"], "ya": ["^", "ia"], "yan": ["^", "ian"], "yang": ["^", "iang"], "yao": ["^", "iao"], "ye": ["^", "ie"], "yi": ["^", "i"], "yin": ["^", "in"], "ying": ["^", "ing"], "yo": ["^", "iou"], "yong": ["^", "iong"], "you": ["^", "iou"], "yu": ["^", "v"], "yuan": ["^", "van"], "yue": ["^", "ve"], "yun": ["^", "vn"], "za": ["z", "a"], "zai": ["z", "ai"], "zan": ["z", "an"], "zang": ["z", "ang"], "zao": ["z", "ao"], "ze": ["z", "e"], "zei": ["z", "ei"], "zen": ["z", "en"], "zeng": ["z", "eng"], "zha": ["zh", "a"], "zhai": ["zh", "ai"], "zhan": ["zh", "an"], "zhang": ["zh", "ang"], "zhao": ["zh", "ao"], "zhe": ["zh", "e"], "zhei": ["zh", "ei"], "zhen": ["zh", "en"], "zheng": ["zh", "eng"], "zhi": ["zh", "iii"], "zhong": ["zh", "ong"], "zhou": ["zh", "ou"], "zhu": ["zh", "u"], "zhua": ["zh", "ua"], "zhuai": ["zh", "uai"], "zhuan": ["zh", "uan"], "zhuang": ["zh", "uang"], "zhui": ["zh", "uei"], "zhun": ["zh", "uen"], "zhuo": ["zh", "uo"], "zi": ["z", "ii"], "zong": ["z", "ong"], "zou": ["z", "ou"], "zu": ["z", "u"], "zuan": ["z", "uan"], "zui": ["z", "uei"], "zun": ["z", "uen"], "zuo": ["z", "uo"]}

def get_en_ph(words):
    res = []
    for idx_i, i in enumerate(words):
        res.append([])
        for idx_j, j in enumerate(i):
            if j.isupper():
                units = re.compile(r'[A-Z]').findall(j)
                for unit in units:
                    res[-1].extend(PHONE_LIST[unit])
            else:
                res[-1].append(j)
    return res


"""
判断列表中的元素是否在字符串中出现，返回该元素，没有返回None
""" 
def list_element_in_text(input_list:list,text:str):
    list_=[]
    for i in input_list:
        if i in text:
           list_.append(i)
    return list_


"""
判断字符串是否是纯数字，有小数和负数
"""
def is_number(s):
    try:  # 如果能运行float(s)语句，返回True（字符串s是浮点数）
        float(s)
        return True
    except ValueError:  # ValueError为Python的一种标准异常，表示"传入无效的参数"
        pass  # 如果引发了ValueError这种异常，不做任何事情（pass：不做任何事情，一般用做占位语句）
    try:
        import unicodedata  # 处理ASCii码的包
        unicodedata.numeric(s)  # 把一个表示数字的字符串转换为浮点数返回的函数
        return True
    except (TypeError, ValueError):
        pass
    return False


class TextAnalysis:
    def __init__(self, nthread=5, user_dict="default", match_keywords=list(POST_UNITS.keys())):
        self.match_keywords = match_keywords
        self.nthread = nthread
        # self.seg = pkuseg.pkuseg(user_dict=user_dict, postag=True)
        load_userdict(user_dict)
        self.seg = pseg
        self.nets = load_ckpt()
        self.converter = Converter('zh-hans')

    def normalize(self, raw_text):
        is_match = True if any(i in raw_text for i in self.match_keywords) else False
        if is_match:
            logging.info(is_match)
            element=list_element_in_text(self.match_keywords, raw_text)
            for i in element:
                i = str(i)
                raw_text = raw_text.replace(i, POST_UNITS[i]) # 将字典名替换成字典内容
            text = w2s(raw_text)
        elif is_number(raw_text):
            if ("E" in raw_text) or ("e" in raw_text):
                text = nsw_normalizer(raw_text).normalize()
            else:
                text = cn2an.an2cn(raw_text, "low")
        else:
            text = nsw_normalizer(raw_text).normalize()

        return text


    def stream_text_to_pinyin(self, text):
        acc_time = 0.0
        check = time.time()
        text = self.converter.convert(text)
        text = self.normalize(text)
        logging.info("text normalize: {}".format(text))
        readlines = text.split('\n')
        for line in readlines:
            line = line.strip()
            if not line:
                continue

            words, pos = [], []
            # for k, v in self.seg.cut(line):
            for k, v in pseg.cut(line, use_paddle=True):
                words.append(k)
                pos.append(v)

            prosody = predict(self.nets, words, pos)
            res = get_pinyin(words)
            res = get_en_ph(res)
            result = []
            for i, [c, p] in enumerate(zip(res, prosody)):
                for idx, item in enumerate(c):
                    if item in ':：()“”《》、':
                        c[idx] = '#2'
                    elif item in '-~':
                        c[idx] = '#3'
                result.extend(c)
                if p:
                    result.extend([p])

            for segment in split_sentence(result):
                logging.info("pinyin segment: {}".format(' '.join(segment)))
                start, end = None, None
                for i, _ in enumerate(segment):
                    if start and end:
                        break

                    if start == None and segment[i][0] != '#':
                        start = i

                    if end == None and segment[-i-1][0] != '#':
                        end = len(segment) - i

                segment = segment[start:end]
                for i in range(len(segment)-2, 0, -1):
                    if segment[i][0] == '#' and segment[i+1][0] == '#':
                        del segment[i+1 if int(segment[i][1]) > int(segment[i+1][1]) else i]

                if not segment:
                    continue

                new_segment = []
                for i in segment:
                    if len(i) > 1 and i[:-1] in pinyin_map:
                        new_segment.extend(pinyin_map[i[:-1]])
                        if pinyin_map[i[:-1]][-1] == 'r':
                            new_segment[-2]=new_segment[-2]+i[-1]
                        else:
                            new_segment[-1]=new_segment[-1]+i[-1]
                    
                    elif i[0] == '#' or i[0] == '^' or i[0] == '{' or re.match('[A-Z]',i[0]):
                        new_segment.append(i)
                    else:
                        logging.warning("invalid character: \"{}\" erase".format(i))

                if new_segment[-1][0] == '#':
                    new_segment = new_segment[:-1]

                new_segment.insert(0, 'sil')
                if len(new_segment) == 78:
                    new_segment.append('^')
                new_segment.extend(['sil', 'eos'])
                output = ' '.join(new_segment)

                acc_time += time.time() - check
                yield output
                check = time.time()

        logging.info("frontend total time:{}".format(acc_time))


def split_sentence(sentence, symbol=PAUSE_SYMBOLS):
    res = []
    start = 0
    sen_len = len(sentence)
    for idx, char in enumerate(sentence):
        if char in symbol:
            if start != idx:
                yield sentence[start:idx]
            start = idx + 1

        if sen_len == idx + 1:
            end = idx + 1
            if char in symbol:
                end = end - 1
            yield sentence[start:end]


def main(raw_text):
    parser = argparse.ArgumentParser()
    parser.add_argument("--user_dict", default='./frontend/extra_data/cut_dict.txt', 
                        help='input path of data')
    args = parser.parse_args()

    text_analysis = TextAnalysis(user_dict=args.user_dict)
    text_pinyin = list(text_analysis.text_to_pinyin(text=raw_text))
    print(text_pinyin)


if __name__ == '__main__':
    check = time.time()
    raw_text = "二〇一七年十月，“绿色水果”。没有用20cm！"
    main(raw_text)
    print('time cost : %.5f sec' % (time.time() - check))

