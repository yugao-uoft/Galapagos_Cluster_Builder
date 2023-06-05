import os
import fileinput
import shutil
import numpy as np
from modules import *
from tcl import *

def attention_0(data_path, json_object, kern_id, kern_dest, dest_cluster_per_layer, hidden_size=768, num_attention_heads=12, max_sentence_len=128, encoder_layer=0, cluster_id=0, out_cluster=False):
    # get linear and act config
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
    # build each function
    l = ['q', 'k', 'v']
    for i in range(len(l)):
        for j in range(json_object['partition']):
            id = kern_id[i*json_object['partition'] + j]
            dest_id = kern_dest[i*json_object['partition'] + j]
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
            in_weight_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/linear_' + str(l[i]) + '/weight_integer.txt', 'r')
            in_bias_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/linear_' + str(l[i]) + '/bias_integer.txt', 'r')
            config_name = 'config_t_linear_' + str(id)
            # dims for linear layer
            M = int(hidden_size / json_object['partition'])
            K = hidden_size
            T = linear_config['dim']['tile']
            P = linear_config['dim']['pe']
            start_index_M = j*int(hidden_size / json_object['partition'])
            start_index_K = 0
            # build linear 
            linear(in_weight_file, in_bias_file, top_file, param_file, weight_file, config_name, 'in', 'pipe_1', id, dest_id, M, K, T, P, start_index_M, start_index_K)
            # m and e for act
            in_m_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/act_' + str(l[i]) + '/m.txt', 'r')
            in_e_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/act_' + str(l[i]) + '/e.txt', 'r')
            config_name = 'config_t_act_' + str(id)
            # dims for act
            channel = int(hidden_size / json_object['partition'])
            start_index = j*int(hidden_size / json_object['partition'])
            in_data_width=32
            out_data_width=8
            act(in_m_file, in_e_file, top_file, param_file, weight_file, config_name, 'pipe_1', 'out', id, dest_id, channel, act_config['dim']['unroll'], start_index, in_data_width, out_data_width)
            top_file.write('\n} \n')
            # build shifting core
            top_file.write('void kernel_' + str(id) + '_skew(\n')
            top_file.write('		hls::stream<dataword>& in, \n')
            top_file.write('		hls::stream<dataword>& out) \n')
            top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
            virtual_dest = dest_id
            config_name = 'config_t_skew_' + str(id)
            num_packet_per_row = 1
            if out_cluster == False:
                skew(top_file, param_file, config_name, num_packet_per_row, 'in', 'out')
            else:
                new_dest = dest_cluster_per_layer[int(i/2)]
                GMI_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, 'in', 'out')
            top_file.write('\n} \n')
            # generate tcl for kernel
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
            top_name1 = 'kernel_' + str(id)
            top_name2 = 'kernel_' + str(id) + '_skew'
            build_kern_top(tcl, kern_path, part, top_name1, top_name2)
            top_name = 'kern_' + str(id)
            create_ip(tcl, cwd, kern_path, top_name)
    # build bypass kernel
    if len(kern_id) > json_object['partition']*3:
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
        # top file for building kernel
        top_file = open(kern_path + '/src/top.cpp', 'w')
        top_file.write('#include "common.hpp" ' + '\n')
        top_file.write('#include "modules.hpp" ' + '\n')
        top_file.write('#include "parameters.hpp" ' + '\n')
        # param
        param_file = open(kern_path + '/src/parameters.hpp', 'w')
        param_file.write('#pragma once' + '\n')
        param_file.write('#include "common.hpp" ' + '\n')
        # build shifting core
        top_file.write('void kernel_' + str(id) + '_skew(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        # dims 
        virtual_dest = dest_id
        new_dest = dest_cluster_per_layer[-1]
        config_name = 'config_t_skew_' + str(id)
        # next layer is in next cluster
        GMI_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, 'in', 'out')
        top_file.write('\n} \n')
        # generate tcl for kernel
        ip_file = open(kern_path + '/generate_ip.tcl', 'w')
        part = json_object['part']
        # generate tcl for kernel_skew
        top_name = 'kernel_' + str(id) + '_skew'
        generate_tcl(ip_file, top_name, part)
        # generate vivado 
        tcl = open(kern_path + '/generate_top.tcl', 'w')
        cwd = os.getcwd()
        create_project(tcl, cwd, part, kern_path)
        top_name = 'kernel_' + str(id) + '_skew'
        build_kern_bypass_top(tcl, kern_path, part, top_name)
        top_name = 'kern_' + str(id)
        create_ip(tcl, cwd, kern_path, top_name)


