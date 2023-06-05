import os

def generate_script(bash_file, cwd, path):
    # remove old stuff
    bash_file.write('cd ' + cwd + '/' + path +'\n')
    bash_file.write('rm -rf hls_project/*' + '\n')
    # hls
    bash_file.write('vivado_hls generate_ip.tcl' + '\n')
    # vivado
    if not os.path.exists(cwd + '/' + path + '/vivado_project'):
        os.makedirs(cwd + '/' + path + '/vivado_project')
    bash_file.write('cd ' + cwd + '/' + path +  '/vivado_project' +'\n')
    bash_file.write('vivado -mode batch -source ' + cwd + '/' + path + '/generate_top.tcl' + '\n')
    bash_file.write('cd ..' + '\n')
    return

def generate_tcl(file, top_name, part_name):
    file.write('open_project hls_project\n')
    file.write('set_top ' + top_name + '\n')
    file.write('open_solution ' + top_name + '\n')
    file.write('add_files src/top.cpp' + '\n')
    file.write('add_files src/common.hpp' + '\n')
    file.write('add_files src/parameters.hpp' + '\n')
    file.write('set_part {' + part_name + '} -tool vivado' + '\n')
    file.write('create_clock  -period 5.0 -name default' + '\n')
    file.write('csynth_design' + '\n')
    file.write('export_design -rtl verilog -format ip_catalog' + '\n')
    return

def create_project(tcl, cwd, part, kern_path):
    tcl.write('create_project project_top -part ' + part + ' -force'  + '\n')
    tcl.write('create_bd_design project_top' + '\n')
    tcl.write('set_property ip_repo_paths ' + cwd + '/' + kern_path + '/hls_project  [current_project]' + '\n')
    tcl.write('update_ip_catalog -rebuild' + '\n')

def create_ip(tcl, cwd, kern_path, top_name):
    # validate 
    tcl.write('validate_bd_design' + '\n')
    tcl.write('make_wrapper -files [get_files ' + cwd + '/' + kern_path + '/vivado_project/project_top.srcs/sources_1/bd/project_top/project_top.bd] -top' + '\n')
    tcl.write('add_files -norecurse ' + cwd + '/' + kern_path + '/vivado_project/project_top.srcs/sources_1/bd/project_top/hdl/project_top_wrapper.v' + '\n')
    tcl.write('save_bd_design' + '\n')
    # ip
    tcl.write('ipx::package_project -root_dir ' + cwd + '/' + kern_path + '/vivado_project/project_top.srcs/sources_1 -vendor yugao.com -library user -taxonomy /UserIP' + '\n')
    tcl.write('ipx::associate_bus_interfaces -busif in_r -clock ap_clk [ipx::current_core]' + '\n')
    tcl.write('ipx::associate_bus_interfaces -busif out_r -clock ap_clk [ipx::current_core]' + '\n')
    tcl.write('ipx::associate_bus_interfaces -clock ap_clk -reset ap_rst_n  [ipx::current_core]' + '\n')
    tcl.write('set_property vendor_display_name {yugao.com} [ipx::current_core]' + '\n')
    tcl.write('set_property name ' + top_name + ' [ipx::current_core]' + '\n')
    tcl.write('set_property display_name ' + top_name + ' [ipx::current_core]' + '\n')
    tcl.write('set_property description ' + top_name + ' [ipx::current_core]' + '\n')
    tcl.write('set_property core_revision 0 [ipx::current_core]' + '\n')
    tcl.write('ipx::create_xgui_files [ipx::current_core]' + '\n')
    tcl.write('ipx::update_checksums [ipx::current_core]' + '\n')
    tcl.write('ipx::save_core [ipx::current_core]' + '\n')
    tcl.write('ipx::check_integrity -quiet [ipx::current_core]' + '\n')
    tcl.write('ipx::archive_core ' + cwd + '/' + kern_path + '/vivado_project/project_top.srcs/sources_1/bd/project_top/project_top_1.0.zip [ipx::current_core]' + '\n')
    tcl.write('close_project' + '\n')
    tcl.write('exit' + '\n')

