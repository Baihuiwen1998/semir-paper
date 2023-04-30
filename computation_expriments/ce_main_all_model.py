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
from models.lbbd_model.generate_cut import cal_sub_data
from models.lbbd_model.lbbd import LogicBasedBenders
from models.lbbd_model.master_model import MasterModel
from models.lbbd_model.sub_model import SubModel
from util.header import ParamsMark

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

def main():
    ori_dir = "D:/Codes/Python/semir-paper/"
    input_dir = ori_dir + "data/input/synthetic_data/"
    output_dir = ori_dir+"data/output/ALL_MODELS/"
    size_set = ["B"]
    # size_set = [ "uat_1_full", "da_type_2_online_solve"]
    # size_set = ["A", "B", "C", "D"]
    for size_name in size_set:
        out_list = list()
        out_list.append((1, 1, 1,  1, 1, 1, 1, 1, 1, 1, 1,  1, 1,  1,  1, 1))
        path = input_dir+size_name+"/"
        for file_name in os.listdir(path):
            ol = list()
            ol.append(file_name)

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

            for solution_mode in range(3):
                ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] = solution_mode
                if ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] == 0:
                    # 建立整体ALPHA模型并求解
                    full_model = FullModelAlpha(data)
                    full_model.construct_model()
                    result = full_model.gen_model_result()
                    if result:
                        # 结果  检查 + 分析
                        ma = ModelAnalysis(data, result)
                        is_correct, finished_rate_list = ma.analysis_result(True)
                        if is_correct:
                            ol.append(full_model.model.objVal)
                            ol.append(full_model.model.Runtime)
                            if full_model.model.Status != gurobipy.GRB.Status.OPTIMAL:
                                ol.append("%f" % full_model.model.MIPGap)
                            else:
                                ol.append("0.00%")
                            ol.append(full_model.model.ObjBound)
                            ol.extend(finished_rate_list)
                elif ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] == 1:
                    # 建立LBBD模型并求解
                    lbbd = LogicBasedBenders(data)
                    is_opt, result = lbbd.solve()
                    # 结果  检查 + 分析
                    ma = ModelAnalysis(data, result)
                    is_correct, finished_rate_list = ma.analysis_result(is_opt)
                    if is_correct:
                        ol.append(result[LBBDResultName.OBJ_VALUE])
                        ol.append(result[LBBDResultName.RUN_TIME])
                        ol.append((result[LBBDResultName.OBJ_VALUE]-result[LBBDResultName.LOWER_BOUND])/result[LBBDResultName.OBJ_VALUE])
                        ol.append(result[LBBDResultName.LOWER_BOUND])
                        ol.append(result[LBBDResultName.ITERATION])
                        ol.extend(finished_rate_list)
                else:
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
                    # 结果  检查 + 分析
                    ma = ModelAnalysis(data, result)
                    is_correct, finished_rate_list = ma.analysis_result(True)
                    if is_correct:
                        ol.append(master_model.model.objVal)
                        ol.append(master_model.model.Runtime)
                        if master_model.model.Status != gurobipy.GRB.Status.OPTIMAL:
                            ol.append("%f" % master_model.model.MIPGap)
                        else:
                            ol.append("0.00%")
                        ol.append(master_model.model.ObjBound)
                        ol.extend(finished_rate_list)

            out_list.append(ol)
            out_df = pd.DataFrame(out_list, columns=['name', 'item_num', 'order_num', 'supplier_num', 'machine_num', 'objVal_MIP',\
                                                 'Runtime', 'Gap', 'lowerBound',  'finished_item_num', 'finished_order_num', 'objVal_LBBD', 'Runtime', 'Gap', 'lowerBound', 'iterNum','finished_item_num',
                                                     'finished_order_num', 'objVal_B&CH', 'Runtime', 'Gap', 'lowerBound', 'finished_item_num',
                                                     'finished_order_num'])
            out_df.to_csv(output_dir + size_name + ".csv", encoding='utf-8-sig')


if __name__ == '__main__':
    main()
