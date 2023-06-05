import os
import fileinput
import shutil
import numpy as np
from modules import *
from tcl import *

def intermediate_output_0(data_path, json_object, kern_id, kern_dest, dest_cluster_per_layer, hidden_size=768, intermediate_size=3072, encoder_layer=0, cluster_id=0, out_cluster=False):
    config = json_object['config']
    for inst in config:
        if inst['name'] == 'linear':
            linear_config = inst
        if inst['name'] == 'act':
            act_config = inst
    # create dir
    if not os.path.exists('kern'):
        os.makedirs('kern')
    if not os.path.exists('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)):
        os.makedirs('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id))
    path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)
    # linear and act
    for i in range(json_object['partition']):
        id = kern_id[i]
        dest = kern_dest[i]
        kern_path = path + '/kern_' + str(id)
        # create dir
        if not os.path.exists(kern_path):
            os.makedirs(kern_path)
        if not os.path.exists(kern_path + '/src'):
            os.makedirs(kern_path + '/src')
        # copy file
        shutil.copy('src/common.hpp', kern_path + '/src/common.hpp')
        shutil.copy('src/modules.hpp', kern_path + '/src/modules.hpp')
        # header file for software usage
        header_file = open(kern_path + '/src/top.hpp', 'w')
        header_file.write('#pragma once' + '\n')
        header_file.write('#include "common.hpp" ' + '\n')
        # top file for building kernel
        top_file = open(kern_path + '/src/top.cpp', 'w')
        top_file.write('#include "common.hpp" ' + '\n')
        top_file.write('#include "modules.hpp" ' + '\n')
        top_file.write('#include "parameters.hpp" ' + '\n')
        top_file.write('#include "weights.hpp" ' + '\n')
        top_file.write('void kernel_' + str(id) + '(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        top_file.write('#pragma HLS dataflow\n')
        top_file.write('hls::stream<dataword> pipe_1; \n')
        top_file.write('hls::stream<dataword> pipe_2; \n')
        # parameters and weights
        param_file = open(kern_path + '/src/parameters.hpp', 'w')
        param_file.write('#pragma once' + '\n')
        param_file.write('#include "common.hpp" ' + '\n')
        weight_file = open(kern_path + '/src/weights.hpp', 'w')
        in_weight_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/linear/weight_integer.txt', 'r')
        in_bias_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/linear/bias_integer.txt', 'r')
        config_name = 'config_t_linear_' + str(id)
        # dim
        M = int(hidden_size / json_object['partition'])
        K = intermediate_size
        T = linear_config['dim']['tile']
        P = linear_config['dim']['pe']
        start_index_M = i*int(hidden_size / json_object['partition'])
        start_index_K = 0
        # linear
        linear(in_weight_file, in_bias_file, top_file, param_file, weight_file, config_name, 'in', 'pipe_1', id, dest, M, K, T, P, start_index_M, start_index_K)
        # parameters and weights
        in_m_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/act_linear/m.txt', 'r')
        in_e_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/act_linear/e.txt', 'r')
        config_name = 'config_t_act_' + str(id)
        # dim
        channel = int(hidden_size / json_object['partition'])
        start_index = i*int(hidden_size / json_object['partition'])
        in_data_width=32
        out_data_width=32
        # act
        act(in_m_file, in_e_file, top_file, param_file, weight_file, config_name, 'pipe_1', 'out', id, dest, channel, act_config['dim']['unroll'], start_index, in_data_width, out_data_width)
        top_file.write('\n} \n')
        # build shifting core
        top_file.write('void kernel_' + str(id) + '_skew(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        # dims 
        num_packet_per_row = 1
        virtual_dest = dest
        config_name = 'config_t_linear_skew_' + str(id)
        # next layer is in next cluster
        if out_cluster == False:
            skew(top_file, param_file, config_name, num_packet_per_row, 'in', 'out')
        else:
            new_dest = dest_cluster_per_layer[0]
            GMI_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, 'in', 'out')
        top_file.write('\n} \n')
        # tcl
        ip_file = open(kern_path + '/generate_ip.tcl', 'w')
        top_name = 'kernel_' + str(id)
        part = json_object['part']
        generate_tcl(ip_file, top_name, part)
        # generate tcl for kernel_skew
        top_name = 'kernel_' + str(id) + '_skew'
        generate_tcl(ip_file, top_name, part)
        # generate vivado 
        tcl = open(kern_path + '/generate_top.tcl', 'w')
        cwd = os.getcwd()
        create_project(tcl, cwd, part, kern_path)
        top_name2 = 'kernel_' + str(id)
        top_name3 = 'kernel_' + str(id) + '_skew'
        build_kern_top(tcl, kern_path, part, top_name2, top_name3)
        top_name = 'kern_' + str(id)
        create_ip(tcl, cwd, kern_path, top_name)


def intermediate_output_1(data_path, json_object, kern_id, kern_dest, kern_src, dest_cluster_per_layer, hidden_size=768, intermediate_size=3072, encoder_layer=0, cluster_id=0):
    config = json_object['config']
    for inst in config:
        if inst['name'] == 'linear':
            linear_config = inst
        if inst['name'] == 'act':
            act_config = inst
        if inst['name'] == 'layernorm':
            layernorm_config = inst
    # create dir
    if not os.path.exists('kern'):
        os.makedirs('kern')
    if not os.path.exists('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)):
        os.makedirs('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id))
    path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)
    # layernorm and act
    id = kern_id[0]
    dest = kern_dest[0]
    kern_path = path + '/kern_' + str(id)
    # create dir
    if not os.path.exists(kern_path):
        os.makedirs(kern_path)
    if not os.path.exists(kern_path + '/src'):
        os.makedirs(kern_path + '/src')
    # copy
    shutil.copy('src/common.hpp', kern_path + '/src/common.hpp')
    shutil.copy('src/modules.hpp', kern_path + '/src/modules.hpp')
    # header
    header_file = open(kern_path + '/src/top.hpp', 'w')
    header_file.write('#pragma once' + '\n')
    header_file.write('#include "common.hpp" ' + '\n')
    # top
    top_file = open(kern_path + '/src/top.cpp', 'w')
    top_file.write('#include "common.hpp" ' + '\n')
    top_file.write('#include "modules.hpp" ' + '\n')
    top_file.write('#include "parameters.hpp" ' + '\n')
    top_file.write('#include "weights.hpp" ' + '\n')
    top_file.write('void kernel_' + str(id) + '(\n')
    top_file.write('		hls::stream<dataword> in_1, \n')
    top_file.write('		hls::stream<dataword> in_2, \n')
    top_file.write('		hls::stream<dataword>& out) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in_1 \n#pragma HLS INTERFACE axis port=in_2\n#pragma HLS INTERFACE axis port=out\n')
    top_file.write('#pragma HLS dataflow\n')
    top_file.write('hls::stream<dataword> pipe_2; \n')
    top_file.write('hls::stream<dataword> pipe_3; \n')
    top_file.write('hls::stream<dataword> pipe_4; \n')
    top_file.write('hls::stream<dataword> pipe_5; \n')
    top_file.write('hls::stream<dataword> pipe_6; \n')
    param_file = open(kern_path + '/src/parameters.hpp', 'w')
    param_file.write('#pragma once' + '\n')
    param_file.write('#include "common.hpp" ' + '\n')
    # identity act
    top_file = open(kern_path + '/src/top.cpp', 'a')
    param_file = open(kern_path + '/src/parameters.hpp', 'a')
    weight_file = open(kern_path + '/src/weights.hpp', 'w')
    in_m1_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/act_linear/m1.txt', 'r')
    in_e1_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/act_linear/e1.txt', 'r')
    config_name = 'config_t_identity_act_' + str(id)
    # dim
    channel = int(hidden_size)
    start_index = 0
    in_data_width=8
    out_data_width=32
    # act
    act(in_m1_file, in_e1_file, top_file, param_file, weight_file, config_name, 'in_2', 'pipe_2', id, dest, channel, act_config['dim']['unroll'], start_index, in_data_width, out_data_width, True)
    # identity add
    config_name = 'config_t_identity_add_' + str(id)
    identity_add(top_file, param_file, config_name, 'in_1', 'pipe_2', 'pipe_3', id, dest, hidden_size)
    # params
    in_shift_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/layernorm/shift.txt', 'r')
    in_bias_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/layernorm/bias.txt', 'r')
    config_name = 'config_t_layernorm_' + str(id)
    # dim
    unroll = layernorm_config['dim']['unroll']
    # layernorm
    layernorm(in_shift_file, in_bias_file, top_file, param_file, weight_file, config_name, 'pipe_3', 'pipe_4', id, dest, hidden_size, unroll)
    # params
    in_m_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/act_layernorm/m.txt', 'r')
    in_e_file = open(data_path + '/' + str(encoder_layer) + '/output' + '/act_layernorm/e.txt', 'r')
    config_name = 'config_t_act_' + str(id)
    # dim
    channel = int(hidden_size)
    start_index = 0
    in_data_width=32
    out_data_width=8
    # act
    act(in_m_file, in_e_file, top_file, param_file, weight_file, config_name, 'pipe_4', 'out', id, dest, channel, act_config['dim']['unroll'], start_index, in_data_width, out_data_width)
    top_file.write('\n} \n')
    # build 2 port arbiter 
    top_file.write('void kernel_' + str(id) + '_arbiter(\n')
    top_file.write('		hls::stream<dataword>& in, \n')
    top_file.write('		hls::stream<dataword> out[2]) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
    config_name = 'config_t_arbiter_' + str(id)
    src_id_1 = kern_src[0]
    src_id_2 = kern_src[1]
    arbiter_2_port(top_file, param_file, config_name, src_id_1, src_id_2, 'in', 'out')
    top_file.write('\n} \n')
    # build shifting core
    top_file.write('void kernel_' + str(id) + '_skew(\n')
    top_file.write('		hls::stream<dataword>& in, \n')
    top_file.write('		hls::stream<dataword>& out) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
    # dims 
    num_packet_per_row = 1
    virtual_dest = dest
    new_dest = dest_cluster_per_layer[0]
    config_name = 'config_t_linear_skew_' + str(id)
    # next layer is in next cluster
    GMI_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, 'in', 'out')
    top_file.write('\n} \n')
    # tcl
    ip_file = open(kern_path + '/generate_ip.tcl', 'w')
    top_name = 'kernel_' + str(id)
    part = json_object['part']
    generate_tcl(ip_file, top_name, part)
    # tcl
    ip_file = open(kern_path + '/generate_ip.tcl', 'w')
    top_name = 'kernel_' + str(id) 
    part = json_object['part']
    generate_tcl(ip_file, top_name, part)
    # generate tcl for kernel_arbiter
    top_name = 'kernel_' + str(id) + '_arbiter'
    generate_tcl(ip_file, top_name, part)
    # generate tcl for kernel_skew
    top_name = 'kernel_' + str(id) + '_skew'
    generate_tcl(ip_file, top_name, part)
    # generate vivado 
    tcl = open(kern_path + '/generate_top.tcl', 'w')
    cwd = os.getcwd()
    create_project(tcl, cwd, part, kern_path)
    top_name1 = 'kernel_' + str(id) + '_arbiter'
    top_name4 = 'kernel_' + str(id)
    top_name5 = 'kernel_' + str(id) + '_skew'
    build_kern_2_port_top(tcl, kern_path, part, top_name1, top_name4, top_name5)
    top_name = 'kern_' + str(id)
    create_ip(tcl, cwd, kern_path, top_name)