def build_kern_top(tcl, kern_path, part, top_name2, top_name3):
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name2 + ':1.0 -name kern' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name3 + ':1.0 -name skew' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_0' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_1' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_2' + '\n')
    # connect
    tcl.write('make_bd_pins_external [get_bd_pins axis_register_slice_0/aclk] ' + '\n')
    tcl.write('make_bd_pins_external [get_bd_pins axis_register_slice_0/aresetn] ' + '\n')
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins axis_register_slice_0/S_AXIS] ' + '\n')
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins axis_register_slice_2/M_AXIS] ' + '\n')
    # property
    tcl.write('set_property -dict [list name {in_r} CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports S_AXIS_0]' + '\n')
    tcl.write('set_property -dict [list name {out_r} CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports M_AXIS_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_rst_n} ] [get_bd_ports aresetn_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_clk} CONFIG.FREQ_HZ {199498000}]  [get_bd_ports aclk_0]' + '\n')
    # connect
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_0/M_AXIS] [get_bd_intf_pins kern/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins kern/out_r] [get_bd_intf_pins axis_register_slice_2/S_AXIS]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_2/M_AXIS] [get_bd_intf_pins skew/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins skew/out_r] [get_bd_intf_pins axis_register_slice_3/S_AXIS]' + '\n')
    # clk	
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_1/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins kern/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_2/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins skew/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_3/aclk]' + '\n')
    # rst
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_1/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins kern/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_2/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins skew/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_3/aresetn]' + '\n')

def build_kern_bypass_top(tcl, kern_path, part, top_name1, top_name2):
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name1 + ':1.0 -name deskew' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name2 + ':1.0 -name skew' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_0' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_1' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_2' + '\n')
    # connect
    tcl.write('make_bd_pins_external [get_bd_pins axis_register_slice_0/aclk] ' + '\n')
    tcl.write('make_bd_pins_external [get_bd_pins axis_register_slice_0/aresetn] ' + '\n')
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins axis_register_slice_0/S_AXIS] ' + '\n')
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins axis_register_slice_2/M_AXIS] ' + '\n')
    # property
    tcl.write('set_property -dict [list name {in_r} CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports S_AXIS_0]' + '\n')
    tcl.write('set_property -dict [list name {out_r} CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports M_AXIS_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_rst_n} ] [get_bd_ports aresetn_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_clk} CONFIG.FREQ_HZ {199498000}]  [get_bd_ports aclk_0]' + '\n')
    # connect
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_0/M_AXIS] [get_bd_intf_pins deskew/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins deskew/out_r] [get_bd_intf_pins axis_register_slice_1/S_AXIS]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_1/M_AXIS] [get_bd_intf_pins skew/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins skew/out_r] [get_bd_intf_pins axis_register_slice_2/S_AXIS]' + '\n')
    # clk	
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins deskew/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_1/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_2/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins skew/ap_clk]' + '\n')
    # rst
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins deskew/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_1/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_2/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins skew/ap_rst_n]' + '\n')

def build_kern_2_port_top(tcl, kern_path, part, top_name1, top_name4, top_name5, fifo_depth=64):
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name1 + ':1.0 -name arbiter' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name4 + ':1.0 -name kern' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name5 + ':1.0 -name skew' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_0' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_data_fifo:2.0 axis_data_fifo_0' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_data_fifo:2.0 axis_data_fifo_1' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_1' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_2' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_3' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name axis_register_slice_4' + '\n')
    # connect
    tcl.write('make_bd_pins_external [get_bd_pins axis_register_slice_0/aclk] ' + '\n')
    tcl.write('make_bd_pins_external [get_bd_pins axis_register_slice_0/aresetn] ' + '\n')
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins axis_register_slice_0/S_AXIS] ' + '\n')
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins axis_register_slice_4/M_AXIS] ' + '\n')
    # set_property
    tcl.write('set_property -dict [list CONFIG.FIFO_DEPTH {' + str(fifo_depth) + '}] [get_bd_cells axis_data_fifo_0]' + '\n')
    tcl.write('set_property -dict [list CONFIG.FIFO_DEPTH {' + str(fifo_depth) + '}] [get_bd_cells axis_data_fifo_1]' + '\n')
    # property
    tcl.write('set_property -dict [list name {in_r} CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports S_AXIS_0]' + '\n')
    tcl.write('set_property -dict [list name {out_r} CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports M_AXIS_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_rst_n} ] [get_bd_ports aresetn_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_clk} CONFIG.FREQ_HZ {199498000}]  [get_bd_ports aclk_0]' + '\n')
    # connect
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_0/M_AXIS] [get_bd_intf_pins arbiter/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins arbiter/out_0] [get_bd_intf_pins axis_data_fifo_0/S_AXIS]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins arbiter/out_1] [get_bd_intf_pins axis_data_fifo_1/S_AXIS]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_data_fifo_0/M_AXIS] [get_bd_intf_pins deskew_0/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_data_fifo_1/M_AXIS] [get_bd_intf_pins deskew_1/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins deskew_0/out_r] [get_bd_intf_pins axis_register_slice_1/S_AXIS]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins deskew_1/out_r] [get_bd_intf_pins axis_register_slice_2/S_AXIS]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_1/M_AXIS] [get_bd_intf_pins kern/in_0]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_2/M_AXIS] [get_bd_intf_pins kern/in_1]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins kern/out_r] [get_bd_intf_pins axis_register_slice_3/S_AXIS]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_register_slice_3/M_AXIS] [get_bd_intf_pins skew/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins skew/out_r] [get_bd_intf_pins axis_register_slice_4/S_AXIS]' + '\n')
    # clk	
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins arbiter/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins deskew_0/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins deskew_1/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins kern/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins skew/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_data_fifo_0/s_axis_aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_data_fifo_1/s_axis_aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_1/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_2/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_3/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_register_slice_4/aclk]' + '\n')
    # rst
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins arbiter/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins deskew_0/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins deskew_1/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_1/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins kern/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_2/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins skew/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_3/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_register_slice_4/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_data_fifo_0/s_axis_aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_data_fifo_1/s_axis_aresetn]' + '\n')

