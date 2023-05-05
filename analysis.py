# -*- coding: utf-8 -*-
# @author: baihuiwen
# @email: bhw21@mails.tsinghua.edu.cn
# @date: 2022/03/24
import logging
from config import *
from util.header import ParamsMark

logger = logging.getLogger(__name__)


class ModelAnalysis:

    def __init__(self, data, result):
        self.data = data
        self.result = result

    def analysis_result(self, optimal):
        """
        主函数
        """
        self.optimal = optimal
        is_correct = self.correctness_analyse()
        logger.info('结果检查完成')
        return is_correct

    def correctness_analyse(self):
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] > 0 and self.optimal:
            result = dict()
            item_supplier = dict()
            order_machine_date = dict()
            for supplier in self.result[LBBDResultName.SUB_RESULT]:
                item_supplier.update(self.result[LBBDResultName.SUB_RESULT][supplier][ResultName.ITEM_SUPPLIER])
                order_machine_date.update(self.result[LBBDResultName.SUB_RESULT][supplier][ResultName.ORDER_MACHINE_DATE])
            result[ResultName.ITEM_SUPPLIER] = item_supplier
            result[ResultName.ORDER_MACHINE_DATE] = order_machine_date
            if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_POOL]:
                result[ResultName.POOL_CAPACITY_RATIO_AVG] = self.result[LBBDResultName.MASTER_RESULT][
                    ResultName.POOL_CAPACITY_RATIO_AVG]
            result[ResultName.SUPPLIER_CAPACITY_RATIO] = self.result[LBBDResultName.MASTER_RESULT][
                ResultName.SUPPLIER_CAPACITY_RATIO]
            self.result = result
        # 生产款式内需求的产量
        produced_item_set = set()
        produced_order_set = set()
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.MILP_MODEL] == 0 or ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] > 0:
            for (item, supplier) in self.result[ResultName.ITEM_SUPPLIER]:
                produced_item_set.add(item)
                for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                    produced_order_set.add(order)
                    sum_order_production = sum(
                        self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                        for machine in set.intersection(
                            set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
                            set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]))
                        for date in self.data[SetName.ORDER_TIME_DICT][order])
                    if sum_order_production < self.data[ParaName.ORDER_QUANTITY_DICT][order] - 0.001 or sum_order_production > self.data[ParaName.ORDER_QUANTITY_DICT][order] + 0.001:
                        logger.info(
                            f"订单_{order}_的产量_{sum_order_production}不足需求量_{self.data[ParaName.ORDER_QUANTITY_DICT][order]}")
                        return False
        else:
            for order in self.result[ResultName.ORDER_PRODUCTION]:
                produced_order_set.add(order)
                produced_item_set.add(self.data[ParaName.ORDER_ITEM_DICT][order])
                sum_order_production = sum(
                    self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                    for machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]
                    for date in self.data[SetName.ORDER_TIME_DICT][order])
                if sum_order_production < self.data[ParaName.ORDER_QUANTITY_DICT][
                    order] - 0.001 or sum_order_production > self.data[ParaName.ORDER_QUANTITY_DICT][order] + 0.001:
                    logger.info(
                        f"订单_{order}_的产量_{sum_order_production}不足需求量_{self.data[ParaName.ORDER_QUANTITY_DICT][order]}")
                    return False
        logger.info(
            f"总款式_{len(self.data[SetName.ITEM_LIST])}_中完成款式产量_{len(produced_item_set)}")
        logger.info(
            f"总订单_{len(self.data[SetName.ORDER_LIST])}_中完成订单产量_{len(produced_order_set)}")

        # 不生产款式的产量
        for item in set(self.data[SetName.ITEM_LIST]) - produced_item_set:
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                sum_order_production = sum(
                    self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                    for machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]
                    for date in self.data[SetName.ORDER_TIME_DICT][order])
                if sum_order_production != 0:
                    logger.info(f"不开展生产的订单_{order}_的产量_{sum_order_production}超过0")
                    return False
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_ITEM_MAX]:
            # 款式日产能上限
            for item in self.data[SetName.ITEM_LIST]:
                if self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item] > 0:
                    for date in self.data[SetName.ITEM_TIME_DICT][item]:
                        sum_item_date_production = \
                            sum(self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0) for order in
                                self.data[SetName.ORDER_BY_ITEM_DICT][item]
                                for machine in self.data[SetName.MACHINE_BY_ORDER_DICT][order]
                                )
                        if sum_item_date_production > self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]:
                            logger.info(
                                f"{date}_款式_{item}_的产量_{sum_item_date_production}_超过日上限_{self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]}")
                            return False

        # 供应商日产能上限
        for supplier in self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT]:
            for date in self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier]:
                if self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date] >= 0:
                    sum_supplier_date_production = \
                        sum(self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                            for item in self.data[SetName.ITEM_BY_SUPPLIER_DICT].get(supplier, [])
                            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]
                            for machine in set.intersection(set(self.data[SetName.MACHINE_BY_ORDER_DICT][order]),
                                                            set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]))
                            )
                    if sum_supplier_date_production > self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][
                        supplier][date]:
                        logger.info(
                            f"{date}_供应商_{supplier}_的产量_{sum_supplier_date_production}_超过日上限_{self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date]}")
                        for (o, m, d) in self.result[ResultName.ORDER_MACHINE_DATE]:
                            if date == d and (m in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]):
                                logger.info(
                                    f"{date}_供应商_{supplier}_的机器_{m}_生产订单_{o}_产量_{self.result[ResultName.ORDER_MACHINE_DATE][o, m, d]}")

                        return False

        # 产线月产能上限
        for machine in self.data[SetName.MACHINE_LIST]:
            for month in self.data[SetName.MACHINE_TIME_MONTH_DICT].get(machine, []):
                sum_machine_month_production = sum(
                    self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                    for order in self.data[SetName.ORDER_BY_MACHINE_DICT][machine]
                    for date in self.data[SetName.TIME_BY_MONTH_DICT][month]
                    if month in self.data[SetName.TIME_BY_MONTH_DICT]
                )
                if sum_machine_month_production > self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                        (machine, month), 0):
                    logger.info(
                        f"{month}_产线_{machine}_的产量_{sum_machine_month_production}_超过月上限_{self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0)}")
                    return False
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.IS_POOL]:
            # 池内的最大和最小产能规划达成率 和平均达成率
            for pool in self.result[ResultName.POOL_CAPACITY_RATIO_AVG]:
                logger.info(f"{pool}_的平均产能规划达成率为_{format(self.result[ResultName.POOL_CAPACITY_RATIO_AVG][pool], '.4f')}")

        return True
