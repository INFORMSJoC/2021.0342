#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
BASE_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR=$BASE_DIR"/src"

# activate virtual environment
source $BASE_DIR/.venv/bin/activate

rerun=0
nblinacs=8
arrival_rate=10.0

INS_BASE_DIR=$BASE_DIR"/data/"$nblinacs"linacs/lambda"$arrival_rate
DATA_DIR=$INS_BASE_DIR"/data"
l_instances=$INS_BASE_DIR"/listInstances.txt"
echo "data folder: "$DATA_DIR
OUTPUT_DIR=$BASE_DIR"/script/output/"$nblinacs"linacs/lambda"$arrival_rate

if [ "$rerun" == "1" ]; then
  source_code=$SOURCE_DIR/main.py

  folder_result=$INS_BASE_DIR"/output/results"

  declare -a solver=("greedy" "daily_greedy" "online_prediction" "daily" "weekly" )
  timeout=3600

  n=0
  while read insname; do
    # if [ $n -le 1 ]; then
    if [ `expr $n % 5` -eq 0 ]; then
      echo "processing $n th instance $insname"

      for s in "${solver[@]}"
      do
        echo "solving $s - instance $insname"
        res_file="$folder_result/$insname-$s.out"
        
        python3 $source_code --mode server --solver $s --timeout $timeout --ins_path $DATA_DIR --ins_name $insname --result_path $folder_result

      done
    fi
    n=$(($n+1))
  done <$l_instances
fi

# finish running simulation, plot results
source_code=$SOURCE_DIR/visualization.py
python3 $source_code --ins_path $INS_BASE_DIR --result_path $OUTPUT_DIR
