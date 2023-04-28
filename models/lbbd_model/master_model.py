import logging
import gurobipy as gp
from config import *
from models.lbbd_model.generate_cut import GenerateCut
from models.lbbd_model.sub_model import SubModel
from util.header import ImportanceMark, ParamsMark, GLOBALDATA
from util.util import var_name_regularizer

logger = logging.getLogger(__name__)

def my_call_back(model, where):
    if where == gp.GRB.Callback.MIPSOL:
        # 添加 user cut
        # 款分配至实体供应商结果
        item_supplier_result = dict()
        for (item, supplier) in GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.VARS][VarName.ALPHA]:
            if model.cbGetSolution(GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.VARS][VarName.ALPHA][item, supplier]) > 0.001:
                if supplier in item_supplier_result:
                    item_supplier_result[supplier].append(item)
                else:
                    item_supplier_result[supplier] = [item]
        for supplier in item_supplier_result:
            sub_data = cal_sub_data(supplier, item_supplier_result[supplier])
            sub_model = SubModel(GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.DATA], sub_data)
            sub_model.construct()
            is_feasible = sub_model.solve(mode=1)
            if not is_feasible:
                # 调用寻找benders cut函数
                item_list, mis_size = GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.CUT_GENERATOR].generate_mis(sub_model)
                # item_list = sub_data[LBBDSubDataName.ITEM_LIST]
                # mis_size = len(item_list)
                model.cbLazy(
                    gp.quicksum(GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.VARS][VarName.ALPHA][item, supplier]
                                for item in item_list)
                    - mis_size
                    <= -1
                )
                # print('[', end='')
                # for item in item_list:
                #     print(str(item), end=',')
                # print(']')
                # print("<", str(mis_size))

                # add cut to other suppliers
                # for supplier_other in GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.DATA][SetName.SUPPLIER_LIST]:
                #     if supplier != supplier_other:
                #         filtered_item_list = set.intersection(set(item_list), set(GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.DATA][SetName.ITEM_BY_SUPPLIER_DICT][supplier_other]))
                #         sub_data = cal_sub_data(supplier_other, filtered_item_list)
                #         sub_model = SubModel(GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.DATA], sub_data)
                #         sub_model.construct()
                #         is_feasible = sub_model.solve(mode=1)
                #         if not is_feasible:
                #             model.cbLazy(
                #                 gp.quicksum(
                #                     GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.VARS][VarName.ALPHA][item, supplier_other]
                #                     for item in filtered_item_list)
                #                 - len(filtered_item_list)
                #                 <= -1
                #             )
        model.update()

