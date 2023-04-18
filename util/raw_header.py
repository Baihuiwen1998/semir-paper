
# ==================
# 字段值
# ==================
class AlgTypeMark:
    initiation = 0
    evaluation = 1
    production = 2
    capacity_planning = 3
    ALL_ALG_TYPE_MARK = [initiation, evaluation, production, capacity_planning]


class AlgoTypeValue:
    INITIAL = 0
    EVALUATION = 1
    PRODUCTION = 2
    ALL_ALG_TYPE_VALUE = {INITIAL,EVALUATION,PRODUCTION}


# 合作模式标识
class CoopModeMark:
    ODM = 'ODM'
    FOB = 'FOB'
    CFOB = 'CFOB'
    ALL_MARK = {ODM, FOB, CFOB}


# 订单颜色优先级标志
class DemandColorMark:
    BLACK = '黑单'
    RED = '红单'
    YELLOW = '黄单'
    GREEN = '绿单'
    BLUE = '蓝单'


# 实体供应商等级标识
class ImportanceMark:
    STRATEGIC = '战略'
    CORE = '核心'
    CULTIVATE = '培养'
    QUALIFIED = '合格'
    ON_WATCH_LIST = '观察'

    ALL_IMPORTANCE_MARK = {STRATEGIC, CORE, CULTIVATE, QUALIFIED, ON_WATCH_LIST}


    IMPORTANCE_GROUP = {
        STRATEGIC: {STRATEGIC},
        CORE: {CORE, CULTIVATE},
        QUALIFIED: {QUALIFIED, ON_WATCH_LIST}
    }


# 款-供应商匹配字段分类
class ItemMatchFeature:
    NON_SP_FEATURE = {'age_group', 'brand', 'fabric_category', 'item_category', 'sex'}


# 实体供应商产能标识
class PerformanceMark:
    A = 'A'
    B = 'B'
    C = 'C_DONE_1'
    D = 'D'
    ALL_PERFORMANCE_MARK = [A, B, C, D]


# 需求产能共用等级标识
class SharedLevelMark:
    BRAND = '品牌'
    CHANNEL = '渠道'
    CATEGORY = '品种细分池'
    BRAND_FORCE_SHARE = '品牌-强制'
    CHANNEL_FORCE_SHARE = '渠道-强制'
    CATEGORY_FORCE_SHARE = '品种细分池-强制'
    ALL_SHARED_LEVEL = {BRAND, CHANNEL, CATEGORY, BRAND_FORCE_SHARE, CHANNEL_FORCE_SHARE, CATEGORY_FORCE_SHARE}


class SpecialValue:
    EMPTY = 'EMPTY'
    INF = -1


class StatusFlag:
    # 你也不想搜索修改0/1标签的时候发现一大堆无关数字吧？
    FALSE_INT = 0
    FALSE_STR = '0'
    TRUE_INT = 1
    TRUE_STR = '1'


class SupplierPoolMark:
    CORE = 'core'
    QUALIFIED = 'qualified'
    STRATEGY = 'strategy'


# 需求类型标识
class TypeMark:
    URGENT = '加翻单'
    PRODUCTION = '订货单'
    ADVANCED = '提前单'
    DEVELOPMENT = '预估单'
    ALL_TYPE_MARK = [URGENT, PRODUCTION, ADVANCED, DEVELOPMENT]

class AgeGroupMark:
    KID = '婴童'
    ADULT = '非婴童'
    ALL_GROUP_MARK = [KID, ADULT]

class FabricCategoryMark:
    TATTING = '梭织'
    WOOL = '毛织'
    KINIT = 'at_针织'
    DENIM = '牛仔'
    ALL_FABRIC_CATEGORY_MARK = [TATTING, WOOL, KINIT, DENIM]

class ItemCapacityGroupMark:
    DENIM_GROUP = '牛仔大类'
    KINIT_GROUP = '针织大类'
    WOOL_GROUP = '毛织大类'
    TATTING_DRESS = '梭织裙子'
    TATTING_OUTFIT = '梭织外套'
    TATTING_TROUSER = '梭织裤子'
    TATTING_KID = '梭织婴童'
    TATTING_TSHIRT = '梭织衬衫'
    ALL_ITEM_CAPACITY_GROUP_MARK = [DENIM_GROUP, KINIT_GROUP, WOOL_GROUP, TATTING_TSHIRT, TATTING_KID, TATTING_TROUSER, TATTING_OUTFIT, TATTING_DRESS]
