import logging
import os

from analysis import ModelAnalysis
from models.full_model.full_model_beta import FullModelBeta
from models.lbbd_model.lbbd import LogicBasedBenders
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare import FeaturePrepare
from models.full_model.full_model_alpha import FullModelAlpha
from models.lbbd_model.master_model import MasterModel
from util.header import ParamsMark

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

def main():

    ori_dir = os.getcwd()
    input_dir = ori_dir+"/data/input/synthetic_data/"
    file_name = 'D/D_3_uat_1_full_梭织/'

    # 数据处理
    dp = DataPrepare(input_dir, file_name)
    data = dp.prepare()

    # 特征处理
    fp = FeaturePrepare(data, file_name)
    data = fp.prepare()

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
    elif ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] == 2:
        # 建立Branch—and-cut并求解
        master_model = MasterModel(data)
        master_model.construct()
        result = master_model.gen_model_result()
    # 结果  检查 + 分析
    ma = ModelAnalysis(data, result)
    analysis_result = ma.analysis_result()

    print('end')

if __name__ == '__main__':
    main()
