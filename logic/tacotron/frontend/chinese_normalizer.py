#!/usr/bin/env python3
# coding=utf-8
# Authors: 
#   2020.9.13 changshu
#
# requirements:
#   - python 3.X
# notes: python 2.X WILL fail or produce misleading results

import sys, os, argparse, re
import cn2an
import logging
# ================================================================================ #
#                                    basic constant
# ================================================================================ #
CHINESE_DIGIS = u'零一二三四五六七八九'
BIG_CHINESE_DIGIS_SIMPLIFIED = u'零壹贰叁肆伍陆柒捌玖'
BIG_CHINESE_DIGIS_TRADITIONAL = u'零壹貳參肆伍陸柒捌玖'
SMALLER_BIG_CHINESE_UNITS_SIMPLIFIED = u'十百千万'
SMALLER_BIG_CHINESE_UNITS_TRADITIONAL = u'拾佰仟萬'
LARGER_CHINESE_NUMERING_UNITS_SIMPLIFIED = u'亿兆京垓秭穰沟涧正载'
LARGER_CHINESE_NUMERING_UNITS_TRADITIONAL = u'億兆京垓秭穰溝澗正載'
SMALLER_CHINESE_NUMERING_UNITS_SIMPLIFIED = u'十百千万'
SMALLER_CHINESE_NUMERING_UNITS_TRADITIONAL = u'拾佰仟萬'

ZERO_ALT = u'〇'
ONE_ALT = u'幺'
TWO_ALTS = [u'两', u'兩']

POSITIVE = [u'正', u'正']
NEGATIVE = [u'负', u'負']
POINT = [u'点', u'點']

# 中文数字系统类型
NUMBERING_TYPES = ['low', 'mid', 'high']

CURRENCY_NAMES = '(人民币|美元|日元|英镑|欧元|马克|法郎|加拿大元|澳元|港币|先令|芬兰马克|爱尔兰镑|' \
                 '里拉|荷兰盾|埃斯库多|比塞塔|印尼盾|林吉特|新西兰元|比索|卢布|新加坡元|韩元|泰铢)'
CURRENCY_UNITS = '((亿|千万|百万|万|千|百)|(亿|千万|百万|万|千|百|)元|(亿|千万|百万|万|千|百|)块|角|毛|分)'
COM_QUANTIFIERS = '(匹|张|座|回|场|尾|条|个|首|阙|阵|网|炮|顶|丘|棵|只|支|袭|辆|挑|担|颗|壳|窠|曲|墙|群|腔|' \
                  '砣|座|客|贯|扎|捆|刀|令|打|手|罗|坡|山|岭|江|溪|钟|队|单|双|对|出|口|头|脚|板|跳|枝|件|贴|' \
                  '针|线|管|名|位|身|堂|课|本|页|家|户|层|丝|毫|厘|分|钱|两|斤|担|铢|石|钧|锱|忽|(千|毫|微)克|' \
                  '毫|厘|分|寸|尺|丈|里|寻|常|铺|程|(千|分|厘|毫|微)米|撮|勺|合|升|斗|石|盘|碗|碟|叠|桶|笼|盆|' \
                  '盒|杯|钟|斛|锅|簋|篮|盘|桶|罐|瓶|壶|卮|盏|箩|箱|煲|啖|袋|钵|年|月|日|季|刻|时|周|天|秒|分|旬|' \
                  '纪|岁|世|更|夜|春|夏|秋|冬|代|伏|辈|丸|泡|粒|颗|幢|堆|条|根|支|道|面|片|张|颗|块)'

# punctuation information are based on Zhon project (https://github.com/tsroten/zhon.git)
CHINESE_PUNC_STOP = '！？｡。'
CHINESE_PUNC_NON_STOP = '＂＃＄％＆＇（）＊＋，－／：；＜＝＞＠［＼］＾＿｀｛｜｝～｟｠｢｣､、〃《》「」『』【】〔〕〖〗〘〙〚〛〜〝〞〟〰〾〿–—‘’‛“”„‟…‧﹏'
CHINESE_PUNC_LIST = CHINESE_PUNC_STOP + CHINESE_PUNC_NON_STOP

