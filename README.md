# SBFL via Bayesian Network - 동한, 지훈
pass

# Generate Call Graph - 나령, 선우
## Get checkout and build data
* There are two methods to get data
### 1. Download all at once
https://drive.google.com/drive/folders/1fSPvBw2tb71Q7yxI_5eHW7SrctnW48gC?usp=sharing   

`tar -xvf checkout.tar`

### 2. checkout and compile directly on the docker
* Docker  
    In working directory
    * Window
        ```
        docker pull agb94/fonte:latest
        dokcer run -it -v "$(Get-Location):/root/workspace/" agb94/fonte:latest bash"
        ```
    * Linux
        ```
        docker pull agb94/fonte:latest
        dokcer run -it -v $(pwd):/root/workspace/ agb94/fonte:latest bash"
        ```
    
* Run Defects4J   
    ```python checkout_and_compile.py```

### 3. Generate `.jar` files using 'ant'
***jar files for Chart are available now. They are in jar_files directory. Below explanation is about how to make that directory.***
* Download ant on the docker
    ```
    apt-get update
    apt install ant
    ```
* Run the each shell script in ant_build directory for each project   
    * Example
        ```
        bash ant_build/chart.sh
        ```
* Copy the jar files of source to jar_files directory
    * Example
        ```
        python copy_jar_files/chart.py
        ```
    * Chart
        * All jar files are in lib directory of each project directory


