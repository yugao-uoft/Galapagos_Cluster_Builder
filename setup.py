from genericpath import exists
import json
import os
import shutil
import fileinput
import numpy as np
import sys

sys.path.insert(0, os.getcwd() + '/python_scripts')

from utils import *
from attention import *
from attention_output import *
from intermediate import *
from intermediate_output import *
from comm import *
from gmi import *

# read file system
with open('config.json', 'r') as f:
    json_object = json.load(f)

data_path = 'ibert_data/encoder'
num_encoder_layer=1
hidden_size = json_object['hidden_size']
num_hidden_layers = json_object['num_hidden_layers']
num_attention_heads = json_object['num_attention_heads']
intermediate_size = json_object['intermediate_size']
max_sentence_len = json_object['max_sentence_len']

# compute cluster id of each layer
cluster_id_per_layer = get_cluster_id_per_layer(json_object)
# compute the number of compute kernels in each layer
num_compute_kernel_per_layer = get_num_compute_kernel_per_layer(json_object, cluster_id_per_layer)
# compute number of compute kernels for each cluster
num_compute_kernel_per_cluster = get_num_compute_kernel_per_cluster(json_object, num_compute_kernel_per_layer)
# compute_kern id for each layer
compute_kern_id_per_layer = get_compute_kern_id_per_layer(json_object, num_attention_heads, cluster_id_per_layer, num_compute_kernel_per_layer)
# compute id and name of virtual kernels for each cluster
virtual_kernel_per_cluster, virtual_kernel_id_per_cluster, virtual_kernel_dest_per_cluster, virtual_kernel_src_per_cluster, num_virtual_kernel_per_cluster = get_virtual_kernel_per_cluster(json_object, num_compute_kernel_per_cluster, cluster_id_per_layer, compute_kern_id_per_layer)
# compute number of comm_kernels for each cluster
comm_kernel_per_cluster, comm_kernel_id_per_cluster, comm_kernel_dest_per_cluster, comm_kernel_src_per_cluster, total_num_kernel_per_cluster = get_comm_kernel_per_cluster(json_object, num_compute_kernel_per_cluster, num_virtual_kernel_per_cluster, cluster_id_per_layer, virtual_kernel_id_per_cluster, compute_kern_id_per_layer)
# compute_kern dest for each layer
compute_kern_dest_per_layer = get_compute_kern_dest_per_layer(json_object, num_attention_heads, cluster_id_per_layer, virtual_kernel_id_per_cluster, virtual_kernel_per_cluster, compute_kern_id_per_layer, comm_kernel_id_per_cluster)
# compute_kern src for each layer
compute_kern_src_per_layer = get_compute_kern_src_per_layer(json_object, num_attention_heads, cluster_id_per_layer, virtual_kernel_id_per_cluster, compute_kern_id_per_layer, comm_kernel_id_per_cluster)
# dest cluster for each layer
dest_cluster_per_layer = get_dest_cluster_per_layer(json_object, cluster_id_per_layer)
# layer part 
part_per_layer = get_part_per_layer(json_object)
# cluster part
part_per_cluster = get_part_per_cluster(json_object, cluster_id_per_layer, part_per_layer)


attention_0_cluster_id = cluster_id_per_layer[0]
attention_1_cluster_id = cluster_id_per_layer[1]
attention_2_cluster_id = cluster_id_per_layer[2]
attention_output_0_cluster_id = cluster_id_per_layer[3]
attention_output_1_cluster_id = cluster_id_per_layer[4]
intermediate_0_cluster_id = cluster_id_per_layer[5]
intermediate_output_0_cluster_id = cluster_id_per_layer[6]
intermediate_output_1_cluster_id = cluster_id_per_layer[7]

attention_0_kern_id = compute_kern_id_per_layer[0]
attention_1_kern_id = compute_kern_id_per_layer[1]
attention_2_kern_id = compute_kern_id_per_layer[2]
attention_output_0_kern_id = compute_kern_id_per_layer[3]
attention_output_1_kern_id = compute_kern_id_per_layer[4]
intermediate_0_kern_id = compute_kern_id_per_layer[5]
intermediate_output_0_kern_id = compute_kern_id_per_layer[6]
intermediate_output_1_kern_id = compute_kern_id_per_layer[7]

attention_0_kern_dest = compute_kern_dest_per_layer[0]
attention_1_kern_dest = compute_kern_dest_per_layer[1]
attention_2_kern_dest = compute_kern_dest_per_layer[2]
attention_output_0_kern_dest = compute_kern_dest_per_layer[3]
attention_output_1_kern_dest = compute_kern_dest_per_layer[4]
intermediate_0_kern_dest = compute_kern_dest_per_layer[5]
intermediate_output_0_kern_dest = compute_kern_dest_per_layer[6]
intermediate_output_1_kern_dest = compute_kern_dest_per_layer[7]

attention_0_kern_src = compute_kern_src_per_layer[0]
attention_1_kern_src = compute_kern_src_per_layer[1]
attention_2_kern_src = compute_kern_src_per_layer[2]
attention_output_0_kern_src = compute_kern_src_per_layer[3]
attention_output_1_kern_src = compute_kern_src_per_layer[4]
intermediate_0_kern_src = compute_kern_src_per_layer[5]
intermediate_output_0_kern_src = compute_kern_src_per_layer[6]
intermediate_output_1_kern_src = compute_kern_src_per_layer[7]

