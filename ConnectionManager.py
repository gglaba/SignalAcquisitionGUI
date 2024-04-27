import paramiko
from paramiko import SSHClient, AutoAddPolicy
import threading
import subprocess
import select

class ConnectionManager:
    def __init__(self,app, ip, username, password, private_key_path):
        self.ip = ip
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.client = None
        self.error_event = threading.Event()
        self.app = app

        self.debug_log_file = open("debug.log", "w")

    def log(self, message):
        self.debug_log_file.write(f"{self.ip}: {message}\n")
        self.debug_log_file.flush()

    def connect(self):
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy())
        private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path)
        self.client.connect(self.ip, username=self.username, pkey=private_key)
        return self.client

    def disconnect(self):
        if self.client:
            self.client.close()
            print(f"Disconnected from {self.ip}")
            self.log(f"Disconnected")

    def execute_command(self, command):
        self.stdin, self.stdout, self.stderr = self.client.exec_command(command)
        self.start_listener()
        self.stdout.channel.recv_exit_status()
        return self.stdout, self.stderr

    def start_listener(self):
        self.stdout_content = ""
        self.stderr_content = ""
        self.listener_thread = threading.Thread(target=self.listener)
        self.listener_thread.start()

    def join_listener(self):
        if self.listener_thread.is_alive():
            self.listener_thread.join()

    def count_threads(self):
        return len(threading.enumerate())

    def listener(self):
        while True:
            read_ready, _, _ = select.select([self.stdout.channel, self.stderr.channel], [], [], 0.1)
            if not read_ready:
                continue
            for stream in read_ready:
                if stream == self.stdout.channel and stream.recv_ready():
                    stdout_content = stream.recv(1024).decode('utf-8')
                    print("STDOUT_LISTENER:", stdout_content, end='', flush=True)
                    self.log(stdout_content)
                elif stream == self.stderr.channel and stream.recv_stderr_ready():
                    stderr_content = stream.recv_stderr(1024).decode('utf-8')
                    print("STDERR_LISTENER:", stderr_content, end='', flush=True)
                    self.log(stderr_content)
                    self.app.error_queue.put(f"{self.ip}: {stderr_content}")
            if self.stdout.channel.exit_status_ready():
                break