# ================================================================================ #
#                                    basic class
# ================================================================================ #
class ChineseChar(object):
    """
    中文字符
    每个字符对应简体和繁体,
    e.g. 简体 = '负', 繁体 = '負'
    转换时可转换为简体或繁体
    """

    def __init__(self, simplified, traditional):
        self.simplified = simplified
        self.traditional = traditional

    def __str__(self):
        return self.simplified or self.traditional or None

    def __repr__(self):
        return self.__str__()


class ChineseNumberUnit(ChineseChar):
    """
    中文数字/数位字符
    每个字符除繁简体外还有一个额外的大写字符
    e.g. '陆' 和 '陸'
    """

    def __init__(self, power, simplified, traditional, big_s, big_t):
        super(ChineseNumberUnit, self).__init__(simplified, traditional)
        self.power = power
        self.big_s = big_s
        self.big_t = big_t

    def __str__(self):
        return '10^{}'.format(self.power)

    @classmethod
    def create(cls, index, value, numbering_type=NUMBERING_TYPES[1], small_unit=False):

        if small_unit:
            return ChineseNumberUnit(power=index + 1,
                                     simplified=value[0], traditional=value[1], big_s=value[1], big_t=value[1])
        elif numbering_type == NUMBERING_TYPES[0]:
            return ChineseNumberUnit(power=index + 8,
                                     simplified=value[0], traditional=value[1], big_s=value[0], big_t=value[1])
        elif numbering_type == NUMBERING_TYPES[1]:
            return ChineseNumberUnit(power=(index + 2) * 4,
                                     simplified=value[0], traditional=value[1], big_s=value[0], big_t=value[1])
        elif numbering_type == NUMBERING_TYPES[2]:
            return ChineseNumberUnit(power=pow(2, index + 3),
                                     simplified=value[0], traditional=value[1], big_s=value[0], big_t=value[1])
        else:
            raise ValueError(
                'Counting type should be in {0} ({1} provided).'.format(NUMBERING_TYPES, numbering_type))


class ChineseNumberDigit(ChineseChar):
    """
    中文数字字符
    """

    def __init__(self, value, simplified, traditional, big_s, big_t, alt_s=None, alt_t=None):
        super(ChineseNumberDigit, self).__init__(simplified, traditional)
        self.value = value
        self.big_s = big_s
        self.big_t = big_t
        self.alt_s = alt_s
        self.alt_t = alt_t

    def __str__(self):
        return str(self.value)

    @classmethod
    def create(cls, i, v):
        return ChineseNumberDigit(i, v[0], v[1], v[2], v[3])


class ChineseMath(ChineseChar):
    """
    中文数位字符
    """

    def __init__(self, simplified, traditional, symbol, expression=None):
        super(ChineseMath, self).__init__(simplified, traditional)
        self.symbol = symbol
        self.expression = expression
        self.big_s = simplified
        self.big_t = traditional


CC, CNU, CND, CM = ChineseChar, ChineseNumberUnit, ChineseNumberDigit, ChineseMath


class NumberSystem(object):
    """
    中文数字系统
    """
    pass


class MathSymbol(object):
    """
    用于中文数字系统的数学符号 (繁/简体), e.g.
    positive = ['正', '正']
    negative = ['负', '負']
    point = ['点', '點']
    """

    def __init__(self, positive, negative, point):
        self.positive = positive
        self.negative = negative
        self.point = point

    def __iter__(self):
        for v in self.__dict__.values():
            yield v


