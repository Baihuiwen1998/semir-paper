import itertools
import logging
import gurobipy

from constant.config import *
from util.header import *
from util.util import var_name_regularizer

logger = logging.getLogger(__name__)


class FullModelBeta:

    def __init__(self, data):

        self.result = None
        self.data = data
        self.model = gurobipy.Model()
        self.vars = dict()

    def construct_model(self):
        """
        建立模型的基本变量、目标、约束：
        1. 变量设置
        2. 目标函数设置
        3. 约束设置
        4. 模型求解参数设置
        """
        self.add_variables()
        self.add_objective()
        self.add_constrains()
        self.set_parameters()

    def add_variables(self):
        """
        给模型添加变量
        :return:
        """
        # =============
        # 款相关变量
        # =============
        logger.info('添加变量：订单生产变量beta')
        self.vars[VarName.BETA] = {order: self.model.addVar(vtype=gurobipy.GRB.BINARY,
                                                            name=var_name_regularizer(
                                                                f'V_{VarName.BETA}({order})'),
                                                            column=None, obj=0.0, lb=0.0, ub=1.0)
                                   for order in self.data[SetName.ORDER_LIST]}
        logger.info('添加变量：订单生产变量gamma')
        self.vars[VarName.GAMMA] = {(order, machine): self.model.addVar(vtype=gurobipy.GRB.BINARY,
                                                                        name=var_name_regularizer(
                                                                            f'V_{VarName.GAMMA}({order}_{machine})'),
                                                                        column=None, obj=0.0, lb=0.0, ub=1.0)
                                    for item in self.data[SetName.ITEM_LIST]
                                    for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                    for machine in self.data[SetName.MACHINE_BY_ITEM_DICT][item]}

        # =============
        # 订单生产相关变量
        # =============
        logger.info('添加变量：订单生产变量z')
        self.vars[VarName.Z] = {(order, machine, date): self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.Z}({order}_{machine}_{date})'),
            vtype=gurobipy.GRB.INTEGER)
            for item in self.data[SetName.ITEM_LIST]
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
            for machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]
            for date in self.data[SetName.ORDER_TIME_DICT][order]
        }

        # =============
        # 产能规划相关变量
        # =============
        logger.info('添加变量：产能规划达成率相关变量')
        # 产能规划达成率
        self.vars[VarName.SUPPLIER_CAPACITY_RATIO] = {supplier: self.model.addVar(
            name=var_name_regularizer(f'V_{VarName.SUPPLIER_CAPACITY_RATIO}_{supplier}'),
            vtype=gurobipy.GRB.CONTINUOUS, lb=0)
            for supplier in self.data[SetName.SUPPLIER_LIST]
        }
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_AVERAGE_OBJ]:
            # 供应商产能规划达成率与池内平均规划率的差值
            self.vars[VarName.SUPPLIER_CAPACITY_RATIO_DELTA] = {supplier: self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.SUPPLIER_CAPACITY_RATIO_DELTA}_{supplier}'),
                vtype=gurobipy.GRB.CONTINUOUS, lb=0)
                for supplier in self.data[SetName.SUPPLIER_LIST]
            }

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_LADDEL_OBJ]:
            # 池内平均产能规划达成率
            self.vars[VarName.POOL_CAPACITY_RATIO_AVG] = {pool: self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.POOL_CAPACITY_RATIO_AVG}_{pool}'),
                vtype=gurobipy.GRB.CONTINUOUS, lb=0)
                for pool in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool]) > 0
            }
            # 供应商池子不符合阶梯性的达成率部分, pool_1（等级更高）相比pool_2平均达成率低的部分
            self.vars[VarName.POOLS_CAPACITY_RATIO_DELTA] = {(pool_1, pool_2): self.model.addVar(
                name=var_name_regularizer(f'V_{VarName.POOLS_CAPACITY_RATIO_DELTA}_{pool_1}_{pool_2}'),
                vtype=gurobipy.GRB.CONTINUOUS, lb=0)
                for pool_1 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                for pool_2 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_1]) > 0
                   and len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_2]) > 0
                   and ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[pool_1] < ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[
                       pool_2]
            }

    def add_objective(self):
        """
        给模型设置目标函数
        :return:
        """
        # =============
        # 款式内订单延误
        # =============
        logger.info('模型添加优化目标：订单延误最少')
        order_delay_obj = gurobipy.quicksum(
            (self.data[ObjCoeffName.ORDER_DELAY_BASE_PUNISH]
             + self.data[ObjCoeffName.ORDER_DELAY_PUNISH] * self.data[ParaName.ORDER_QUANTITY_DICT][order]) *
            (1 - self.vars[VarName.BETA][order])
            for order in self.data[SetName.ORDER_LIST]
        )
        self.data[ObjName.ORDER_DELAY_OBJ] = order_delay_obj

        obj = order_delay_obj
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_AVERAGE_OBJ]:
            # =============
            # 产能规划达成率
            # =============
            logger.info('模型添加优化目标：池内实体供应商产能规划达成率均衡')
            capacity_average_obj = gurobipy.quicksum(
                self.data[ObjCoeffName.CAPACITY_AVERAGE_PUNISH]
                * self.vars[VarName.SUPPLIER_CAPACITY_RATIO_DELTA][supplier]
                for supplier in self.data[SetName.SUPPLIER_LIST]
            )
            self.data[ObjName.CAPACITY_AVERAGE_OBJ] = capacity_average_obj

            obj += capacity_average_obj

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_LADDEL_OBJ]:
            logger.info('模型添加优化目标：池子内产能规划达成率均值呈现阶梯')
            capacity_ladder_obj = self.data[ObjCoeffName.SUPPLIER_LADDER_PUNISH] * gurobipy.quicksum(
                self.vars[VarName.POOLS_CAPACITY_RATIO_DELTA][pool_1, pool_2]
                for pool_1 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                for pool_2 in self.data[SetName.SUPPLIER_BY_POOL_DICT]
                if len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_1]) > 0 and \
                len(self.data[SetName.SUPPLIER_BY_POOL_DICT][pool_2]) > 0 and \
                ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[pool_1] < ImportanceMark.ALL_IMPORTANCE_LEVEL_DICT[pool_2])
            self.data[ObjName.CAPACITY_LADDER_OBJ] = capacity_ladder_obj
            obj += capacity_ladder_obj

        self.model.setObjective(obj, gurobipy.GRB.MINIMIZE)

    def add_constrains(self):
        """
        给模型添加约束函数
        :return:
        """
        # =============
        # 订单生产约束
        # =============
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.ITEM_MULTI_SUPPLIER]:
            logger.info('模型添加约束：订单只能在一个实体供应商内的产线上进行生产')
            for item in self.data[SetName.ITEM_LIST]:
                for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                    for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]:
                        for machine_1 in set.intersection(set(self.data[SetName.MACHINE_BY_ITEM_DICT][item]),
                                                          set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier])):
                            for machine_2 in self.data[SetName.MACHINE_BY_ITEM_DICT][item]:
                                if self.data[ParaName.MACHINE_SUPPLIER_DICT][machine_2] != supplier:
                                    self.model.addConstr(
                                        self.vars[VarName.GAMMA][order, machine_1] + self.vars[VarName.GAMMA][
                                            order, machine_2]
                                        <= 1,
                                        name=f"only_produced_in_one_supplier_{order}_{machine_1}_{machine_2}")
        else:
            logger.info('模型添加约束：单款内订单只能在一个实体供应商内的产线上进行生产')
            for item in self.data[SetName.ITEM_LIST]:
                for order_1 in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                    for order_2 in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                        for supplier in self.data[SetName.SUPPLIER_BY_ITEM_DICT][item]:
                            for machine_1 in set.intersection(set(self.data[SetName.MACHINE_BY_ITEM_DICT][item]),
                                                              set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][
                                                                      supplier])):
                                for machine_2 in self.data[SetName.MACHINE_BY_ITEM_DICT][item]:
                                    if self.data[ParaName.MACHINE_SUPPLIER_DICT][machine_2] != supplier:
                                        self.model.addConstr(
                                            self.vars[VarName.GAMMA][order_1, machine_1] + self.vars[VarName.GAMMA][
                                                order_2, machine_2]
                                            <= 1,
                                            name=f"only_produced_in_one_supplier_{order_1}_{order_2}_{machine_1}_{machine_2}")

        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.CAPACITY_AVERAGE_OBJ]:
            # =============
            # 产能规划达成率约束
            # =============
            logger.info('模型添加约束：产能规划达成率约束')
            for supplier in self.data[SetName.SUPPLIER_LIST]:
                self.model.addConstr(
                    self.vars[VarName.SUPPLIER_CAPACITY_RATIO][supplier] ==
                    gurobipy.quicksum(
                        self.vars[VarName.Z][order, machine, date] for item in self.data[SetName.ITEM_LIST]
                        for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                        for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                        set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]))
                        for date in self.data[SetName.ORDER_TIME_DICT][order]
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
                        gurobipy.quicksum(
                            self.vars[VarName.Z][order, machine, date] for item in self.data[SetName.ITEM_LIST]
                            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                            for supplier in self.data[SetName.SUPPLIER_BY_POOL_DICT][pool]
                            for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                            set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]))
                            for date in self.data[SetName.ORDER_TIME_DICT][order]
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

        # =============
        # 需求生产约束
        # =============
        logger.info('模型添加约束：需求量生产')
        for order in self.data[SetName.ORDER_LIST]:
            self.model.addConstr(gurobipy.quicksum(
                self.vars[VarName.Z][order, machine, date]
                for machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]
                for date in self.data[SetName.ORDER_TIME_DICT][order]
            ) == self.data[ParaName.ORDER_QUANTITY_DICT][order] * self.vars[VarName.BETA][order],
                                 name=f"order_{order}_production_quantity"
                                 )

        logger.info('模型添加约束：同款内订单的生产与否相同')
        for item in self.data[SetName.ITEM_LIST]:
            for order_pairs in itertools.combinations(self.data[SetName.ORDER_BY_ITEM_DICT][item], 2):
                self.model.addConstr(self.vars[VarName.BETA][order_pairs[0]] == \
                                     self.vars[VarName.BETA][order_pairs[1]],
                                     name=f"item_{item}_order_pair_{order_pairs[0]}_{order_pairs[1]}_production"
                                     )
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                for machine in self.data[SetName.MACHINE_BY_ITEM_DICT][item]:
                    self.model.addConstr(self.vars[VarName.GAMMA][order, machine]
                                         <= self.vars[VarName.BETA][order],
                                         name=f"order_{order}_machine_{machine}_if_production"
                                         )

        logger.info('模型添加约束：订单在机器上的产量变量z与变量gamma的关系')
        for item in self.data[SetName.ITEM_LIST]:
            for machine in self.data[SetName.MACHINE_BY_ITEM_DICT][item]:
                for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                    self.model.addConstr(gurobipy.quicksum(
                        self.vars[VarName.Z][order, machine, date]
                        for date in self.data[SetName.ORDER_TIME_DICT][order]
                    ) <= self.data[ParaName.ORDER_QUANTITY_DICT][order] * self.vars[VarName.GAMMA][order, machine],
                                         name=f"order_{order}_machine_{machine}_production_quantity"
                                         )

        # logger.info('模型添加约束：超出每日最优线天量的计算')
        # for item in self.sub_data_by_iteration[DAOptSubIterationDataName.ITEM_ASSIGNMENT_LIST]:
        #     for demand in self.data[DAOptSetName.DEMAND_BY_ITEM_DICT][item]:
        #         for date in self.data[DAOptSetName.DEMAND_TIME_DICT][demand]:
        #             if self.data[DAOptParaName.DEMAND_OPTIMAL_QUANTITY_DICT][demand] != -1:
        #                 self.model.addConstr(
        #                     self.vars[DAOptVarName.X_OVER][demand, date] >= self.vars[DAOptVarName.X][demand, date] -
        #                     self.data[DAOptParaName.DEMAND_OPTIMAL_QUANTITY_DICT][demand],
        #                     name=f"optimal_quantity_of_demand_{demand}_on_{date}"
        #                 )

        # =============
        # 款式日生产上限
        # =============
        # if not ParamsMark.ALL_PARAMS_DICT[ParamsMark.ITEM_MULTI_SUPPLIER]:
        logger.info('模型添加约束：对款的单日生产上限限制')
        for item in self.data[SetName.ITEM_LIST]:
            for date in self.data[SetName.ITEM_TIME_DICT][item]:
                self.model.addConstr(gurobipy.quicksum(
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
                if self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date] >= 0 and date in self.data[
                    SetName.TIME_LIST]:
                    self.model.addConstr(
                        gurobipy.quicksum(
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
                self.model.addConstr(gurobipy.quicksum(
                    self.vars[VarName.Z].get((order, machine, date), 0)
                    for order in self.data[SetName.ORDER_BY_MACHINE_DICT][machine]
                    for date in self.data[SetName.TIME_BY_MONTH_DICT][month]
                    if month in self.data[SetName.TIME_BY_MONTH_DICT] and (order, machine, date) in
                    self.vars[VarName.Z]
                ) <= self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0),
                                     name=f"demand_capacity_limit_for_machine_{machine}_in_{month}"
                                     )

    def set_parameters(self):
        """
        设置模型求解的参数
        :return:
        """
        self.model.setParam(gurobipy.GRB.Param.MIPGap, ParamsMark.ALL_PARAMS_DICT[ParamsMark.MIP_GAP])  # 给定停止的Gap
        self.model.setParam(gurobipy.GRB.Param.TimeLimit, ParamsMark.ALL_PARAMS_DICT[ParamsMark.MAX_RUNTIME])  # 求解时间上限

    def gen_model_result(self):
        """
        模型求解，并获取求解结果
        :return:
        """
        logger.info('------ 求解开始 ------')
        self.model.optimize()
        logger.info('------ 求解结束 ------')

        if self.model.Status in [gurobipy.GRB.Status.INFEASIBLE, gurobipy.GRB.Status.UNBOUNDED]:
            # self.model.computeIIS()
            # self.model.write(self.file_dir + self.name + '_model.ilp')
            # error_info = '!!! 没有可行解 !!!'
            # logger.error(error_info)
            # raise Exception(error_info)
            return False

        # 获取求解结果

        order_machine_date_result = dict()
        for (order, machine, date), var in self.vars[VarName.Z].items():
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

        # 订单生产结果
        order_production_result = dict()
        for order, var in self.vars[VarName.BETA].items():
            value = var.x
            if value > 0.001:
                order_production_result[order] = value
        self.result[ResultName.ORDER_PRODUCTION] = order_production_result
        order_machine_result = dict()
        item_supplier_dict = dict()
        for item in self.data[SetName.ITEM_LIST]:
            item_supplier_dict[item] = set()
        for (order, machine), var in self.vars[VarName.GAMMA].items():
            value = var.x
            if value > 0.001:
                order_machine_result[order, machine] = value
                item_supplier_dict[self.data[ParaName.ORDER_ITEM_DICT][order]].add(self.data[ParaName.MACHINE_SUPPLIER_DICT][machine])

        return self.result
