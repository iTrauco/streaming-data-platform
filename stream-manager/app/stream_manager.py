class StreamManager:
    def __init__(self):
        self.config = {
            "instance": "stream-relay",
            "zone": "us-central1-a",
        }
    
    def get_ssh_command(self):
        return f"gcloud compute ssh {self.config['instance']} --zone={self.config['zone']}"
    
    def get_stream_command(self, rtmp_url, stream_key):
        # Corrected YouTube RTMP URL format
        return f'ffmpeg -i rtmp://localhost:1935/live -c copy -f flv {rtmp_url}/{stream_key}'
    
    def execute_remote_command(self, command):
        ssh_command = f"{self.get_ssh_command()} --command='{command}'"
        return ssh_command