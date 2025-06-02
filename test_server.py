#!/usr/bin/env python3
import sys
import subprocess

print("Testing server...", file=sys.stderr)

# Try running the server directly
try:
    result = subprocess.run(
        [sys.executable, "server.py"],
        capture_output=True,
        text=True,
        timeout=5
    )
    print(f"STDOUT: {result.stdout}", file=sys.stderr)
    print(f"STDERR: {result.stderr}", file=sys.stderr)
    print(f"Return code: {result.returncode}", file=sys.stderr)
except subprocess.TimeoutExpired:
    print("Server started successfully (timeout expected for long-running process)", file=sys.stderr)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)