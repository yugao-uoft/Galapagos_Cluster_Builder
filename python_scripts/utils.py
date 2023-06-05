import os
import fileinput
import shutil
import numpy as np

def get_part_per_layer(json_object):
    return  [json_object['attention_0']['part'], json_object['attention_1']['part'], json_object['attention_2']['part'], json_object['attention_output_0']['part'], json_object['attention_output_1']['part'], json_object['intermediate_0']['part'], json_object['intermediate_output_0']['part'],  json_object['intermediate_output_1']['part']]

def get_part_per_cluster(json_object, cluster_id_per_layer, part_per_layer):
    cluster = json_object['cluster']
    part_per_cluster = []
    for i in range(len(cluster)):
        layer = 0
        for j in range(len(cluster_id_per_layer)):
            if cluster_id_per_layer[j] == i:
                layer = j
        part_per_cluster.append(part_per_layer[layer])
    return part_per_cluster

def get_cluster_id_per_layer(json_object):
    # extract info from json
    cluster = json_object['cluster']
    # get the cluster id and within cluster location for each layer
    for i in range(len(cluster)):
        for j in range(len(cluster[i])):
            if cluster[i][j] == 'attention_0':
                attention_0_cluster_id = i
                attention_0_in_cluster_id = j
            elif cluster[i][j] == 'attention_1':
                attention_1_cluster_id = i
                attention_1_in_cluster_id = j
            elif cluster[i][j] == 'attention_2':
                attention_2_cluster_id = i
                attention_2_in_cluster_id = j
            elif cluster[i][j] == 'attention_output_0':
                attention_output_0_cluster_id = i
                attention_output_0_in_cluster_id = j
            elif cluster[i][j] == 'attention_output_1':
                attention_output_1_cluster_id = i
                attention_output_1_in_cluster_id = j
            elif cluster[i][j] == 'intermediate_0':
                intermediate_0_cluster_id = i
                intermediate_0_in_cluster_id = j
            elif cluster[i][j] == 'intermediate_output_0':
                intermediate_output_0_cluster_id = i
                intermediate_output_0_in_cluster_id = j
            elif cluster[i][j] == 'intermediate_output_1':
                intermediate_output_1_cluster_id = i
                intermediate_output_1_in_cluster_id = j
    return [attention_0_cluster_id, attention_1_cluster_id, attention_2_cluster_id, attention_output_0_cluster_id, attention_output_1_cluster_id, intermediate_0_cluster_id, intermediate_output_0_cluster_id, intermediate_output_1_cluster_id]


def get_num_compute_kernel_per_layer(json_object, cluster_id_per_layer):
    # extract info from json
    cluster = json_object['cluster']
    num_kernel_attention_0 = json_object['attention_0']['partition'] * 3
    num_kernel_attention_1 = 12
    num_kernel_attention_2 = 12
    num_kernel_attention_output_0 = json_object['attention_output_0']['partition']
    num_kernel_attention_output_1 = 1
    num_kernel_intermediate_0 = json_object['intermediate_0']['partition']
    num_kernel_intermediate_output_0 = json_object['intermediate_output_0']['partition']
    num_kernel_intermediate_output_1 = 1
    # add one extra kernel for sending bypass
    attention_0_cluster_id = cluster_id_per_layer[0]
    attention_output_1_cluster_id = cluster_id_per_layer[4]
    if attention_0_cluster_id != attention_output_1_cluster_id: 
        num_kernel_attention_0 += 1
    # add one extra kernel for sending bypass
    intermediate_0_cluster_id = cluster_id_per_layer[5]
    intermediate_output_1_cluster_id = cluster_id_per_layer[7]
    if intermediate_0_cluster_id != intermediate_output_1_cluster_id: 
        num_kernel_intermediate_0 += 1
    return [num_kernel_attention_0, num_kernel_attention_1, num_kernel_attention_2, num_kernel_attention_output_0, num_kernel_attention_output_1, num_kernel_intermediate_0, num_kernel_intermediate_output_0, num_kernel_intermediate_output_1]

def get_compute_kern_id_per_layer(json_object, num_attention_heads, cluster_id_per_layer, num_compute_kernel_per_layer):
    attention_0_cluster_id = cluster_id_per_layer[0]
    attention_1_cluster_id = cluster_id_per_layer[1]
    attention_2_cluster_id = cluster_id_per_layer[2]
    attention_output_0_cluster_id = cluster_id_per_layer[3]
    attention_output_1_cluster_id = cluster_id_per_layer[4]
    intermediate_0_cluster_id = cluster_id_per_layer[5]
    intermediate_output_0_cluster_id = cluster_id_per_layer[6]
    intermediate_output_1_cluster_id = cluster_id_per_layer[7]
    num_kernel_attention_0 = num_compute_kernel_per_layer[0]
    num_kernel_attention_1 = num_compute_kernel_per_layer[1]
    num_kernel_attention_2 = num_compute_kernel_per_layer[2]
    num_kernel_attention_output_0 = num_compute_kernel_per_layer[3]
    num_kernel_attention_output_1 = num_compute_kernel_per_layer[4]
    num_kernel_intermediate_0 = num_compute_kernel_per_layer[5]
    # compute kern id for attention_0
    attention_0_kern_id = [0 for _ in range(num_kernel_attention_0)]
    for i in range(num_kernel_attention_0):
        attention_0_kern_id[i] = i+1
    # compute kern_id for attention_1
    attention_1_kern_id = [0 for _ in range(num_attention_heads)]
    if attention_0_cluster_id != attention_1_cluster_id:
        for i in range(num_attention_heads):
            attention_1_kern_id[i] = i + 1
    else:
        for i in range(num_attention_heads):
            attention_1_kern_id[i] = num_kernel_attention_0 + i + 1
    # compute kern id for attention 2
    attention_2_kern_id = [0 for _ in range(num_attention_heads)]
    if attention_1_cluster_id != attention_2_cluster_id:
        for i in range(num_attention_heads):
            attention_2_kern_id[i] = i + 1
    else:
        for i in range(num_attention_heads):
            attention_2_kern_id[i] =  attention_1_kern_id[num_attention_heads-1] + i + 1
    # compute kern id for attention output 0
    attention_output_0_kern_id = [0 for _ in range(json_object['attention_output_0']['partition'])]
    if attention_2_cluster_id != attention_output_0_cluster_id:
        for i in range(json_object['attention_output_0']['partition']):
            attention_output_0_kern_id[i] = i + 1
    else:
        for i in range(json_object['attention_output_0']['partition']):
            attention_output_0_kern_id[i] =  attention_2_kern_id[num_attention_heads-1] + i + 1
    # compute kern id for attention output 1
    attention_output_1_kern_id = []
    if attention_output_0_cluster_id != attention_output_1_cluster_id:
        attention_output_1_kern_id.append(1)
    else:
        attention_output_1_kern_id.append(attention_output_0_kern_id[json_object['attention_output_0']['partition']-1] + 1)
    # compute kern id for intermediate_0
    intermediate_0_kern_id = [0 for _ in range(num_kernel_intermediate_0)]
    if attention_output_1_cluster_id != intermediate_0_cluster_id:
        for i in range(num_kernel_intermediate_0):
            intermediate_0_kern_id[i] = i + 1
    else:
        for i in range(num_kernel_intermediate_0):
            intermediate_0_kern_id[i] =  attention_output_1_kern_id[0] + i + 1
    # compute kern id for intermediate_output_0
    intermediate_output_0_kern_id = [0 for _ in range(json_object['intermediate_output_0']['partition'])]
    if intermediate_0_cluster_id != intermediate_output_0_cluster_id:
        for i in range(json_object['intermediate_output_0']['partition']):
            intermediate_output_0_kern_id[i] = i + 1
    else:
        for i in range(json_object['intermediate_output_0']['partition']):
            if intermediate_0_cluster_id != intermediate_output_1_cluster_id:
                intermediate_output_0_kern_id[i] = intermediate_0_kern_id[json_object['intermediate_0']['partition']-1] + i + 2
            else:
                intermediate_output_0_kern_id[i] = intermediate_0_kern_id[json_object['intermediate_0']['partition']-1] + i + 1
    # compute kern id for intermediate_output_1
    intermediate_output_1_kern_id = []
    if intermediate_output_0_cluster_id != intermediate_output_1_cluster_id:
        intermediate_output_1_kern_id.append(1)
    else:
        intermediate_output_1_kern_id.append(intermediate_output_0_kern_id[json_object['intermediate_output_0']['partition']-1] + 1)
    return [attention_0_kern_id, attention_1_kern_id, attention_2_kern_id, attention_output_0_kern_id, attention_output_1_kern_id, intermediate_0_kern_id,intermediate_output_0_kern_id,intermediate_output_1_kern_id]



