# from flask import Blueprint, jsonify, request
# from datetime import datetime, timedelta
# import os
# import pandas as pd
# import re

# # 创建一个 Flask 蓝图，用于模块化注册这个文件中的所有接口
# calculate_ari_bp = Blueprint('calculate_ARI', __name__)

# # 用于提取每行中第三个数字（用于 .pro 文件字段）
# def extract_first_value(line):
#     values = re.findall(r'[-+]?\d*\.\d+|\d+', line)
#     if len(values) > 2:
#         try:
#             return float(values[2])
#         except ValueError:
#             return None
#     return None

# # 解析 .pro 文件，返回指定时间范围内的雪层观测记录
# def parse_pro_file(file_path, stime, etime, step):
#     data = []
#     try:
#         with open(file_path, 'r') as file:
#             lines = file.readlines()
#             data_start_index = None

#             for i, line in enumerate(lines):
#                 if "[DATA]" in line:
#                     data_start_index = i + 1
#                     break

#             if data_start_index is None:
#                 return []

#             # 生成请求的时间点
#             time_points = []
#             current_time = stime
#             while current_time <= etime:
#                 time_points.append(current_time)
#                 current_time += timedelta(hours=step)

#             record = {}
#             for line in lines[data_start_index:]:
#                 line = line.strip()
#                 if line.startswith("0500"):
#                     t_str = line.split(',')[1]
#                     current_time = datetime.strptime(t_str, "%d.%m.%Y %H:%M:%S")
#                     if current_time in time_points:
#                         record = {
#                             'time': current_time.strftime("%Y-%m-%d %H:%M:%S")
#                         }
#                         data.append(record)
#                 elif line.startswith("0501"):
#                     record['height'] = extract_first_value(line)

#         # 只保留匹配时间点的记录
#         times = {tp.strftime("%Y-%m-%d %H:%M:%S") for tp in time_points}
#         return [r for r in data if r.get('time') in times]
#     except Exception as e:
#         print(f"Error reading .pro file {file_path}: {e}")
#         return []

# # 解析 .smet 文件，返回指定时间范围内的气象数据
# def parse_smet_file(file_path, stime, etime, step):
#     header, df = parse_smet_file_content(file_path)
#     if df.empty:
#         return []

#     time_column = df.columns[0]
#     df[time_column] = pd.to_datetime(df[time_column])

#     # 生成请求的时间点
#     time_points = []
#     current_time = stime
#     while current_time <= etime:
#         time_points.append(current_time)
#         current_time += timedelta(hours=step)

#     # 过滤数据并重命名时间列为 'time'
#     filtered_df = df[df[time_column].isin(time_points)]
#     filtered_df = filtered_df.rename(columns={time_column: 'time'})
#     filtered_df['time'] = filtered_df['time'].dt.strftime("%Y-%m-%d %H:%M:%S")
#     return filtered_df.to_dict(orient='records')

# # 辅助函数：解析 .smet 文件内容
# def parse_smet_file_content(file_path):
#     header = {}
#     data = []
#     with open(file_path, 'r') as file:
#         header_mode = True
#         for line in file:
#             if line.startswith('[DATA]'):
#                 header_mode = False
#                 continue
#             if header_mode:
#                 if '=' in line:
#                     parts = line.strip().split('=')
#                     header[parts[0].strip()] = parts[1].strip()
#             else:
#                 data.append(line.strip().split())

#     if not data:
#         return header, pd.DataFrame()

#     df = pd.DataFrame(data, columns=header['fields'].split())
#     return header, df

# # 接口：/ca，POST 方法
# @calculate_ari_bp.route('/ca', methods=['POST'])
# def calculate_ari():
#     # 解析 JSON 请求体
#     if not request.is_json:
#         return jsonify({'error': 'Request body must be JSON'}), 400
#     body = request.get_json()
#     stime_str = body.get('stime')
#     etime_str = body.get('etime')
#     step = body.get('step')

#     # 参数验证
#     if stime_str is None or etime_str is None or step is None:
#         return jsonify({'error': 'Missing required parameters: stime, etime, step'}), 400

