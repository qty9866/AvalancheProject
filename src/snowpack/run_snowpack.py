# import os
# import subprocess
# from datetime import datetime, timedelta, timezone
# import logging
# import sys

# # =============================
# # 日志系统初始化
# # =============================
# log_dir = "/home/projects/logs"
# os.makedirs(log_dir, exist_ok=True)
# log_path = os.path.join(log_dir, "run_snowpack.log")

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[
#         logging.FileHandler(log_path, mode='a'),
#         # logging.StreamHandler(sys.stdout)
#     ]
# )
# logger = logging.getLogger(__name__)

# # =============================
# # 工具函数：运行 Shell 命令
# # =============================
# def run_shell(cmd, cwd=None):
#     logger.info(f"▶️ 执行命令: {cmd}")
#     result = subprocess.run(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
#     if result.returncode != 0:
#         logger.error(f"❌ 命令失败: {cmd}")
#         logger.error(result.stderr)
#         raise RuntimeError(f"命令执行失败: {cmd}")
#     else:
#         logger.info(result.stdout)


# # =============================
# # 主流程函数
# # =============================
# def run():
#     logger.info("🏁 开始 Snowpack 模拟流程")

#     # 获取东八区当前时间
#     CHINA_TZ = timezone(timedelta(hours=8))
#     today = datetime.now(CHINA_TZ).replace(hour=0, minute=0, second=0, microsecond=0)

#     # 仿真结束时间 = 今天 00:00 + 4 天
#     end_date = today + timedelta(days=4)
#     end_str = end_date.strftime('%Y-%m-%dT00:00')

#     # 步骤1：执行 wrfout2smet.py
#     logger.info("📥 执行 wrfout2smet.py")
#     run_shell("python wrfout2smet.py", cwd="/home/projects/src/snowpack")

#     # 步骤2：执行 run_snowpack.sh
#     logger.info(f"❄️  执行 run_snowpack.sh {end_str}")
#     run_shell(f"./run_snowpack.sh {end_str}", cwd="/home/projects/data/snowpack_input")

#     # 步骤3：执行 pro_plot.py
#     logger.info("🖼️  执行 pro_plot.py 生成图像")
#     run_shell("python pro_plot.py", cwd="/home/projects/src/snowpack")

#     logger.info("🎉 Snowpack 全部流程执行完成")



# if __name__ == "__main__":
#     run()

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
log_path = os.path.join(log_dir, "run_snowpack.log")

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
# 工具函数：运行 Shell 命令
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
# 主流程函数
# =============================
def run():
    logger.info("🏁 开始 Snowpack 模拟流程")

    # 获取东八区昨天的日期
    CHINA_TZ = timezone(timedelta(hours=8))
    yesterday = datetime.now(CHINA_TZ) - timedelta(days=1)
    yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)

    # 仿真结束时间 = 昨天 00:00 + 4 天
    end_date = yesterday + timedelta(days=4)
    end_str = end_date.strftime('%Y-%m-%dT00:00')

    logger.info(f"🕒 仿真开始时间: {yesterday.strftime('%Y-%m-%dT00:00')}")
    logger.info(f"🕒 仿真结束时间: {end_str}")

    # 步骤1：执行 wrfout2smet.py
    logger.info("📥 执行 wrfout2smet.py")
    run_shell("python wrfout2smet.py", cwd="/home/projects/src/snowpack")

    # 步骤2：执行 run_snowpack.sh
    logger.info(f"❄️ 执行 run_snowpack.sh {end_str}")
    run_shell(f"./run_snowpack.sh {end_str}", cwd="/home/projects/data/snowpack_input")

    # 步骤3：执行 pro_plot.py
    logger.info("🖼️ 执行 pro_plot.py 生成图像")
    run_shell("python pro_plot.py", cwd="/home/projects/src/snowpack")

    logger.info("🎉 Snowpack 全部流程执行完成")


if __name__ == "__main__":
    run()
