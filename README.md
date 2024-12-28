# Stream Platform

## Sprint Feature Development Roadmap
```
develop
├── feat/env-setup
│   └── Basic secrets.env and gitignore setup
├── feat/secrets-manager-integration
│   └── Integrate Streamlit UI with Secret Manager CRUD operations
├── feat/rtmp-auth
│   └── Add NGINX RTMP authentication
├── feat/auto-shutdown
│   └── Implement VM inactivity monitoring and shutdown
└── feat/monitoring
    └── Add basic health/status monitoring dashboard
```

## POC Restructure
```
./stream-platform/
├── app/                     # Docker app code
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── stream_manager.py
│   └── utils/
│       └── secret_manager.py
├── infrastructure/
│   ├── terraform/
│   │   ├── iam.tf
│   │   ├── instance_groups.tf
│   │   ├── load_balancer.tf
│   │   ├── main.tf
│   │   ├── output.tf
│   │   ├── terraform.tfstate
│   │   ├── terraform.tfstate.backup
│   │   ├── terraform.tfvars
│   │   └── variables.tf 
│   └── scripts/
│       └── startup.sh
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── setup.py
└── .gitignore
```


## Current Data Science HPC Specs

### Core System Specifications
- **Model**: Dell Precision 5820 Tower
- **Chassis**: 950W PCIe FlexBay with CL FMX

### Processing
- **CPU**: Intel® Xeon® W-2245
 - Cache: 16.5 MB
 - Cores/Threads: 8C/16T
 - Base Clock: 3.90 GHz
 - Boost Clock: 4.70 GHz Turbo
 - TDP: 155W

### Graphics
- **GPU**: NVIDIA® RTX™ A5000
 - Memory: 24 GB GDDR6
 - Display Outputs: 4x DisplayPort
 - CUDA Cores: 8192
 - RT Cores: 80 (2nd Gen)
 - Tensor Cores: 320 (3rd Gen)
 - Memory Bandwidth: 768 GB/s

### Memory Configuration
- **Total RAM**: 128 GB
- **Configuration**: 4 x 32 GB
- **Type**: DDR4 RDIMM ECC
- **Speed**: 2933 MT/s

### Storage Solution
- **Primary Drive**: 512 GB M.2 PCIe NVMe SSD (Class 40)
- **Secondary Storage**: 
 - 2x 2TB Samsung 970 PRO NVMe SSDs in RAID 0
 - 4TB Western Digital Black HDD (7200 RPM) for data storage

### Operating System
- **Distribution**: Ubuntu 24.02 XFCE 4.18
- **Kernel**: 6.5 or later (optimized for Xeon)

### GPU Optimization Notes
- CUDA Toolkit 12.2 installed
- cuDNN 8.9.7 configured
- NGC Container Runtime enabled
- GPU clock settings optimized via nvidia-smi:
 - Power limit set to 230W
 - Memory transfer rate: +1000MHz
 - Graphics clock: +100MHz
- Fan curve adjusted for sustained workloads

### Performance Tuning Scripts
- Custom scripts location: /opt/performance_tuning/
 - cpu_governor.sh: Sets CPU governor to performance
 - gpu_optimize.sh: Configures optimal GPU settings
 - memory_tune.sh: Optimizes memory allocation
 - nvme_tune.sh: Configures NVMe queue depths
 - raid_tune.sh: Optimizes RAID array performance

### Additional Notes
- Entry level high-performance computing data science workstation optmizing for use on Debian Linux 24.01 w/ XFCE 04.18 desktop
- Currently optmizing for parallel batch processing or streaming data workflows 
- PCIe Gen 4.0 enabled for maximum storage throughput
- ECC memory configured for data integrity