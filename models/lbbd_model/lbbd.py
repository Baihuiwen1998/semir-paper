from models.lbbd_model.generate_cut import GenerateCut
from models.lbbd_model.master_model import MasterModel
from config import *
from models.lbbd_model.relaxed_master_model import RelaxedMasterModel
from models.lbbd_model.relaxed_sub_model import RelaxedSubModel
from models.lbbd_model.sub_model import SubModel
from models.lbbd_model.generate_cut import cal_sub_data
import logging
import time
from util.header import *

formatter = '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
logging.basicConfig(level=logging.DEBUG, format=formatter)
logger = logging.getLogger(__name__)

class LogicBasedBenders:
    """
    logic based benders
    """

    def __init__(self, data):
        """
        模型初始化
        :param data: 记录建模所需的所有信息
        :param name: 模型名称
        """
        # 基础数据记录
        self.data = data
        # 初始化模型
        self.master_model = None  # 主问题模型
        self.sub_models = dict()
        self.cut_generator = None
        self.master_data = dict()
        self.sub_data = dict()
        self.lbbd_cut_data = dict()
        self.result = dict()

    def solve(self):
        """
        Logic-based benders 求解主函数
        """

        # 初始化数据
        iteration = 0
        self.update_data()

        # 构建主问题模型
        self.master_model = MasterModel(self.data)
        self.master_model.construct()

        # 构建加强割算法类
        self.cut_generator = GenerateCut(self.data)

        start_time = time.time()
        # 开始lbbd迭代循环
        while iteration < ParamsMark.ALL_PARAMS_DICT[ParamsMark.MAX_ITERATION]:
            iteration += 1
            all_sub_feasible = True

            # 求解主问题
            self.master_data = self.master_model.solve_lbbd(self.lbbd_cut_data)

            # 清空数据
            self.update_data()

            # 创建子问题进行可行性检验
            for supplier in self.master_data[ResultName.ITEM_SUPPLIER]:
                sub_data = cal_sub_data(self.data, supplier, self.master_data[ResultName.ITEM_SUPPLIER][supplier])
                sub_model = SubModel(self.data, sub_data)
                sub_model.construct()
                self.sub_models[supplier] = sub_model
                is_feasible = sub_model.solve(mode=1)
                if not is_feasible:
                    all_sub_feasible = False
                    # 调用寻找benders cut函数
                    self.lbbd_cut_data[LBBDCutName.MIS_BY_SUPPLIER_DICT][sub_model.supplier], \
                    self.lbbd_cut_data[LBBDCutName.MIS_SIZE_BY_SUPPLIER_DICT][sub_model.supplier] = \
                        self.cut_generator.generate_mis(sub_model)

            # 如果全都可行，求解子问题
            if all_sub_feasible:
                self.result[LBBDResultName.MASTER_RESULT] = self.master_data
                self.result[LBBDResultName.SUB_RESULT] = dict()
                for supplier in self.sub_models:
                    sub_result = self.sub_models[supplier].solve(mode=2)
                    self.result[LBBDResultName.SUB_RESULT][supplier] = sub_result
                end_time = time.time()
                self.result[LBBDResultName.RUN_TIME] = end_time - start_time
                self.result[LBBDResultName.OBJ_VALUE] = self.master_model.model.objVal
                self.result[LBBDResultName.LOWER_BOUND] = self.master_model.model.objVal
                self.result[LBBDResultName.ITERATION] = iteration
                return True, self.result
            # 否则，更新计算时长
            end_time = time.time()
            if end_time - start_time > ParamsMark.ALL_PARAMS_DICT[ParamsMark.MAX_RUNTIME]:
                # 超出计算时长
                # 求解子问题得到最多可以生产的款式数
                self.result[LBBDResultName.SUB_RESULT] = dict()
                for supplier in self.master_data[ResultName.ITEM_SUPPLIER]:
                    sub_data = cal_sub_data(self.data, supplier, self.master_data[ResultName.ITEM_SUPPLIER][supplier])
                    sub_model = RelaxedSubModel(self.data, sub_data, 0, 3)
                    sub_model.construct()
                    sub_result = sub_model.solve(mode=2)
                    self.result[LBBDResultName.SUB_RESULT][supplier] = sub_result
                # 建立松弛的主问题求解
                relaxed_master_model = RelaxedMasterModel(self.data)
                relaxed_master_model.construct()
                relaxed_master_model.add_fixed_assignments(self.result[LBBDResultName.SUB_RESULT])
                self.result[LBBDResultName.MASTER_RESULT] = relaxed_master_model.solve(self.lbbd_cut_data)
                self.result[LBBDResultName.RUN_TIME] = end_time - start_time
                self.result[LBBDResultName.OBJ_VALUE] = relaxed_master_model.model.objVal
                self.result[LBBDResultName.LOWER_BOUND] = self.master_model.model.objVal
                self.result[LBBDResultName.ITERATION] = iteration
                break
        # 超出时长or MAX_ITERATION 时，获取一个可行解
        return False, self.result


    def update_data(self):
        self.sub_models = dict()
        self.result = dict()
        self.lbbd_cut_data[LBBDCutName.MIS_BY_SUPPLIER_DICT] = dict()
        self.lbbd_cut_data[LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT] = dict()
        for supplier in self.data[SetName.SUPPLIER_LIST]:
            self.lbbd_cut_data[LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT][supplier] = list()
        self.lbbd_cut_data[LBBDCutName.MIS_BY_SUPPLIER_DICT] = dict()
        self.lbbd_cut_data[LBBDCutName.MIS_SIZE_BY_SUPPLIER_DICT] = dict()





