# import gurobipy as gp
# from gurobi import *
# from constant.config import VarName, LBBDSubDataName, SetName, LBBDCutName
# from models.lbbd_model.generate_cut import GenerateCut
# from models.lbbd_model.sub_model import SubModel
#
#
# class MyCallBack(gpGRBCallback):
#     def __init__(self, data, vars):
#         self.data = data
#         self.best_obj = None
#         self.cut_generator = GenerateCut(data)
#         self.vars = vars
#
#     def __call__(self, model, where):
#         if where == gp.GRB.Callback.MIP:
#             sol_obj = model.cbGet(gp.GRB.Callback.MIP_OBJBST)
#             if self.best_obj is None or sol_obj < self.best_obj:
#                 self.best_obj = sol_obj
#                 # 添加 user cut
#                 # 款分配至实体供应商结果
#                 item_supplier_result = dict()
#                 for (item, supplier), var in self.vars[VarName.ALPHA].items():
#                     value = var.x
#                     if value > 0.001:
#                         if supplier in item_supplier_result:
#                             item_supplier_result[supplier].append(item)
#                         else:
#                             item_supplier_result[supplier] = [item]
#                 for supplier in item_supplier_result:
#                     sub_data = self.cal_sub_data(supplier, item_supplier_result[supplier])
#                     sub_model = SubModel(self.data, sub_data)
#                     sub_model.construct()
#                     is_feasible = sub_model.solve(mode=1)
#                     if not is_feasible:
#                         # 调用寻找benders cut函数
#                         item_list, mis_size = self.cut_generator.generate_mis(sub_model)
#                         model.cbCut(
#                             gp.quicksum(self.vars[VarName.ALPHA][item, supplier]
#                                         for item in item_list)
#                             - mis_size
#                             <= -1
#                         )
#                 model.update()
#
#     def cal_sub_data(self, supplier, item_list):
#         sub_data = dict()
#         sub_data[LBBDSubDataName.SUPPLIER] = supplier
#         sub_data[LBBDSubDataName.ITEM_LIST] = item_list
#         sub_data[LBBDSubDataName.ORDER_LIST] = list()
#         for item in item_list:
#             sub_data[LBBDSubDataName.ORDER_LIST].extend(self.data[SetName.ORDER_BY_ITEM_DICT][item])
#         sub_data[LBBDSubDataName.MACHINE_LIST] = self.data[SetName.MACHINE_BY_SUPPLIER_DICT][supplier]
#         return sub_data