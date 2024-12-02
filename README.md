# SBFL via Bayesian Network - 동한, 지훈
pass

# Generate Call Graph - 나령, 선우
## Get checkout and build data
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


