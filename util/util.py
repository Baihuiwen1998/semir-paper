

import datetime
import functools
import logging
import os
import time
import typing

logger = logging.getLogger(__name__)


# def name_regulator(name_f_string, prefix=''):
#     """
#     标准化的变量命名。
#     :param name_f_string: 原始的字符串
#     :param prefix: 字符串前缀，默认为空
#     :return:
#     """
#     v_name_translated = pinyin.get(name_f_string, format="strip")
#     if prefix != '':
#         v_name_formatted = f'{prefix}@{v_name_translated}'
#     else:
#         v_name_formatted = f'{v_name_translated}'
#     v_name = re.sub(" ", "", v_name_formatted)
#     return v_name

def str2datetime(date_str, sep=''):
    """
    将str格式的date转化为datetime格式
    :param date_str: str格式的date
    :param sep: 年月日之间的分隔符
    :return: datetime格式的date
    """
    date_format = f'%Y{sep}%m{sep}%d %H:%M:%S'
    return datetime.datetime.strptime(date_str, date_format)


def str2date(date_str):
    """
    将str格式的date转化为date格式
    :param date_str: str格式的date
    :param sep: 年月日之间的分隔符
    :return: date格式的date
    """

    return datetime.date(*map(int, date_str.split('-')))


def datetime2str(date_time, sep=''):
    """
    将datetime格式的date转化为str格式
    :param date_time: datetime格式的date
    :param sep: 年月日之间的分隔符
    :return: str格式的date
    """
    date_format = f'%Y{sep}%m{sep}%d %H:%M:%S'
    return date_time.strftime(date_format)


def date2str(date_time, sep='-'):
    """
    将date格式的date转化为str格式
    :param date_time: date格式的date
    :param sep: 年月日之间的分隔符
    :return: str格式的date
    """
    date_format = f'%Y{sep}%m{sep}%d'
    return date_time.strftime(date_format)


def name_regulator(name_f_string, prefix=''):
    return prefix + name_f_string


def remove_path(path):
    """
    删除某一路径，以及内部所有的文件和文件夹
    :param path: 需要被删除的路径
    :return:
    """
    if os.path.isdir(path):
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)
            if os.path.isdir(file_path):
                remove_path(file_path)
            else:
                os.remove(file_path)
        os.rmdir(path)
    elif os.path.isfile(path):
        os.remove(path)
    else:
        logger.warning('{}路径无实体'.format(path))


def topological_sort(graph, nodes, degree_flag='IN'):
    """
    利用图的关系，结合拓扑排序，获取与所选点相关的所有点，并按拓扑排序进行排列
    :param graph: 拓扑图，dict存储，用key-value表示先后关系
    :param nodes: 需要进行拓扑排序的点
    :param degree_flag: 关系图表达的内容，'IN' 表示key->value的依赖关系，'OUT' 表示value->key的依赖关系
    :return:
    """
    # #计算每个顶点的入度
    need_node_queue = [u for u in nodes if u in graph]
    nodes_result = []
    degrees = dict((u, 0) for u in need_node_queue)
    while need_node_queue:
        node = need_node_queue.pop()
        nodes_result.append(node)
        for next_node in graph.get(node, []):
            if next_node not in degrees.keys():
                degrees[next_node] = 1
                need_node_queue.append(next_node)
            else:
                degrees[next_node] += 1

    # 筛选入度为0的顶点
    node_queue = [node for node, degree in degrees.items() if degree == 0]
    sort_result = []
    while node_queue:
        node = node_queue.pop()
        sort_result.append(node)
        for next_node in graph.get(node, []):
            degrees[next_node] -= 1
            if degrees[next_node] == 0:
                node_queue.append(next_node)

    # 长度不同，说明图中有环，不存在拓扑排序
    if len(sort_result) == len(degrees):
        if degree_flag == 'IN':
            return sort_result
        else:
            return list(reversed(sort_result))
    else:
        error_info = 'there is a circle in the map.'
        logger.error(error_info)
        raise Exception(error_info)


