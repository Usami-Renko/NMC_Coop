#!/usr/bin/env python
# coding=UTF-8
'''
@Author: wanghao
@Date: 2019-12-09 16:52:02
@LastEditors: wanghao
@LastEditTime: 2020-06-04 09:00:48
@Description  : process postvar
'''
from read_info_from_ctl import read_info_from_ctl
import os

def config_submodule(cong):
    for key, value in cong.items():
        globals()[key] = value

def get_time_strlist(time):
    segemntsize = 5
    ntimes = len(time)
    nsegments = len(time) // segemntsize
    if len(time) % segemntsize != 0:
        nsegments += 1
    
    segments = [time[isegment*segemntsize:(isegment+1)*segemntsize] \
         if isegment < nsegments - 1 else time[isegment*segemntsize:] \
         for isegment in range(nsegments)]
    
    time_strlist = [','.join(segment) for segment in segments]
    time_strlist[0] = '(/' + time_strlist[0] + ',&'
    for seg_idx in range(1, nsegments-1):
        time_strlist[seg_idx] = '&' + time_strlist[seg_idx] + ',&'
    time_strlist[-1] = '&' + time_strlist[-1] + '/)'
    
    return time_strlist

def transf2nc_F_interp_(ctlfilename,interp_ctlfilename,ex_data,interp2fnl_data,ex_nc,ddate):
    ctlinfo = read_info_from_ctl(ctlfilename)
    interp2fnl_ctlinfo = read_info_from_ctl(interp_ctlfilename)

    nlon,nlat,nlevel,ntime = ctlinfo.dimensions['longitude'],ctlinfo.dimensions['latitude'],ctlinfo.dimensions['levels'],ctlinfo.dimensions['time']
    interp_nlon,interp_nlat = interp2fnl_ctlinfo.dimensions['longitude'],interp2fnl_ctlinfo.dimensions['latitude']
    # print(ctlinfo.filename)
    time = [itime.strftime("%Y%m%d%H") for itime in ctlinfo.variables['time']]
    time_strlist = get_time_strlist(time)
    levels = ctlinfo.variables['levels'][:]
    levels = ','.join([str(ilevel) for ilevel in levels])

    if platform == 'PC':
        real_bytes == 4
    if platform == 'Pi':
        real_bytes == 1

    with open('grapes2nc_{}.f90'.format(ddate),'w') as fili:
        sec_1 = ['program grapes2nc',
                'use netcdf',
                'implicit none',
                '',
                '! 定义数据文件的名称',
                'character(len = 200) :: infile = "{}"'.format(ex_data),
                'character(len = 200) :: interp2fnl_infile = "{}"'.format(interp2fnl_data),
                'character(len = 200) :: ncfile = "{}"'.format(ex_nc),
                '',
                'integer, parameter :: NDIMS = 4, NDIMS_1 = 3',
                'integer, parameter :: nx={}, ny={}'.format(nlon,nlat),
                'integer, parameter :: interp2fnl_nx={}, interp2fnl_ny={}'.format(interp_nlon,interp_nlat),
                'integer, parameter :: nz={}, nt={}'.format(nlevel,ntime),
                'integer :: it,iz,iy,ix,n_rec',
                '',
                '! 当创建netCDF文件的时候，变量和维数都有一个对应的ID',
                'integer :: ncid, x_dimid, y_dimid, z_dimid, t_dimid, &', 
                '& interp2fnl_x_dimid, interp2fnl_y_dimid,dimids(NDIMS),dimids_1(NDIMS_1), &',
                '& interp2fnl_dimids(NDIMS),interp2fnl_dimids_1(NDIMS_1)',
                'integer :: lon_varid, lat_varid, interp2fnl_lon_varid, interp2fnl_lat_varid, time_varid, level_varid',
                'integer :: dimids_lon(1), dimids_lat(1), dimids_time(1), dimids_level(1)',
                'integer :: interp2fnl_dimids_lon(1), interp2fnl_dimids_lat(1)',
                ''
                'real      :: level(nz), lat(ny), lon(nx), interp2fnl_lat(interp2fnl_ny), interp2fnl_lon(interp2fnl_nx)',
                'integer   :: time(nt)',
                'real      :: temp(nx,ny)'
                ]
        sec_1 = [line+'\n' for line in sec_1] # 在list中加入换行符
        fili.writelines(sec_1)
        
        sec_2 = ['integer :: ']
        sec_3 = ['real, dimension(:,:,:,:), allocatable :: ']
        sec_4 = ['real, dimension(:,:,:), allocatable :: ']
        for inn,ivar in enumerate(ctlinfo.varname):
            sec_2.append(ivar+'_varid,')
            if ctlinfo.variables[ivar].dimensions == nlevel:
                sec_3.append(ivar+',')
            elif ctlinfo.variables[ivar].dimensions == 1:
                sec_4.append(ivar+',')
        
        fili.writelines(''.join(sec_2).strip(',')+'\n')
        fili.writelines('!要保存到文件的数据数组\n')
        fili.writelines(''.join(sec_3).strip(',')+'\n')
        fili.writelines(''.join(sec_4).strip(',')+'\n')
        
        #fili.write('print*,"infile ==", trim(adjustl(infile))\n')
        #fili.write('print*,"ncfile ==", trim(adjustl(ncfile))\n')

        fili.writelines('\n! 为数据数组分配内存\n')
        for ivar in ctlinfo.varname:
            if ivar in interp2fnl_ctlinfo.varname:
                if interp2fnl_ctlinfo.variables[ivar].dimensions == nlevel:
                    fili.write('allocate({}(interp2fnl_nx,interp2fnl_ny,nz,nt))\n'.format(ivar))
                elif interp2fnl_ctlinfo.variables[ivar].dimensions == 1:
                    fili.write('allocate({}(interp2fnl_nx,interp2fnl_ny,nt))\n'.format(ivar))
            else:
                if ctlinfo.variables[ivar].dimensions == nlevel:
                    fili.write('allocate({}(nx,ny,nz,nt))\n'.format(ivar))
                elif  ctlinfo.variables[ivar].dimensions == 1:
                    fili.write('allocate({}(nx,ny,nt))\n'.format(ivar))

        fili.write('\n! 生成时间信息\n')
        fili.write('time = {}\n'.format(time_strlist[0]))
        if len(time_strlist) > 1:
            for timestr in time_strlist[1:]:
                fili.write('{}\n'.format(timestr))
        
        fili.write('\n! 生成层次信息\n')
        fili.write('level = (/{}/)\n'.format(levels))

        fili.write('\n! 生成经纬度信息\n')
        fili.write('do iy = 1,ny\n')
        fili.write('  lat(iy) = {}+{}*({}-1)\n'.format(ctlinfo.variables['latitude'][0],ctlinfo.crement['latitude'],'iy'))
        fili.write('end do\n')
        fili.write('do ix = 1,nx\n')
        fili.write('  lon(ix) = {}+{}*({}-1)\n'.format(ctlinfo.variables['longitude'][0],ctlinfo.crement['longitude'],'ix'))
        fili.write('end do\n')
        
        fili.write('do iy = 1, interp2fnl_ny\n')
        fili.write('  interp2fnl_lat(iy) = {}+{}*({}-1)\n'.format(interp2fnl_ctlinfo.variables['latitude'][0],interp2fnl_ctlinfo.crement['latitude'],'iy'))
        fili.write('end do\n')
        fili.write('do ix = 1,interp2fnl_nx\n')
        fili.write('  interp2fnl_lon(ix) = {}+{}*({}-1)\n'.format(interp2fnl_ctlinfo.variables['longitude'][0],interp2fnl_ctlinfo.crement['longitude'],'ix'))
        fili.write('end do\n')

        fili.write('\n! 往数据数组里写数据\n')
        fili.write('! 读取不需要插值的变量\n')
        fili.write('open(99,file=trim(adjustl(infile)),form="unformatted",access="direct",recl=nx*ny*{})\n'.format(real_bytes))
        fili.write('n_rec = 0\n')
        fili.write('do it = 1, nt\n')
        for ivar in ctlinfo.varname:
            if ivar in interp2fnl_ctlinfo.varname:
                if interp2fnl_ctlinfo.variables[ivar].dimensions == nlevel:
                    fili.write('  do iz = 1, nz\n')
                    fili.write('    n_rec = n_rec + 1\n')
                    fili.write('    read(99,rec=n_rec)((temp(ix,iy),ix=1,nx),iy=1,ny)\n')
                    fili.write('  end do\n')
                elif interp2fnl_ctlinfo.variables[ivar].dimensions == 1:
                    fili.write('  n_rec = n_rec + 1\n')
                    fili.write('  read(99,rec=n_rec)(({}(ix,iy,it),ix=1,nx),iy=1,ny)\n'.format(ivar))
            else:
                if ctlinfo.variables[ivar].dimensions == nlevel:
                    fili.write('  do iz = 1, nz\n')
                    fili.write('    n_rec = n_rec + 1\n')
                    fili.write('    read(99,rec=n_rec)(({}(ix,iy,iz,it),ix=1,nx),iy=1,ny)\n'.format(ivar))
                    fili.write('  end do\n')
                elif ctlinfo.variables[ivar].dimensions == 1:
                    fili.write('  n_rec = n_rec + 1\n')
                    fili.write('  read(99,rec=n_rec)(({}(ix,iy,it),ix=1,nx),iy=1,ny)\n'.format(ivar))
        fili.write('end do\n')
        fili.write('close(99)\n')
        
        fili.write('\n! 读取插值变量\n')
        fili.write('open(99,file=trim(adjustl(interp2fnl_infile)),form="unformatted",access="direct",recl=interp2fnl_nx*interp2fnl_ny*{})\n'.format(real_bytes))
        fili.write('n_rec = 0\n')
        fili.write('do it = 1, nt\n')
        for ivar in interp2fnl_ctlinfo.varname:
            if interp2fnl_ctlinfo.variables[ivar].dimensions == nlevel:
                fili.write('  do iz = 1, nz\n')
                fili.write('    n_rec = n_rec + 1\n')
                fili.write('    read(99,rec=n_rec)(({}(ix,iy,iz,it),ix=1,interp2fnl_nx),iy=1,interp2fnl_ny)\n'.format(ivar))
                fili.write('  end do\n')
            if interp2fnl_ctlinfo.variables[ivar].dimensions == 1:
                fili.write('  n_rec = n_rec + 1\n')
                fili.write('  read(99,rec=n_rec)(({}(ix,iy,it),ix=1,interp2fnl_nx),iy=1,interp2fnl_ny)\n'.format(ivar))
        fili.write('end do\n')
        fili.write('close(99)\n')

        fili.write('\n! 创建netCDF文件，返回文件对应的ID，如果存在则覆盖，check子程序用来检验执行是否成功 \n')
        fili.write('call check( nf90_create(trim(adjustl(ncfile)), cmode=or(nf90_clobber,nf90_64bit_offset), ncid=ncid) )\n')
        
        fili.write('\n! 定义维数，返回一个对应的ID \n')
        fili.write('call check( nf90_def_dim(ncid, "ntime", nt, t_dimid) )\n')
        fili.write('call check( nf90_def_dim(ncid, "nlevel", nz, z_dimid) )\n')
        fili.write('call check( nf90_def_dim(ncid, "nlat", ny, y_dimid) )\n')
        fili.write('call check( nf90_def_dim(ncid, "nlon", nx, x_dimid) )\n')
        fili.write('call check( nf90_def_dim(ncid, "interp2fnl_nlat", interp2fnl_ny, interp2fnl_y_dimid) )\n')
        fili.write('call check( nf90_def_dim(ncid, "interp2fnl_nlon", interp2fnl_nx, interp2fnl_x_dimid) )\n')

        fili.write('\n! 把上面得到的ID写到一个存放ID的数组里，注意，在fortran中，数组是以列为主存放数据的 \n')
        fili.write('dimids =  (/ x_dimid, y_dimid, z_dimid, t_dimid /)\n')
        fili.write('dimids_1 =  (/ x_dimid, y_dimid, t_dimid /)\n')
        fili.write('dimids_lon   =  (/ x_dimid /)\n')
        fili.write('dimids_lat   =  (/ y_dimid /)\n')
        fili.write('interp2fnl_dimids = (/ interp2fnl_x_dimid, interp2fnl_y_dimid, z_dimid, t_dimid /)\n')
        fili.write('interp2fnl_dimids_lon = (/ interp2fnl_x_dimid /)\n')
        fili.write('interp2fnl_dimids_lat = (/ interp2fnl_y_dimid /)\n')
        fili.write('dimids_level =  (/ z_dimid /)\n')
        fili.write('dimids_time  =  (/ t_dimid /)\n')

        fili.write('\n! 定义变量，返回一个对应的ID\n')
        fili.write('call check( nf90_def_var(ncid, "times", nf90_int, dimids_time, time_varid) )\n')
        fili.write('call check( nf90_put_att(ncid, time_varid, "incr", "{}"))\n'.format(int(ctlinfo.crement['time'].total_seconds()/3600)))
        fili.write('call check( nf90_def_var(ncid, "levels", nf90_float, dimids_level, level_varid) )\n')
        fili.write('call check( nf90_put_att(ncid, level_varid, "units", "hPa"))\n')
        fili.write('call check( nf90_def_var(ncid, "latitude", nf90_float, dimids_lat, lat_varid) )\n')
        fili.write('call check( nf90_put_att(ncid, lat_varid, "units", "degree_north"))\n')
        fili.write('call check( nf90_def_var(ncid, "longitude", nf90_float, dimids_lon, lon_varid) )\n')
        fili.write('call check( nf90_put_att(ncid, lon_varid, "units", "degree_east"))\n')
        fili.write('call check( nf90_def_var(ncid, "interp2fnl_latitude", nf90_float, interp2fnl_dimids_lat, interp2fnl_lat_varid) )\n')
        fili.write('call check( nf90_put_att(ncid, interp2fnl_lat_varid, "units", "degree_north"))\n')
        fili.write('call check( nf90_def_var(ncid, "interp2fnl_longitude", nf90_float, interp2fnl_dimids_lon, interp2fnl_lon_varid) )\n')
        fili.write('call check( nf90_put_att(ncid, interp2fnl_lon_varid, "units", "degree_east"))\n')
        for ivar in ctlinfo.varname:
            if ivar in interp2fnl_ctlinfo.varname:
                if interp2fnl_ctlinfo.variables[ivar].dimensions == nlevel:
                    fili.write('call check( nf90_def_var(ncid, "{}", nf90_float, interp2fnl_dimids, {}_varid) )\n'.format(ivar,ivar))
                elif interp2fnl_ctlinfo.variables[ivar].dimensions == 1:
                    fili.write('call check( nf90_def_var(ncid, "{}", nf90_float, interp2fnl_dimids_1, {}_varid) )\n'.format(ivar,ivar))
                fili.write('call check( nf90_put_att(ncid, {}_varid, "long_name", "{}"))\n'.format(ivar,ctlinfo.variables[ivar].attributes['long_name']))
            else:
                if ctlinfo.variables[ivar].dimensions == nlevel:
                    fili.write('call check( nf90_def_var(ncid, "{}", nf90_float, dimids, {}_varid) )\n'.format(ivar,ivar))
                elif ctlinfo.variables[ivar].dimensions == 1:
                    fili.write('call check( nf90_def_var(ncid, "{}", nf90_float, dimids_1, {}_varid) )\n'.format(ivar,ivar))
                fili.write('call check( nf90_put_att(ncid, {}_varid, "long_name", "{}"))\n'.format(ivar,ctlinfo.variables[ivar].attributes['long_name']))

        fili.write('call check( nf90_put_att(ncid, nf90_global, "description", "Transf postvar data to NC"))')

        fili.write('\n! 定义完成，关闭定义模式 \n')
        fili.write('call check( nf90_enddef(ncid) )\n')

        fili.write('\n! 写入数据 \n')
        fili.write('call check( nf90_put_var(ncid, time_varid, time) )\n')
        fili.write('call check( nf90_put_var(ncid, level_varid, level) )\n')
        fili.write('call check( nf90_put_var(ncid, lat_varid, lat) )\n')
        fili.write('call check( nf90_put_var(ncid, lon_varid, lon) )\n')
        fili.write('call check( nf90_put_var(ncid, interp2fnl_lon_varid, interp2fnl_lon) )\n')
        fili.write('call check( nf90_put_var(ncid, interp2fnl_lat_varid, interp2fnl_lat) )\n')
        for ivar in ctlinfo.varname:
            fili.write('call check( nf90_put_var(ncid, {}_varid, {}) )\n'.format(ivar,ivar) )
        
        fili.write('\n! 关闭文件 \n')
        fili.write('call check( nf90_close(ncid) )\n')

        fili.write('\n! 提示写文件成功 \n')
        fili.write('print *, "*** SUCCESS writing example file ", trim(adjustl(ncfile))\n')
        
        fili.write('\n')
        for ivar in ctlinfo.varname:
            fili.write('deallocate({})\n'.format(ivar))
        
        fili.write('\ncontains\n')
        fili.write('  subroutine check(status)\n')
        fili.write('  integer, intent ( in) :: status\n')

        fili.write('\n  if(status /= nf90_noerr) then\n')
        fili.write('    print *, trim(nf90_strerror(status))\n')
        fili.write('    stop 2\n')
        fili.write('  end if\n')
        fili.write('  end subroutine check\n')
        fili.write('end program grapes2nc\n')

        fili.close()
