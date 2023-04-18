# def add_z_isT_constrains(self):
#     # =============
#     # Z_is\hat_t 款式生产总量
#     # =============
#     for item in self.data[DAOptSetName.ITEM_LIST]:
#         for supplier in self.data[DAOptSetName.SUPPLIER_BY_ITEM_DICT][item]:
#             self.model.addConstr(
#                 gurobipy.quicksum(self.vars[DAOptVarName.HAT_Z][item, supplier, month]
#                                   for month in self.data[DAOptSetName.ITEM_MONTH_DICT][item]) ==
#                 self.data[DAOptParaName.ITEM_QUANTITY_DICT][item] * self.vars[DAOptVarName.ALPHA][
#                     item, supplier])
#     # =============
#     # 月生产上限
#     # =============
#     # supplimentary_lift-2 对于款式而言，月产量 <= min(款日上限，实体供应商日上限, 产线月产能)
#     for item in self.data[DAOptSetName.ITEM_LIST]:
#         item_max_occupy = self.data[DAOptParaName.ITEM_MAX_OCCUPY_DICT][item]
#         if self.data[DAOptParaName.ITEM_MAX_OCCUPY_DICT][item] < 0:
#             item_max_occupy = float('inf')
#         for month in self.data[DAOptSetName.ITEM_MONTH_DICT][item]:
#             for supplier in self.data[DAOptSetName.SUPPLIER_BY_ITEM_DICT][item]:
#                 # supplimentary_lift-2.1
#                 self.model.addConstr(self.vars[DAOptVarName.HAT_Z][item, supplier, month] <=
#                                      sum(min(item_max_occupy,
#                                              self.data[DAOptParaName.SUPPLIER_DAILY_MAX_PRODUCTION_DICT][supplier].get(
#                                                  date,
#                                                  float('inf')))
#                                          for date in self.data[DAOptSetName.ITEM_TIME_DICT][item] if
#                                          date[:7] == month))
#                 # supplimentary_lift-2.2
#                 self.model.addConstr(self.vars[DAOptVarName.HAT_Z][item, supplier, month] <=
#                                      gurobipy.quicksum(
#                                          self.data[DAOptParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
#                                              (machine, month), 0)
#                                          for machine in set.intersection(
#                                              set(self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
#                                              set(self.data[DAOptSetName.MACHINE_BY_ITEM_DICT][item])))
#                                      )
#
#     # supplimentary_lift-3 对于供应商而言，月产量 <= min(实体供应商日上限，sum(款式日上限)，产线月上限)
#     for supplier in self.data[DAOptSetName.SUPPLIER_LIST]:
#         for month in self.data[DAOptSetName.TIME_MONTH_LIST]:
#             # supplimentary_lift-3.1
#             self.model.addConstr(gurobipy.quicksum(self.vars[DAOptVarName.HAT_Z][item, supplier, month]
#                                                    for item in
#                                                    self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT][supplier]
#                                                    if (item, supplier, month) in self.vars[DAOptVarName.HAT_Z]) <=
#                                  gurobipy.quicksum(
#                                      self.vars[DAOptVarName.KAPPA][supplier, date]
#                                      for date in self.data[DAOptSetName.TIME_BY_MONTH_DICT][month] if
#                                      date[:7] == month and (supplier, date) in self.vars[DAOptVarName.KAPPA])
#                                  )
#             if self.add_binary:
#                 # supplimentary_lift-3.2
#                 self.model.addConstr(gurobipy.quicksum(self.vars[DAOptVarName.HAT_Z][item, supplier, month]
#                                                        for item in
#                                                        self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT][supplier]
#                                                        if
#                                                        (item, supplier, month) in self.vars[DAOptVarName.HAT_Z]) <=
#                                      gurobipy.quicksum(
#                                          self.data[DAOptParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
#                                              (machine, month), 0)
#                                          * self.vars[DAOptVarName.NU][machine, month]
#                                          for machine in self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]
#                                          if (machine, month) in self.vars[DAOptVarName.NU]
#                                      ))
#             else:
#                 # supplimentary_lift-3.2
#                 self.model.addConstr(gurobipy.quicksum(self.vars[DAOptVarName.HAT_Z][item, supplier, month]
#                                                        for item in
#                                                        self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT][supplier]
#                                                        if
#                                                        (item, supplier, month) in self.vars[DAOptVarName.HAT_Z]) <=
#                                      gurobipy.quicksum(
#                                          self.data[DAOptParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
#                                              (machine, month), 0)
#                                          for machine in self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]
#                                      ))
#
#     # supplimentary_lift-4 对于算法供应商而言，相同channel的算法供应商对应可生产需求月产量<= 月产能
#     for supplier in self.data[DAOptSetName.SUPPLIER_LIST]:
#         for channel in self.data[DAOptSetName.CHANNEL_LIST]:
#             for month in self.data[DAOptSetName.TIME_MONTH_LIST]:
#                 if self.add_binary:
#                     self.model.addConstr(gurobipy.quicksum(self.vars[DAOptVarName.HAT_Z][item, supplier, month]
#                                                            for item in
#                                                            set.intersection(set(
#                                                                self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT][
#                                                                    supplier]),
#                                                                set(self.data[
#                                                                        DAOptSetName.ITEM_BY_CHANNEL_DICT][
#                                                                        channel]))
#                                                            if (item, supplier, month) in self.vars[
#                                                                DAOptVarName.HAT_Z]) <=
#                                          gurobipy.quicksum(
#                                              self.data[DAOptParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
#                                                  (machine, month), 0)
#                                              * self.vars[DAOptVarName.NU][machine, month]
#                                              for machine in set.intersection(
#                                                  set(self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
#                                                  set(self.data[DAOptSetName.MACHINE_BY_CHANNEL_DICT][channel]))
#                                              if (machine, month) in self.vars[DAOptVarName.NU]
#                                          ))
#                 else:
#                     self.model.addConstr(gurobipy.quicksum(self.vars[DAOptVarName.HAT_Z][item, supplier, month]
#                                                            for item in
#                                                            set.intersection(set(
#                                                                self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT][
#                                                                    supplier]),
#                                                                set(self.data[
#                                                                        DAOptSetName.ITEM_BY_CHANNEL_DICT][
#                                                                        channel]))
#                                                            if (item, supplier, month) in self.vars[
#                                                                DAOptVarName.HAT_Z]) <=
#                                          sum(
#                                              self.data[DAOptParaName.MACHINE_MONTH_MAX_PRODUCTION_DICT].get(
#                                                  (machine, month), 0)
#                                              for machine in set.intersection(
#                                                  set(self.data[DAOptSetName.MACHINE_BY_SUPPLIER_DICT][supplier]),
#                                                  set(self.data[DAOptSetName.MACHINE_BY_CHANNEL_DICT][channel]))
#                                          ))