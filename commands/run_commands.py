import os
import json

import requests

from communication import send_requests

with open(os.path.join(os.path.dirname(__file__), '..', 'config', 'json', 'data_nodes.json')) as data_nodes_file:
    data_nodes_data_json = json.load(data_nodes_file)

with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'files_info.json')) as files_info_file:
    files_info_file_json = json.load(files_info_file)
    
with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'files_info.json')) as file:
    file_info = json.loads(file.read())


# TODO: check if **kwargs may be used in recognize_command()
# TODO: wrap global vars in class
# files_info_file = open(os.path.join(os.path.dirname(__file__), 'data', 'files_info.json'))
# files_info_file_json = json.load(files_info_file)

class SomeClass:
    N = len(data_nodes_data_json['data_nodes'])
    counter = 0
    list_of_min = []
    list_of_max = []


class Command:
    json_data_obj = {}

    @staticmethod
    def make_file(content):
        Command.json_data_obj = content['make_file']
        send_requests.make_file(Command.json_data_obj['destination_file'])
        file_info = {
            'files': [
                {

                    'file_name': Command.json_data_obj['destination_file'],
                    'lock': False,
                    'last_fragment_block_size': 1024,
                    'key_ranges': None,
                    'file_fragments': []
                }
            ]
        }
        # TODO: initialize and append to list at the same time
        # file_info['files'] = []
        # file_info['files'].append(
        #     {
        #         'file_name': json_data_obj['destination_file'],
        #         'lock': False,
        #         'last_fragment_block_size': 1024,
        #         'key_ranges': None,
        #         'file_fragments': []
        #     }
        # )
        with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'files_info.json'), 'w+') as file:
            json.dump(file_info, file, indent=4)

        Command.json_data_obj.clear()
        Command.json_data_obj['distribution'] = data_nodes_data_json['distribution']

    @staticmethod
    def map_reduce(content):
        Command.json_data_obj = content['map_reduce']

        send_requests.map(content['map_reduce'])
        send_requests.reduce(content['map_reduce'])

    # TODO: refactor append command
    @staticmethod
    def append(content):
        Command.json_data_obj = content['append']
        file_name = Command.json_data_obj['file_name']
        Command.json_data_obj = {}   
        for item in files_info_file_json['files']:
            if item['file_name'] == file_name:
                if not item['file_fragments']:
                    Command.json_data_obj['data_node_ip'] = 'http://' + data_nodes_data_json['data_nodes'][0][
                        'data_node_address']
                else:
                    id = 1

                    for key, value in (item['file_fragments'][-1]).items():
                        id = key

                    for i in data_nodes_data_json['data_nodes']:
                        if i['data_node_id'] == int(id):
                            prev_ind = data_nodes_data_json['data_nodes'].index(i)
                            if prev_ind + 1 == len(data_nodes_data_json['data_nodes']):
                                Command.json_data_obj['data_node_ip'] = 'http://' + \
                                                                        data_nodes_data_json['data_nodes'][0][
                                                                            'data_node_address']
                            else:
                                Command.json_data_obj['data_node_ip'] = 'http://' + \
                                                                        data_nodes_data_json['data_nodes'][
                                                                            prev_ind + 1][
                                                                            'data_node_address']

    # TODO: check and refactor
    @staticmethod
    def refresh_table(content):
        Command.json_data_obj = content['refresh_table']
        

        for item in file_info['files']:
            if item['file_name'] == Command.json_data_obj['file_name']:
                id = ''
                for i in data_nodes_data_json['data_nodes']:

                    if i['data_node_address'] == Command.json_data_obj['ip'].split('//')[1]:
                        id = i['data_node_id']
                item['file_fragments'].append(
                    {
                        id: Command.json_data_obj['segment_name']
                    }
                )
        with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'files_info.json'), 'w')as file:
            json.dump(file_info, file, indent=4)

    @staticmethod
    def hash(content):
        Command.json_data_obj = content['hash']
        SomeClass.list_of_max.append(Command.json_data_obj['list_keys'][0])
        SomeClass.list_of_min.append(Command.json_data_obj['list_keys'][1])

        # TODO: implement through class
        SomeClass.counter += 1

        if SomeClass.counter == SomeClass.N:
            max_hash = max(SomeClass.list_of_max)
            min_hash = min(SomeClass.list_of_min)
            step = (max_hash - min_hash) / SomeClass.N
            context = {
                'shuffle': {
                    'nodes_keys': [],
                    'max_hash': max_hash,
                    'file_name': Command.json_data_obj['file_name']
                }
            }
            mid_hash = min_hash
            SomeClass.counter = 0
            for i in data_nodes_data_json['data_nodes']:
                SomeClass.counter += 1
                if SomeClass.counter == SomeClass.N:
                    end_hash = max_hash
                else:
                    end_hash = mid_hash + step
                context['shuffle']['nodes_keys'].append({
                    'data_node_ip': i['data_node_address'],
                    'hash_keys_range': [mid_hash, end_hash]
                })
                mid_hash += step

            

            for i in files_info_file_json['files']:
                arr = Command.json_data_obj['file_name'].split('.')
                file_name = arr[0].split('_')[0] + '.' + arr[-1]
                if file_name == i['file_name'].split(os.sep)[-1]:
                    print(context['shuffle']['nodes_keys'])
                    i['key_ranges'] = context['shuffle']['nodes_keys']

            with open(os.path.join(os.path.dirname(__file__), '..', 'data', 'files_info.json'), 'w')as file:
                json.dump(files_info_file_json, file, indent=4)

            for i in data_nodes_data_json['data_nodes']:
                url = 'http://' + i['data_node_address']
                response = requests.post(url, data=json.dumps(context))
            SomeClass.counter = 0

    @staticmethod
    def get_file(content):
        Command.json_data_obj = content['get_file']
        file_name = Command.json_data_obj['file_name']
        context = {'data_nodes_ip': []}
        for i in data_nodes_data_json['data_nodes']:
            url = 'http://' + i['data_node_address']
            context['data_nodes_ip'].append(url)
        Command.json_data_obj = context

    @staticmethod
    def get_result_of_key(content):
        Command.json_data_obj = content['get_result_of_key']
        key = Command.json_data_obj['key']
        file_name = Command.json_data_obj['file_name']
        context = {}
        
        Command.json_data_obj.clear()

        for item in files_info_file_json['files']:
            if item['file_name'] == file_name:
                Command.json_data_obj['key_ranges'] = item['key_ranges']
        url = 'http://' + data_nodes_data_json['data_nodes'][0]['data_node_address']
        context['get_hash_of_key'] = key
        response = requests.post(url, data=json.dumps(context))
        Command.json_data_obj['hash_key'] = response.json()

    @staticmethod
    def recognize_command(content):
        if 'make_file' in content:
            Command.make_file(content)

        elif 'map_reduce' in content:
            Command.map_reduce(content)

        elif 'append' in content:
            Command.append(content)

        elif 'refresh_table' in content:
            Command.refresh_table(content)

        elif 'hash' in content:
            Command.hash(content)

        elif 'clear_data' in content:
            send_requests.clear_data(content)

        elif 'get_file' in content:
            Command.get_file(content)

        elif 'get_result_of_key' in content:
            Command.get_result_of_key(content)

        return Command.json_data_obj