def get_num_compute_kernel_per_cluster(json_object, num_compute_kernel_per_layer):
    cluster = json_object['cluster']
    # compute number of kernels for each cluster, only compute kernels
    num_kernel_per_cluster = [0 for _ in range(len(cluster))]
    for i in range(len(cluster)):
        temp = 0
        for j in range(len(cluster[i])):
            if cluster[i][j] == 'attention_0':
                temp += num_compute_kernel_per_layer[0]
            elif cluster[i][j] == 'attention_1':
                temp += num_compute_kernel_per_layer[1]
            elif cluster[i][j] == 'attention_2':
                temp += num_compute_kernel_per_layer[2]
            elif cluster[i][j] == 'attention_output_0':
                temp += num_compute_kernel_per_layer[3]
            elif cluster[i][j] == 'attention_output_1':
                temp += num_compute_kernel_per_layer[4]
            elif cluster[i][j] == 'intermediate_0':
                temp += num_compute_kernel_per_layer[5]
            elif cluster[i][j] == 'intermediate_output_0':
                temp += num_compute_kernel_per_layer[6]
            elif cluster[i][j] == 'intermediate_output_1':
                temp += num_compute_kernel_per_layer[7]
        num_kernel_per_cluster[i] = temp
    return num_kernel_per_cluster