# generate script 
cwd = os.getcwd()
cluster = json_object['cluster']
for encoder_layer in range(num_encoder_layer):
    for i in range(len(cluster)):
        num_kernel = num_compute_kernel_per_cluster[i] + len(comm_kernel_id_per_cluster[i]) + 1
        for j in range(num_kernel):
            kern_path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(i) + '/kern_' + str(j)
            if not os.path.exists(kern_path):
                os.makedirs(kern_path)
            bash_file = open(kern_path + '/build.sh', 'w')
            generate_script(bash_file, cwd, kern_path)

bash_file = open('build.sh', 'w')
for encoder_layer in range(num_encoder_layer):
    for i in range(len(cluster)):
        num_kernel = num_compute_kernel_per_cluster[i] + len(comm_kernel_id_per_cluster[i]) + 1
        for j in range(num_kernel):
            kern_path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(i) + '/kern_' + str(j)
            bash_file.write('for((i=0;i<1;i++)); do nohup bash ' + kern_path + '/build.sh' + ' & done' + '\n')
    bash_file.write('wait\n\n')

for encoder_layer in range(num_encoder_layer):
    # build gmi kernels
    for i in range(len(virtual_kernel_per_cluster)):
        build_gmi_kernel(data_path, part_per_cluster[i], encoder_layer, i, virtual_kernel_per_cluster[i], virtual_kernel_id_per_cluster[i], virtual_kernel_dest_per_cluster[i], virtual_kernel_src_per_cluster[i])

for encoder_layer in range(num_encoder_layer):
    # build comm kernels
    for i in range(len(comm_kernel_per_cluster)):
        for j in range(len(comm_kernel_per_cluster[i])):
            build_comm_kernel(data_path, part_per_cluster[i], encoder_layer, i, comm_kernel_per_cluster[i][j], comm_kernel_id_per_cluster[i][j], comm_kernel_dest_per_cluster[i][j], comm_kernel_src_per_cluster[i][j])

for encoder_layer in range(num_encoder_layer):
    # build attention_0
    if attention_0_cluster_id != attention_1_cluster_id: 
        out_cluster=True
    else: 
        out_cluster=False
    attention_0(data_path, json_object['attention_0'], attention_0_kern_id, attention_0_kern_dest, dest_cluster_per_layer[0], hidden_size, num_attention_heads, max_sentence_len, encoder_layer, attention_0_cluster_id, out_cluster)
    # build attention_1
    if attention_1_cluster_id != attention_2_cluster_id: 
        out_cluster=True
    else: 
        out_cluster=False
    attention_1(data_path, json_object['attention_1'], attention_1_kern_id, attention_1_kern_dest, attention_1_kern_src, dest_cluster_per_layer[1], hidden_size, num_attention_heads, max_sentence_len, encoder_layer, attention_1_cluster_id, out_cluster)
    # build attention_2
    if attention_2_cluster_id != attention_output_0_cluster_id: 
        out_cluster=True
    else: 
        out_cluster=False
    partition = json_object['attention_output_0']['partition']
    attention_2(data_path, json_object['attention_2'], attention_2_kern_id, attention_2_kern_dest, attention_2_kern_src, dest_cluster_per_layer[2], hidden_size, num_attention_heads, max_sentence_len, encoder_layer, attention_2_cluster_id, partition, out_cluster)
    # build attention_output_0
    if attention_output_0_cluster_id != attention_output_1_cluster_id: 
        out_cluster=True
    else: 
        out_cluster=False
    attention_output_0(data_path, json_object['attention_output_0'], attention_output_0_kern_id, attention_output_0_kern_dest, attention_output_0_kern_src, dest_cluster_per_layer[3], hidden_size, num_attention_heads, max_sentence_len, encoder_layer, attention_output_0_cluster_id, out_cluster)
    # build attention_output_1
    if attention_output_1_cluster_id != intermediate_0_cluster_id: 
        out_cluster=True
    else: 
        out_cluster=False
    attention_output_1(data_path, json_object['attention_output_1'], attention_output_1_kern_id, attention_output_1_kern_dest, attention_output_1_kern_src, dest_cluster_per_layer[4], hidden_size, num_attention_heads, max_sentence_len, encoder_layer, attention_output_1_cluster_id, out_cluster)
    # # build intermediate_0
    if intermediate_0_cluster_id != intermediate_output_0_cluster_id: 
        out_cluster=True
    else: 
        out_cluster=False
    intermediate_0(data_path, json_object['intermediate_0'], intermediate_0_kern_id, intermediate_0_kern_dest, dest_cluster_per_layer[5], hidden_size, intermediate_size, encoder_layer, intermediate_0_cluster_id, out_cluster)
    # # intermediate_output_0
    if intermediate_output_0_cluster_id != intermediate_output_1_cluster_id: 
        out_cluster=True
    else: 
        out_cluster=False
    intermediate_output_0(data_path, json_object['intermediate_output_0'], intermediate_output_0_kern_id, intermediate_output_0_kern_dest, dest_cluster_per_layer[6], hidden_size, intermediate_size, encoder_layer, intermediate_output_0_cluster_id, out_cluster)
    # intermediate_output_1
    intermediate_output_1(data_path, json_object['intermediate_output_1'], intermediate_output_1_kern_id, intermediate_output_1_kern_dest, intermediate_output_1_kern_src, dest_cluster_per_layer[7], hidden_size, intermediate_size, encoder_layer, intermediate_output_1_cluster_id)





