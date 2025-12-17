begin
  ; 输入文件路径
  in_files = "/home/projects/data/wrf_output/wrfout_d01_2025-12-15_00:00:00.nc"
  a = addfile(in_files, "r")

  ; 获取时间和经纬度
  times = wrf_user_getvar(a, "times", -1)
  ntimes = dimsizes(times)
  lat = wrf_user_getvar(a, "lat", 0)
  lon = wrf_user_getvar(a, "lon", 0)

  ; 输出路径
  output_dir = "/home/projects/static/wrf_pic_d02/"

  ; 定义格点范围
  x_start = 82
  x_end   = 172
  y_start = 47
  y_end   = 95

  ; 遍历每个时间步，仅保留 00 和 12 点
  do i = 0, ntimes - 1
    t_string = times(i)
    hour_string = str_get_cols(t_string, 11, 12)

    if (hour_string.eq."00" .or. hour_string.eq."12") then
      ; 获取温度变量（单位：K，转为 ℃）
      draw_var3 = wrf_user_getvar(a, "tk", i)
      draw_varc = draw_var3 - 273.15

      ; 获取维度，避免越界
      dims = dimsizes(draw_varc)
      ydim = dims(1)
      xdim = dims(2)

      if (x_start .lt. 0) then
        x1 = 0
      else
        x1 = x_start
      end if

      if (x_end .gt. xdim - 1) then
        x2 = xdim - 1
      else
        x2 = x_end
      end if

      if (y_start .lt. 0) then
        y1 = 0
      else
        y1 = y_start
      end if

      if (y_end .gt. ydim - 1) then
        y2 = ydim - 1
      else
        y2 = y_end
      end if

      ; 截取子区域
      draw_varc_0 = draw_varc(0, y1:y2, x1:x2)

      ; 输出文件名
      t_string_clean = str_sub_str(t_string, " ", "_")
      output_file = output_dir + t_string_clean

      ; 打开 PNG 工作区
      wks_type = "png"
      wks_type@wkBackgroundOpacityF = .0
      wks_type@wkHeight = 2048
      wks_type@wkWidth  = 2048 * (15.0 / 8.0)
      wks_type@wkBackgroundColor = "black"
      wks = gsn_open_wks(wks_type, output_file)

      ; 绘图资源
      res = True
      res@cnFillOn      = True
      res@cnFillPalette = "temp_19lev"
      res@lbOrientation = "Vertical"
      res@lbLabelBarOn  = True
      res@cnLevelSelectionMode = "AutomaticLevels"
      res@lbLabelFontHeightF = 0.015
      res@lbLabelFontColor   = "white"
      res@lbLabelAutoStride  = True

      res = wrf_map_resources(a, res)

      ; 字体颜色与标签调整
      res@gsnStringFontHeightF = 0.025
      res@gsnStringFontColor = "white"
      res@tmXBLabelFontColor = "white"
      res@tmYLLabelFontColor = "white"
      res@tmXBLabelFontHeightF = 0.015
      res@tmYLLabelFontHeightF = 0.015
      res@tmXBLabelDeltaF = -0.6
      res@tmYLLabelDeltaF = -0.6

      ; 添加主标题
      res@tiMainString = "2m Temperature"
      res@tiMainFontHeightF = 0.02
      res@tiMainFont = "helvetica"
      res@tiMainFontColor = "white"
      res@tiMainJust = "CenterLeft"
      res@tiMainOffsetXF = -0.2

      ; 经纬度限制（根据区域自行调整）
      res@mpMinLonF = 95
      res@mpMaxLonF = 103
      res@mpMinLatF = 28
      res@mpMaxLatF = 32

      res@tfDoNDCOverlay = True
      res@gsnAddCyclic = False
      res@mpShapeMode = "FreeAspect"
      res@vpWidthF = 0.8
      res@vpHeightF = 0.8 * (8.0 / 15.0)
      res@vpXF = (1.0 - res@vpWidthF) / 2.0
      res@vpYF = 1.0 - (1.0 - res@vpHeightF) / 2.0

      ; 绘图
      plot_full = gsn_csm_contour_map(wks, draw_varc_0, res)

      print("✔ 成功绘图: " + output_file)
      delete(wks)
    end if
  end do
end
