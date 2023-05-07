import logging
import os

from config import *
from model_prepare.data_prepare import DataPrepare
from model_prepare.feature_prepare_random import FeaturePrepareRandom
from model_prepare.feature_prepare_semir import FeaturePrepareSemir
from test_master_model import TestMasterModel
from test_relaxed_sub_model import TestRelaxedSubModel
from util.header import ParamsMark

# from test_master_model import TestMasterModel

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
    ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] = 1
    ori_dir = "/Users/emmabai/PycharmProjects/semir-paper/"
    input_dir = ori_dir+"data/input/random_data/"
    output_dir = ori_dir+"data/output/"
    file = 'Set_7/' + '1/'

    input_file_dir = os.path.join(input_dir, file)

    for basic_file in [input_file_dir]:
        os.makedirs(basic_file, exist_ok=True)

    # read data from file if needed

    # 数据处理
    dp = DataPrepare(input_dir, file)
    data = dp.prepare()

    # 特征处理
    fp = FeaturePrepareRandom(data, file)
    data = fp.prepare()
    supplier = 5
    item_list = [53, 80, 91]# , 105]
    sub_data = cal_sub_data(data, supplier, item_list)
    sub_model = TestRelaxedSubModel(data, sub_data)
    sub_model.construct()
    is_feasible = sub_model.solve(mode=2)

    time_set = set()
    for item in item_list:
        print("--------------------item:" + str(item) +":" + str(data[ParaName.ITEM_QUANTITY_DICT][item]) + "---------------------------")

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
                print(str(month) + ":" + str(data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0)))
    print("--------------------supplier_daily_max_production---------------------------")
    for date in sorted(time_set):
        print("supplier_daily_max:" + str(date) + ":" + str(
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
    master_model.solve_lbbd()

if __name__ == '__main__':
    main()
