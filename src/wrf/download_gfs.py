# home/projects/src/wrf
import os
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
import time

# === 日志设置 ===
log_dir = "/home/projects/logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "download_gfs.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='a'),
    ]
)
logger = logging.getLogger(__name__)

# === 主执行函数 ===
def run():
    logger.info("🚀 启动 GFS 数据下载任务...")

    # 自动使用 UTC 日期
    forecast_date = datetime.utcnow().strftime('%Y%m%d')
    forecast_cycle = "00"
    forecast_hours = range(0, 97, 6)

    # 修改后的 GFS 下载地址
    base_url = f"https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{forecast_date}/{forecast_cycle}/atmos"

    # 目标保存目录
    gfs_base_dir = "/WRF/Product_WRF/GFS_DATA"
    save_dir = os.path.join(gfs_base_dir, f"gfs_{forecast_date}_{forecast_cycle}z")
    os.makedirs(save_dir, exist_ok=True)
    logger.info(f"📁 GFS 数据将保存至: {save_dir}")

    # ======================
    #    断点续传下载函数
    # ======================
    def download_file(hour):
        forecast_hour = f"{hour:03d}"
        file_name = f"gfs.t{forecast_cycle}z.pgrb2.0p25.f{forecast_hour}"
        file_url = f"{base_url}/{file_name}"
        save_path = os.path.join(save_dir, file_name)

        max_retries = 10

        for attempt in range(max_retries):
            try:
                # 已下载的字节数（用于断点续传）
                downloaded = 0
                if os.path.exists(save_path):
                    downloaded = os.path.getsize(save_path)

                # HEAD 请求获取文件总大小
                head = requests.head(file_url, timeout=20)
                if head.status_code != 200:
                    raise Exception(f"HEAD 请求失败: {head.status_code}")

                total_size = int(head.headers.get("content-length", 0))

                # ✔ 已经完整下载
                if downloaded == total_size and total_size > 0:
                    logger.info(f"⚡ 已存在且完整: {file_name}")
                    return

                # Range 断点续传头
                headers = {"Range": f"bytes={downloaded}-"}

                if attempt > 0:
                    logger.warning(f"第 {attempt} 次重试下载 {file_name}（断点续传）...")

                response = requests.get(
                    file_url,
                    headers=headers,
                    stream=True,
                    timeout=30
                )

                if response.status_code not in (200, 206):
                    raise Exception(f"状态码异常: {response.status_code}")

                # 有部分已下载则追加写入
                mode = "ab" if downloaded > 0 else "wb"

                with open(save_path, mode) as f, tqdm(
                    desc=file_name,
                    total=total_size,
                    initial=downloaded,
                    unit="B",
                    unit_scale=True,
                    unit_divisor=1024,
                ) as bar:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))

                # 验证文件完整性
                final_size = os.path.getsize(save_path)
                if final_size == total_size:
                    logger.info(f"✅ 下载完成: {file_name}")
                    return
                else:
                    raise Exception(
                        f"文件大小不一致 downloaded={final_size}, expected={total_size}"
                    )

            except Exception as e:
                logger.error(f"❌ 下载异常: {file_name}, 错误: {e}, 尝试: {attempt+1}")
                time.sleep(2)

                if attempt == max_retries - 1:
                    raise Exception(f"{file_name} 最终失败: {e}")

        raise Exception(f"文件超过最大重试次数: {file_name}")

    # ======================
    #      并发下载
    # ======================
    error_files = []

    # ✔ 降低并发 —— 避免 AWS 限流
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(download_file, hour) for hour in forecast_hours]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                error_files.append(str(e))

    if error_files:
        logger.error("❌ 以下文件下载失败:")
        for error in error_files:
            logger.error(f"• {error}")
        raise Exception("GFS 数据下载存在失败文件，请检查日志")

    logger.info("🎉 所有 GFS 文件下载完成！")


if __name__ == "__main__":
    run()