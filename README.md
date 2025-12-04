# WRF-SNOWPACK Simulation System

🚀 自动化的气象模拟与雪崩预警系统，集成 WRF、SNOWPACK、NCL 以及前后端服务，支持全流程自动化处理和数据接口调用。

---

## 📌 项目功能概览

本项目集成 WRF 模型和 SNOWPACK 模型，结合定时任务、数据接口与绘图服务，实现如下功能：

1. ⏬ 定时自动下载 GFS 气象数据  

2. ⚙️ 自动修改 WRF/WPS 配置文件（`namelist.wps` 和 `namelist.input`）  

3. 🧭 自动执行 `geogrid.exe`、`metgrid.exe`、`ungrib.exe`、`real.exe`、`wrf.exe` 生成模拟结果  

4. 🗂 自动存放 wrfout 文件于指定路径  

5. 📈 使用 NCL 绘制 wrfout 结果图并返回给前端  

6. 🔁 提供接口读取 wrfout 数据并以 JSON 返回  

7. 🔄 wrfout 转换为 `.smet` 文件供 SNOWPACK 使用  

8. ⚙️ 根据模拟时间动态生成 SNOWPACK `.ini` 文件  

9. ❄️ 执行 SNOWPACK 模拟，生成 `.haz`、`.pro`、`.smet` 等结果文件  

10. 🧊 绘制雪剖面图，分析雪崩预警，提供 JSON 接口返回核心参数


---

## 📁 项目目录结构

```bash
.
├── config
├── data
│   ├── snowpack_input
│   │   ├── test
│   │   └── work
│   ├── snowpack_output
│   └── wrf_output
├── docs
├── logs
├── ncl_scripts
├── src
│   ├── endpoint_api
│   │   └── __pycache__
│   ├── scheduler
│   │   └── __pycache__
│   ├── snowpack
│   │   └── __pycache__
│   └── wrf
│       └── __pycache__
├── static
│   ├── sp_pic
│   ├── wrf_pic_d01
│   └── wrf_pic_d02
└── tests
    └── __pycache__

```
## 🔧 环境与依赖

推荐使用 Conda 管理环境：

```bash
conda create -n wrf_env python=3.10
conda activate wrf_env
pip install -r requirements.txt
```
