# @author: baihuiwen
# @email: bhw21@mails.tsinghua.edu.cn
# @date: 2023/4/4

"""
main文件
用于获取semir原始数据，进行特征提取，生成新的实验数据集

1. 获取脱敏数据
2. 根据要求筛选
"""
import os
import logging
import random
import pandas as pd
from constant.config import *
from data_generation.raw_data_prepare.load_raw_data import LoadRawData
from data_generation.raw_data_prepare.transform_to_desensitized_data import TransformData
from model_prepare.data_prepare import DataPrepare
from util.header import *
from util.raw_header import FileName, FabricCategoryMark

# 定义logger的格式
formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

ITEM_NUM_DICT = {"A": [8, 10], "B": [30, 40], "C": [80, 100], "D": [200, 300]}
ORDER_NUM_DICT = {"A": 30, "B": 150, "C": 300, "D": 900}
SUPPLIER_NUM_DICT = {"A": [3, 4], "B": [10, 20], "C": [10, 20], "D": [20, 30]}


def gen_instances(data, set_size):
    instance_size_list = list()
    item_num = random.choice(ITEM_NUM_DICT[set_size])
    order_num = 100000
    while order_num > ORDER_NUM_DICT[set_size]:
        item_df = data[DataName.ITEM]
        if item_df.shape[0] < min(ITEM_NUM_DICT[set_size]):
            return False, None
        else:
            while item_df.shape[0] < item_num:
                item_num = random.choice(ITEM_NUM_DICT[set_size])
        sampled_item_df = item_df.sample(n=item_num)
        item_id_set = set(sampled_item_df[ItemHeader.ITEM_ID].to_list())

        order_df = data[DataName.ORDER]
        filtered_order_df = order_df[order_df[OrderHeader.ITEM_ID].isin(item_id_set)]
        order_num = filtered_order_df.shape[0]
    instance_size_list.append(item_num)
    instance_size_list.append(order_num)

    # 根据款式筛选具有生产能力的supplier
    item_df = data[DataName.ITEM]
    machine_df = data[DataName.MACHINE]
    item_machine_df = pd.merge(item_df, machine_df, on=[ItemHeader.CHANNEL, ItemHeader.AGE_GROUP, ItemHeader.FABRIC_CATEGORY])
    eligible_supplier_set = set(item_machine_df[MachineHeader.SUPPLIER_ID].to_list())

    supplier_num = random.choice(SUPPLIER_NUM_DICT[set_size])
    if len(eligible_supplier_set) < supplier_num:
        return False, None
    sampled_supplier_set = set(random.sample(list(eligible_supplier_set), supplier_num))
    supplier_df = data[DataName.SUPPLIER]
    filtered_supplier_df = supplier_df[supplier_df[SupplierHeader.SUPPLIER_ID].isin(sampled_supplier_set)]
    machine_df = data[DataName.MACHINE]
    filtered_machine_df = machine_df[machine_df[MachineHeader.SUPPLIER_ID].isin(sampled_supplier_set)]

    instance_size_list.append(supplier_num)
    instance_size_list.append(len(set(filtered_machine_df[MachineHeader.MACHINE_ID].to_list())))

    filtered_data = {
        DataName.ITEM: sampled_item_df,
        DataName.ORDER: filtered_order_df,
        DataName.SUPPLIER: filtered_supplier_df,
        DataName.MACHINE: filtered_machine_df,
        DataName.CALENDAR: data[DataName.CALENDAR],
        'instance_size': instance_size_list
    }
    return True, filtered_data

# main函数
def main():
    ori_dir = "D:/Codes/Python/semir-paper/"
    input_dir = ori_dir + "data/input/desensitized_data/"
    output_desensitized_dir = ori_dir + "data/input/synthetic_data/"
    for set_size in ["A", "B", "C", "D"]:
        item_num_sum = 0
        order_num_sum = 0
        supplier_num_sum = 0
        machine_num_sum = 0
        item_num_set = set()
        order_num_set = set()
        supplier_num_set = set()
        machine_num_set = set()
        instance_num = 1
        for raw_data_name in ['uat_1_full', 'da_type_2_online_solve']:
            for fabric in FabricCategoryMark.ALL_FABRIC_CATEGORY_MARK:
                file = raw_data_name +'/' + fabric+'/'
                # 数据处理
                dp = DataPrepare(input_dir, file)
                data = dp.prepare()

                for repeat_num in range(5):
                    is_created, filtered_data = gen_instances(data, set_size)
                    if is_created:
                        synthetic_file_dir = output_desensitized_dir + set_size + "/" + set_size + "_" + str(
                            instance_num) + "_" + raw_data_name + "_" + \
                                             fabric + "/"
                        os.makedirs(synthetic_file_dir, exist_ok=True)
                        filtered_data[DataName.ITEM].to_csv(
                            os.path.join(synthetic_file_dir, FileName.ITEM_FILE_NAME + '.csv'), index=False)
                        filtered_data[DataName.MACHINE].to_csv(
                            os.path.join(synthetic_file_dir, FileName.MACHINE_FILE_NAME + '.csv'), index=False)
                        filtered_data[DataName.SUPPLIER].to_csv(
                            os.path.join(synthetic_file_dir, FileName.SUPPLIER_FILE_NAME + '.csv'), index=False)
                        filtered_data[DataName.ORDER].to_csv(
                            os.path.join(synthetic_file_dir, FileName.ORDER_FILE_NAME + '.csv'), index=False)
                        filtered_data[DataName.CALENDAR].to_csv(
                            os.path.join(synthetic_file_dir, FileName.CALENDAR_FILE_NAME + '.csv'), index=False)

                        item_num_sum += filtered_data['instance_size'][0]
                        order_num_sum += filtered_data['instance_size'][1]
                        supplier_num_sum += filtered_data['instance_size'][2]
                        machine_num_sum += filtered_data['instance_size'][3]
                        item_num_set.add(filtered_data['instance_size'][0])
                        order_num_set.add(filtered_data['instance_size'][1])
                        supplier_num_set.add(filtered_data['instance_size'][2])
                        machine_num_set.add(filtered_data['instance_size'][3])

                        instance_num += 1
        instance_num -=1
        print(item_num_sum/instance_num)
        print(order_num_sum / instance_num)
        print(supplier_num_sum / instance_num)
        print(machine_num_sum / instance_num)
        print(item_num_set)
        print(order_num_set)
        print(supplier_num_set)
        print(machine_num_set)



if __name__ == '__main__':
    main()

