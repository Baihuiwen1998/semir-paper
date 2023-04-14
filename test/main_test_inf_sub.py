import logging
import os

import setuptools.glob

from analysis import ModelAnalysis
from constant.config import *
from lbbd import LogicBasedBenders
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare import FeaturePrepare
from models.full_model import FullModel
from models.lbbd_model.sub_model import SubModel
from test_relaxed_sub_model import TestRelaxedSubModel
from test_master_model import TestMasterModel

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)


def cal_sub_data(data, supplier, item_list):
    sub_data = dict()
    sub_data[LBBDSubDataName.SUPPLIER] = supplier
    sub_data[LBBDSubDataName.ITEM_LIST] = item_list
    sub_data[LBBDSubDataName.ORDER_LIST] = list()
    for item in item_list:
        sub_data[LBBDSubDataName.ORDER_LIST].extend(data[SetName.ORDER_BY_ITEM_DICT][item])
    sub_data[LBBDSubDataName.MACHINE_LIST] = data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
    return sub_data


def main():
    ori_dir = "D:/Codes/Python/semir-paper/"
    input_dir = ori_dir+"data/input/desensitized_data/"
    output_dir = ori_dir+"data/output/"
    file = 'uat_1_full/' + '针织/'

    input_file_dir = os.path.join(input_dir, file)
    output_file_dir = os.path.join(output_dir, file)
    for basic_file in [input_file_dir, output_file_dir]:
        os.makedirs(basic_file, exist_ok=True)

    # read data from file if needed

    # 数据处理
    dp = DataPrepare(input_dir, file)
    data = dp.prepare()

    # 特征处理
    fp = FeaturePrepare(data, file)
    data = fp.prepare()
    supplier = 3001192
    item_list = ['C44725894', 'C44729124', 'C44741027', 'C44983441', 'C45460451', 'C45726082', 'C45966874', 'C45969314', 'C45975657', 'C47031809', 'C47031817', 'C47220376', 'C47227773', 'C47610837', 'C49207597', 'C50160231']
    sub_data = cal_sub_data(data, supplier, item_list)
    sub_model = TestRelaxedSubModel(data, sub_data)
    sub_model.construct()
    is_feasible = sub_model.solve(mode=2)

    time_set = set()
    for item in item_list:
        print("--------------------item:" + item +":" + str(data[ParaName.ITEM_QUANTITY_DICT][item]) + "---------------------------")

        if data[ParaName.ITEM_MAX_OCCUPY_DICT][item] < 0:
            item_max_occupy = float('inf')
        else:
            item_max_occupy = data[ParaName.ITEM_MAX_OCCUPY_DICT][item]
        print("item_max_occupy="+str(item_max_occupy))

        for order in data[SetName.ORDER_BY_ITEM_DICT][item]:
            print("--------------------order:" + str(order) +":" + str(data[ParaName.ORDER_QUANTITY_DICT][order]) + "---------------------------")
            print("production_date:", end='')
            for date in data[SetName.ORDER_TIME_DICT][order]:
                print(date, end=',')
            print()
            time_set = time_set.union(set(data[SetName.ORDER_TIME_DICT][order]))

        for machine in set.intersection(set(data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]), set(data[SetName.MACHINE_BY_ITEM_DICT][item])):
            print("--------------------machine:" + str(machine) +"---------------------------")
            for month in data[SetName.ITEM_MONTH_DICT][item]:
                print(month +":" + str(data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0)))
    print("--------------------supplier_daily_max_production---------------------------")
    for date in sorted(time_set):
        print("supplier_daily_max:" + date + ":" + str(
            data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier].get(date, float('inf'))))
    print('end')

    # for channel in data[DAOptSetName.ITEM_BY_CHANNEL_DICT]:
    #     if 'C45496371' in data[DAOptSetName.ITEM_BY_CHANNEL_DICT][channel]:
    #         print(channel)
    # for channel in data[DAOptSetName.MACHINE_BY_CHANNEL_DICT]:
    #     if 6 in data[DAOptSetName.MACHINE_BY_CHANNEL_DICT][channel]:
    #         print(channel)

    master_model = TestMasterModel(data, supplier, item_list)
    master_model.construct()
    master_model.solve()

if __name__ == '__main__':
    main()