def get_virtual_kernel_per_cluster(json_object, num_kernel_per_cluster, cluster_id_per_layer, compute_kern_id_per_layer):
    cluster = json_object['cluster']
    virtual_kernel_id_per_cluster = [[] for _ in range(len(cluster))]
    virtual_kernel_dest_per_cluster = [[] for _ in range(len(cluster))]
    virtual_kernel_src_per_cluster = [[] for _ in range(len(cluster))]
    virtual_kernel_per_cluster = [[] for _ in range(len(cluster))]
    num_virtual_kernel_per_cluster = [0 for _ in range(len(cluster))]
    # 
    attention_0_cluster_id = cluster_id_per_layer[0]
    attention_1_cluster_id = cluster_id_per_layer[1]
    attention_2_cluster_id = cluster_id_per_layer[2]
    attention_output_0_cluster_id = cluster_id_per_layer[3]
    attention_output_1_cluster_id = cluster_id_per_layer[4]
    intermediate_0_cluster_id = cluster_id_per_layer[5]
    intermediate_output_0_cluster_id = cluster_id_per_layer[6]
    intermediate_output_1_cluster_id = cluster_id_per_layer[7]
    # attention_0
    virtual_kernel_per_cluster[attention_0_cluster_id].append(['broadcast'])
    virtual_kernel_id_per_cluster[attention_0_cluster_id].append(num_kernel_per_cluster[attention_0_cluster_id]+1)
    num_virtual_kernel_per_cluster[attention_0_cluster_id] += 1
    # dest
    temp = []
    for i in range(len(compute_kern_id_per_layer[0])):
        temp.append(compute_kern_id_per_layer[0][i])
    if attention_0_cluster_id == attention_output_1_cluster_id:
        temp.append(compute_kern_id_per_layer[4][0])
    virtual_kernel_dest_per_cluster[attention_0_cluster_id].append(temp)
    # src
    temp = []
    temp.append(compute_kern_id_per_layer[7][0])
    virtual_kernel_src_per_cluster[attention_0_cluster_id].append(temp)
    # attention_1
    if attention_0_cluster_id != attention_1_cluster_id:
        for i in range(json_object['attention_0']['partition']*2):
            virtual_kernel_per_cluster[attention_1_cluster_id].append(['scatter'])
            virtual_kernel_id_per_cluster[attention_1_cluster_id].append(num_kernel_per_cluster[attention_1_cluster_id]+1 + i)
            num_virtual_kernel_per_cluster[attention_1_cluster_id] += 1
        # dest
        for _ in range(2):
            for i in range(json_object['attention_0']['partition']):
                temp = []
                for j in range(int(len(compute_kern_id_per_layer[1]) / json_object['attention_0']['partition'])):
                    temp.append(compute_kern_id_per_layer[1][j + i * int(len(compute_kern_id_per_layer[1]) / json_object['attention_0']['partition'])] )
                virtual_kernel_dest_per_cluster[attention_1_cluster_id].append(temp)
        # src
        for i in range(json_object['attention_0']['partition'] * 2):
            temp = []
            temp.append(compute_kern_id_per_layer[0][i])
            virtual_kernel_src_per_cluster[attention_1_cluster_id].append(temp)
    # attention_2
    if attention_1_cluster_id != attention_2_cluster_id:
        for i in range(json_object['attention_0']['partition']):
            virtual_kernel_per_cluster[attention_2_cluster_id].append(['scatter'])
            num_virtual_kernel_per_cluster[attention_2_cluster_id] += 1
        virtual_kernel_per_cluster[attention_2_cluster_id].append(['forward'])
        num_virtual_kernel_per_cluster[attention_2_cluster_id] += 1
        for i in range(json_object['attention_0']['partition']):
            virtual_kernel_id_per_cluster[attention_2_cluster_id].append(num_kernel_per_cluster[attention_2_cluster_id]+1 + i)
        virtual_kernel_id_per_cluster[attention_2_cluster_id].append(num_kernel_per_cluster[attention_2_cluster_id]+1 + json_object['attention_0']['partition'])
        # dest
        for i in range(json_object['attention_0']['partition']):
            temp = []
            for j in range(int(len(compute_kern_id_per_layer[2]) / json_object['attention_0']['partition'])):
                temp.append(compute_kern_id_per_layer[2][j + i * int(len(compute_kern_id_per_layer[2]) / json_object['attention_0']['partition'])] )
            virtual_kernel_dest_per_cluster[attention_2_cluster_id].append(temp)
        temp = []
        for i in range(int(len(compute_kern_id_per_layer[2]))):
            temp.append(compute_kern_id_per_layer[2][i])
        virtual_kernel_dest_per_cluster[attention_2_cluster_id].append(temp) 
        # src
        for i in range(json_object['attention_0']['partition']):
            temp = []
            temp.append(compute_kern_id_per_layer[0][i])
            virtual_kernel_src_per_cluster[attention_2_cluster_id].append(temp)
    elif attention_2_cluster_id != attention_0_cluster_id and attention_2_cluster_id == attention_1_cluster_id:
        for i in range(json_object['attention_0']['partition']):
            virtual_kernel_per_cluster[attention_2_cluster_id].append(['scatter'])
            virtual_kernel_id_per_cluster[attention_2_cluster_id].append(num_kernel_per_cluster[attention_2_cluster_id]+1 + i  + json_object['attention_0']['partition']*2)
            num_virtual_kernel_per_cluster[attention_2_cluster_id] += 1
        #dest
        for i in range(json_object['attention_0']['partition']):
            temp = []
            for j in range(int(len(compute_kern_id_per_layer[2]) / json_object['attention_0']['partition'])):
                temp.append(compute_kern_id_per_layer[2][j + i * int(len(compute_kern_id_per_layer[2]) / json_object['attention_0']['partition'])] )
            virtual_kernel_dest_per_cluster[attention_2_cluster_id].append(temp)
        # src
        for i in range(json_object['attention_0']['partition']):
            temp = []
            temp.append(compute_kern_id_per_layer[0][i + json_object['attention_0']['partition']*2])
            virtual_kernel_src_per_cluster[attention_2_cluster_id].append(temp)
    # attention_output_0
    if attention_2_cluster_id != attention_output_0_cluster_id:
        if num_kernel_per_cluster[attention_output_0_cluster_id] > 1:
            virtual_kernel_per_cluster[attention_output_0_cluster_id].append(['gather', 'broadcast'])
            num_virtual_kernel_per_cluster[attention_output_0_cluster_id] += 1
        else:
            virtual_kernel_per_cluster[attention_output_0_cluster_id].append(['gather'])
            num_virtual_kernel_per_cluster[attention_output_0_cluster_id] += 1
        virtual_kernel_id_per_cluster[attention_output_0_cluster_id].append(num_kernel_per_cluster[attention_output_0_cluster_id]+1)
        # dest
        temp = []
        for i in range(len(compute_kern_id_per_layer[3])):
            temp.append(i+1)
        virtual_kernel_dest_per_cluster[attention_output_0_cluster_id].append(temp)
        # src
        temp = []
        for i in range(len(compute_kern_id_per_layer[2])):
            temp.append(compute_kern_id_per_layer[2][i])
        virtual_kernel_src_per_cluster[attention_output_0_cluster_id].append(temp)
    # attention_output_1
    if attention_output_0_cluster_id != attention_output_1_cluster_id:
        if json_object['attention_output_0']['partition'] > 1:
            virtual_kernel_per_cluster[attention_output_1_cluster_id].append(['gather'])
        else:
            virtual_kernel_per_cluster[attention_output_1_cluster_id].append(['forward'])
        virtual_kernel_id_per_cluster[attention_output_1_cluster_id].append(num_kernel_per_cluster[attention_output_1_cluster_id]+1)
        num_virtual_kernel_per_cluster[attention_output_1_cluster_id] += 1
        # dest
        temp = []
        temp.append(1)
        virtual_kernel_dest_per_cluster[attention_output_1_cluster_id].append(temp)
        # src
        temp = []
        for i in range(len(compute_kern_id_per_layer[3])):
            temp.append(compute_kern_id_per_layer[3][i])
        virtual_kernel_src_per_cluster[attention_output_1_cluster_id].append(temp)
    if attention_0_cluster_id != attention_output_1_cluster_id:
        virtual_kernel_per_cluster[attention_output_1_cluster_id].append(['forward'])
        virtual_kernel_id_per_cluster[attention_output_1_cluster_id].append(num_kernel_per_cluster[attention_output_1_cluster_id]+1 + len(virtual_kernel_id_per_cluster[attention_output_1_cluster_id]))
        num_virtual_kernel_per_cluster[attention_output_1_cluster_id] += 1
        # dest
        temp = []
        temp.append(compute_kern_id_per_layer[4][0])
        virtual_kernel_dest_per_cluster[attention_output_1_cluster_id].append(temp)
    # intermediate_0
    if attention_output_1_cluster_id != intermediate_0_cluster_id:
        if len(compute_kern_id_per_layer[5]) > 1:
            virtual_kernel_per_cluster[intermediate_0_cluster_id].append(['broadcast'])
            virtual_kernel_id_per_cluster[intermediate_0_cluster_id].append(num_kernel_per_cluster[intermediate_0_cluster_id]+1)
            num_virtual_kernel_per_cluster[intermediate_0_cluster_id] += 1
        else:
            virtual_kernel_per_cluster[intermediate_0_cluster_id].append(['forward'])
            virtual_kernel_id_per_cluster[intermediate_0_cluster_id].append(num_kernel_per_cluster[intermediate_0_cluster_id]+1)
            num_virtual_kernel_per_cluster[intermediate_0_cluster_id] += 1
        # dest
        temp = []
        for i in range(len(compute_kern_id_per_layer[5])):
            temp.append(compute_kern_id_per_layer[5][i])
        virtual_kernel_dest_per_cluster[intermediate_0_cluster_id].append(temp)
        # src
        temp = []
        temp.append(compute_kern_id_per_layer[4][0])
        virtual_kernel_src_per_cluster[intermediate_0_cluster_id].append(temp)
    # intermediate_output_0
    if intermediate_0_cluster_id != intermediate_output_0_cluster_id:
        if json_object['intermediate_0']['partition'] > 1 and json_object['intermediate_output_0']['partition'] > 1:
            virtual_kernel_per_cluster[intermediate_output_0_cluster_id].append(['gather','broadcast'])
            virtual_kernel_id_per_cluster[intermediate_output_0_cluster_id].append(num_kernel_per_cluster[intermediate_output_0_cluster_id]+1)
            num_virtual_kernel_per_cluster[intermediate_output_0_cluster_id] += 1
        elif json_object['intermediate_0']['partition'] > 1 and json_object['intermediate_output_0']['partition'] == 1:
            virtual_kernel_per_cluster[intermediate_output_0_cluster_id].append(['gather'])
            virtual_kernel_id_per_cluster[intermediate_output_0_cluster_id].append(num_kernel_per_cluster[intermediate_output_0_cluster_id]+1)
            num_virtual_kernel_per_cluster[intermediate_output_0_cluster_id] += 1
        elif json_object['intermediate_0']['partition'] == 1 and json_object['intermediate_output_0']['partition'] > 1:
            virtual_kernel_per_cluster[intermediate_output_0_cluster_id].append(['broadcast'])
            virtual_kernel_id_per_cluster[intermediate_output_0_cluster_id].append(num_kernel_per_cluster[intermediate_output_0_cluster_id]+1)
            num_virtual_kernel_per_cluster[intermediate_output_0_cluster_id] += 1
        else:
            virtual_kernel_per_cluster[intermediate_output_0_cluster_id].append(['forward'])
            virtual_kernel_id_per_cluster[intermediate_output_0_cluster_id].append(num_kernel_per_cluster[intermediate_output_0_cluster_id]+1)
            num_virtual_kernel_per_cluster[intermediate_output_0_cluster_id] += 1
        # dest
        temp = []
        for i in range(len(compute_kern_id_per_layer[6])):
            temp.append(compute_kern_id_per_layer[6][i])
        virtual_kernel_dest_per_cluster[intermediate_output_0_cluster_id].append(temp)
        # src
        temp = []
        for i in range(len(compute_kern_id_per_layer[5])):
            temp.append(compute_kern_id_per_layer[5][i])
        virtual_kernel_src_per_cluster[intermediate_output_0_cluster_id].append(temp)
    # intermediate_output_1
    if intermediate_output_0_cluster_id != intermediate_output_1_cluster_id:
        if json_object['intermediate_output_0']['partition'] > 1:
            virtual_kernel_per_cluster[intermediate_output_1_cluster_id].append(['gather'])
        else:
            virtual_kernel_per_cluster[intermediate_output_1_cluster_id].append(['forward'])
        virtual_kernel_id_per_cluster[intermediate_output_1_cluster_id].append(num_kernel_per_cluster[intermediate_output_1_cluster_id]+1)
        num_virtual_kernel_per_cluster[intermediate_output_1_cluster_id] += 1
        # dest
        temp = []
        temp.append(1)
        virtual_kernel_dest_per_cluster[intermediate_output_1_cluster_id].append(temp)
        # src
        temp = []
        for i in range(len(compute_kern_id_per_layer[6])):
            temp.append(compute_kern_id_per_layer[6][i])
        virtual_kernel_src_per_cluster[intermediate_output_1_cluster_id].append(temp)
    if intermediate_0_cluster_id != intermediate_output_1_cluster_id:
        virtual_kernel_per_cluster[intermediate_output_1_cluster_id].append(['forward'])
        virtual_kernel_id_per_cluster[intermediate_output_1_cluster_id].append(num_kernel_per_cluster[intermediate_output_1_cluster_id]+1+len(virtual_kernel_id_per_cluster[intermediate_output_1_cluster_id]))
        num_virtual_kernel_per_cluster[intermediate_output_1_cluster_id] += 1
        # dest
        temp = []
        temp.append(compute_kern_id_per_layer[7][0])
        virtual_kernel_dest_per_cluster[intermediate_output_1_cluster_id].append(temp)
    return virtual_kernel_per_cluster, virtual_kernel_id_per_cluster, virtual_kernel_dest_per_cluster, virtual_kernel_src_per_cluster, num_virtual_kernel_per_cluster

