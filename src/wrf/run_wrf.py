# src/wrf/scheduler/run_wrf.py
import os
import subprocess
from datetime import datetime, timedelta, timezone
import logging
import sys

# =============================
# 日志系统初始化
# =============================
log_dir = "/home/projects/logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "run_wrf.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_path, mode='a'),
        # logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# =============================
# 路径配置
# =============================
WORK_DIR = "/WRF/Product_WRF/work"
MET_SOURCE = "/WRF/Product_WRF/WPS/met_em.d0*"
GEO_SOURCE = "/WRF/Product_WRF/WPS/geo_em.d0*"
NAMELIST_INPUT = os.path.join(WORK_DIR, "namelist.input")

# =============================
# 工具函数：运行 Shell 命令
# =============================
def run_shell(cmd, cwd=None, background=False):
    logger.info(f"▶️ 执行命令: {cmd}")
    if background:
        subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        result = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            logger.error(f"❌ 命令失败: {cmd}")
            logger.error(result.stderr)
            raise RuntimeError(f"命令执行失败: {cmd}")
        else:
            logger.info(result.stdout)

# =============================
# 步骤1：清理旧文件
# =============================
def clean_work_directory():
    logger.info("🧹 清理 work 目录中旧文件...")
    patterns = [
        "met_em.d0*",
        "geo_em.d0*",
        "rsl.*"
    ]
    for pattern in patterns:
        run_shell(f"rm -f {pattern}", cwd=WORK_DIR)

# =============================
# 步骤2：软链接 met_em 和 geo_em
# =============================
def link_input_files():
    logger.info("🔗 链接 met_em 和 geo_em 文件")
    run_shell(f"ln -sf {MET_SOURCE} ./", cwd=WORK_DIR)
    run_shell(f"ln -sf {GEO_SOURCE} ./", cwd=WORK_DIR)

# =============================
# 步骤3：更新 namelist.input 时间
# =============================
def update_namelist_input(start_date, end_date):
    logger.info("📝 修改 namelist.input 起止时间")

    with open(NAMELIST_INPUT, "r") as f:
        lines = f.readlines()

    def replace_value(key, value):
        for i, line in enumerate(lines):
            if line.strip().startswith(key):
                lines[i] = f" {key:<22} = {value}\n"
                return
        raise ValueError(f"{key} not found in namelist.input")

    # 拆解年月日
    sy, sm, sd = start_date.year, start_date.month, start_date.day
    ey, em, ed = end_date.year, end_date.month, end_date.day

    replace_value("start_year", f"{sy}")
    replace_value("start_month", f"{sm:02d}")
    replace_value("start_day", f"{sd:02d}")
    replace_value("start_hour", "00")

    replace_value("end_year", f"{ey}")
    replace_value("end_month", f"{em:02d}")
    replace_value("end_day", f"{ed:02d}")
    replace_value("end_hour", "00")

    with open(NAMELIST_INPUT, "w") as f:
        f.writelines(lines)

    logger.info(f"✅ namelist.input 已更新为 {start_date} -> {end_date}")

# =============================
# 步骤4-5：运行 real.exe 和 wrf.exe
# =============================
def run_wrf_programs():
    logger.info("🚀 执行 real.exe")
    run_shell("./real.exe", cwd=WORK_DIR)

    logger.info("🚀 启动 wrf.exe 后台运行 (32核)")
    run_shell("nohup mpirun -np 32 ./wrf.exe &", cwd=WORK_DIR, background=True)

# =============================
# 主流程函数
# =============================
def run():
    logger.info("🏁 开始 WRF 模拟流程")
    CHINA_TZ = timezone(timedelta(hours=8))
    # today = datetime.now(CHINA_TZ).date()
    today = (datetime.now(CHINA_TZ) - timedelta(days=1)).date()
    start_date = today
    end_date = today + timedelta(days=4)

    clean_work_directory()
    link_input_files()
    update_namelist_input(start_date, end_date)
    run_wrf_programs()

    logger.info("🎉 WRF 模拟启动完成")

# =============================
# 入口函数
# =============================
if __name__ == "__main__":
    run()