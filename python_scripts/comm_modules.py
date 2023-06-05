import numpy as np

def packet_decoder(header_file, top_file, param_file, top_name, num_op_code, base_id):
    config_name = 'config_t_packet_decoder_0'
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_OP_CODE=' + str(num_op_code) + ';\n')
    param_file.write('static const unsigned base_id=' + str(base_id) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('void ' + top_name + '(\n')
    top_file.write('		hls::stream<dataword>& in, \n')
    top_file.write('		hls::stream<dataword> out[' + str(num_op_code) + ']) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
    top_file.write('PacketDecoder<' + config_name + '>(in, out); \n')
    top_file.write('} \n')
    # header
    header_file.write('void ' + top_name + '(\n')
    header_file.write('		hls::stream<dataword>& in, \n')
    header_file.write('		hls::stream<dataword> out[' + str(num_op_code) + ']); \n')
    return


def comm_broadcast(header_file, top_file, param_file, top_name, id, num_children, children_id, virtual=False):
    config_name = 'config_t_broadcast_' + str(id)
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_CHILDREN=' + str(num_children) + ';\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('};' + '\n')
    # children id
    children_id_name = 'broadcast_children_id_' + str(id)
    param_file.write('const ap_uint<PACKET_DEST_LENGTH> ' + children_id_name + '[' + str(num_children) + ']={')
    for i in range(len(children_id)):
        if i == len(children_id)-1:
            param_file.write(str(children_id[i]))
        else:
            param_file.write(str(children_id[i]) + ', ')
    param_file.write('};\n')
    # top file
    top_file.write('void ' + top_name + '(\n')
    top_file.write('		hls::stream<dataword>& in, \n')
    top_file.write('		hls::stream<dataword>& out, \n')
    top_file.write('		hls::stream<dataword>& in_fifo, \n')
    top_file.write('		hls::stream<dataword>& out_fifo) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n#pragma HLS INTERFACE axis port=in_fifo\n#pragma HLS INTERFACE axis port=out_fifo\n')
    top_file.write('Bcast<' + config_name + '>(' + children_id_name + ', in, out, in_fifo, out_fifo); \n')
    top_file.write('} \n')
    # header
    header_file.write('void ' + top_name + '(\n')
    header_file.write('		hls::stream<dataword>& in, \n')
    header_file.write('		hls::stream<dataword>& out, \n')
    header_file.write('		hls::stream<dataword>& in_fifo, \n')
    header_file.write('		hls::stream<dataword>& out_fifo); \n')
    return

def comm_gather(header_file, top_file, param_file, top_name1, top_name2, id, num_children, dest, base_src, flit_num, virtual=False):
    config_name = 'config_t_gather_' + str(id)
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_CHILDREN=' + str(num_children) + ';\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned base_src=' + str(base_src) + ';\n')
    param_file.write('static const unsigned flit_num=' + str(flit_num) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('void ' + top_name1 + '(\n')
    top_file.write('		hls::stream<dataword>& in, \n')
    top_file.write('		hls::stream<dataword> out[' + str(num_children) + ']) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
    top_file.write('GatherRecv<' + config_name + '>(in, out); \n')
    top_file.write('} \n')
    top_file.write('void ' + top_name2 + '(\n')
    top_file.write('		hls::stream<dataword> in[' + str(num_children) + '], \n')
    top_file.write('		hls::stream<dataword> &out) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
    top_file.write('GatherSend<' + config_name + '>(in, out); \n')
    top_file.write('} \n')
    # header
    header_file.write('void ' + top_name1 + '(\n')
    header_file.write('		hls::stream<dataword>& in, \n')
    header_file.write('		hls::stream<dataword> out[' + str(num_children) + ']); \n')
    # header
    header_file.write('void ' + top_name2 + '(\n')
    header_file.write('		hls::stream<dataword> in[' + str(num_children) + '], \n')
    header_file.write('		hls::stream<dataword> &out); \n')
    return

def comm_scatter(header_file, top_file, param_file, top_name, id, flit_num, flit_num_last, num_node, num_children, children_id, virtual=False):
    config_name = 'config_t_scatter_' + str(id)
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned flit_num=' + str(flit_num) + ';\n')
    param_file.write('static const unsigned flit_num_last=' + str(flit_num_last) + ';\n')
    param_file.write('static const unsigned NUM_NODE=' + str(num_node) + ';\n')
    param_file.write('static const unsigned NUM_CHILDREN=' + str(num_children) + ';\n')
    param_file.write('};' + '\n')
    # children id
    children_id_name = 'scatter_children_id_' + str(id)
    param_file.write('const ap_uint<PACKET_DEST_LENGTH> ' + children_id_name + '[' + str(num_children) + ']={')
    for i in range(len(children_id)):
        if i == len(children_id)-1:
            param_file.write(str(children_id[i]))
        else:
            param_file.write(str(children_id[i]) + ', ')
    param_file.write('};\n')
    # top file
    top_file.write('void ' + top_name + '(\n')
    top_file.write('		hls::stream<dataword>& in, \n')
    top_file.write('		hls::stream<dataword>& out) \n')
    top_file.write('{ \n#pragma HLS interface ap_ctrl_none port=return \n#pragma HLS INTERFACE axis port=in\n#pragma HLS INTERFACE axis port=out\n')
    top_file.write('Scatter<' + config_name + '>(' + children_id_name + ', in, out); \n')
    top_file.write('} \n')
    # header
    header_file.write('void ' + top_name + '(\n')
    header_file.write('		hls::stream<dataword>& in, \n')
    header_file.write('		hls::stream<dataword>& out); \n')
    return