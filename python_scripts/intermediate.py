import os
import fileinput
import shutil
import numpy as np
from modules import *
from tcl import *

def intermediate_0(data_path, json_object, kern_id, kern_dest, dest_cluster_per_layer, hidden_size=768, intermediate_size=3072, encoder_layer=0, cluster_id=0, out_cluster=False):
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
        top_file.write('hls::stream<dataword> pipe_3; \n')
        # parameters and weights
        param_file = open(kern_path + '/src/parameters.hpp', 'w')
        param_file.write('#pragma once' + '\n')
        param_file.write('#include "common.hpp" ' + '\n')
        weight_file = open(kern_path + '/src/weights.hpp', 'w')
        in_weight_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/linear/weight_integer.txt', 'r')
        in_bias_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/linear/bias_integer.txt', 'r')
        config_name = 'config_t_linear_' + str(id)
        # dim
        M = int(intermediate_size / json_object['partition'])
        K = hidden_size
        T = linear_config['dim']['tile']
        P = linear_config['dim']['pe']
        start_index_M = i*int(intermediate_size / json_object['partition'])
        start_index_K = 0
        # linear
        linear(in_weight_file, in_bias_file, top_file, param_file, weight_file, config_name, 'in', 'pipe_1', id, dest, M, K, T, P, start_index_M, start_index_K)
        # parameters and weights
        in_b_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/gelu/b.txt', 'r')
        in_c_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/gelu/c.txt', 'r')
        in_shift_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/gelu/shift.txt', 'r')
        in_const_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/gelu/const.txt', 'r')
        config_name = 'config_t_gelu_' + str(id)
        # dim
        channel = int(intermediate_size / json_object['partition'])
        start_index = i*int(intermediate_size / json_object['partition'])
        # gelu
        gelu(in_b_file, in_c_file, in_shift_file, in_const_file, top_file, param_file, weight_file, config_name, 'pipe_1', 'pipe_2', id, dest, channel, start_index)
        # parameters and weights
        in_m_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/act/m.txt', 'r')
        in_e_file = open(data_path + '/' + str(encoder_layer) + '/intermediate' + '/act/e.txt', 'r')
        config_name = 'config_t_act_' + str(id)
        # dim
        channel = int(intermediate_size / json_object['partition'])
        start_index = i*int(intermediate_size / json_object['partition'])
        in_data_width=32
        out_data_width=8
        # act
        act(in_m_file, in_e_file, top_file, param_file, weight_file, config_name, 'pipe_2', 'out', id, dest, channel, act_config['dim']['unroll'], start_index, in_data_width, out_data_width)
        top_file.write('\n} \n')
        # build shifting core
        top_file.write('void kernel_' + str(id) + '_skew(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        # dims 
        num_packet_per_row = 4
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
    # build bypass kernel
    if len(kern_id) > json_object['partition']:
        id = kern_id[-1]
        dest_id = kern_dest[-1]
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
        header_file.write('void kernel_' + str(id) + '_skew(\n')
        header_file.write('		hls::stream<dataword>& in, \n')
        header_file.write('		hls::stream<dataword>& out); \n')
        header_file.write('void kernel_' + str(id) + '_deskew(\n')
        header_file.write('		hls::stream<dataword>& in, \n')
        header_file.write('		hls::stream<dataword>& out); \n')
        header_file.write('void kernel_' + str(id) + '(\n')
        header_file.write('		hls::stream<dataword>& in, \n')
        header_file.write('		hls::stream<dataword>& out); \n')
        # top file for building kernel
        top_file = open(kern_path + '/src/top.cpp', 'w')
        top_file.write('#include "common.hpp" ' + '\n')
        top_file.write('#include "modules.hpp" ' + '\n')
        top_file.write('#include "parameters.hpp" ' + '\n')
        # param
        param_file = open(kern_path + '/src/parameters.hpp', 'w')
        param_file.write('#pragma once' + '\n')
        param_file.write('#include "common.hpp" ' + '\n')
        # build de-shifting core
        top_file.write('void kernel_' + str(id) + '_deskew(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        # dims 
        num_packet_per_row = 1
        config_name = 'config_t_linear_deskew_' + str(id)
        linear_deskew(top_file, param_file, config_name, num_packet_per_row, 'in', 'out')
        top_file.write('\n} \n')
        # build shifting core
        top_file.write('void kernel_' + str(id) + '_skew(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        # dims 
        virtual_dest = dest_id
        new_dest = dest_cluster_per_layer[-1]
        config_name = 'config_t_linear_skew_' + str(id)
        # next layer is in next cluster
        GMI_linear_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, 'in', 'out')
        top_file.write('\n} \n')
        # generate tcl for kernel
        ip_file = open(kern_path + '/generate_ip.tcl', 'w')
        part = json_object['part']
        # generate tcl for kernel_deskew
        top_name = 'kernel_' + str(id) + '_deskew'
        generate_tcl(ip_file, top_name, part)
        # generate tcl for kernel_skew
        top_name = 'kernel_' + str(id) + '_skew'
        generate_tcl(ip_file, top_name, part)
        # generate vivado 
        tcl = open(kern_path + '/generate_top.tcl', 'w')
        cwd = os.getcwd()
        create_project(tcl, cwd, part, kern_path)
        top_name1 = 'kernel_' + str(id) + '_deskew'
        top_name2 = 'kernel_' + str(id) + '_skew'
        build_kern_bypass_top(tcl, kern_path, part, top_name1, top_name2)
        top_name = 'kern_' + str(id)
        create_ip(tcl, cwd, kern_path, top_name)