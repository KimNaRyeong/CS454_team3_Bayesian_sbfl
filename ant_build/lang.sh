#!/bin/bash

# 실패한 프로젝트를 저장할 배열
failed_projects=()

for i in $(seq 1 40); do
    dir="checkout/Lang_$i"

    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"

        cd "$dir"

        build_log=$(mktemp)
        ant -f build.xml jar | tee "$build_log"
        exit_code=${PIPESTATUS[0]}  # Ant 명령의 종료 상태 코드 저장

        # 실패 조건 확인 (Ant 종료 코드 및 로그에 "BUILD FAILED" 포함 여부)
        if [[ $exit_code -ne 0 ]] || grep -q "BUILD FAILED" "$build_log"; then
            failed_projects+=("$dir")
        fi

        rm -f "$build_log"

        cd - > /dev/null
    else
        echo "Directory $dir does not exist. Skipping."
    fi

    echo "======================================================================================="
done

# 실패한 프로젝트 출력
if [ "${#failed_projects[@]}" -ne 0 ]; then
    echo "The following projects failed to build:"
    for project in "${failed_projects[@]}"; do
        echo "$project"
    done
else
    echo "All projects built successfully."
fi