import os
import fileinput
import shutil
import numpy as np
from comm_modules import *
from tcl import *

def build_comm_kernel(data_path, part, encoder_layer, cluster_id, kernel_name, kernel_id, kernel_dest, kernel_src):
    # create dir
    if not os.path.exists('kern'):
        os.makedirs('kern')
    if not os.path.exists('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)):
        os.makedirs('kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id))
    path = 'kern/layer_' + str(encoder_layer) + '/cluster_' + str(cluster_id)
    id = kernel_id
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
    # parameters and weights
    param_file = open(kern_path + '/src/parameters.hpp', 'w')
    param_file.write('#pragma once' + '\n')
    param_file.write('#include "common.hpp" ' + '\n')
    # generate hls 
    ip_file = open(kern_path + '/generate_ip.tcl', 'w')
    # generate vivado 
    tcl = open(kern_path + '/generate_top.tcl', 'w')
    cwd = os.getcwd()
    create_project(tcl, cwd, part, kern_path)
    # core
    if kernel_name == ['broadcast']:
        top_name = 'broadcast_' + str(id)
        comm_broadcast(header_file, top_file, param_file, top_name, id, len(kernel_dest), kernel_dest)
        # generate hls 
        generate_tcl(ip_file, top_name, part)
        # create vivado ip
        build_bcast_top(tcl, kern_path, part, top_name, 'in', True, 'out', True)
    elif kernel_name == ['gather']:
        top_name = 'gather_' + str(id)
        top_name1 = 'gather_recv_' + str(id)
        top_name2 = 'gather_send_' + str(id)
        flit_num = 12
        comm_gather(header_file, top_file, param_file, top_name1, top_name2, id, len(kernel_src), kernel_dest[0], kernel_src[0], flit_num)
        # generate hls 
        generate_tcl(ip_file, top_name1, part)
        generate_tcl(ip_file, top_name2, part)
        # create vivado ip
        build_gather_top(tcl, kern_path, part, top_name, top_name1, top_name2, len(kernel_src), 'in', True, 'out', True)
    elif kernel_name == ['scatter']:
        top_name = 'scatter_' + str(id)
        flit_num = 1
        flit_num_last = 1
        num_node = len(kernel_dest)
        num_children = len(kernel_dest)
        children_id = kernel_dest
        comm_scatter(header_file, top_file, param_file, top_name, id, flit_num, flit_num_last, num_node, num_children, children_id)
        # generate hls 
        generate_tcl(ip_file, top_name, part)
        # create vivado ip
        build_scatter_top(tcl, kern_path, part, top_name, 'in', True, 'out', True)
    elif kernel_name == ['gather','broadcast']:
        top_name = 'gather_' + str(id)
        top_name1 = 'gather_recv_' + str(id)
        top_name2 = 'gather_send_' + str(id)
        top_name3 = 'broadcast_' + str(id)
        flit_num = 48
        comm_gather(header_file, top_file, param_file, top_name1, top_name2, id, len(kernel_src), '-1', kernel_src[0], flit_num)
        comm_broadcast(header_file, top_file, param_file, top_name3, id, len(kernel_dest), kernel_dest)
        # generate hls 
        generate_tcl(ip_file, top_name1, part)
        generate_tcl(ip_file, top_name2, part)
        generate_tcl(ip_file, top_name3, part)
        # create vivado ip
        port = build_gather_top(tcl, kern_path, part, top_name, top_name1, top_name2, len(kernel_src), 'in', True, 'out', False)
        build_bcast_top(tcl, kern_path, part, top_name3, port, False, 'out', True)
    # ip
    top_name = 'kern_' + str(id)
    create_ip(tcl, cwd, kern_path, top_name)
    
    