def build_packet_decoder_top(tcl, kern_path, part, top_name, num_port):
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name + ':1.0 -name packet_decoder' + '\n')
    # connect
    tcl.write('make_bd_pins_external [get_bd_pins packet_decoder/ap_clk] ' + '\n')
    tcl.write('make_bd_pins_external [get_bd_pins packet_decoder/ap_rst_n] ' + '\n')
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins packet_decoder/in_r] ' + '\n')
    # property
    tcl.write('set_property -dict [list name {in_r} CONFIG.FREQ_HZ {199498000}] [get_bd_intf_ports in_r_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_rst_n} ] [get_bd_ports ap_rst_n_0]' + '\n')
    tcl.write('set_property -dict [list name {ap_clk} CONFIG.FREQ_HZ {199498000} ]  [get_bd_ports ap_clk_0]' + '\n')
    port_list = []
    for i in range(num_port):
        port_list.append('packet_decoder/out_' + str(i))
    return port_list

def build_bcast_top(tcl, kern_path, part, top_name, in_port, external_input, out_port, external_output, fifo_depth=64):
    tcl.write('create_bd_cell -type hier ' + top_name + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name + ':1.0 -name ' + top_name + '/bcast' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name ' + top_name + '/axis_register_slice_0' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name ' + top_name + '/axis_register_slice_1' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_data_fifo:2.0 ' + top_name + '/axis_data_fifo_0' + '\n')
    # connect
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/M_AXIS] [get_bd_intf_pins ' + top_name + '/bcast/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_register_slice_1/S_AXIS] [get_bd_intf_pins ' + top_name + '/bcast/out_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_data_fifo_0/M_AXIS] [get_bd_intf_pins ' + top_name + '/bcast/in_fifo]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_data_fifo_0/S_AXIS] [get_bd_intf_pins ' + top_name + '/bcast/out_fifo]' + '\n')
    if external_input == False:
        tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + in_port + '] [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/S_AXIS]' + '\n')
    else:
        tcl.write('make_bd_intf_pins_external  [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/S_AXIS]' + '\n')
        tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports S_AXIS_0]\n')
        tcl.write('set_property name in_r [get_bd_intf_ports S_AXIS_0]\n')
    if external_output == True:
        tcl.write('make_bd_intf_pins_external  [get_bd_intf_pins ' + top_name + '/axis_register_slice_1/M_AXIS]' + '\n')
        tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000}] [get_bd_intf_ports M_AXIS_0]\n')
        tcl.write('set_property name out_r [get_bd_intf_ports M_AXIS_0]\n')
    # set_property
    tcl.write('set_property -dict [list CONFIG.FIFO_DEPTH {' + str(fifo_depth) + '}] [get_bd_cells ' + top_name + '/axis_data_fifo_0]' + '\n')
    if external_input == False:
        # clk	
        tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_register_slice_0/aclk]' + '\n')
        # rst
        tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_register_slice_0/aresetn]' + '\n')
    else:
        # clk
        tcl.write('make_bd_pins_external [get_bd_pins ' + top_name + '/axis_register_slice_0/aclk] ' + '\n')
        tcl.write('make_bd_pins_external [get_bd_pins ' + top_name + '/axis_register_slice_0/aresetn] ' + '\n')
        # rst
        tcl.write('set_property -dict [list name {ap_rst_n} ] [get_bd_ports aresetn_0]' + '\n')
        tcl.write('set_property -dict [list name {ap_clk} CONFIG.FREQ_HZ {199498000} ]  [get_bd_ports aclk_0]' + '\n')
    # clk	
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_register_slice_1/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/bcast/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_data_fifo_0/s_axis_aclk]' + '\n')
    # rst
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_register_slice_1/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/bcast/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_data_fifo_0/s_axis_aresetn]' + '\n')
    return top_name + '/axis_register_slice_1/M_AXIS'
    

