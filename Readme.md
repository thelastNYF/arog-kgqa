# ARoG: Abstraction Reasoning on Graph

## 🚀 Overview
This repository contains the official implementation for the paper **"Privacy-protected Retrieval-Augmented Generation for Knowledge Graphs Question Answering"**.
![Project Structure Screenshot](model.png)

## 📂 Repository Structure

```
ARoG-main/
├── 📁 CoT/               # IO, CoT, CoT-SC Baselines 
├── 📁 data/              # Dataset files 
├── 📁 evaluation/        # Evaluation scripts and files
├── 📁 Freebase/          # Freebase Setup
│
├── 📄 freebase_func.py     # KG Search
├── 📄 lm_server.py         # Call for SentenceTransformer
├── 📄 main_freebase.py     # Main execution script
├── 📄 model.png            # Model picture
├── 📄 prompt_list.py       # Prompts used
├── 📄 README.md            # This documentation
├── 📄 requirements.py      # Requirements
└── 📄 utils.py             # Utility functions
```
## ⚙️ Create a conda environment and install dependencies:

```
conda create -n ARoG-envior python=3.10
conda activate ARoG-envior
pip install -r requirements.txt
```

## 📥 Setup Freebase and SentenceTransformer
```
See Freebase/README.md
```
```
python lm_server.py
```

## 🚀 Execution Steps
### 1. Retrieve-then-Generate
```
python main_freebase.py  --dataset webqsp --width 3 --depth 3
```
### 2. Evaluation
```
python evaluation/eval_arog/eval.py --dataset webqsp --output_file ARoG_0710_naive_1_webqsp_True_True_depth_3_width_3_total.json
```