# ================================================================================ #
#                                    basic utils
# ================================================================================ #
def create_system(numbering_type=NUMBERING_TYPES[1]):
    """
    根据数字系统类型返回创建相应的数字系统，默认为 mid
    NUMBERING_TYPES = ['low', 'mid', 'high']: 中文数字系统类型
        low:  '兆' = '亿' * '十' = $10^{9}$,  '京' = '兆' * '十', etc.
        mid:  '兆' = '亿' * '万' = $10^{12}$, '京' = '兆' * '万', etc.
        high: '兆' = '亿' * '亿' = $10^{16}$, '京' = '兆' * '兆', etc.
    返回对应的数字系统
    """

    # chinese number units of '亿' and larger
    all_larger_units = zip(
        LARGER_CHINESE_NUMERING_UNITS_SIMPLIFIED, LARGER_CHINESE_NUMERING_UNITS_TRADITIONAL)
    larger_units = [CNU.create(i, v, numbering_type, False)
                    for i, v in enumerate(all_larger_units)]
    # chinese number units of '十, 百, 千, 万'
    all_smaller_units = zip(
        SMALLER_CHINESE_NUMERING_UNITS_SIMPLIFIED, SMALLER_CHINESE_NUMERING_UNITS_TRADITIONAL)
    smaller_units = [CNU.create(i, v, small_unit=True)
                     for i, v in enumerate(all_smaller_units)]
    # digis
    chinese_digis = zip(CHINESE_DIGIS, CHINESE_DIGIS,
                        BIG_CHINESE_DIGIS_SIMPLIFIED, BIG_CHINESE_DIGIS_TRADITIONAL)
    digits = [CND.create(i, v) for i, v in enumerate(chinese_digis)]
    digits[0].alt_s, digits[0].alt_t = ZERO_ALT, ZERO_ALT
    digits[1].alt_s, digits[1].alt_t = ONE_ALT, ONE_ALT
    digits[2].alt_s, digits[2].alt_t = TWO_ALTS[0], TWO_ALTS[1]

    # symbols
    positive_cn = CM(POSITIVE[0], POSITIVE[1], '+', lambda x: x)
    negative_cn = CM(NEGATIVE[0], NEGATIVE[1], '-', lambda x: -x)
    point_cn = CM(POINT[0], POINT[1], '.', lambda x,
                  y: float(str(x) + '.' + str(y)))
    system = NumberSystem()
    system.units = smaller_units + larger_units
    system.digits = digits
    system.math = MathSymbol(positive_cn, negative_cn, point_cn)
    return system


def num2chn(number_string, numbering_type=NUMBERING_TYPES[1], big=False,
            traditional=False, alt_zero=False, alt_one=False, alt_two=True,
            use_zeros=True, use_units=True):

    def get_value(value_string, use_zeros=True):

        striped_string = value_string.lstrip('0')

        # record nothing if all zeros
        if not striped_string:
            return []

        # record one digits
        elif len(striped_string) == 1:
            if use_zeros and len(value_string) != len(striped_string):
                return [system.digits[0], system.digits[int(striped_string)]]
            else:
                return [system.digits[int(striped_string)]]

        # recursively record multiple digits
        else:
            result_unit = next(u for u in reversed(
                system.units) if u.power < len(striped_string))
            result_string = value_string[:-result_unit.power]
            return get_value(result_string) + [result_unit] + get_value(striped_string[-result_unit.power:])

    system = create_system(numbering_type)

    int_dec = number_string.split('.')
    if len(int_dec) == 1:
        int_string = int_dec[0]
        dec_string = ""
    elif len(int_dec) == 2:
        int_string = int_dec[0]
        dec_string = int_dec[1]
    else:
        raise ValueError(
            "invalid input num string with more than one dot: {}".format(number_string))

    if use_units and len(int_string) > 1:
        result_symbols = get_value(int_string)
    else:
        result_symbols = [system.digits[int(c)] for c in int_string]
    dec_symbols = [system.digits[int(c)] for c in dec_string]
    if dec_string:
        result_symbols += [system.math.point] + dec_symbols

    if alt_two:
        liang = CND(2, system.digits[2].alt_s, system.digits[2].alt_t,
                    system.digits[2].big_s, system.digits[2].big_t)
        for i, v in enumerate(result_symbols):
            if isinstance(v, CND) and v.value == 2:
                next_symbol = result_symbols[i +
                                             1] if i < len(result_symbols) - 1 else None
                previous_symbol = result_symbols[i - 1] if i > 0 else None
                if isinstance(next_symbol, CNU) and isinstance(previous_symbol, (CNU, type(None))):
                    if next_symbol.power != 1 and ((previous_symbol is None) or (previous_symbol.power != 1)):
                        result_symbols[i] = liang

    # if big is True, '两' will not be used and `alt_two` has no impact on output
    if big:
        attr_name = 'big_'
        if traditional:
            attr_name += 't'
        else:
            attr_name += 's'
    else:
        if traditional:
            attr_name = 'traditional'
        else:
            attr_name = 'simplified'

    result = ''.join([getattr(s, attr_name) for s in result_symbols])

    if alt_zero:
        result = result.replace(
            getattr(system.digits[0], attr_name), system.digits[0].alt_s)

    if alt_one:
        result = result.replace(
            getattr(system.digits[1], attr_name), system.digits[1].alt_s)

    for i, p in enumerate(POINT):
        if result.startswith(p):
            return CHINESE_DIGIS[0] + result

    # ^10, 11, .., 19
    if len(result) >= 2 and result[1] in [SMALLER_CHINESE_NUMERING_UNITS_SIMPLIFIED[0],
                                          SMALLER_CHINESE_NUMERING_UNITS_TRADITIONAL[0]] and \
            result[0] in [CHINESE_DIGIS[1], BIG_CHINESE_DIGIS_SIMPLIFIED[1], BIG_CHINESE_DIGIS_TRADITIONAL[1]]:
        result = result[1:]

    return result