def get_comm_kernel_per_cluster(json_object, num_compute_kernel_per_cluster, num_virtual_kernel_per_cluster, cluster_id_per_layer, virtual_kernel_id_per_cluster, compute_kern_id_per_layer):
    cluster = json_object['cluster']
    attention_0_cluster_id = cluster_id_per_layer[0]
    attention_1_cluster_id = cluster_id_per_layer[1]
    attention_2_cluster_id = cluster_id_per_layer[2]
    attention_output_0_cluster_id = cluster_id_per_layer[3]
    attention_output_1_cluster_id = cluster_id_per_layer[4]
    intermediate_0_cluster_id = cluster_id_per_layer[5]
    intermediate_output_0_cluster_id = cluster_id_per_layer[6]
    intermediate_output_1_cluster_id = cluster_id_per_layer[7]
    # compute the total num of kernels, compute kernel + virtual kernel
    num_kernel_per_cluster = [0 for _ in range(len(cluster))]
    for i in range(len(cluster)):
        num_kernel_per_cluster[i] = num_compute_kernel_per_cluster[i] + num_virtual_kernel_per_cluster[i]
    # compute number of comm_kernels for each cluster
    comm_kernel_per_cluster = [[] for _ in range(len(cluster))]
    comm_kernel_id_per_cluster = [[] for _ in range(len(cluster))]
    comm_kernel_dest_per_cluster = [[] for _ in range(len(cluster))]
    comm_kernel_src_per_cluster = [[] for _ in range(len(cluster))]
    # attention_0
    if attention_0_cluster_id == attention_1_cluster_id:
        for i in range(json_object['attention_0']['partition']*2):
            comm_kernel_per_cluster[attention_0_cluster_id].append(['scatter'])
            comm_kernel_id_per_cluster[attention_0_cluster_id].append(num_kernel_per_cluster[attention_0_cluster_id] + 1)
            num_kernel_per_cluster[attention_0_cluster_id] += 1
        # dest
        for _ in range(2):
            for i in range(json_object['attention_0']['partition']):
                temp = []
                for j in range(int(len(compute_kern_id_per_layer[1]) / json_object['attention_0']['partition'])):
                    temp.append(compute_kern_id_per_layer[1][j + i * int(len(compute_kern_id_per_layer[1]) / json_object['attention_0']['partition'])] )
                comm_kernel_dest_per_cluster[attention_1_cluster_id].append(temp)
        # src
        for _ in range(2):
            for i in range(json_object['attention_0']['partition']):
                temp = []
                temp.append(compute_kern_id_per_layer[0][i])
                comm_kernel_src_per_cluster[attention_0_cluster_id].append(temp)
    if attention_0_cluster_id == attention_2_cluster_id:
        for i in range(json_object['attention_0']['partition']):
            comm_kernel_per_cluster[attention_0_cluster_id].append(['scatter'])
            comm_kernel_id_per_cluster[attention_0_cluster_id].append(num_kernel_per_cluster[attention_0_cluster_id] + 1)
            num_kernel_per_cluster[attention_0_cluster_id] += 1
        # dest
        for i in range(json_object['attention_0']['partition']):
            temp = []
            for j in range(int(len(compute_kern_id_per_layer[2]) / json_object['attention_0']['partition'])):
                temp.append(compute_kern_id_per_layer[2][j + i * int(len(compute_kern_id_per_layer[2]) / json_object['attention_0']['partition'])] )
            comm_kernel_dest_per_cluster[attention_2_cluster_id].append(temp)
        # src
        for i in range(json_object['attention_0']['partition']):
            temp = []
            temp.append(compute_kern_id_per_layer[0][i + json_object['attention_0']['partition']*2])
            comm_kernel_src_per_cluster[attention_0_cluster_id].append(temp)
    # attention_2
    if attention_2_cluster_id == attention_output_0_cluster_id:
        if json_object['attention_output_0']['partition'] > 1:
            comm_kernel_per_cluster[attention_2_cluster_id].append(['gather', 'broadcast'])
        else:
            comm_kernel_per_cluster[attention_2_cluster_id].append(['gather'])
        comm_kernel_id_per_cluster[attention_2_cluster_id].append(num_kernel_per_cluster[attention_2_cluster_id] + 1)
        num_kernel_per_cluster[attention_2_cluster_id] += 1
        # dest
        temp = []
        for i in range(len(compute_kern_id_per_layer[3])):
            temp.append(compute_kern_id_per_layer[3][i])
        comm_kernel_dest_per_cluster[attention_output_0_cluster_id].append(temp)
        # src
        temp = []
        for i in range(len(compute_kern_id_per_layer[2])):
            temp.append(compute_kern_id_per_layer[2][i])
        comm_kernel_src_per_cluster[attention_2_cluster_id].append(temp)
    # attention_output_0
    if attention_output_0_cluster_id == attention_output_1_cluster_id:
        if json_object['attention_output_0']['partition'] > 1:
            comm_kernel_per_cluster[attention_output_0_cluster_id].append(['gather'])
            comm_kernel_id_per_cluster[attention_output_0_cluster_id].append(num_kernel_per_cluster[attention_output_0_cluster_id] + 1)
            num_kernel_per_cluster[attention_output_0_cluster_id] += 1
            # dest
            temp = []
            temp.append(compute_kern_id_per_layer[4][0])
            comm_kernel_dest_per_cluster[attention_output_1_cluster_id].append(temp)
            # src
            temp = []
            for i in range(len(compute_kern_id_per_layer[3])):
                temp.append(compute_kern_id_per_layer[3][i])
            comm_kernel_src_per_cluster[attention_output_0_cluster_id].append(temp)
    # attention_output_1
    if attention_output_1_cluster_id == intermediate_0_cluster_id:
        comm_kernel_per_cluster[attention_output_1_cluster_id].append(['broadcast'])
        comm_kernel_id_per_cluster[attention_output_1_cluster_id].append(num_kernel_per_cluster[attention_output_1_cluster_id] + 1)
        num_kernel_per_cluster[attention_output_1_cluster_id] += 1
        # dest
        temp = []
        for i in range(len(compute_kern_id_per_layer[5])):
            temp.append(compute_kern_id_per_layer[5][i])
        comm_kernel_dest_per_cluster[intermediate_0_cluster_id].append(temp)
        # src
        temp = []
        for i in range(len(compute_kern_id_per_layer[4])):
            temp.append(compute_kern_id_per_layer[4][i])
        comm_kernel_src_per_cluster[attention_output_1_cluster_id].append(temp)
    # intermediate_0
    if intermediate_0_cluster_id == intermediate_output_0_cluster_id:
        if json_object['intermediate_0']['partition'] > 1 and json_object['intermediate_output_0']['partition'] > 1:
            comm_kernel_per_cluster[intermediate_0_cluster_id].append(['gather', 'broadcast'])
            comm_kernel_id_per_cluster[intermediate_0_cluster_id].append(num_kernel_per_cluster[intermediate_0_cluster_id] + 1)
            num_kernel_per_cluster[intermediate_0_cluster_id] += 1
            # dest
            temp = []
            for i in range(len(compute_kern_id_per_layer[6])):
                temp.append(compute_kern_id_per_layer[6][i])
            comm_kernel_dest_per_cluster[intermediate_output_0_cluster_id].append(temp)
            # src
            temp = []
            for i in range(len(compute_kern_id_per_layer[5])):
                temp.append(compute_kern_id_per_layer[5][i])
            comm_kernel_src_per_cluster[intermediate_0_cluster_id].append(temp)
        elif json_object['intermediate_0']['partition'] > 1 and json_object['intermediate_output_0']['partition'] == 1:
            comm_kernel_per_cluster[intermediate_0_cluster_id].append(['gather'])
            comm_kernel_id_per_cluster[intermediate_0_cluster_id].append(num_kernel_per_cluster[intermediate_0_cluster_id] + 1)
            num_kernel_per_cluster[intermediate_0_cluster_id] += 1
            # dest
            temp = []
            for i in range(len(compute_kern_id_per_layer[6])):
                temp.append(compute_kern_id_per_layer[6][i])
            comm_kernel_dest_per_cluster[intermediate_output_0_cluster_id].append(temp)
            # src
            temp = []
            for i in range(len(compute_kern_id_per_layer[5])):
                temp.append(compute_kern_id_per_layer[5][i])
            comm_kernel_src_per_cluster[intermediate_0_cluster_id].append(temp)
        elif json_object['intermediate_0']['partition'] == 1 and json_object['intermediate_output_0']['partition'] > 1:
            comm_kernel_per_cluster[intermediate_0_cluster_id].append(['broadcast'])
            comm_kernel_id_per_cluster[intermediate_0_cluster_id].append(num_kernel_per_cluster[intermediate_0_cluster_id] + 1)
            num_kernel_per_cluster[intermediate_0_cluster_id] += 1
            # dest
            temp = []
            for i in range(len(compute_kern_id_per_layer[6])):
                temp.append(compute_kern_id_per_layer[6][i])
            comm_kernel_dest_per_cluster[intermediate_output_0_cluster_id].append(temp)
            # src
            temp = []
            for i in range(len(compute_kern_id_per_layer[5])):
                temp.append(compute_kern_id_per_layer[5][i])
            comm_kernel_src_per_cluster[intermediate_0_cluster_id].append(temp)
    # intermediate_output_0
    if intermediate_output_0_cluster_id == intermediate_output_1_cluster_id:
        if json_object['intermediate_output_0']['partition'] > 1:
            comm_kernel_per_cluster[intermediate_output_0_cluster_id].append(['gather'])
            comm_kernel_id_per_cluster[intermediate_output_0_cluster_id].append(num_kernel_per_cluster[intermediate_output_0_cluster_id] + 1)
            num_kernel_per_cluster[intermediate_output_0_cluster_id] += 1
            # dest
            temp = []
            temp.append(compute_kern_id_per_layer[7][0])
            comm_kernel_dest_per_cluster[intermediate_output_1_cluster_id].append(temp)
            # src
            temp = []
            for i in range(len(compute_kern_id_per_layer[6])):
                temp.append(compute_kern_id_per_layer[6][i])
            comm_kernel_src_per_cluster[intermediate_output_0_cluster_id].append(temp)
    # total kernel
    for i in range(len(cluster)):
        num_kernel_per_cluster[i] += 1
    return comm_kernel_per_cluster, comm_kernel_id_per_cluster, comm_kernel_dest_per_cluster, comm_kernel_src_per_cluster, num_kernel_per_cluster


