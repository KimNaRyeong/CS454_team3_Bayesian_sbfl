#!/bin/bash

for i in $(seq 1 20); do
    dir="checkout/Chart_$i"

    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"

        cd "$dir"

        build_log=$(mktemp)
        ant -f ant/build.xml compile > "$build_log" 2>&1

        jar_file=$(grep '\[jar\] Building jar:' "$build_log" | awk -F': ' '{print $2}' | xargs)

        if [ -f "$jar_file" ]; then
            mkdir -p lib 
            cp "$jar_file" lib/
            echo "Copied $(basename "$jar_file") to lib/ directory"
        else
            echo "JAR file not found in $dir. Skipping."
        fi

        rm -f "$build_log"

        cd - > /dev/null
    else
        echo "Directory $dir does not exist. Skipping."
    fi

    echo "======================================================================================="
done