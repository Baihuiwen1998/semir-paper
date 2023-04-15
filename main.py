import logging
import os

from analysis import ModelAnalysis
from lbbd import LogicBasedBenders
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare import FeaturePrepare
from models.full_model import FullModel

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

def main():
    ori_dir = "D:/Codes/Python/semir-paper/"
    input_dir = ori_dir+"data/input/desensitized_data/"
    file_name = 'uat_1_full/针织/'
    solution_mode = 1   # {0: 整体模型, 1: LBBD模型}
    # 数据处理
    dp = DataPrepare(input_dir, file_name)
    data = dp.prepare()

    # 特征处理
    fp = FeaturePrepare(data, file_name, solution_mode)
    data = fp.prepare()

    result = None
    if solution_mode == 0:
        # 建立整体模型并求解
        full_model = FullModel(data)
        full_model.construct_model()
        result = full_model.gen_model_result()
    elif solution_mode == 1:
        # 建立LBBD模型并求解
        lbbd = LogicBasedBenders(data)
        is_opt, result = lbbd.solve()
    # 结果  检查 + 分析
    ma = ModelAnalysis(data, result, solution_mode)
    analysis_result = ma.analysis_result()

    print('end')

if __name__ == '__main__':
    main()
