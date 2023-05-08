%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%
%                          %%%%  不进行插值  %%%%
%
%      在已知时间确定要读取的H8数据的情况下，根据CALIPSO经纬度（LL）读取H8各波段数据。
%
%      function H8bands = getH8bands(lat_cal1,lon_cal1,h8data)
%
%      所有function已经放在主函数后面，不用调去单独的function
%
%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
clear
tStart = tic;
% addpath('/Users/fu/数据/calipso/vfm_plot/processH8/CALIPSO');
%% 设置H8 CALIPSO路径 /home/fuhy/data/CALIPSO
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
addpath(genpath('/home/fuhy/public/data/H8/L1/'));
addpath(genpath('/home/fuhy/CALIPSO/APro/2016/'));
% addpath(genpath('/home/fuhy/data/CALIPSO/'));
load('H8Timelist.mat');
% calpathname = '/Users/fu/数据/calipso/vfm_plot/processH8/CALIPSO/';
% h8pathname = '/Users/fu/数据/calipso/vfm_plot/';
calpathname = '/home/fuhy/data/CALIPSO/';
% h8pathname = '/home/fuhy/jma/netcdf/';
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
parfor mon_num = 3:5
    %%
    % 读入CALIPSO数据
    calfilename = [calpathname,'CALIPSO_AVD_2016_',num2str(mon_num,'%.2d'),'.csv'];
    if isfile(calfilename)
        cal_ds = tabularTextDatastore(calfilename,'TreatAsMissing','NA','MissingValue',0);
        cal_ds.SelectedVariableNames = {'Latitude_2','Longitude_2','Profile_UTC_Time_2'};% 选择ds变量
        % 读取CALIPSO经纬度及时间
        cal_ds_s = readall(cal_ds);
        % 经纬度信息
        lat_cal = double(cal_ds_s.Latitude_2);
        lon_cal = double(cal_ds_s.Longitude_2);
        to360num = find(lon_cal < 0);
        lon_cal(to360num) = lon_cal(to360num) + 360; % 将经度范围从-180～180转换为0～360
        strdtime_cal = cal_ds_s.Profile_UTC_Time_2;
        strdtime_cal = cvrtStrdTime(strdtime_cal); % 格式'yyyyMMddHHmmss'
        %%
        % 设置要读取的H8数据集，主要为16波段信息及经纬度
        fieldname = {'albedo_01','albedo_02','albedo_03','albedo_04','albedo_05','albedo_06',...
            'tbb_07','tbb_08','tbb_09','tbb_10','tbb_11','tbb_12',...
            'tbb_13','tbb_14','tbb_15','tbb_16','SOZ','SAZ','SOA','SAA','Hour'};
        m = length(strdtime_cal);
        num_H8field = length(fieldname);
        h8bands = NaN(m,num_H8field);
        for n1 = 1:m
            [date, time] = cal2h8dt2(strdtime_cal(n1),lat_cal(n1),lon_cal(n1),TimeList); % 转为H8日期和时间
            % 时间信息
            filename = strcat('NC_H08_',date,'_',time(1:4),'_R21_FLDK.06001_06001.nc');
            % 空间范围限定
            if exist(filename,'file') == 2 ...
                    && lon_cal(n1) > 79.99 && lon_cal(n1) < 200.01 ...
                    && lat_cal(n1) >-60.01 && lat_cal(n1) < 60.01
                h8bands(n1,:) = getH8Bands(lon_cal(n1),lat_cal(n1),filename,fieldname);
            end
            if n1/(0.0001*m) == fix(n1/(0.0001*m))
                p=round(n1/m*100,2); %这样做是可以让进度条的%位数为2位
                tEnd = toc(tStart);
                str=['Processing ',num2str(mon_num,'%.2d'),', 2016. ',num2str(p),...
                    '%, ',num2str(n1),'/',num2str(m),' finished. Elapsed time = ',tEnd];%进度条上显示的内容
                disp(str);

                various={'albedo_01','albedo_02','albedo_03','albedo_04','albedo_05','albedo_06',...
                    'tbb_07','tbb_08','tbb_09','tbb_10','tbb_11','tbb_12',...
                    'tbb_13','tbb_14','tbb_15','tbb_16','SOZ','SAZ','SOA','SAA','H8Hour'};
                H8bands = array2table(h8bands,'VariableNames',various);
                savename = ['H8_SWC_2016_',num2str(mon_num,'%.2d'),'.csv'];
                writetable(H8bands,savename);
            end
        end
        various={'albedo_01','albedo_02','albedo_03','albedo_04','albedo_05','albedo_06',...
            'tbb_07','tbb_08','tbb_09','tbb_10','tbb_11','tbb_12',...
            'tbb_13','tbb_14','tbb_15','tbb_16','SOZ','SAZ','SOA','SAA','H8Hour'};
        H8bands = array2table(h8bands,'VariableNames',various);
        savename = ['H8_SWC_2016_',num2str(mon_num,'%.2d'),'.csv'];
        writetable(H8bands,savename);
    end
