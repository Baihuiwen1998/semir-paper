import logging
import os

import gurobipy
import pandas as pd

from ce_analysis import ModelAnalysis
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare_random import FeaturePrepareRandom
from model_prepare.feature_prepare_semir import FeaturePrepareSemir
from models.full_model.full_model_alpha import FullModelAlpha
from config import *
from util.header import ParamsMark

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

def main():
    ori_dir = "/Users/emmabai/PycharmProjects/semir-paper/"
    input_dir = ori_dir + "data/input/random_data/"
    output_dir = ori_dir+"data/output/MIP/"
    size_set = ["Set_4"]
    # size_set = ["C", "D"]
    for size_name in size_set:
        out_list = list()
        out_list.append((1, 1, 1,  1, 1, 1, 1, 1, 1, 1, 1,  1, 1,  1,  1, 1))
        path = input_dir+size_name+"/"
        for file_name in os.listdir(path):
            ol = list()
            ol.append(size_name+file_name)

            # read data from file if needed
            # 数据处理
            dp = DataPrepare(path, file_name+"/")
            data = dp.prepare()

            ol.append(data[DataName.ITEM].shape[0])
            ol.append(data[DataName.ORDER].shape[0])

            # 特征处理
            if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
                fp = FeaturePrepareRandom(data, file_name)
            else:
                fp = FeaturePrepareSemir(data, file_name)
            data = fp.prepare()
            ol.append(len(data[SetName.SUPPLIER_LIST]))
            ol.append(len(data[SetName.MACHINE_LIST]))

            result = None
            # 建立整体模型并求解
            full_model = FullModelAlpha(data)
            full_model.construct_model()
            result = full_model.gen_model_result()
            if result:
                # 结果  检查 + 分析
                ma = ModelAnalysis(data, result)
                is_correct, finished_rate_list = ma.analysis_result()
                if is_correct:
                    ol.append(full_model.model.objVal)
                    ol.append(full_model.model.Runtime)
                    if full_model.model.Status != gurobipy.GRB.Status.OPTIMAL:
                        ol.append("%f" % full_model.model.MIPGap)
                    else:
                        ol.append("0.00%")
                    ol.append("检查正确")
                    ol.extend(finished_rate_list)
                else:
                    ol.append(full_model.model.objVal)
                    ol.append(full_model.model.Runtime)
                    if full_model.model.Status != gurobipy.GRB.Status.OPTIMAL:
                        ol.append("%f" % full_model.model.MIPGap)
                    else:
                        ol.append("0.00%")
                    ol.append("检查错误")

            out_list.append(ol)

            out_df = pd.DataFrame(out_list, columns=['name', 'item_num', 'order_num', 'supplier_num', 'machine_num', 'objVal',\
                                                 'Runtime', 'MIPGap', 'is_correct', 'finished_item_num', 'finished_order_num', 'pool_1', 'pool_2',\
                                                 'pool_3', 'pool_4', 'pool_5'])
            out_df.to_csv(output_dir+size_name+".csv", encoding='utf-8-sig')

if __name__ == '__main__':
    main()
