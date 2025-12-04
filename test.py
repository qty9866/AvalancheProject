import os
import requests
from tqdm import tqdm
from datetime import datetime

# === 测试下载速度 ===
def test_download_speed():
    # 获取当前日期（UTC）
    forecast_date = datetime.utcnow().strftime('%Y%m%d')
    forecast_cycle = "00"
    forecast_hour = 6  # 测试下载 6 小时的文件

    # 构造下载链接
    base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{forecast_date}/{forecast_cycle}/atmos"
    file_name = f"gfs.t{forecast_cycle}z.pgrb2.0p25.f{forecast_hour:03d}"
    file_url = f"{base_url}/{file_name}"

    # 目标保存路径
    save_dir = "/WRF/Product_WRF/GFS_DATA/test"
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, file_name)

    # 打印测试信息
    print(f"开始测试下载文件: {file_name}")
    print(f"下载 URL: {file_url}")
    print(f"保存路径: {save_path}")

    try:
        # 发送 HTTP 请求
        response = requests.get(file_url, stream=True, timeout=30)
        response.raise_for_status()

        # 获取文件总大小
        total_size = int(response.headers.get("content-length", 0))

        # 下载并显示进度
        with open(save_path, "wb") as f, tqdm(
            desc=file_name,
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
                    bar.update(len(chunk))

        print("下载成功！")
    except requests.exceptions.RequestException as e:
        print(f"下载失败: {e}")

if __name__ == "__main__":
    test_download_speed()