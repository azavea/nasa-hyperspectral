import subprocess
import sys


def run_command(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in proc.stdout:
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()
    proc.wait()
    return proc.returncode