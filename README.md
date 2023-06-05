# Galapagos_Cluster_Builder
An automation tool for building Transformers on muli-FPGAs. In the example, we use I-BERT as our test model.

## Pre-requests
- Galapagos Hardware Stack Installed. [GitHub Pages]([https://pages.github.com/](https://github.com/UofT-HPRC/galapagos/tree/yugao))
- Xilinx Vivado & Xilinx Vivado_HLS Installed. Current versions supported are 2018.3, 2019.1

## Setup
First you need to change the JSON file for different HLS IP core configurations.

Then creating kernel files.

`python3 setup.py`

Next, build HLS IP cores for each kernel.

`source build.sh`

Finally, copy the `Kern` directory to the `galapagos/userIP/ip_repo`.

## File Description
This section introduces the JSON file used to setup kernel configurations, Galapagos cluster configurations, and Layer configurations for I-BERT.
### config.json
```
"num_build_thread": 48,
"max_sentence_len": 128,
"hidden_size": 768,
"num_hidden_layers": 12,
"num_attention_heads": 12,
"intermediate_size": 3072,
"num_layer_per_encoder": 8,
"cluster": [["attention_0", "attention_1", "attention_2", "attention_output_0", "attention_output_1", "intermediate_0", "intermediate_output_0", "intermediate_output_1"]],

"attention_0": 
{
	"partition": 1,
	"part": "xczu19eg-ffvc1760-2-i",
	"board": "sidewinder",
	"config": 
	[
		{
			"name": "linear",
			"cluster": 0,
			"dim": 
			{
				"M": 768,
				"K": 768,
				"tile": 2,
				"pe": 6
			}
		},
		{
			"name": "act",
			"dim": 
			{
				"unroll": 4
			}
		}
	]
},

...

```

`num_build_thread` describes how many CPU threads used to build HLS IP cores.
`max_sentence_len` describes the Transformer sentence length.
`hidden_size` describes the Transformer hidden state size.
`num_hidden_layers` describes the Transformer number of encoder layers.
`num_attention_heads` describes the Transformer number of attention heads.
`intermediate_size` describes the Transformer intermediate size.
`num_layer_per_encoder` describes the Transformer number of layers within each encoder.
`cluster` describes the grouping of Galapgos clusters. In this example, the eight layers are grouped into one cluster.
`attention_0` describes the configuration of layer `attention_0`, including the FPGA used, and the kernels within the layer.
`linear` describes the linear kernel configurations.
`act` describes the quantization kernel configurations.