# ==================
# 特殊集合
# ==================
# 核心供应商池的划分条件
CORE_PHYSICAL_SUPPLIER_RULE = {(ImportanceMark.STRATEGIC, PerformanceMark.A),
                               (ImportanceMark.STRATEGIC, PerformanceMark.B),
                               (ImportanceMark.STRATEGIC, PerformanceMark.C),
                               (ImportanceMark.STRATEGIC, PerformanceMark.D),
                               (ImportanceMark.CORE, PerformanceMark.A),
                               (ImportanceMark.CORE, PerformanceMark.B),
                               (ImportanceMark.CORE, PerformanceMark.C),
                               (ImportanceMark.CORE, PerformanceMark.D),
                               (ImportanceMark.CULTIVATE, PerformanceMark.A),
                               (ImportanceMark.CULTIVATE, PerformanceMark.B)}

# 合格供应商池的划分条件
NON_CORE_PHYSICAL_SUPPLIER_RULE = {(ImportanceMark.CULTIVATE, PerformanceMark.C),
                                   (ImportanceMark.CULTIVATE, PerformanceMark.D),
                                   (ImportanceMark.QUALIFIED, PerformanceMark.A),
                                   (ImportanceMark.QUALIFIED, PerformanceMark.B),
                                   (ImportanceMark.QUALIFIED, PerformanceMark.C),
                                   (ImportanceMark.QUALIFIED, PerformanceMark.D),
                                   (ImportanceMark.ON_WATCH_LIST, PerformanceMark.A),
                                   (ImportanceMark.ON_WATCH_LIST, PerformanceMark.B),
                                   (ImportanceMark.ON_WATCH_LIST, PerformanceMark.C),
                                   (ImportanceMark.ON_WATCH_LIST, PerformanceMark.D),
                                   }


# ==================
# 本地文件名
# ==================
class RawFileName:
    AVERAGE_DEPTH_FILE_NAME = 'alg_average_depth'
    ALGO_DICTIONARY_FILE_NAME = 'alg_algo_dictionary'
    CALENDAR_FILE_NAME = 'alg_calendar'
    DEMAND_BOND_FILE_NAME = 'alg_demand_bond'
    DEMAND_DETAIL_FILE_NAME = 'alg_demand_detail'
    DEMAND_FILE_NAME = 'alg_demand'
    ITEM_DETAIL_FILE_NAME = 'alg_item_detail'
    ITEM_FILE_NAME = 'alg_item'
    PHYSICAL_SUPPLIER_CAPACITY_TARGET_FILE_NAME = 'alg_physical_supplier_capacity_target'
    PHYSICAL_SUPPLIER_LABEL_FILE_NAME = 'alg_physical_supplier_label'
    PHYSICAL_SUPPLIER_MAX_CAPACITY_FILE_NAME = 'physical_supplier_max_capacity'
    PHYSICAL_SUPPLIER_FILE_NAME = 'alg_physical_supplier'
    SUPPLIER_CAPACITY_FILE_NAME = 'alg_supplier_capacity'
    SUPPLIER_FILE_NAME = 'alg_supplier'
    SUPPLIER_LADDER_NAME = 'supplier_ladder'
    TIME_GROUP_FILE_NAME = 'alg_time_group'

class FileName:
    ITEM_FILE_NAME = 'item'
    MACHINE_FILE_NAME = 'machine'
    ORDER_FILE_NAME = 'order'
    SUPPLIER_FILE_NAME = 'supplier'
    CALENDAR_FILE_NAME = 'calendar'

class AnalysisFiles:
    OfflineDemandAnalysisFileName = 'demand'
    OfflineSupplierAnalysisFileName = 'supplier'
    OfflineAverageDepthFileName = 'average_depth'
    OfflinePhysicalSupplierDepthAnalysisFileName = 'physical_supplier_depth'
    OfflinePhysicalSupplierFabricAnalysisFileName = 'physical_supplier_fabric'
    OfflinePhysicalSupplierAnalysisFileName = 'physical_supplier_capacity'
    OfflinePhysicalSupplierMatchAnalysisFileName = 'physical_supplier_match'
    CorrectnessAnalysisFileName = 'correctness'


