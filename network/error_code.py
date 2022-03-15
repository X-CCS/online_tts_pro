# -*- coding: utf-8 -*-
from enum import Enum, unique
@unique
class ErrorCode(Enum):
    OK = {200: "成功"}
    FAIL = {10000: "失败"}
    PARAM_IS_NULL = {10001: "请求参数为空"}
    PARAM_ILLEGAL = {10002: "请求参数非法"}
    JSON_PARSE_FAIL = {10003: "JSON转换失败"}
    UNKNOWN_ERROR = {10004: "未知异常"}

    def get_code(self):
        return list(self.value.keys())[0]

    def get_msg(self):
        return list(self.value.values())[0]