def get_compute_kern_dest_per_layer(json_object, num_attention_heads, cluster_id_per_layer, virtual_kernel_id_per_cluster, virtual_kernel_per_cluster, compute_kern_id_per_layer, comm_kernel_id_per_cluster):
    cluster = json_object['cluster']
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
    # compute kern_dest for attention_0
    curr_comm_index = [0 for _ in range(len(cluster))]
    attention_0_kern_dest = []
    if attention_0_cluster_id != attention_1_cluster_id:
        for j in range(int(json_object['attention_0']['partition'])):
            attention_0_kern_dest.append(virtual_kernel_id_per_cluster[attention_1_cluster_id][j])
        for j in range(int(json_object['attention_0']['partition'])):
            attention_0_kern_dest.append(virtual_kernel_id_per_cluster[attention_1_cluster_id][j + int(json_object['attention_0']['partition'])])
    else:
        for j in range(json_object['attention_0']['partition']):
            attention_0_kern_dest.append(comm_kernel_id_per_cluster[attention_0_cluster_id][curr_comm_index[attention_0_cluster_id]])
            curr_comm_index[attention_0_cluster_id] += 1
            # attention_0_kern_dest[0].append(num_kernel_attention_0 + 1 + j * int(num_attention_heads / json_object['attention_0']['partition']))
        for j in range(json_object['attention_0']['partition']):
            # attention_0_kern_dest[1].append(num_kernel_attention_0 + 1 + j * int(num_attention_heads / json_object['attention_0']['partition']))
            attention_0_kern_dest.append(comm_kernel_id_per_cluster[attention_0_cluster_id][curr_comm_index[attention_0_cluster_id]])
            curr_comm_index[attention_0_cluster_id] += 1
    if attention_0_cluster_id != attention_2_cluster_id and attention_1_cluster_id != attention_2_cluster_id:
        for j in range(json_object['attention_0']['partition']):
            attention_0_kern_dest.append(virtual_kernel_id_per_cluster[attention_2_cluster_id][j])
    elif attention_0_cluster_id != attention_2_cluster_id and attention_1_cluster_id == attention_2_cluster_id:
        for j in range(json_object['attention_0']['partition']):
            attention_0_kern_dest.append(virtual_kernel_id_per_cluster[attention_2_cluster_id][j + int(json_object['attention_0']['partition'] * 2)])
    else:
        for j in range(json_object['attention_0']['partition']):
            attention_0_kern_dest.append(comm_kernel_id_per_cluster[attention_0_cluster_id][curr_comm_index[attention_0_cluster_id]])
            curr_comm_index[attention_0_cluster_id] += 1
    # bypass
    if attention_0_cluster_id != attention_output_1_cluster_id:
        attention_0_kern_dest.append(virtual_kernel_id_per_cluster[attention_output_1_cluster_id][-1])
    # compute kern_dest for attention_1
    attention_1_kern_dest = [0 for _ in range(num_attention_heads)]
    if attention_1_cluster_id != attention_2_cluster_id:
        for i in range(num_attention_heads):
            virtual_kernel_id = 0
            for j in range(len(virtual_kernel_per_cluster[attention_2_cluster_id])):
                if virtual_kernel_per_cluster[attention_2_cluster_id][j] == ['forward']:
                    virtual_kernel_id = j
            attention_1_kern_dest[i] = virtual_kernel_id_per_cluster[attention_2_cluster_id][virtual_kernel_id]
    else:
        for i in range(num_attention_heads):
            attention_1_kern_dest[i] = attention_2_kern_id[i]
    # compute kern_dest for attention_2
    attention_2_kern_dest = [0 for _ in range(num_attention_heads)]
    if attention_2_cluster_id != attention_output_0_cluster_id:
        for i in range(num_attention_heads):
            attention_2_kern_dest[i] = virtual_kernel_id_per_cluster[attention_output_0_cluster_id][0]
    else:
        for i in range(num_attention_heads):
            attention_2_kern_dest[i] = comm_kernel_id_per_cluster[attention_2_cluster_id][curr_comm_index[attention_2_cluster_id]]
        curr_comm_index[attention_2_cluster_id] += 1
    # compute kern_dest for attention_output_0
    attention_output_0_kern_dest = [0 for _ in range(json_object['attention_output_0']['partition'])]
    if attention_output_0_cluster_id != attention_output_1_cluster_id:
        for i in range(json_object['attention_output_0']['partition']):
            attention_output_0_kern_dest[i] = virtual_kernel_id_per_cluster[attention_output_1_cluster_id][0]
    else:
        if json_object['attention_output_0']['partition'] == 1:
            attention_output_0_kern_dest[0] = attention_output_1_kern_id[0]
        else:
            for i in range(json_object['attention_output_0']['partition']):
                attention_output_0_kern_dest[i] = comm_kernel_id_per_cluster[attention_output_0_cluster_id][curr_comm_index[attention_output_0_cluster_id]]
            curr_comm_index[attention_output_0_cluster_id] += 1
    # compute kern_dest for attention_output_1
    attention_output_1_kern_dest = []
    if attention_output_1_cluster_id != intermediate_0_cluster_id:
        attention_output_1_kern_dest.append(virtual_kernel_id_per_cluster[intermediate_0_cluster_id][0])
    else:
        attention_output_1_kern_dest.append(comm_kernel_id_per_cluster[attention_output_1_cluster_id][curr_comm_index[attention_output_1_cluster_id]])
        curr_comm_index[attention_output_1_cluster_id] += 1
    # compute kern_dest for intermediate_0
    intermediate_0_kern_dest = [0 for _ in range(json_object['intermediate_0']['partition'])]
    if intermediate_0_cluster_id != intermediate_output_0_cluster_id:
        for i in range(json_object['intermediate_0']['partition']):
            intermediate_0_kern_dest[i] = virtual_kernel_id_per_cluster[intermediate_output_0_cluster_id][0]
    else:
        if json_object['intermediate_0']['partition'] == 1 and json_object['intermediate_output_0']['partition'] == 1:
            intermediate_0_kern_dest[0] = intermediate_output_0_kern_id[0]
        else:
            for i in range(json_object['intermediate_0']['partition']):
                intermediate_0_kern_dest[i] = comm_kernel_id_per_cluster[intermediate_0_cluster_id][curr_comm_index[intermediate_0_cluster_id]]
            curr_comm_index[intermediate_0_cluster_id] += 1
    # bypass
    if intermediate_0_cluster_id != intermediate_output_1_cluster_id:
        intermediate_0_kern_dest.append(virtual_kernel_id_per_cluster[intermediate_output_1_cluster_id][-1])
    # compute kern_dest for intermediate_output_0
    intermediate_output_0_kern_dest = [0 for _ in range(json_object['intermediate_output_0']['partition'])]
    if intermediate_output_0_cluster_id != intermediate_output_1_cluster_id:
        for i in range(json_object['intermediate_output_0']['partition']):
            intermediate_output_0_kern_dest[i] = virtual_kernel_id_per_cluster[intermediate_output_1_cluster_id][0]
    else:
        if json_object['intermediate_output_0']['partition'] == 1:
            intermediate_output_0_kern_dest[0] = intermediate_output_1_kern_id[0]
        else:
            for i in range(json_object['intermediate_output_0']['partition']):
                intermediate_output_0_kern_dest[i] = comm_kernel_id_per_cluster[intermediate_output_0_cluster_id][curr_comm_index[intermediate_output_0_cluster_id]]
            curr_comm_index[intermediate_output_0_cluster_id] += 1
    # compute kern_dest for intermediate_output_1
    intermediate_output_1_kern_dest = [virtual_kernel_id_per_cluster[attention_0_cluster_id][0]]
    return [attention_0_kern_dest, attention_1_kern_dest, attention_2_kern_dest, attention_output_0_kern_dest, attention_output_1_kern_dest, intermediate_0_kern_dest, intermediate_output_0_kern_dest, intermediate_output_1_kern_dest]

