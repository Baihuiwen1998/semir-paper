class OrderHeader:
    ORDER_ID = 'order_id'
    ITEM_ID = 'item_id'
    FABRIC_CATEGORY = 'fabric_category'
    MAX_PRODUCTION_LIMIT = 'max_production_limit'
    ARRIVAL_DATE = 'arrival_date'
    DUE_DATE = 'due_date'
    CAPACITY_NEEDED = 'capacity_needed'

class ItemHeader:
    AGE_GROUP = 'age_group'
    BRAND = 'brand'
    CHANNEL = 'channel'
    FABRIC_CATEGORY = 'fabric_category'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    ITEM_ID = 'item_id'
    SHARE_LEVEL = 'share_level'

class SupplierHeader:
    SUPPLIER_ID = 'supplier_id'
    IMPORTANCE = 'importance'
    FABRIC_CATEGORY = 'fabric_category'
    DATE = 'date'
    MAX_LINE_LIMIT = 'max_line_limit'

class MachineHeader:
    MACHINE_ID = 'machine_id'
    SUPPLIER_ID = 'supplier_id'
    BRAND = 'brand'
    CHANNEL = 'channel'
    FABRIC_CATEGORY = 'fabric_category'
    AGE_GROUP = 'age_group'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    MONTH = 'month'
    PLANNED_CAPACITY = 'planned_capacity'
    AVAILABLE_CAPACITY = 'available_capacity'

class CalendarHeader:
    DATE = 'work_date'
    IS_WORKDAY = 'valid'


class SupplierPoolMark:
    STRATEGY = '战略'
    CORE = '核心'
    CULTIVATE = '培养'
    QUALIFIED = '合格'
    ON_WATCH = '观察'

# 供应商等级标识
class ImportanceMark:
    STRATEGY = '战略'
    CORE = '核心'
    QUALIFIED = '合格'
    CULTIVATE = '培养'
    ON_WATCH = '观察'

    ALL_IMPORTANCE_MARK = {STRATEGY, CORE, CULTIVATE, QUALIFIED, ON_WATCH}
    ALL_IMPORTANCE_LEVEL_DICT = {STRATEGY: 0,
                                 CORE: 1,
                                 CULTIVATE: 2,
                                 QUALIFIED: 3,
                                 ON_WATCH: 4}

class ParamsMark:
    MAX_ITERATION = 'max_iter'             # 最大迭代次数
    MAX_RUNTIME = 'max_runtime'                 # 最长的求解时间
    SHARE_LEVEL = 'share_level'                 # 产线的产能共用水平，0-存在可用产线集合的交集，1-按照channel区分，2-按照channel-age-group区分
    CAPACITY_AVERAGE_OBJ = 'capacity_average_obj'   # 是否启动供应商均衡目标函数
    CAPACITY_LADDEL_OBJ = 'capacity_ladder_obj'     # 是否启动供应商池成阶梯目标函数
    NU_VAR = 'nu_var'                               # 是否启用变量nu
    MIP_GAP = 'mip_gap'                                 # 求解停止准则
    ITEM_MULTI_SUPPLIER = 'item_multi_supplier'       # 一个款式内的订单可以分给多个supplier生产
    MILP_MODEL = 'milp_model'                           # 选择采用alpha还是beta为决策变量的MILP模型
    SOLUTION_MODE = 'solution_mode'
    CUT_MODE = 'cut_mode'
    IS_LIFT = 'is_lift'
    ALL_PARAMS_DICT = {MAX_ITERATION: 500,
                       MAX_RUNTIME: 3600,
                       SHARE_LEVEL: 0,
                       CAPACITY_AVERAGE_OBJ: True,
                       CAPACITY_LADDEL_OBJ: True,
                       NU_VAR: False,
                       MIP_GAP: 0.001,
                       ITEM_MULTI_SUPPLIER: False,
                       MILP_MODEL: 0,    # {0:alpha, 1:beta}
                       SOLUTION_MODE: 0,     # {0: 整体模型, 1: LBBD模型, 2: Branch-and-check}
                       CUT_MODE: 0,      # {0: greedy, 1: dbfs}
                       IS_LIFT: False
                       }


class GLOBALDATA:
    DATA = "data"
    VARS = "vars"
    CUT_GENERATOR = "cut_generator"
    ALL_GLOBAL_DATA_DICT = {
        DATA: None,
        VARS: None,
        CUT_GENERATOR: None
    }