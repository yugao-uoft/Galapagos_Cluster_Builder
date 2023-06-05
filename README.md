# Galapagos_Cluster_Builder
An automation tool for building Transformers on muli-FPGAs. In the example, we use I-BERT as our test model.

## Pre-requests
```
Galapagos Hardware Stack Installed. [GitHub Pages]([https://pages.github.com/](https://github.com/UofT-HPRC/galapagos/tree/yugao))
Xilinx Vivado & Xilinx Vivado_HLS Installed. Current versions supported are 2018.3, 2019.1
```
## Setup
First you need to change the JSON file for different HLS IP core configurations.

Then creating kernel files.

`python3 setup.py`

Next, build HLS IP cores for each kernel.

`source build.sh`

Finally, copy the `Kern` directory to the `galapagos/userIP/ip_repo`.

## File Description
This section introduces the JSON file used to setup kernel configurations, Galapagos cluster configurations, and Layer configurations for I-BERT.
### CONFIG.JSON
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
	"attention_1": 
	{
		"partition": 1,
		"part": "xczu19eg-ffvc1760-2-i",
		"board": "sidewinder",
		"config": 
		[
			{
				"name": "attention_matmul",
				"dim": 
				{
					"pe": 2
				}
			},
			{
				"name": "softmax",
				"dim": 
				{
					"unroll": 2
				}
			}
		]
	},
	"attention_2": 
	{
		"partition": 1,
		"part": "xczu19eg-ffvc1760-2-i",
		"board": "sidewinder",
		"config": 
		[
			{
				"name": "softmax_matmul",
				"dim": 
				{
					"pe": 2
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
	"attention_output_0":
	{
		"partition": 1,
		"part": "xczu19eg-ffvc1760-2-i",
		"board": "sidewinder",
		"config": 
		[
			{
				"name": "linear",
				"dim": 
				{
					"M": 768,
					"K": 768,
					"tile": 4,
					"pe": 12
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
	"attention_output_1":
	{
		"partition": 1,
		"part": "xczu19eg-ffvc1760-2-i",
		"board": "sidewinder",
		"config": 
		[
			{
				"name": "layernorm",
				"dim": 
				{
					"unroll": 16
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
	"intermediate_0":
	{
		"partition": 1,
		"part": "xczu19eg-ffvc1760-2-i",
		"board": "sidewinder",
		"config": 
		[
			{
				"name": "linear",
				"dim": 
				{
					"M": 3072,
					"K": 768,
					"tile": 4,
					"pe": 12
				}
			},
			{
				"name": "gelu",
				"dim": 
				{
					"unroll": 4
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
	"intermediate_output_0":
	{
		"partition": 1,
		"part": "xczu19eg-ffvc1760-2-i",
		"board": "sidewinder",
		"config": 
		[
			{
				"name": "linear",
				"dim": 
				{
					"M": 768,
					"K": 3072,
					"tile": 4,
					"pe": 12
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
	"intermediate_output_1":
	{
		"partition": 1,
		"part": "xczu19eg-ffvc1760-2-i",
		"board": "sidewinder",
		"config": 
		[
			{
				"name": "layernorm",
				"dim": 
				{
					"unroll": 4
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
	}
```