# ================================================================================ #
#                          different types of rewriters
# ================================================================================ #
class Cardinal:
    """
    CARDINAL类
    """

    def __init__(self, cardinal=None, chntext=None):
        self.cardinal = cardinal
        self.chntext = chntext

    def chntext2cardinal(self):
        return chn2num(self.chntext)

    def cardinal2chntext(self):
        return num2chn(self.cardinal)

class Digit:
    """
    DIGIT类
    """

    def __init__(self, digit=None, chntext=None):
        self.digit = digit
        self.chntext = chntext

    def digit2chntext(self):
        return num2chn(self.digit, alt_two=False, use_units=False)


class TelePhone:
    """
    TELEPHONE类
    """

    def __init__(self, telephone=None, raw_chntext=None, chntext=None):
        self.telephone = telephone
        self.raw_chntext = raw_chntext
        self.chntext = chntext

    def telephone2chntext(self, fixed=False):

        if fixed:
            sil_parts = self.telephone.split('-')
            self.raw_chntext = '<SIL>'.join([
                num2chn(part, alt_two=False, use_units=False) for part in sil_parts
            ])
            self.chntext = self.raw_chntext.replace('<SIL>', '')
        else:
            sp_parts = self.telephone.strip('+').split()
            self.raw_chntext = '<SP>'.join([
                num2chn(part, alt_two=False, use_units=False) for part in sp_parts
            ])
            self.chntext = self.raw_chntext.replace('<SP>', '')
        return self.chntext


class Fraction:
    """
    FRACTION类
    """

    def __init__(self, fraction=None, chntext=None):
        self.fraction = fraction
        self.chntext = chntext

    def chntext2fraction(self):
        denominator, numerator = self.chntext.split('分之')
        return chn2num(numerator) + '/' + chn2num(denominator)

    def fraction2chntext(self):
        numerator, denominator = self.fraction.split('/')
        return num2chn(denominator) + '分之' + num2chn(numerator)


class Date:
    """
    DATE类
    """

    def __init__(self, date=None, chntext=None):
        self.date = date
        self.chntext = chntext

    def date2chntext(self):
        date = self.date
        try:
            year, other = date.strip().split('年', 1)
            year = Digit(digit=year).digit2chntext() + '年'
        except ValueError:
            other = date
            year = ''
        if other:
            try:
                month, day = other.strip().split('月', 1)
                month = Cardinal(cardinal=month).cardinal2chntext() + '月'
            except ValueError:
                day = date
                month = ''
            if day:
                day = Cardinal(cardinal=day[:-1]).cardinal2chntext() + day[-1]
        else:
            month = ''
            day = ''
        chntext = year + month + day
        self.chntext = chntext
        return self.chntext


class Money:
    """
    MONEY类
    """

    def __init__(self, money=None, chntext=None):
        self.money = money
        self.chntext = chntext

    def money2chntext(self):
        money = self.money
        pattern = re.compile(r'(\d+(\.\d+)?)')
        matchers = pattern.findall(money)
        if matchers:
            for matcher in matchers:
                money = money.replace(matcher[0], Cardinal(cardinal=matcher[0]).cardinal2chntext())
        self.chntext = money
        return self.chntext


class Percentage:
    """
    PERCENTAGE类
    """

    def __init__(self, percentage=None, chntext=None):
        self.percentage = percentage
        self.chntext = chntext

    def chntext2percentage(self):
        return chn2num(self.chntext.strip().strip('百分之')) + '%'

    def percentage2chntext(self):
        return '百分之' + num2chn(self.percentage.strip().strip('%'))


