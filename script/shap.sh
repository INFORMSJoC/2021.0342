#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR=$BASE_DIR"/src"

# activate virtual environment
source $BASE_DIR/.venv/bin/activate

source_code=$SOURCE_DIR/script_shap.py

nblinacs=6
arrival_rate=9.0
DATA_DIR=$BASE_DIR"/data/"$nblinacs"linacs/lambda"$arrival_rate"/"

echo "base folder: "$DATA_DIR

folder_output=$BASE_DIR"/script/output/"$nblinacs"linacs/lambda"$arrival_rate"/"

python3 $source_code --base_folder $DATA_DIR --result_path $folder_output



