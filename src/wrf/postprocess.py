# import os
# import shutil
# import logging
# from datetime import datetime, timezone, timedelta
# import subprocess
# from PIL import Image

# # =============================
# # 日志系统初始化
# # =============================
# log_dir = "/home/projects/logs"
# os.makedirs(log_dir, exist_ok=True)
# log_path = os.path.join(log_dir, "postprocess.log")

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s - %(levelname)s - %(message)s",
#     handlers=[ 
#         logging.FileHandler(log_path, mode='a'),
#     ]
# )
# logger = logging.getLogger(__name__)

# # =============================
# # 常量路径
# # =============================
# WRF_WORK_DIR = "/WRF/Product_WRF/work"
# WRF_OUTPUT_DIR = "/home/projects/data/wrf_output"
# NCL_SCRIPT_DIR = "/home/projects/ncl_scripts"
# STATIC_DIRS = [
#     "/home/projects/static/wrf_pic_d01/",
#     "/home/projects/static/wrf_pic_d02/"
# ]


# def clear_output_directory():
#     """清空输出目录 wrf_output"""
#     logger.info("🧹 清空旧的 wrf_output 输出目录...")
#     for f in os.listdir(WRF_OUTPUT_DIR):
#         fpath = os.path.join(WRF_OUTPUT_DIR, f)
#         if os.path.isfile(fpath):
#             os.remove(fpath)
#     for static_dir in STATIC_DIRS:
#         logger.info(f"🧹 清空图像输出目录: {static_dir}")
#         for f in os.listdir(static_dir):
#             fpath = os.path.join(static_dir, f)
#             if os.path.isfile(fpath):
#                 os.remove(fpath)


# def copy_latest_wrfout():
#     """复制今天的 wrfout 文件到输出目录"""
#     CHINA_TZ = timezone(timedelta(hours=8))
#     # today_str = datetime.now(CHINA_TZ).strftime('%Y-%m-%d')
#     yesterday = datetime.now(CHINA_TZ) - timedelta(days=1)
#     today_str = yesterday.strftime('%Y-%m-%d')
#     target_name = f"wrfout_d01_{today_str}_00:00:00"
#     target_name_with_suffix = target_name + ".nc"
#     source_path = os.path.join(WRF_WORK_DIR, target_name)
#     target_path = os.path.join(WRF_OUTPUT_DIR, target_name_with_suffix)

#     if not os.path.exists(source_path):
#         raise FileNotFoundError(f"❌ 找不到文件: {source_path}")

#     shutil.copy2(source_path, target_path)
#     logger.info(f"✅ 已复制 wrfout 文件到输出目录: {target_path}")
#     return target_path  # 返回目标路径供后续修改 NCL 使用

# def modify_ncl_scripts(input_path):
#     """修改 d01.ncl 和 d02.ncl 中的输入路径"""
#     for script_name in ["d01.ncl", "d02.ncl"]:
#         script_path = os.path.join(NCL_SCRIPT_DIR, script_name)
#         logger.info(f"📝 修改 {script_name} 输入路径为: {input_path}")
#         with open(script_path, "r") as f:
#             lines = f.readlines()

#         for i, line in enumerate(lines):
#             if "in_files" in line:
#                 lines[i] = f'  in_files = "{input_path}"\n'
#                 break

#         with open(script_path, "w") as f:
#             f.writelines(lines)


# def run_ncl_scripts():
#     """运行 NCL 脚本 d01.ncl 和 d02.ncl"""
#     logger.info("📈 执行 NCL 绘图脚本...")

#     # 获取当前系统环境变量，并补充 Conda 环境变量
#     env = os.environ.copy()
#     env["PATH"] = "/root/miniconda3/envs/wrf_env/bin:" + env["PATH"]
#     env["LD_LIBRARY_PATH"] = "/root/miniconda3/envs/wrf_env/lib"
#     env["NCARG_ROOT"] = "/root/miniconda3/envs/wrf_env"

#     for script in ["d01.ncl", "d02.ncl"]:
#         cmd = f"ncl {script}"
#         try:
#             subprocess.run(cmd, shell=True, cwd=NCL_SCRIPT_DIR, check=True, env=env)
#             logger.info(f"✅ 已完成: {cmd}")
#         except subprocess.CalledProcessError as e:
#             logger.error(f"❌ 执行失败: {cmd}，错误信息: {e}")


# def crop_images():
#     """裁剪 wrf_pic_d01 和 wrf_pic_d02 中的图片"""
#     logger.info("✂️ 正在裁剪图片...")
#     for directory in STATIC_DIRS:
#         for filename in os.listdir(directory):
#             if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
#                 try:
#                     file_path = os.path.join(directory, filename)
#                     img = Image.open(file_path)
#                     width, height = img.size
#                     left = 960
#                     top = 450
#                     right = width - 835
#                     bottom = height - 450

#                     cropped_img = img.crop((left, top, right, bottom))
#                     cropped_img.save(file_path)
#                     logger.info(f"✅ 图片已裁剪: {filename}")
#                 except Exception as e:
#                     logger.error(f"处理图片 {filename} 时出错: {e}")


# def run():
#     logger.info("🏁 启动 WRF 后处理流程")
#     clear_output_directory()
#     wrfout_path = copy_latest_wrfout()
#     modify_ncl_scripts(wrfout_path)
#     run_ncl_scripts()
#     crop_images()
#     logger.info("🎉 后处理流程完成")


# if __name__ == "__main__":
#     run()

import os
import shutil
import logging
from datetime import datetime, timezone, timedelta
import subprocess
from PIL import Image

