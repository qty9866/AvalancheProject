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

    ; 打开 PNG 工作区，高分辨率
    wks_type = "png"
    wks_type@wkBackgroundOpacityF = .0
    wks_type@wkHeight = 2048
    wks_type@wkWidth  = 2048
    wks_type@wkBackgroundColor = "black"
    wks = gsn_open_wks(wks_type, output_file)

    ; 资源设置
    res = True
    res@cnFillOn      = True
    res@cnFillPalette = "temp_19lev"
    res@lbOrientation = "Vertical"

    res = wrf_map_resources(a, res)

    ; 字体颜色和大小优化
    res@gsnStringFontHeightF = 0.025
    res@gsnStringFontColor = "white"
    res@tmXBLabelFontColor = "white"
    res@tmYLLabelFontColor = "white"
    res@lbLabelFontColor   = "white"
    res@tmXBLabelFontHeightF = 0.018
    res@tmYLLabelFontHeightF = 0.018
    res@tmXBLabelDeltaF = -0.6
    res@tmYLLabelDeltaF = -0.6

    ; 添加主标题
    res@tiMainString = "2m Temperature (" + t_string + ")"
    res@tiMainFontHeightF = 0.025
    res@tiMainFontColor = "white"

    ; 经纬度范围
    res@mpMinLatF = min(lat)-1
    res@mpMaxLatF = max(lat)+1
    res@mpMinLonF = min(lon)-1
    res@mpMaxLonF = max(lon)+1

    ; 地图设置
    res@tfDoNDCOverlay = True
    res@gsnAddCyclic = False

    ; 绘图
    plot_full = gsn_csm_contour_map(wks, draw_varc_0, res)

    delete(wks)
  end do
end  