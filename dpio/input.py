import os
import json
import configparser

def read_from_path(file_path):
    # 将路径切分为root与file的形式
    with open(file_path,"r") as fp:
        json_dict = json.load()
    return json_dict

def read_from_folder(folder_path):
    # 批量读取该路径下的所有文件
    return 1

def read_config_file(config_file_path):
    config = configparser.ConfigParser()
    config.read(config_file_path,encoding = 'UTF8')

    data_root = config.get('Paths','data_root')

    feature_file_path_rela = config.get('Paths','feature_file_path')
    location_file_path_rela = config.get('Paths','location_file_path')
    vision_file_path_rela = config.get('Paths','vision_file_path')

    feature_file_path = os.path.join(data_root,feature_file_path_rela)
    location_file_path = os.path.join(data_root,location_file_path_rela)
    vision_file_path = os.path.join(data_root,vision_file_path_rela)

    return [feature_file_path,location_file_path,vision_file_path]

def read_from_geojson():
    return -1