def build_gather_top(tcl, kern_path, part, top_name, top_name1, top_name2, max_child_num, in_port, external_input, out_port, external_output, fifo_depth=64):
    tcl.write('create_bd_cell -type hier ' + top_name + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name1 + ':1.0 -name ' + top_name + '/gather_recv' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name2 + ':1.0 -name ' + top_name + '/gather_send' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name ' + top_name + '/axis_register_slice_0' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name ' + top_name + '/axis_register_slice_1' + '\n')
    for i in range(max_child_num):
        tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_data_fifo:2.0 ' + top_name + '/axis_data_fifo_' + str(i) + '\n')
    # connect
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/M_AXIS] [get_bd_intf_pins ' + top_name + '/gather_recv/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_register_slice_1/S_AXIS] [get_bd_intf_pins ' + top_name + '/gather_send/out_r]' + '\n')
    for i in range(max_child_num):
        tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_data_fifo_' + str(i) + '/S_AXIS] [get_bd_intf_pins ' + top_name + '/gather_recv/out_' + str(i) + ']' + '\n')
        tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_data_fifo_' + str(i) + '/M_AXIS] [get_bd_intf_pins ' + top_name + '/gather_send/in_' + str(i) + ']' + '\n')
    if external_input == False:
        tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + in_port + '] [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/S_AXIS]' + '\n')
    else:
        tcl.write('make_bd_intf_pins_external  [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/S_AXIS]' + '\n')
        tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports S_AXIS_0]\n')
        tcl.write('set_property name in_r [get_bd_intf_ports S_AXIS_0]\n')
    if external_output == True:
        tcl.write('make_bd_intf_pins_external  [get_bd_intf_pins ' + top_name + '/axis_register_slice_1/M_AXIS]' + '\n')
        tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000}] [get_bd_intf_ports M_AXIS_0]\n')
        tcl.write('set_property name out_r [get_bd_intf_ports M_AXIS_0]\n')
    # set_property
    for i in range(max_child_num):
        tcl.write('set_property -dict [list CONFIG.FIFO_DEPTH {' + str(fifo_depth) + '}] [get_bd_cells ' + top_name + '/axis_data_fifo_' + str(i) + ']' + '\n')
    if external_input == False:
        # clk	
        tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_register_slice_0/aclk]' + '\n')
        # rst
        tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_register_slice_0/aresetn]' + '\n')
    else:
        # clk
        tcl.write('make_bd_pins_external [get_bd_pins ' + top_name + '/axis_register_slice_0/aclk] ' + '\n')
        tcl.write('make_bd_pins_external [get_bd_pins ' + top_name + '/axis_register_slice_0/aresetn] ' + '\n')
        # rst
        tcl.write('set_property -dict [list name {ap_rst_n} ] [get_bd_ports aresetn_0]' + '\n')
        tcl.write('set_property -dict [list name {ap_clk} CONFIG.FREQ_HZ {199498000} ]  [get_bd_ports aclk_0]' + '\n')
    # clk	
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_register_slice_1/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/gather_recv/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/gather_send/ap_clk]' + '\n')
    for i in range(max_child_num):
        tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_data_fifo_' + str(i) + '/s_axis_aclk]' + '\n')
    # rst
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_register_slice_1/aresetn]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/gather_recv/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/gather_send/ap_rst_n]' + '\n')
    for i in range(max_child_num):
        tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_data_fifo_' + str(i) + '/s_axis_aresetn]' + '\n')
    return top_name + '/axis_register_slice_1/M_AXIS'

