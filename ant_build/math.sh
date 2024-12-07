#!/bin/bash

# JUnit 버전과 URL 설정
JUNIT_VERSION="4.8.2"
JUNIT_URL="https://repo1.maven.org/maven2/junit/junit/${JUNIT_VERSION}/junit-${JUNIT_VERSION}.jar"

# 반복문: Math_1에서 Math_50까지
for i in $(seq 1 50); do
    dir="checkout/Math_$i"

    if [ -d "$dir" ]; then
        echo "Processing directory: $dir"

        # 1. JUnit 다운로드
        junit_path="$dir/lib/junit-${JUNIT_VERSION}.jar"
        mkdir -p "$dir/lib"
        if [ ! -f "$junit_path" ]; then
            echo "Downloading JUnit for $dir..."
            wget -O "$junit_path" "$JUNIT_URL"
        else
            echo "JUnit already exists for $dir."
        fi

        # 2. build.xml 수정
        build_file="$dir/build.xml"
        if [ -f "$build_file" ]; then
            echo "Modifying build.xml in $dir..."

            # JUnit 경로를 `build.xml`에 추가
            sed -i "s|<property name=\"junit.jar\" value=\".*\"/>|<property name=\"junit.jar\" value=\"lib/junit-${JUNIT_VERSION}.jar\"/>|" "$build_file"

            # HTTPS URL로 변경
            sed -i "s|http://repo1.maven.org/maven2/junit/junit/${JUNIT_VERSION}/junit-${JUNIT_VERSION}.jar|${JUNIT_URL}|" "$build_file"

            # 테스트 실패 중단 방지
            sed -i "s|<property name=\"test.failonerror\" value=\"true\"/>|<property name=\"test.failonerror\" value=\"false\"/>|" "$build_file"
        else
            echo "build.xml not found in $dir. Skipping modification."
            continue
        fi

        # 3. Ant 빌드 실행
        echo "Running Ant build in $dir..."
        ant -f "$build_file" jar -Dtest.failonerror=false
        echo "======================================================================================="
    else
        echo "Directory $dir does not exist. Skipping."
    fi
done

echo "Processing completed!"
