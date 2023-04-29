
"""
main文件
用于生成随机算例
"""
import math
import random

import numpy as np
import pandas as pd

from util.header import *
import os

from util.raw_header import FileName


def cal_cum_dis(dis):
    cum_dis = []
    sum = 0
    for i in range(len(dis)):
        sum+= dis[i]
        cum_dis.append(sum)
    return cum_dis

for i in range(5):
    num_of_item = 100
    num_of_supplier = 10
    num_of_machine_types = 15
    num_of_periods = 120
    num_of_periods_per_hat = 30
    num_of_hat_periods = math.ceil(num_of_periods/num_of_periods_per_hat)   # 向上取整


    distribution_of_num_of_order_per_item = [0.113, 0.243, 0.243, 0.333, 0.04, 0.011, 0.006, 0.006, 0.005] # 1为起始 1为距离
    distribution_of_order_quantity = [0.35, 0.28, 0.2, 0.1, 0.05, 0.02]         # 0为起始 以 10 为距离
    distribution_of_num_of_machine_per_supplier = [0.296, 0.185, 0.074, 0.111, 0.148, 0.111, 0.037, 0.038] # 1为起始 1为距离
    distribution_of_machine_types_per_item = [0.5, 0.4, 0.1]
    distribution_of_order_time_range = [0.091, 0.091, 0.182, 0.091, 0.182, 0.091, 0.091, 0.08, 0.06, 0.042] # 35为起点，gap为5
    cum_distribution_of_num_of_order_per_item = cal_cum_dis(distribution_of_num_of_order_per_item)
    cum_distribution_of_order_quantity = cal_cum_dis(distribution_of_order_quantity)
    cum_distribution_of_num_of_machine_per_supplier = cal_cum_dis(distribution_of_num_of_machine_per_supplier)
    cum_distribution_of_machine_types_per_item = cal_cum_dis(distribution_of_machine_types_per_item)
    cum_distribution_of_order_time_range = cal_cum_dis(distribution_of_order_time_range)

    distribution_of_supplier_daily_max = [0.15, 0.08, 0.161, 0.05, 0.024, 0.03, 0.056, 0.065, 0.058, 0.03, 0.048, 0.038, 0.035, 0.022, 0.015, 0.008, 0.03, 0.015, 0.015, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01] # 2 为开始，跨度为1
    distribution_of_machine_monthly_max = [0.2, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1] # 10为起点，30为跨度
    distribution_of_item_daily_max = [0.5, 0.3, 0.12, 0.08] # 1为起点， 跨度为1
    cum_distribution_of_supplier_daily_max = cal_cum_dis(distribution_of_supplier_daily_max)
    cum_distribution_of_machine_monthly_max = cal_cum_dis(distribution_of_machine_monthly_max)
    cum_distribution_of_item_daily_max = cal_cum_dis(distribution_of_item_daily_max)
    # 生成item以及对应可以生产的machine_type
    items_list = []
    order_list = []
    order_idx = 0
    for item_idx in range(num_of_item):

        minimum_production_per_date = 1
        sum_quantity = 0
        mini_start_date = num_of_periods
        maxi_end_date = 0
        # 生成item的order
        rnd = random.random()
        idx = 0
        while rnd > cum_distribution_of_num_of_order_per_item[idx]:
            idx = idx+1
        order_num_of_i = idx+1
        for o in range(order_num_of_i):
            rnd = random.random()
            idx = 0
            while rnd > cum_distribution_of_order_quantity[idx]:
                idx = idx + 1
            order_quantity = random.randint(10*idx+1, 10*(idx+1)+1)

            rnd = random.random()
            idx = 0
            while rnd > cum_distribution_of_order_time_range[idx]:
                idx = idx + 1
            order_time_range = random.randint(30 + 5*idx, 30 + 5*(idx+1))
            start_date = random.randint(0, num_of_periods-order_time_range)
            order_list.append((order_idx, item_idx, start_date, start_date+order_time_range, order_quantity)) # 订单序号，所属款式，开始日期，结束日期，所需产量
            order_idx = order_idx + 1

            sum_quantity += order_quantity
            mini_start_date = min(mini_start_date, start_date)
            maxi_end_date = max(maxi_end_date, start_date+order_time_range)
            minimum_production_per_date = max(minimum_production_per_date, math.ceil(order_quantity/order_time_range))
        minimum_production_per_date = max(minimum_production_per_date, math.ceil(sum_quantity/(maxi_end_date-mini_start_date)))

        rnd = random.random()
        idx = 0
        while rnd > cum_distribution_of_machine_types_per_item[idx]:
            idx = idx + 1

        machine_type_num_of_i = idx + 1
        machine_type_list = random.sample(range(1, num_of_machine_types), machine_type_num_of_i)

        rnd = random.random()
        idx = 0
        while rnd > cum_distribution_of_item_daily_max[idx]:
            idx = idx + 1

        item_daily_max = idx + 1
        item_daily_max = max(item_daily_max, minimum_production_per_date)

        for machine_type in machine_type_list:
            items_list.append((item_idx, machine_type, item_daily_max))

    item_df = pd.DataFrame(items_list, columns=[ItemHeader.ITEM_ID, ItemHeader.MACHINE_TYPE, ItemHeader.MAX_PRODUCTION_LIMIT])
    order_df = pd.DataFrame(order_list, columns=[OrderHeader.ORDER_ID, OrderHeader.ITEM_ID, OrderHeader.ARRIVAL_DATE, OrderHeader.DUE_DATE, OrderHeader.CAPACITY_NEEDED])

    # 生成supplier以及对应的machine，machine生成对应的machine_type

    supplier_list = []
    machine_list = []

    machine_idx = 0
    for supplier_idx in range(num_of_supplier):
        importance = random.randint(0, 5)
        if importance == 0:
            importance = '战略'
        elif importance == 1:
            importance = '核心'
        elif importance == 2:
            importance = '合格'
        elif importance == 3:
            importance = '培养'
        elif importance == 4:
            importance = '观察'
        for date in range(num_of_periods):
            # 生成supplier的在date的产能
            rnd = random.random()
            idx = 0
            while rnd > cum_distribution_of_supplier_daily_max[idx]:
                idx = idx + 1
            supplier_daily_max = idx+1
            supplier_list.append((supplier_idx, date, supplier_daily_max, importance))
        # 生成supplier的machine
        rnd = random.random()
        idx = 0
        while rnd > cum_distribution_of_num_of_order_per_item[idx]:
            idx = idx + 1
        machine_num_of_s = idx + 1
        for m in range(machine_num_of_s):
            machine_type = random.randint(0, num_of_machine_types)
            for month in range(num_of_hat_periods):
                # 生成machine的在month的产能
                rnd = random.random()
                idx = 0
                while rnd > cum_distribution_of_machine_monthly_max[idx]:
                    idx = idx + 1
                machine_month_max = random.randint(10 + 30*idx, 10 + 30*(idx+1))
                machine_list.append((machine_idx, supplier_idx, month, machine_month_max, machine_type))
            machine_idx = machine_idx+1


    supplier_df = pd.DataFrame(supplier_list, columns=[SupplierHeader.SUPPLIER_ID, SupplierHeader.DATE, SupplierHeader.MAX_LINE_LIMIT, SupplierHeader.IMPORTANCE])
    machine_df = pd.DataFrame(machine_list, columns=[MachineHeader.MACHINE_ID, MachineHeader.SUPPLIER_ID, MachineHeader.MONTH, MachineHeader.PLANNED_CAPACITY, MachineHeader.MACHINE_TYPE])

    calendar_list = list()
    for date in range(num_of_periods):
        calendar_list.append((date, date//num_of_periods_per_hat))
    calendar_df = pd.DataFrame(calendar_list, columns=[CalendarHeader.DATE, CalendarHeader.MONTH])


    random_file_dir = "/Users/emmabai/PycharmProjects/semir-paper/" + "data/input/random_data/Set_6/"+str(i)+"/"
    os.makedirs(random_file_dir, exist_ok=True)
    item_df.to_csv(os.path.join(random_file_dir, FileName.ITEM_FILE_NAME + '.csv'), index=False)
    machine_df.to_csv(
        os.path.join(random_file_dir, FileName.MACHINE_FILE_NAME + '.csv'), index=False)
    supplier_df.to_csv(
        os.path.join(random_file_dir, FileName.SUPPLIER_FILE_NAME + '.csv'), index=False)
    order_df.to_csv(
        os.path.join(random_file_dir, FileName.ORDER_FILE_NAME + '.csv'), index=False)
    calendar_df.to_csv(
        os.path.join(random_file_dir, FileName.CALENDAR_FILE_NAME + '.csv'), index=False)
