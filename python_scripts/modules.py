import numpy as np

# generate matmul src files
def linear(in_weight_file, in_bias_file, top_file, param_file, weight_file, config_name, in_port, out_port, id, dest, M=768, K=768, T=2, P=12, index_M=0, index_K=0):
    # read data
    weight = []
    for line in in_weight_file.readlines():
        weight = weight + line.split()
    weight = list(map(int, weight))
    bias = []
    for line in in_bias_file.readlines():
        bias = bias + line.split()
    bias = list(map(int, bias))
    # scaling factor
    S = 4
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned M=' + str(M) + ';\n')
    param_file.write('static const unsigned K=' + str(K) + ';\n')
    param_file.write('static const unsigned NUM_TILE=' + str(T) + ';\n')
    param_file.write('static const unsigned NUM_PE=' + str(P) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=8' + ';\n')
    param_file.write('static const unsigned OUT_DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned SCALE_FACTOR=4' + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned OUT_VEC_WIDTH=BUS_WIDTH/OUT_DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned ITER_PE=K/(NUM_PE * VEC_WIDTH)' + ';\n')
    param_file.write('};' + '\n')
    # set dim
    I = int(K / (P * 64))
    b_cols = np.array([0]*int(M*K), dtype=np.uint8)
    b = np.array([[[[0]*int(128/S) ]*int(M*I/T) ]*P ]*int(T/2), dtype=np.uint64)
    temp = np.uint64(0)
    temp1 = np.uint64(0)
    for i in range(M):
        for j in range(K):
            b_cols[j + i * K] = weight[j + index_K + (i + index_M) * K]
    bias2d = np.array([[0]*16]*int(M/16), dtype=np.int32)
    for i in range(int(M/16)):
        for j in range(16):
            bias2d[i][j] = bias[i * 16 + index_M + j]
    # create bias
    weight_file.write('#define LINEAR_BIAS_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(M/16)):
        weight_file.write('{ ')
        for j in range(16):
            if j == 15:
                weight_file.write(str(bias2d[i][j]))
            else:
                weight_file.write(str(bias2d[i][j]) + ', ')
        if i == int(M/16) - 1:
            weight_file.write(' } ')
        else:
            weight_file.write(' }, ')
    weight_file.write(' };\n')
    # create weights
    cnt=0
    for i in range(int(M / T)):
        for j in range(int(T / 2)):
            for p in range(2):
                for k in range(P):
                    for m in range(I):
                        for w in range(int(64/S)):
                            temp1 = 0
                            for s in range(S):
                                temp = b_cols[cnt] << (s*8)
                                temp1 = temp1 + temp
                                cnt+=1;
                            b[j][k][int(i*I+m)][int(w+p*int(64/S))] = temp1
    # write to file
    weight_file.write('#define LINEAR_WEIGHTS_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(T / 2)):
        weight_file.write('{ ')
        for j in range(P):
            weight_file.write('{ ')
            for k in range(int(M * I / T)):
                weight_file.write('{ ')
                for w in range(int(64 * 2 / S)):
                    if w == int(64  * 2 / S - 1):
                        weight_file.write(str(b[i][j][k][w]))
                    else:
                        weight_file.write(str(b[i][j][k][w]) + ', ')
                if k == int(M * I / T - 1):
                    weight_file.write(' } ')
                else:
                    weight_file.write(' }, ')
            if j == P - 1:
                weight_file.write(' } ')
            else:
                weight_file.write(' }, ')
        if i == int(T / 2 - 1):
            weight_file.write(' } ')
        else:
            weight_file.write(' }, ')
    weight_file.write(' };\n')
    # top file
    top_file.write('const ap_uint<' + str(int(8*S)) + '> weights[' + str(int(T / 2)) + '][' + str(int(P)) + '][' + str(int(M * I / T)) + '][' + str(int(128/S)) + '] = LINEAR_WEIGHTS_' + str(id) + ';\n')
    top_file.write('const ap_int<32> bias[' + str(int(M/16)) + '][' + str(int(16)) + '] = LINEAR_BIAS_' + str(id) + ';\n')
    top_file.write('Linear<' + config_name + '>(weights, bias, ' + in_port + ', ' + out_port + '); \n')
    return


# skew
def skew(top_file, param_file, config_name, num_packet_per_row, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_PACKET=' + str(num_packet_per_row) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('Skew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# GMI skew
def GMI_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_PACKET=' + str(num_packet_per_row) + ';\n')
    param_file.write('static const unsigned virtual_dest=' + str(virtual_dest) + ';\n')
    param_file.write('static const unsigned dest=' + str(new_dest) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('GMISkew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# linear de-skew
def linear_deskew(top_file, param_file, config_name, num_packet_per_row, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_PACKET=' + str(num_packet_per_row) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('LinearDeskew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# linear skew
def linear_skew(top_file, param_file, config_name, num_packet_per_row, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_PACKET=' + str(num_packet_per_row) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('LinearSkew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# GMI linear skew
def GMI_linear_skew(top_file, param_file, config_name, num_packet_per_row, virtual_dest, new_dest, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned NUM_PACKET=' + str(num_packet_per_row) + ';\n')
    param_file.write('static const unsigned virtual_dest=' + str(virtual_dest) + ';\n')
    param_file.write('static const unsigned dest=' + str(new_dest) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('GMILinearSkew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# generate act src files
def act(in_m_file, in_e_file, top_file, param_file, weight_file, config_name, in_port, out_port, id, dest, channel=768, unroll_factor=16, index=0, in_data_width=32, out_data_width=8, identity=False):
    # read data
    m = []
    for line in in_m_file.readlines():
        m = m + line.split()
    m = list(map(int, m))
    if len(m) == 1:
        m = [m[0]] * channel
    # e
    e = []
    for line in in_e_file.readlines():
        e = e + line.split()
    e = list(map(int, e))
    if len(e) == 1:
        e = [e[0]] * channel
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned NUM_CHANNEL=' + str(channel) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=' + str(in_data_width) + ';\n')
    param_file.write('static const unsigned OUT_DATA_WIDTH=' + str(out_data_width) + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned OUT_VEC_WIDTH=BUS_WIDTH/OUT_DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned UNROLL_FACTOR=' + str(unroll_factor) + ';\n')
    param_file.write('};' + '\n')
    # unroll factor
    if identity == True:
        unroll = 64
    else:
        unroll = 16
    # convert dim
    m2d = np.array([[0]*unroll]*int(channel/unroll), dtype=np.int32)
    for i in range(int(channel/unroll)):
        for j in range(unroll):
            m2d[i][j] = m[index + i * unroll + j]
    e2d = np.array([[0]*unroll]*int(channel/unroll), dtype=np.int32)
    for i in range(int(channel/unroll)):
        for j in range(unroll):
            e2d[i][j] = e[index + i * unroll + j]
    # create m
    if identity == True:
        weight_file.write('#define IDENTITY_ACT_M_' + str(id) + ' \\' + '\n')
    else:
        weight_file.write('#define ACT_M_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(channel/unroll)):
        weight_file.write('{ ')
        for j in range(unroll):
            if j == unroll-1:
                weight_file.write(str(m2d[i][j]))
            else:
                weight_file.write(str(m2d[i][j]) + ', ')
        if i == int(channel/unroll) - 1:
            weight_file.write(' } ')
        else:
            weight_file.write(' }, ')
    weight_file.write(' };\n')
    # create e
    if identity == True:
        weight_file.write('#define IDENTITY_ACT_E_' + str(id) + ' \\' + '\n')
    else:
        weight_file.write('#define ACT_E_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(channel/unroll)):
        weight_file.write('{ ')
        for j in range(unroll):
            if j == unroll-1:
                weight_file.write(str(e2d[i][j]))
            else:
                weight_file.write(str(e2d[i][j]) + ', ')
        if i == int(channel/unroll) - 1:
            weight_file.write(' } ')
        else:
            weight_file.write(' }, ')
    weight_file.write(' };\n')
    # top file
    if identity == True:
        top_file.write('const ap_int<32> identity_m[' + str(int(channel/unroll)) + '][' + str(int(unroll)) + '] = IDENTITY_ACT_M_' + str(id) + ';\n')
        top_file.write('const ap_int<32> identity_e[' + str(int(channel/unroll)) + '][' + str(int(unroll)) + '] = IDENTITY_ACT_E_' + str(id) + ';\n')
        top_file.write('IdentityQuantAct<' + config_name + '>(identity_m, identity_e, ' + in_port + ', ' + out_port + '); \n')
    else:
        top_file.write('const ap_int<32> m[' + str(int(channel/unroll)) + '][' + str(int(unroll)) + '] = ACT_M_' + str(id) + ';\n')
        top_file.write('const ap_int<32> e[' + str(int(channel/unroll)) + '][' + str(int(unroll)) + '] = ACT_E_' + str(id) + ';\n')
        top_file.write('QuantAct<' + config_name + '>(m, e, ' + in_port + ', ' + out_port + '); \n')
    return

# 2 port arbiter
def arbiter_2_port(top_file, param_file, config_name, src_id_1, src_id_2, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned src_1=' + str(src_id_1) + ';\n')
    param_file.write('static const unsigned src_2=' + str(src_id_2) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('Arbiter<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# generate attention_matmul src files
def attention_matmul(top_file, param_file, config_name, max_sentence_len, in_port1, in_port2, out_port, id, dest, M=64, P=2):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned M=' + str(M) + ';\n')
    param_file.write('static const unsigned NUM_PE=' + str(P) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=8' + ';\n')
    param_file.write('static const unsigned OUT_DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned OUT_VEC_WIDTH=BUS_WIDTH/OUT_DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned MAX_SEQUENCE_LEN=' + str(max_sentence_len) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('AttentionMatmul<' + config_name + '>(' + in_port1 + ', ' + in_port2 + ', ' + out_port + '); \n')
    return

# attention de-skew
def attention_deskew(top_file, param_file, config_name, MAX_FLIT_NUM, data_width, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned MAX_FLIT_NUM=' + str(MAX_FLIT_NUM) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=' + str(data_width) + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('AttentionDeskew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# attention skew
def attention_skew(top_file, param_file, config_name, MAX_FLIT_NUM, data_width, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned MAX_FLIT_NUM=' + str(MAX_FLIT_NUM) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=' + str(data_width) + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('AttentionSkew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# GMI attention skew
def GMI_attention_skew(top_file, param_file, config_name, MAX_FLIT_NUM, data_width, virtual_dest, new_dest, in_port, out_port):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned virtual_dest=' + str(virtual_dest) + ';\n')
    param_file.write('static const unsigned dest=' + str(new_dest) + ';\n')
    param_file.write('static const unsigned MAX_FLIT_NUM=' + str(MAX_FLIT_NUM) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=' + str(data_width) + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('GMIAttentionSkew<' + config_name + '>(' + in_port + ', ' + out_port + '); \n')
    return

# generate softmax src files
def softmax(in_const_file, in_x0_file, in_b_file, in_c_file, in_m_file, in_e_file, top_file, param_file, weight_file, config_name, max_sentence_len, in_port, out_port, id, dest, unroll):
    # read data
    const = int(in_const_file.read())
    x0 = int(in_x0_file.read())
    b = int(in_b_file.read())
    c = int(in_c_file.read())
    m = int(in_m_file.read())
    e = int(in_e_file.read())
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned NUM_CHANNEL=' + str(max_sentence_len) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned OUT_DATA_WIDTH=8' + ';\n')
    param_file.write('static const unsigned QUANT_DATA_WIDTH=16' + ';\n')
    param_file.write('static const unsigned UNROLL_FACTOR=' + str(unroll) + ';\n')
    param_file.write('static const unsigned MAX_SEQUENCE_LEN=' + str(max_sentence_len) + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned OUT_VEC_WIDTH=BUS_WIDTH/OUT_DATA_WIDTH' + ';\n')
    param_file.write('};' + '\n')
    weight_file.write('#define SOFTMAX_CONST_' + str(id) + ' ' + str(const) + '\n')
    weight_file.write('#define SOFTMAX_X0_' + str(id) + ' ' + str(x0) + '\n')
    weight_file.write('#define SOFTMAX_B_' + str(id) + ' ' + str(b) + '\n')
    weight_file.write('#define SOFTMAX_C_' + str(id) + ' ' + str(c) + '\n')
    weight_file.write('#define SOFTMAX_M_' + str(id) + ' ' + str(m) + '\n')
    weight_file.write('#define SOFTMAX_E_' + str(id) + ' ' + str(e) + '\n')
    # top file
    top_file.write('const ap_int<32> self_const=SOFTMAX_CONST_' + str(id) + ';\n')
    top_file.write('const ap_int<32> x0=SOFTMAX_X0_' + str(id) + ';\n')
    top_file.write('const ap_int<32> b=SOFTMAX_B_' + str(id) + ';\n')
    top_file.write('const ap_int<32> c=SOFTMAX_C_' + str(id) + ';\n')
    top_file.write('const ap_int<32> m=SOFTMAX_M_' + str(id) + ';\n')
    top_file.write('const ap_int<16> e=SOFTMAX_E_' + str(id) + ';\n')
    top_file.write('Softmax<' + config_name + '>(self_const, x0, b, c, m, e, ' + in_port + ', ' + out_port + '); \n')
    return

# generate softmax_matmul src files
def softmax_matmul(top_file, param_file, config_name, max_sentence_len, in_port1, in_port2,  out_port, id, dest, M=64, P=2):
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned M=' + str(M) + ';\n')
    param_file.write('static const unsigned NUM_PE=' + str(P) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=8' + ';\n')
    param_file.write('static const unsigned OUT_DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned OUT_VEC_WIDTH=BUS_WIDTH/OUT_DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned MAX_SEQUENCE_LEN=' + str(max_sentence_len) + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('SoftmaxMatmul<' + config_name + '>(' + in_port1 + ', ' + in_port2 + ', ' + out_port + '); \n')
    return

def identity_add(top_file, param_file, config_name, in_port1, in_port2, out_port, id, dest, K=768):
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned K=' + str(K) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('};' + '\n')
    # top file
    top_file.write('IdentityAdd<' + config_name + '>(' + in_port1 + ', ' + in_port2 + ', ' + out_port + '); \n')
    return

# generate layernorm src files
def layernorm(in_shift_file, in_bias_file, top_file, param_file, weight_file, config_name, in_port, out_port, id, dest, channel=768, unroll=16):
    # read data
    shift = int(in_shift_file.read())
    bias = []
    for line in in_bias_file.readlines():
        bias = bias + line.split()
    bias = list(map(int, bias))
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned NUM_CHANNEL=' + str(channel) + ';\n')
    param_file.write('static const unsigned LOG_NUM_CHANNEL=' + str(int(np.log2(channel))) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned IM_DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned UNROLL_FACTOR=' + str(unroll) + ';\n')
    param_file.write('static const unsigned shift=' + str(shift) + ';\n')
    param_file.write('};' + '\n')
    # create bias
    weight_file.write('#define LAYERNORM_BIAS_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(channel)):
        if i == int(channel) - 1:
            weight_file.write(str(bias[i]))
        else:
            weight_file.write(str(bias[i]) + ', ')
    weight_file.write(' };\n')
    # top file
    top_file.write('const ap_int<32> bias[' + str(int(channel)) + '] = LAYERNORM_BIAS_' + str(id) + ';\n')
    top_file.write('LayerNorm<' + config_name + '>(bias, ' + in_port + ', ' + out_port + '); \n')
    return

# generate gelu src files
def gelu(in_b_file, in_c_file, in_shift_file, in_const_file, top_file, param_file, weight_file, config_name, in_port, out_port, id, dest, channel=3072, index=0):
    # read data
    const = int(in_const_file.read())
    b = []
    for line in in_b_file.readlines():
        b = b + line.split()
    b = list(map(int, b))
    c = []
    for line in in_c_file.readlines():
        c = c + line.split()
    c = list(map(int, c))
    shift = []
    for line in in_shift_file.readlines():
        shift = shift + line.split()
    shift = list(map(int, shift))
    # params
    param_file.write('struct ')
    param_file.write(config_name + '\n')
    param_file.write('{' + '\n')
    param_file.write('static const unsigned id=' + str(id) + ';\n')
    param_file.write('static const unsigned dest=' + str(dest) + ';\n')
    param_file.write('static const unsigned NUM_CHANNEL=' + str(channel) + ';\n')
    param_file.write('static const unsigned BUS_WIDTH=512' + ';\n')
    param_file.write('static const unsigned DATA_WIDTH=32' + ';\n')
    param_file.write('static const unsigned VEC_WIDTH=BUS_WIDTH/DATA_WIDTH' + ';\n')
    param_file.write('static const unsigned UNROLL_FACTOR=NUM_CHANNEL/VEC_WIDTH' + ';\n')
    param_file.write('static const unsigned self_const=' + str(const) + ';\n')
    param_file.write('};' + '\n')
    # convert dim
    b2d = np.array([[0]*16]*int(channel/16), dtype=np.int32)
    for i in range(int(channel/16)):
        for j in range(16):
            b2d[i][j] = b[index + i * 16 + j]
    c2d = np.array([[0]*16]*int(channel/16), dtype=np.int32)
    for i in range(int(channel/16)):
        for j in range(16):
            c2d[i][j] = c[index + i * 16 + j]
    shift2d = np.array([[0]*16]*int(channel/16), dtype=np.int32)
    for i in range(int(channel/16)):
        for j in range(16):
            shift2d[i][j] = shift[index + i * 16 + j]
    # create bias
    weight_file.write('#define GELU_B_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(channel/16)):
        weight_file.write('{ ')
        for j in range(16):
            if j == 15:
                weight_file.write(str(b2d[i][j]))
            else:
                weight_file.write(str(b2d[i][j]) + ', ')
        if i == int(channel/16) - 1:
            weight_file.write(' } ')
        else:
            weight_file.write(' }, ')
    weight_file.write(' };\n')
    # c
    weight_file.write('#define GELU_C_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(channel/16)):
        weight_file.write('{ ')
        for j in range(16):
            if j == 15:
                weight_file.write(str(c2d[i][j]))
            else:
                weight_file.write(str(c2d[i][j]) + ', ')
        if i == int(channel/16) - 1:
            weight_file.write(' } ')
        else:
            weight_file.write(' }, ')
    weight_file.write(' };\n')
    # shift
    weight_file.write('#define GELU_SHIFT_' + str(id) + ' \\' + '\n')
    weight_file.write('{ ')
    for i in range(int(channel/16)):
        weight_file.write('{ ')
        for j in range(16):
            if j == 15:
                weight_file.write(str(shift2d[i][j]))
            else:
                weight_file.write(str(shift2d[i][j]) + ', ')
        if i == int(channel/16) - 1:
            weight_file.write(' } ')
        else:
            weight_file.write(' }, ')
    weight_file.write(' };\n')
    # top file
    top_file.write('const ap_int<32> b[' + str(int(channel/16)) + '][' + str(int(16)) + '] = GELU_B_' + str(id) + ';\n')
    top_file.write('const ap_int<32> c[' + str(int(channel/16)) + '][' + str(int(16)) + '] = GELU_C_' + str(id) + ';\n')
    top_file.write('const ap_int<32> shift[' + str(int(channel/16)) + '][' + str(int(16)) + '] = GELU_SHIFT_' + str(id) + ';\n')
    top_file.write('Gelu<' + config_name + '>(b, c, shift, ' + in_port + ', ' + out_port + '); \n')
    return