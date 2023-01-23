#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR=$BASE_DIR"/src"

# activate virtual environment
source $BASE_DIR/.venv/bin/activate

source_code=$SOURCE_DIR/script_tuning.py

# rerun = 0 to plot the existing results, 1 to rerun the whole experiment and plot the new results
rerun=1

nblinacs=4
arrival_rate=6.0
DATA_DIR=$BASE_DIR"/data/"$nblinacs"linacs/lambda"$arrival_rate"/"

echo "base folder: "$DATA_DIR

folder_output=$BASE_DIR"/script/output/tuning"

python3 $source_code --base_folder $DATA_DIR --rerun $rerun --result_path $folder_output



