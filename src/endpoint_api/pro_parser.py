from flask import jsonify, Blueprint, request
import pandas as pd
import re, os
from datetime import datetime, timedelta

pro_parser_bp = Blueprint('pro_parser', __name__)

def extract_first_value(line):
    values = re.findall(r'[-+]?\d*\.\d+|\d+', line)
    if len(values) > 2:
        try:
            return float(values[2])
        except ValueError:
            pass
    return None

def parse_pro_file(file_path, stime, etime, step):
    data = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    # 找 [DATA] 段开始
    start = next((i+1 for i, l in enumerate(lines) if '[DATA]' in l), None)
    if start is None:
        return []
    # 构建时间点列表
    times = []
    t = stime
    while t <= etime:
        times.append(t)
        t += timedelta(hours=step)
    # 逐行解析
    record = {}
    for line in lines[start:]:
        line = line.strip()
        if line.startswith('0500'):
            t_str = line.split(',')[1]
            t_obj = datetime.strptime(t_str, '%d.%m.%Y %H:%M:%S')
            if t_obj in times:
                record = {'time': t_obj.strftime('%Y-%m-%d %H:%M:%S')}
                data.append(record)
        elif line.startswith('0501'):
            record['height'] = extract_first_value(line)
        elif line.startswith('0502'):
            record['element_density'] = extract_first_value(line)
        elif line.startswith('0503'):
            record['element_temperature'] = extract_first_value(line)
        elif line.startswith('0506'):
            record['liquid_water_content'] = extract_first_value(line)
        elif line.startswith('0517'):
            record['stress'] = extract_first_value(line)
        elif line.startswith('0518'):
            record['viscosity'] = extract_first_value(line)
        elif line.startswith('0601'):
            record['snow_shear_strength'] = extract_first_value(line)
    return data

@pro_parser_bp.route('/process_files', methods=['POST'])
def process_files():
    station = request.args.get('station')
    stime_str = request.args.get('stime')
    etime_str = request.args.get('etime')
    step_str  = request.args.get('step')

    if not all([station, stime_str, etime_str, step_str]):
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        stime = datetime.strptime(stime_str, '%Y-%m-%dT%H:%M:%S')
        etime = datetime.strptime(etime_str, '%Y-%m-%dT%H:%M:%S')
        step  = int(step_str)
    except ValueError:
        return jsonify({'error': 'Invalid date or step format'}), 400

    if etime <= stime or step <= 0:
        return jsonify({'error': 'etime must be > stime and step > 0'}), 400

    hours = (etime - stime).total_seconds() / 3600
    if step > hours:
        return jsonify({'error': 'step is larger than the time range'}), 400

    base_dir = '/home/projects/data/snowpack_output'
    pro_path = os.path.join(base_dir, f'{station}.pro')

    if not os.path.exists(pro_path):
        return jsonify({'error': 'Station .pro file not found'}), 404

    pro_data = parse_pro_file(pro_path, stime, etime, step)

    # 计算三天内新增累计雪深
    heights = [r.get('height', 0) for r in pro_data]
    cumulative_new = 0.0
    for prev, curr in zip(heights, heights[1:]):
        diff = curr - prev
        if diff > 0:
            cumulative_new += diff

    # 构造输出结果
    result = []
    total_steps = int(hours / step) + 1
    img_url = f"{request.url_root}static/sp_pic/{station}.png"
    for i in range(total_steps):
        t = stime + timedelta(hours=i*step)
        t_str = t.strftime('%Y-%m-%d %H:%M:%S')
        pro_rec = next((r for r in pro_data if r['time'] == t_str), {})
        record = {'time': t_str}
        record.update({
            'snow_layer_thickness':      pro_rec.get('height'),
            'snow_layer_density':        pro_rec.get('element_density'),
            'snow_layer_temperature':    pro_rec.get('element_temperature'),
            'liquid_water_content':      pro_rec.get('liquid_water_content'),
            'snow_layer_stress':         pro_rec.get('stress'),
            'snow_layer_viscosity':      pro_rec.get('viscosity'),
            'snow_layer_shear_strength': pro_rec.get('snow_shear_strength'),
            'new_snow_depth_3d':         None if cumulative_new == 0 else round(cumulative_new, 2),
            'img_url':                   img_url,
        })

        # 全部转为字符串，None 或缺失 => ""
        for k, v in record.items():
            record[k] = "" if v is None else str(v)

        result.append(record)

    return jsonify(result)