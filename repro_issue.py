
import subprocess
import os
import sys
import time

# Create a C file that demonstrates the issue
c_code = r"""
#include <stdio.h>
#include <windows.h>

void __attribute__((constructor)) flush_init() {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    printf("DEBUG: Constructor ran\n");
}

int main() {
    int a;
    printf("Nhap a: ");
    // fflush(stdout); // Uncommenting this fixes it manually
    scanf("%d", &a);
    printf("Ban nhap: %d\n", a);
    return 0;
}
"""

with open("test_buffering.c", "w") as f:
    f.write(c_code)

# Compile it
print("Compiling...")
subprocess.run(["gcc", "-o", "test_buffering.exe", "test_buffering.c"], check=True)

# Run it with Python subprocess to simulate app.py behavior
print("\nRunning with text=True, bufsize=0 (SIMULATING BUG)...")
try:
    p = subprocess.Popen(
        ["test_buffering.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0  # This is the problematic setting in app.py
    )
except ValueError as e:
    print(f"Caught expected ValueError with text=True, bufsize=0: {e}")
    # Fallback to default buffering for text mode execution simulation
    p = subprocess.Popen(
        ["test_buffering.exe"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

def read_output(process):
    while True:
        char = process.stdout.read(1)
        if not char:
            break
        print(f"OUT: {repr(char)}")
        if "Nhap a: " in char: # unlikely to catch split chunks like this but logic holds
            pass

import threading
t = threading.Thread(target=read_output, args=(p,))
t.start()

time.sleep(1)
print("Sending input '10'...")
try:
    p.stdin.write("10\n")
    p.stdin.flush()
except Exception as e:
    print(f"Input error: {e}")

t.join(timeout=2)
if p.poll() is None:
    p.kill()