def attention_1(data_path, json_object, kern_id, kern_dest, kern_src, dest_cluster_per_layer, hidden_size=768, num_attention_heads=12, max_sentence_len=128, encoder_layer=0, cluster_id=0, out_cluster=False):
    config = json_object['config']
    for inst in config:
        if inst['name'] == 'attention_matmul':
            attention_matmul_config = inst
        if inst['name'] == 'softmax':
            softmax_config = inst
    if not os.path.exists('kern'):
        os.makedirs('kern')
    if not os.path.exists('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)):
        os.makedirs('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id))
    path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)
    for i in range(num_attention_heads):
        id = kern_id[i]
        dest = kern_dest[i]
        kern_path = path + '/kern_' + str(id)
        # create dir
        if not os.path.exists(kern_path):
            os.makedirs(kern_path)
        if not os.path.exists(kern_path + '/src'):
            os.makedirs(kern_path + '/src')
        # copy
        shutil.copy('src/common.hpp', kern_path + '/src/common.hpp')
        shutil.copy('src/modules.hpp', kern_path + '/src/modules.hpp')
        # header file
        header_file = open(kern_path + '/src/top.hpp', 'w')
        header_file.write('#pragma once' + '\n')
        header_file.write('#include "common.hpp" ' + '\n')
        header_file.write('void kernel_' + str(id) + '_skew(\n')
        header_file.write('		hls::stream<dataword>& in, \n')
        header_file.write('		hls::stream<dataword>& out); \n')
        header_file.write('void kernel_' + str(id) + '_deskew_0(\n')
        header_file.write('		hls::stream<dataword>& in, \n')
        header_file.write('		hls::stream<dataword>& out); \n')
        header_file.write('void kernel_' + str(id) + '_deskew_1(\n')
        header_file.write('		hls::stream<dataword>& in, \n')
        header_file.write('		hls::stream<dataword>& out); \n')
        header_file.write('void kernel_' + str(id) + '_arbiter(\n')
        header_file.write('		hls::stream<dataword>& in, \n')
        header_file.write('		hls::stream<dataword> out[2]); \n')
        header_file.write('void kernel_' + str(id) + '(\n')
        header_file.write('		hls::stream<dataword>& in_1, \n')
        header_file.write('		hls::stream<dataword>& in_2, \n')
        header_file.write('		hls::stream<dataword>& out); \n')
        # top file
        top_file = open(kern_path + '/src/top.cpp', 'w')
        top_file.write('#include "common.hpp" ' + '\n')
        top_file.write('#include "modules.hpp" ' + '\n')
        top_file.write('#include "parameters.hpp" ' + '\n')
        top_file.write('#include "weights.hpp" ' + '\n')
        top_file.write('void kernel_' + str(id) + '(\n')
        top_file.write('		hls::stream<dataword>& in_1, \n')
        top_file.write('		hls::stream<dataword>& in_2, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in_1\n#pragma HLS INTERFACE axis port=in_2\n#pragma HLS INTERFACE axis port=out\n')
        top_file.write('#pragma HLS dataflow\n')
        top_file.write('hls::stream<dataword> pipe_1; \n')
        param_file = open(kern_path + '/src/parameters.hpp', 'w')
        param_file.write('#pragma once' + '\n')
        param_file.write('#include "common.hpp" ' + '\n')
        config_name = 'config_t_attention_matmul_' + str(id)
        # attention dot product
        attention_matmul(top_file, param_file, config_name, max_sentence_len, 'in_1', 'in_2', 'pipe_1', id, dest, int(hidden_size / num_attention_heads), attention_matmul_config['dim']['pe'])
        # weight for softmax
        weight_file = open(kern_path + '/src/weights.hpp', 'w')
        in_const_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/softmax/const.txt', 'r')
        in_x0_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/softmax/x0.txt', 'r')
        in_b_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/softmax/b.txt', 'r')
        in_c_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/softmax/c.txt', 'r')
        in_m_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/softmax/m.txt', 'r')
        in_e_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/softmax/e.txt', 'r')
        config_name = 'config_t_softmax_' + str(id)
        #softmax
        softmax(in_const_file, in_x0_file, in_b_file, in_c_file, in_m_file, in_e_file, top_file, param_file, weight_file, config_name, max_sentence_len, 'pipe_1', 'out', id, dest, softmax_config['dim']['unroll'])
        top_file.write('\n} \n')
        # build 2 port arbiter 
        top_file.write('void kernel_' + str(id) + '_arbiter(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword> out[2]) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        config_name = 'config_t_arbiter_' + str(id)
        src_id_1 = kern_src[i][0]
        src_id_2 = kern_src[i][1]
        arbiter_2_port(top_file, param_file, config_name, src_id_1, src_id_2, 'in', 'out')
        top_file.write('\n} \n')
        # build shifting core
        top_file.write('void kernel_' + str(id) + '_skew(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        virtual_dest = dest
        config_name = 'config_t_skew_' + str(id)
        num_packet_per_row = 1
        if out_cluster == False:
            skew(top_file, param_file, config_name, num_packet_per_row, 'in', 'out')
        else:
            new_dest = dest_cluster_per_layer[int(i/2)]
            GMI_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, 'in', 'out')
        top_file.write('\n} \n')
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


def attention_2(data_path, json_object, kern_id, kern_dest, kern_src, dest_cluster_per_layer, hidden_size=768, num_attention_heads=12, max_sentence_len=128, encoder_layer=0, cluster_id=0, next_layer_partition=1, out_cluster=False):
    config = json_object['config']
    for inst in config:
        if inst['name'] == 'softmax_matmul':
            softmax_matmul_config = inst
        if inst['name'] == 'act':
            act_config = inst
    if not os.path.exists('kern'):
        os.makedirs('kern')
    if not os.path.exists('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)):
        os.makedirs('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id))
    path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)
    for i in range(num_attention_heads):
        id = kern_id[i]
        dest = kern_dest[i]
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
        top_file.write('		hls::stream<dataword>& in_1, \n')
        top_file.write('		hls::stream<dataword>& in_2, \n')
        top_file.write('		hls::stream<dataword>& out) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in_1\n#pragma HLS INTERFACE axis port=in_2\n#pragma HLS INTERFACE axis port=out\n')
        top_file.write('#pragma HLS dataflow\n')
        top_file.write('hls::stream<dataword> pipe_1; \n')
        top_file.write('hls::stream<dataword> pipe_2; \n')
        param_file = open(kern_path + '/src/parameters.hpp', 'w')
        param_file.write('#pragma once' + '\n')
        param_file.write('#include "common.hpp" ' + '\n')
        config_name = 'config_t_softmax_matmul_' + str(id)
        # softmax matmul
        softmax_matmul(top_file, param_file, config_name, max_sentence_len, 'in_1', 'in_2', 'pipe_1', id, dest, int(hidden_size / num_attention_heads), softmax_matmul_config['dim']['pe'])
        # weight for act
        weight_file = open(kern_path + '/src/weights.hpp', 'w')
        in_m_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/act_out/m.txt', 'r')
        in_e_file = open(data_path + '/' + str(encoder_layer) + '/self_attention' + '/act_out/e.txt', 'r')
        config_name = 'config_t_act_' + str(id)
        # dim for act
        channel = 64
        start_index = 0
        in_data_width=32
        out_data_width=8
        # act
        act(in_m_file, in_e_file, top_file, param_file, weight_file, config_name, 'pipe_1', 'out', id, dest, channel, act_config['dim']['unroll'], start_index, in_data_width, out_data_width)
        top_file.write('\n} \n')
        # build 2 port arbiter 
        top_file.write('void kernel_' + str(id) + '_arbiter(\n')
        top_file.write('		hls::stream<dataword>& in, \n')
        top_file.write('		hls::stream<dataword> out[2]) \n')
        top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
        config_name = 'config_t_arbiter_' + str(id)
        src_id_1 = kern_src[i][0]
        src_id_2 = kern_src[i][1]
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