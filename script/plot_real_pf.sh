#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR=$BASE_DIR"/src"

# activate virtual environment
source $BASE_DIR/.venv/bin/activate

source_code=$SOURCE_DIR/plot_patient_flow.py


DATA_DIR=$BASE_DIR"/data/"

folder_output=$BASE_DIR"/script/output/"

python3 $source_code --base_folder $DATA_DIR --result_path $folder_output



