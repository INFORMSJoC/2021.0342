#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR=$BASE_DIR"/src"

# activate virtual environment
source $BASE_DIR/.venv/bin/activate

# rerun = 0 to plot the existing results, 1 to rerun the whole experiment and plot the new results
rerun=0

source_code=$SOURCE_DIR/script_real_ins.py

DATA_DIR=$BASE_DIR"/data"

OUTPUT_DIR=$BASE_DIR"/script/output/real_ins"

python3 $source_code --rerun $rerun --ins_path $DATA_DIR --result_path $OUTPUT_DIR




