import os
from pathlib import Path

# Define the required directories and subdirectories
required_directories = {
    "app": {
        "config": {},
        "utils": {},
        "services": {},
        "ui": {}
    },
    "infrastructure": {
        "terraform": {
            "modules": {
                "network": {
                    "main.tf": "# Network module configuration\n",
                    "variables.tf": "# Network module variables\n",
                    "outputs.tf": "# Network module outputs\n"
                },
                "compute": {
                    "main.tf": "# Compute module configuration\n",
                    "variables.tf": "# Compute module variables\n",
                    "outputs.tf": "# Compute module outputs\n"
                },
                "storage": {
                    "main.tf": "# Storage module configuration\n",
                    "variables.tf": "# Storage module variables\n",
                    "outputs.tf": "# Storage module outputs\n"
                },
                "bigquery": {
                    "main.tf": "# BigQuery module configuration\n",
                    "variables.tf": "# BigQuery module variables\n",
                    "outputs.tf": "# BigQuery module outputs\n"
                }
            },
            "main.tf": "# Root Terraform main configuration\n",
            "variables.tf": "# Root Terraform variables\n",
            "outputs.tf": "# Root Terraform outputs\n"
        },
        "scripts": {
            "startup.sh": "#!/bin/bash\n# Startup script\n"
        }
    }
}

# Directories to ignore during traversal
IGNORED_DIRS = {"venv", "__pycache__", ".git", ".idea", "node_modules", ".terraform"}

def create_directories(base_path, directories):
    """
    Recursively create directories and add necessary files without overwriting existing ones.
    """
    for dir_name, subdirs in directories.items():
        dir_path = Path(base_path) / dir_name
        
        # Create directory if it doesn't exist
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        
        # Add __init__.py for Python modules if needed
        if dir_name in ["config", "utils", "services", "ui"]:
            init_file = dir_path / "__init__.py"
            if not init_file.exists():
                init_file.touch()
                print(f"Created file: {init_file}")
        
        # Process subdirectories and files
        if isinstance(subdirs, dict):
            # Handle files at current level
            for file_name, content in subdirs.items():
                if isinstance(content, str):
                    file_path = dir_path / file_name
                    if not file_path.exists():
                        file_path.write_text(content)
                        print(f"Created file: {file_path}")
            
            # Recursively process subdirectories
            subdirs_only = {k: v for k, v in subdirs.items() if isinstance(v, dict)}
            if subdirs_only:
                create_directories(dir_path, subdirs_only)

def find_and_create_directories(start_path, directories):
    """
    Recursively search for matching directories starting from the given path
    and create required subdirectories where needed.
    """
    start_path = Path(start_path)
    
    def walk_directory(current_path):
        try:
            # Get all subdirectories, excluding ignored ones
            subdirs = [d for d in current_path.iterdir() 
                      if d.is_dir() and d.name not in IGNORED_DIRS]
            
            # Check if any of the required directories exist at this level
            for target_dir, sub_structure in directories.items():
                target_path = current_path / target_dir
                if target_path.exists():
                    print(f"\nFound existing directory: {target_path}")
                    print("Creating any missing subdirectories and files...")
                    create_directories(target_path, sub_structure)
            
            # Recursively check subdirectories
            for subdir in subdirs:
                walk_directory(subdir)
                
        except PermissionError as e:
            print(f"Permission denied accessing {current_path}: {e}")
        except Exception as e:
            print(f"Error processing {current_path}: {e}")

    walk_directory(start_path)

def main():
    current_path = Path.cwd()
    print(f"Starting directory structure check from: {current_path}")
    
    # Recursively find and create the required directory structure
    find_and_create_directories(current_path, required_directories)
    print("\nDirectory structure check complete.")
    print("All required directories and files have been verified/created where needed.")

if __name__ == "__main__":
    main()