def cal_sub_data(supplier, item_list):
    sub_data = dict()
    sub_data[LBBDSubDataName.SUPPLIER] = supplier
    sub_data[LBBDSubDataName.ITEM_LIST] = item_list
    sub_data[LBBDSubDataName.ORDER_LIST] = list()
    for item in item_list:
        sub_data[LBBDSubDataName.ORDER_LIST].extend(GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.DATA][SetName.ORDER_BY_ITEM_DICT][item])
    sub_data[LBBDSubDataName.MACHINE_LIST] = GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.DATA][SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
    return sub_data

class MasterModel:
    def __init__(self, data):
        self.master_result_data = None
        self.data = data
        self.model = gp.Model()
        self.vars = dict()
        self.best_obj = None
        self.cut_generator = GenerateCut(data)
        self.cb = None

    def construct(self):
        """
        建立主问题模型的基本变量、目标、约束：
        1. 变量设置
        2. 目标函数设置
        3. 约束设置
        4. 模型求解参数设置
        """
        self.add_variables()
        self.add_objective()
        self.add_constrains()
        self.add_relaxed_sub_variables()  # 添加有效割的变量
        self.add_relaxed_sub_constrains()  # 添加有效割约束
        self.set_parameters()

    def solve_lbbd(self, lbbd_cut_data):
        """
        迭代过程的建模和求解主题函数：
        1. 添加Benders割
        5. 求解并获取求解结果
        :return:
        """
        self.lbbd_cut_data = lbbd_cut_data
        self.add_lbbd_cuts()
        result = self.gen_model_result()
        return result


    def add_relaxed_sub_variables(self):
        """
        添加子问题的松弛变量
        """

        logger.info('添加变量：松弛子问题变量Z_osT')
        self.vars[VarName.HAT_Z] = {(order, supplier, month): self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.HAT_Z}({order}_{supplier}_{month})'),
            vtype=gp.GRB.CONTINUOUS)
            for item in self.data[SetName.ITEM_LIST]
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
            for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]
            for month in self.data[SetName.ITEM_MONTH_DICT][item]}

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.NU_VAR]:
            logger.info('添加变量：松弛子问题辅助变量nu_m\hat_t')
            self.vars[VarName.NU] = {(machine, month): self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.NU}({machine}_{month})'),
                vtype=gp.GRB.BINARY)
                for machine in self.data[SetName.MACHINE_LIST]
                for month in self.data[SetName.MACHINE_TIME_MONTH_DICT][machine]
            }


        logger.info('添加变量：松弛子问题辅助变量kappa_st')
        self.vars[VarName.KAPPA] = {(supplier, date): self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.KAPPA}({supplier}_{date})'),
            vtype=gp.GRB.CONTINUOUS)
            for supplier in self.data[SetName.SUPPLIER_LIST]
            for date in self.data[SetName.TIME_LIST]}

    def add_z_osT_constrains(self):
        # =============
        # Z_os\hat_t 需求生产总量
        # =============
        for item in self.data[SetName.ITEM_LIST]:
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]:
                    self.model.addConstr(
                       gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                          for month in self.data[SetName.ORDER_TIME_MONTH_DICT][order]) ==
                        self.data[ParaName.ORDER_QUANTITY_DICT][order] * self.vars[VarName.ALPHA][
                            item, supplier])

        # =============
        # 月生产上限
        # =============
        # supplimentary_2-1 对于订单而言，月产量 <= min(款日上限，实体供应商日上限,产线月上限)
        # for item in self.data[SetName.ITEM_LIST]:
        #     item_max_occupy = self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]
        #     for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]:
        #         for month in self.data[SetName.ITEM_MONTH_DICT][item]:
        #             for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
        #                 if (order, supplier, month) in self.vars[VarName.HAT_Z]:
        #                     if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
        #                         # supplimentary_2-1.1
        #                         self.model.addConstr(
        #                             self.vars[VarName.HAT_Z][order, supplier, month] <=
        #                             sum(min(item_max_occupy,
        #                                     self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier].get(date,
        #                                                                                                          self.data[
        #                                                                                                              ParaName.MAX_QUANTITY]))
        #                                 for date in self.data[SetName.ORDER_TIME_DICT][order] if
        #                                 self.data[ParaName.MONTH_BY_TIME_DICT][date] == month)
        #                         )
        #                     else:
        #                         # supplimentary_2-1.1
        #                         self.model.addConstr(
        #                             self.vars[VarName.HAT_Z][order, supplier, month] <=
        #                             sum(min(item_max_occupy,
        #                                     self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier].get(date,
        #                                                                                                               self.data[ParaName.MAX_QUANTITY]))
        #                                 for date in self.data[SetName.ORDER_TIME_DICT][order] if
        #                                 date[:7] == month)
        #                         )
                            # supplimentary_2-1.2
                            # self.model.addConstr(self.vars[VarName.HAT_Z][order, supplier, month] <= sum(
                            #                      self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                            #                          (machine, month), 0)
                            #                      for machine in set.intersection(
                            #                          set(self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
                            #                          set(self.data[DAOptSetName.MACHINE_BY_ORDER_DICT][order]))
                            #                  ))

        # supplimentary_2-2 对于款式而言，月产量 <= min(款日上限，实体供应商日上限, 产线月产能)
        for item in self.data[SetName.ITEM_LIST]:
            item_max_occupy = self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]
            for month in self.data[SetName.ITEM_MONTH_DICT][item]:
                for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]:
                    if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
                        # supplimentary_2-2.1
                        self.model.addConstr(
                            gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                        for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                        if (order, supplier, month) in self.vars[VarName.HAT_Z]) <=
                            sum(min(item_max_occupy,
                                    self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier].get(date,
                                                                                                         self.data[
                                                                                                             ParaName.MAX_QUANTITY]))
                                for date in self.data[SetName.ITEM_TIME_DICT][item] if
                                self.data[ParaName.MONTH_BY_TIME_DICT][date] == month))
                    else:
                        # supplimentary_2-2.1
                        self.model.addConstr(
                           gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                              for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                              if (order, supplier, month) in self.vars[VarName.HAT_Z]) <=
                            sum(min(item_max_occupy,
                                    self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier].get(date,
                                                                                                         self.data[ParaName.MAX_QUANTITY]))
                                for date in self.data[SetName.ITEM_TIME_DICT][item] if
                                date[:7] == month))
                    # supplimentary_2-2.2
                    self.model.addConstr(
                       gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                          for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                          if (order, supplier, month) in self.vars[VarName.HAT_Z]) <=
                       gp.quicksum(
                            self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0)
                            for machine in set.intersection(
                                set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
                                set(self.data[SetName.MACHINE_BY_ITEM_DICT][item])))
                    )

        # supplimentary_2-3 对于供应商而言，月产量 <= min(实体供应商日上限，sum(款式日上限)，产线月上限)
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            for month in self.data[SetName.TIME_MONTH_LIST]:
                if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_RANDOM_DATA]:
                    # supplimentary_2-3.1
                    self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                     for item in
                                                     self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]
                                                     for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                     if (order, supplier, month) in self.vars[VarName.HAT_Z]) <=
                                         gp.quicksum(
                                             self.vars[VarName.KAPPA][supplier, date]
                                             for date in self.data[SetName.TIME_BY_MONTH_DICT][month] if
                                             self.data[ParaName.MONTH_BY_TIME_DICT][date] == month and (supplier, date) in self.vars[VarName.KAPPA])
                                         )
                else:
                    # supplimentary_2-3.1
                    self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                           for item in
                                                           self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]
                                                           for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                           if (order, supplier, month) in self.vars[VarName.HAT_Z]) <=
                                        gp.quicksum(
                                             self.vars[VarName.KAPPA][supplier, date]
                                             for date in self.data[SetName.TIME_BY_MONTH_DICT][month] if
                                             date[:7] == month and (supplier, date) in self.vars[VarName.KAPPA])
                                         )
                if ParamsMark.ALL_PARAMS_DICT[ParamsMark.NU_VAR]:
                    # supplimentary_2-3.2
                    self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                           for item in
                                                           self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]
                                                           for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                           if
                                                           (order, supplier, month) in self.vars[VarName.HAT_Z]) <=
                                        gp.quicksum(
                                             self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                 (machine, month), 0)
                                             * self.vars[VarName.NU][machine, month]
                                             for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
                                             if (machine, month) in self.vars[VarName.NU]
                                         ))
                else:
                    # supplimentary_2-3.2
                    self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                           for item in
                                                           self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]
                                                           for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                           if
                                                           (order, supplier, month) in self.vars[VarName.HAT_Z]) <=
                                         sum(self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                 (machine, month), 0)
                                             for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
                                         ))
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.SHARE_LEVEL] == 0:
            # supplimentary_2-4 对于具有交叉可用machine的情况而言，集合a内部的产量<= 集合a对应machine月产能
            for supplier in self.data[SetName.SUPPLIER_LIST]:
                for month in self.data[SetName.TIME_MONTH_LIST]:
                    for idx in range(len(self.data[SetName.MACHINE_SUB_SETS_BY_SUPPLIER_DICT][supplier])):
                        machine_subset = self.data[SetName.MACHINE_SUB_SETS_BY_SUPPLIER_DICT][supplier][idx]
                        item_subset = self.data[SetName.ITEM_SUB_SETS_BY_SUPPLIER_DICT][supplier][idx]
                        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.NU_VAR]:
                            self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                                   for item in item_subset
                                                                   for order in
                                                                   self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                                   if (order, supplier, month) in self.vars[
                                                                       VarName.HAT_Z]) <=
                                                gp.quicksum(
                                                     self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                         (machine, month), 0)
                                                     * self.vars[VarName.NU][machine, month]
                                                     for machine in machine_subset
                                                     if (machine, month) in self.vars[VarName.NU]
                                                 ))
                        else:
                            self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                                   for item in item_subset
                                                                   for order in
                                                                   self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                                   if (order, supplier, month) in self.vars[
                                                                       VarName.HAT_Z]) <=
                                                gp.quicksum(
                                                     self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                         (machine, month), 0)
                                                     for machine in machine_subset
                                                 ))
        elif ParamsMark.ALL_PARAMS_DICT[ParamsMark.SHARE_LEVEL] == 1:
            # supplimentary_2-4 对于算法供应商而言，相同channel的算法供应商对应可生产需求月产量<= 月产能
            for supplier in self.data[SetName.SUPPLIER_LIST]:
                for channel in self.data[SetName.CHANNEL_LIST]:
                    for month in self.data[SetName.TIME_MONTH_LIST]:
                        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.NU_VAR]:
                            self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                                   for item in
                                                                   set.intersection(set(
                                                                       self.data[SetName.ITEM_BY_SUPPLIER_DICT][
                                                                           supplier]),
                                                                       set(self.data[
                                                                               SetName.ITEM_BY_CHANNEL_DICT][
                                                                               channel]))
                                                                   for order in
                                                                   self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                                   if (order, supplier, month) in self.vars[
                                                                       VarName.HAT_Z]) <=
                                                gp.quicksum(
                                                     self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                         (machine, month), 0)
                                                     * self.vars[VarName.NU][machine, month]
                                                     for machine in set.intersection(
                                                         set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
                                                         set(self.data[SetName.MACHINE_BY_CHANNEL_DICT][channel]))
                                                     if (machine, month) in self.vars[VarName.NU]
                                                 ))
                        else:
                            self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                                   for item in
                                                                   set.intersection(set(
                                                                       self.data[SetName.ITEM_BY_SUPPLIER_DICT][
                                                                           supplier]),
                                                                       set(self.data[
                                                                               SetName.ITEM_BY_CHANNEL_DICT][
                                                                               channel]))
                                                                   for order in
                                                                   self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                                   if (order, supplier, month) in self.vars[
                                                                       VarName.HAT_Z]) <=
                                                 sum(
                                                     self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                         (machine, month), 0)
                                                     for machine in set.intersection(
                                                         set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
                                                         set(self.data[SetName.MACHINE_BY_CHANNEL_DICT][channel]))
                                                 ))
        elif ParamsMark.ALL_PARAMS_DICT[ParamsMark.SHARE_LEVEL] == 2:
            # supplimentary_2-4 对于算法供应商而言，相同channel的算法供应商对应可生产需求月产量<= 月产能
            for supplier in self.data[SetName.SUPPLIER_LIST]:
                for label in self.data[SetName.LABEL_LIST]:
                        for month in self.data[SetName.TIME_MONTH_LIST]:
                            if ParamsMark.ALL_PARAMS_DICT[ParamsMark.NU_VAR]:
                                self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                                       for item in
                                                                       set.intersection(set(
                                                                           self.data[SetName.ITEM_BY_SUPPLIER_DICT][
                                                                               supplier]),
                                                                           set(self.data[
                                                                                   SetName.ITEM_BY_LABEL_DICT][
                                                                                   label[0], label[1], label[2]]))
                                                                       for order in
                                                                       self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                                       if (order, supplier, month) in self.vars[
                                                                           VarName.HAT_Z]) <=
                                                    gp.quicksum(
                                                         self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                             (machine, month), 0)
                                                         * self.vars[VarName.NU][machine, month]
                                                         for machine in set.intersection(
                                                             set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][
                                                                     supplier]),
                                                             set(self.data[SetName.MACHINE_BY_LABEL_DICT][label[0], label[1], label[2]]))
                                                         if (machine, month) in self.vars[VarName.NU]
                                                     ))
                            else:
                                self.model.addConstr(gp.quicksum(self.vars[VarName.HAT_Z][order, supplier, month]
                                                                       for item in
                                                                       set.intersection(set(
                                                                           self.data[SetName.ITEM_BY_SUPPLIER_DICT][
                                                                               supplier]),
                                                                           set(self.data[
                                                                                   SetName.ITEM_BY_LABEL_DICT][
                                                                                   label[0], label[1], label[2]]))
                                                                       for order in
                                                                       self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                                       if (order, supplier, month) in self.vars[
                                                                           VarName.HAT_Z]) <=
                                                     sum(
                                                         self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                             (machine, month), 0)
                                                         for machine in set.intersection(
                                                             set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][
                                                                     supplier]),
                                                             set(self.data[SetName.MACHINE_BY_LABEL_DICT][label[0], label[1], label[2]]))
                                                     ))

    def add_nu(self):
        # =============
        # nu_m\hat_t 定义用约束，注：由于z_os\hat t已经决策到了月维度，所以不需要该项
        # =============
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]:
                for month in self.data[SetName.MACHINE_TIME_MONTH_DICT][machine]:
                    # 内含有可在machine生产且生产日期包括month的order的款式列表
                    item_list = []
                    for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(supplier, []):
                        for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                            if month in self.data[SetName.ORDER_TIME_MONTH_DICT][order]:
                                if machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]:
                                    item_list.append(item)
                                    break
                    # supplimentary_2-5.1
                    self.model.addConstr(
                        self.vars[VarName.NU][machine, month] <=
                       gp.quicksum(self.vars[VarName.ALPHA][item, supplier] for item in item_list))
                    # 有效不等式，不会去掉最优解 # supplimentary_2-5.2
                    for item in item_list:
                        self.model.addConstr(
                            self.vars[VarName.NU][machine, month] >=
                            self.vars[VarName.ALPHA][item, supplier])


    def add_relaxed_sub_constrains(self):
        """
        添加子问题的松弛约束
        """

        self.add_z_osT_constrains()
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.NU_VAR]:
            self.add_nu()


        # =============
        # kappa_st 定义用约束
        # =============
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            item_max_occupy_dict = {}
            for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(supplier, []):
                item_max_occupy_dict[item] = self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]

            for date in self.data[SetName.TIME_LIST]:
                # 内含有可在physical_supplier生产且生产日期包括date的款式列表
                item_list = []
                for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(supplier, []):
                    if date in self.data[SetName.ITEM_TIME_DICT][item]:
                        item_list.append(item)

                # 内含有可在physical_supplier生产且生产日期包括date的款式列表
                self.model.addConstr(
                    self.vars[VarName.KAPPA][supplier, date] <=
                    self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier].get(date, self.data[
                        ParaName.MAX_QUANTITY])
                )
                if len(item_list) > 0:
                    self.model.addConstr(
                        self.vars[VarName.KAPPA][supplier, date] <=
                       gp.quicksum(item_max_occupy_dict[item] * self.vars[VarName.ALPHA][item, supplier]
                                          for item in item_list
                                          ))
                else:
                    self.model.addConstr(self.vars[VarName.KAPPA][supplier, date] <= 0)


    def add_lbbd_cuts(self):
        """
        给模型添加添加LBBD迭代过程的feasibility割约束函数
        :return:
        """
        for supplier in self.lbbd_cut_data[
            LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT]:
            for item_list in self.lbbd_cut_data[
            LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT][supplier]:
                self.model.addConstr(
                   gp.quicksum(self.vars[VarName.ALPHA][item, supplier]
                                      for item in item_list)
                    - len(item_list)
                    <= -1
                )

        for supplier in self.lbbd_cut_data[
            LBBDCutName.MIS_BY_SUPPLIER_DICT]:
            self.model.addConstr(
               gp.quicksum(self.vars[VarName.ALPHA][item, supplier]
                                  for item in self.lbbd_cut_data[
                                      LBBDCutName.MIS_BY_SUPPLIER_DICT][
                                      supplier])
                - self.lbbd_cut_data[
                          LBBDCutName.MIS_SIZE_BY_SUPPLIER_DICT][
                          supplier]
                <= -1
            )

    def add_variables(self):
        """
        给模型添加变量
        :return:
        """
        # =============
        # 款相关变量
        # =============
        logger.info('添加变量：单款生产变量alpha')
        self.vars[VarName.ALPHA] = {(item, supplier): self.model.addVar(vtype=gp.GRB.BINARY,
                                                                        name=var_name_regularizer(
                                                                                 f'V_{VarName.ALPHA}({item}_{supplier})'),
                                                                        column=None, obj=0.0, lb=0.0, ub=1.0)
                                    for item in self.data[SetName.ITEM_LIST]
                                    for supplier in
                                    self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]}

        # =============
        # 产能规划相关变量
        # =============
        logger.info('添加变量：产能规划达成率相关变量')
        # 平均产能规划达成率
        self.vars[VarName.SUPPLIER_CAPACITY_RATIO] = {supplier: self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.SUPPLIER_CAPACITY_RATIO}_{supplier}'),
            vtype=gp.GRB.CONTINUOUS, lb=0)
            for supplier in self.data[SetName.SUPPLIER_LIST]
        }
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_AVERAGE_OBJ]:
            # 供应商产能规划达成率与池内平均规划率的差值
            self.vars[VarName.SUPPLIER_CAPACITY_RATIO_DELTA] = {supplier: self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.SUPPLIER_CAPACITY_RATIO_DELTA}_{supplier}'),
                vtype=gp.GRB.CONTINUOUS, lb=0)
                for supplier in self.data[SetName.SUPPLIER_LIST]
            }

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_LADDEL_OBJ]:
            # 池内平均产能规划达成率
            self.vars[VarName.POOL_CAPACITY_RATIO_AVG] = {pool: self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.POOL_CAPACITY_RATIO_AVG}_{pool}'),
                vtype=gp.GRB.CONTINUOUS, lb=0)
                for pool in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool]) > 0
            }
            # 供应商池子不符合阶梯性的达成率部分, pool_1（等级更高）相比pool_2平均达成率低的部分
            self.vars[VarName.POOLS_CAPACITY_RATIO_DELTA] = {(pool_1, pool_2): self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.POOLS_CAPACITY_RATIO_DELTA}_{pool_1}_{pool_2}'),
                vtype=gp.GRB.CONTINUOUS, lb=0)
                for pool_1 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                for pool_2 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_1]) > 0
                   and len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_2]) > 0
                   and ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[pool_1] < ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[
                       pool_2]
            }

        # =============
        # 实体供应商不可行方案辅助变量
        # =============
        self.vars[VarName.THETA] = {}

    def add_objective(self):
        """
        给模型设置目标函数
        :return:
        """
        # =============
        # 款式内订单延误
        # =============
        logger.info('模型添加优化目标：订单延误最少')
        order_delay_obj =gp.quicksum(
            (self.data[ObjCoeffName.ORDER_DELAY_BASE_PUNISH]
             + self.data[ObjCoeffName.ORDER_DELAY_PUNISH] * self.data[ParaName.ORDER_QUANTITY_DICT][
                 order]) *
            (1 -gp.quicksum(
                self.vars[VarName.ALPHA][self.data[ParaName.ORDER_ITEM_DICT][order], supplier]
                for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][
                    self.data[ParaName.ORDER_ITEM_DICT][order]]))
            for order in self.data[SetName.ORDER_LIST]
        )
        self.data[ObjName.ORDER_DELAY_OBJ] = order_delay_obj

        obj = order_delay_obj
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_AVERAGE_OBJ]:
            # =============
            # 产能规划达成率
            # =============
            logger.info('模型添加优化目标：池内实体供应商产能规划达成率均衡')
            capacity_average_obj =gp.quicksum(
                self.data[ObjCoeffName.CAPACITY_AVERAGE_PUNISH]
                * self.vars[VarName.SUPPLIER_CAPACITY_RATIO_DELTA][supplier]
                for supplier in self.data[SetName.SUPPLIER_LIST]
            )
            self.data[ObjName.CAPACITY_AVERAGE_OBJ] = capacity_average_obj

            obj += capacity_average_obj

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_LADDEL_OBJ]:
            logger.info('模型添加优化目标：池子内产能规划达成率均值呈现阶梯')
            capacity_ladder_obj = self.data[ObjCoeffName.SUPPLIER_LADDER_PUNISH] *gp.quicksum(
                self.vars[VarName.POOLS_CAPACITY_RATIO_DELTA][pool_1, pool_2]
                for pool_1 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                for pool_2 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_1]) > 0 and \
                len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_2]) > 0 and \
                ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[pool_1] < ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[pool_2])
            self.data[ObjName.CAPACITY_LADDER_OBJ] = capacity_ladder_obj
            obj += capacity_ladder_obj

        self.model.setObjective(obj, gp.GRB.MINIMIZE)

    def add_constrains(self):
        """
        给模型添加约束函数
        :return:
        """
        # =============
        # 款生产约束
        # =============
        logger.info('模型添加约束：单款只能在一个实体供应商进行生产')
        for item in self.data[SetName.ITEM_LIST]:
            self.model.addConstr(
               gp.quicksum(
                    self.vars[VarName.ALPHA][item, supplier] for supplier in
                    self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]
                ) <= 1,
                name=f"item_{item}_uses_at_most_1_phy-supplier"
            )
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_AVERAGE_OBJ]:
            # =============
            # 产能规划达成率约束
            # =============
            logger.info('模型添加约束：产能规划达成率约束')
            for supplier in self.data[SetName.SUPPLIER_LIST]:
                self.model.addConstr(
                    self.vars[VarName.SUPPLIER_CAPACITY_RATIO][supplier] ==
                   gp.quicksum(
                        self.vars[VarName.ALPHA][item, supplier] *
                        self.data[ParaName.ITEM_QUANTITY_DICT][
                            item]
                        for item in self.data[SetName.ITEM_LIST]
                        if (item, supplier) in self.vars[VarName.ALPHA]
                    ) / sum([
                        self.data[ParaName.MACHINE_CAPACITY_PLANNED_DICT].get((machine, month), 0)
                        for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT].get(supplier, [])
                        for month in self.data[SetName.MACHINE_TIME_MONTH_DICT].get(machine, [])]),
                    name=f"planned_capacity_occupied_ratio_of_{supplier}"
                )
            for pool in self.data[SetName.SUPPLIER_BY_POOL_DICT]:
                for supplier in self.data[SetName.SUPPLIER_BY_POOL_DICT][pool]:
                    self.model.addConstr(
                        self.vars[VarName.SUPPLIER_CAPACITY_RATIO_DELTA][supplier] >=
                        self.vars[VarName.SUPPLIER_CAPACITY_RATIO][supplier] -
                        self.vars[VarName.POOL_CAPACITY_RATIO_AVG][pool],
                        name=f"supplier_capacity_ratio_delta_of_{supplier}_in_pool_{pool}_1"
                    )
                    self.model.addConstr(
                        self.vars[VarName.SUPPLIER_CAPACITY_RATIO_DELTA][supplier] >=
                        self.vars[VarName.POOL_CAPACITY_RATIO_AVG][pool]
                        - self.vars[VarName.SUPPLIER_CAPACITY_RATIO][supplier],
                        name=f"supplier_capacity_ratio_delta_of_{supplier}_in_pool_{pool}_2"
                    )

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_LADDEL_OBJ]:
            for pool in self.data[SetName.SUPPLIER_BY_POOL_DICT]:
                if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool]) > 0:
                    self.model.addConstr(
                       gp.quicksum(
                            self.vars[VarName.ALPHA][item, supplier] *
                            self.data[ParaName.ITEM_QUANTITY_DICT][
                                item]
                            for supplier in self.data[SetName.SUPPLIER_BY_POOL_DICT][pool]
                            for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]
                            if (item, supplier) in self.vars[VarName.ALPHA]
                        ) / sum([
                            self.data[ParaName.MACHINE_CAPACITY_PLANNED_DICT].get((machine, month), 0)
                            for supplier in self.data[SetName.SUPPLIER_BY_POOL_DICT][pool]
                            for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT].get(supplier, [])
                            for month in self.data[SetName.MACHINE_TIME_MONTH_DICT].get(machine, [])]) ==
                        self.vars[VarName.POOL_CAPACITY_RATIO_AVG][pool],
                        name=f"pool_capacity_ratio_avg_of_{pool}"
                    )

            for pool_1 in self.data[SetName.SUPPLIER_BY_POOL_DICT]:
                for pool_2 in self.data[SetName.SUPPLIER_BY_POOL_DICT]:
                    if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_1]) > 0 and \
                            len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_2]) > 0 and \
                            ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[pool_1] < ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[
                        pool_2]:
                        self.model.addConstr(
                            self.vars[VarName.POOLS_CAPACITY_RATIO_DELTA][pool_1, pool_2] >=
                            self.vars[VarName.POOL_CAPACITY_RATIO_AVG][pool_2]
                            - self.vars[VarName.POOL_CAPACITY_RATIO_AVG][pool_1],
                            name=f"planned_capacity_ratio_delta_of_{pool_1}_and_{pool_2}"
                        )

    def cal_sub_data(self, supplier, item_list):
        sub_data = dict()
        sub_data[LBBDSubDataName.SUPPLIER] = supplier
        sub_data[LBBDSubDataName.ITEM_LIST] = item_list
        sub_data[LBBDSubDataName.ORDER_LIST] = list()
        for item in item_list:
            sub_data[LBBDSubDataName.ORDER_LIST].extend(self.data[SetName.ORDER_BY_ITEM_DICT][item])
        sub_data[LBBDSubDataName.MACHINE_LIST] = self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
        return sub_data

    def set_parameters(self):
        """
        设置模型求解的参数
        :return:
        """
        self.model.setParam(gp.GRB.Param.TimeLimit, ParamsMark.ALL_PARAMS_DICT[ParamsMark.MAX_RUNTIME])  # 求解时间上限
        self.model.setParam(gp.GRB.Param.MIPGap, ParamsMark.ALL_PARAMS_DICT[ParamsMark.MIP_GAP])  # 给定停止的Gap
        # self.model.setParam(gp.GRB.Param.OutputFlag, 0)
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] == 2:
            self.model.setParam('LazyConstraints', 1)
            GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.VARS] = self.vars
            GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.DATA] = self.data
            GLOBALDATA.ALL_GLOBAL_DATA_DICT[GLOBALDATA.CUT_GENERATOR] = GenerateCut(self.data)
            self.model._cb = my_call_back

    def gen_model_result(self):
        """
        模型求解，并获取求解结果
        :return:
        """
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] == 2:
            self.model.optimize(self.model._cb)
        else:
            self.model.optimize()

        if self.model.Status in [gp.GRB.Status.INFEASIBLE, gp.GRB.Status.UNBOUNDED]:
            self.model.computeIIS()
            error_info = '!!! 没有可行解 !!!'
            logger.error(error_info)
            raise Exception(error_info)

        # 款分配至实体供应商结果
        item_supplier_result = dict()
        for (item, supplier), var in self.vars[VarName.ALPHA].items():
            value = var.x
            if value > 0.001:
                if supplier in item_supplier_result:
                    item_supplier_result[supplier].append(item)
                else:
                    item_supplier_result[supplier] = [item]

        supplier_capacity_ratio_result = dict()
        for supplier, var in self.vars[VarName.SUPPLIER_CAPACITY_RATIO].items():
            value = var.x
            supplier_capacity_ratio_result[supplier] = value

        pool_capacity_ratio_avg_result = dict()
        for pool, var in self.vars[VarName.POOL_CAPACITY_RATIO_AVG].items():
            value = var.x
            pool_capacity_ratio_avg_result[pool] = value

        self.master_result_data = {
            ResultName.ITEM_SUPPLIER: item_supplier_result,
            ResultName.SUPPLIER_CAPACITY_RATIO: supplier_capacity_ratio_result,
            ResultName.POOL_CAPACITY_RATIO_AVG: pool_capacity_ratio_avg_result
        }

        return self.master_result_data

    def add_fixed_assignments(self, sub_result):
        temp_item_list = []
        for supplier in sub_result:
            for (item, supplier) in sub_result[supplier][ResultName.ITEM_SUPPLIER]:
                temp_item_list.append(item)
                self.model.addConstr(self.vars[VarName.ALPHA][item, supplier] == 1, name=f"item_{item}_production_in_{supplier}")
        # not_produced_item_set = set(self.data[SetName.ITEM_LIST])-set(temp_item_list)
        # for item in not_produced_item_set:
        #     self.model.addConstr(gp.quicksum(self.vars[VarName.ALPHA][item, supplier] for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item])
        #                          == 0, name=f"item_{item}_production")
    def construct_as_full_model(self):
        # =============
        # 订单生产相关变量
        # =============
        logger.info('添加变量：订单生产变量z')
        self.vars[VarName.Z] = {(order, machine, date): self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.Z}({order}_{machine}_{date})'),
            vtype=gp.GRB.INTEGER)
            for item in self.data[SetName.ITEM_LIST]
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
            for machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]
            for date in self.data[SetName.ORDER_TIME_DICT][order]
        }

        # =============
        # 需求生产约束
        # =============
        logger.info('模型添加约束：需求量生产')
        for item in self.data[SetName.ITEM_LIST]:
            for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]:
                for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                    self.model.addConstr(gp.quicksum(
                        self.vars[VarName.Z][order, machine, date]
                        for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                        set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT].get(supplier, [])))
                        for date in self.data[SetName.ORDER_TIME_DICT][order]
                    ) == self.data[ParaName.ORDER_QUANTITY_DICT][order] *
                                         self.vars[VarName.ALPHA][item, supplier],
                                         name=f"order_{order}_production_quantity"
                                         )
        # =============
        # 款式日生产上限
        # =============
        logger.info('模型添加约束：对款的单日生产上限限制')
        for item in self.data[SetName.ITEM_LIST]:
            for date in self.data[SetName.ITEM_TIME_DICT][item]:
                self.model.addConstr(gp.quicksum(
                    self.vars[VarName.Z].get((order, machine, date), 0) for order in
                    self.data[SetName.ORDER_BY_ITEM_DICT][item]
                    for machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]
                ) <= self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item],
                                     name=f"production_limit_of_item_{item}_on_{date}"
                                     )
        # =============
        # 实体供应商产能日上限
        # =============
        logger.info('模型添加约束：实体供应商产能日上限')
        for supplier in self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT]:
            for date in self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier]:
                if self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date] >= 0 and date in self.data[SetName.TIME_LIST]:
                    self.model.addConstr(
                        gp.quicksum(
                            self.vars[VarName.Z][order, machine, date]
                            for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(supplier, [])
                            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                            for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                            set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]))
                            if (order, machine, date) in self.vars[VarName.Z]
                        ) <= self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date],
                        name=f"production_limit_of_supplier_{supplier}'s_on_{date}"
                    )

        # =============
        # 产线产能月上限
        # =============
        logger.info('模型添加约束：产线产能月上限')
        for machine in self.data[SetName.MACHINE_LIST]:
            for month in self.data[SetName.MACHINE_TIME_MONTH_DICT].get(machine, []):
                self.model.addConstr(gp.quicksum(
                    self.vars[VarName.Z].get((order, machine, date), 0)
                    for order in self.data[SetName.ORDER_BY_MACHINE_DICT][machine]
                    for date in self.data[SetName.TIME_BY_MONTH_DICT][month]
                    if month in self.data[SetName.TIME_BY_MONTH_DICT] and (order, machine, date) in
                    self.vars[VarName.Z]
                ) <= self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0),
                                     name=f"demand_capacity_limit_for_machine_{machine}_in_{month}"
                                     )


    def gen_model_result_as_full_model(self):
        """
        模型求解，并获取求解结果
        :return:
        """
        logger.info('------ 求解开始 ------')
        self.model.optimize()
        logger.info('------ 求解结束 ------')

        if self.model.Status in [gp.GRB.Status.INFEASIBLE, gp.GRB.Status.UNBOUNDED]:
            # self.model.computeIIS()
            # self.model.write(self.file_dir + self.name + '_model.ilp')
            # error_info = '!!! 没有可行解 !!!'
            # logger.error(error_info)
            # raise Exception(error_info)
            return False

        # 获取求解结果

        order_machine_date_result = dict()
        for(order, machine, date), var in self.vars[VarName.Z].items():
            value = var.x
            if value > 0.001:
                order_machine_date_result[order, machine, date] = value

        supplier_capacity_ratio_result = dict()
        for supplier, var in self.vars[VarName.SUPPLIER_CAPACITY_RATIO].items():
            value = var.x
            supplier_capacity_ratio_result[supplier] = value

        pool_capacity_ratio_avg_result = dict()
        for pool, var in self.vars[VarName.POOL_CAPACITY_RATIO_AVG].items():
            value = var.x
            pool_capacity_ratio_avg_result[pool] = value

        self.result = {
            ResultName.ORDER_MACHINE_DATE: order_machine_date_result,
            ResultName.SUPPLIER_CAPACITY_RATIO: supplier_capacity_ratio_result,
            ResultName.POOL_CAPACITY_RATIO_AVG: pool_capacity_ratio_avg_result
        }

        # 款分配至实体供应商结果
        item_supplier_result = dict()
        for (item, supplier), var in self.vars[VarName.ALPHA].items():
            value = var.x
            if value > 0.001:
                item_supplier_result[item, supplier] = value
        self.result[ResultName.ITEM_SUPPLIER] = item_supplier_result

        return self.result