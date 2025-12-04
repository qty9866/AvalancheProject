# import os
# import glob
# import json
# import netCDF4 as nc
# import numpy as np
# import pandas as pd
# from datetime import datetime

# # 配置路径
# STATIONS_FILE = '/home/projects/config/stations.json'
# WRF_DIR = '/home/projects/data/wrf_output/'
# SMET_DIR = '/home/projects/data/snowpack_input'
# TIME_FORMAT = '%Y-%m-%d_%H:%M:%S'
# SMET_TIME_FMT = '%Y-%m-%dT%H:%M'

# # 加载站点经纬度
# with open(STATIONS_FILE, 'r') as f:
#     stations = json.load(f)

# wrf_files = sorted(glob.glob(os.path.join(WRF_DIR, 'wrfout*')))
# if not wrf_files:
#     raise FileNotFoundError(f"在 {WRF_DIR} 未找到 wrfout 文件")

# # 处理每个站点
# for sid, meta in stations.items():
#     lat_target = meta['latitude']
#     lon_target = meta['longitude']
#     print(f"处理站点 {sid}: lat={lat_target}, lon={lon_target}")

#     # 用于合并所有域数据
#     all_records = []

#     for wrf_file in wrf_files:
#         # 打开 netCDF
#         ds = nc.Dataset(wrf_file)
#         lat = ds.variables['XLAT'][0, :, :]
#         lon = ds.variables['XLONG'][0, :, :]
#         dist = (lat - lat_target)**2 + (lon - lon_target)**2
#         j, i = np.unravel_index(dist.argmin(), dist.shape)

#         # 时间序列
#         times = ds.variables['Times'][:]
#         dt_list = [datetime.strptime(b''.join(t).decode(), TIME_FORMAT)
#                    for t in times]

#         def get_var(name, default_val=-999):
#             try:
#                 arr = ds.variables[name][:, j, i]
#                 return np.array(arr)
#             except KeyError:
#                 return np.full(len(dt_list), default_val)

#         T2 = get_var('T2')
#         Q2 = get_var('Q2')
#         PSFC = get_var('PSFC')
#         U10 = get_var('U10')
#         V10 = get_var('V10')
#         RAINNC = get_var('RAINNC', np.nan)
#         RAINC = get_var('RAINC', np.nan)
#         rain_total = np.nan_to_num(RAINNC) + np.nan_to_num(RAINC)

#         SWDOWN = get_var('SWDOWN')          # 入射短波
#         FSA = get_var('FSA')                # 地表吸收短波
#         GLW = get_var('GLW')                # 向下长波

#         # ✅ 使用 FSA 推算 OSWR（反射短波）
#         OSWR = np.where((SWDOWN != -999) & (FSA != -999), SWDOWN - FSA, -999.0)
#         ISWR = SWDOWN  # 保留 SWDOWN 作为 ISWR

#         SNOWH = get_var('SNOWH')
#         try:
#             tslb = ds.variables['TSLB']
#             TS1 = tslb[:, 0, j, i]
#             TS2 = tslb[:, 1, j, i]
#             TS3 = tslb[:, 2, j, i]
#         except Exception:
#             TS1 = TS2 = TS3 = np.full(len(dt_list), -999.0)

#         # 这里改为用 TSK 代替 TSG，TSK是地表土壤温度
#         TSG = get_var('TSK')

#         # 计算相对湿度 RH
#         RH = np.full(len(dt_list), -999.0)
#         mask = (Q2 != -999) & (PSFC != -999)
#         ps_hpa = PSFC[mask] / 100.0
#         t2_c = T2[mask] - 273.15
#         es = 6.112 * np.exp(17.67 * t2_c / (t2_c + 243.5))
#         e = (Q2[mask] * ps_hpa) / (0.622 + 0.378 * Q2[mask])
#         RH[mask] = np.clip(e / es, 0, 1)

#         VW = np.sqrt(U10**2 + V10**2)
#         DW = np.degrees(np.arctan2(U10, V10)) % 360

#         diffs = np.diff(np.insert(rain_total, 0, 0.0))
#         diffs[diffs < 0] = 0
#         PSUM = diffs  # 保留毫米单位


#         for ts, ta, rh, tsg, hs, vw, dw, oswr, iswr, ilwr, psum in zip(
#              dt_list, T2, RH, TSG, SNOWH, VW, DW, OSWR, ISWR, GLW, PSUM):
#             all_records.append({
#                 'timestamp': ts,
#                 'TA': round(ta, 2),
#                 'RH': round(rh, 2),
#                 'TSG': round(tsg if not np.isnan(tsg) else -999, 2),
#                 'TSS': -999.0,
#                 'HS': round(hs if hs != -999 else -999, 2),
#                 'VW': round(vw, 2),
#                 'DW': round(dw, 2),
#                 'OSWR': round(oswr, 2),
#                 'ISWR': round(iswr, 2),
#                 'ILWR': round(ilwr, 2),
#                 'PSUM': round(psum, 2),
#                 'TS1': -999.0,
#                 'TS2': -999.0,
#                 'TS3': -999.0
#             })
#         ds.close()

