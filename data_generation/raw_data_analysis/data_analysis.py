
import logging
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from model_prepare.data_prepare import DataPrepare

from constant.config import *
from model_prepare.feature_prepare import FeaturePrepare
from util.header import *

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)


en_name_of_fabric = {
            '梭织': 'Woven',
            '毛织': 'Woolen',
            'at_针织': 'Knit',
            '牛仔': 'Denim'
        }


class DataAnalysis:
    def __init__(self, data, fabric):
        self.fabric = fabric
        self.data = data
        self.raw_data_features = dict()

    def cal_features(self, new_list):
        new_list = self.cal_machine_supplier_features(new_list)
        new_list = self.cal_item_order_features(new_list)
        return new_list

    def cal_machine_supplier_features(self, new_list):
        item_supplier_num_list = list()
        item_machine_num_list = list()
        for item in self.data[SetName.ITEM_LIST]:
            item_machine_num_list.append((item, len(self.data[SetName.MACHINE_BY_ITEM_DICT][item])))
            item_supplier_num_list.append((item, len(self.data[SetName.SUPPLIER_BY_ITEM_DICT][item])))

        item_machine_num_df = pd.DataFrame(item_machine_num_list, columns=['item_id', 'machine_num'])
        item_supplier_num_df = pd.DataFrame(item_supplier_num_list, columns=['item_id', 'supplier_num'])


        supplier_item_num_list = list()
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            supplier_item_num_list.append((supplier, len(self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier])))
        supplier_item_num_df = pd.DataFrame(supplier_item_num_list, columns=['supplier_id', 'item_num'])

        supplier_machine_num_list = list()
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            supplier_machine_num_list.append((supplier, len(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier])))
        supplier_machine_num_df = pd.DataFrame(supplier_machine_num_list, columns=['supplier_id', 'machine_num'])

        new_list.append(len(self.data[SetName.ITEM_LIST]))
        new_list.append(len(self.data[SetName.ORDER_LIST]))
        new_list.append(len(self.data[SetName.SUPPLIER_LIST]))
        new_list.append(len(self.data[SetName.MACHINE_LIST]))
        new_list.append(item_machine_num_df['machine_num'].mean())
        new_list.append(item_supplier_num_df['supplier_num'].mean())
        new_list.append(supplier_item_num_df['item_num'].mean())
        new_list.append(supplier_machine_num_df['machine_num'].mean())

        # print("供应商数量："+str(len(self.data[DAOptSetName.SUPPLIER_LIST])))
        # print("产线数量：" + str(len(self.data[DAOptSetName.MACHINE_LIST])))
        # print("单位款式平均可生产产线数量：" + str(item_machine_num_df['machine_num'].mean()))
        # print("单位款式平均可生产供应商数量：" + str(item_supplier_num_df['supplier_num'].mean()))
        # print("单位供应商平均可生产款式数量：" + str(supplier_item_num_df['item_num'].mean()))
        # print("单位供应商内产线数量：" + str(supplier_machine_num_df['machine_num'].mean()))
        return new_list


    def cal_item_order_features(self, new_list):
        item_order_num_list = list()
        item_quantity_list = list()
        order_quantity_list = list()
        order_production_time_length_list = list()

        for item in self.data[SetName.ITEM_LIST]:
            item_order_num_list.append((item, len(self.data[SetName.ORDER_BY_ITEM_DICT][item])))
            item_quantity_list.append((item, self.data[ParaName.ITEM_QUANTITY_DICT][item]))
        for order in self.data[SetName.ORDER_LIST]:
            order_quantity_list.append((order, self.data[ParaName.ORDER_QUANTITY_DICT][order]))
            order_production_time_length_list.append((order, len(self.data[SetName.ORDER_TIME_DICT][order])))

        item_order_num_df = pd.DataFrame(item_order_num_list, columns=['item_id', 'item_order_num'])
        item_quantity_df = pd.DataFrame(item_quantity_list, columns=['item_id', 'item_quantity'])
        order_quantity_df = pd.DataFrame(order_quantity_list, columns=['item_id', 'order_quantity'])
        order_production_time_length_df = pd.DataFrame(order_production_time_length_list, columns=['order_id', 'order_production_time_length'])

        new_list.append(item_order_num_df['item_order_num'].mean())
        new_list.append(item_quantity_df['item_quantity'].mean())
        new_list.append(order_quantity_df['order_quantity'].mean())
        new_list.append(order_production_time_length_df['order_production_time_length'].mean())
        # new_list.append(order_arrival_time_df['order_arrival_time'].mean())
        # new_list.append(order_due_time_df['order_due_time'].mean())
        return new_list

    def cal_figures(self, suanli_name, fabric, out_dir):
        # item_supplier_num_list = list()
        # item_machine_num_list = list()
        # for item in self.data[DAOptSetName.ITEM_LIST]:
        #     item_machine_num_list.append((item, len(self.data[DAOptSetName.MACHINE_BY_ITEM_DICT][item])))
        #     item_supplier_num_list.append((item, len(self.data[DAOptSetName.SUPPLIER_BY_ITEM_DICT][item])))
        #
        # item_machine_num_df = pd.DataFrame(item_machine_num_list, columns=['item_id', 'machine_num'])
        # item_supplier_num_df = pd.DataFrame(item_supplier_num_list, columns=['item_id', 'supplier_num'])
        #
        # supplier_item_num_list = list()
        # for supplier in self.data[DAOptSetName.SUPPLIER_LIST]:
        #     supplier_item_num_list.append((supplier, len(self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT][supplier])))
        # supplier_item_num_df = pd.DataFrame(supplier_item_num_list, columns=['supplier_id', 'item_num'])
        #
        # supplier_machine_num_list = list()
        # for supplier in self.data[DAOptSetName.SUPPLIER_LIST]:
        #     supplier_machine_num_list.append((supplier, len(self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier])))
        # supplier_machine_num_df = pd.DataFrame(supplier_machine_num_list, columns=['supplier_id', 'machine_num'])
        #
        #
        # item_machine_num = item_machine_num_df['machine_num'].value_counts()
        # colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(item_machine_num.index)))
        # plt.pie(item_machine_num.values, labels=item_machine_num.index, autopct='%3.1f%%', colors=colors)
        # plt.title("Number of eligible machines per item, fabric:" + en_name_of_fabric[self.fabric],
        #           fontsize=16)
        # plt.show()
        #
        #
        # item_supplier_num = item_supplier_num_df['supplier_num'].value_counts()
        # colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(item_supplier_num.index)))
        # plt.pie(item_supplier_num.values, labels=item_supplier_num.index, autopct='%3.1f%%', colors=colors)
        # plt.title("Number of eligible suppliers per item, fabric:" + en_name_of_fabric[self.fabric],
        #           fontsize=16)
        # plt.show()
        #
        # supplier_item_num = supplier_item_num_df['item_num'].value_counts()
        # colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(supplier_item_num.index)))
        # plt.pie(supplier_item_num.values, labels=supplier_item_num.index, autopct='%3.1f%%', colors=colors)
        # plt.title("Number of items per supplier is eligible to produce, fabric:" + en_name_of_fabric[self.fabric],
        #           fontsize=16)
        # plt.show()
        #
        # supplier_machine_num = supplier_machine_num_df['machine_num'].value_counts()
        # colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(supplier_machine_num.index)))
        # plt.pie(supplier_machine_num.values, labels=supplier_machine_num.index, autopct='%3.1f%%', colors=colors)
        # plt.title("Number of machines per supplier, fabric:" + en_name_of_fabric[self.fabric],
        #           fontsize=16)
        # plt.show()


        item_quantity_list = list()
        order_quantity_list = list()
        order_production_time_length_list = list()

        for item in self.data[SetName.ITEM_LIST]:
            item_quantity_list.append((item, self.data[ParaName.ITEM_QUANTITY_DICT][item]))
        for order in self.data[SetName.ORDER_LIST]:
            order_quantity_list.append((order, self.data[ParaName.ORDER_QUANTITY_DICT][order]))
            order_production_time_length_list.append((order, len(self.data[SetName.ORDER_TIME_DICT][order])))

        item_quantity_df = pd.DataFrame(item_quantity_list, columns=['item_id', 'item_quantity'])
        order_quantity_df = pd.DataFrame(order_quantity_list, columns=['item_id', 'order_quantity'])
        order_production_time_length_df = pd.DataFrame(order_production_time_length_list, columns=['order_id', 'order_production_time_length'])

        item_quantity = item_quantity_df['item_quantity'].value_counts()
        order_quantity = order_quantity_df['order_quantity'].value_counts()
        order_production_time_length = order_production_time_length_df['order_production_time_length'].value_counts()

        colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(item_quantity.index)))
        plt.hist(item_quantity.values)
        plt.title("Item quantity, fabric:" + en_name_of_fabric[self.fabric],
                  fontsize=16)
        plt.savefig(out_dir+suanli_name+"_"+fabric+"_item_quantity.png", dpi = 500, bbox_inches = 'tight')

        plt.show()

        colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(order_quantity.index)))
        plt.hist(order_quantity.values)
        plt.title("Order quantity, fabric:" + en_name_of_fabric[self.fabric],
                  fontsize=16)
        plt.savefig(out_dir+suanli_name + "_" + fabric + "_order_quantity.png", dpi=500, bbox_inches='tight')

        plt.show()

        colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(order_production_time_length.index)))
        plt.pie(order_production_time_length.values, labels=order_production_time_length.index, autopct='%3.1f%%', colors=colors)
        plt.title("Order production time length, fabric:" + en_name_of_fabric[self.fabric],
                  fontsize=16)
        plt.savefig(out_dir+suanli_name + "_" + fabric + "_order_production_time_length.png", dpi=500, bbox_inches='tight')

        plt.show()

        order_df = self.data[DataName.ORDER]
        order_df = order_df[[OrderHeader.ORDER_ID, OrderHeader.ARRIVAL_DATE]]
        order_arrival_date = order_df[OrderHeader.ARRIVAL_DATE].value_counts()
        colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(order_arrival_date.index)))
        plt.pie(order_arrival_date.values, labels=order_arrival_date.index, autopct='%3.1f%%', colors=colors)
        plt.title("Order arrival date, fabric:" + en_name_of_fabric[self.fabric],
                  fontsize=16)
        plt.savefig(out_dir+suanli_name + "_" + fabric + "_order_arrival_date.png", dpi=500, bbox_inches='tight')

        plt.show()

        order_df = self.data[DataName.ORDER]
        order_df = order_df[[OrderHeader.ORDER_ID, OrderHeader.DUE_DATE]]
        order_due_date = order_df[OrderHeader.DUE_DATE].value_counts()
        colors = plt.get_cmap('Blues')(np.linspace(0.2, 0.7, len(order_due_date.index)))
        plt.pie(order_due_date.values, labels=order_due_date.index, autopct='%3.1f%%', colors=colors)
        plt.title("Order due date, fabric:" + en_name_of_fabric[self.fabric],
                  fontsize=16)
        plt.savefig(out_dir+suanli_name + "_" + fabric + "_order_due_date.png", dpi=500, bbox_inches='tight')

        plt.show()



