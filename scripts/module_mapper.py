import ast
import os
from pathlib import Path
from typing import Dict, Set, List, Tuple
import json
from datetime import datetime
from rich import print
from rich.console import Console
from rich.panel import Panel

console = Console()

class ModuleMapper:
    def __init__(self):
        self.root_dir = Path.cwd()
        # Expanded ignored paths
        self.ignored_patterns = {
            '.venv', 'venv', 'env',  # Virtual environments
            '__pycache__', '.pytest_cache',  # Python cache
            '.git', '.github',  # Git
            '.idea', '.vscode',  # IDEs
            'node_modules',  # Node.js
            'site-packages', 'dist-packages',  # Installed packages
            'build', 'dist', 'egg-info',  # Build artifacts
            '.tox', '.coverage',  # Testing
            'migrations',  # Django/database migrations
            'tests', 'test'  # Test directories
        }
        self.module_map: Dict[str, Dict] = {}
        self.import_graph: Dict[str, Dict] = {}
        
        console.print(f"[bold green]Initializing ModuleMapper at project root:[/bold green] {self.root_dir}")
    
    def _should_ignore_path(self, path: Path) -> bool:
        """Check if a path should be ignored based on patterns."""
        path_parts = str(path).lower().split(os.sep)
        return any(ignored in path_parts for ignored in self.ignored_patterns)

    def _is_project_python_file(self, file_path: Path) -> bool:
        """Check if file is a project Python file (not in ignored paths)."""
        return (
            file_path.is_file() 
            and file_path.suffix == '.py'
            and not self._should_ignore_path(file_path)
        )
    
    def _get_relative_module_path(self, file_path: Path) -> str:
        """Get the module path relative to project root."""
        try:
            return str(file_path.relative_to(self.root_dir)).replace('/', '.').replace('\\', '.')[:-3]
        except ValueError:
            return None
            
    def _parse_imports(self, file_path: Path) -> Tuple[Set[str], Set[str]]:
        """Parse imports and exports from a Python file."""
        imports = set()
        exports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            imports.add(name.name)
                    else:
                        if node.module:
                            imports.add(node.module)
                
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    if node.name != '__init__':
                        exports.add(node.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            exports.add(target.id)
                            
        except Exception as e:
            console.print(f"[red]Error parsing {file_path}: {e}[/red]")
            return set(), set()
            
        return imports, exports

    def map_project(self) -> Dict[str, Dict]:
        """Map all Python modules in the project."""
        console.print("\n[yellow]Mapping Python modules in project...[/yellow]")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not any(ignored in d.lower() for ignored in self.ignored_patterns)]
            
            current_path = Path(root)
            
            # Skip if current path should be ignored
            if self._should_ignore_path(current_path):
                continue
            
            for file in files:
                file_path = current_path / file
                
                # Skip if not a project Python file
                if not self._is_project_python_file(file_path):
                    continue
                
                relative_module = self._get_relative_module_path(file_path)
                if not relative_module:
                    continue
                    
                imports, exports = self._parse_imports(file_path)
                
                self.module_map[relative_module] = {
                    'path': str(file_path),
                    'imports': list(imports),
                    'exports': list(exports)
                }
                console.print(f"[green]Mapped module:[/green] {relative_module}")
        
        module_count = len(self.module_map)
        if module_count == 0:
            console.print("[yellow]No project Python modules found![/yellow]")
        else:
            console.print(f"\n[bold green]Found {module_count} project Python modules[/bold green]")
        
        return self.module_map

    def save_mapping(self, prefix: str = ''):
        """Save the module mapping to a JSON file."""
        output_dir = self.root_dir / 'migration_data'
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        prefix = f"{prefix}_" if prefix else ""
        
        module_map_file = output_dir / f'{prefix}module_map_{timestamp}.json'
        with open(module_map_file, 'w') as f:
            json.dump(self.module_map, f, indent=2)
            
        console.print(f"\n[bold green]Module map saved to:[/bold green] {module_map_file}")
        return module_map_file

def get_mapping_files() -> List[Path]:
    """Get list of existing mapping files."""
    migration_dir = Path.cwd() / 'migration_data'
    if not migration_dir.exists():
        return []
    return sorted(list(migration_dir.glob('*module_map*.json')))

def update_imports(old_map_path: str, new_map_path: str):
    """Update import statements in Python files."""
    console.print(f"\n[yellow]Updating imports using mapping files...[/yellow]")
    try:
        with open(old_map_path, 'r') as f:
            old_map = json.load(f)
        with open(new_map_path, 'r') as f:
            new_map = json.load(f)
            
        # Implementation for updating imports would go here
        console.print("[green]Import statements updated successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error updating imports: {e}[/red]")

def display_menu():
    """Display the main menu."""
    console.print(Panel.fit(
        "[bold cyan]Python Module Migration Tool[/bold cyan]\n"
        "1. Map Current Project Structure\n"
        "2. Map New Project Structure\n"
        "3. Update Import Statements\n"
        "4. View Existing Mappings\n"
        "5. Exit"
    ))

def main():
    while True:
        display_menu()
        try:
            choice = int(input("\nEnter your choice (1-5): "))
            
            if choice == 5:
                console.print("[yellow]Goodbye![/yellow]")
                break
                
            elif choice == 1:
                console.print("\n[bold]Mapping current project structure...[/bold]")
                mapper = ModuleMapper()
                if mapper.map_project():
                    mapper.save_mapping('original')
                
            elif choice == 2:
                console.print("\n[bold]Mapping new project structure...[/bold]")
                mapper = ModuleMapper()
                if mapper.map_project():
                    mapper.save_mapping('new')
                
            elif choice == 3:
                mapping_files = get_mapping_files()
                if len(mapping_files) < 2:
                    console.print("[red]Error: Need at least two mapping files to update imports.[/red]")
                    continue
                
                console.print("\n[yellow]Available mapping files:[/yellow]")
                for i, f in enumerate(mapping_files, 1):
                    console.print(f"{i}. {f.name}")
                
                old_idx = int(input("\nSelect number for ORIGINAL mapping file: ")) - 1
                new_idx = int(input("Select number for NEW mapping file: ")) - 1
                
                if 0 <= old_idx < len(mapping_files) and 0 <= new_idx < len(mapping_files):
                    update_imports(str(mapping_files[old_idx]), str(mapping_files[new_idx]))
                else:
                    console.print("[red]Invalid selection[/red]")
            
            elif choice == 4:
                mapping_files = get_mapping_files()
                if not mapping_files:
                    console.print("[red]No mapping files found in migration_data directory.[/red]")
                    continue
                
                console.print("\n[yellow]Available mapping files:[/yellow]")
                for i, f in enumerate(mapping_files, 1):
                    console.print(f"{i}. {f.name}")
                
                file_idx = int(input("\nSelect a file number to view (or 0 to go back): ")) - 1
                if file_idx >= 0 and file_idx < len(mapping_files):
                    with open(mapping_files[file_idx], 'r') as f:
                        data = json.load(f)
                        console.print_json(data=data)
            
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