import pandas as pd
import json

from ipycytoscape import *
import ipywidgets as widgets
from ipywidgets import GridspecLayout
from IPython.display import clear_output
import os


import requests


def get_entries(path_model_th_cls):
    # GitHub repository information
    owner = 'SDM-TIB'
    repo = 'CoyPU_demo_LDM'
    # GitHub API URL to list the contents of the directory
    url = f'https://api.github.com/repos/{owner}/{repo}/contents/{path_model_th_cls}'

    # Send the request to GitHub API
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        contents = response.json()

        # Get the names of all entries in the directory
        entries = [entry['name'] for entry in contents]
        return entries
    return []

def select_cluster(country, path_model_th_cls, content):
    # entries = os.listdir(path_model_th_cls)
    entries = get_entries(path_model_th_cls)
    country_entries = []
    for name in entries:
        cls = pd.read_csv(content+path_model_th_cls + '/' + name, delimiter="\t", header=None)
        cls.columns = ['Country', 'Indicator', 'category', 'Cost']
        if country in cls.Country.to_list():
            country_entries.append(name)
    return country_entries


def adding_prediction(name, cls, prediction):
    c = name.split('-')[1][:-4]
    ix = prediction.index[prediction['col2'] == c].tolist()
    if len(ix)==0:
        return cls
    ix = ix[0]
    for ind in prediction.index[ix+1:]:
        if 'Cluster' == prediction['col1'][ind]:
            break
        cls.loc[len(cls.index)] = [prediction['col1'][ind], prediction['category'][ind], 'Predicted:'+prediction['col2'][ind],
                                   prediction['weight'][ind]]
    return cls

def load_cluster(path_model_th_cls, name, prediction, replacement_map, content):
    cls = pd.read_csv(content + path_model_th_cls + '/' + name, delimiter="\t", header=None)
    cls.columns = ['Country', 'Indicator', 'category', 'Cost']
    cls = adding_prediction(name, cls, prediction)
    cls['Country'].replace(replacement_map, inplace=True)
    return cls

def create_json_to_cytoscape(path_model_th_cls, name, prediction, replacement_map, content): # entity_type
    rdf_graph = load_cluster(path_model_th_cls, name, prediction, replacement_map, content)
    graph_json = dict()
    graph_json['nodes'] = []
    graph_json['edges'] = []
    drug_id = dict()
    id_x = 0
    for i in range(rdf_graph.shape[0]):
        subj = rdf_graph.iloc[i]['Country']
        obj = rdf_graph.iloc[i]['Indicator']
        prop = rdf_graph.iloc[i]['category']
        edge = dict()
        edge['data'] = dict()

        if subj in drug_id.keys():
            edge['data']['id'] = id_x
            edge['data']['source'] = drug_id[subj]
            edge['data']['Label'] = prop
            id_x += 1
        else:
            node = dict()
            node['data'] = dict()
            drug_id[subj] = id_x
            node['data']['id'] = id_x
            node['data']['name'] = subj
            node['data']['type'] = 'Country' # entity_type[subj]
            edge['data']['id'] = id_x + 1
            edge['data']['source'] = id_x
            edge['data']['Label'] = prop
            graph_json['nodes'].append(node)
            id_x += 2
        if obj in drug_id.keys():
            edge['data']['target'] = drug_id[obj]
        else:
            node = dict()
            node['data'] = dict()
            drug_id[obj] = id_x
            node['data']['id'] = id_x
            node['data']['name'] = obj
            node['data']['type'] = 'Indicator' # entity_type[obj]
            edge['data']['target'] = id_x
            graph_json['nodes'].append(node)
            id_x += 1
#             if obj == k:
#                 node['classes'] = 'red'  # Single class

        graph_json['edges'].append(edge)

    return graph_json

def create_graph_cytoscape(path_model_th_cls, name, prediction, replacement_map, content):
    middle_vertex = create_json_to_cytoscape(path_model_th_cls, name, prediction, replacement_map, content)
    # load a style dictionary
#     with open(content + 'Visualizing_Cluster/styles_prediction.json') as fi:
#         s = json.load(fi)
    s = download_json(content + 'Visualizing_Cluster/styles_prediction.json')
    # Create the cytoscape graph widget
    cytoscapeobj = CytoscapeWidget()
    cytoscapeobj.graph.add_graph_from_json(middle_vertex, directed=True, multiple_edges=True)  # , directed=True, input_data['elements']
    
    cytoscapeobj.set_style(s)
    cytoscapeobj.set_layout(name='breadthfirst', animate=True, nodeSpacing = 1)  # concentric,  breadthfirst, fcose, dagre, grid
    return cytoscapeobj

def download_json(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to download JSON file: {response.status_code}")