def main():
    overall_sheet = list()
    for suanli_name in ['da_type_2_online_solve', 'uat_1_full']:
        for fabric in en_name_of_fabric:
            new_list = list()
            ori_dir = "D:/Codes/Python/semir-paper/"
            input_dir = ori_dir+"data/input/desensitized_data/"
            output_dir = ori_dir+"data_generation/raw_data_analysis/out/figures/"
            file = suanli_name+'/' + fabric+'/'
            new_list.append(fabric)
            new_list.append(suanli_name)

            # 数据处理
            dp = DataPrepare(input_dir, file)
            data = dp.prepare()

            # 特征处理
            fp = FeaturePrepare(data, file)
            data = fp.prepare()

            ma = DataAnalysis(data, fabric)
            # new_list = ma.cal_features(new_list)
            # overall_sheet.append(new_list)
            ma.cal_figures(suanli_name, fabric, output_dir)
    # overall_df = pd.DataFrame(overall_sheet, columns=['fabric', 'instance', 'item_num', 'order_num', 'supplier_num','machine_num',\
    #                                                   'avg machine_num_per_item', 'avg supplier_num_per_item', 'avg item_num_per_supplier',\
    #                                                   'avg machine_num_per_supplier', 'avg order_num_per_item', 'avg item_quantity', 'avg order_quantity',\
    #                                                   'avg order_time_window_length'])#, 'avg order_arrival_date', 'avg order_due_date'])
    # overall_df.to_csv("D:/Codes/Python/semir-paper/data_generation/raw_data_analysis/out/raw_data_analysis.csv", encoding='utf-8-sig')

if __name__ == '__main__':
    main()