def get_compute_kern_src_per_layer(json_object, num_attention_heads, cluster_id_per_layer, virtual_kernel_id_per_cluster, compute_kern_id_per_layer, comm_kernel_id_per_cluster):
    cluster = json_object['cluster']
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
    # compute kern_src for attention_0
    attention_0_kern_src = [[0 for _ in range(json_object['attention_0']['partition'])] for _ in range(3)]
    for i in range(3):
        for j in range(json_object['attention_0']['partition']):
            attention_0_kern_src[i][j] = virtual_kernel_id_per_cluster[attention_0_cluster_id][0]
    # compute kern_src for attention_1
    curr_comm_index = [0 for _ in range(len(cluster))]
    attention_1_kern_src = [ [0,0] for _ in range(num_attention_heads)]
    if attention_0_cluster_id != attention_1_cluster_id:
        for i in range(json_object['attention_0']['partition']):
            for j in range(int(num_attention_heads/json_object['attention_0']['partition'])):
                attention_1_kern_src[i * int(num_attention_heads/json_object['attention_0']['partition']) + j][0] = virtual_kernel_id_per_cluster[attention_1_cluster_id][i]
                attention_1_kern_src[i * int(num_attention_heads/json_object['attention_0']['partition']) + j][1] = virtual_kernel_id_per_cluster[attention_1_cluster_id][i + json_object['attention_0']['partition']]
    else:
        for i in range(json_object['attention_0']['partition']):
            for j in range(int(num_attention_heads/json_object['attention_0']['partition'])):
                attention_1_kern_src[i * int(num_attention_heads/json_object['attention_0']['partition']) + j][0] = comm_kernel_id_per_cluster[attention_1_cluster_id][curr_comm_index[attention_1_cluster_id]]
            curr_comm_index[attention_1_cluster_id] += 1
        for i in range(json_object['attention_0']['partition']):
            for j in range(int(num_attention_heads/json_object['attention_0']['partition'])):
                attention_1_kern_src[i * int(num_attention_heads/json_object['attention_0']['partition']) + j][1] = comm_kernel_id_per_cluster[attention_1_cluster_id][curr_comm_index[attention_1_cluster_id]]
            curr_comm_index[attention_1_cluster_id] += 1
    # compute kern_src for attention_2
    attention_2_kern_src = [ [0,0] for _ in range(num_attention_heads)]
    if attention_1_cluster_id != attention_2_cluster_id:
        for i in range(json_object['attention_0']['partition']):
            for j in range(int(num_attention_heads/json_object['attention_0']['partition'])):
                attention_2_kern_src[i * int(num_attention_heads/json_object['attention_0']['partition']) + j][0] = virtual_kernel_id_per_cluster[attention_2_cluster_id][i]
        for i in range(num_attention_heads):
            attention_2_kern_src[i][1] = virtual_kernel_id_per_cluster[attention_2_cluster_id][json_object['attention_0']['partition']]
    elif attention_0_cluster_id != attention_2_cluster_id:
        for i in range(json_object['attention_0']['partition']):
            for j in range(int(num_attention_heads/json_object['attention_0']['partition'])):
                attention_2_kern_src[i * int(num_attention_heads/json_object['attention_0']['partition']) + j][1] = virtual_kernel_id_per_cluster[attention_2_cluster_id][i + json_object['attention_0']['partition']*2]
        for i in range(num_attention_heads):
            attention_2_kern_src[i][0] = attention_1_kern_id[i]
    else:
        for i in range(json_object['attention_0']['partition']):
            for j in range(int(num_attention_heads/json_object['attention_0']['partition'])):
                attention_2_kern_src[i * int(num_attention_heads/json_object['attention_0']['partition']) + j][1] = comm_kernel_id_per_cluster[attention_2_cluster_id][curr_comm_index[attention_2_cluster_id]]
            curr_comm_index[attention_2_cluster_id] += 1
        for i in range(num_attention_heads):
            attention_2_kern_src[i][0] = attention_1_kern_id[i]
    # compute kern_src for attention_output_0
    attention_output_0_kern_src = []
    if attention_2_cluster_id != attention_output_0_cluster_id:
        for i in range(json_object['attention_output_0']['partition']):
            attention_output_0_kern_src.append(virtual_kernel_id_per_cluster[attention_output_0_cluster_id][0])
    else:
        for i in range(json_object['attention_output_0']['partition']):
            attention_output_0_kern_src.append(comm_kernel_id_per_cluster[attention_output_0_cluster_id][curr_comm_index[attention_output_0_cluster_id]])
        curr_comm_index[attention_output_0_cluster_id] += 1
    # compute kern_src for attention_output_1
    attention_output_1_kern_src = []
    if attention_output_0_cluster_id != attention_output_1_cluster_id:
        attention_output_1_kern_src.append(virtual_kernel_id_per_cluster[attention_output_1_cluster_id][0])
        # bypass src id
        attention_output_1_kern_src.append(virtual_kernel_id_per_cluster[attention_output_1_cluster_id][1])
    else:
        if json_object['attention_output_0']['partition'] == 1:
            attention_output_1_kern_src.append(attention_output_0_kern_id[0])
        else:
            attention_output_1_kern_src.append(comm_kernel_id_per_cluster[attention_output_1_cluster_id][curr_comm_index[attention_output_1_cluster_id]])
            curr_comm_index[attention_output_1_cluster_id] += 1
        # bypass src id
        attention_output_1_kern_src.append(virtual_kernel_id_per_cluster[attention_0_cluster_id][0])
    # compute kern_src for intermediate_0
    intermediate_0_kern_src = []
    if attention_output_1_cluster_id != intermediate_0_cluster_id:
        for i in range(json_object['intermediate_0']['partition']):
            intermediate_0_kern_src.append(virtual_kernel_id_per_cluster[intermediate_0_cluster_id][0])
    else:
        for i in range(json_object['intermediate_0']['partition']):
            intermediate_0_kern_src.append(comm_kernel_id_per_cluster[intermediate_0_cluster_id][curr_comm_index[intermediate_0_cluster_id]])
        curr_comm_index[intermediate_0_cluster_id] += 1
    # compute kern_src for intermediate_output_0
    intermediate_output_0_kern_src = []
    if intermediate_0_cluster_id != intermediate_output_0_cluster_id:
        for i in range(json_object['intermediate_output_0']['partition']):
            intermediate_output_0_kern_src.append(virtual_kernel_id_per_cluster[intermediate_output_0_cluster_id][0])
    else:
        if json_object['intermediate_output_0']['partition'] == 1 and json_object['intermediate_0']['partition'] == 1:
            intermediate_output_0_kern_src.append(intermediate_0_kern_id[0])
        else:
            for i in range(json_object['intermediate_output_0']['partition']):
                intermediate_output_0_kern_src.append(comm_kernel_id_per_cluster[intermediate_output_0_cluster_id][curr_comm_index[intermediate_output_0_cluster_id]])
            curr_comm_index[intermediate_output_0_cluster_id] += 1
    # compute kern_src for intermediate_output_1
    intermediate_output_1_kern_src = []
    if intermediate_output_0_cluster_id != intermediate_output_1_cluster_id:
        intermediate_output_1_kern_src.append(virtual_kernel_id_per_cluster[intermediate_output_1_cluster_id][0])
        # bypass src id
        intermediate_output_1_kern_src.append(virtual_kernel_id_per_cluster[intermediate_output_1_cluster_id][1])
    else:
        if json_object['intermediate_output_0']['partition'] == 1:
            intermediate_output_1_kern_src.append(intermediate_output_0_kern_id[0])
        else:
            intermediate_output_1_kern_src.append(comm_kernel_id_per_cluster[intermediate_output_1_cluster_id][curr_comm_index[intermediate_output_1_cluster_id]])
            curr_comm_index[intermediate_output_1_cluster_id] += 1
        # add bypass src
        intermediate_output_1_kern_src.append(intermediate_0_kern_src[0])
    return [attention_0_kern_src, attention_1_kern_src, attention_2_kern_src, attention_output_0_kern_src, attention_output_1_kern_src, intermediate_0_kern_src, intermediate_output_0_kern_src, intermediate_output_1_kern_src]

