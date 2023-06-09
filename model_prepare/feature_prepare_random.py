from config import *
from util.header import *
from util.util import *
import numpy as np
logger = logging.getLogger(__name__)
formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)


class FeaturePrepareRandom:
    def __init__(self, data, filename):
        self.data = data
        self.filename = filename


    def prepare(self):
        """
        主函数
        1. 生成模型的参数
        2. 生成模型的集合
        3. 生成模型目标函数系数
        """
        self.gen_model_sets()
        self.gen_model_params()
        self.gen_model_params()
        self.gen_match_sets_and_params()
        self.filter_data()
        if ParamsMark.ALL_PARAMS_DICT[ParamsMark.SOLUTION_MODE] > 0:
            self.gen_sub_item_machine_sets()
        self.gen_model_coefficients()
        self.print_model_info()
        logger.info('数据处理完成')
        return self.data

    # =================
    # 模型相关集合
    # =================
    def gen_model_sets(self):
        self.gen_order_sets()
        self.gen_item_sets()
        self.gen_time_sets()
        self.gen_machine_sets()
        self.gen_supplier_sets()

    def gen_order_sets(self):
        """
        获取需求相关集合
        """
        logger.info('模型获取集合：需求集合')
        order_df = self.data[DataName.ORDER].copy()

        # 生成订单列表
        self.data[SetName.ORDER_LIST] = sorted(order_df['order_id'].to_list())

        # 给定款下的订单列表
        self.data[SetName.ORDER_BY_ITEM_DICT] = order_df.groupby([OrderHeader.ITEM_ID])[
            OrderHeader.ORDER_ID].apply(list).to_dict()

    def gen_item_sets(self):
        """
        获取款相关集合
        """
        logger.info('模型获取集合：款集合')
        item_df = self.data[DataName.ITEM].copy()

        # 筛选本期有订单需求的款式
        item_df = item_df[item_df[ItemHeader.ITEM_ID].isin(self.data[SetName.ORDER_BY_ITEM_DICT])]

        # 生成款清单
        self.data[SetName.ITEM_LIST] = sorted(set(item_df[ItemHeader.ITEM_ID].to_list()))  # 防止同一数据处理出的中间表排序有差异


    def gen_time_sets(self):
        """
        时间处理
        """
        logger.info('模型获取集合：排单时间相关集合')

        calendar_df = self.data[DataName.CALENDAR]

        # 日历提供的排程日期集合
        calendar_time_set = set(calendar_df[CalendarHeader.DATE].to_list())

        calendar_month_set = set(calendar_df[CalendarHeader.MONTH].to_list())
        self.data[SetName.TIME_LIST] = calendar_time_set
        self.data[SetName.TIME_MONTH_LIST] = calendar_month_set
        # 时间按月分类
        self.data[SetName.TIME_BY_MONTH_DICT] = calendar_df.groupby([CalendarHeader.MONTH])[
            CalendarHeader.DATE].apply(list).to_dict()
        self.data[ParaName.MONTH_BY_TIME_DICT] = calendar_df.set_index([CalendarHeader.DATE])[CalendarHeader.MONTH].to_dict()

    def gen_machine_sets(self):
        """
        处理产线集合
        """
        logger.info('模型获取集合：产线集合')

        machine_df = self.data[DataName.MACHINE]

        # 产线集合
        self.data[SetName.MACHINE_LIST] = sorted(list(set(machine_df[MachineHeader.MACHINE_ID].to_list())))


        # 过滤规划产能为0的产线
        total_planned_capacity = machine_df.groupby([MachineHeader.MACHINE_ID])[
            MachineHeader.PLANNED_CAPACITY].sum().to_dict()
        non_empty_supplier = set()
        for machine in total_planned_capacity:
            if total_planned_capacity[machine] > 0:
                non_empty_supplier.add(machine)
            else:
                self.data[SetName.MACHINE_LIST].remove(machine)

        # 产线按实体供应商分类
        self.data[SetName.MACHINE_BY_SUPPLIER_DICT] = \
            machine_df[machine_df[MachineHeader.MACHINE_ID].isin(self.data[SetName.MACHINE_LIST])]. \
                groupby([MachineHeader.SUPPLIER_ID])[MachineHeader.MACHINE_ID].apply(set).to_dict()

    def gen_supplier_sets(self):
        """
        处理供应商对应集合
        """
        logger.info('模型获取集合：供应商集合')
        supplier_df = self.data[DataName.SUPPLIER]

        # 实体供应商清单, 过滤无算法供应商的实体供应商
        origin_supplier_list = \
            sorted(list(set(supplier_df[SupplierHeader.SUPPLIER_ID].to_list())))

        filtered_supplier_set = set()
        self.data[SetName.SUPPLIER_LIST] = []
        for supplier in origin_supplier_list:
            if supplier in self.data[SetName.MACHINE_BY_SUPPLIER_DICT]:
                self.data[SetName.SUPPLIER_LIST].append(supplier)
                filtered_supplier_set.add(supplier)

        # 供应商核心分类
        self.data[SetName.SUPPLIER_STRATEGY_LIST] = \
            sorted(list(set(supplier_df[
                                (supplier_df[SupplierHeader.IMPORTANCE] == ImportanceMark.STRATEGY) &
                                (supplier_df[SupplierHeader.SUPPLIER_ID].isin(
                                    filtered_supplier_set))
                                ][SupplierHeader.SUPPLIER_ID])))

        self.data[SetName.SUPPLIER_CORE_LIST] = \
            sorted(list(set(supplier_df[
                                (supplier_df[SupplierHeader.SUPPLIER_ID].isin(
                                    filtered_supplier_set))
                                & (supplier_df[SupplierHeader.IMPORTANCE] == ImportanceMark.CORE)
                                ][SupplierHeader.SUPPLIER_ID].to_list())))


        self.data[SetName.SUPPLIER_QUALIFIED_LIST] = \
            sorted(list(set(supplier_df[
                                (supplier_df[SupplierHeader.IMPORTANCE] == ImportanceMark.QUALIFIED) &
                                (supplier_df[SupplierHeader.SUPPLIER_ID].isin(
                                    filtered_supplier_set))
                                ][SupplierHeader.SUPPLIER_ID])))

        self.data[SetName.SUPPLIER_CULTIVATE_LIST] = \
            sorted(list(set(supplier_df[
                                (supplier_df[SupplierHeader.IMPORTANCE] == ImportanceMark.CULTIVATE) &
                                (supplier_df[SupplierHeader.SUPPLIER_ID].isin(
                                    filtered_supplier_set))
                                ][SupplierHeader.SUPPLIER_ID])))

        self.data[SetName.SUPPLIER_ON_WATCH_LIST] = \
            sorted(list(set(supplier_df[
                                (supplier_df[SupplierHeader.IMPORTANCE] == ImportanceMark.ON_WATCH) &
                                (supplier_df[SupplierHeader.SUPPLIER_ID].isin(
                                    filtered_supplier_set))
                                ][SupplierHeader.SUPPLIER_ID])))

        self.data[SetName.SUPPLIER_BY_POOL_DICT] = {
            SupplierPoolMark.STRATEGY: self.data[SetName.SUPPLIER_STRATEGY_LIST],
            SupplierPoolMark.CORE: self.data[SetName.SUPPLIER_CORE_LIST],
            SupplierPoolMark.QUALIFIED: self.data[SetName.SUPPLIER_QUALIFIED_LIST],
            SupplierPoolMark.CULTIVATE: self.data[SetName.SUPPLIER_CULTIVATE_LIST],
            SupplierPoolMark.ON_WATCH: self.data[SetName.SUPPLIER_ON_WATCH_LIST]
        }


    # =================
    # 模型相关约束参数
    # =================

    def gen_model_params(self):
        self.gen_order_params()
        self.gen_item_params()
        self.gen_machine_params()
        self.gen_supplier_params()

    def gen_order_params(self):
        """
        获取订单相关参数
        """
        logger.info('模型获取参数：排单订单数据')
        order_df = self.data[DataName.ORDER].copy()

        # 订单需求量字典
        self.data[ParaName.ORDER_QUANTITY_DICT] = order_df.set_index([OrderHeader.ORDER_ID])[
            OrderHeader.CAPACITY_NEEDED].to_dict()
        self.data[ParaName.MAX_QUANTITY] = sum(self.data[ParaName.ORDER_QUANTITY_DICT].values())

        # # 订单每日最优产线数
        # self.data[ParaName.ORDER_OPTIMAL_QUANTITY_DICT] = order_df.set_index([OrderHeader.ORDER_ID])[
        #     OrderHeader.MAX_PRODUCTION_LIMIT].to_dict()

        # 订单对应款式
        self.data[ParaName.ORDER_ITEM_DICT] = order_df.set_index([OrderHeader.ORDER_ID])[
            OrderHeader.ITEM_ID].to_dict()

    def gen_item_params(self):
        """
        获取款相关参数
        """
        logger.info('模型获取参数：大货排单款参数')
        item_df = self.data[DataName.ITEM]
        # 款对应需求线天数求和
        item_quantity = {}

        for item in self.data[SetName.ORDER_BY_ITEM_DICT]:
            order_list = self.data[SetName.ORDER_BY_ITEM_DICT][item]
            item_quantity[item] = sum([self.data[ParaName.ORDER_QUANTITY_DICT][order] for order in order_list])
        self.data[ParaName.ITEM_QUANTITY_DICT] = item_quantity
        self.data[SetName.ELIGIBLE_MACHINE_TYPE_SET_BY_ITEM_DICT] = item_df.groupby([ItemHeader.ITEM_ID])[
            ItemHeader.MACHINE_TYPE].apply(set).to_dict()

    def gen_machine_params(self):
        """
        处理产线数据
        """
        logger.info('模型获取数据：排单产线数据')

        machine_df = self.data[DataName.MACHINE]

        # 记录产线产能规划产能
        self.data[ParaName.MACHINE_CAPACITY_PLANNED_DICT] = \
            machine_df[
                machine_df[MachineHeader.MACHINE_ID].isin(self.data[SetName.MACHINE_LIST])].set_index(
                [MachineHeader.MACHINE_ID, MachineHeader.MONTH]
            )[MachineHeader.PLANNED_CAPACITY].to_dict()

        # 算法供应商折算后最大产能
        self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT] = \
            machine_df[
                machine_df[MachineHeader.SUPPLIER_ID].isin(self.data[SetName.SUPPLIER_LIST])].set_index(
                [MachineHeader.MACHINE_ID, MachineHeader.MONTH]
            )[MachineHeader.PLANNED_CAPACITY].to_dict()
        # 产线对应的供应商
        self.data[ParaName.MACHINE_SUPPLIER_DICT] = \
            machine_df.set_index([MachineHeader.MACHINE_ID])[SupplierHeader.SUPPLIER_ID].to_dict()

        self.data[ParaName.MACHINE_TYPE_DICT] = machine_df.set_index([MachineHeader.MACHINE_ID])[MachineHeader.MACHINE_TYPE].to_dict()

    def gen_supplier_params(self):
        """
        处理供应商对应数据
        """
        logger.info('模型获取数据：实体供应商数据')

        supplier_df = self.data[DataName.SUPPLIER]

        # 供应商产能上限
        self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT] = dict()
        for supplier, sub_supplier_df in supplier_df[supplier_df[SupplierHeader.SUPPLIER_ID].isin(self.data[SetName.SUPPLIER_LIST])].groupby([SupplierHeader.SUPPLIER_ID]):
            self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier] = sub_supplier_df.set_index([SupplierHeader.DATE])[SupplierHeader.MAX_LINE_LIMIT].to_dict()

    # =================
    # 模型数据匹配
    # =================
    def gen_match_sets_and_params(self):
        """
        将数据进行匹配
        """
        logger.info('模型获取数据：排单生产匹配数据')
        # 读取原数据
        order_df = self.data[DataName.ORDER].copy()
        item_df = self.data[DataName.ITEM]
        machine_df = self.data[DataName.MACHINE]

        # ================
        # 基于需求数据，获取款最大产线数
        # ================
        self.data[ParaName.ITEM_MAX_OCCUPY_DICT] = item_df. \
            groupby([ItemHeader.ITEM_ID])[ItemHeader.MAX_PRODUCTION_LIMIT].apply(max).to_dict()


        self.data[SetName.MACHINE_BY_ORDER_DICT] = {}
        self.data[SetName.ORDER_BY_MACHINE_DICT] = {}
        self.data[SetName.ITEM_BY_SUPPLIER_DICT] = {}
        self.data[SetName.SUPPLIER_BY_ITEM_DICT] = {}
        self.data[SetName.MACHINE_BY_ITEM_DICT] = {}
        self.data[SetName.ITEM_BY_CHANNEL_DICT] = {}

        for item in self.data[SetName.ITEM_LIST]:
            possible_supplier = []
            possible_machine = []
            item_order_list = self.data[SetName.ORDER_BY_ITEM_DICT].get(item, [])

            possible_supplier = [supplier
                                 for supplier in self.data[SetName.SUPPLIER_LIST]
                                 if len(list(
                    machine for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
                    if self.data[ParaName.MACHINE_TYPE_DICT][machine] in \
                    self.data[SetName.ELIGIBLE_MACHINE_TYPE_SET_BY_ITEM_DICT][item])
                )]

            possible_machine = [machine
                                for supplier in possible_supplier
                                for machine in self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
                                if self.data[ParaName.MACHINE_TYPE_DICT][machine] in
                                self.data[SetName.ELIGIBLE_MACHINE_TYPE_SET_BY_ITEM_DICT][item]]

            self.data[SetName.SUPPLIER_BY_ITEM_DICT][item] = possible_supplier
            for supplier in possible_supplier:
                if supplier in self.data[SetName.ITEM_BY_SUPPLIER_DICT]:
                    self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier].append(item)
                else:
                    self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier] = [item]

            self.data[SetName.MACHINE_BY_ITEM_DICT][item] = possible_machine
            for order in item_order_list:
                self.data[SetName.MACHINE_BY_ORDER_DICT][order] = possible_machine
                for machine in self.data[SetName.MACHINE_BY_ORDER_DICT].get(order, []):
                    if machine in self.data[SetName.ORDER_BY_MACHINE_DICT]:
                        self.data[SetName.ORDER_BY_MACHINE_DICT][machine].append(order)
                    else:
                        self.data[SetName.ORDER_BY_MACHINE_DICT][machine] = [order]

        for supplier in self.data[SetName.ITEM_BY_SUPPLIER_DICT]:
            self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier] = sorted(
                self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier])
        for machine in self.data[SetName.ORDER_BY_MACHINE_DICT]:
            self.data[SetName.ORDER_BY_MACHINE_DICT][machine] = sorted(
                self.data[SetName.ORDER_BY_MACHINE_DICT][machine])

    # =================
    # 模型数据过滤
    # =================
    def filter_data(self):
        """
        数据进入模型前的过滤等前处理
        """
        logger.info('模型获取数据：算法数据前处理')
        # ==============
        # 过滤日期属性
        # ==============
        order_df = self.data[DataName.ORDER]
        calendar_df = self.data[DataName.CALENDAR]
        self.data[SetName.ORDER_TIME_DICT] = {}
        self.data[SetName.ORDER_TIME_MONTH_DICT] = {}
        self.data[SetName.TIME_BY_ORDER_MONTH_DICT] = {}
        order_arrival_date_dict = order_df.set_index([OrderHeader.ORDER_ID])[
            OrderHeader.ARRIVAL_DATE].to_dict()
        order_due_date_dict = order_df.set_index([OrderHeader.ORDER_ID])[
            OrderHeader.DUE_DATE].to_dict()
        calendar_time_set = set(calendar_df[CalendarHeader.DATE].to_list())


        for order in self.data[SetName.ORDER_LIST]:
            order_time_set = set()
            for date in range(order_arrival_date_dict[order], order_due_date_dict[order]+1):
                order_time_set.add(date)
            all_date_list = sorted(set.intersection(order_time_set, calendar_time_set))
            machine_list = self.data[SetName.MACHINE_BY_ORDER_DICT].get(order, [])
            all_date_list = sorted(set.intersection(order_time_set, calendar_time_set))
            tmp_month_set = set()
            tmp_date_list = []

            for date in all_date_list:
                month_str = self.data[ParaName.MONTH_BY_TIME_DICT][date]
                self.data[SetName.TIME_BY_ORDER_MONTH_DICT][order, month_str] = \
                    self.data[SetName.TIME_BY_ORDER_MONTH_DICT].get((order, month_str), set())
                self.data[SetName.TIME_BY_ORDER_MONTH_DICT][order, month_str].add(date)
                for machine in machine_list:
                    if self.data[ParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get((machine, month_str), 0) > 0:
                        tmp_date_list.append(date)
                        if month_str not in tmp_month_set:
                            tmp_month_set.add(month_str)
                        break
            if len(tmp_date_list) > 0:
                self.data[SetName.ORDER_TIME_DICT][order] = tmp_date_list
                self.data[SetName.ORDER_TIME_MONTH_DICT][order] = sorted(tmp_month_set)
            else:
                self.data[SetName.ORDER_TIME_DICT][order] = []
                self.data[SetName.ORDER_TIME_MONTH_DICT][order] = []

        self.data[SetName.MACHINE_TIME_DICT], self.data[SetName.MACHINE_TIME_MONTH_DICT] = {}, {}
        for machine in self.data[SetName.MACHINE_LIST]:
            self.data[SetName.MACHINE_TIME_DICT][machine] = set()
            self.data[SetName.MACHINE_TIME_MONTH_DICT][machine] = set()
            order_list = self.data[SetName.ORDER_BY_MACHINE_DICT].get(machine, [])
            for order in order_list:
                time_set = set(self.data[SetName.ORDER_TIME_DICT].get(order, []))
                self.data[SetName.MACHINE_TIME_DICT][machine] |= time_set
            self.data[SetName.MACHINE_TIME_DICT][machine] = sorted(
                self.data[SetName.MACHINE_TIME_DICT][machine])
            for date in self.data[SetName.MACHINE_TIME_DICT][machine]:
                self.data[SetName.MACHINE_TIME_MONTH_DICT][machine].add(self.data[ParaName.MONTH_BY_TIME_DICT][date])
            self.data[SetName.MACHINE_TIME_MONTH_DICT][machine] = sorted(
                self.data[SetName.MACHINE_TIME_MONTH_DICT][machine])

        self.data[SetName.ITEM_TIME_DICT] = {}
        self.data[SetName.ITEM_MONTH_DICT] = {}
        for item in self.data[SetName.ITEM_LIST]:
            item_time = set()
            item_month = set()
            for order in self.data[SetName.ORDER_BY_ITEM_DICT][item]:
                for date in self.data[SetName.ORDER_TIME_DICT][order]:
                    item_time.add(date)
                    item_month.add(self.data[ParaName.MONTH_BY_TIME_DICT][date])
            self.data[SetName.ITEM_TIME_DICT][item] = sorted(item_time)
            self.data[SetName.ITEM_MONTH_DICT][item] = sorted(item_month)

        # ==============
        # 过滤多余供应商
        # ==============
        machine_df = self.data[DataName.MACHINE]
        required_machine_set = set()
        for machine in self.data[SetName.ORDER_BY_MACHINE_DICT]:
            if len(self.data[SetName.ORDER_BY_MACHINE_DICT].get(machine, [])) > 0:
                required_machine_set.add(machine)
        # 更新machine list
        final_machine_set = set(self.data[SetName.MACHINE_LIST]) & required_machine_set
        self.data[SetName.MACHINE_LIST] = sorted(final_machine_set)

        self.data[SetName.MACHINE_BY_SUPPLIER_DICT] = \
            machine_df[machine_df[MachineHeader.MACHINE_ID].isin(final_machine_set)]. \
                groupby([MachineHeader.SUPPLIER_ID])[MachineHeader.MACHINE_ID].apply(set).to_dict()
        # 更新supplier list
        self.data[SetName.SUPPLIER_LIST] = sorted(
            self.data[SetName.MACHINE_BY_SUPPLIER_DICT])
        final_supplier_set = set(self.data[SetName.SUPPLIER_LIST])

        # 供应商核心分类
        self.data[SetName.SUPPLIER_STRATEGY_LIST] = \
            sorted(set(self.data[SetName.SUPPLIER_STRATEGY_LIST]) & final_supplier_set)

        self.data[SetName.SUPPLIER_CORE_LIST] = \
            sorted(set(self.data[SetName.SUPPLIER_CORE_LIST]) & final_supplier_set)

        self.data[SetName.SUPPLIER_QUALIFIED_LIST] = \
            sorted(set(self.data[SetName.SUPPLIER_QUALIFIED_LIST]) & final_supplier_set)
        self.data[SetName.SUPPLIER_CULTIVATE_LIST] = \
            sorted(set(self.data[SetName.SUPPLIER_CULTIVATE_LIST]) & final_supplier_set)
        self.data[SetName.SUPPLIER_ON_WATCH_LIST] = \
            sorted(set(self.data[SetName.SUPPLIER_ON_WATCH_LIST]) & final_supplier_set)

        self.data[SetName.SUPPLIER_BY_POOL_DICT] = {
            SupplierPoolMark.STRATEGY: self.data[SetName.SUPPLIER_STRATEGY_LIST],
            SupplierPoolMark.CORE: self.data[SetName.SUPPLIER_CORE_LIST],
            SupplierPoolMark.QUALIFIED: self.data[SetName.SUPPLIER_QUALIFIED_LIST],
            SupplierPoolMark.CULTIVATE: self.data[SetName.SUPPLIER_CULTIVATE_LIST],
            SupplierPoolMark.ON_WATCH: self.data[SetName.SUPPLIER_ON_WATCH_LIST]
        }

        # ==============
        # 过滤多余的日期和月份
        # ==============
        time_month_set = set()
        for item in self.data[SetName.ITEM_LIST]:
            time_month_set = time_month_set.union(set(self.data[SetName.ITEM_MONTH_DICT][item]))
        self.data[SetName.TIME_MONTH_LIST] = list(time_month_set)

        # 筛选日期，剔除无可生产需求的日期
        time_set = set()
        for order in self.data[SetName.ORDER_LIST]:
            time_set = time_set.union(set(self.data[SetName.ORDER_TIME_DICT][order]))
        self.data[SetName.TIME_LIST] = list(time_set)

    # =================
    # 模型相关目标函数系数
    # =================
    def gen_model_coefficients(self):
        """
        算法使用常数&系数
        """
        logger.info('模型获取数据：算法使用系数与常数')

        # =================
        # 基础固定系数
        # =================

        self.data[ObjCoeffName.ORDER_DELAY_BASE_PUNISH] = 20

        self.data[ObjCoeffName.ORDER_DELAY_PUNISH] = 1

        # self.data[ObjCoeffName.ORDER_PRODUCT_OPT_PUNISH] = 10

        self.data[ObjCoeffName.CAPACITY_AVERAGE_PUNISH] = 10

        self.data[ObjCoeffName.SUPPLIER_LADDER_PUNISH] = 10


    def print_model_info(self):
        logger.info(f'算例名称_{self.filename}')
        logger.info(f'款式数量_{len(self.data[SetName.ITEM_LIST])}_订单数量_{len(self.data[SetName.ORDER_LIST])}')
        logger.info(
            f'供应商数量_{len(self.data[SetName.SUPPLIER_LIST])}_产线数量_{len(self.data[SetName.MACHINE_LIST])}')

    def gen_sub_item_machine_sets(self):
        logger.info("生成款式-供应商-机器对应集合")

        self.data[SetName.MACHINE_SUB_SETS_BY_SUPPLIER_DICT] = dict()
        self.data[SetName.ITEM_SUB_SETS_BY_SUPPLIER_DICT] = dict()
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            machine_index_dict = {v: k for k, v in enumerate(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier])}
            item_sub_sets_list = list()
            machine_sub_sets_list = list()
            visited_machine_sets_binary = set()
            for item_index_1 in range(len(self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier])-1):
                for item_index_2 in range(item_index_1+1, len(self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier])):
                    item_1 = self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier][item_index_1]
                    item_2 = self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier][item_index_2]
                    item_subset = {item_1, item_2}

                    machine_subset = set.union(set(self.data[SetName.MACHINE_BY_ITEM_DICT][item_1]), (set(self.data[SetName.MACHINE_BY_ITEM_DICT][item_2])))
                    machine_subset = set.intersection(machine_subset, set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]))
                    machine_subset_binary = 0
                    for machine in machine_subset:
                        machine_subset_binary = machine_subset_binary | (1<<machine_index_dict[machine])
                    if machine_subset_binary not in visited_machine_sets_binary:
                        visited_machine_sets_binary.add(machine_subset_binary)
                        if len(machine_subset) != len(self.data[SetName.MACHINE_BY_ITEM_DICT][item_1]) + len(self.data[SetName.MACHINE_BY_ITEM_DICT][item_2]):
                            for item_index_3 in range(len(self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier])):
                                if item_index_3 == item_index_1 | item_index_3 == item_index_2:
                                    continue
                                item_3 = self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier][item_index_3]
                                machine_set_by_item_3 = set.intersection(set(self.data[SetName.MACHINE_BY_ITEM_DICT][item_3]), set(self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]))
                                if machine_set_by_item_3.issubset(machine_subset):
                                    item_subset.add(item_3)

                            machine_sub_sets_list.append(machine_subset)
                            item_sub_sets_list.append(item_subset)

            self.data[SetName.MACHINE_SUB_SETS_BY_SUPPLIER_DICT][supplier] = machine_sub_sets_list
            self.data[SetName.ITEM_SUB_SETS_BY_SUPPLIER_DICT][supplier] = item_sub_sets_list

        logger.info("生成订单-供应商-月份-订单对应集合")
        self.data[SetName.UNCOVERED_ORDERS_SET_BY_ORDER_SUPPLIER_MONTH_DICT] = dict()
        orders_def_0_by_order_supplier_month_dict = dict()
        orders_not_covered_list_by_order_supplier_month_dict = dict()
        orders_covered_list_by_order_supplier_month_dict = dict()

        cnt_variable_num = 0
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            visited_date_sets_binary = set()
            for item_1 in self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]:
                for order_1 in self.data[SetName.ORDER_BY_ITEM_DICT][item_1]:
                    for month in self.data[SetName.ORDER_TIME_MONTH_DICT][order_1]:
                        orders_not_covered_list_by_order_supplier_month_dict[order_1, supplier, month] = set()
                        orders_covered_list_by_order_supplier_month_dict[order_1, supplier, month] = set()
                        orders_def_0_by_order_supplier_month_dict[order_1, supplier, month] = set()
                        date_set_binary = 0
                        for date in self.data[SetName.TIME_BY_ORDER_MONTH_DICT][order_1, month]:
                            date_set_binary = date_set_binary | (1 << date)
                        if date_set_binary not in visited_date_sets_binary:
                            visited_date_sets_binary.add(date_set_binary)
                            for item_2 in self.data[SetName.ITEM_BY_SUPPLIER_DICT][supplier]:
                                for order_2 in self.data[SetName.ORDER_BY_ITEM_DICT][item_2]:
                                    if month in self.data[SetName.ORDER_TIME_MONTH_DICT][order_2]:
                                        if set(self.data[SetName.TIME_BY_ORDER_MONTH_DICT][order_2, month]).issubset(
                                                set(self.data[SetName.TIME_BY_ORDER_MONTH_DICT][order_1, month])):
                                            orders_covered_list_by_order_supplier_month_dict[
                                                order_1, supplier, month].add(order_2)
                                        else:
                                            dates_left_over = set(self.data[SetName.TIME_BY_ORDER_MONTH_DICT][order_2, month]) - set(self.data[SetName.TIME_BY_ORDER_MONTH_DICT][order_1, month])
                                            capacity_by_supplier = 0
                                            for date in dates_left_over:
                                                capacity_by_supplier += min(self.data[ParaName.ITEM_MAX_OCCUPY_DICT][item_2], self.data[ParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier][date])
                                            if capacity_by_supplier >= self.data[ParaName.ORDER_QUANTITY_DICT][order_2]:
                                                orders_def_0_by_order_supplier_month_dict[order_1, supplier, month].add(order_2)
                                            else:
                                                orders_not_covered_list_by_order_supplier_month_dict[order_1, supplier, month].add(order_2)
                                                cnt_variable_num = cnt_variable_num+1
        self.data[SetName.UNCOVERED_ORDERS_SET_BY_ORDER_SUPPLIER_MONTH_DICT] = orders_not_covered_list_by_order_supplier_month_dict
        self.data[SetName.COVERED_ORDERS_SET_BY_ORDER_SUPPLIER_MONTH_DICT] = orders_covered_list_by_order_supplier_month_dict
