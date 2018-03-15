"""
Implements the TestResult class which cases use to record their results.
"""

import time


class TestResult():
    def __init__(self, case_num):
        self.__case_num = case_num
        self.__valid = None
        self.__raw = {}

    @property
    def case_num(self):
        return self.__case_num

    def set_valid(self, res):
        self.__valid = res

    def set_raw_data(self, raw):
        self.__raw = raw

    def add_raw_data(self, key, value):
        self.__raw[key] = value

    def serializable(self):
        return {
            "case": self.__case_num,
            "valid": self.__valid,
            "raw": self.__raw
        }


class TestResultWrapper():
    def __init__(self, interface, harness, generator):
        self.__start_time = None
        self.__end_time = None
        self.__interface = interface
        self.__harness = harness
        self.__generator = generator
        self.__results = {}
        self.set_start_now()

    def add_test_result(self, test_result):
        if test_result.case_num not in self.__results:
            self.__results[test_result.case_num] = []
        self.__results[test_result.case_num].append(test_result)

    def set_start_now(self):
        self.__start_time = time.time()

    def set_end_now(self):
        self.__end_time = time.time()

    def serializable(self):
        serializable_results = {}
        for k, trs in self.__results.iteritems():
            serializable_results[k] = map(lambda tr: tr.serializable(), trs)
        return {
            "interface": self.__interface.status()[1],
            "harness": {
                "name": self.__harness.name
            },
            "generator": {
                "name": self.__generator.name,
                "includes_phy": self.__generator.includes_phy,
                "includes_mac": self.__generator.includes_mac
            },
            "start_time": self.__start_time,
            "end_time": self.__end_time,
            "results": serializable_results
        }
