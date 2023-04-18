import setuptools.archive_util
import setuptools.command.install

from models.lbbd_model.master_model import MasterModel
from constant.config import *
from models.lbbd_model.relaxed_master_model import RelaxedMasterModel
from models.lbbd_model.relaxed_sub_model import RelaxedSubModel
from models.lbbd_model.sub_model import SubModel
import numpy as np
import copy
import logging
import time
from util.header import *

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

class LogicBasedBenders:
    """
    logic based benders
    """

    def __init__(self, data):
        """
        模型初始化
        :param data: 记录建模所需的所有信息
        :param name: 模型名称
        """
        # 基础数据记录
        self.data = data
        # 初始化模型
        self.master_model = None  # 主问题模型
        self.sub_models = dict()
        self.master_data = dict()
        self.sub_data = dict()
        self.lbbd_cut_data = dict()
        self.result = dict()

    def solve(self):
        """
        Logic-based benders 求解主函数
        """

        # 初始化数据
        iteration = 0
        self.update_data()

        # 构建主问题模型
        self.master_model = MasterModel(self.data)
        self.master_model.construct()

        start_time = time.time()
        # 开始lbbd迭代循环
        while iteration < ParamsMark.ALL_PARAMS_DICT[ParamsMark.MAX_ITERATION]:
            iteration += 1
            all_sub_feasible = True

            # 求解主问题
            self.master_data = self.master_model.solve(self.lbbd_cut_data)

            # 清空数据
            self.update_data()

            # 创建子问题进行可行性检验
            for supplier in self.master_data[ResultName.ITEM_SUPPLIER]:
                sub_data = self.cal_sub_data(supplier, self.master_data[ResultName.ITEM_SUPPLIER][supplier])
                sub_model = SubModel(self.data, sub_data)
                sub_model.construct()
                self.sub_models[supplier] = sub_model
                is_feasible = sub_model.solve(mode=1)
                if not is_feasible:
                    all_sub_feasible = False
                    self.add_lbbd_cut(sub_model)  # 添加LBBD cut，包含了寻找MIS的启发式函数等

            # 如果全都可行，求解子问题
            if all_sub_feasible:
                self.result[LBBDResultName.MASTER_RESULT] = self.master_data
                self.result[LBBDResultName.SUB_RESULT] = dict()
                for supplier in self.sub_models:
                    sub_result = self.sub_models[supplier].solve(mode=2)
                    self.result[LBBDResultName.SUB_RESULT][supplier] = sub_result
                end_time = time.time()
                self.result[LBBDResultName.RUN_TIME] = end_time - start_time
                self.result[LBBDResultName.OBJ_VALUE] = self.master_model.model.objVal
                self.result[LBBDResultName.LOWER_BOUND] = self.master_model.model.objVal
                self.result[LBBDResultName.ITERATION] = iteration
                return True, self.result
            # 否则，更新计算时长
            end_time = time.time()
            if end_time - start_time > ParamsMark.ALL_PARAMS_DICT[ParamsMark.MAX_RUNTIME]:
                # 超出计算时长
                # 求解子问题得到最多可以生产的款式数
                self.result[LBBDResultName.SUB_RESULT] = dict()
                for supplier in self.master_data[ResultName.ITEM_SUPPLIER]:
                    sub_data = self.cal_sub_data(supplier, self.master_data[ResultName.ITEM_SUPPLIER][supplier])
                    sub_model = RelaxedSubModel(self.data, sub_data, 0, 3)
                    sub_model.construct()
                    sub_result = sub_model.solve(mode=2)
                    self.result[LBBDResultName.SUB_RESULT][supplier] = sub_result
                # 建立松弛的主问题求解
                relaxed_master_model = RelaxedMasterModel(self.data)
                relaxed_master_model.construct()
                relaxed_master_model.add_fixed_assignments(self.result[LBBDResultName.SUB_RESULT])
                self.result[LBBDResultName.MASTER_RESULT] = relaxed_master_model.solve(self.lbbd_cut_data)
                self.result[LBBDResultName.RUN_TIME] = end_time - start_time
                self.result[LBBDResultName.OBJ_VALUE] = relaxed_master_model.model.objVal
                self.result[LBBDResultName.LOWER_BOUND] = self.master_model.model.objVal
                self.result[LBBDResultName.ITERATION] = iteration
                break
        # 超出时长or MAX_ITERATION 时，获取一个可行解
        return False, self.result

    def cal_sub_data(self, supplier, item_list):
        sub_data = dict()
        sub_data[LBBDSubDataName.SUPPLIER] = supplier
        sub_data[LBBDSubDataName.ITEM_LIST] = item_list
        sub_data[LBBDSubDataName.ORDER_LIST] = list()
        for item in item_list:
            sub_data[LBBDSubDataName.ORDER_LIST].extend(self.data[SetName.ORDER_BY_ITEM_DICT][item])
        sub_data[LBBDSubDataName.MACHINE_LIST] = self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
        return sub_data

    def update_data(self):
        self.sub_models = dict()
        self.result = dict()
        self.lbbd_cut_data[LBBDCutName.MIS_BY_SUPPLIER_DICT] = dict()
        self.lbbd_cut_data[LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT] = dict()
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            self.lbbd_cut_data[LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT][supplier] = list()
        self.lbbd_cut_data[LBBDCutName.MIS_BY_SUPPLIER_DICT] = dict()
        self.lbbd_cut_data[LBBDCutName.MIS_SIZE_BY_SUPPLIER_DICT] = dict()

    def add_lbbd_cut(self, sub_model):
        """
        更新logic-based cut的信息
        寻找MIS
        """
        self.lbbd_cut_data[LBBDCutName.MIS_BY_SUPPLIER_DICT][sub_model.supplier], self.lbbd_cut_data[LBBDCutName.MIS_SIZE_BY_SUPPLIER_DICT][sub_model.supplier] = \
            self.gen_mis(sub_model)


    def sort_items_by_quantity(self, item_list):
        quantity = []
        for item in item_list:
            quantity.append(self.data[ParaName.ITEM_QUANTITY_DICT][item])

        quantity = np.array(quantity)
        idx = np.argsort(quantity)
        sorted_item_list = []
        for i in range(len(quantity)):
            sorted_item_list.append(item_list[idx[i]])
        return sorted_item_list

    def gen_mis(self, sub_model):
        """
        寻找最小不可行款式集合

        """
        # item_list = self.greedy_gen_mis(sub_model)
        item_list = self.dfbs_gen_mis(sub_model)
        # 将MIS放到其他supplier上进行测试
        # self.add_mis_to_other_suppliers(item_list, supplier)
        return item_list, len(item_list)
        # return self.cut_lifting(sub_model, item_list)

    def dfbs_gen_mis(self, sub_model):
        """
        depth first binary search 寻找最小不可行款集合
        """
        sub_data = sub_model.sub_data
        item_list = self.sort_items_by_quantity(item_list=sub_data[LBBDSubDataName.ITEM_LIST])

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
                    logger.info("!!!!!!!!!" + "供应商：" + str(sub_data_copy[LBBDSubDataName.SUPPLIER]) +"最小不可行集合!!!!!!!!!")
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

    def greedy_gen_mis(self, sub_model):
        """
        贪婪方法寻找最小不可行款集合
        """
        sub_data = sub_model.sub_data
        supplier = sub_model.supplier
        item_list = self.sort_items_by_quantity(item_list=sub_data[LBBDSubDataName.ITEM_LIST])
        flag = True
        idx = 0
        while flag:
            all_feasible = True
            while idx < len(item_list):
                item = item_list[idx]
                idx += 1
                sub_data_copy = copy.deepcopy(sub_data)
                sub_data_copy[LBBDSubDataName.ITEM_LIST] = copy.deepcopy(item_list)
                sub_data_copy[LBBDSubDataName.ITEM_LIST].remove(item)
                sub_model = SubModel(self.data, sub_data_copy)
                sub_model.construct()
                if_feasible = sub_model.solve(mode=1)
                if not if_feasible:
                    # 不可行
                    logger.info("!!!!!!!!!" + "供应商：" + str(supplier) + "子问题不可行!!!!!!!!!")
                    print('[', end='')
                    for item in item_list:
                        print(str(item), end=',')
                    print(']')
                    item_list = sub_data_copy[LBBDSubDataName.ITEM_LIST]
                    all_feasible = False
                    idx -= 1
                    break
            if all_feasible or (len(item_list) == 1):
                # 去掉所有款式都可行，则说明找到了令supplier 产生不可解的最小款组合方案
                flag = False
        return item_list

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
                    logger.info("!!!!!!!!!" + "供应商：" + str(supplier) + "子问题不可行!!!!!!!!!")
                    print('[', end='')
                    for item in item_list_copy:
                        print(str(item), end=',')
                    print(']')

                    lifted_item_list.append(item)
        return lifted_item_list, mis_size


    def add_mis_to_other_suppliers(self, item_list, tested_supplier):
        """
        :param item_list:
        :return:
        """
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            if supplier != tested_supplier:
                filtered_item_list = set.intersection(set(item_list), set(self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]))
                sub_data = self.cal_sub_data(supplier, filtered_item_list)
                sub_model = SubModel(self.data, sub_data)
                sub_model.construct()
                self.sub_models[supplier] = sub_model
                is_feasible = sub_model.solve(mode=1)
                if not is_feasible:
                    self.lbbd_cut_data[LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT][supplier].append(filtered_item_list)






