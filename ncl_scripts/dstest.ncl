begin
  ; 输入文件路径
  in_files = "/home/projects/data/wrf_output/wrfout_d02_merged.nc"
  a = addfile(in_files, "r")

  ; 获取时间和经纬度
  times = wrf_user_getvar(a, "times", -1)
  ntimes = dimsizes(times)
  lat = wrf_user_getvar(a, "lat", 0)
  lon = wrf_user_getvar(a, "lon", 0)

  ; 输出路径
  output_dir = "../static/wrf_pic_d02/"

  ; 遍历每个时间步
  do i = 0, ntimes - 1
    ; 获取变量并转为摄氏度
    draw_var3 = wrf_user_getvar(a, "tk", i)
    draw_varc = draw_var3 - 273.15
    draw_varc_0 = draw_varc(0,:,:)

    ; 格式化时间字符串为 output 文件名，如 2025-04-08_00:00:00
    t_string = times(i)
    t_string_clean = str_sub_str(t_string, " ", "_") ; 将空格替换为 "_"

    ; 输出文件路径（不加 .png，因为 gsn_open_wks 会自动加）
    output_file = output_dir + t_string_clean

    ; 打开 PNG 工作区，高分辨率，调整宽高比例
    wks_type = "png"
    wks_type@wkBackgroundOpacityF = .0
    wks_type@wkHeight = 2048
    wks_type@wkWidth  = 2048 * (15.0 / 8.0) ; 宽度 = 高度 * (15/8)
    wks_type@wkBackgroundColor = "black"
    wks = gsn_open_wks(wks_type, output_file)

    ; 资源设置
    res = True
    res@cnFillOn      = True
    res@cnFillPalette = "temp_19lev"
    res@lbOrientation = "Vertical"
    res@lbLabelBarOn  = True ; 确保显示图例（colorbar）

    ; 设置等温线间隔，手动控制温度级别
    res@cnLevelSelectionMode = "ManualLevels" ; 手动设置等温线
    res@cnMinLevelValF  = -10.0 ; 最小温度
    res@cnMaxLevelValF  = 40.0  ; 最大温度
    res@cnLevelSpacingF = 2.0    ; 每2°C一个级别

    ; 图例标签设置
    res@lbLabelFontHeightF = 0.015 ; 图例标签字体大小
    res@lbLabelFontColor   = "white" ; 图例标签颜色
    res@lbLabelAutoStride  = False ; 禁用自动调整标签间隔
    res@lbLabelStride      = 2 ; 隔一个颜色方块显示一个数字

    res = wrf_map_resources(a, res)

    ; 字体颜色和大小优化
    res@gsnStringFontHeightF = 0.025
    res@gsnStringFontColor = "white"
    res@tmXBLabelFontColor = "white"
    res@tmYLLabelFontColor = "white"
    res@tmXBLabelFontHeightF = 0.015 ; 经纬度标签字体大小
    res@tmYLLabelFontHeightF = 0.015 ; 经纬度标签字体大小
    res@tmXBLabelDeltaF = -0.6
    res@tmYLLabelDeltaF = -0.6

    ; 添加主标题
    res@tiMainString = "2m Temperature"
    res@tiMainFontHeightF = 0.02 ; 字体大小
    res@tiMainFont = "helvetica" ; 非加粗字体
    res@tiMainFontColor = "white"
    res@tiMainJust = "CenterLeft" ; 左对齐
    res@tiMainOffsetXF = -0.2     ; 向左偏移

    ; 经纬度范围
    lat_range = (max(lat) + 1) - (min(lat) - 1)
    lon_range = lat_range * 15.0 / 8.0
    lon_center = (min(lon) + max(lon)) / 2.0
    res@mpMinLonF = lon_center - lon_range / 2.0
    res@mpMaxLonF = lon_center + lon_range / 2.0
    res@mpMinLatF = min(lat) - 1
    res@mpMaxLatF = max(lat) + 1

    ; 地图设置
    res@tfDoNDCOverlay = True
    res@gsnAddCyclic = False

    ; 强制视口比例匹配经纬度范围比例
    res@mpShapeMode = "FreeAspect"
    res@vpWidthF = 0.75 ; 略微减小，为图例留空间
    res@vpHeightF = 0.75 * (8.0 / 15.0) ; 高度 = 宽度 * (8/15)
    res@vpXF = (1.0 - res@vpWidthF) / 2.0
    res@vpYF = 1.0 - (1.0 - res@vpHeightF) / 2.0

    ; 绘图
    plot_full = gsn_csm_contour_map(wks, draw_varc_0, res)

    ; 打印范围信息以便调试
    print("Lat range: " + lat_range)
    print("Lon range: " + lon_range)
    print("mpMinLonF: " + res@mpMinLonF + " mpMaxLonF: " + res@mpMaxLonF)

    delete(wks)
  end do
end