# UIUC Information Extraction Pipeline (Patched)
One single script to run text information extraction, including fine-grained entity extraction, relation extraction and event extraction.

This is forked from [the original repository](https://github.com/limanling/uiuc_ie_pipeline_fine_grained), see documentation there for additional details.

### Changelog
- 2020-12-04: Fixed an issue with hardcoded GPU parameters to let the script run on single GPU devices.

## Requirements
Docker (Please do not set up UIUC IE Pipeline in a NAS, as the EDL needs MongoDB, which may lead to permission issues in a NAS.)

## Quick Start

### Running on raw text data
* Prepare a data directory `data` containing sub-directories `rsd` and `ltf`. The `rsd` sub-directory contains RSD (Raw Source Data, ending with `*.rsd.txt`), and `ltf` sub-directory has LTF (Logical Text Format, ending with `*.ltf.xml`) files. 
	* If you have RSD files, please use the [`aida_utilities/rsd2ltf.py`](https://github.com/limanling/uiuc_ie_pipeline_finegrained_source_code/blob/master/aida_utilities/rsd2ltf.py) to generate the LTF files. 
  ```bash
  docker run --rm -v ${ltf_dir}:${ltf_dir} -v ${rsd_dir}:${rsd_dir} -i limanling/uiuc_ie_m36 /opt/conda/envs/py36/bin/python /aida_utilities/rsd2ltf.py --seg_option nltk+linebreak --tok_option nltk_wordpunct --extension .rsd.txt ${rsd_dir} ${ltf_dir}
  ```
	* If you have LTF files, please use the AIDA ltf2rsd tool (`LDC2018E62_AIDA_Month_9_Pilot_Eval_Corpus_V1.0/tools/ltf2txt/ltf2rsd.perl`) to generate the RSD files. 
* Start services
```bash
sh set_up_m36.sh
```
* Run the scripts. Note that the file paths are absolute paths.   
```bash
sh pipeline_full_en.sh ${data_root}
```
For example, 
```bash
sh pipeline_full_en.sh ${PWD}/data/testdata_dryrun
```

## Source Code

Please find source code in https://github.com/limanling/uiuc_ie_pipeline_finegrained_source_code.

## References
```
@inproceedings{li2020gaia,
  title={GAIA: A Fine-grained Multimedia Knowledge Extraction System},
  author={Li, Manling and Zareian, Alireza and Lin, Ying and Pan, Xiaoman and Whitehead, Spencer and Chen, Brian and Wu, Bo and Ji, Heng and Chang, Shih-Fu and Voss, Clare and others},
  booktitle={Proceedings of the 58th Annual Meeting of the Association for Computational Linguistics: System Demonstrations},
  pages={77--86},
  year={2020}
}
```

