#!/bin/bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
echo $SCRIPT_DIR

BASE_DIR="$(dirname "$SCRIPT_DIR")"
echo $BASE_DIR

SOURCE_DIR=$BASE_DIR"/src"
echo $SOURCE_DIR

# activate virtual environment
source $SOURCE_DIR/.venv/bin/activate

source_code=$SOURCE_DIR/script_capacity_sim.py

declare -a nblinacs=(4 6 8)

for n in "${nblinacs[@]}"
do
    echo "running capacity simulation with nblinacs = "$n
    python3 $source_code --nblinacs $n --base_folder $BASE_DIR
done