# ==================
# 数据库输入表头
# ==================
class DemandHeader:
    ADVANCEMENT_CANDIDATE = 'advancement_candidate'
    ALGO_FINISHED = 'algo_finished'
    ALGO_PHYSICAL_SUPPLIER_ID = 'algo_physical_supplier_id'
    ARRIVAL_DATE = 'arrival_date'
    DEMAND_ID = 'demand_id'
    DESIGNATED_PHYSICAL_SUPPLIER_ID = 'designated_physical_supplier_id'
    FABRIC_CATEGORY = 'fabric_category'
    FORCED_USING_PRIVATE_CAPACITY = 'forced_using_private_capacity'
    HISTORY_SUPPLIER_ID = 'history_supplier_id'
    ITEM_ID = 'item_id'
    MANUAL_ARRIVAL_DATE = 'manual_arrival_date'
    MAX_PRODUCTION_LIMIT = 'max_production_limit'
    MAX_PRODUCTION_PERIOD = 'max_production_period'
    MIN_PRODUCTION_PERIOD = 'min_production_period'
    PRIORITY = 'priority'
    SHARED_CAPACITY_AVAILABILITY = 'shared_capacity_availability'
    TYPE = 'type'


class DevelopmentDemandHeader:
    ADVANCEMENT_CANDIDATE = 'advancement_candidate'
    ALGO_FINISHED = 'algo_finished'
    ALGO_PHYSICAL_SUPPLIER_ID = 'algo_physical_supplier_id'
    ARRIVAL_DATE = 'arrival_date'
    DEMAND_ID = 'demand_id'
    DESIGNATED_PHYSICAL_SUPPLIER_ID = 'designated_physical_supplier_id'
    FORCED_USING_PRIVATE_CAPACITY = 'forced_using_private_capacity'
    HISTORY_SUPPLIER_ID = 'history_supplier_id'
    ITEM_ID = 'item_id'
    MANUAL_ARRIVAL_DATE = 'manual_arrival_date'
    MAX_PRODUCTION_LIMIT = 'max_production_limit'
    MAX_PRODUCTION_PERIOD = 'max_production_period'
    MIN_PRODUCTION_PERIOD = 'min_production_period'
    PRIORITY = 'priority'
    SHARED_CAPACITY_AVAILABILITY = 'shared_capacity_availability'
    TYPE = 'type'


class ProductionDemandHeader:
    ALGO_FINISHED = 'algo_finished'
    ALGO_PHYSICAL_SUPPLIER_ID = 'algo_physical_supplier_id'
    ARRIVAL_DATE = 'arrival_date'
    DEMAND_ID = 'demand_id'
    DESIGNATED_PHYSICAL_SUPPLIER_ID = 'designated_physical_supplier_id'
    FORCED_USING_PRIVATE_CAPACITY = 'forced_using_private_capacity'
    HISTORY_SUPPLIER_ID = 'history_supplier_id'
    ITEM_ID = 'item_id'
    MAX_PRODUCTION_LIMIT = 'max_production_limit'
    MAX_PRODUCTION_PERIOD = 'max_production_period'
    MIN_PRODUCTION_PERIOD = 'min_production_period'
    PRIORITY = 'priority'
    SHARED_CAPACITY_AVAILABILITY = 'shared_capacity_availability'
    TYPE = 'type'


class DemandDetailHeader:
    DEMAND_ID = 'demand_id'
    DUE_DATE = 'due_date'
    CAPACITY_NEEDED = 'capacity_needed'


