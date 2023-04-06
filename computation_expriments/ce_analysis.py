# -*- coding: utf-8 -*-
# @author: baihuiwen
# @email: bhw21@mails.tsinghua.edu.cn
# @date: 2022/03/24
import copy
import logging
from constant.config import *

logger = logging.getLogger(__name__)


class ModelAnalysis:

    def __init__(self, data, result, mode):
        self.data = data
        self.result = result
        self.mode = mode  # 0-整体模型  # 1-lbbd模型

    def analysis_result(self):
        """
        主函数
        """

        is_correct, finished_rate_list = self.correctness_analyse()
        logger.info('结果检查完成')
        return is_correct, finished_rate_list

    def correctness_analyse(self):
        finished_rate_list = list()
        if self.mode == 1:
            result = dict()
            item_supplier = dict()
            order_machine_date = dict()
            for supplier in self.result[LBBDResultName.SUB_RESULT]:
                item_supplier.update(self.result[LBBDResultName.SUB_RESULT][supplier][ResultName.ITEM_SUPPLIER])
                order_machine_date.update(self.result[LBBDResultName.SUB_RESULT][supplier][ResultName.ORDER_MACHINE_DATE])
            result[ResultName.ITEM_SUPPLIER] = item_supplier
            result[ResultName.ORDER_MACHINE_DATE] = order_machine_date
            result[ResultName.POOL_CAPACITY_RATIO_UB] = self.result[LBBDResultName.MASTER_RESULT][
                ResultName.POOL_CAPACITY_RATIO_UB]
            result[ResultName.POOL_CAPACITY_RATIO_LB] = self.result[LBBDResultName.MASTER_RESULT][
                ResultName.POOL_CAPACITY_RATIO_LB]
            result[ResultName.SUPPLIER_CAPACITY_RATIO] = self.result[LBBDResultName.MASTER_RESULT][
                ResultName.SUPPLIER_CAPACITY_RATIO]
            self.result = result
        # 生产款式内需求的产量
        produced_item_set = set()
        produced_order_set = set()
        for (item, supplier) in self.result[ResultName.ITEM_SUPPLIER]:
            produced_item_set.add(item)
            for order in self.data[DAOptSetName.ORDER_BY_ITEM_DICT][item]:
                produced_order_set.add(order)
                sum_order_production = sum(
                    self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                    for machine in set.intersection(
                        set(self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
                        set(self.data[DAOptSetName.MACHINE_BY_ORDER_DICT][order]))
                    for date in self.data[DAOptSetName.ORDER_TIME_DICT][order])
                if sum_order_production < self.data[ParaName.ORDER_QUANTITY_DICT][order] - 0.001 or sum_order_production > self.data[ParaName.ORDER_QUANTITY_DICT][order] + 0.001:
                    logger.info(
                        f"订单_{order}_的产量_{sum_order_production}不足需求量_{self.data[ParaName.ORDER_QUANTITY_DICT][order]}")
                    return False, None
        logger.info(
            f"总款式_{len(self.data[DAOptSetName.ITEM_LIST])}_中完成款式产量_{len(produced_item_set)}")
        logger.info(
            f"总订单_{len(self.data[DAOptSetName.ORDER_LIST])}_中完成订单产量_{len(produced_order_set)}")
        finished_rate_list.append(len(produced_item_set))
        finished_rate_list.append(len(produced_order_set))
        # 不生产款式的产量
        for item in set(self.data[DAOptSetName.ITEM_LIST]) - produced_item_set:
            for order in self.data[DAOptSetName.ORDER_BY_ITEM_DICT][item]:
                sum_order_production = sum(
                    self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                    for machine in self.data[DAOptSetName.MACHINE_BY_ORDER_DICT][order]
                    for date in self.data[DAOptSetName.ORDER_TIME_DICT][order])
                if sum_order_production != 0:
                    logger.info(f"不开展生产的订单_{order}_的产量_{sum_order_production}超过0")
                    return False, None

        # 款式日产能上限
        for item in self.data[DAOptSetName.ITEM_LIST]:
            if self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item] > 0:
                for date in self.data[DAOptSetName.ITEM_TIME_DICT][item]:
                    sum_item_date_production = \
                        sum(self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0) for order in
                            self.data[DAOptSetName.ORDER_BY_ITEM_DICT][item]
                            for machine in self.data[DAOptSetName.MACHINE_BY_ORDER_DICT][order]
                            )
                    if sum_item_date_production > self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]:
                        logger.info(
                            f"{date}_款式_{item}_的产量_{sum_item_date_production}_超过日上限_{self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item]}")
                        return False, None

        # 供应商日产能上限
        for supplier in self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT]:
            for date in self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier]:
                if self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date] >= 0:
                    sum_supplier_date_production = \
                        sum(self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                            for item in self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT].get(supplier, [])
                            for order in self.data[DAOptSetName.ORDER_BY_ITEM_DICT][item]
                            for machine in set.intersection(set(self.data[DAOptSetName.MACHINE_BY_ORDER_DICT][order]),
                                                            set(self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]))
                            )
                    if sum_supplier_date_production > self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][
                        supplier][date]:
                        logger.info(
                            f"{date}_供应商_{supplier}_的产量_{sum_supplier_date_production}_超过日上限_{self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date]}")
                        for (o, m, d) in self.result[ResultName.ORDER_MACHINE_DATE]:
                            if date == d and (m in self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]):
                                logger.info(
                                    f"{date}_供应商_{supplier}_的机器_{m}_生产订单_{o}_产量_{self.result[ResultName.ORDER_MACHINE_DATE][o, m, d]}")

                        return False, None

        # 产线月产能上限
        for machine in self.data[DAOptSetName.MACHINE_LIST]:
            for month in self.data[DAOptSetName.MACHINE_TIME_MONTH_DICT].get(machine, []):
                sum_machine_month_production = sum(
                    self.result[ResultName.ORDER_MACHINE_DATE].get((order, machine, date), 0)
                    for order in self.data[DAOptSetName.ORDER_BY_MACHINE_DICT][machine]
                    for date in self.data[DAOptSetName.TIME_BY_MONTH_DICT][month]
                    if month in self.data[DAOptSetName.TIME_BY_MONTH_DICT]
                )
                if sum_machine_month_production > self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
                        (machine, month), 0):
                    logger.info(
                        f"{month}_产线_{machine}_的产量_{sum_machine_month_production}_超过月上限_{self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month), 0)}")
                    return False, None

        # 池内的最大和最小产能规划达成率 和平均达成率
        for pool in self.result[ResultName.POOL_CAPACITY_RATIO_UB]:
            average_pool_capacity_ratio = sum(
                self.result[ResultName.SUPPLIER_CAPACITY_RATIO][supplier] * sum([
                    self.data[ParaName.MACHINE_CAPACITY_PLANNED_DICT].get((machine, month), 0)
                    for machine in self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT].get(supplier, [])
                    for month in self.data[DAOptSetName.MACHINE_TIME_MONTH_DICT].get(machine, [])])
                for supplier in self.data[DAOptSetName.SUPPLIER_BY_POOL_DICT][pool]) / sum([
                    self.data[ParaName.MACHINE_CAPACITY_PLANNED_DICT].get((machine, month), 0)
                    for supplier in self.data[DAOptSetName.SUPPLIER_BY_POOL_DICT][pool]
                    for machine in self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT].get(supplier, [])
                    for month in self.data[DAOptSetName.MACHINE_TIME_MONTH_DICT].get(machine, [])])
            logger.info(f"{pool}_的产能规划达成率，最高为_{format(self.result[ResultName.POOL_CAPACITY_RATIO_UB][pool], '.4f')}_最低为_{format(self.result[ResultName.POOL_CAPACITY_RATIO_LB][pool], '.4f')}_平均产能规划达成率为_{format(average_pool_capacity_ratio, '.4f')}")
            finished_rate_list.append(f"{pool}_的产能规划达成率，最高为_{format(self.result[ResultName.POOL_CAPACITY_RATIO_UB][pool], '.4f')}_最低为_{format(self.result[ResultName.POOL_CAPACITY_RATIO_LB][pool], '.4f')}_平均产能规划达成率为_{format(average_pool_capacity_ratio, '.4f')}")


        return True, finished_rate_list