# ================================================================================ #
#                            NSW Normalizer
# ================================================================================ #
class nsw_normalizer:
    def __init__(self, raw_text):
        self.raw_text = '^' + raw_text + '$'
        self.norm_text = ''

    def _particular(self):
        text = self.norm_text
        pattern = re.compile(r"(([a-zA-Z]+)二([a-zA-Z]+))")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], matcher[1]+'2'+matcher[2], 1)
        self.norm_text = text
        return self.norm_text

    def normalize(self):
        text = self.raw_text
        ########################################################################
        # 规范化邮箱
        pattern = re.compile(r"[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('邮箱')
            for matcher in matchers:
                text = text.replace("126","一二六")
                text = text.replace("@","at")
                text = text.replace("_","下划线")
                text = text.replace(".","点")

        # 规范 任意数字元/天
        pattern = re.compile(r"((-|\+)?\d+(\.\d+)?[元|米/]/(天|秒))")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('任意数字元/天')
            for matcher in matchers:
                text = cn2an.transform(text, "an2cn")
                text = text.replace("/天","每天",1)
                text = text.replace("/秒","每秒",1)

        # 规范2-4成 2-4 (不严谨后续需要改)
        pattern = re.compile(r"\d{1}-\d{1}成")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('2-4成比分2-4')
            for matcher in matchers:
                text = text.replace("2","两",1)
                text = text.replace("-","到",1)
                text = text.replace("-","比",1)

        # 规范特殊数字 如：14，000
        pattern = re.compile(r"((\d+)，(\d+)颗)")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('特殊数字14，000')
            for matcher in matchers:
                text = text.replace("，","")
                text = cn2an.transform(text, "an2cn")

        # 规范科学计数法 如：1.03E+08、2.2602E-7、1.23400E-03
        pattern = re.compile(r"([+|-]?\d+(.{0}|.\d+))[Ee]{1}([+|-]?\d+)")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('规范科学计数法')
            for matcher in matchers:
                text = text.replace("E","乘以十的")
                text = text.replace("e","乘以十的")
                text = text.replace("$","次方") #将结尾的$替换成次方

        # 规范英文字母2英文字母 如：O2O或B2C。
        pattern = re.compile(r"[A-Za-z]+2[A-Za-z]")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('O2O或B2C')
            for matcher in matchers:
                text = text.replace("2"," to ")

        # 规范化小数点 如：2983.07克或12345.60米。
        pattern = re.compile(r"([0-9]{1,}[.][0-9]*)")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('文本中小数点')
            for matcher in matchers:
                text = cn2an.transform(text, "an2cn")
                text = text.replace(".","点")
                text = text.replace("二百零二","二零二")

        # 规范化182-3123-3213 (+86)182-3123-3213
        pattern = re.compile(r"(\d{3})-(\d{4})-(\d{4})")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('号码182-3123-3213 跟+86')
            for matcher in matchers:
                text = text.replace("-","")
                text = text.replace("+","")
                text = text.replace("(","")
                text = text.replace(")","")
                text = text.replace("（","")
                text = text.replace("）","")

        # 规范化 时间(pm am AM PM)
        pattern = re.compile(r"(\d{1,2}\:\d{1,2}(\s*?)(?:AM|PM|am|pm))")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('时间pm am AM PM')
            for matcher in matchers:
                text = position_swap(text)
                text = text.replace("pm","下午")
                text = text.replace("PM","下午")
                text = text.replace("am","上午")
                text = text.replace("AM","上午")
                text = text.replace(":","点")
                text = text.replace(" ","")
                text = text+"分"
                text = cn2an.transform(text, "an2cn") # 数值转换
                logging.info("text: {}".format(text))

        # 规范化 小时:分钟:秒
        pattern = re.compile(r"(0?[0-9]|1[0-9]|2[0-3]):(0?[0-9]|[1-5][0-9]):(0?[0-9]|[1-5][0-9])") #可以00或者0
        matchers = pattern.findall(text)
        if matchers:
            logging.info('小时:分钟:秒')
            for matcher in matchers:
                text = cn2an.transform(text, "an2cn") # 数值转换
                count=0
                num_list = []
                str_list=list(text)
                for each_char in str_list:
                    count+=1

                    if each_char==":":
                        num_list.append(count-1)

                text = text.replace(text[num_list[0]],"点",1) # 只是替换一次
                text = text.replace(text[num_list[1]],"分",1) # 只是替换一次
                text_list = list(text)
                text_list.insert(-1,"秒")
                text = "".join(text_list)
       
        # 规范化 小时:分钟 出现两次
        pattern = re.compile(r"(0?[0-9]|1[0-9]|2[0-3]):(0?[0-9]|[1-5][0-9])、(0?[0-9]|1[0-9]|2[0-3]):(0?[0-9]|[1-5][0-9])") #
        matchers = pattern.findall(text)
        if matchers:
            logging.info('小时:分钟两次')
            for matcher in matchers:
                text = text.replace(":","点")

                text_list = re.findall(r"\d+点\d+",text)
                text_list_1 = [i+"分" for i in text_list]

                index_1= text.index(str(text_list[0]))
                index_2= text.index(str(text_list[1]))

                a = index_1+len(str(text_list[0]))
                b = index_2+len(str(text_list[1]))

                text = text.replace(text[index_1:a],text_list_1[0])
                text = text.replace(text[index_2+1:b+1],text_list_1[1]) # 见了一个新词进去所以下标要往后+1
                text = text.replace("2场","两场")
                text = cn2an.transform(text, "an2cn") # 数值转换

        # 规范化 小时:分钟 只出现一个
        pattern = re.compile(r"(0?[0-9]|1[0-9]|2[0-3]):(0?[0-9]|[1-5][0-9])") #
        matchers = pattern.findall(text)
        if matchers:
            logging.info('小时:分钟')
            for matcher in matchers:
                logging.info("matcher:",matcher)
                text = text.replace(":","点")
                text = cn2an.transform(text, "an2cn") # 数值转换
                text_list = list(text)
                text_list.insert(-1,"分")
                text = "".join(text_list)

        # 规范化特殊符号，例如 〇
        pattern = re.compile(r".*〇.*")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('特殊符号')
            for matcher in matchers:
                text = text.replace("〇","零")

        # 规范化人民币，例如 ￥10.01￥10￥1,111.01￥1,000,12￥0.1￥10.00
        pattern = re.compile("￥(-?[0-9,]+)(\.[0-9]+)?")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('人民币符号')
            for matcher in matchers:
                text = text.replace("￥","人民币")

        # 规范化1%~3%
        pattern = re.compile(r".*[0-9]*%~[0-9]*%.*")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('1%~3%')
            for matcher in matchers:
                text = text.replace("~","到")

        # 规范化-10~+20
        pattern = re.compile(r"([+|-]?\d+(.{0}|.\d+))~([+|-]?\d+)")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('-10~+20')
            for matcher in matchers:
                text = cn2an.transform(text, "an2cn")
                text = text.replace("~","到")
                text = text.replace("+","正")

        # 规范化年/月/日
        pattern = re.compile(r"(?:(?:1[6-9]|[2-9][0-9])[0-9]{2}([/.]?)(?:(?:0?[1-9]|1[0-2])\1(?:0?[1-9]|1[0-9]|2[0-8])|(?:0?[13-9]|1[0-2])\1(?:29|30)|(?:0?[13578]|1[02])\1(?:31))|(?:(?:1[6-9]|[2-9][0-9])(?:0[48]|[2468][048]|[13579][26])|(?:16|[2468][048]|[3579][26])00)([/.]?)0?2\2(?:29))")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('年/月/日')
            for matcher in matchers:
                count = 0
                num_list = []
                str_list = list(text)
                for each_char in str_list:
                    count += 1

                    if each_char == "/":
                        num_list.append(count-1)

                text = text.replace(text[num_list[0]],"年",1) # 只是替换一次
                text = text.replace(text[num_list[1]],"月",1) # 只是替换一次
                text = cn2an.transform(text, "an2cn") # 数值转换
                text = text.replace("$","日",1) # 将最后一个$替换成日的读法

        # 规范化年-月-日
        pattern = re.compile(r"((((19|20)\d{2})-(0?(1|[3-9])|1[012])-(0?[1-9]|[12]\d|30))|(((19|20)\d{2})-(0?[13578]|1[02])-31)|(((19|20)\d{2})-0?2-(0?[1-9]|1\d|2[0-8]))|((((19|20)([13579][26]|[2468][048]|0[48]))|(2000))-0?2-29))")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('年-月-日')
            for matcher in matchers:
                count=0
                num_list = []
                str_list=list(text)
                for each_char in str_list:
                    count+=1

                    if each_char=="-":
                        num_list.append(count-1)

                text = text.replace(text[num_list[0]],"年",1) # 只是替换一次
                text = text.replace(text[num_list[1]],"月",1) # 只是替换一次
                text = cn2an.transform(text, "an2cn") # 数值转换
                text = text.replace("$","日",1) # 将最后一个$替换成日的读法

        # 规范化角度（°）
        pattern = re.compile(r"\d+\.?\d*°") # 数字°
        matchers = pattern.findall(text)
        if matchers:
            logging.info('角度')
            for matcher in matchers:
                text = text.replace("°","度")

        # 规范化"2楼的2名歌手的二重唱堪称完美"
        pattern = re.compile(r"[0-9]+[台|名|种|局|场]")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('特殊处理两字')
            for matcher in matchers:
                logging.info('matcher:',matcher)
                text = text.replace(matcher,"两"+ matcher[1]) # 这里后续需要优化为多个数字的

        # 规范化"*号#号"
        pattern = re.compile(r"[*#]+[号]")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('*号#号')
            for matcher in matchers:
                text = text.replace("*","星")
                text = text.replace("#","井")

        # 规范化 比分
        pattern = re.compile(r"\d+：\d+")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('比分')
            for matcher in matchers:
                text = cn2an.transform(text, "an2cn") # 数值转换
                text = text.replace("：","比")

        # 规范化温度（℃）
        pattern = re.compile(r".*℃.*")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('温度')
            for matcher in matchers:
                text = cn2an.transform(text, "an2cn") # 数值转换
                text = text.replace("-","到")

        # 规范化xx
        pattern = re.compile(r".*××.*")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('某某')
            for matcher in matchers:
                text = text.replace("××","某某")
       
        # 规范化算式
        pattern = re.compile(r".*=.*")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('算式')
            for matcher in matchers:
                text = text.replace("*","乘以")
                text = text.replace("×","乘以")
                text = text.replace("/","除以")
                text = text.replace(".","点")
                text = text.replace("-","减去")
                text = text.replace("+","加上")
                text = text.replace("<","小于")
                text = text.replace("=","等于")
                text = text.replace(">","大于")
                text = text.replace("÷","除以")

        # 规范化链接
        pattern = re.compile(r"(https?|ftp|file)://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]")
        matchers = pattern.findall(text)
        if matchers:
            logging.info('链接')
            for matcher in matchers:
                text = text.replace("://","冒号两斜杠")
                text = text.replace("/","斜杠")
                text = text.replace(".","点")

        # 规范化日期
        pattern = re.compile(r"\D+((([089]\d|(19|20)\d{2})年)?(\d{1,2}月(\d{1,2}[日号])?)?)")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], Date(date=matcher[0]).date2chntext(), 1)

        # 规范化金钱
        pattern = re.compile(r"\D+((\d+(\.\d+)?)[多余几]?" + CURRENCY_UNITS + r"(\d" + CURRENCY_UNITS + r"?)?)")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], Money(money=matcher[0]).money2chntext(), 1)

        # 规范化固话/手机号码
        # 手机
        # http://www.jihaoba.com/news/show/13680
        # 移动：139、138、137、136、135、134、159、158、157、150、151、152、188、187、182、183、184、178、198
        # 联通：130、131、132、156、155、186、185、176
        # 电信：133、153、189、180、181、177
        pattern = re.compile(r"\D((\+?86 ?)?1([38]\d|5[0-35-9]|7[678]|9[89])\d{8})\D")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], TelePhone(telephone=matcher[0]).telephone2chntext(), 1)
        # 固话
        pattern = re.compile(r"\D((0(10|2[1-3]|[3-9]\d{2})-?)?[1-9]\d{6,7})\D")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], TelePhone(telephone=matcher[0]).telephone2chntext(fixed=True), 1)

        # 规范化分数
        pattern = re.compile(r"(\d+/\d+)")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher, Fraction(fraction=matcher).fraction2chntext(), 1)

        # 规范化百分数
        text = text.replace('％', '%')
        pattern = re.compile(r"(\d+(\.\d+)?%)")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], Percentage(percentage=matcher[0]).percentage2chntext(), 1)

        # 规范化纯数+量词
        pattern = re.compile(r"(\d+(\.\d+)?)[多余几]?" + COM_QUANTIFIERS)
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], Cardinal(cardinal=matcher[0]).cardinal2chntext(), 1)

        # 规范化数字编号
        pattern = re.compile(r"(\d{4,32})")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher, Digit(digit=matcher).digit2chntext(), 1)

        # 规范化纯数
        pattern = re.compile(r"(\d+(\.\d+)?)")
        matchers = pattern.findall(text)
        if matchers:
            for matcher in matchers:
                text = text.replace(matcher[0], Cardinal(cardinal=matcher[0]).cardinal2chntext(), 1)

        ############################################
        self.norm_text = text
        self._particular()

        return self.norm_text.lstrip('^').rstrip('$')


