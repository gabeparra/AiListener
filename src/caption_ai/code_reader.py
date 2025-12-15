"""Code reading and analysis utilities for Glup."""

import os
from pathlib import Path
from typing import List, Dict, Optional

# Common code file extensions
CODE_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.sh',
    '.bash', '.zsh', '.fish', '.r', '.m', '.mm', '.sql', '.html', '.css',
    '.scss', '.sass', '.less', '.vue', '.svelte', '.xml', '.json', '.yaml',
    '.yml', '.toml', '.ini', '.cfg', '.md', '.txt', '.rust', '.dart'
}

# Files/directories to ignore
IGNORE_PATTERNS = {
    '__pycache__', '.git', '.venv', 'venv', 'node_modules', '.next', 'dist',
    'build', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.idea', '.vscode',
    '.DS_Store', '*.pyc', '*.pyo', '*.pyd', '.env', '.env.local'
}


class CodeReader:
    """Read and analyze code files."""
    
    def __init__(self, root_path: Optional[Path] = None):
        """Initialize code reader with project root."""
        if root_path is None:
            # Default to project root
            self.root_path = Path(__file__).parent.parent.parent
        else:
            self.root_path = Path(root_path).resolve()
    
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        path_str = str(path)
        path_name = path.name
        
        # Check ignore patterns
        for pattern in IGNORE_PATTERNS:
            if pattern in path_str or path_name == pattern or path_name.startswith(pattern.replace('*', '')):
                return True
        
        # Ignore hidden files/directories (except specific ones)
        if path_name.startswith('.') and path_name not in {'.gitignore', '.env.example', '.cursorignore'}:
            return True
        
        return False
    
    def is_code_file(self, path: Path) -> bool:
        """Check if file is a code file."""
        return path.suffix.lower() in CODE_EXTENSIONS
    
    def list_code_files(self, directory: Optional[Path] = None, max_depth: int = 5) -> List[Dict[str, str]]:
        """List all code files in directory."""
        if directory is None:
            directory = self.root_path
        
        directory = Path(directory).resolve()
        
        # Ensure we don't go outside project root
        try:
            directory.relative_to(self.root_path)
        except ValueError:
            return []
        
        code_files = []
        
        try:
            for root, dirs, files in os.walk(directory):
                root_path = Path(root)
                
                # Calculate depth
                depth = len(root_path.relative_to(directory).parts)
                if depth > max_depth:
                    dirs.clear()
                    continue
                
                # Filter out ignored directories
                dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]
                
                for file in files:
                    file_path = root_path / file
                    if not self.should_ignore(file_path) and self.is_code_file(file_path):
                        rel_path = file_path.relative_to(self.root_path)
                        code_files.append({
                            'path': str(rel_path),
                            'full_path': str(file_path),
                            'name': file_path.name,
                            'extension': file_path.suffix,
                            'size': file_path.stat().st_size if file_path.exists() else 0,
                        })
        except PermissionError:
            pass
        
        return sorted(code_files, key=lambda x: x['path'])
    
    def read_file(self, file_path: str, max_lines: int = 1000) -> Optional[Dict[str, any]]:
        """Read a code file."""
        try:
            path = (self.root_path / file_path).resolve()
            
            # Security: ensure file is within project root
            try:
                path.relative_to(self.root_path)
            except ValueError:
                return None
            
            if not path.exists() or not path.is_file():
                return None
            
            if self.should_ignore(path):
                return None
            
            # Read file with encoding detection
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                # Try latin-1 as fallback
                content = path.read_text(encoding='latin-1')
            
            lines = content.split('\n')
            total_lines = len(lines)
            
            # Limit lines if too large
            if len(lines) > max_lines:
                content = '\n'.join(lines[:max_lines])
                truncated = True
            else:
                truncated = False
            
            return {
                'path': str(path.relative_to(self.root_path)),
                'full_path': str(path),
                'name': path.name,
                'extension': path.suffix,
                'content': content,
                'total_lines': total_lines,
                'truncated': truncated,
                'size': path.stat().st_size,
            }
        except (PermissionError, OSError, UnicodeDecodeError) as e:
            return None
    
    def search_in_files(self, query: str, file_pattern: Optional[str] = None, max_results: int = 10) -> List[Dict[str, any]]:
        """Search for text in code files."""
        code_files = self.list_code_files()
        results = []
        
        query_lower = query.lower()
        
        for file_info in code_files:
            if file_pattern and file_pattern not in file_info['path']:
                continue
            
            file_data = self.read_file(file_info['path'], max_lines=500)
            if not file_data:
                continue
            
            content_lower = file_data['content'].lower()
            if query_lower in content_lower:
                # Find line numbers where query appears
                lines = file_data['content'].split('\n')
                matches = []
                for i, line in enumerate(lines[:500], 1):
                    if query_lower in line.lower():
                        matches.append({
                            'line': i,
                            'content': line.strip()[:200],
                        })
                
                results.append({
                    'file': file_info['path'],
                    'matches': matches[:5],  # Limit matches per file
                    'match_count': len(matches),
                })
                
                if len(results) >= max_results:
                    break
        
        return results


# Global instance
code_reader = CodeReader()

