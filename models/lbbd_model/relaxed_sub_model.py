import logging
import gurobipy as gp
from config import *
from util.util import var_name_regularizer

logger = logging.getLogger(__name__)


class RelaxedSubModel:
    """
    建立子问题模型
    """

    def __init__(self, data, sub_data, mis_size, relax_mode):
        self.supplier = sub_data[LBBDSubDataName.SUPPLIER]
        self.data = data
        self.model = gp.Model()
        self.vars = dict()
        self.sub_data = sub_data  # 子问题迭代过程所需数据
        self.is_feasible = None
        self.result = None
        self.mis_size = mis_size
        self.relax_mode = relax_mode  # 1-lifting  2-调整alpha变量 # 3-允许有款式不生产

    def construct(self):
        """
        建模的主体函数，包含以下几部分：
        1. 变量设置
        2. 目标函数设置
        3. 约束设置
        :return:
        """
        self.add_variables()
        self.add_objective()
        self.add_constrains()

    def add_variables(self):
        """
        给模型添加变量
        :return:
        """
        # =============
        # 订单生产相关变量
        # =============
        # logger.info('添加变量：订单生产变量alpha')
        self.vars[VarName.ALPHA] = {item: self.model.addVar(vtype=gp.GRB.BINARY,
                                                            name=var_name_regularizer(
                                                                f'V_{VarName.ALPHA}({item})'),
                                                            column=None, obj=0.0, lb=0.0, ub=1.0)
                                    for item in self.sub_data[LBBDSubDataName.ITEM_LIST]}

        # logger.info('添加变量：订单生产变量z')
        self.vars[VarName.Z] = {(order, machine, date): self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.Z}({order}_{machine}_{date})'),
            vtype=gp.GRB.INTEGER)
            for item in self.sub_data[LBBDSubDataName.ITEM_LIST]
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
            for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                            set(self.sub_data[LBBDSubDataName.MACHINE_LIST]))
            for date in self.data[SetName.ORDER_TIME_DICT][order]
        }

    def add_objective(self):

        if self.relax_mode == 3:
            item_product_opt_obj = -100 * gp.quicksum(self.vars[VarName.ALPHA][item] for item in
                                                            self.sub_data[LBBDSubDataName.ITEM_LIST])
            self.model.setObjective(item_product_opt_obj, gp.GRB.MINIMIZE)
        else:
            self.model.setObjective(0, gp.GRB.MINIMIZE)

    def add_constrains(self):
        """
        给模型添加约束函数，约束按照不同类型可以分功能添加
        :return:
        """
        # =============
        # 款式生产
        # =============
        if self.relax_mode == 1:
            self.model.addConstr(
                gp.quicksum(self.vars[VarName.ALPHA][item] for item in
                                  self.sub_data[LBBDSubDataName.ITEM_LIST]) == self.mis_size)

        # =============
        # 需求生产约束
        # =============
        # logger.info('模型添加约束：需求量生产')
        for item in self.sub_data[LBBDSubDataName.ITEM_LIST]:
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                self.model.addConstr(gp.quicksum(
                    self.vars[VarName.Z][order, machine, date]
                    for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                    set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT].get(
                                                        self.supplier, [])))
                    for date in self.data[SetName.ORDER_TIME_DICT][order]
                ) == self.data[ParaName.ORDER_QUANTITY_DICT][order] * self.vars[VarName.ALPHA][item],
                                     name=f"order_{order}_production_quantity"
                                     )
        # =============
        # 款式日生产上限
        # =============
        # logger.info('模型添加约束：对款的单日生产上限限制')
        for item in self.sub_data[LBBDSubDataName.ITEM_LIST]:
            for date in self.data[SetName.ITEM_TIME_DICT][item]:
                self.model.addConstr(gp.quicksum(
                    self.vars[VarName.Z].get((order, machine, date), 0) for order in
                    self.data[SetName.ORDER_BY_ITEM_DICT][item]
                    for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                    set(self.sub_data[LBBDSubDataName.MACHINE_LIST]))
                ) <= self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item],
                                     name=f"production_limit_of_item_{item}_on_{date}"
                                     )

        # =============
        # 实体供应商产能日上限
        # =============
        # logger.info('模型添加约束：实体供应商产能日上限')
        for date in self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][self.supplier]:
            if self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][self.supplier][date] >= 0 and date in \
                    self.data[SetName.TIME_LIST]:
                self.model.addConstr(
                    gp.quicksum(
                        self.vars[VarName.Z][order, machine, date]
                        for item in self.sub_data[LBBDSubDataName.ITEM_LIST]
                        for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                        for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                        set(self.sub_data[LBBDSubDataName.MACHINE_LIST]))
                        if (order, machine, date) in self.vars[VarName.Z]
                    ) <= self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][self.supplier][date],
                    name=f"production_limit_of_supplier_{self.supplier}'s_on_{date}"
                )

        # =============
        # 产线产能月上限
        # =============
        # logger.info('模型添加约束：产线产能月上限')
        for machine in self.sub_data[LBBDSubDataName.MACHINE_LIST]:
            for month in self.data[SetName.MACHINE_TIME_MONTH_DICT].get(machine, []):
                self.model.addConstr(gp.quicksum(
                    self.vars[VarName.Z].get((order, machine, date), 0)
                    for order in set.intersection(set(self.sub_data[LBBDSubDataName.ORDER_LIST]),
                                                  set(self.data[SetName.ORDER_BY_MACHINE_DICT][machine]))
                    for date in self.data[SetName.TIME_BY_MONTH_DICT][month]
                    if month in self.data[SetName.TIME_BY_MONTH_DICT] and (order, machine, date) in
                    self.vars[VarName.Z]
                ) <= self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0),
                                     name=f"demand_capacity_limit_for_machine_{machine}_in_{month}")

    def add_alpha_equals_1_constrains(self, item):
        self.model.addConstr(self.vars[VarName.ALPHA][item] == 1, name=f"item_{item}_production")

    def solve(self, mode):
        """
        求解子问题
        mode = 1时，只对模型进行检验是否可行，不求最优解
        mode = 2时，对模型求最优解
        mode = 3时，求解模型的松弛解

        4. 模型求解参数设置
        5. 求解并获取求解结果
        """

        self.set_model_parameters(mode)
        self.gen_model_result(mode)
        if mode == 1:
            return self.is_feasible
        elif mode == 2:
            return self.result

    def set_model_parameters(self, mode):
        """
        设置模型求解的参数
        :return:
        """
        if mode == 1:
            self.model.setParam(gp.GRB.Param.OutputFlag, 0)
            # 判断模型是否可行，所以只要找到一个可行解就停止
            self.model.setParam(gp.GRB.Param.SolutionLimit, 1)
        elif mode == 2:
            # self.model.setParam(gp.GRB.Param.OutputFlag, 1)
            # 求最优解
            self.model.setParam(gp.GRB.Param.SolutionLimit, 2000000000)
        elif mode == 3:
            self.model.setParam(gp.GRB.Param.SolutionLimit, 2000000000)

    def gen_model_result(self, mode):
        # logger.info('求解供应商{}子问题'.format(self.supplier))
        self.model.optimize()
        if self.model.Status in [gp.GRB.Status.INFEASIBLE, gp.GRB.Status.UNBOUNDED]:
            # error_info = '{} !!! 子问题没有可行解 !!!'.format(self.supplier)
            # logger.info(error_info)
            self.is_feasible = False
        else:
            if mode == 1:
                # error_info = '{} !!! 子问题可行 !!!'.format(self.supplier)
                self.is_feasible = True
                # 获取求解结果
                order_machine_date_result = dict()
                for (order, machine, date), var in self.vars[VarName.Z].items():
                    value = var.x
                    if value > 0.001:
                        order_machine_date_result[order, machine, date] = value
                return self.is_feasible
            elif mode == 2:
                # 获取求解结果
                order_machine_date_result = dict()
                for (order, machine, date), var in self.vars[VarName.Z].items():
                    value = var.x
                    if value > 0.001:
                        order_machine_date_result[order, machine, date] = value
                item_supplier = dict()
                for item, var in self.vars[VarName.ALPHA].items():
                    value = var.x
                    if value > 0.001:
                        item_supplier[item, self.supplier] = 1
                self.result = {
                    ResultName.ORDER_MACHINE_DATE: order_machine_date_result,
                    ResultName.ITEM_SUPPLIER: item_supplier
                }

                return self.result
