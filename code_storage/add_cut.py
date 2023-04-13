# # 将MIS放到其他supplier上进行测试
#                 self.add_mis_to_other_suppliers(item_list, supplier)
#
# def add_mis_to_other_suppliers(self, item_list, tested_supplier):
#     """
#     :param item_list:
#     :return:
#     """
#     for supplier in self.data[DAOptSetName.SUPPLIER_LIST]:
#         if supplier != tested_supplier:
#             filtered_item_list = set.intersection(set(item_list),
#                                                   set(self.data[DAOptSetName.ITEM_BY_SUPPLIER_DICT][supplier]))
#             sub_data = self.cal_sub_data(supplier, filtered_item_list)
#             sub_model = SubModel(self.data, sub_data)
#             sub_model.construct()
#             is_feasible = sub_model.solve(mode=1)
#             if not is_feasible:
#                 self.lbbd_cut_data[LBBDCutName.INFEASIBLE_ITEM_SET_LIST_BY_SUPPLIER_DICT][supplier].append(
#                     filtered_item_list)
