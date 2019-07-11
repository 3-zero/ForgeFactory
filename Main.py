from Simulator.Simulator import *
from copy import deepcopy
from datetime import datetime
import json
import sys
from Predictor.Predictor import *

def dict_to_time(obj):
    return int((datetime(obj['year'], obj['month'], obj['day'], obj['hour'], obj['minute'],
             obj['second'], obj['millisecond'] * 1000) - simul_start_time).total_seconds()/60)

def read(file):
    try:
        with open(file) as fs:
            js = json.load(fs)
            return js
    except Exception as e:
        print("Error: read json", file)
        print(e.message)
        sys.exit(1)

def read_data(file):
    path='./data/190707_test_data/'
    data = read(path+file+'.json')
    if file == 'product':
        for d in data:
            d['properties']['deadline'] = dict_to_time(d['properties']['deadline'])
            d['properties']['order_date'] = dict_to_time(d['properties']['order_date'])
    elif file == 'job':
        for d in data:
            d['properties']['deadline'] = dict_to_time(d['properties']['deadline'])
            d['properties']['order_date'] = dict_to_time(d['properties']['order_date'])
            d['properties']['current_equip'] = None
            d['properties']['last_process'] = None
            d['properties']['last_process_end_time'] = None
            d['properties']['instruction_list'] = []
            d['properties']['last_heating_furnace'] = None
            d['properties']['next_instruction'] = 0
            d['properties']['product'] = None
            d['properties']['ingot'] = None
            product_id_list = d['properties']['product_id_list']
            for product_id in product_id_list:
                for product in product_data:
                    #print(product['id'], product_id)
                    if product['id'] == product_id:
                        instruction_list = product['properties']['instruction_id_list']
                        if d['properties']['product'] == None:
                            d['properties']['product'] = product['properties']
                        break
                for i in range(len(instruction_list)):
                    inst = instruction_list[i].split('_')
                    if inst[0] == 'heating':
                        instruction_list[i] = 'heating'
                    elif inst[0] == 'forging':
                        instruction_list[i] = 'forging'
                    elif inst[0] == 'cutting':
                        instruction_list[i] = 'cutting'
                    elif inst[0] == 'heat':
                        instruction_list[i] = 'treating'
                        #instruction_list[i] = 'heating'

                d['properties']['instruction_list'].append(instruction_list)
            ingot_id = d['properties']['ingot_id_list'][0]
            if len(d['properties']['instruction_list']) == 0:
                print('Error : instruction list is empty!')
                exit(1)
            for ingot in ingot_data:
                if ingot['id'] == ingot_id:
                    d['properties']['ingot'] = ingot['properties']
                    break
    elif file == 'ingot':
        None
    return data

#warnings.filterwarnings(action='ignore')
#from absl import logging
#logging._warn_preinit_stderr = 0

simul_start_time = datetime(2013, 2, 26, 10)

"""
json 입력받을 때 time이 dictionary형식으로 저장되어있는데,
여기에 기준 simul_start_time을 뺀 minute 값으로 바꿔줘야함.
이후의 모든 time표현값들이 simul_start_time 기준 분 값으로 계산될 것임
-완-
"""
product_data = read_data('product')
ingot_data = read_data('ingot')
job_data = read_data('job')

#print(product_data), print(ingot_data), print(job_data)

predictor = Predictor()

simulator = Simulator(predictor, deepcopy(product_data), deepcopy(ingot_data), deepcopy(job_data), 10, 2, 2, 5)
simulator.run()