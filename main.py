import logging
import os

from analysis import ModelAnalysis
from config import LBBDResultName, ResultName
from model_prepare.feature_prepare_random import FeaturePrepareRandom
from models.full_model.full_model_beta import FullModelBeta
from models.lbbd_model.lbbd import LogicBasedBenders
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare_semir import FeaturePrepareSemir
from models.full_model.full_model_alpha import FullModelAlpha
from models.lbbd_model.master_model import MasterModel
from models.lbbd_model.sub_model import SubModel
from util.header import ParamsMark
from models.lbbd_model.generate_cut import cal_sub_data
formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

def main():

    ori_dir = os.getcwd()
    input_dir = ori_dir+"/data/input/synthetic_data/"
    file_name = 'B/B_4_uat_1_full_梭织/'

    # 数据处理
    dp = DataPrepare(input_dir, file_name)
    data = dp.prepare()

    # 特征处理
    if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
        fp = FeaturePrepareRandom(data, file_name)
    else:
        fp = FeaturePrepareSemir(data, file_name)
    data = fp.prepare()
    is_opt = True
    result = None
    if ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] == 0:
        # 建立整体模型并求解
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.MILP_MODEL] == 0:              # alpha
            full_model = FullModelAlpha(data)
        else:
            full_model = FullModelBeta(data)
        full_model.construct_model()
        result = full_model.gen_model_result()
    elif ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] == 1:
        # 建立LBBD模型并求解
        lbbd = LogicBasedBenders(data)
        is_opt, result = lbbd.solve()
    else:
        result = dict()
        # 建立Branch—and-cut并求解
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
    analysis_result = ma.analysis_result(is_opt)

    print('end')

if __name__ == '__main__':
    main()