end
%% Get H8'times in the format of H8'filenames.
function H8time = cvrtStrdTime(time_cal)
% CALIPSO Profile_UTC_Time转换为'yyyyMMddHHmmss'
format longG
time_flr = floor(time_cal); % 向下取整
time_day = time_cal - time_flr; % 得到天的比例小数
H8time = datetime(num2str(time_flr),'Format','yyMMdd')+days(time_day);
H8time.Format = 'yyyyMMddHHmmss';
end
%% Get H8 bands according to CALIPSO's latitudes and longitudes.
% 20220721
% 修改：
%       1. 不读取H8经纬度网格：认为H8观测经纬度固定，直接计算读取的位置即可；
%       2. 不插值：插值对各波段无影响，通过计算各波段梯度来确定
function H8bands = getH8Bands(lon_cal,lat_cal,h8data_name,fieldname)
% lon_cal 已转换为0-360
% lat_cal 为90 - -90

% 找到距离CALIPSO最近的H8点经纬度
% H8经纬度为0.02度的网格，保留2位小数
% lat_h8=round(lat_cal/0.02)*0.02;
% lon_h8=round(lon_cal/0.02)*0.02;

% 确定目标点不超出边界
lon_cal=max(80.0,lon_cal);
lon_cal=min(200.0,lon_cal);
lat_cal=max(-60.0,lat_cal);
lat_cal=min(60.0,lat_cal);

% 找到距离CALIPSO最近的H8点经纬度
% H8经纬度为0.02度的网格，保留2位小数
num_lon_h8 = round((lon_cal - 80)/0.02)+1;
num_lat_h8 = round((60 - lat_cal)/0.02)+1;
lon_length = 1;
lat_length = 1;

% 读取各波段
N = length(fieldname);
H8bands = NaN(1,N);


for k = 1:N
    H8bands(k) =...
        ncread(h8data_name,fieldname{k},[num_lon_h8,num_lat_h8],[lon_length,lat_length])';
end
end
%% 根据CALIPSO时间找到对应H8时间，H8时间是每十分钟观测一次，因此根据CALIPSO时间找到最接近的H8观测时间
function [H8d, H8t] = cal2h8dt2(DT_CAL,Lat_CAL,Lon_CAL,TimeList)

% CALIPSO H8时间匹配
Lat_H8 = round(100*(60-(0:0.02:120)));
Lon_H8 = round(100*(80+(0:0.02:120)));

Lat_H8_1=round(Lat_CAL/0.02)*2; % calipso点最近的h8点经纬度，得到一个目标H8经纬度
Lon_H8_1=round(Lon_CAL/0.02)*2;
Lon_H8_1=max(8000,Lon_H8_1);
Lon_H8_1=min(20000,Lon_H8_1);
Lat_H8_1=max(-6000,Lat_H8_1);
Lat_H8_1=min(6000,Lat_H8_1);
Lon_H8_1=round(Lon_H8_1);
Lat_H8_1=round(Lat_H8_1);

idx_H8Lon=Lon_H8==Lon_H8_1; % 列
idx_H8Lat=Lat_H8==Lat_H8_1; % 行

HoursH8pixel = hours(TimeList(idx_H8Lat,idx_H8Lon));
% 读取h8t为格式datetime
DT_CAL = DT_CAL - HoursH8pixel;
DT_CAL.Format = 'HHmmss';
DT_CAL1 = char(DT_CAL);
caldt = str2double(string(DT_CAL1(:,3:6)));
H8T = cal2h8dt1(caldt); % 找到对应H8最近的时间，H8为每十分钟一次观测
H8t = [DT_CAL1(:,1:2),H8T];
DT_CAL.Format = 'yyyyMMdd';
H8d = char(DT_CAL);
end
function H8T_str = cal2h8dt1(DT_CAL)
% 找到对应H8最近的时间，H8为每十分钟一次观测
H8T = NaN(length(DT_CAL),1);
H8Tnum = DT_CAL >= 5430 | DT_CAL < 430;
H8T(H8Tnum) = 0;
H8Tnum = DT_CAL >= 430 & DT_CAL < 1430;
H8T(H8Tnum) = 1000;
H8Tnum = DT_CAL >= 1430 & DT_CAL < 2430;
H8T(H8Tnum) = 2000;
H8Tnum = DT_CAL >= 2430 & DT_CAL < 3430;
H8T(H8Tnum) = 3000;
H8Tnum = DT_CAL >= 3430 & DT_CAL < 4430;
H8T(H8Tnum) = 4000;
H8Tnum = DT_CAL >= 4430 & DT_CAL < 5430;
H8T(H8Tnum) = 5000;
H8T_str = num2str(H8T,'%.4d');
end