def nsw_test_case(raw_text):
    print('I:' + raw_text)
    print('O:' + nsw_normalizer(raw_text).normalize())
    print('')


def position_swap(s:str):
    """
    将时间跟am pm倒换
    """
    if "pm" in s:
        pm_index= s.index("pm")
        s= s[pm_index:]+ s[:pm_index]
    if "PM" in s:
        PM_index= s.index("PM")
        s= s[PM_index:]+ s[:PM_index]
    if "am" in s:
        am_index= s.index("am")
        s= s[am_index:]+ s[:am_index]
    if "AM" in s:
        AM_index= s.index("AM")
        s= s[AM_index:]+ s[:AM_index]
    s = s.replace("$","",1)
    s = s.replace("^","",1)
    return s



def nsw_test():
    # nsw_test_case('固话：0595-23865596或23880880。')
    # nsw_test_case('固话：0595-23865596或23880880。')
    # nsw_test_case('手机：+86 19859213959或15659451527。')
    # nsw_test_case('分数：32477/76391。')
    # nsw_test_case('百分数：80.03%。')
    # nsw_test_case('编号：31520181154418。')
    # nsw_test_case('纯数：2983.07克或12345.60米。')
    # nsw_test_case('日期：1999年2月20日或09年3月15号。')
    # nsw_test_case('金钱：12块5，34.5元，20.1万')
    # nsw_test_case('特殊：O2O或B2C。')
    # nsw_test_case('3456万吨')
    # nsw_test_case('2938个')
    # nsw_test_case('938')
    # nsw_test_case('今天吃了115个小笼包231个馒头')
    # nsw_test_case('有62％的概率')
    # nsw_test_case('周××交通肇事一案')
    # nsw_test_case('周×交通肇事一案')
    # nsw_test_case('今天温度-20-30℃')
    # nsw_test_case('2楼的2名歌手的二重唱堪称完美')
    # nsw_test_case('7°')
    # nsw_test_case('锐角37°')
    # nsw_test_case('锐角360°')
    nsw_test_case('2017-10-27')
    nsw_test_case('2017/10/27')
    # nsw_test_case('二〇一七年十月')
    # nsw_test_case('研讨会定于12月23日上午9:35')
    # nsw_test_case('18:59:48')
    # nsw_test_case('8.30am')
    # nsw_test_case('5.30pm')
    # nsw_test_case('8am')
    # nsw_test_case('5pm ')
    # nsw_test_case('8AM')
    # nsw_test_case('5PM')
    # nsw_test_case('8.30AM')
    # nsw_test_case('5.30PM')
    # nsw_test_case('2局比分18：25、21：25')
    # nsw_test_case('2场开始时间18:25、21:25')
    # nsw_test_case('21:25')
    # nsw_test_case('0724-4356333')
    # nsw_test_case('182-3123-3213')
    # nsw_test_case('(+86)182-3123-3213')
    # nsw_test_case('12345678901')
    # nsw_test_case('１２３４５６７８９')
    # nsw_test_case('那么向1000B8000上写数据')
    # nsw_test_case('￥1000元')
    # nsw_test_case('小王的钱包有1116$')
    # nsw_test_case('作为魅蓝首款18：9全面屏手机')
    # nsw_test_case('人名币兑换优金币的比率为0.003125')
    # nsw_test_case('全美的房产税在1%~3%不等')
    nsw_test_case('生产日期2001-11-2') # 没有完成

if __name__ == '__main__':
    nsw_test()
