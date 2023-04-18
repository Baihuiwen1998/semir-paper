# @author: baihuiwen
# @email: bhw21@mails.tsinghua.edu.cn
# @date: 2023/4/3

import os
import logging

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from constant.config import RawDataName
from data_generation.raw_data_prepare.load_raw_data import LoadRawData
from model_prepare.data_prepare import DataPrepare
from util.raw_header import *


# 定义logger的格式
formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)


class ItemAnalysis:
    def __init__(self, data):
        self.data = data

    def cal_item_features(self):
        """
        款式信息
        """
        en_name_of_fabric = {
            '梭织': 'Woven',
            '毛织': 'Woolen',
        'at_针织': 'Knit',
        '牛仔': 'Denim'
        }
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.rcParams['axes.unicode_minus'] = False
        # item_df = self.data[DAOptRawDataName.ITEM]
        demand_df = self.data[RawDataName.DEMAND]
        print(self.data[RawDataName.FABRIC])


        item_demand_num = demand_df[DemandHeader.ITEM_ID].value_counts()
        print("款式数量：" + str(len(item_demand_num.index)))
        print("订单数量：" + str(demand_df.shape[0]))
        item_demand_num = {'item_id': item_demand_num.index, 'demand_num': item_demand_num.values}

        item_demand_num_df = pd.DataFrame(item_demand_num)
        print("平均每款订单数："+str(item_demand_num_df['demand_num'].mean()))
        # item_demand_num_df['demand_num'].plot.pie(autopct='%3.1f%%')

        demand_num = item_demand_num_df['demand_num'].value_counts()
        colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(demand_num.index)))
        plt.pie(demand_num.values, labels=demand_num.index, autopct='%3.1f%%', colors=colors)
        plt.title("Number of orders per item, fabric:" + en_name_of_fabric[self.data[RawDataName.FABRIC]], fontsize=16)
        plt.show()



# main函数
def main():
    ori_dir = "//"
    input_dir = ori_dir+"data/input/raw_data/"
    file = 'da_type_2_online_solve/'

    # 原数据读取
    lrd = LoadRawData(input_dir, file)
    raw_data_by_fabric = lrd.load()
    logger.info("数据读取完毕")

    for fabric in raw_data_by_fabric:
        ia = ItemAnalysis(raw_data_by_fabric[fabric])
        ia.cal_order_features()


if __name__ == '__main__':
    main()


