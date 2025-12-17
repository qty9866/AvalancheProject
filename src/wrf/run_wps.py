# src/wrf/run_wps.py
import os
import subprocess
import logging
from datetime import datetime, timedelta, timezone

# =============================
# 日志系统初始化
# =============================
log_dir = "/home/projects/logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "run_wps.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =============================
# 目录与文件路径
# =============================
WPS_DIR = "/WRF/Product_WRF/WPS"
GFS_DIR = "/WRF/Product_WRF/GFS_DATA"
NAMELIST_PATH = os.path.join(WPS_DIR, "namelist.wps")

# =============================
# 工具函数：运行 shell 命令
# =============================
def run_shell(cmd, cwd=None):
    logger.info(f"▶️ 执行命令: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        logger.error(f"❌ 命令失败: {cmd}")
        logger.error(result.stderr)
        raise RuntimeError(f"命令执行失败: {cmd}")
    else:
        logger.info(result.stdout)

# =============================
# 步骤1：清理 WPS 目录
# =============================
def clean_wps_directory():
    logger.info("🧹 清理旧的 WPS 文件...")
    patterns = [
        "GRIBFILE.AA*",
        "met_em.d01.*",
        "geo_em.d01.nc",
        "FILE:202*"
    ]
    for pattern in patterns:
        run_shell(f"rm -f {pattern}", cwd=WPS_DIR)

# =============================
# 步骤2：链接 GFS 数据
# =============================
def link_grib_files(forecast_date):
    folder_name = f"gfs_{forecast_date}_00z"
    grib_path = os.path.join(GFS_DIR, folder_name, "gfs.t00z.pgrb2.0p25.f0*")
    link_script = os.path.join(WPS_DIR, "link_grib.csh")
    if not os.path.exists(link_script):
        raise FileNotFoundError(f"link_grib.csh 脚本不存在: {link_script}")
    run_shell(f"{link_script} {grib_path}", cwd=WPS_DIR)

# =============================
# 步骤3：修改 namelist.wps 起止时间
# =============================
def update_namelist(start_date, end_date):
    logger.info("📝 修改 namelist.wps 起止时间...")
    with open(NAMELIST_PATH, "r") as f:
        lines = f.readlines()

    def replace_line(key, new_value):
        for i, line in enumerate(lines):
            if line.strip().startswith(key):
                lines[i] = f" {key} = '{new_value}'\n"
                return
        raise ValueError(f"{key} 未找到于 namelist.wps")

    replace_line("start_date", f"{start_date}_00:00:00")
    replace_line("end_date", f"{end_date}_00:00:00")

    with open(NAMELIST_PATH, "w") as f:
        f.writelines(lines)
    logger.info(f"✅ namelist.wps 已更新为 {start_date} -> {end_date}")

# =============================
# 步骤4：运行 WPS 三个程序
# =============================
def run_wps_programs():
    logger.info("🚀 开始执行 WPS 三个程序: ungrib.exe, geogrid.exe, metgrid.exe")
    for exe in ["ungrib.exe", "geogrid.exe", "metgrid.exe"]:
        exe_path = os.path.join(WPS_DIR, exe)
        if not os.path.exists(exe_path):
            raise FileNotFoundError(f"{exe} 不存在: {exe_path}")
        run_shell(f"./{exe}", cwd=WPS_DIR)

# =============================
# 主流程
# =============================
def run():
    logger.info("🏁 WPS 流程开始")
    CHINA_TZ = timezone(timedelta(hours=8))
    today = (datetime.now(CHINA_TZ) - timedelta(days=1)).date()
    forecast_date = today.strftime("%Y%m%d")
    start_date = today.strftime("%Y-%m-%d")
    end_date = (today + timedelta(days=4)).strftime("%Y-%m-%d")

    try:
        clean_wps_directory()
        link_grib_files(forecast_date)
        update_namelist(start_date, end_date)
        run_wps_programs()
    except Exception as e:
        logger.exception("❌ WPS 流程执行失败")
        raise e
    else:
        logger.info("🎉 WPS 流程完成")

# =============================
# 入口
# =============================
if __name__ == "__main__":
    run()