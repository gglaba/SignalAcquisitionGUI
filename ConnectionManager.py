import paramiko
import os
import fnmatch
from paramiko import SSHClient, AutoAddPolicy
import threading
import subprocess
from scp import SCPClient
import select

#class for managing connection - basically trying to keep backend separate

class ConnectionManager:
    def __init__(self,app, ip, username, password, private_key_path): #initializing with ip, username, password and private key path (not sure if the key is necessary but keeping it for making sure there are no password tempts)
        self.ip = ip
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.client = None
        self.error_event = threading.Event() #event for error handling
        self.app = app #passing app instance so error msgbox can be shown properly

        self.debug_log_file = open("debug.log", "w") #debug log for extra info

    def log(self, message): #helper method for logging 
        self.debug_log_file.write(f"{self.ip}: {message}\n")
        self.debug_log_file.flush()

    def connect(self): #method for connecting to pitaya
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy()) #auto add policy for adding host key
        private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path) #loading private key
        self.client.connect(self.ip, username=self.username, pkey=private_key)
        return self.client

    def disconnect(self): #simple method for disconnecting from pitaya
        if self.client:
            self.client.close()
            print(f"Disconnected from {self.ip}")
            self.log(f"Disconnected")

    def execute_command(self, command): #method for executing command on pitaya, basically used only to run send_acquire on remote
        self.stdin, self.stdout, self.stderr = self.client.exec_command(command)
        self.start_listener() #starting listener thread for stdout and stderr
        self.stdout.channel.recv_exit_status() #waiting for command to finish
        return self.stdout, self.stderr

    def start_listener(self): #method for starting stdout and stderr listener thread
        self.stdout_content = ""
        self.stderr_content = ""
        self.listener_thread = threading.Thread(target=self.listener) #thread so it doesn't block the main thread/gui
        self.listener_thread.start()

    def join_listener(self): #joining listeners, used for waiting for command to finish
        if self.listener_thread.is_alive(): 
            self.listener_thread.join()

    def listener(self): #listener method for stdout and stderr
        while True:
            read_ready, _, _ = select.select([self.stdout.channel, self.stderr.channel], [], [], 0.1) #selecting ready streams
            if not read_ready:
                continue
            for stream in read_ready: 
                if stream == self.stdout.channel and stream.recv_ready(): #if stdout is ready
                    stdout_content = stream.recv(1024).decode('utf-8') #printing stdout as well as logging it
                    print("STDOUT_LISTENER:", stdout_content, end='', flush=True)
                    self.log(stdout_content)
                elif stream == self.stderr.channel and stream.recv_stderr_ready(): #same for stderr
                    stderr_content = stream.recv_stderr(1024).decode('utf-8')
                    print("STDERR_LISTENER:", stderr_content, end='', flush=True)
                    self.log(stderr_content)
                    self.app.error_queue.put(f"{self.ip}: {stderr_content}") #adding stderr to main app error_que so messagebox can be shown
            if self.stdout.channel.exit_status_ready():
                break

    def list_files(self, directory): #helper method for listing files in directory (used only in transfering files)
        sftp = self.client.open_sftp()
        files = sftp.listdir(directory)
        sftp.close()
        return files


    def transfer_all_csv_files(self, remote_directory, local_directory): #transfering data files from pitaya to local machine

        if not os.path.exists(local_directory): #making sure local directory exists, not doing it atm for remote directory might add in future
            print(f"Local directory {local_directory} does not exist.")
            self.app.error_queue.put(f"{self.ip}: Local directory {local_directory} does not exist.")
            return

        with SCPClient(self.client.get_transport()) as scp: #using scp for transfering files, mostly because its faster than sftp
            try:
                remote_files = self.list_files(remote_directory) #listing files in remote directory
            except Exception as e:
                print(f"Failed to list remote directory {remote_directory}. Error: {str(e)}")
                self.app.error_queue.put(f"{self.ip}: Failed to list remote directory {remote_directory}. Error: {str(e)}") #if error is raised messagebox appears
                return

            print(f"Remote files: {remote_files}")

            csv_files = [file for file in remote_files if file.endswith('.csv')] #tmp location in pitaya has other files so filtering only csv files

            # Transfer each CSV file
            for csv_file in csv_files:
                remote_path = os.path.join(remote_directory, csv_file).replace("\\", "/")#replacing backslashes with forward slashes
                local_path = os.path.join(local_directory, csv_file)
                try:
                    scp.get(remote_path, local_path) #transfering file
                    print(f"Successfully transferred {csv_file}.")
                    remote_file_size = self.client.exec_command(f"wc -c < {remote_path}")[1].read().decode('utf-8').strip() #getting file size of remote file
                    local_file_size = os.path.getsize(local_path) #getting file size of local file
                    size_difference = abs(int(remote_file_size) - local_file_size) #making sure file sizes match before deleting remote file
                    if size_difference <= 10240:  # Allow a difference of up to 10KB - dont know how much linux - windows file size difference might be
                        # Delete the file on the remote server
                        self.client.exec_command(f"rm {remote_path}")
                        print(f"Successfully deleted {csv_file} on the remote server.")
                    else:
                        print(f"File sizes do not match for {csv_file}. Not deleting the remote file.")
                        self.app.error_queue.put(f"{self.ip}: File sizes do not match for {csv_file}. Not deleting the remote file.") #if file sizes dont match, messagebox appears
                except Exception as e:
                    print(f"Failed to transfer {csv_file}. Error: {str(e)}")
                    self.app.error_queue.put(f"{self.ip}: Failed to transfer {csv_file}. Error: {str(e)}") #for any other error - messagebox