from flask import Blueprint, jsonify, request
import os
import numpy as np
import netCDF4 as nc
from datetime import datetime, timedelta
from wrf import destagger

wrf_visual_bp = Blueprint('wrf_visual_bp', __name__, static_folder='static')

# 路径配置
DATA_DIR = '/home/projects/data/wrf_output/'
OUTPUT_DIR = '/home/projects/static/wrf_pic_d02/'

'''
参数元数据配置（如需使用可取消注释）
PARAM_META = {
    'fira': {'cn': '长波辐射', 'unit': 'W/m²'},
    'fsa': {'cn': '短波辐射', 'unit': 'W/m²'},
    'psfc': {'cn': '地面气压', 'unit': 'hPa'},
    'q2': {'cn': '2米湿度', 'unit': 'kg/kg'},
    'rainc': {'cn': '对流降水', 'unit': 'mm'},
    'rainnc': {'cn': '非对流降水', 'unit': 'mm'},
    'snow': {'cn': '降雪量', 'unit': 'mm'},
    'snowh': {'cn': '积雪深度', 'unit': 'm'},
    't2': {'cn': '2米气温', 'unit': '℃'},
    'total_rain': {'cn': '总降水量', 'unit': 'mm'},
    'wind_dir': {'cn': '风向', 'unit': '度'},
    'wind_speed': {'cn': '风速', 'unit': 'm/s'},
}
'''

# 预定义的区域网格索引（需根据实际数据调整！）
REGION_GRID = {
    'd01': {   # 墨脱区域
        'x_start': 72,  
        'x_end': 76,
        'y_start': 37,
        'y_end': 41
    },
    'd02': {  # 波密地区
        'x_start': 77,  
        'x_end': 81,
        'y_start': 42,
        'y_end': 46
    }
}

def get_latest_wrfout():
    """获取最新的 wrfout 文件"""
    if not os.path.isdir(DATA_DIR):
        return None
    wrf_files = [f for f in os.listdir(DATA_DIR) if f.startswith('wrfout')]
    if not wrf_files:
        return None
    wrf_files.sort(key=lambda f: os.path.getctime(os.path.join(DATA_DIR, f)))
    return os.path.join(DATA_DIR, wrf_files[-1])

def get_12h_time_indices(ds, start_date):
    """获取 12 小时间隔的时间索引（跳过前三个符合条件的时间点）"""
    try:
        times = nc.num2date(ds['XTIME'][:], units=ds['XTIME'].units)
    except:
        times = [
            datetime.strptime(''.join(t).astype(str), '%Y-%m-%d_%H:%M:%S')
            for t in ds['Times'][:]
        ]
    
    indices = []
    for i, t in enumerate(times):
        delta = t - start_date
        if delta.total_seconds() % 43200 == 0:  # 43200秒=12小时
            indices.append(i)
    return indices[3:] if len(indices) > 3 else []

def process_wind(ds, time_idx, region_id):
    """处理风速风向（使用 destagger 的推荐参数）"""
    try:
        # 直接从变量读取交错网格风分量
        u_stag = ds.variables['U'][time_idx]
        v_stag = ds.variables['V'][time_idx]
        # 解交错网格（U 在第 3 维度交错，V 在第 2 维度交错）
        u = destagger(u_stag, stagger_dim=2)
        v = destagger(v_stag, stagger_dim=1)
        # 计算风速和风向
        speed = np.sqrt(u**2 + v**2)
        wind_dir = np.arctan2(v, u) * (180 / np.pi)
        wind_dir = (wind_dir + 360) % 360
        # 返回区域平均值
        return np.nanmean(speed), np.nanmean(wind_dir)
    except Exception as e:
        print(f"风速计算错误: {e}")
        return "", ""

def process_region(region_id):
    """处理指定区域的数据"""
    wrf_file = get_latest_wrfout()
    if not wrf_file:
        return jsonify({"error": "未找到 WRF 输出文件"}), 404
    try:
        with nc.Dataset(wrf_file) as ds:
            if region_id not in REGION_GRID:
                return jsonify({"error": "无效区域ID"}), 400
            grid = REGION_GRID[region_id]

            first_time = datetime.strptime(
                ''.join(ds['Times'][0][:].astype(str)), 
                '%Y-%m-%d_%H:%M:%S'
            )
            time_indices = get_12h_time_indices(ds, first_time)

            results = []
            for idx in time_indices:
                timestr = ''.join(ds['Times'][idx][:].astype(str))
                time_obj = datetime.strptime(timestr, '%Y-%m-%d_%H:%M:%S')

                # 区域切片参数
                slice_args = {
                    'y_slice': slice(grid['y_start'], grid['y_end']),
                    'x_slice': slice(grid['x_start'], grid['x_end'])
                }

                # 计算风速风向
                wind_speed, wind_dir = process_wind(ds, idx, region_id)

                def safe_mean(varname, offset=0, div=1):
                    try:
                        val = np.nanmean(
                            ds[varname][idx][
                                slice_args['y_slice'], 
                                slice_args['x_slice']
                            ]
                        )
                        if offset != 0:
                            val = val + offset
                        if div != 1:
                            val = val / div
                        return "" if np.isnan(val) else val
                    except Exception:
                        return ""

                # 各参数计算
                rainc = safe_mean('RAINC')
                rainnc = safe_mean('RAINNC')
                snowh = safe_mean('SNOWH')
                snow = safe_mean('SNOW')
                fsa = safe_mean('FSA')
                fira = safe_mean('FIRA')
                t2 = safe_mean('T2', offset=-273.15)
                q2 = safe_mean('Q2')
                psfc = safe_mean('PSFC', div=100)

                # 统一处理数值格式
                def format_value(val, ndigits):
                    try:
                        return str(round(float(val), ndigits)) if val != "" else ""
                    except:
                        return ""

                # 总降水量计算
                total_rain = ""
                if rainc != "" and rainnc != "":
                    try:
                        total_rain = str(round(float(rainc) + float(rainnc), 1))
                    except:
                        pass

                record = {
                    'time': time_obj.strftime('%Y%m%d %H:%M:%S'),
                    'wind_speed': format_value(wind_speed, 2),
                    'wind_dir': format_value(wind_dir, 1),
                    'total_rain': total_rain,
                    'rainc': format_value(rainc, 1),
                    'rainnc': format_value(rainnc, 1),
                    'snowh': format_value(snowh, 3),
                    'snow': format_value(snow, 1),
                    'fsa': format_value(fsa, 1),
                    'fira': format_value(fira, 1),
                    't2': format_value(t2, 1),
                    'q2': format_value(q2, 6),
                    'psfc': format_value(psfc, 1),
                    'img_url': f"{request.host_url}static/wrf_pic_{region_id}/{time_obj.strftime('%Y-%m-%d_%H:%M:%S')}.png"  # 修正的f-string
                }
                results.append(record)
            return jsonify(results)
    except Exception as e:
        return jsonify({"error": f"处理失败: {str(e)}"}), 500

@wrf_visual_bp.route('/getParams/d01')
def get_d01_params():
    return process_region('d01')

@wrf_visual_bp.route('/getParams/d02')
def get_d02_params():
    return process_region('d02')