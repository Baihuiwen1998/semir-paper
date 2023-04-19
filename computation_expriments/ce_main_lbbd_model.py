import logging
import os

import gurobipy
import pandas as pd

from ce_analysis import ModelAnalysis
from models.full_model.full_model_alpha import FullModelAlpha
from models.lbbd_model.lbbd import LogicBasedBenders
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare import FeaturePrepare
from constant.config import *
from util.header import ParamsMark

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

def main():
    ori_dir = "D:/Codes/Python/semir-paper/"
    input_dir = ori_dir + "data/input/synthetic_data/"
    output_dir = ori_dir+"data/output/LBBD/"
    # size_set = [ "uat_1_full", "da_type_2_online_solve"]
    # size_set = ["A"]        # , "B", "C", "D"]
    size_set = ["supplimentary"]        # ["nIterOver1"]
    for size_name in size_set:
        out_list = list()
        out_list.append((1, 1, 1,  1, 1, 1, 1, 1, 1, 1, 1, 1,  1, 1,  1,  1, 1))
        path = input_dir+size_name+"/"
        for file_name in os.listdir(path):
        # for file_name in ['C_1_uat_1_full_梭织', 'C_4_uat_1_full_梭织']:
            ol = list()
            ol.append(file_name)

            # read data from file if needed
            # 数据处理
            dp = DataPrepare(path, file_name+"/")
            data = dp.prepare()

            # 特征处理
            fp = FeaturePrepare(data, file_name)
            data = fp.prepare()

            ol.append(len(data[SetName.ITEM_LIST]))
            ol.append(len(data[SetName.ORDER_LIST]))
            ol.append(len(data[SetName.SUPPLIER_LIST]))
            ol.append(len(data[SetName.MACHINE_LIST]))

            # 建立LBBD模型并求解
            lbbd = LogicBasedBenders(data)
            is_opt, result = lbbd.solve()
            # 结果  检查 + 分析
            ma = ModelAnalysis(data, result)
            is_correct, finished_rate_list = ma.analysis_result()
            if is_correct:
                ol.append(result[LBBDResultName.OBJ_VALUE])
                ol.append(result[LBBDResultName.RUN_TIME])
                ol.append(result[LBBDResultName.LOWER_BOUND])
                ol.append(result[LBBDResultName.ITERATION])
                ol.append("检查正确")
                ol.extend(finished_rate_list)
            else:
                ol.append(result[LBBDResultName.OBJ_VALUE])
                ol.append(result[LBBDResultName.RUN_TIME])
                ol.append(result[LBBDResultName.LOWER_BOUND])
                ol.append(result[LBBDResultName.ITERATION])
                ol.append("检查错误")

            out_list.append(ol)

            out_df = pd.DataFrame(out_list, columns=['name', 'item_num', 'order_num', 'supplier_num', 'machine_num', 'objVal',\
                                                     'Runtime', 'lowerBound', 'iteration', 'is_correct', 'finished_item_num', 'finished_order_num', 'pool_1', 'pool_2',\
                                                     'pool_3', 'pool_4', 'pool_5'])
            out_df.to_csv(output_dir+size_name+".csv", encoding='utf-8-sig')


if __name__ == '__main__':
    main()
