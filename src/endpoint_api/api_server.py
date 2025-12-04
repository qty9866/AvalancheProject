from flask import Flask
from flask_cors import CORS

from src.endpoint_api.pro_parser import pro_parser_bp # ✅ 注册雪情数据解析模块
from src.endpoint_api.wrf_visual import wrf_visual_bp # ✅ 注册 WRF 可视化模块
#from src.endpoint_api.postprocess_ncl import postprocess_ncl_bp # ✅ 注册 NCL 后处理模块
from src.endpoint_api.calculate_ARI import calculate_ari_bp # ✅ 注册 ARI 计算模块
# 设置静态文件目录
app = Flask(__name__, static_folder='/home/projects/static', static_url_path='/static')
CORS(app)  # 开放跨域请求给前端

app.register_blueprint(pro_parser_bp, url_prefix="/pro") 
app.register_blueprint(wrf_visual_bp, url_prefix="/wrf")  
# app.register_blueprint(postprocess_ncl_bp, url_prefix="/ncl")
app.register_blueprint(calculate_ari_bp, url_prefix="/ari")

# ✅ 启动定时任务
#start_schedule_thread()  # 这边解耦了 后期

@app.route("/")
def index():
    return {"message": "Welcome to the WRF&SNOWPACK API Server From CICDI!🎿"}

if __name__ == "__main__":
    # 打印所有注册的接口信息
    print("\n📍 Registered API Routes:")
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        print(f"{rule.endpoint:30s} {methods:20s} {rule.rule}")
    app.run(host="0.0.0.0", port=10012, debug=True)