def build_scatter_top(tcl, kern_path, part, top_name, in_port, external_input, out_port, external_output):
    tcl.write('create_bd_cell -type hier ' + top_name + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:hls:' + top_name + ':1.0 -name ' + top_name + '/scatter' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name ' + top_name + '/axis_register_slice_0' + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name ' + top_name + '/axis_register_slice_1' + '\n')
    # connect
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/M_AXIS] [get_bd_intf_pins ' + top_name + '/scatter/in_r]' + '\n')
    tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + top_name + '/axis_register_slice_1/S_AXIS] [get_bd_intf_pins ' + top_name + '/scatter/out_r]' + '\n')
    if external_input == False:
        tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + in_port + '] [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/S_AXIS]' + '\n')
    else:
        tcl.write('make_bd_intf_pins_external  [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/S_AXIS]' + '\n')
        tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports S_AXIS_0]\n')
        tcl.write('set_property name in_r [get_bd_intf_ports S_AXIS_0]\n')
    if external_output == True:
        tcl.write('make_bd_intf_pins_external  [get_bd_intf_pins ' + top_name + '/axis_register_slice_1/M_AXIS]' + '\n')
        tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000}] [get_bd_intf_ports M_AXIS_0]\n')
        tcl.write('set_property name out_r [get_bd_intf_ports M_AXIS_0]\n')
    if external_input == False:
        # clk	
        tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_register_slice_0/aclk]' + '\n')
        # rst
        tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_register_slice_0/aresetn]' + '\n')
    else:
        # clk
        tcl.write('make_bd_pins_external [get_bd_pins ' + top_name + '/axis_register_slice_0/aclk] ' + '\n')
        tcl.write('make_bd_pins_external [get_bd_pins ' + top_name + '/axis_register_slice_0/aresetn] ' + '\n')
        # rst
        tcl.write('set_property -dict [list name {ap_rst_n} ] [get_bd_ports aresetn_0]' + '\n')
        tcl.write('set_property -dict [list name {ap_clk} CONFIG.FREQ_HZ {199498000} ]  [get_bd_ports aclk_0]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/scatter/ap_clk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/scatter/ap_rst_n]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_register_slice_1/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_register_slice_1/aresetn]' + '\n')
    return top_name + '/axis_register_slice_1/M_AXIS'

def build_forward_top(tcl, kern_path, part, top_name, in_port, external_input, out_port, external_output):
    # connect
    tcl.write('create_bd_cell -type hier ' + top_name + '\n')
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_register_slice:1.1 -name ' + top_name + '/axis_register_slice_0' + '\n')
    if external_input == False:
        tcl.write('connect_bd_intf_net [get_bd_intf_pins ' + in_port + '] [get_bd_intf_pins ' + top_name + '/axis_register_slice_0/S_AXIS]' + '\n')
    else:
        tcl.write('make_bd_intf_pins_external  [get_bd_intf_pins ' + top_name + 'axis_register_slice_0/S_AXIS]' + '\n')
        tcl.write('set_property name in_r [get_bd_intf_ports S_AXIS_0]' + '\n')
        tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000} CONFIG.HAS_TLAST {1} CONFIG.TDATA_NUM_BYTES {64} CONFIG.TDEST_WIDTH {8} CONFIG.TID_WIDTH {8} CONFIG.TUSER_WIDTH {16}] [get_bd_intf_ports in_r]\n')
    # clk	
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins ' + top_name + '/axis_register_slice_0/aclk]' + '\n')
    # rst
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins ' + top_name + '/axis_register_slice_0/aresetn]' + '\n')
    return top_name + '/axis_register_slice_0/M_AXIS'

def build_switch_top(tcl, kern_path, part, out_port_list):
    tcl.write('create_bd_cell -type ip -vlnv xilinx.com:ip:axis_switch:1.1 axis_switch_net' + '\n')
    tcl.write('set_property -dict [list CONFIG.NUM_SI {' + str(len(out_port_list)) + '} CONFIG.HAS_TLAST {1}   CONFIG.ARB_ON_MAX_XFERS {0} CONFIG.ARB_ON_TLAST {1} CONFIG.M00_AXIS_HIGHTDEST {0xff} ] [get_bd_cells axis_switch_net]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_clk] [get_bd_pins axis_switch_net/aclk]' + '\n')
    tcl.write('connect_bd_net [get_bd_ports ap_rst_n] [get_bd_pins axis_switch_net/aresetn]' + '\n')
    for i in range(len(out_port_list)):
        tcl.write('connect_bd_intf_net [get_bd_intf_pins axis_switch_net/S0' + str(i) + '_AXIS] [get_bd_intf_pins ' + out_port_list[i] + ']' + '\n')	
    tcl.write('make_bd_intf_pins_external [get_bd_intf_pins axis_switch_net/M00_AXIS] ' + '\n')
    tcl.write('set_property name out_r [get_bd_intf_ports M00_AXIS_0]' + '\n')
    tcl.write('set_property -dict [list CONFIG.FREQ_HZ {199498000}] [get_bd_intf_ports out_r]\n')
