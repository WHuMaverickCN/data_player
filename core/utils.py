import re
import os
import json
from datetime import datetime
from http.server import SimpleHTTPRequestHandler
import urllib.parse

class Period:
    def __init__(self,start_time,end_time):
        self.start_time = start_time
        self.end_time = end_time

class DataFilter:
    def __init__(self,period):
        self.period = period

    def update_time_stamp(self,start_time,end_time):
        self.start_time = start_time
        self.end_time = end_time

    def search_vec_data(self,target_path,period):
        target_folder = ['VecPE','TrajJsonData_noH']
        target_path_dict = {}
        tsp = TimeStampProcessor()
        if os.path.isdir(target_path):
            __list = os.listdir(target_path)
            try:
                vehicle_SN = __list[0]
                target_path = os.path.join(target_path,vehicle_SN)
                __inner_list = os.listdir(target_path)
                for item in __inner_list:
                    if item in target_folder:
                        _vec_slice_path = os.path.join(target_path,item)
                        _target_list = os.listdir(_vec_slice_path)
                        if 'Traj' in item:
                            _file_named_timestamp_dict = {}
                            for _file_name in _target_list:
                                ts = tsp.get_vec_data_timestamp(_file_name,mode = 'traj')
                                _file_named_timestamp_dict[_file_name] = ts
                                target_path_dict[item] = _file_named_timestamp_dict
                        elif 'Vec' in item:
                            _file_named_timestamp_dict = {}
                            for _file_name in _target_list:
                                ts = tsp.get_vec_data_timestamp(_file_name,mode = 'vec')
                                _file_named_timestamp_dict[_file_name] = ts
                                target_path_dict[item] = _file_named_timestamp_dict
            except IndexError:
                return IndexError
        elif os.path.isfile(target_path):
            return -1
        output_dict = {}
        for _key,_unsorted_dict in target_path_dict.items():
            for __file_name,__timestamp in _unsorted_dict.items():
                 _unsorted_dict[__file_name]= tsp.check_timestamp_format(__timestamp)
        
        select_dict = {}
        for _key,_unsorted_dict in target_path_dict.items():
            select_dict[_key] = self.get_files_in_time_range(_unsorted_dict,period)
        return select_dict
    
    def search_loc_data(self,path,period):
        return 1
    
    def search_vis_data(self,path,period):
        return 1
    
    def binary_search(self, timestamps, period):
        # 二分查找开始时间的索引
        low = 0
        high = len(timestamps) - 1
        while low <= high:
            mid = (low + high) // 2
            if float(timestamps[mid][1]) < float(period.start_time):
                low = mid + 1
            elif float(timestamps[mid][1]) > float(period.end_time):
                high = mid - 1
            else:
                print("return mid:",timestamps[mid][1],period)
                return mid
        return -1
    def get_files_in_time_range(self,timestamps_dict, period):
        timestamps = sorted(timestamps_dict.items(), key=lambda x: x[1])  # 按时间戳排序
        index = self.binary_search(timestamps, period)
        if index == -1:
            return []
        files_in_range = []
        while index >= 0 and timestamps[index][1] >= period.start_time:
            files_in_range.append(timestamps[index])
            index -= 1
        while index >= 0 and timestamps[index][1] <= period.end_time:
            if timestamps[index] not in files_in_range:
                files_in_range.append(timestamps[index])
            index += 1
        selected_files = dict(sorted(files_in_range, key=lambda x: x[1]))
        return selected_files

class TimeStampProcessor:
    def unify_timestamp(self,input):
        if input is str:
            print("str")
        else:
            print(type(input))
        return 1
    
    def check_period(self,period):
        period.start_time = self.check_timestamp_format(period.start_time)
        period.end_time = self.check_timestamp_format(period.end_time)
        return period
    
    def check_timestamp_format(self,temporal_timestamp):
        if type(temporal_timestamp) != str:
            temporal_timestamp = temporal_timestamp.__str__()
        l = len(temporal_timestamp)
        timestamp_pattern = r'^\d{10}$'
        timestamp_pattern_16 = r'^\d{16}$'

        if l == 10 and re.match(timestamp_pattern, temporal_timestamp):
            return temporal_timestamp
        elif l==16 and re.match(timestamp_pattern_16, temporal_timestamp):
            return temporal_timestamp[:10]
            
    def trans_timestamp_to_general_format(self,temporal_timestamp):
        if type(temporal_timestamp) != str:
            return TypeError
        data_obj = datetime.fromtimestamp(int(temporal_timestamp))
        return data_obj.strftime("%Y-%m-%d %H:%M:%S")

    def calculate_time_interval(self,period):
        # 将时间戳转换为 datetime 对象
        if period.start_time=='' or period.end_time=='':
            return ''
        dt1 = datetime.fromtimestamp(float(period.start_time))
        dt2 = datetime.fromtimestamp(float(period.end_time))
        
        # 计算时间间隔
        delta = dt2 - dt1
        
        # 提取时分秒
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        hours += delta.days*24
        # 格式化输出
        time_interval = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return time_interval
    def get_vec_data_timestamp(self,file_name,mode='vec'):
        # return file_name
        if mode == 'vec':
            return file_name.split('_')[0]
        if mode == 'traj':
            return file_name.split('_')[1].split('.')[0]

    def get_raw_data_package_timestamp(self,file_name):
        # extract timestamp from the file name of loc \ vision data
        name,suffix = file_name.split('.')
        items = name.split('_')
        try:
            date = items[2]
            time = items[3]
            time_str = date + ' ' + time
            time_format = "%Y-%m-%d %H-%M-%S"
            local_time = datetime.strptime(time_str, time_format)
            beijing_timestamp = local_time.timestamp()
            print("utc+8:", beijing_timestamp)
        except IndexError:
            return None
        
    # 创建自定义的请求处理程序，用于返回 GeoJSON 文件
class DP_GeoJSONHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        # 解析请求路径
        parsed_path = urllib.parse.urlparse(self.path)
        file_path = urllib.parse.unquote(parsed_path.path)

        # 获取 GeoJSON 文件路径
        geojson_file = file_path[1:]  # 移除 URL 中的斜杠
        
        # 检查文件是否存在
        if not os.path.exists(geojson_file):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'File Not Found')
            return

        # 设置响应头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # 允许所有源
        self.end_headers()

        # 读取并发送 GeoJSON 文件内容
        with open(geojson_file, 'rb') as f:
            self.wfile.write(f.read())
    # 创建本地 HTTP 服务器并运行

class DataPackage:
    def __init__(self,feature,vision,location,ground_truth):
        self.feature = feature
        self.vision = vision
        self.location = location
        self.ground_truth = ground_truth

    def write_to_folder(self,path):
        target_feature_path = os.path.join(path,'features')
        with open(target_feature_path,'w') as fo:
            json.dumps(self.feature,fo,intent=2)

        
        