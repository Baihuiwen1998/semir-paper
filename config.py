class RawDataName:
    """
    原始Semir数据表名称
    """
    ALGO_TYPE = 'algo_type'  # 算法所属阶段
    ALGO_BRAND = 'algo_brand'  # 算法所处理的品牌
    FABRIC = 'fabric'  # 算法处理的面种
    # dataframe
    ALGO_DICT = 'algo_dictionary_df'
    AVERAGE_DEPTH = 'average_depth_df'
    CALENDAR = 'calendar_df'
    DEMAND = 'demand_df'
    DEMAND_BOND = 'demand_bond_df'
    DEMAND_DETAIL = 'demand_detail_df'
    ITEM = 'item_df'
    ITEM_DETAIL = 'item_detail_df'
    PHYSICAL_SUPPLIER = 'physical_supplier_df'
    PHYSICAL_SUPPLIER_CAPACITY_TARGET = 'physical_supplier_capacity_target_df'
    PHYSICAL_SUPPLIER_LABEL = 'physical_supplier_label_df'
    PHYSICAL_SUPPLIER_MAX_CAPACITY = 'physical_supplier_max_capacity_df'
    SUPPLIER = 'supplier_df'
    SUPPLIER_CAPACITY = 'supplier_capacity_df'
    SUPPLIER_LADDER = 'supplier_ladder_df'

class RawDataFeatureName:
    """
    原始数据特征分布
    """
    DISTRIBUTION_OF_DEMAND_NUM_PER_ITEM = 'DISTRIBUTION_OF_DEMAND_PER_ITEM'
    DISTRIBUTION_OF_MACHINE_NUM_PER_ITEM = 'DISTRIBUTION_OF_MACHINE_NUM_PER_ITEM'
    DISTRIBUTION_OF_MACHINE_NUM_PER_SUPPLIER = 'DISTRIBUTION_OF_MACHINE_NUM_PER_SUPPLIER'
    DISTRIBUTION_OF_DEMAND_QUANTITY = 'DISTRIBUTION_OF_DEMAND_QUANTITY'
    DISTRIBUTION_OF_DEMAND_TIME_WINDOW_WIDTH = 'DISTRIBUTION_OF_DEMAND_TIME_WINDOW_WIDTH'
    DISTRIBUTION_OF_DEMAND_ARRIVAL_DATE = 'DISTRIBUTION_OF_DEMAND_ARRIVAL_DATE'
    DISTRIBUTION_OF_DEMAND_DUE_DATE = 'DISTRIBUTION_OF_DEMAND_DUE_DATE'
    DISTRIBUTION_OF_MACHINE_MONTH_CAPACITY = 'DISTRIBUTION_OF_MACHINE_MONTH_CAPACITY'
    DISTRIBUTION_OF_SUPPLIER_DATE_CAPACITY = 'DISTRIBUTION_OF_SUPPLIER_DATE_CAPACITY'

class DataName:
    """
    算例数据表名
    """
    ITEM = 'item_df'
    ORDER = 'order_df'
    SUPPLIER = 'supplier_df'
    MACHINE = 'machine_df'
    CALENDAR = 'calendar_df'


