import logging
import os

import gurobipy
import pandas as pd

from ce_analysis import ModelAnalysis
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare_random import FeaturePrepareRandom
from model_prepare.feature_prepare_semir import FeaturePrepareSemir
from config import *
from models.full_model.full_model_alpha import FullModelAlpha
from models.lbbd_model.master_model import MasterModel
from models.lbbd_model.sub_model import SubModel
from models.lbbd_model.generate_cut import cal_sub_data
from util.header import ParamsMark

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

def main():
    ori_dir = "/Users/emmabai/PycharmProjects/semir-paper/"
    input_dir = ori_dir + "data/input/random_data/"
    output_dir = ori_dir+"data/output/B&CH/"
    # size_set = [ "uat_1_full", "da_type_2_online_solve"]
    # size_set = ["A", "B", "C", "D"]
    size_set = ["Set_6", "Set_7"]
    for size_name in size_set:
        out_list = list()
        out_list.append((1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  1, 1,  1,  1, 1))
        path = input_dir+size_name+"/"
        for file_name in os.listdir(path):
            ol = list()
            ol.append(file_name)

            # read data from file if needed
            # 数据处理
            dp = DataPrepare(path, file_name+"/")
            data = dp.prepare()

            # 特征处理
            if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
                fp = FeaturePrepareRandom(data, file_name)
            else:
                fp = FeaturePrepareSemir(data, file_name)
            data = fp.prepare()

            ol.append(len(data[SetName.ITEM_LIST]))
            ol.append(len(data[SetName.ORDER_LIST]))
            ol.append(len(data[SetName.SUPPLIER_LIST]))
            ol.append(len(data[SetName.MACHINE_LIST]))

            # 建立主问题模型并求解
            result = dict()
            master_model = MasterModel(data)
            master_model.construct()
            master_data = master_model.gen_model_result()
            result[LBBDResultName.MASTER_RESULT] = master_data
            result[LBBDResultName.SUB_RESULT] = dict()
            for supplier in master_data[ResultName.ITEM_SUPPLIER]:
                sub_data = cal_sub_data(data, supplier, master_data[ResultName.ITEM_SUPPLIER][supplier])
                sub_model = SubModel(data, sub_data)
                sub_model.construct()
                sub_result = sub_model.solve(mode=2)
                result[LBBDResultName.SUB_RESULT][supplier] = sub_result

            result[LBBDResultName.RUN_TIME] = master_model.model.Runtime
            result[LBBDResultName.OBJ_VALUE] = master_model.model.objVal
            result["Gap"] = "%f" % master_model.model.MIPGap

            # 结果  检查 + 分析
            ma = ModelAnalysis(data, result)
            is_correct, finished_rate_list = ma.analysis_result(True)
            if is_correct:
                ol.append(result[LBBDResultName.OBJ_VALUE])
                ol.append(result[LBBDResultName.RUN_TIME])
                ol.append(result["Gap"])
                # ol.append(result[LBBDResultName.ITERATION])
                ol.append("检查正确")
                ol.extend(finished_rate_list)
            else:
                ol.append(result[LBBDResultName.OBJ_VALUE])
                ol.append(result[LBBDResultName.RUN_TIME])
                ol.append(result[LBBDResultName.LOWER_BOUND])
                # ol.append(result[LBBDResultName.ITERATION])
                ol.append("检查错误")

            out_list.append(ol)

            out_df = pd.DataFrame(out_list, columns=['name', 'item_num', 'order_num', 'supplier_num', 'machine_num', 'objVal',\
                                                     'Runtime', 'Gap', 'is_correct', 'finished_item_num', 'finished_order_num', 'pool_1', 'pool_2',\
                                                     'pool_3', 'pool_4', 'pool_5'])
            out_df.to_csv(output_dir+size_name+"_greedy_cut.csv", encoding='utf-8-sig')

if __name__ == '__main__':
    main()
