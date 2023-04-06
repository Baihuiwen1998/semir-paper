from util.raw_header import *
from constant.config import *

import pandas as pd


class TransformData:

    def __init__(self, raw_data_by_fabric):
        self.raw_data_by_fabric = raw_data_by_fabric
        self.desensitized_data = dict()

    def desensitize(self):
        for fabric in FabricCategoryMark.ALL_FABRIC_CATEGORY_MARK:
            self.desensitized_data[fabric] = dict()
            # 款式数据
            item_df = self.raw_data_by_fabric[fabric][RawDataName.ITEM]
            self.desensitized_data[fabric][DataName.ITEM] = item_df

            # 订单数据
            order_df = pd.merge(self.raw_data_by_fabric[fabric][RawDataName.DEMAND],
                                self.raw_data_by_fabric[fabric][RawDataName.DEMAND_DETAIL],
                                how='left', left_on=DemandHeader.DEMAND_ID, right_on=DemandDetailHeader.DEMAND_ID)
            order_df.rename(columns={'demand_id': 'order_id'}, inplace=True)
            self.desensitized_data[fabric][DataName.ORDER] = order_df

            # 供应商数据
            supplier_df = pd.merge(self.raw_data_by_fabric[fabric][RawDataName.PHYSICAL_SUPPLIER],
                                   self.raw_data_by_fabric[fabric][RawDataName.PHYSICAL_SUPPLIER_MAX_CAPACITY],
                                   how='left', left_on=PhysicalSupplierHeader.PHYSICAL_SUPPLIER_ID,
                                   right_on=PhysicalSupplierMaxCapacityHeader.PHYSICAL_SUPPLIER_ID)
            supplier_df.rename(columns={'physical_supplier_id': 'supplier_id'}, inplace=True)
            self.desensitized_data[fabric][DataName.SUPPLIER] = supplier_df

            # 机器数据
            machine_df = pd.merge(self.raw_data_by_fabric[fabric][RawDataName.SUPPLIER],
                                  self.raw_data_by_fabric[fabric][RawDataName.SUPPLIER_CAPACITY],
                                  how='left', left_on=SupplierHeader.SUPPLIER_ID,
                                  right_on=SupplierCapacityHeader.SUPPLIER_ID)
            machine_df.rename(columns={'supplier_id': 'machine_id', 'physical_supplier_id': 'supplier_id'}, inplace=True)
            self.desensitized_data[fabric][DataName.MACHINE] = machine_df

            # 日历数据
            calendar_df = self.raw_data_by_fabric[fabric][RawDataName.CALENDAR]
            self.desensitized_data[fabric][DataName.CALENDAR] = calendar_df
        return self.desensitized_data