class ItemHeader:
    AGE_GROUP = 'age_group'
    AMOUNT_LEVEL = 'amount_level'
    BATCH = 'batch'
    BRAND = 'brand'
    CHANNEL = 'channel'
    COOP_MODE = 'coop_mode'
    FABRIC_CATEGORY = 'fabric_category'
    INTERNAL_ITEM_EARLY_ID = 'internal_item_early_id'
    INTERNAL_ITEM_ID = 'internal_item_id'
    IS_PK_ITEM = 'is_pk_item'
    IS_POPULAR_ITEM = 'is_popular_item'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    ITEM_CATEGORY = 'item_category'
    ITEM_ID = 'item_id'
    QUARTER = 'quarter'
    SEX = 'sex'
    YEAR = 'year'
    SHARE_LEVEL = 'share_level'


class DevelopmentItemHeader:
    AGE_GROUP = 'age_group'
    AMOUNT_LEVEL = 'amount_level'
    BATCH = 'batch'
    BRAND = 'brand'
    CHANNEL = 'channel'
    COOP_MODE = 'coop_mode'
    FABRIC_CATEGORY = 'fabric_category'
    INTERNAL_ITEM_EARLY_ID = 'internal_item_early_id'
    INTERNAL_ITEM_ID = 'internal_item_id'
    IS_PK_ITEM = 'is_pk_item'
    IS_POPULAR_ITEM = 'is_popular_item'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    ITEM_CATEGORY = 'item_category'
    ITEM_ID = 'item_id'
    QUARTER = 'quarter'
    SEX = 'sex'
    YEAR = 'year'


class ProductionItemHeader:
    AGE_GROUP = 'age_group'
    AMOUNT_LEVEL = 'amount_level'
    BATCH = 'batch'
    BRAND = 'brand'
    CHANNEL = 'channel'
    COOP_MODE = 'coop_mode'
    FABRIC_CATEGORY = 'fabric_category'
    INTERNAL_ITEM_EARLY_ID = 'internal_item_early_id'
    INTERNAL_ITEM_ID = 'internal_item_id'
    IS_PK_ITEM = 'is_pk_item'
    IS_POPULAR_ITEM = 'is_popular_item'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    ITEM_CATEGORY = 'item_category'
    ITEM_ID = 'item_id'
    QUARTER = 'quarter'
    SEX = 'sex'
    YEAR = 'year'


class ItemDetailHeader:
    ITEM_ID = 'item_id'
    LABEL_KEY = 'label_key'
    LABEL_VALUE = 'label_value'


class DevelopmentItemDetailHeader:
    ITEM_ID = 'item_id'
    LABEL_KEY = 'label_key'
    LABEL_VALUE = 'label_value'


class ProductionItemDetailHeader:
    ITEM_ID = 'item_id'
    LABEL_KEY = 'label_key'
    LABEL_VALUE = 'label_value'


class SupplierHeader:
    AGE_GROUP = 'age_group'
    BRAND = 'brand'
    CHANNEL = 'channel'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    FABRIC_CATEGORY = 'fabric_category'
    FORCED_SHARED_CAPACITY_AVAILABILITY = 'forced_shared_capacity_availability'
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'
    QUARTER = 'quarter'
    SUPPLIER_ID = 'supplier_id'
    YEAR = 'year'


class SupplierCapacityHeader:
    AVAILABLE_CAPACITY = 'available_capacity'
    CAPACITY_RESERVATION_RATIO = 'capacity_reservation_ratio'
    CAPACITY_OVERRIDE_RATIO = 'capacity_override_ratio'
    EXTRA_ORDER_OCCUPIED_CAPACITY = 'extra_order_occupied_capacity'
    MONTH = 'month'
    PLANNED_CAPACITY = 'planned_capacity'
    SUPPLIER_ID = 'supplier_id'


class SupplierLadderHeader:
    CORE_RATIO = 'core_ratio'
    QUALIFIED_RATIO = 'qualified_ratio'
    STAGE = 'stage'
    STRATEGY_RATIO = 'strategy_ratio'
    TYPE = 'type'


class PhysicalSupplierHeader:
    IMPORTANCE = 'importance'
    PERFORMANCE = 'performance'
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'


class PhysicalSupplierCapacityTargetHeader:
    MONTH = 'month'
    OCCUPATION_TARGET = 'occupation_target'
    OCCUPATION_TARGET_ADJUST_RATIO = 'occupation_target_adjust_ratio'
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'


