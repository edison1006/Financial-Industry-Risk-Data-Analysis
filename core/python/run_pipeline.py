import subprocess

def run(cmd):
    print(">", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    run(["python", "generate_data.py"])
    run(["python", "load_data.py"])

if __name__ == "__main__":
    main()
