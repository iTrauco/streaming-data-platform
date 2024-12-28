# # Create NGINX RTMP configuration
# mkdir -p /usr/local/nginx/conf
# cat > /usr/local/nginx/conf/nginx.conf <<EOF
# worker_processes auto;
# error_log /usr/local/nginx/logs/error.log info;
# pid /usr/local/nginx/logs/nginx.pid;

# events {
#     worker_connections 1024;
# }

# rtmp {
#     server {
#         listen 1935;
#         chunk_size 4096;
        
#         application live {
#             live on;
#             record off;
            
#             # Pull stream keys from Secret Manager and store in file
#             exec_static /usr/local/bin/update-stream-destinations.sh;
            
#             # Read key from file and push to YouTube
#             exec_pull cat /usr/local/nginx/conf/youtube_key.txt;
#             push rtmp://a.rtmp.youtube.com/live2/\${streaming_key};
#         }
#     }
# }

# http {
#     include mime.types;
#     default_type application/octet-stream;
    
#     server {
#         listen 80;
        
#         location /metrics {
#             stub_status on;
#             access_log off;
#             allow 127.0.0.1;
#             deny all;
#         }
#     }
# }
# EOF

# # Create script to update stream destinations
# mkdir -p /usr/local/bin
# cat > /usr/local/bin/update-stream-destinations.sh <<'EOF'
# #!/bin/bash

# # Get stream keys from Secret Manager
# KEYS=$(gcloud secrets versions access latest --secret="stream-keys")

# # Extract YouTube key and store it in a file
# echo "$(echo $KEYS | jq -r .youtube)" > /usr/local/nginx/conf/youtube_key.txt

# # Log the update
# echo "Stream keys updated at $(date)" | logger
# EOF

# # Set proper permissions
# chmod +x /usr/local/bin/update-stream-destinations.sh
# touch /usr/local/nginx/conf/youtube_key.txt
# chown nobody:nogroup /usr/local/nginx/conf/youtube_key.txt
# chmod 600 /usr/local/nginx/conf/youtube_key.txt



#!/bin/bash
# Exit on error
set -e
# Install required packages
apt-get update
apt-get install -y \
    build-essential \
    libpcre3-dev \
    libssl-dev \
    zlib1g-dev \
    prometheus-node-exporter \
    jq \
    curl \
    wget \
    unzip

# Download and build NGINX with RTMP module
cd /tmp
wget http://nginx.org/download/nginx-1.18.0.tar.gz
wget https://github.com/arut/nginx-rtmp-module/archive/master.zip
tar -zxvf nginx-1.18.0.tar.gz
unzip master.zip
cd nginx-1.18.0
./configure --prefix=/usr/local/nginx \
    --with-http_ssl_module \
    --add-module=../nginx-rtmp-module-master \
    --with-http_stub_status_module
make
make install

# Create NGINX service file
cat > /lib/systemd/system/nginx.service <<EOF
[Unit]
Description=nginx - high performance web server
Documentation=https://nginx.org/en/docs/
After=network-online.target remote-fs.target nss-lookup.target
Wants=network-online.target

[Service]
Type=forking
PIDFile=/usr/local/nginx/logs/nginx.pid
ExecStartPre=/usr/local/nginx/sbin/nginx -t -c /usr/local/nginx/conf/nginx.conf
ExecStart=/usr/local/nginx/sbin/nginx -c /usr/local/nginx/conf/nginx.conf
ExecReload=/bin/kill -s HUP \$MAINPID
ExecStop=/bin/kill -s TERM \$MAINPID

[Install]
WantedBy=multi-user.target
EOF

# Create NGINX RTMP configuration
mkdir -p /usr/local/nginx/conf
cat > /usr/local/nginx/conf/nginx.conf <<EOF
worker_processes auto;
error_log /usr/local/nginx/logs/error.log info;
pid /usr/local/nginx/logs/nginx.pid;

events {
    worker_connections 1024;
}

rtmp {
    server {
        listen 1935;
        chunk_size 4096;
        
        application live {
            live on;
            record off;
            
            # Pull stream keys from Secret Manager and store in file
            exec_static /usr/local/bin/update-stream-destinations.sh;
            
            # Read key from file and push to YouTube
            exec_pull cat /usr/local/nginx/conf/youtube_key.txt;
            push rtmp://a.rtmp.youtube.com/live2/\${streaming_key};
        }
    }
}

http {
    include mime.types;
    default_type application/octet-stream;
    
    server {
        listen 80;
        
        location /metrics {
            stub_status on;
            access_log off;
            allow 127.0.0.1;
            deny all;
        }
    }
}
EOF

# Create script to update stream destinations
mkdir -p /usr/local/bin
cat > /usr/local/bin/update-stream-destinations.sh <<'EOF'
#!/bin/bash

# Get stream keys from Secret Manager
KEYS=$(gcloud secrets versions access latest --secret="stream-keys")

# Extract YouTube key and store it in a file
echo "$(echo $KEYS | jq -r .youtube)" > /usr/local/nginx/conf/youtube_key.txt

# Log the update
echo "Stream keys updated at $(date)" | logger
EOF

# Set proper permissions
chmod +x /usr/local/bin/update-stream-destinations.sh
touch /usr/local/nginx/conf/youtube_key.txt
chown nobody:nogroup /usr/local/nginx/conf/youtube_key.txt
chmod 600 /usr/local/nginx/conf/youtube_key.txt

# Reload systemd and start services
systemctl daemon-reload
systemctl enable nginx
systemctl start nginx
systemctl enable prometheus-node-exporter
systemctl start prometheus-node-exporter

# Signal startup completion
echo "Startup complete" | logger