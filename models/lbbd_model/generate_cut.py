import copy

import logging

import numpy as np

from config import ParaName, LBBDSubDataName, SetName, LBBDCutName
from models.lbbd_model.relaxed_sub_model import RelaxedSubModel
from models.lbbd_model.sub_model import SubModel
from util.header import ParamsMark

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


class GenerateCut:
    def __init__(self, data):
        self.data = data


    def generate_mis(self, sub_model, descending):
        """
        寻找最小不可行款式集合

        """
        item_list = None
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CUT_MODE] == 0:
            item_list = self.greedy_gen_mis(sub_model, descending)
        elif ParamsMark.ALL_PARAMS_DICT[ParamsMark.CUT_MODE] == 1:
            item_list = self.dfbs_gen_mis(sub_model, descending)
        elif ParamsMark.ALL_PARAMS_DICT[ParamsMark.CUT_MODE] == 2:
            item_list = self.greedy_gen_cut(sub_model)

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_LIFT]:
            return self.cut_lifting(sub_model, item_list)
        else:
            return item_list, len(item_list)



    def sort_items_by_quantity(self, item_list, is_descending):
        quantity = []
        for item in item_list:
            quantity.append(self.data[ParaName.ITEM_QUANTITY_DICT][item])

        quantity = np.array(quantity)
        if is_descending:
            idx = np.argsort(-quantity)
        else:
            idx = np.argsort(quantity)
        sorted_item_list = []
        for i in range(len(quantity)):
            sorted_item_list.append(item_list[idx[i]])
        return sorted_item_list

    def greedy_gen_cut(self, sub_model):
        """
        greedy：持续随机挑选变量赋值为0，直到可行，输出所偶有取值为1的变量集合
        """
        sub_data = sub_model.sub_data
        item_list = sub_data[LBBDSubDataName.ITEM_LIST]

        sub_data_copy = copy.deepcopy(sub_data)
        relaxed_sub_model = RelaxedSubModel(self.data, sub_data_copy, len(item_list), 2)
        relaxed_sub_model.construct()

        T_item_list = copy.deepcopy(item_list)
        for item in item_list:
            relaxed_sub_model.add_alpha_equals_1_constrains(item)
        is_feasible = relaxed_sub_model.solve(mode=1)

        while True:
            item_selected = T_item_list[0]
            c = relaxed_sub_model.model.getConstrByName(f"item_{item_selected}_production")
            relaxed_sub_model.model.remove(c)

            is_feasible = relaxed_sub_model.solve(mode=1)
            if is_feasible:
                # 不可行
                # logger.info("!!!!!!!!!子问题不可行greedy-cut!!!!!!!!!")
                # print('[', end='')
                # for item in T_item_list:
                #     print(str(item), end=',')
                # print(']')
                return T_item_list
            else:
                T_item_list.remove(item_selected)

    def dfbs_gen_mis(self, sub_model, is_descending):
        """
        depth first binary search 寻找最小不可行款集合
        """
        sub_data = sub_model.sub_data
        item_list = self.sort_items_by_quantity(item_list=sub_data[LBBDSubDataName.ITEM_LIST], is_descending=is_descending)

        sub_data_copy = copy.deepcopy(sub_data)
        relaxed_sub_model = RelaxedSubModel(self.data, sub_data_copy, len(item_list), 2)
        relaxed_sub_model.construct()


        T_item_list = copy.deepcopy(item_list)
        T1_item_list = []
        T2_item_list = []
        S_item_list = []

        I_item_list = []
        is_return_len_temp = False
        while True:
            if len(T_item_list) <= 1:
                I_item_list.extend(T_item_list)
                for item in T_item_list:
                    relaxed_sub_model.add_alpha_equals_1_constrains(item)
                is_feasible = relaxed_sub_model.solve(mode=1)
                if not is_feasible:
                    # 不可行
                    logger.info("!!!!!!!!!" + "供应商：" + str(sub_data_copy[LBBDSubDataName.SUPPLIER]) +"最小不可行集合(dfbs)!!!!!!!!!, is_descending："+str(is_descending))
                    print('[', end='')
                    for item in I_item_list:
                        print(str(item), end=',')
                    print(']')
                    return I_item_list
                T_item_list = copy.deepcopy(S_item_list)
                S_item_list = []
                if len(T_item_list) >= 2:
                    is_return_len_temp = True
                else:
                    T2_item_list = copy.deepcopy(T_item_list)
                    T1_item_list = []
                    is_return_len_temp = False
            else:
                # split T into T1 and T2
                T1_item_list = T_item_list[:len(T_item_list)//2]
                T2_item_list = T_item_list[len(T_item_list)//2:]
                is_return_len_temp = False
            if not is_return_len_temp:
                I_item_list.extend(S_item_list)
                I_item_list.extend(T1_item_list)
                for item in set.union(set(S_item_list), set(T1_item_list)):
                    relaxed_sub_model.add_alpha_equals_1_constrains(item)
                is_feasible = relaxed_sub_model.solve(mode=1)
                if is_feasible:
                    S_item_list.extend(T1_item_list)
                    T_item_list = copy.deepcopy(T2_item_list)
                else:
                    T_item_list = copy.deepcopy(T1_item_list)
                for item in set.union(set(S_item_list), set(T1_item_list)):
                    c = relaxed_sub_model.model.getConstrByName(f"item_{item}_production")
                    # c.__dict__
                    relaxed_sub_model.model.remove(c)
                    I_item_list.remove(item)

    def greedy_gen_mis(self, sub_model, is_descending):
        """
        贪婪方法寻找最小不可行款集合
        """
        sub_data = sub_model.sub_data
        item_list = sub_data[LBBDSubDataName.ITEM_LIST]

        sub_data_copy = copy.deepcopy(sub_data)
        relaxed_sub_model = RelaxedSubModel(self.data, sub_data_copy, len(item_list), 2)
        relaxed_sub_model.construct()

        for item in item_list:
            relaxed_sub_model.add_alpha_equals_1_constrains(item)
        is_feasible = relaxed_sub_model.solve(mode=1)
        T_item_list = self.sort_items_by_quantity(item_list=sub_data[LBBDSubDataName.ITEM_LIST],
                                                  is_descending=is_descending)
        flag = True
        idx = 0
        while flag:
            all_feasible = True
            while idx < len(T_item_list):
                item = T_item_list[idx]
                idx += 1
                c = relaxed_sub_model.model.getConstrByName(f"item_{item}_production")
                # c.__dict__
                relaxed_sub_model.model.remove(c)
                is_feasible = relaxed_sub_model.solve(mode=1)
                if not is_feasible:
                    T_item_list.remove(item)
                    all_feasible = False
                    idx -= 1
                    break
                else:
                    relaxed_sub_model.add_alpha_equals_1_constrains(item)
            if all_feasible or (len(item_list) == 1):
                # 不可行
                # logger.info("!!!!!!!!!" + "供应商：" + str(sub_model.supplier) + "子问题不可行!!!!!!!!!, is_descending："+str(is_descending))
                # print('[', end='')
                # for item in T_item_list:
                #     print(str(item), end=',')
                # print(']')
                # 去掉所有款式都可行，则说明找到了令supplier 产生不可解的最小款组合方案
                flag = False
        return T_item_list

    def cut_lifting(self, sub_model, item_list):
        mis_size = len(item_list)
        lifted_item_list = copy.deepcopy(item_list)
        sub_data = sub_model.sub_data
        supplier = sub_model.supplier
        for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]:
            if item not in item_list:
                item_list_copy = copy.deepcopy(lifted_item_list)
                item_list_copy.append(item)
                sub_data_copy = copy.deepcopy(sub_data)
                sub_data_copy[LBBDSubDataName.ITEM_LIST] = item_list_copy
                sub_model = RelaxedSubModel(self.data, sub_data_copy, mis_size, 1)
                sub_model.construct()
                if_feasible = sub_model.solve(mode=1)
                if not if_feasible:
                    # logger.info("!!!!!!!!!" + "供应商：" + str(supplier) + "Lifted子问题不可行!!!!!!!!!")
                    # print('[', end='')
                    # for item in item_list_copy:
                    #     print(str(item), end=',')
                    # print(']', end=',')
                    # print("mis_size="+str(mis_size))

                    lifted_item_list.append(item)
        return lifted_item_list, mis_size

    # def add_mis_to_other_suppliers(self, item_list, tested_supplier):
    #     """
    #     :param item_list:
    #     :return:
    #     """
    #     lbbd_cut_data = dict()
    #     for supplier in self.data[SetName.SUPPLIER_LIST]:
    #         if supplier != tested_supplier:
    #             filtered_item_list = set.intersection(set(item_list), set(self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]))
    #             sub_data = cal_sub_data(supplier, filtered_item_list)
    #             sub_model = SubModel(self.data, sub_data)
    #             sub_model.construct()
    #             self.sub_models[supplier] = sub_model
    #             is_feasible = sub_model.solve(mode=1)
    #             if not is_feasible:
    #                 lbbd_cut_data[LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT][supplier].append(filtered_item_list)
    #
    #     return lbbd_cut_data

