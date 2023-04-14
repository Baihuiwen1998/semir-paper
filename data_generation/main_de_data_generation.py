# @author: baihuiwen
# @email: bhw21@mails.tsinghua.edu.cn
# @date: 2023/3/17

"""
main文件
用于获取semir原始数据，进行特征提取，生成新的实验数据集

1. 读取数据
2. 获取特征
3. 生成新的脱敏数据集
"""
import os
import logging

from constant.config import *
from data_generation.raw_data_prepare.load_raw_data import LoadRawData
from data_generation.raw_data_prepare.transform_to_desensitized_data import TransformData
from util.raw_header import FileName

# 定义logger的格式
formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

# main函数
def main():
    ori_dir = "D:/Codes/Python/semir-paper/"
    input_dir = ori_dir+"data/input/raw_data/"
    output_desensitized_dir = ori_dir+"data/input/desensitized_data/"
    # output_synthetic_dir = ori_dir+"data/input/synthetic_data/"
    file = 'da_type_2_online_solve/'

    # 原数据读取
    lrd = LoadRawData(input_dir, file)
    raw_data_by_fabric = lrd.load()
    logger.info("数据读取完毕")

    # 将原始数据转化为脱敏的Paper可用数据
    td = TransformData(raw_data_by_fabric)
    transformed_data_by_fabric = td.desensitize()
    for fabric in transformed_data_by_fabric:
        desensitized_file_dir = output_desensitized_dir+file+fabric+'/'
        os.makedirs(desensitized_file_dir)
        transformed_data_by_fabric[fabric][DataName.ITEM].to_csv(
            os.path.join(desensitized_file_dir, FileName.ITEM_FILE_NAME + '.csv'), index=False)
        transformed_data_by_fabric[fabric][DataName.MACHINE].to_csv(
            os.path.join(desensitized_file_dir, FileName.MACHINE_FILE_NAME + '.csv'), index=False)
        transformed_data_by_fabric[fabric][DataName.SUPPLIER].to_csv(
            os.path.join(desensitized_file_dir, FileName.SUPPLIER_FILE_NAME + '.csv'), index=False)
        transformed_data_by_fabric[fabric][DataName.ORDER].to_csv(
            os.path.join(desensitized_file_dir, FileName.ORDER_FILE_NAME + '.csv'), index=False)
        transformed_data_by_fabric[fabric][DataName.CALENDAR].to_csv(
            os.path.join(desensitized_file_dir, FileName.CALENDAR_FILE_NAME + '.csv'), index=False)
    logger.info("数据脱敏成功")
    # 特征获取

    # 生成新的数据集


if __name__ == '__main__':
    main()