#     df_new = pd.DataFrame(all_records)
#     df_new.set_index('timestamp', inplace=True)
#     df_new = df_new[~df_new.index.duplicated(keep='last')]

#     smet_path = os.path.join(SMET_DIR, f"{sid}.smet")
#     if not os.path.isfile(smet_path):
#         print(f"警告：未找到 {smet_path}, 跳过")
#         continue

#     cols = ['TA', 'RH', 'TSG', 'TSS', 'HS', 'VW', 'DW', 'OSWR', 'ISWR', 'ILWR', 'PSUM', 'TS1', 'TS2', 'TS3']

#     header_lines = []
#     data_old = []
#     with open(smet_path) as f:
#         lines = f.readlines()

#     in_data = False
#     for ln in lines:
#         if ln.strip() == '[DATA]':
#             in_data = True
#             continue
#         if not in_data:
#             header_lines.append(ln)
#         else:
#             parts = ln.strip().split()
#             if len(parts) != len(cols) + 1:
#                 print(f"⚠️ 跳过列数不匹配的旧行：{parts}")
#                 continue
#             data_old.append(parts)

#     df_old = pd.DataFrame(data_old, columns=['timestamp'] + cols)
#     df_old['timestamp'] = pd.to_datetime(df_old['timestamp'])
#     df_old.set_index('timestamp', inplace=True)
#     df_old = df_old.astype(float)

#     df_combined = pd.concat([df_old, df_new])
#     df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
#     df_combined.sort_index(inplace=True)

#     with open(smet_path, 'w') as f:
#         for hl in header_lines:
#             f.write(hl)
#         f.write('[DATA]\n')
#         def fmt(v):
#             return "-999" if v == -999 else f"{v:.2f}"
#         for ts, row in df_combined.iterrows():
#             vals = '\t'.join(fmt(row[c]) for c in cols)
#             f.write(f"{ts.strftime(SMET_TIME_FMT)}\t{vals}\n")
#     print(f"更新完成: {smet_path}")
import os
import glob
import json
import netCDF4 as nc
import numpy as np
import pandas as pd
from datetime import datetime

# 配置路径
STATIONS_FILE = '/home/projects/config/stations.json'
WRF_DIR = '/home/projects/data/wrf_output/'
SMET_DIR = '/home/projects/data/snowpack_input'
TIME_FORMAT = '%Y-%m-%d_%H:%M:%S'
SMET_TIME_FMT = '%Y-%m-%dT%H:%M'

# 加载站点经纬度
with open(STATIONS_FILE, 'r') as f:
    stations = json.load(f)

wrf_files = sorted(glob.glob(os.path.join(WRF_DIR, 'wrfout*')))
if not wrf_files:
    raise FileNotFoundError(f"在 {WRF_DIR} 未找到 wrfout 文件")

# 初始化每个站点的结果字典
station_records = {sid: [] for sid in stations}

