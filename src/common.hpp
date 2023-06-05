#ifndef COMMON_HPP
#define COMMON_HPP

#include "hls_stream.h"
#include <ap_int.h>
#include "ap_utils.h"



# define PACKET_DATA_LENGTH 512
# define PACKET_KEEP_LENGTH 64
# define PACKET_LAST
# define PACKET_USER_LENGTH 16
# define PACKET_DEST_LENGTH 8

#define BATCH_SIZE 1


struct dataword
{
	ap_uint<PACKET_DATA_LENGTH> data;
	ap_uint<PACKET_DEST_LENGTH> id;
	ap_uint<PACKET_DEST_LENGTH> dest;
	ap_uint<PACKET_USER_LENGTH> user;
	ap_uint<1> last;
};


enum PACKET_TYPE {BCAST=0, REDUCE, GATHER, SCATTER, BARRIER, SEND};
enum DATA_TYPE {INT_8=0, INT_16, INT_32, INT_64};
enum COMPUTE_TYPE {MATMUL=0, SOFTMAX, GELU};

#endif 
