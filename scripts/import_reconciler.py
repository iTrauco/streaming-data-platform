import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json
from datetime import datetime
from rich import print
from rich.console import Console
from rich.panel import Panel
import configparser
import subprocess
from dataclasses import dataclass
import sys

console = Console()

@dataclass
class ImportChange:
    file_path: str
    old_import: str
    new_import: str
    status: str = "pending"  # pending, success, error

class ImportReconciler:
    def __init__(self):
        self.root_dir = Path.cwd()
        self.config_file = self.root_dir / '.import_reconciler.ini'
        self.load_config()
        
    def load_config(self):
        """Load or create configuration file."""
        self.config = configparser.ConfigParser()
        
        if self.config_file.exists():
            self.config.read(self.config_file)
        else:
            self.config['DEFAULT'] = {
                'last_mapping_dir': str(self.root_dir / 'migration_data'),
                'source_truth_dir': str(self.root_dir)
            }
            self.save_config()
            
    def save_config(self):
        """Save current configuration."""
        with open(self.config_file, 'w') as f:
            self.config.write(f)
            
    def get_mapping_files(self) -> List[Path]:
        """Get mapping files from last used directory."""
        mapping_dir = Path(self.config['DEFAULT']['last_mapping_dir'])
        if not mapping_dir.exists():
            return []
        return sorted(list(mapping_dir.glob('*module_map*.json')))
    
    def verify_module_location(self, module_path: str) -> bool:
        """Verify if a module exists in the new structure."""
        source_dir = Path(self.config['DEFAULT']['source_truth_dir'])
        module_parts = module_path.split('.')
        file_path = source_dir.joinpath(*module_parts).with_suffix('.py')
        return file_path.exists()
        
    def analyze_import_changes(self, old_map: Dict, new_map: Dict) -> List[ImportChange]:
        """Analyze and create list of required import changes."""
        changes = []
        
        # Map old paths to new paths based on exports
        path_mapping = {}
        for old_path, old_info in old_map.items():
            old_exports = set(old_info['exports'])
            for new_path, new_info in new_map.items():
                new_exports = set(new_info['exports'])
                if old_exports & new_exports:  # If there's overlap in exports
                    path_mapping[old_path] = new_path
                    break
        
        # Create list of required changes
        for old_path, old_info in old_map.items():
            file_path = old_info['path']
            
            # Check each import in the file
            for import_path in old_info['imports']:
                if import_path in path_mapping:
                    changes.append(ImportChange(
                        file_path=file_path,
                        old_import=import_path,
                        new_import=path_mapping[import_path]
                    ))
        
        return changes
    
    def update_imports_in_file(self, file_path: str, changes: List[ImportChange]) -> bool:
        """Update imports in a single file."""
        try:
            with open(file_path, 'r') as f:
                tree = ast.parse(f.read())
                
            modifier = ImportModifier(changes)
            new_tree = modifier.visit(tree)
            
            with open(file_path, 'w') as f:
                f.write(ast.unparse(new_tree))
                
            return True
        except Exception as e:
            console.print(f"[red]Error updating {file_path}: {e}[/red]")
            return False
            
    def run_tests(self) -> Tuple[bool, str]:
        """Run pytest and return results."""
        try:
            result = subprocess.run(
                ['pytest'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0, result.stdout
        except Exception as e:
            return False, str(e)
            
    def reconcile_imports(self, old_map_path: Path, new_map_path: Path):
        """Main reconciliation process."""
        # Load mapping files
        with open(old_map_path) as f:
            old_map = json.load(f)
        with open(new_map_path) as f:
            new_map = json.load(f)
            
        # Analyze changes needed
        changes = self.analyze_import_changes(old_map, new_map)
        console.print(f"[yellow]Found {len(changes)} import changes needed[/yellow]")
        
        # Process each file's changes
        processed_files = set()
        for change in changes:
            if change.file_path not in processed_files:
                file_changes = [c for c in changes if c.file_path == change.file_path]
                console.print(f"\nUpdating imports in: {change.file_path}")
                
                if self.update_imports_in_file(change.file_path, file_changes):
                    console.print("[green]✓ Successfully updated imports[/green]")
                else:
                    console.print("[red]✗ Failed to update imports[/red]")
                    
                processed_files.add(change.file_path)
        
        # Run tests and show results
        console.print("\n[yellow]Running tests...[/yellow]")
        success, test_output = self.run_tests()
        
        if success:
            console.print("[green]✓ All tests passed[/green]")
        else:
            console.print("[red]✗ Some tests failed[/red]")
            console.print("\nTest output:")
            console.print(test_output)

class ImportModifier(ast.NodeTransformer):
    def __init__(self, changes: List[ImportChange]):
        self.changes = {c.old_import: c.new_import for c in changes}
        
    def visit_Import(self, node):
        new_names = []
        for alias in node.names:
            new_name = self.changes.get(alias.name, alias.name)
            new_names.append(ast.alias(name=new_name, asname=alias.asname))
        return ast.Import(names=new_names)
        
    def visit_ImportFrom(self, node):
        if node.module in self.changes:
            return ast.ImportFrom(
                module=self.changes[node.module],
                names=node.names,
                level=node.level
            )
        return node

def main():
    reconciler = ImportReconciler()
    
    while True:
        console.print(Panel.fit(
            "[bold cyan]Import Reconciliation Tool[/bold cyan]\n"
            "1. Select Mapping Files\n"
            "2. Set Source Truth Directory\n"
            "3. Run Reconciliation\n"
            "4. View Last Results\n"
            "5. Exit"
        ))
        
        try:
            choice = int(input("\nEnter your choice (1-5): "))
            
            if choice == 5:
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            elif choice == 1:
                mapping_files = reconciler.get_mapping_files()
                if len(mapping_files) < 2:
                    console.print("[red]Need at least two mapping files![/red]")
                    continue
                    
                console.print("\n[yellow]Available mapping files:[/yellow]")
                for i, f in enumerate(mapping_files, 1):
                    console.print(f"{i}. {f.name}")
                    
                old_idx = int(input("\nSelect ORIGINAL mapping file: ")) - 1
                new_idx = int(input("Select NEW mapping file: ")) - 1
                
                if 0 <= old_idx < len(mapping_files) and 0 <= new_idx < len(mapping_files):
                    reconciler.config['DEFAULT']['old_map'] = str(mapping_files[old_idx])
                    reconciler.config['DEFAULT']['new_map'] = str(mapping_files[new_idx])
                    reconciler.save_config()
                    console.print("[green]Mapping files selected and saved[/green]")
                    
            elif choice == 2:
                current = reconciler.config['DEFAULT']['source_truth_dir']
                console.print(f"\nCurrent source truth directory: {current}")
                new_dir = input("Enter new directory path (or Enter to keep current): ").strip()
                
                if new_dir:
                    if os.path.isdir(new_dir):
                        reconciler.config['DEFAULT']['source_truth_dir'] = new_dir
                        reconciler.save_config()
                        console.print("[green]Source truth directory updated[/green]")
                    else:
                        console.print("[red]Invalid directory path[/red]")
                        
            elif choice == 3:
                if 'old_map' not in reconciler.config['DEFAULT']:
                    console.print("[red]Please select mapping files first[/red]")
                    continue
                    
                old_map = Path(reconciler.config['DEFAULT']['old_map'])
                new_map = Path(reconciler.config['DEFAULT']['new_map'])
                
                if not old_map.exists() or not new_map.exists():
                    console.print("[red]Mapping files not found[/red]")
                    continue
                    
                reconciler.reconcile_imports(old_map, new_map)
                
            elif choice == 4:
                # TODO: Implement viewing last results
                console.print("[yellow]Feature coming soon[/yellow]")
                
            input("\nPress Enter to continue...")
            console.clear()
            
        except ValueError:
            console.print("[red]Please enter a valid number[/red]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Goodbye![/yellow]")
            break
        except Exception as e:
            console.print(f"[red]An error occurred: {e}[/red]")

if __name__ == "__main__":
    main()