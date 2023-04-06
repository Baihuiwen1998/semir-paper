# if ParamsMark.ALL_PARAMS_DICT[ParamsMark.LAMBDA_VAR]:
#     logger.info('添加变量：松弛子问题辅助变量lambda_st')
#     self.vars[VarName.LAMBDA] = {(supplier, date): self.model.addVar(
#         name=var_name_regularizer(f'V_{VarName.LAMBDA}({supplier}_{date})'),
#         vtype=gurobipy.GRB.BINARY)
#         for supplier in self.data[DAOptSetName.SUPPLIER_LIST]
#         for date in self.data[DAOptSetName.TIME_LIST]}
#
#
#
#     def add_lambda(self):
#         # =============
#         # lambda_st 定义用约束
#         # =============
#         for supplier in self.data[DAOptSetName.SUPPLIER_LIST]:
#             for date in self.data[DAOptSetName.TIME_LIST]:
#                 # 内含有可在physical_supplier生产且生产日期包括date的款式列表
#                 item_list = []
#                 for item in self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT].get(supplier, []):
#                     if date in self.data[DAOptSetName.ITEM_TIME_DICT][item]:
#                         item_list.append(item)
#                 # test-6.1
#                 self.model.addConstr(
#                     self.vars[VarName.LAMBDA][supplier, date] <=
#                     gurobipy.quicksum(self.vars[VarName.ALPHA][item, supplier] for item in item_list))
#                 # test-6.2
#                 for item in item_list:
#                     self.model.addConstr(
#                         self.vars[VarName.LAMBDA][supplier, date] >=
#                         self.vars[VarName.ALPHA][item, supplier])
#
#
#         if ParamsMark.ALL_PARAMS_DICT[ParamsMark.LAMBDA_VAR]:
#             self.add_lambda()
#
# class ParamsMark:
#     MAX_ITERATION = 'max_iteration'             # 最大迭代次数
#     MAX_RUNTIME = 'max_runtime'                 # 最长的求解时间
#     SHARE_LEVEL = 'share_level'                 # 产线的产能共用水平，0-存在可用产线集合的交集，1-按照channel区分，2-按照channel-age-group区分
#     CAPACITY_AVERAGE_OBJ = 'capacity_average_obj'   # 是否启动供应商均衡目标函数
#     CAPACITY_LADDEL_OBJ = 'capacity_ladder_obj'     # 是否启动供应商池成阶梯目标函数
#     NU_VAR = 'nu_var'                               # 是否启用变量nu
#     LAMBDA_VAR = 'lambda_var'                       # 是否启用变量lambda
#     ALL_PARAMS_DICT = {MAX_ITERATION: 500,
#                        MAX_RUNTIME: 3600,
#                        SHARE_LEVEL: 1,
#                        CAPACITY_AVERAGE_OBJ: True,
#                        CAPACITY_LADDEL_OBJ: True,
#                        NU_VAR: False
#                        LAMBDA_VAR: False
#                        }