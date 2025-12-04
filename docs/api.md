URL                                             功能说明
http://localhost:2012/                          首页欢迎



http://localhost:2012/pro/process_files         获取所有站点最新.pro/.smet 数据
http://localhost:2012/pro/get_latest_images     获取所有图像名 -路径映射
http://localhost:2012/pro/get_image/xxx.png     获取指定图像文件内容

http://localhost:2012/ncl/run	            	触发 .nc 文件的处理（执行 NCL 脚本生成图片）
http://localhost:2012/ncl/plot_temp_profile 	对 .pro 文件生成雪温剖面图
http://localhost:2012/ncl/plot_snow_type	    对 .pro 文件生成积雪类型分布图


http://113.62.130.58:10012/wrf/latest-pic	    获取 data/wrf_output/pic/ 中最新生成的图片文件内容
http://113.62.130.58:10012/getParams	        提取最新一个.nc 文件中的平均气象参数（温度、积雪、水汽、风速等）