class SetName:
    ORDER_LIST = 'order_list'  # 订单列表
    ORDER_BY_ITEM_DICT = 'order_by_item_dict'  # 给定款式item下的订单列表{item_1:[order_1,...,order_n], ...}
    ITEM_BY_CHANNEL_DICT = 'item_by_channel_dict'
    ITEM_LIST = 'item_list'  # 款式列表
    TIME_LIST = 'time_list'
    TIME_MONTH_LIST = 'time_month_list'
    TIME_BY_MONTH_DICT = 'time_by_month_dict'
    MACHINE_LIST = 'machine_list'
    CHANNEL_LIST = 'channel_list'
    MACHINE_BY_SUPPLIER_DICT = 'machine_by_supplier_dict'
    SUPPLIER_LIST = 'supplier_list'
    SUPPLIER_CORE_LIST = 'supplier_core_list'
    SUPPLIER_STRATEGY_LIST = 'supplier_strategy_list'
    SUPPLIER_QUALIFIED_LIST = 'supplier_qualified_list'
    SUPPLIER_CULTIVATE_LIST = 'supplier_cultivate_list'
    SUPPLIER_ON_WATCH_LIST = 'supplier_on_watch_list'
    SUPPLIER_BY_POOL_DICT = 'supplier_by_pool_dict'
    SUPPLIER_CAPACITY_EMPTY_SET = 'supplier_capacity_empty_set'
    MACHINE_BY_ORDER_DICT = 'machine_by_order_dict'
    MACHINE_BY_ITEM_DICT = 'machine_by_item_dict'
    ORDER_BY_MACHINE_DICT = 'order_by_machine_dict'
    SUPPLIER_BY_ITEM_DICT = 'supplier_by_item_dict'
    ITEM_BY_SUPPLIER_DICT = 'item_by_supplier_dict'
    ORDER_TIME_DICT = 'order_time_dict'
    ORDER_TIME_MONTH_DICT = 'order_time_month_dict'
    TIME_BY_ORDER_MONTH_DICT = 'time_by_order_month_dict'
    MACHINE_BY_CHANNEL_DICT = 'machine_by_channel_dict'
    MACHINE_TIME_DICT = 'machine_time_dict'
    MACHINE_TIME_MONTH_DICT = 'machine_time_month_dict'
    ITEM_TIME_DICT = 'item_time_dict'
    ITEM_MONTH_DICT = 'item_month_dict'
    LABEL_LIST = 'label_list'
    MACHINE_BY_LABEL_DICT = 'machine_by_label_dict'
    ITEM_BY_LABEL_DICT = 'item_by_label_dict'
    ELIGIBLE_MACHINE_TYPE_SET_BY_ITEM_DICT = 'item_eligible_machine_type_set'

    MACHINE_SUB_SETS_BY_SUPPLIER_DICT = 'machine_sub_sets_by_supplier_dict'
    ITEM_SUB_SETS_BY_SUPPLIER_DICT = 'item_sub_sets_by_supplier_dict'


class ParaName:
    MAX_QUANTITY = 'max_quantity' # 大m
    # 需求相关参数
    ORDER_QUANTITY_DICT = 'order_quantity_dict'  # 给定需求的产能线天数需求字典(Q_d) e.g.{order_1: integer_1, ...]}
    ORDER_OPTIMAL_QUANTITY_DICT = 'order_optimal_quantity_dict'  # 需求的每日最优生产量字典 e.g. {order_1: quantity1, ... }
    ORDER_ITEM_DICT = 'order_item_dict'  # 需求对应的款字典 e.g. [order_1: item_1,...]
    # 款式相关参数
    ITEM_MAX_OCCUPY_DICT = 'item_max_occupy_dict'  # 给定款的单日最大可用产能(O_m) e.g. {item1: integer1, ...}
    ITEM_QUANTITY_DICT = 'item_quantity_dict'  # 款式对应线天数字典
    ITEM_SHARE_LEVEL_DICT = 'item_share_level_dict' # 款式对应共有水平
    # 产线相关参数
    MACHINE_MONTH_MAX_PRODUCTION_DICT = 'supplier_month_max_production_dict'  # 给定算法供应商的每月产能上限(O_sT) e.g. {(supplier_1, time_str_1): integer1, ...}
    MACHINE_CAPACITY_PLANNED_DICT = 'machine_capacity_planned_dict'  # 给定产线的每月产能规划产能() e.g. {(machine_1, time_str_1): integer1, ...}
    MACHINE_SUPPLIER_DICT = 'machine_supplier_dict'  # 给定机器对应的供应商字典 e.g. {machine1: supplier_1,...}
    MACHINE_TYPE_DICT = 'machine_type_dict'
    # 供应商相关参数
    SUPPLIER_CAPACITY_TARGET_DICT = 'supplier_capacity_target_dict'  # 给定实体供应商和时间(月份)的产能规划达成目标字典(Omega_sT) e.g. [(supplier1, month_str_1): float1, ...]
    SUPPLIER_DAILY_MAX_PRODUCTION_DICT = 'supplier_daily_max_production_dict'  # 给定实体供应商的每日产能上限(O_st) e.g. {(supplier_1, fabric_category1, time_str_1): integer1, ...}
    MONTH_BY_TIME_DICT = 'month_by_time_dict'


