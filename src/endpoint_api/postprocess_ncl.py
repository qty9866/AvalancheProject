from flask import Blueprint, jsonify, request, send_file
import os , re
import subprocess
import matplotlib.pyplot as plt
import matplotlib.dates
import matplotlib.patches as mpatches
import numpy as np
import netCDF4 as nc
from datetime import datetime
from matplotlib.colors import ListedColormap

# 🔹 蓝图实例：所有 /ncl 路由挂在这个模块下
postprocess_ncl_bp = Blueprint('postprocess_ncl', __name__)

# 🔹 路径配置
NC_DIR = 'data/wrf_output/'
PRO_DIR = 'data/snowpack_output/'
PIC_DIR = 'data/snowpack_output/pic/'
PROCESSED_FILE_LOG = 'logs/processed_files.txt'
NCL_SCRIPT_PATH = 'ncl_scripts/plot_wrf.ncl'

# 🔹 工具函数：从 .pro 文件中提取温度剖面图数据
def parse_pro_for_temp(file_path):
    times, heights, temps = [], [], []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        data_start = next(i for i, l in enumerate(lines) if "[DATA]" in l) + 1
        current_time = None
        for line in lines[data_start:]:
            line = line.strip()
            if line.startswith("0500"):
                time_str = line.split(',')[1]
                current_time = datetime.strptime(time_str, "%d.%m.%Y %H:%M:%S")
            elif line.startswith("0501"):
                heights += [float(h) for h in re.findall(r'[-+]?\d*\.\d+|\d+', line)[2:]]
                times += [current_time] * len(re.findall(r'[-+]?\d*\.\d+|\d+', line)[2:])
            elif line.startswith("0503"):
                temps += [float(t) - 273.15 for t in re.findall(r'[-+]?\d*\.\d+|\d+', line)[2:]]
    return np.array(times), np.array(heights), np.array(temps)

# 🔹 接口：绘制雪温剖面图
@postprocess_ncl_bp.route('/plot_temp_profile', methods=['GET'])
def plot_temp_profile():
    file_path = request.args.get('file')
    if not file_path:
        return jsonify({'error': 'file 参数缺失'}), 400

    full_path = os.path.join(PRO_DIR, file_path)
    times, heights, temps = parse_pro_for_temp(full_path)
    fig, ax = plt.subplots(figsize=(10, 6))
    sc = ax.scatter(times, heights, c=temps, cmap='coolwarm', s=10)
    ax.set_ylabel('Snow Depth (cm)')
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m-%d'))
    cbar = plt.colorbar(sc, label='Temperature (°C)')
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    output_file = os.path.join(PIC_DIR, f"{os.path.basename(file_path)}_temp.png")
    plt.savefig(output_file, transparent=True)
    plt.close()
    return send_file(output_file)

# 🔹 接口：绘制雪层类型图
@postprocess_ncl_bp.route('/plot_snow_type', methods=['GET'])
def plot_snow_type():
    file_path = request.args.get('file')
    if not file_path:
        return jsonify({'error': 'file 参数缺失'}), 400

    full_path = os.path.join(PRO_DIR, file_path)
    times, heights, types = parse_pro_file_for_type(full_path)
    fig, ax = plt.subplots(figsize=(10, 6))
    cmap = create_snow_type_colormap()
    mapped = 1 - np.array([map_snow_type(t) for t in types])
    sc = ax.scatter(times[:len(types)], heights[:len(types)], c=mapped, cmap=cmap, s=5)
    ax.set_ylabel('Snow Height (cm)')
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%m-%d'))
    cbar = plt.colorbar(sc)
    output_file = os.path.join(PIC_DIR, f"{os.path.basename(file_path)}_type.png")
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    plt.savefig(output_file, transparent=True)
    plt.close()
    return send_file(output_file)

# 🔹 工具函数：处理雪类型颜色映射
def parse_pro_file_for_type(file_path):
    times, heights, types = [], [], []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        data_start = next(i for i, l in enumerate(lines) if "[DATA]" in l) + 1
        current_time = None
        for line in lines[data_start:]:
            line = line.strip()
            if line.startswith("0500"):
                time_str = line.split(',')[1]
                current_time = datetime.strptime(time_str, "%d.%m.%Y %H:%M:%S")
            elif line.startswith("0501"):
                h_values = [float(v) for v in re.findall(r'[-+]?\d*\.\d+|\d+', line)[2:]]
                times += [current_time] * len(h_values)
                heights += h_values
            elif line.startswith("0513"):
                types += [float(v) for v in re.findall(r'[-+]?\d*\.\d+|\d+', line)[2:]]
    return np.array(times), np.array(heights), np.array(types)

def map_snow_type(value):
    thresholds = [200, 278, 356, 450, 650, 750, 771, 850, 900, 950]
    for i, t in enumerate(thresholds):
        if value < t:
            return i / len(thresholds)
    return 1.0

def create_snow_type_colormap():
    colors = [
        (128/255,128/255,128/255), (1,1,0), (0,1,1),
        (1,0.65,0), (1,0,0), (1,0,1), (0,0,1),
        (0.678,0.847,0.902), (1,0.75,0.8), (0,0.5,0), (0,1,0)
    ]
    return ListedColormap(colors)

# 🔹 接口：运行 .nc 后处理（执行 NCL）
@postprocess_ncl_bp.route('/run', methods=['GET'])
def run_ncl_for_nc():
    files = sorted([f for f in os.listdir(NC_DIR) if f.endswith('.nc')])
    processed = set()
    if os.path.exists(PROCESSED_FILE_LOG):
        with open(PROCESSED_FILE_LOG, 'r') as f:
            processed.update(line.strip() for line in f)

    for fname in files:
        if fname in processed:
            continue
        input_path = os.path.join(NC_DIR, fname)
        with open(NCL_SCRIPT_PATH, 'r') as f:
            content = f.read().replace('replace_me.nc', input_path)
        temp_script = os.path.join('ncl_scripts', 'temp_script.ncl')
        with open(temp_script, 'w') as f:
            f.write(content)

        subprocess.call(f"ncl {temp_script}", shell=True)
        os.remove(temp_script)

        out_img = os.path.join(PIC_DIR, fname.replace('.nc', '.png'))
        if os.path.exists(out_img):
            subprocess.call(f"convert -trim {out_img} {out_img}", shell=True)

        with open(PROCESSED_FILE_LOG, 'a') as logf:
            logf.write(fname + '\n')

        return send_file(out_img)

    return jsonify({'message': 'No new .nc files to process'})