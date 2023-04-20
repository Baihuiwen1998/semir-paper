# @author: baihuiwen
# @email: bhw21@mails.tsinghua.edu.cn
# @date: 2023/3/17
import pandas as pd
import copy
import numpy as np
from config import *
from util.raw_header import *
from util.util import *

logger = logging.getLogger(__name__)
formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)


class LoadRawData:
    """
    读取原始数据，筛选得到所需数据，并对面种进行 区分
    """
    def __init__(self, input_dir, file):
        self.raw_data = dict()
        self.data_by_fabric = dict()  # 在森马中，算例可以按照面种拆分。不可拆分情况下为 self.data = dict()
        self.input_dir = input_dir
        self.file = file

    def load(self):
        """
        主函数
        """
        self.read_data()
        self.filter_data()
        logger.info('数据读入完成')
        return self.data_by_fabric

    def filter_data(self):
        """
        数据筛选
        """
        for fabric in FabricCategoryMark.ALL_FABRIC_CATEGORY_MARK:
            self.data_by_fabric[fabric] = copy.deepcopy(self.raw_data)
            self.data_by_fabric[fabric][RawDataName.FABRIC] = fabric
            # 需求表筛选
            demand_df = self.data_by_fabric[fabric][RawDataName.DEMAND]
            demand_df = demand_df[demand_df[DemandHeader.FABRIC_CATEGORY] == fabric]  # 按面种筛选需求
            demand_df = demand_df[[DemandHeader.DEMAND_ID, DemandHeader.ITEM_ID, DemandHeader.FABRIC_CATEGORY, DemandHeader.MAX_PRODUCTION_LIMIT, DemandHeader.ARRIVAL_DATE]]
            self.data_by_fabric[fabric][RawDataName.DEMAND] = demand_df

            # 需求细节表筛选
            demand_id_list = demand_df[DemandHeader.DEMAND_ID].to_list()
            demand_detail_df = self.data_by_fabric[fabric][RawDataName.DEMAND_DETAIL]
            demand_detail_df = demand_detail_df[demand_detail_df[DemandDetailHeader.DEMAND_ID].isin(demand_id_list)]
            demand_detail_df = demand_detail_df[[DemandDetailHeader.DEMAND_ID, DemandDetailHeader.DUE_DATE, DemandDetailHeader.CAPACITY_NEEDED]]
            self.data_by_fabric[fabric][RawDataName.DEMAND_DETAIL] = demand_detail_df

            # 款式表筛选
            item_df = self.data_by_fabric[fabric][RawDataName.ITEM]
            item_df = item_df[item_df[ItemHeader.FABRIC_CATEGORY] == fabric]  # 按面种筛选款式
            item_df = item_df[[ItemHeader.ITEM_ID, ItemHeader.BRAND, ItemHeader.CHANNEL, ItemHeader.FABRIC_CATEGORY, ItemHeader.AGE_GROUP, ItemHeader.ITEM_CAPACITY_GROUP]]
            self.data_by_fabric[fabric][RawDataName.ITEM] = item_df

            # 款式细节表筛选
            item_id_list = item_df[ItemHeader.ITEM_ID].to_list()
            item_detail_df = self.data_by_fabric[fabric][RawDataName.ITEM_DETAIL]
            item_detail_df = item_detail_df[item_detail_df[ItemDetailHeader.ITEM_ID].isin(item_id_list)]
            self.data_by_fabric[fabric][RawDataName.ITEM_DETAIL] = item_detail_df

            # 算法供应商表筛选
            supplier_df = self.data_by_fabric[fabric][RawDataName.SUPPLIER]
            supplier_df = supplier_df[supplier_df[SupplierHeader.FABRIC_CATEGORY] == fabric]  # 按面种筛选算法供应商
            supplier_df = supplier_df[supplier_df[SupplierHeader.BRAND] == '巴拉巴拉'] # 按照品牌筛选
            supplier_df = supplier_df[[SupplierHeader.SUPPLIER_ID, SupplierHeader.PHYSICAL_SUPPLIER_ID, SupplierHeader.BRAND, SupplierHeader.CHANNEL, SupplierHeader.AGE_GROUP, SupplierHeader.FABRIC_CATEGORY, SupplierHeader.ITEM_CAPACITY_GROUP]]
            self.data_by_fabric[fabric][RawDataName.SUPPLIER] = supplier_df

            # 算法供应商产能表
            supplier_id_list = supplier_df[SupplierHeader.SUPPLIER_ID].to_list()
            supplier_capacity_df = self.data_by_fabric[fabric][RawDataName.SUPPLIER_CAPACITY]
            supplier_capacity_df = supplier_capacity_df[
                supplier_capacity_df[SupplierCapacityHeader.SUPPLIER_ID].isin(supplier_id_list)]
            supplier_capacity_df = supplier_capacity_df[[SupplierCapacityHeader.SUPPLIER_ID, SupplierCapacityHeader.MONTH, SupplierCapacityHeader.PLANNED_CAPACITY, SupplierCapacityHeader.AVAILABLE_CAPACITY]]
            self.data_by_fabric[fabric][RawDataName.SUPPLIER_CAPACITY] = supplier_capacity_df

            # 实体供应商表
            physical_supplier_id_list = supplier_df[SupplierHeader.PHYSICAL_SUPPLIER_ID].to_list()
            physical_supplier_df = self.data_by_fabric[fabric][RawDataName.PHYSICAL_SUPPLIER]
            physical_supplier_df = physical_supplier_df[
                physical_supplier_df[PhysicalSupplierHeader.PHYSICAL_SUPPLIER_ID].isin(physical_supplier_id_list)]
            physical_supplier_df = physical_supplier_df[[PhysicalSupplierHeader.PHYSICAL_SUPPLIER_ID, PhysicalSupplierHeader.IMPORTANCE]]
            self.data_by_fabric[fabric][RawDataName.PHYSICAL_SUPPLIER] = physical_supplier_df

            # 实体供应商产能目标
            physical_supplier_id_list = physical_supplier_df[PhysicalSupplierHeader.PHYSICAL_SUPPLIER_ID].to_list()
            physical_supplier_capacity_target_df = self.data_by_fabric[fabric][
                RawDataName.PHYSICAL_SUPPLIER_CAPACITY_TARGET]
            physical_supplier_capacity_target_df = physical_supplier_capacity_target_df[
                physical_supplier_capacity_target_df[PhysicalSupplierCapacityTargetHeader.PHYSICAL_SUPPLIER_ID].isin(
                    physical_supplier_id_list)]
            physical_supplier_capacity_target_df = physical_supplier_capacity_target_df[[PhysicalSupplierCapacityTargetHeader.PHYSICAL_SUPPLIER_ID, PhysicalSupplierCapacityTargetHeader.MONTH, PhysicalSupplierCapacityTargetHeader.OCCUPATION_TARGET]]
            self.data_by_fabric[fabric][
                RawDataName.PHYSICAL_SUPPLIER_CAPACITY_TARGET] = physical_supplier_capacity_target_df

            # 实体供应商产能上限
            physical_supplier_max_capacity_df = self.data_by_fabric[fabric][
                RawDataName.PHYSICAL_SUPPLIER_MAX_CAPACITY]
            physical_supplier_max_capacity_df = physical_supplier_max_capacity_df[
                physical_supplier_max_capacity_df[PhysicalSupplierMaxCapacityHeader.PHYSICAL_SUPPLIER_ID].isin(
                    physical_supplier_id_list)]
            physical_supplier_max_capacity_df = physical_supplier_max_capacity_df[[PhysicalSupplierMaxCapacityHeader.PHYSICAL_SUPPLIER_ID, PhysicalSupplierMaxCapacityHeader.FABRIC_CATEGORY, PhysicalSupplierMaxCapacityHeader.DATE, PhysicalSupplierMaxCapacityHeader.MAX_LINE_LIMIT]]
            # 筛选面种
            physical_supplier_max_capacity_df = physical_supplier_max_capacity_df[physical_supplier_max_capacity_df[PhysicalSupplierMaxCapacityHeader.FABRIC_CATEGORY] == fabric]
            self.data_by_fabric[fabric][
                RawDataName.PHYSICAL_SUPPLIER_MAX_CAPACITY] = physical_supplier_max_capacity_df

            # 实体供应商标签
            physical_supplier_label_df = self.data_by_fabric[fabric][RawDataName.PHYSICAL_SUPPLIER_LABEL]
            physical_supplier_label_df = physical_supplier_label_df[
                physical_supplier_label_df[PhysicalSupplierLabelHeader.PHYSICAL_SUPPLIER_ID].isin(
                    physical_supplier_id_list)]
            self.data_by_fabric[fabric][RawDataName.PHYSICAL_SUPPLIER_LABEL] = physical_supplier_label_df

            # 均深度
            average_depth_df = self.data_by_fabric[fabric][RawDataName.AVERAGE_DEPTH]
            # average_depth_df = average_depth_df[average_depth_df[AverageDepthHeader.BRAND] == self.algo_brand]
            average_depth_df = average_depth_df[average_depth_df[AverageDepthHeader.FABRIC_CATEGORY] == fabric]
            self.data_by_fabric[fabric][RawDataName.AVERAGE_DEPTH] = average_depth_df

            calendar_df = self.data_by_fabric[fabric][RawDataName.CALENDAR]
            calendar_df = calendar_df[[CalendarHeader.DATE, CalendarHeader.IS_WORKDAY]]
            self.data_by_fabric[fabric][RawDataName.CALENDAR] = calendar_df

    def read_data(self):
        """
        数据的读入
        """
        # 需求表
        demand_df = pd.read_csv(os.path.join(self.input_dir + self.file, RawFileName.DEMAND_FILE_NAME + '.csv'))
        demand_df['arrival_date'] = demand_df['arrival_date'].apply(lambda x: str2date(x))
        # 需求细节表
        demand_detail_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.DEMAND_DETAIL_FILE_NAME + '.csv'))
        demand_detail_df['due_date'] = demand_detail_df['due_date'].apply(lambda x: str2date(x))

        # 款式表
        item_df = pd.read_csv(os.path.join(self.input_dir + self.file, RawFileName.ITEM_FILE_NAME + '.csv'))
        item_df['internal_item_id'] = item_df['internal_item_id'].apply(
            lambda x: str(x) if np.isnan(x) else str(int(x)))
        # 款式细节表
        item_detail_df = pd.read_csv(os.path.join(self.input_dir + self.file, RawFileName.ITEM_DETAIL_FILE_NAME + '.csv'))
        # 算法供应商表
        supplier_df = pd.read_csv(os.path.join(self.input_dir + self.file, RawFileName.SUPPLIER_FILE_NAME + '.csv'))
        supplier_df['physical_supplier_id'] = '000' + supplier_df['physical_supplier_id'].astype(str)
        # 算法供应商产能表
        supplier_capacity_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.SUPPLIER_CAPACITY_FILE_NAME + '.csv'))

        # 实体供应商表
        physical_supplier_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.PHYSICAL_SUPPLIER_FILE_NAME + '.csv'))
        physical_supplier_df['physical_supplier_id'] = '000' + physical_supplier_df['physical_supplier_id'].astype(str)

        # 实体供应商产能目标
        physical_supplier_capacity_target_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.PHYSICAL_SUPPLIER_CAPACITY_TARGET_FILE_NAME + '.csv'))
        physical_supplier_capacity_target_df['physical_supplier_id'] = '000' + physical_supplier_capacity_target_df[
            'physical_supplier_id'].astype(str)

        # 实体供应商产能上限
        physical_supplier_max_capacity_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.PHYSICAL_SUPPLIER_MAX_CAPACITY_FILE_NAME + '.csv'))
        physical_supplier_max_capacity_df['physical_supplier_id'] = '000' + physical_supplier_max_capacity_df[
            'physical_supplier_id'].astype(str)

        # 实体供应商标签
        physical_supplier_label_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.PHYSICAL_SUPPLIER_LABEL_FILE_NAME + '.csv'))
        physical_supplier_label_df['physical_supplier_id'] = '000' + physical_supplier_label_df[
            'physical_supplier_id'].astype(str)
        # 均深度
        average_depth_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.AVERAGE_DEPTH_FILE_NAME + '.csv'))
        # 日历
        calendar_df = pd.read_csv(os.path.join(self.input_dir + self.file, RawFileName.CALENDAR_FILE_NAME + '.csv'))
        calendar_df['work_date'] = calendar_df['work_date'].apply(lambda x: str2date(x))
        # 算法输入参数
        algo_dictionary_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.ALGO_DICTIONARY_FILE_NAME + '.csv'))

        # 实体供应商产能阶梯
        supplier_ladder_df = pd.read_csv(
            os.path.join(self.input_dir + self.file, RawFileName.SUPPLIER_LADDER_NAME + '.csv'))
        supplier_ladder_df['type'] = supplier_ladder_df['type'].apply(lambda x: int(x))
        supplier_ladder_df['stage'] = supplier_ladder_df['stage'].apply(lambda x: int(x))
        supplier_ladder_df['strategy_ratio'] = supplier_ladder_df['strategy_ratio'].apply(lambda x: float(x))
        supplier_ladder_df['core_ratio'] = supplier_ladder_df['core_ratio'].apply(lambda x: float(x))
        supplier_ladder_df['qualified_ratio'] = supplier_ladder_df['qualified_ratio'].apply(lambda x: float(x))

        self.raw_data = {RawDataName.DEMAND: demand_df,
                         RawDataName.DEMAND_DETAIL: demand_detail_df,
                         RawDataName.ITEM: item_df,
                         RawDataName.ITEM_DETAIL: item_detail_df,
                         RawDataName.SUPPLIER: supplier_df,
                         RawDataName.SUPPLIER_CAPACITY: supplier_capacity_df,
                         RawDataName.PHYSICAL_SUPPLIER: physical_supplier_df,
                         RawDataName.PHYSICAL_SUPPLIER_CAPACITY_TARGET: physical_supplier_capacity_target_df,
                         RawDataName.PHYSICAL_SUPPLIER_MAX_CAPACITY: physical_supplier_max_capacity_df,
                         RawDataName.PHYSICAL_SUPPLIER_LABEL: physical_supplier_label_df,
                         RawDataName.CALENDAR: calendar_df,
                         RawDataName.ALGO_DICT: algo_dictionary_df,
                         RawDataName.AVERAGE_DEPTH: average_depth_df,
                         RawDataName.SUPPLIER_LADDER: supplier_ladder_df}