class ObjCoeffName:
    """
    目标函数系数
    """
    CAPACITY_AVERAGE_PUNISH = 'capacity_average_punish'                         # 同池供应商达成率不均衡惩罚
    ORDER_DELAY_PUNISH = 'order_delay_punish'                                 # 订单延误精细惩罚字典
    ORDER_DELAY_BASE_PUNISH = 'order_delay_base_punish'                       # 订单延误基础惩罚参数
    ORDER_PRODUCT_OPT_PUNISH = 'order_product_opt_punish'                     # 订单超出最优产线数惩罚
    SUPPLIER_LADDER_PUNISH = 'supplier_ladder_punish'                # 阶梯产能达成率惩罚
    # lbbd 约束用参数
    ITEM_PHYSICAL_SUPPLIER_PUNISH_MATRIX = 'item_physical_supplier_punish_matrix' # 款式分配到实体供应商惩罚（软约束用）

class VarName:
    """
    变量名称
    """
    ALPHA = 'alpha'
    BETA = 'beta'
    GAMMA = 'gamma'     # 0-1变量，gamma_{o,m}表示订单在机器m上生产
    SUPPLIER_CAPACITY_RATIO = 'supplier_capacity_ratio'
    CAPACITY_RATIO_AVG = 'capacity_ratio_avg'
    POOL_CAPACITY_RATIO_AVG = 'pool_capacity_ratio_avg'
    POOLS_CAPACITY_RATIO_DELTA = 'pool_capacity_ratio_delta'
    SUPPLIER_CAPACITY_RATIO_DELTA = 'supplier_capacity_ratio_delta'
    Z = 'z'
    HAT_Z = '\hat_z'                # 连续变量，\hat_z_{o,s,\hat_t} 表示订单o在供应商s处\hat_t月的产量
    NU = 'nu'                        # 0-1变量，nu_{m,hat_t}表示是否有\hat_t月产线m可生产款式被分配至该产线所属实体供应商
    KAPPA = 'kappa'                 # 连续变量，表示供应商s在t日的最大产量
    THETA = 'theta'  # 0-1变量，theta_{p,k}实体供应商第k个不可行的款分配方案是否被选择

    # LAMBDA = 'lambda'  # 0-1变量，lambda_{s, t}表示是否有t日s供应商可生产的款式被分配至该供应商

class ObjName:
    ORDER_DELAY_OBJ = 'order_delay_obj'
    CAPACITY_AVERAGE_OBJ = 'capacity_average_obj'
    CAPACITY_LADDER_OBJ = 'capacity_ladder_obj'

class ResultName:
    ORDER_PRODUCTION = 'order_production'
    ITEM_SUPPLIER = 'item_supplier'
    ORDER_MACHINE_DATE = 'order_machine_date'
    SUPPLIER_CAPACITY_RATIO = 'supplier_capacity_ratio'
    POOL_CAPACITY_RATIO_AVG = 'pool_capacity_ratio_avg'

class LBBDResultName:
    MASTER_RESULT = 'master_result'         # 记录主问题的变量求解结果
    SUB_RESULT = 'sub_result'               # 记录子问题的求解结果， dict_by_supplier
    IS_OPTIMAL = 'is_optimal'               # 记录LBBD是否获得了最优解，还是由于停止准则结束求解
    OBJ_VALUE = 'obj_value'                 # 最终目标函数值
    LOWER_BOUND = 'lower_bound'             # 结束时的下界，如果取得最优解，则下界=OBJ_VALUE，否则下界为最后一次主问题迭代的目标函数值
    RUN_TIME = 'run_time'                   # 整体求解时间
    ITERATION = 'iteration'                 # 经过了多少次迭代


class LBBDSubDataName:
    SUPPLIER = 'supplier'
    ITEM_LIST = 'item_list'
    ORDER_LIST = 'order_list'
    MACHINE_LIST = 'machine_list'

class LBBDCutName:
    INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT = 'infeasible_item_set_list_by_supplier_dict'
    MIS_BY_SUPPLIER_DICT = 'mis_by_supplier_dict'
    MIS_SIZE_BY_SUPPLIER_DICT = 'mis_size_by_supplier_dict'