def get_dest_cluster_per_layer(json_object, cluster_id_per_layer):
    cluster = json_object['cluster']
    attention_0_cluster_id = cluster_id_per_layer[0]
    attention_1_cluster_id = cluster_id_per_layer[1]
    attention_2_cluster_id = cluster_id_per_layer[2]
    attention_output_0_cluster_id = cluster_id_per_layer[3]
    attention_output_1_cluster_id = cluster_id_per_layer[4]
    intermediate_0_cluster_id = cluster_id_per_layer[5]
    intermediate_output_0_cluster_id = cluster_id_per_layer[6]
    intermediate_output_1_cluster_id = cluster_id_per_layer[7]
    # attention_0
    attention_0_dest_cluster = []
    if attention_0_cluster_id != attention_1_cluster_id:
        attention_0_dest_cluster.append(attention_1_cluster_id)
    if attention_0_cluster_id != attention_2_cluster_id:
        attention_0_dest_cluster.append(attention_2_cluster_id)
    if attention_0_cluster_id != attention_output_1_cluster_id:
        attention_0_dest_cluster.append(attention_output_1_cluster_id)
    # attention_1
    attention_1_dest_cluster = []
    if attention_1_cluster_id != attention_2_cluster_id:
        attention_1_dest_cluster.append(attention_2_cluster_id)
    # attention_2
    attention_2_dest_cluster = []
    if attention_2_cluster_id != attention_output_0_cluster_id:
        attention_2_dest_cluster.append(attention_output_0_cluster_id)
    # attention_output_0
    attention_output_0_dest_cluster = []
    if attention_output_0_cluster_id != attention_output_1_cluster_id:
        attention_output_0_dest_cluster.append(attention_output_1_cluster_id)
    # attention_output_1
    attention_output_1_dest_cluster = []
    if attention_output_1_cluster_id != intermediate_0_cluster_id:
        attention_output_1_dest_cluster.append(intermediate_0_cluster_id)
    # intermediate_0
    intermediate_0_dest_cluster = []
    if intermediate_0_cluster_id != intermediate_output_0_cluster_id:
        intermediate_0_dest_cluster.append(intermediate_output_0_cluster_id)
    if intermediate_0_cluster_id != intermediate_output_1_cluster_id:
        intermediate_0_dest_cluster.append(intermediate_output_1_cluster_id)
    # intermediate_output_0
    intermediate_output_0_dest_cluster = []
    if intermediate_output_0_cluster_id != intermediate_output_1_cluster_id:
        intermediate_output_0_dest_cluster.append(intermediate_output_1_cluster_id)
    # intermediate_output_1
    intermediate_output_1_dest_cluster = []
    intermediate_output_1_dest_cluster.append(intermediate_output_1_cluster_id + 1)
    return [attention_0_dest_cluster, attention_1_dest_cluster, attention_2_dest_cluster, attention_output_0_dest_cluster, attention_output_1_dest_cluster, intermediate_0_dest_cluster, intermediate_output_0_dest_cluster, intermediate_output_1_dest_cluster]