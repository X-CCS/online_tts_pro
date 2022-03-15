#!/usr/bin/env python3
#-*- coding: utf8 -*-

import re
import logging
from pypinyin import lazy_pinyin, load_phrases_dict, \
                     Style, load_phrases_dict, load_single_dict
from frontend.extra_data import pinyin_dict
import jieba.posseg as pseg


load_phrases_dict(pinyin_dict.phrases_dict)
load_single_dict(pinyin_dict.single_dict)

chinese_reg = '[\u4E00-\u9FA5]'
chinese_num_reg = '零|一|二|三|四|五|六|七|八|九|零|壹|贰|叁|肆|伍|陆|柒|捌|玖|貳|參|陸'

def get_pinyin(text_list, style=Style.TONE3):
    res = []
    for idx, word in enumerate(text_list):
        word_pinyin = lazy_pinyin(word, style=style, neutral_tone_with_five=True)
        logging.info("word {} lazy_pinyin: {}".format(word, word_pinyin))

        # AABB reading
        if len(word_pinyin) == 4:
            if word[-2] == word[-1] and re.search(chinese_reg, word[-2]) and not re.search(chinese_num_reg, word[-2]):
                word_pinyin[-1] = word_pinyin[-1][:-1] + word_pinyin[-2][-1]

            if (word[-4] == word[-3] and re.search(chinese_reg, word[-3]) and not re.search(chinese_num_reg, word[-3])):
                word_pinyin[-3] = word_pinyin[-3][:-1] + word_pinyin[-4][-1]

        # modified tone
        if len(word_pinyin) > 1:
            count = 0
            for word_idx, _ in enumerate(word_pinyin[1:]):
                if word_pinyin[word_idx][-1] == '3' and word_pinyin[word_idx+1][-1] == '3':
                    count = count + 1
                elif count != 0:
                    while count:
                        word_pinyin[word_idx-count] = ''.join([word_pinyin[word_idx-count][:-1], '2'])
                        count = count - 1

                if word_idx+2 == len(word_pinyin) and count != 0:
                    while count:
                        word_pinyin[word_idx+1-count] = ''.join([word_pinyin[word_idx+1-count][:-1], '2'])
                        count = count - 1

        # "不"change tone
        if '不' in word:
            bu_index = word.index('不')
            if bu_index < len(word) - 1:
                tone = word_pinyin[bu_index + 1][-1]
            elif idx + 1 < len(text_list):
                tone = lazy_pinyin(text_list[idx + 1], style=style, neutral_tone_with_five=True)[0][-1]
            else:
                tone = ''

            if re.match('[1-5]', tone):
                word_pinyin[bu_index] = word_pinyin[bu_index][:-1] + ('2' if eval(tone) == 4 else '4')

        # "一"change tone
        if '一' in word:
            yi_index = word.index('一')
            if yi_index < len(word) - 1 and not re.search(chinese_num_reg+'|月', text_list[idx][yi_index + 1]):
                tone = word_pinyin[yi_index + 1][-1]
            elif idx + 1 < len(text_list) and not re.search(chinese_num_reg+'|月', text_list[idx + 1]):
                tone = lazy_pinyin(text_list[idx + 1], style=style, neutral_tone_with_five=True)[0][-1]
            else:
                tone = ''

            if re.match('[1-5]', tone):
                word_pinyin[yi_index] = word_pinyin[yi_index][:-1] + ('2' if eval(tone) == 4 else word_pinyin[yi_index][-1])

        # "得"change tone
        if '得' in word:
            de_die_index = word.index('得')
            if len(word) == 1 and idx + 1 < len(text_list):
                for w in pseg.cut(text_list[idx + 1]):
                    if w.flag == 'v':
                        word_pinyin[de_die_index] = 'die3'

        # "地"change tone
        if '地' in word:
            de_di_index = word.index('地')
            if len(word) == 1:
                if idx + 1 < len(text_list):
                    w = list(pseg.cut(text_list[idx + 1]))[0]
                    if w.flag == 'v':
                        word_pinyin[de_di_index] = 'de5'

                if idx > 0 and word_pinyin[de_di_index] != 'de5':
                    w = list(pseg.cut(text_list[idx - 1]))[0]
                    if w.flag == 'd':
                        word_pinyin[de_di_index] = 'de5'

        if res and res[-1][-1][-1] == '3' and word_pinyin[0][-1] == '3':
            res[-1][-1] = res[-1][-1][:-1] + '2'
        res.append(word_pinyin)

    return res