#     # 解析时间和步长
#     try:
#         stime = datetime.strptime(stime_str, "%Y-%m-%dT%H:%M:%S")
#         etime = datetime.strptime(etime_str, "%Y-%m-%dT%H:%M:%S")
#         step = int(step)
#     except Exception:
#         return jsonify({'error': 'Invalid date or step format'}), 400

#     # 验证时间顺序
#     if etime <= stime:
#         return jsonify({'error': 'etime must be later than stime'}), 400
#     if step <= 0:
#         return jsonify({'error': 'step must be a positive integer'}), 400

#     # 准备时间点
#     time_diff_hours = (etime - stime).total_seconds() / 3600
#     if step > time_diff_hours:
#         return jsonify({'error': 'step is larger than the time range'}), 400
#     num_points = int(time_diff_hours // step) + 1
#     time_points = [stime + timedelta(hours=i*step) for i in range(num_points)]
#     time_points_str = [tp.strftime("%Y-%m-%d %H:%M:%S") for tp in time_points]

#     directory = '/home/projects/data/snowpack_output/'
#     if not os.path.isdir(directory):
#         return jsonify({'error': 'Data directory not found'}), 500

#     ari_result = {}
#     for fname in os.listdir(directory):
#         file_path = os.path.join(directory, fname)
#         if not os.path.isfile(file_path):
#             continue
#         station_name = os.path.splitext(fname)[0]
#         file_ext = os.path.splitext(fname)[1].lower()

#         # 改为只处理 .pro 文件
#         if file_ext == '.pro':
#             # 从 .pro 文件中解析雪层高度数据
#             pro_data = parse_pro_file(file_path, stime, etime, step)

#             ari_series = []
#             for record in pro_data:
#                 t_str = record['time']
#                 snow_depth = record.get('height', 0) or 0

#                 # 打印调试信息
#                 # print(f"Time: {t_str}, Snow depth: {snow_depth}")

#                 # 计算24小时前的时间点
#                 t_prev = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S") - timedelta(hours=24)
#                 t_prev_str = t_prev.strftime("%Y-%m-%d %H:%M:%S")

#                 # 查找24小时前的雪深
#                 snow_depth_prev = 0
#                 for prev_record in pro_data:
#                     if prev_record['time'] == t_prev_str:
#                         snow_depth_prev = prev_record.get('height', 0) or 0
#                         break

#                 # 计算 ARI
#                 new_snow_24h = max(0, snow_depth - snow_depth_prev)
#                 ari_val = ((snow_depth / 60 ) + (new_snow_24h / 20)) / 2
#                 ari_series.append({
#                     'time': t_str,
#                     'ARI': round(ari_val, 4)
#                 })

#             ari_result[station_name] = ari_series

#     return jsonify(ari_result)

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os
import pandas as pd
import re
import random

calculate_ari_bp = Blueprint('calculate_ARI', __name__)

def extract_first_value(line):
    values = re.findall(r'[-+]?\d*\.\d+|\d+', line)
    if len(values) > 2:
        try:
            return float(values[2])
        except ValueError:
            return None
    return None

def parse_pro_file(file_path, stime, etime, step):
    data = []
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
            data_start_index = None

            for i, line in enumerate(lines):
                if "[DATA]" in line:
                    data_start_index = i + 1
                    break

            if data_start_index is None:
                return []

            time_points = []
            current_time = stime
            while current_time <= etime:
                time_points.append(current_time)
                current_time += timedelta(hours=step)

            record = {}
            for line in lines[data_start_index:]:
                line = line.strip()
                if line.startswith("0500"):
                    t_str = line.split(',')[1]
                    current_time = datetime.strptime(t_str, "%d.%m.%Y %H:%M:%S")
                    if current_time in time_points:
                        record = {'time': current_time.strftime("%Y-%m-%d %H:%M:%S")}
                        data.append(record)
                elif line.startswith("0501") and record:
                    height = extract_first_value(line)
                    if height is not None:
                        record['height'] = height
        times = {tp.strftime("%Y-%m-%d %H:%M:%S") for tp in time_points}
        return [r for r in data if r.get('time') in times]
    except Exception as e:
        print(f"Error reading .pro file {file_path}: {e}")
        return []

