import logging
import gurobipy
from config import *
from util.util import var_name_regularizer

logger = logging.getLogger(__name__)


class TestMasterModel:
    def __init__(self, data, supplier, items_list):
        self.master_result_data = None
        self.obj_val = 0
        self.data = data
        self.model = gurobipy.Model()
        self.vars = dict()
        self.add_binary = False  # 是否添加0-1变量lambda 和nu
        self.supplier = supplier
        self.items_list = items_list

    def construct(self):
        """
        建立主问题模型的基本变量、目标、约束：
        1. 变量设置
        2. 目标函数设置
        3. 约束设置
        4. 模型求解参数设置
        """
        self.add_relaxed_sub_variables()  # 添加有效割的变量
        self.add_relaxed_sub_constrains()  # 添加有效割约束
        self.set_parameters()

    def solve(self):
        """
        迭代过程的建模和求解主题函数：
        1. 添加Benders割
        5. 求解并获取求解结果
        :return:
        """
        result = self.gen_model_result()
        return result

    def add_relaxed_sub_variables(self):
        """
        添加子问题的松弛变量
        """
        logger.info('添加变量：松弛子问题变量Z_dpT')
        self.vars[VarName.HAT_Z] = {(order, self.supplier, month): self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.HAT_Z}({order}_{self.supplier}_{month})'),
            vtype=gurobipy.GRB.CONTINUOUS)
            for item in self.items_list
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
            for month in self.data[SetName.ITEM_MONTH_DICT][item]}

        if self.add_binary:
            logger.info('添加变量：松弛子问题辅助变量nu_m\hat_t')
            self.vars[VarName.NU] = {(machine, month): self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.NU}({machine}_{month})'),
                vtype=gurobipy.GRB.BINARY)
                for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]
                for month in self.data[SetName.MACHINE_TIME_MONTH_DICT][machine]
            }

            logger.info('添加变量：松弛子问题辅助变量lambda_st')
            self.vars[VarName.LAMBDA] = {(self.supplier, date): self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.LAMBDA}({self.supplier}_{date})'),
                vtype=gurobipy.GRB.BINARY)
                for date in self.data[SetName.TIME_LIST]}

        logger.info('添加变量：松弛子问题辅助变量kappa_st')
        self.vars[VarName.KAPPA] = {(self.supplier, date): self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.KAPPA}({self.supplier}_{date})'),
            vtype=gurobipy.GRB.CONTINUOUS)
            for date in self.data[SetName.TIME_LIST]}

    def add_relaxed_sub_constrains(self):
        """
        添加子问题的松弛约束
        """
        # =============
        # Z_os\hat_t 需求生产总量
        # =============
        for item in self.items_list:
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                self.model.addConstr(
                    gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                      for month in self.data[SetName.ORDER_TIME_MONTH_DICT][order]) ==
                    self.data[ParaName.ORDER_QUANTITY_DICT][order] )

        # =============
        # 月生产上限
        # =============
        # supplimentary_2-1 对于订单而言，月产量 <= min(款日上限，实体供应商日上限,产线月上限)
        for item in self.items_list:
            item_max_occupy = self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]
            if self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item] < 0:
                item_max_occupy = float('inf')
            for month in self.data[SetName.ITEM_MONTH_DICT][item]:
                for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                    if (order, self.supplier, month) in self.vars[VarName.HAT_Z]:
                        self.model.addConstr(
                            self.vars[VarName.HAT_Z][order, self.supplier, month] <=
                            sum(min(item_max_occupy,
                                    self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][self.supplier].get(date,
                                                                                                              float('inf')))
                                for date in self.data[SetName.ORDER_TIME_DICT][order] if
                                date[:7] == month)
                        )
                        self.model.addConstr(self.vars[VarName.HAT_Z][order, self.supplier, month] <= sum(
                                             self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                 (machine, month), 0)
                                             for machine in set.intersection(
                                                 set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]),
                                                 set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]))
                                         ))

        # supplimentary_2-2 对于款式而言，月产量 <= min(款日上限，实体供应商日上限, 产线月产能)
        for item in self.items_list:
            item_max_occupy = self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]
            if self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item] < 0:
                item_max_occupy = float('inf')
            for month in self.data[SetName.ITEM_MONTH_DICT][item]:
                # supplimentary_2-2.1
                self.model.addConstr(
                    gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                      for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                      if (order, self.supplier, month) in self.vars[VarName.HAT_Z]) <=
                    sum(min(item_max_occupy,
                            self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][self.supplier].get(date,
                                                                                                      float('inf')))
                        for date in self.data[SetName.ITEM_TIME_DICT][item] if
                        date[:7] == month))
                # supplimentary_2-2.2
                self.model.addConstr(
                    gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                      for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                      if (order, self.supplier, month) in self.vars[VarName.HAT_Z]) <=
                    gurobipy.quicksum(
                        self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0)
                        for machine in set.intersection(
                                                 set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]),
                                                 set(self.data[SetName.MACHINE_BY_ITEM_DICT][item])))
                )

        # supplimentary_2-3 对于供应商而言，月产量 <= min(实体供应商日上限，sum(款式日上限)，产线月上限)
        for month in self.data[SetName.TIME_MONTH_LIST]:
            # supplimentary_2-3.1
            self.model.addConstr(gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                                   for item in
                                                   self.data[SetName.ITEM_BY_SUPPLIER_DICT][self.supplier]
                                                   for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                   if (order, self.supplier, month) in self.vars[VarName.HAT_Z]) <=
                                 gurobipy.quicksum(
                                     self.vars[VarName.KAPPA][self.supplier, date]
                                     for date in self.data[SetName.TIME_BY_MONTH_DICT][month] if
                                     date[:7] == month and (self.supplier, date) in self.vars[VarName.KAPPA])
                                 )
            if self.add_binary:
                # supplimentary_2-3.2
                self.model.addConstr(gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                                       for item in
                                                       self.data[SetName.ITEM_BY_SUPPLIER_DICT][self.supplier]
                                                       for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                       if
                                                       (order, self.supplier, month) in self.vars[VarName.HAT_Z]) <=
                                     gurobipy.quicksum(
                                         self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                             (machine, month), 0)
                                         * self.vars[VarName.NU][machine, month]
                                         for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]
                                         if (machine, month) in self.vars[VarName.NU]
                                     ))
            else:
                # supplimentary_2-3.2
                self.model.addConstr(gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                                       for item in
                                                       self.data[SetName.ITEM_BY_SUPPLIER_DICT][self.supplier]
                                                       for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                       if
                                                       (order, self.supplier, month) in self.vars[VarName.HAT_Z]) <=
                                     gurobipy.quicksum(
                                         self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                             (machine, month), 0)
                                         for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]
                                     ))

        # supplimentary_2-4 对于算法供应商而言，相同channel的算法供应商对应可生产需求月产量<= 月产能
        for channel in self.data[SetName.CHANNEL_LIST]:
            for month in self.data[SetName.TIME_MONTH_LIST]:
                if self.add_binary:
                    self.model.addConstr(gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                                           for item in
                                                           set.intersection(set(
                                                               self.data[SetName.ITEM_BY_SUPPLIER_DICT][
                                                                   self.supplier]),
                                                                            set(self.data[
                                                                                    SetName.ITEM_BY_CHANNEL_DICT][
                                                                                    channel]))
                                                           for order in
                                                           self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                           if (order, self.supplier, month) in self.vars[
                                                               VarName.HAT_Z]) <=
                                         gurobipy.quicksum(
                                             self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                 (machine, month), 0)
                                             * self.vars[VarName.NU][machine, month]
                                             for machine in set.intersection(
                                                 set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]),
                                                 set(self.data[SetName.MACHINE_BY_CHANNEL_DICT][channel]))
                                             if (machine, month) in self.vars[VarName.NU]
                                         ))
                else:
                    self.model.addConstr(gurobipy.quicksum(self.vars[VarName.HAT_Z][order, self.supplier, month]
                                                           for item in
                                                           set.intersection(set(
                                                               self.data[SetName.ITEM_BY_SUPPLIER_DICT][
                                                                   self.supplier]),
                                                                            set(self.data[
                                                                                    SetName.ITEM_BY_CHANNEL_DICT][
                                                                                    channel]))
                                                           for order in
                                                           self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                                           if (order, self.supplier, month) in self.vars[
                                                               VarName.HAT_Z]) <=
                                         sum(
                                             self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                                                 (machine, month), 0)
                                             for machine in set.intersection(
                                                 set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]),
                                                 set(self.data[SetName.MACHINE_BY_CHANNEL_DICT][channel]))
                                         ))

        if self.add_binary:
            # =============
            # nu_m\hat_t 定义用约束，注：由于z_os\hat t已经决策到了月维度，所以不需要该项

            for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][self.supplier]:
                for month in self.data[SetName.MACHINE_TIME_MONTH_DICT][machine]:
                    # 内含有可在machine生产且生产日期包括month的order的款式列表
                    item_list = []
                    for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(self.supplier, []):
                        for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                            if month in self.data[SetName.ORDER_TIME_MONTH_DICT][order]:
                                if machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]:
                                    item_list.append(item)
                                    break
                    # supplimentary_2-5.1
                    self.model.addConstr(
                        self.vars[VarName.NU][machine, month] <=
                        gurobipy.quicksum(self.vars[VarName.ALPHA][item, self.supplier] for item in item_list))
                    # 有效不等式，不会去掉最优解 # supplimentary_2-5.2
                    for item in item_list:
                        self.model.addConstr(
                            self.vars[VarName.NU][machine, month] >=
                            self.vars[VarName.ALPHA][item, self.supplier])
            # =============
            # lambda_st 定义用约束
            # =============

            for date in self.data[SetName.TIME_LIST]:
                # 内含有可在physical_supplier生产且生产日期包括date的款式列表
                item_list = []
                for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(self.supplier, []):
                    if date in self.data[SetName.ITEM_TIME_DICT][item]:
                        item_list.append(item)
                # supplimentary_2-6.1
                self.model.addConstr(
                    self.vars[VarName.LAMBDA][self.supplier, date] <=
                    gurobipy.quicksum(self.vars[VarName.ALPHA][item, self.supplier] for item in item_list))
                # supplimentary_2-6.2
                for item in item_list:
                    self.model.addConstr(
                        self.vars[VarName.LAMBDA][self.supplier, date] >=
                        self.vars[VarName.ALPHA][item, self.supplier])
        # =============
        # kappa_st 定义用约束
        # =============

        item_max_occupy_dict = {}
        for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(self.supplier, []):
            if self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item] < 0:
                item_max_occupy_dict[item] = float('inf')
            else:
                item_max_occupy_dict[item] = self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]
        for date in self.data[SetName.TIME_LIST]:
            # 内含有可在physical_supplier生产且生产日期包括date的款式列表
            item_list = []
            for item in self.items_list:
                if date in self.data[SetName.ITEM_TIME_DICT][item]:
                    item_list.append(item)

            # 内含有可在physical_supplier生产且生产日期包括date的款式列表
            self.model.addConstr(
                self.vars[VarName.KAPPA][self.supplier, date] <= \
                # self.vars[DAOptVarName.LAMBDA][supplier, date] * \
                self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][self.supplier].get(date, self.data[
                    ParaName.MAX_QUANTITY])
            )
            self.model.addConstr(
                self.vars[VarName.KAPPA][self.supplier, date] <=
                sum(item_max_occupy_dict[item] for item in item_list))

            # kappa-3
            if len(item_list) == 0:
                self.model.addConstr(
                    self.vars[VarName.KAPPA][self.supplier, date] <= 0
                )

    def set_parameters(self):
        """
        设置模型求解的参数
        :return:
        """
        self.model.setParam(gurobipy.GRB.Param.TimeLimit, 3600)  # 求解时间上限
        self.model.setParam(gurobipy.GRB.Param.MIPGap, 0.001)  # 给定停止的Gap
        # self.model.setParam(gurobipy.GRB.Param.OutputFlag, 0)

    def gen_model_result(self):
        """
        模型求解，并获取求解结果
        :return:
        """
        self.model.optimize()

        if self.model.Status in [gurobipy.GRB.Status.INFEASIBLE, gurobipy.GRB.Status.UNBOUNDED]:
            self.model.computeIIS()
            error_info = '!!! 没有可行解 !!!'
            logger.error(error_info)
            raise Exception(error_info)

        # 获取求解结果
        self.obj_val = self.model.objVal
        # 款分配至实体供应商结果
        order_supplier_month = dict()

        for (order, supplier, month), var in self.vars[VarName.HAT_Z].items():
            value = var.x
            if value > 0.001:
                order_supplier_month[order, supplier, month] = value
                print(str(self.data[ParaName.ORDER_ITEM_DICT][order]) + "," + str(order) + "," + str(supplier) + "," + str(month) + ":" + str(value))
        for (supplier, date), var in self.vars[VarName.KAPPA].items():
            value = var.x
            if value > 0.001:
                print(str(supplier) + "," + str(date) +":"+ str(value))
        return order_supplier_month
