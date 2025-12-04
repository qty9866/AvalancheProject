# src/scheduler/jobs.py
from src.wrf.download_gfs import run as gfs_download
from src.wrf.run_wps import run as run_wps
from src.wrf.run_wrf import run as run_wrf
from src.wrf.postprocess import run as postprocess
from src.snowpack.run_snowpack import run as run_snowpack
from apscheduler.schedulers.blocking import BlockingScheduler
from pytz import timezone


def start_scheduler():
    scheduler = BlockingScheduler(timezone=timezone("Asia/Shanghai"))
    scheduler.add_job(gfs_download, 'cron', hour=17, minute=30)
    scheduler.add_job(run_wps, 'cron', hour=22, minute=0)
    scheduler.add_job(run_wrf, 'cron', hour=22, minute=20)
    scheduler.add_job(postprocess, 'cron', hour=23, minute=30)
    scheduler.add_job(run_snowpack, 'cron', hour=23, minute=50)

    print("✅ 定时任务调度器启动中...")
    scheduler.start()

if __name__ == "__main__":
    start_scheduler()