import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from datetime import datetime
import matplotlib.dates
import re
import os
import time
import matplotlib.patches as mpatches

plt.rcParams['font.weight'] = 'bold'


# def create_striped_red_colormap():
#     # 创建自定义颜色映射
#     colors = [(1, 0, 0), (0, 0, 0)]  # 红色和黑色交替
#     cmap = LinearSegmentedColormap.from_list('striped_red', colors, N=100)  # N 表示颜色映射的离散级别，可调整条纹密度
#     return cmap


# def get_striped_red_rgba():
#     cmap = create_striped_red_colormap()
#     # 获取颜色映射的所有颜色
#     rgba_colors = cmap(np.linspace(0, 1, 256))  # 获取 256 个离散颜色，可根据需要调整数量
#     return rgba_colors


# 自定义积雪类型颜色映射，根据给定色卡，将 RGB 颜色值转换为 0-1 范围，并修改颜色顺序
def create_snow_type_colormap():
    # striped_red_rgba = get_striped_red_rgba()
    colors = [
        (128 / 255, 128 / 255, 128 / 255),
        (255 / 255, 255 / 255, 0 / 255),  # 积雪类型 1
        (0 / 255, 255 / 255, 255 / 255),  # 积雪类型 2
        (255 / 255, 165 / 255, 0 / 255),
        (255 / 255, 0 / 255, 0 / 255),    # 积雪类型 4
        (255 / 255, 0 / 255, 255 / 255),  # 积雪类型 5
        (0 / 255, 0 / 255, 255 / 255),    # 积雪类型 6
        (173 / 255, 216 / 255, 230 / 255),  # 积雪类型 7
        (255 / 255, 192 / 255, 203 / 255),  # 积雪类型 8
        (0 / 255, 128 / 255, 0 / 255),    # 积雪类型 9
        (0 / 255, 255 / 255, 0 / 255)     # 积雪类型 10
    ]
    return ListedColormap(colors)


def extract_first_value(line):
    values = re.findall(r'[-+]?\d*\.\d+|\d+', line)
    try:
        return [float(val) for val in values[2:]]
    except ValueError:
        print(f"数据转换错误，行数据为：{line}")
        return []


def color_mapping(value):
    # 自定义映射逻辑
    if value < 200:
        return 0
    elif 200 <= value < 278:
        return 0.1
    elif 278 <= value < 356:
        return 0.2
    elif 356 <= value < 450:
        return 0.3
    elif 450 <= value < 650:
        return 0.4
    elif 650 <= value < 750:
        return 0.5
    elif 750 <= value < 771:
        return 0.6
    elif 771 <= value < 850:
        return 0.7
    elif 850 <= value < 900:
        return 0.8
    elif 900 <= value < 950:
        return 0.9
    else:
        return 1.0


def parse_pro_file(file_path):
    times = []
    snow_depths = []
    snow_type = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        data_start_index = None
        for i, line in enumerate(lines):
            if "[DATA]" in line:
                data_start_index = i + 1
    # 遍历数据部分的行
    n_elems = 0
    current_time = None
    index = 0
    for i in range(data_start_index, len(lines)):
        line = lines[i].strip()
        if line.startswith("0500"):
            time_str = line.split(',')[1]
            # 将时间字符串转换为 datetime 对象
            current_time = datetime.strptime(time_str, "%d.%m.%Y %H:%M:%S")
        elif line.startswith("0501"):
            n_elems = float(line.split(',')[2] )
            height_values = extract_first_value(line)
            for value in height_values:
                times.append(current_time)
                snow_depths.append(value)
        elif line.startswith("0513"):
            type_values = extract_first_value(line)
            for value in type_values:
                if index < len(times):  # 确保不超过 times 的长度
                    snow_type.append(value)
                    index += 1
    return np.array(times), np.array(snow_depths), np.array(snow_type)


# 绘制雪层图形
def plot_snowpack_profile(file_path, output_folder):
    times, snow_depths, snow_type = parse_pro_file(file_path)
    fig, ax = plt.subplots(figsize=(20.45, 11.48))
    fig.subplots_adjust(left=0.15, right=0.95, top=0.95, bottom=0.05)
    ax.set_xlim(min(times), max(times))
    # 紧贴纵坐标
    ax.set_ylim(0, max(snow_depths))

    # 绘制雪深的线图
    # ax.plot(times, snow_depths, color='white', linewidth=2, label='Snow Depth')

    # 绘制积雪类型的颜色填充图
    snow_type_cmap = create_snow_type_colormap()
    # 自定义取值填色
    mapped_snow_type = np.array([color_mapping(val) for val in snow_type])
    mapped_snow_type = 1 - mapped_snow_type
    # 各个参数分别表示颜色填充图的边界、填充颜色、透明度等信息，s表示散点大小
    sc = ax.scatter(times[:len(snow_type)], snow_depths[:len(snow_type)], c=mapped_snow_type, cmap=snow_type_cmap, s=5, rasterized=True)


    # 设置坐标轴标签和标题
    ax.set_ylabel('Snow Height (cm)', color='white', size=22)
    # ax.set_title('Snowpack Profile', color='white', size=22)

    # 格式化横坐标的日期显示
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(matplotlib.dates.DayLocator(interval=60))
    # 设置横坐标刻度文字大小和颜色
    ax.tick_params(axis='x', which='major', labelsize=15, colors='white')
    # 设置纵坐标刻度文字大小和颜色
    ax.tick_params(axis='y', which='major', labelsize=15, colors='white')


    # 添加颜色条
    cbar = plt.colorbar(sc, label='')
    # cbar.ax.set_ylabel('Snow Type', color='white', size=18)
    cbar.ax.tick_params(labelsize=15)
    # 隐藏刻度线和刻度标签
    cbar.ax.tick_params(axis='y', which='both', length=0)
    cbar.ax.set_yticklabels([])


    # 自定义图标列表，确保浅绿色对应 + 号
    icons = ['*', '◎', '▬', '∞', '○', 'v', '^', '□', '●', '/', '+']
    # 为每个颜色添加对应的图标到颜色条旁边
    for i, (color, icon) in enumerate(zip(snow_type_cmap.colors, icons)):
        # 下面表达式中，2、1、0.5分别控制 颜色条高度和图标大小 
        cbar.ax.text(2, (i + 0.5) / (len(icons) + 0), icon, color='white', fontsize=15, va='center', ha='center')


    # 显示图例
    ax.legend()
    legend = ax.get_legend()
    plt.setp(legend.get_texts(), color='white', size=22)  # 将图例文字颜色改为白色

    # 设置图形背景为透明
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    # 保存图形，使用时间戳和文件名命名
    base_name = os.path.basename(file_path).split('.')[0]  
    output_filename = os.path.join(output_folder, f"{base_name}.png")
    plt.savefig(output_filename)
    plt.close(fig)


def main():
    folder_path = '/home/projects/data/snowpack_output/'  
    output_folder = '/home/projects/static/sp_pic/'  
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    pro_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.pro')]
    for file_path in pro_files:
        plot_snowpack_profile(file_path, output_folder)

if __name__ == "__main__":
    main()