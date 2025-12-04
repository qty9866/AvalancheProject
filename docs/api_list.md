# 📘 WRF & SNOWPACK API 接口文档

## 🚀 **启动项目：**

```bash
nohup mpirun -np 32 ./wrf.exe &
```

cd /home/projects/
# 测试
python -m src.endpoint_api.api_server 
# 生产
gunicorn -w 16 -b 0.0.0.0:10012 src.endpoint_api.api_server:app > /home/projects/logs/gunicorn.log 2>&1 &
# 生产输出日志
gunicorn -w 8 -b 0.0.0.0:10012 src.endpoint_api.api_server:app \
--access-logfile /home/projects/logs/gunicorn_access.log \
--error-logfile /home/projects/logs/gunicorn_error.log \
--capture-output --log-level info \
--enable-stdio-inheritance &
# 关闭服务
fuser -k 10012/tcp

# 定时任务开启
```bash
cd /home/projects/ 
nohup python -m src.scheduler.jobs > /home/projects/logs/scheduler.out 2>&1 &
```
