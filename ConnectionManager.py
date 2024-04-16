import paramiko
from paramiko import SSHClient, AutoAddPolicy

class ConnectionManager:
    def __init__(self, ip, username, password, private_key_path):
        self.ip = ip
        self.username = username
        self.password = password
        self.private_key_path = private_key_path
        self.client = None

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

    def execute_command(self, command):
        if self.client:
            stdin, stdout, stderr = self.client.exec_command(command)
            for line in iter(lambda: stdout.readline(2048), ""):
                yield line

    def run_command_routine(self):
        try:
            # Connect to device 1
            ssh_client1 = self.connect_ssh(self.device1_ip)
            print(f"Connected to {self.device1_ip}")

            # Connect to device 2
            ssh_client2 = self.connect_ssh(self.device2_ip)
            print(f"Connected to {self.device2_ip}")

            # Run commands on device 1
            output1 = self.execute_command(ssh_client1,"cd RedPitaya/G && ./send_acquire")
            print(f"Output from {self.device1_ip}:")
            print(output1)



            # Run commands on device 2
            output2 = self.execute_command(ssh_client2,"cd RedPitaya/G && ./send_acquire")
            print(f"Output from {self.device2_ip}:")
            print(output2)



            ssh_client1.close()
            ssh_client2.close()



        except Exception as e:
            print(f"An error occurred: {e}")

# Usage example
# device1_ip = "rp-f0ba38.local"
# device2_ip = "rp-f0ac70.local"
# username = "root"
# private_key_path = "/home/grzesiula/.ssh/id_rsa"

# command_routine = SSHCommandRoutine(device1_ip, device2_ip, username, private_key_path)
# command_routine.run_command_routine()