# =============================
# 日志系统初始化
# =============================
log_dir = "/home/projects/logs"
os.makedirs(log_dir, exist_ok=True)
log_path = os.path.join(log_dir, "postprocess.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[ 
        logging.FileHandler(log_path, mode='a'),
    ]
)
logger = logging.getLogger(__name__)

# =============================
# 常量路径
# =============================
WRF_WORK_DIR = "/WRF/Product_WRF/work"
WRF_OUTPUT_DIR = "/home/projects/data/wrf_output"
NCL_SCRIPT_DIR = "/home/projects/ncl_scripts"
STATIC_DIRS = [
    "/home/projects/static/wrf_pic_d01/",
    "/home/projects/static/wrf_pic_d02/"
]

# =============================
# 函数定义
# =============================

def clear_output_directory():
    """清空输出目录 wrf_output 和静态图片目录"""
    logger.info("🧹 清空旧的 wrf_output 输出目录...")
    for f in os.listdir(WRF_OUTPUT_DIR):
        fpath = os.path.join(WRF_OUTPUT_DIR, f)
        if os.path.isfile(fpath):
            os.remove(fpath)

    for static_dir in STATIC_DIRS:
        logger.info(f"🧹 清空图像输出目录: {static_dir}")
        for f in os.listdir(static_dir):
            fpath = os.path.join(static_dir, f)
            if os.path.isfile(fpath):
                os.remove(fpath)


def prepare_new_wrfout():
    """
    尝试准备新的 wrfout 文件（临时目录）
    - 不破坏现有结果
    - 成功返回临时文件路径
    """
    CHINA_TZ = timezone(timedelta(hours=8))
    yesterday = datetime.now(CHINA_TZ) - timedelta(days=1)
    date_str = yesterday.strftime('%Y-%m-%d')

    wrf_name = f"wrfout_d01_{date_str}_00:00:00"
    source_path = os.path.join(WRF_WORK_DIR, wrf_name)

    if not os.path.exists(source_path):
        logger.error(f"❌ 新 wrfout 不存在: {source_path}")
        return None

    # 简单可用性校验（文件大小）
    if os.path.getsize(source_path) < 100 * 1024 * 1024:  # 小于100MB则认为异常
        logger.error("❌ wrfout 文件异常（体积过小，可能未跑完）")
        return None

    # 临时目录
    tmp_dir = os.path.join(WRF_OUTPUT_DIR, "_tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_target = os.path.join(tmp_dir, wrf_name + ".nc")

    shutil.copy2(source_path, tmp_target)
    logger.info(f"📦 新 wrfout 已准备完成（临时）: {tmp_target}")
    return tmp_target


def modify_ncl_scripts(input_path):
    """修改 d01.ncl 和 d02.ncl 中的输入路径"""
    for script_name in ["d01.ncl", "d02.ncl"]:
        script_path = os.path.join(NCL_SCRIPT_DIR, script_name)
        logger.info(f"📝 修改 {script_name} 输入路径为: {input_path}")
        with open(script_path, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            if "in_files" in line:
                lines[i] = f'  in_files = "{input_path}"\n'
                break

        with open(script_path, "w") as f:
            f.writelines(lines)


def run_ncl_scripts():
    """运行 NCL 脚本 d01.ncl 和 d02.ncl"""
    logger.info("📈 执行 NCL 绘图脚本...")

    env = os.environ.copy()
    env["PATH"] = "/root/miniconda3/envs/wrf_env/bin:" + env["PATH"]
    env["LD_LIBRARY_PATH"] = "/root/miniconda3/envs/wrf_env/lib"
    env["NCARG_ROOT"] = "/root/miniconda3/envs/wrf_env"

    for script in ["d01.ncl", "d02.ncl"]:
        cmd = f"ncl {script}"
        try:
            subprocess.run(cmd, shell=True, cwd=NCL_SCRIPT_DIR, check=True, env=env)
            logger.info(f"✅ 已完成: {cmd}")
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ 执行失败: {cmd}，错误信息: {e}")


def crop_images():
    """裁剪 wrf_pic_d01 和 wrf_pic_d02 中的图片"""
    logger.info("✂️ 正在裁剪图片...")
    for directory in STATIC_DIRS:
        for filename in os.listdir(directory):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                try:
                    file_path = os.path.join(directory, filename)
                    img = Image.open(file_path)
                    width, height = img.size
                    left = 960
                    top = 450
                    right = width - 835
                    bottom = height - 450

                    cropped_img = img.crop((left, top, right, bottom))
                    cropped_img.save(file_path)
                    logger.info(f"✅ 图片已裁剪: {filename}")
                except Exception as e:
                    logger.error(f"处理图片 {filename} 时出错: {e}")


def run():
    logger.info("🏁 启动 WRF 后处理流程")

    # 1️⃣ 尝试准备新 wrfout（不破坏旧数据）
    new_wrfout = prepare_new_wrfout()
    if new_wrfout is None:
        logger.warning("⚠️ 新 wrfout 未就绪，保留现有结果，后处理终止")
        return

    # 2️⃣ 新 wrfout 可用，清空旧目录并替换
    clear_output_directory()
    final_wrfout = os.path.join(WRF_OUTPUT_DIR, os.path.basename(new_wrfout))
    shutil.move(new_wrfout, final_wrfout)

    # 3️⃣ 后续处理
    modify_ncl_scripts(final_wrfout)
    run_ncl_scripts()
    crop_images()

    logger.info("🎉 后处理流程完成")


if __name__ == "__main__":
    run()