# 逐文件处理，避免一次性加载所有文件导致内存溢出
for wrf_file in wrf_files:
    print(f"📦 正在处理 WRF 文件: {wrf_file}")
    ds = nc.Dataset(wrf_file)

    lat_all = ds.variables['XLAT'][0, :, :]
    lon_all = ds.variables['XLONG'][0, :, :]
    times = ds.variables['Times'][:]
    dt_list = [datetime.strptime(b''.join(t).decode(), TIME_FORMAT) for t in times]

    for sid, meta in stations.items():
        lat_target = meta['latitude']
        lon_target = meta['longitude']
        print(f"  ↪️  处理站点 {sid}: lat={lat_target}, lon={lon_target}")

        dist = (lat_all - lat_target) ** 2 + (lon_all - lon_target) ** 2
        j, i = np.unravel_index(dist.argmin(), dist.shape)

        def get_var(name, default_val=-999):
            try:
                arr = ds.variables[name][:, j, i]
                return np.array(arr)
            except KeyError:
                return np.full(len(dt_list), default_val)

        T2 = get_var('T2')
        Q2 = get_var('Q2')
        PSFC = get_var('PSFC')
        U10 = get_var('U10')
        V10 = get_var('V10')
        RAINNC = get_var('RAINNC', np.nan)
        RAINC = get_var('RAINC', np.nan)
        rain_total = np.nan_to_num(RAINNC) + np.nan_to_num(RAINC)

        SWDOWN = get_var('SWDOWN')
        FSA = get_var('FSA')
        GLW = get_var('GLW')

        OSWR = np.where((SWDOWN != -999) & (FSA != -999), SWDOWN - FSA, -999.0)
        ISWR = SWDOWN

        SNOWH = get_var('SNOWH')
        try:
            tslb = ds.variables['TSLB']
            TS1 = tslb[:, 0, j, i]
            TS2 = tslb[:, 1, j, i]
            TS3 = tslb[:, 2, j, i]
        except Exception:
            TS1 = TS2 = TS3 = np.full(len(dt_list), -999.0)

        TSG = get_var('TSK')

        RH = np.full(len(dt_list), -999.0)
        mask = (Q2 != -999) & (PSFC != -999)
        ps_hpa = PSFC[mask] / 100.0
        t2_c = T2[mask] - 273.15
        es = 6.112 * np.exp(17.67 * t2_c / (t2_c + 243.5))
        e = (Q2[mask] * ps_hpa) / (0.622 + 0.378 * Q2[mask])
        RH[mask] = np.clip(e / es, 0, 1)

        VW = np.sqrt(U10 ** 2 + V10 ** 2)
        DW = np.degrees(np.arctan2(U10, V10)) % 360

        diffs = np.diff(np.insert(rain_total, 0, 0.0))
        diffs[diffs < 0] = 0
        PSUM = diffs

        for ts, ta, rh, tsg, hs, vw, dw, oswr, iswr, ilwr, psum in zip(
            dt_list, T2, RH, TSG, SNOWH, VW, DW, OSWR, ISWR, GLW, PSUM):
            station_records[sid].append({
                'timestamp': ts,
                'TA': round(ta, 2),
                'RH': round(rh, 2),
                'TSG': round(tsg if not np.isnan(tsg) else -999, 2),
                'TSS': -999.0,
                'HS': round(hs if hs != -999 else -999, 2),
                'VW': round(vw, 2),
                'DW': round(dw, 2),
                'OSWR': round(oswr, 2),
                'ISWR': round(iswr, 2),
                'ILWR': round(ilwr, 2),
                'PSUM': round(psum, 2),
                'TS1': -999.0,
                'TS2': -999.0,
                'TS3': -999.0
            })

    ds.close()

# 写入每个站点的 SMET 文件
for sid, records in station_records.items():
    smet_path = os.path.join(SMET_DIR, f"{sid}.smet")
    if not os.path.isfile(smet_path):
        print(f"⚠️ 警告：未找到 {smet_path}, 跳过")
        continue

    df_new = pd.DataFrame(records)
    df_new.set_index('timestamp', inplace=True)
    df_new = df_new[~df_new.index.duplicated(keep='last')]

    # 读取原有 SMET 文件
    cols = ['TA', 'RH', 'TSG', 'TSS', 'HS', 'VW', 'DW', 'OSWR', 'ISWR', 'ILWR', 'PSUM', 'TS1', 'TS2', 'TS3']
    header_lines = []
    data_old = []
    with open(smet_path) as f:
        lines = f.readlines()

    in_data = False
    for ln in lines:
        if ln.strip() == '[DATA]':
            in_data = True
            continue
        if not in_data:
            header_lines.append(ln)
        else:
            parts = ln.strip().split()
            if len(parts) != len(cols) + 1:
                print(f"⚠️ 跳过列数不匹配的旧行：{parts}")
                continue
            data_old.append(parts)

    df_old = pd.DataFrame(data_old, columns=['timestamp'] + cols)
    df_old['timestamp'] = pd.to_datetime(df_old['timestamp'])
    df_old.set_index('timestamp', inplace=True)
    df_old = df_old.astype(float)

    # 合并新旧数据
    df_combined = pd.concat([df_old, df_new])
    df_combined = df_combined[~df_combined.index.duplicated(keep='last')]
    df_combined.sort_index(inplace=True)

    # 写入新 SMET 文件
    tmp_path = smet_path + '.tmp'
    with open(tmp_path, 'w') as f:
        for hl in header_lines:
            f.write(hl)
        f.write('[DATA]\n')
        def fmt(v):
            return "-999" if v == -999 else f"{v:.2f}"
        for ts, row in df_combined.iterrows():
            vals = '\t'.join(fmt(row[c]) for c in cols)
            f.write(f"{ts.strftime(SMET_TIME_FMT)}\t{vals}\n")
    os.replace(tmp_path, smet_path)
    print(f"✅ 更新完成: {smet_path}")
