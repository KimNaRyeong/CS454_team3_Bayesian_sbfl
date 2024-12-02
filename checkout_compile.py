import os
import subprocess

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
    except subprocess.CalledProcessError as e:
        print("Error:", e)
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)

def make_info_command(pid):
    info_pre = "defects4j info -p "+pid
    return info_pre

def make_checkout_command(pid, vid):
    command = "defects4j checkout -p "+pid+" -v "+vid+"b -w ./checkout/"+pid+"_"+vid
    return command

def make_compile_command(pid, vid):
    command = "defects4j compile -w ./checkout/"+pid+"_"+vid
    return command

def make_test_command(pid, vid):
    command = "defects4j test -w ./checkout/"+pid+"_"+vid
    return command

def make_coverage_command(pid, vid, test_signature):
    command = "defects4j coverage -w ./checkout/"+pid+"_"+vid+" -t "+test_signature
    return command

if __name__ == "__main__":
    # bug_data folder
    bug_data_path = "./bug_data/"

    bugs = [file.split('.json')[0] for file in os.listdir(bug_data_path) if file.endswith('.json')]

    for bug in bugs:
        pid, vid = bug.split('-')
        
        print(f"Doing checkout for {pid}-{vid}")
        run_command(make_checkout_command(pid, vid))

        print("Compiling...")
        run_command(make_compile_command(pid, vid))