def dataframe_row_to_dataclass(source, destination, rename_map: dict):
    """
    完成 dataframe行 到 dataclass 的转换, 按照重命名字典进行更新
    :param source: 来源dataframe行
    :param destination: 目标数据类
    :param rename_map: 来源与目标的重命名映射
    :return:
    """
    if rename_map is None:
        rename_map = {}
    destination_source_name_map = {v: k for k, v in rename_map.items()}
    for destination_name in destination.__dict__.keys():
        if destination_name in destination_source_name_map.keys():
            source_value = source[destination_source_name_map[destination_name]]
            if source_value is not None:
                destination.__dict__[destination_name] = source_value


def dataclass_dict_group_by_fields(dataclass_dict: dict, fields) -> dict:
    """
    将以字典value存储的dataclass按照dataclass里面的字段进行筛选
    :param dataclass_dict: 需要进行筛选的dataclass的字典
    :param fields: 需要筛选的字段名，若为单值则输出一级dict， 若为list或set，则输出二级dict，一级的key是所有的筛选字段名
    :return: 根据字典名汇总的dataclass字典的key的字典
    """
    result_dict = dict()
    if isinstance(fields, (list, set)):
        result_dict = {k: dict() for k in fields}
        for idx, dataclass in dataclass_dict.items():
            for field in fields:
                property_data = dataclass.__dict__[field]
                if isinstance(property_data, set):
                    for element in property_data:
                        if element not in result_dict[field]:
                            result_dict[field][element] = set()
                        result_dict[field][element].add(idx)
                elif isinstance(property_data, (int, str)):
                    property_data = str(property_data)
                    if property_data not in result_dict[field]:
                        result_dict[field][property_data] = set()
                    result_dict[field][property_data].add(idx)
    elif isinstance(fields, str):
        for idx, dataclass in dataclass_dict.items():
            property_data = dataclass.__dict__[fields]
            if isinstance(property_data, set):
                for element in property_data:
                    if element not in result_dict:
                        result_dict[element] = set()
                    result_dict[element].add(idx)
            elif isinstance(property_data, (int, str)):
                property_data = str(property_data)
                if property_data not in result_dict:
                    result_dict[property_data] = set()
                result_dict[property_data].add(idx)
    else:
        logger.warning("Unsupported type {} as fields".format(type(fields)))
    return result_dict


def get_interval_date(start: datetime.date, end: datetime.date,
                      last_date: bool = False) -> typing.Set[datetime.date]:
    """
    输出所有在起止时间内的日期，以集合形式输出
    :param start: 开始时间
    :param end: 结束时间
    :param last_date: 输出的list是否要包含最后一天，True则包含，False则不包含
    :return: 从开始时间到结束时间的日期集合
    """
    result_date = set()
    while start < end:
        result_date.add(start)
        start += datetime.timedelta(days=1)

    if last_date:
        result_date.add(end)

    return result_date


def var_name_regularizer(name_f_string, prefix='v'):
    """
    标准化的变量命名。
    :param name_f_string: 原始的字符串
    :param prefix: 字符串前缀，默认为'v'
    :return:
    """
    # v_name_translated = pinyin.get(name_f_string, format="strip")
    # v_name_formatted = f'{prefix}@{v_name_translated}'
    # v_name = re.sub("\s", "", v_name_formatted)
    # return v_name
    return name_f_string


def print_func_time(func_name=None, least_time=0):
    """
    装饰器，用于统计算法的求解时间。
    可以根据需要设置最少的计算用时。
    :param func_name: 求解名称
    :param least_time: 最少的求解用时
    :return:
    """
    def decorator_main_name(func):
        @functools.wraps(func)
        def wrapper_main_name(*args, **kwargs):
            if func_name is None:
                func_name_new = func.__name__
            else:
                func_name_new = func_name
            func_start_time = datetime.datetime.now()
            logger.info('time start for function[{}]'.format(func_name_new))
            func_value = func(*args, **kwargs)
            func_end_time = datetime.datetime.now()
            logger.info('time end for function[{}]'.format(func_name_new))
            logger.info('duration for function[{}] is {}'.format(func_name_new, func_end_time - func_start_time))
            func_seconds = (func_end_time - func_start_time).total_seconds()
            left_seconds = least_time - func_seconds
            if left_seconds > 0:
                time.sleep(left_seconds)
                logger.info('duration for least is {}'.format(datetime.timedelta(seconds=left_seconds)))
            return func_value
        return wrapper_main_name
    return decorator_main_name

def set_to_str(info_set):
    s = ''
    for item in sorted(info_set):
        s = s + str(item)
    return s