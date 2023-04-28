# -*- coding: utf-8 -*-
# @author: baihuiwen
# @email: bhw21@mails.tsinghua.edu.cn
# @date: 2023/3/20


import logging
import os
import pandas as pd
from config import *
from util.header import ParamsMark
from util.raw_header import FileName
from util.util import str2date

logger = logging.getLogger(__name__)


class DataPrepare:
    def __init__(self, input_dir, file):
        self.data = dict()
        self.input_dir = input_dir
        self.file = file

    def reduce_data_size(self, reduce_percent):
        """
        测试 期间有些算例太大了，删减一些需求

        """
        order_df = self.data[DataName.ORDER]
        row_num = order_df.shape[0]
        order_df = order_df.head(int(row_num*reduce_percent))
        # order_df = order_df.sample(frac=reduce_percent, replace=True, random_state=1)
        self.data[DataName.ORDER] = order_df
        return self.data

    def prepare(self):
        """
        主函数
        """
        self.read_data()
        logger.info('数据读入完成')
        return self.data

    def read_data(self):
        """
        数据的读入
        """
        # 款式表
        item_df = pd.read_csv(os.path.join(self.input_dir + self.file, FileName.ITEM_FILE_NAME + '.csv'))

        # 订单表
        order_df = pd.read_csv(os.path.join(self.input_dir + self.file, FileName.ORDER_FILE_NAME + '.csv'))
        if not ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
            order_df['arrival_date'] = order_df['arrival_date'].apply(lambda x: str2date(x))
            order_df['due_date'] = order_df['due_date'].apply(lambda x: str2date(x))

        # 供应商表
        supplier_df = pd.read_csv(os.path.join(self.input_dir + self.file, FileName.SUPPLIER_FILE_NAME + '.csv'))

        # 机器表
        machine_df = pd.read_csv(os.path.join(self.input_dir + self.file, FileName.MACHINE_FILE_NAME + '.csv'))

        # 时间表
        calendar_df = pd.read_csv(os.path.join(self.input_dir + self.file, FileName.CALENDAR_FILE_NAME + '.csv'))
        if not ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
            calendar_df['work_date'] = calendar_df['work_date'].apply(lambda x: str2date(x))
        self.data = {DataName.ITEM: item_df,
                     DataName.ORDER: order_df,
                     DataName.SUPPLIER: supplier_df,
                     DataName.MACHINE: machine_df,
                     DataName.CALENDAR: calendar_df}
        return self.data