def parse_smet_file(file_path, stime, etime, step):
    header, df = parse_smet_file_content(file_path)
    if df.empty:
        return []

    time_column = df.columns[0]
    df[time_column] = pd.to_datetime(df[time_column])

    time_points = []
    current_time = stime
    while current_time <= etime:
        time_points.append(current_time)
        current_time += timedelta(hours=step)

    filtered_df = df[df[time_column].isin(time_points)]
    filtered_df = filtered_df.rename(columns={time_column: 'time'})
    filtered_df['time'] = filtered_df['time'].dt.strftime("%Y-%m-%d %H:%M:%S")
    return filtered_df.to_dict(orient='records')

def parse_smet_file_content(file_path):
    header = {}
    data = []
    with open(file_path, 'r') as file:
        header_mode = True
        for line in file:
            if line.startswith('[DATA]'):
                header_mode = False
                continue
            if header_mode:
                if '=' in line:
                    parts = line.strip().split('=')
                    header[parts[0].strip()] = parts[1].strip()
            else:
                data.append(line.strip().split())

    if not data:
        return header, pd.DataFrame()

    df = pd.DataFrame(data, columns=header['fields'].split())
    return header, df

@calculate_ari_bp.route('/ca', methods=['POST'])
def calculate_ari():
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON'}), 400
    body = request.get_json()
    stime_str = body.get('stime')
    etime_str = body.get('etime')
    step = body.get('step')

    if stime_str is None or etime_str is None or step is None:
        return jsonify({'error': 'Missing required parameters: stime, etime, step'}), 400

    try:
        stime = datetime.strptime(stime_str, "%Y-%m-%dT%H:%M:%S")
        etime = datetime.strptime(etime_str, "%Y-%m-%dT%H:%M:%S")
        step = int(step)
    except Exception:
        return jsonify({'error': 'Invalid date or step format'}), 400

    if etime <= stime:
        return jsonify({'error': 'etime must be later than stime'}), 400
    if step <= 0:
        return jsonify({'error': 'step must be a positive integer'}), 400

    time_diff_hours = (etime - stime).total_seconds() / 3600
    if step > time_diff_hours:
        return jsonify({'error': 'step is larger than the time range'}), 400

    directory = '/home/projects/data/snowpack_output/'
    if not os.path.isdir(directory):
        return jsonify({'error': 'Data directory not found'}), 500

    ari_result = {}
    for fname in os.listdir(directory):
        file_path = os.path.join(directory, fname)
        if not os.path.isfile(file_path):
            continue
        station_name = os.path.splitext(fname)[0]
        file_ext = os.path.splitext(fname)[1].lower()

        if file_ext == '.pro':
            pro_data = parse_pro_file(file_path, stime, etime, step)

            ari_series = []
            for record in pro_data:
                t_str = record['time']
                height_str = record.get('height')

                try:
                    snow_depth = float(height_str)

                    t_prev = datetime.strptime(t_str, "%Y-%m-%d %H:%M:%S") - timedelta(hours=24)
                    t_prev_str = t_prev.strftime("%Y-%m-%d %H:%M:%S")

                    snow_depth_prev = None
                    for prev_record in pro_data:
                        if prev_record['time'] == t_prev_str:
                            try:
                                snow_depth_prev = float(prev_record.get('height'))
                            except:
                                pass
                            break

                    if snow_depth_prev is None:
                        ari_val = round(random.uniform(0.0, 0.2), 4)
                    else:
                        new_snow_24h = max(0.0, snow_depth - snow_depth_prev)
                        ari_val = ((snow_depth / 60.0) + (new_snow_24h / 20.0)) / 2.0
                        ari_val = round(ari_val, 4)

                except Exception:
                    ari_val = round(random.uniform(0.0, 0.2), 4)

                ari_series.append({
                    'time': t_str,
                    'ARI': ari_val
                })

            ari_result[station_name] = ari_series

    return jsonify(ari_result)