#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

BASE_DIR="$(dirname "$SCRIPT_DIR")"

SOURCE_DIR=$BASE_DIR"/src"

# activate virtual environment
source $BASE_DIR/.venv/bin/activate

source_code=$SOURCE_DIR/script_train_prediction_model.py

nblinacs=4
arrival_rate=5.0
DATA_DIR=$BASE_DIR"/data/"$nblinacs"linacs/lambda"$arrival_rate
echo "data folder: "$DATA_DIR

RESULT_DIR=$SCRIPT_DIR"/output/"$nblinacs"linacs/lambda"$arrival_rate

for n in "${nblinacs[@]}"
do
    echo "training prediction models with nblinacs = "$n
    python3 $source_code --base_folder $DATA_DIR --result_path $RESULT_DIR
done