class PhysicalSupplierMaxCapacityHeader:
    DATE = 'date'
    FABRIC_CATEGORY = 'fabric_category'
    HISTORY_DAILY_OCCUPATION = 'history_daily_occupation'
    MAX_LINE_LIMIT = 'max_line_limit'
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'


class PhysicalSupplierLabelHeader:
    LABEL_KEY = 'label_key'
    LABEL_PRIORITY = 'label_priority'
    LABEL_VALUE = 'label_value'
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'


class AverageDepthHeader:
    AGE_GROUP = 'age_group'
    AVERAGE_DEPTH = 'average_depth'
    BRAND = 'brand'
    CHANNEL = 'channel'
    FABRIC_CATEGORY = 'fabric_category'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'


class AlgoDictionaryHeader:
    DICTIONARY_KEY = 'dictionary_key'
    DICTIONARY_VALUE = 'dictionary_value'


class AlgoDictKeyHeader:
    BY_PASS_CHANNEL_BARRIER = 'bypass_channel_barrier'
    MAX_PK_PHYSICAL_SUPPLIER = 'max_pk_physical_supplier'


class CalendarHeader:
    DATE = 'work_date'
    IS_WORKDAY = 'valid'


class DemandAnalysisHeader:
    DEMAND_ID = 'demand_id'
    TYPE = 'type'
    PRIORITY = 'priority'
    SHARED_CAPACITY_AVAILABILITY = 'shared_capacity_availability'
    IS_PK_ITEM = 'is_pk_item'
    ITEM_ID = 'item_id'
    AMOUNT_LEVEL = 'amount_level'
    ITEM_CATEGORY = 'item_category'
    BRAND = 'brand'
    CHANNEL = 'channel'
    AGE_GROUP = 'age_group'
    FABRIC_CATEGORY = 'fabric_category'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    IS_COMPLETE = 'is_complete'
    SUPPLIER_ID = 'supplier_id'
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'
    CAPACITY_NEEDED = 'capacity_needed'
    PRODUCTION = 'production'
    IS_SHARED_PRODUCTION = 'is_shared_production'
    HISTORY_SUPPLIER_CONDITION = 'history_supplier_condition'
    ARRIVAL_DATE = 'arrival_date'
    DUE_DATE = 'due_date'
    ACTUAL_ONLINE_DATE = 'actual_online_date'
    ACTUAL_OFFLINE_DATE = 'actual_offline_date'
    MATERIAL_CODE = 'material_code'


class SupplierAnalysisHeader:
    SUPPLIER_ID = 'supplier_id'
    MONTH = 'month'
    SUPPLIER_PRODUCTION = 'supplier_production'
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'
    BRAND = 'brand'
    CHANNEL = 'channel'
    AGE_GROUP = 'age_group'
    FABRIC_CATEGORY = 'fabric_category'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    PLANNED_CAPACITY = 'planned_capacity'
    AVAILABLE_CAPACITY = 'available_capacity'
    LEFTOVER_CAPACITY = 'leftover_capacity'
    POOL = 'supplier_pool'


class AverageDepthAnalysisHeader:
    BRAND = 'brand'
    CHANNEL = 'channel'
    AGE_GROUP = 'age_group'
    FABRIC_CATEGORY = 'fabric_category'
    ITEM_CAPACITY_GROUP = 'item_capacity_group'
    AVERAGE_DEPTH = 'average_depth'
    CORE_PHYSICAL_SUPPLIER_AVERAGE_DEPTH = 'core_physical_supplier_average_depth'
    NON_CORE_PHYSICAL_SUPPLIER_AVERAGE_DEPTH = 'non_core_physical_supplier_average_depth'


class PhysicalSupplierDepthAnalysisHeader:
    PHYSICAL_SUPPLIER_ID = 'physical_supplier_id'
    PHYSICAL_SUPPLIER_AVERAGE_DEPTH = 'physical_supplier_average_depth'

class DemandAssignmentDetailHeader:
    DEMAND_ID = 'alg_demand_id'
    PLAN_TYPE = 'plan_type'
    TIME = 'assignment_date'
    SUPPLIER_ID = 'line_id'
    PHYSICAL_SUPPLIER_ID = 'supplier_code'
    USED_CAPACITY = 'used_capacity'


