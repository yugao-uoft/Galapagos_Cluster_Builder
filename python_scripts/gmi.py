import os
import fileinput
import shutil
import numpy as np
from comm_modules import *
from tcl import *

def build_gmi_kernel(data_path, part, encoder_layer, cluster_id, kernel_name, kernel_id, kernel_dest, kernel_src):
    # create dir
    if not os.path.exists('kern'):
        os.makedirs('kern')
    if not os.path.exists('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)):
        os.makedirs('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id))
    path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)
    kern_path = path + '/kern_0'
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
    # parameters and weights
    param_file = open(kern_path + '/src/parameters.hpp', 'w')
    param_file.write('#pragma once' + '\n')
    param_file.write('#include "common.hpp" ' + '\n')
    # packet decoder
    num_op_code = len(kernel_id)
    base_id = kernel_id[0]
    top_name = 'packet_decoder'
    packet_decoder(header_file, top_file, param_file, top_name, num_op_code, base_id)
    # generate hls tcl
    ip_file = open(kern_path + '/generate_ip.tcl', 'w')
    generate_tcl(ip_file, top_name, part)
    # create vivado ip
    tcl = open(kern_path + '/generate_top.tcl', 'w')
    cwd = os.getcwd()
    create_project(tcl, cwd, part, kern_path)
    port_list = build_packet_decoder_top(tcl, kern_path, part, top_name, len(kernel_name))
    # prim
    if len(kernel_name) > 1:
        out_external =  False
    else:
        out_external =  True
    out_port_list = []
    for i in range(len(kernel_name)):
        id = kernel_id[i]
        if kernel_name[i] == ['broadcast']:
            top_name = 'broadcast_' + str(id)
            num_children = len(kernel_dest[i])
            children_id = kernel_dest[i]
            comm_broadcast(header_file, top_file, param_file, top_name, id, num_children, children_id, True)
            # # generate hls tcl
            generate_tcl(ip_file, top_name, part)
            # create vivado ip
            port = build_bcast_top(tcl, kern_path, part, top_name, port_list[i], False, 'out', out_external)
            out_port_list.append(port)
        elif kernel_name[i] == ['gather']:
            top_name = 'gather_' + str(id)
            top_name1 = 'gather_recv_' + str(id)
            top_name2 = 'gather_send_' + str(id)
            num_children = len(kernel_src[i])
            dest = kernel_dest[i][0]
            src = kernel_src[i][0]
            flit_num = 12
            comm_gather(header_file, top_file, param_file, top_name1, top_name2, id, num_children, dest, src, flit_num, True)
            # # generate hls tcl
            generate_tcl(ip_file, top_name1, part)
            generate_tcl(ip_file, top_name2, part)
            # create vivado ip
            port = build_gather_top(tcl, kern_path, part, top_name, top_name1, top_name2, len(kernel_src[i]), port_list[i], False, 'out', out_external)
            out_port_list.append(port)
        elif kernel_name[i] == ['scatter']:
            top_name = 'scatter_' + str(id)
            flit_num = 1
            flit_num_last = 1
            num_node = len(kernel_dest[i])
            num_children = len(kernel_dest[i])
            children_id = kernel_dest[i]
            comm_scatter(header_file, top_file, param_file, top_name, id, flit_num, flit_num_last, num_node, num_children, children_id, True)
            # # generate hls tcl
            generate_tcl(ip_file, top_name, part)
            # create vivado ip
            port = build_scatter_top(tcl, kern_path, part, top_name, port_list[i], False, 'out', out_external)
            out_port_list.append(port)
        elif kernel_name[i] == ['gather','broadcast']:
            top_name = 'gather_' + str(id)
            top_name1 = 'gather_recv_' + str(id)
            top_name2 = 'gather_send_' + str(id)
            top_name3 = 'broadcast_' + str(id)
            num_children = len(kernel_src[i])
            dest = kernel_dest[i][0]
            src = kernel_src[i][0]
            flit_num = 48
            comm_gather(header_file, top_file, param_file, top_name1, top_name2, id, num_children, dest, src, flit_num, True)
            num_children = len(kernel_dest[i])
            children_id = kernel_dest[i]
            comm_broadcast(header_file, top_file, param_file, top_name3, id, num_children, children_id, True)
            # # generate hls tcl
            generate_tcl(ip_file, top_name1, part)
            generate_tcl(ip_file, top_name2, part)
            generate_tcl(ip_file, top_name3, part)
            # create vivado ip
            port = build_gather_top(tcl, kern_path, part, top_name, top_name1, top_name2, len(kernel_src[i]), port_list[i], False, 'out', False)
            port = build_bcast_top(tcl, kern_path, part, top_name3, port, False, 'out', out_external)
            out_port_list.append(port)
        elif kernel_name[i] == ['forward']:
            # create vivado ip
            top_name = 'forward_' + str(id)
            port = build_forward_top(tcl, kern_path, part, top_name, port_list[i], False, 'out', out_external)
            out_port_list.append(port)
    # switch
    if len(kernel_name) > 1:
        build_switch_top(tcl, kern_path, part, out_port_list)
    # ip
    top_name = 'kern_0'
    create_ip(tcl, cwd, kern_path, top_name)
    