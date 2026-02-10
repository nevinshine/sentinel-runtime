import socket
import subprocess
import os
import sys

PORT = 9999

def run_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', PORT))
    s.listen(1)
    print(f"[*] Vulnerable Server listening on port {PORT}...")
    print(f"[*] PID: {os.getpid()}")
    print("[*] Send this PID to Sentinel: ./sentinel_loader mark <PID>")

    while True:
        conn, addr = s.accept()
        print(f"[+] Connection from {addr}")
        conn.send(b"Sentinel Vulnerable Shell.\n")
        conn.send(b"Try: 'ping -c 1 8.8.8.8' (Should be BLOCKED)\n")
        conn.send(b"Try: ':(){ :|:& };:' (Fork Bomb - Should spike Dashboard)\n")
        conn.send(b"> ")
        
        while True:
            try:
                data = conn.recv(1024)
                if not data: break
                cmd = data.decode().strip()
                if cmd == "exit": break
                if not cmd: continue
                
                print(f"[*] Executing: {cmd}")
                
                # Execute command
                # Sentinel blocks by INODE. 
                # If /bin/ping is blocked, this subprocess call will fail with Permission Denied
                subprocess.call(cmd, shell=True)
                
                conn.send(b"> ")
            except Exception as e:
                conn.send(f"Error: {e}\n".encode())
                
        conn.close()

if __name__ == "__main__":
    run_server()
