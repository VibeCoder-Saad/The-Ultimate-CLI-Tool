#!/usr/bin/env python3
"""
mycli - The Ultimate Command-Line Automation Tool v3.0
A modular, extensible, and powerful command-line framework to automate your digital life.
"""

import os
import sys
import json
import click
import psutil
import subprocess
import shutil
import hashlib
import secrets
import string
from pathlib import Path
from datetime import datetime, timedelta
import requests
import zipfile
import tarfile
from collections import defaultdict
import mimetypes

# Third-party imports
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

try:
    import boto3
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

try:
    import whois
    WHOIS_AVAILABLE = True
except ImportError:
    WHOIS_AVAILABLE = False

try:
    from alpha_vantage.timeseries import TimeSeries
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False

try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False

# Global configuration path
CONFIG_DIR = Path.home() / ".mycli"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Default configuration template
DEFAULT_CONFIG = {
    "user_profile": {
        "default_downloads_path": "auto",
        "default_project_parent_dir": "auto"
    },
    "api_keys": {
        "weather_api_key": "YOUR_OPENWEATHERMAP_API_KEY",
        "news_api_key": "YOUR_NEWSAPI_ORG_KEY",
        "alpha_vantage_api_key": "YOUR_ALPHA_VANTAGE_KEY"
    },
    "aws_credentials": {
        "aws_access_key_id": "YOUR_AWS_ACCESS_KEY",
        "aws_secret_access_key": "YOUR_AWS_SECRET_KEY",
        "default_s3_bucket": "your-default-bucket-name"
    },
    "organize_map": {
        ".pdf": "Documents",
        ".docx": "Documents",
        ".md": "Documents",
        ".jpg": "Images",
        ".jpeg": "Images",
        ".png": "Images",
        ".webp": "Images",
        ".zip": "Archives",
        ".tar.gz": "Archives",
        ".mp4": "Videos",
        ".mov": "Videos",
        ".mp3": "Music",
        ".iso": "OS_Images",
        ".dmg": "OS_Images"
    }
}

def ensure_config():
    """Ensure configuration directory and file exist."""
    CONFIG_DIR.mkdir(exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        click.echo(f"Created default config at {CONFIG_FILE}")
        click.echo("Run 'mycli config edit' to customize your settings.")

def load_config():
    """Load configuration from file."""
    ensure_config()
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        click.echo("Error: Config file is corrupted. Recreating...")
        CONFIG_FILE.unlink()
        ensure_config()
        return DEFAULT_CONFIG

def check_api_key(config, key_path, service_name):
    """Check if API key is configured and not a placeholder."""
    keys = config
    for part in key_path.split('.'):
        keys = keys.get(part, {})
    
    if not keys or keys.startswith("YOUR_") or keys == "":
        click.echo(f"Error: {service_name} API key not set. Please add it to your config file by running 'mycli config edit'.")
        return False
    return True

# Main CLI group
@click.group()
def cli():
    """The ultimate command-line tool for personal and developer automation."""
    pass

# Core commands (config and sysinfo)
@cli.command()
@click.argument('action', type=click.Choice(['show', 'edit']))
def config(action):
    """Manage the config file. Use 'show' to display or 'edit' to modify."""
    ensure_config()
    
    if action == 'show':
        config_data = load_config()
        click.echo(json.dumps(config_data, indent=2))
    elif action == 'edit':
        editor = os.environ.get('EDITOR', 'nano')
        subprocess.run([editor, str(CONFIG_FILE)])

@cli.command()
def sysinfo():
    """Display system information."""
    click.echo("=== System Information ===")
    
    # CPU information
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    click.echo(f"CPU: {cpu_count} cores, {cpu_percent}% usage")
    
    # Memory information
    memory = psutil.virtual_memory()
    click.echo(f"Memory: {memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB ({memory.percent}% used)")
    
    # Disk information
    disk = psutil.disk_usage('/')
    click.echo(f"Disk: {disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB ({disk.percent}% used)")
    
    # System uptime
    boot_time = psutil.boot_time()
    uptime = datetime.now() - datetime.fromtimestamp(boot_time)
    click.echo(f"Uptime: {uptime.days} days, {uptime.seconds // 3600} hours")

# File Management Group
@cli.group()
def file():
    """File and directory management commands."""
    pass

@file.command()
@click.option('--path', default=None, help='Path to organize (defaults to Downloads)')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
def organize(path, dry_run):
    """Organize files into subdirectories based on file extensions."""
    config_data = load_config()
    organize_map = config_data.get('organize_map', {})
    
    if path is None:
        downloads_path = config_data['user_profile']['default_downloads_path']
        if downloads_path == "auto":
            path = str(Path.home() / "Downloads")
        else:
            path = downloads_path
    
    path_obj = Path(path)
    if not path_obj.exists():
        click.echo(f"Error: Path {path} does not exist.")
        return
    
    click.echo(f"Organizing files in: {path}")
    if dry_run:
        click.echo("DRY RUN - No files will be moved")
    
    moved_count = 0
    for file_path in path_obj.iterdir():
        if file_path.is_file():
            extension = file_path.suffix.lower()
            if extension in organize_map:
                target_dir = path_obj / organize_map[extension]
                target_path = target_dir / file_path.name
                
                if dry_run:
                    click.echo(f"Would move: {file_path.name} -> {organize_map[extension]}/")
                else:
                    target_dir.mkdir(exist_ok=True)
                    file_path.rename(target_path)
                    click.echo(f"Moved: {file_path.name} -> {organize_map[extension]}/")
                moved_count += 1
    
    click.echo(f"{'Would move' if dry_run else 'Moved'} {moved_count} files")

@file.command()
@click.option('--days', required=True, type=int, help='Delete files older than N days')
@click.option('--path', default='.', help='Path to clean (default: current directory)')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without deleting')
def cleanup(days, path, dry_run):
    """Delete files older than specified days."""
    path_obj = Path(path)
    cutoff_date = datetime.now() - timedelta(days=days)
    
    deleted_count = 0
    total_size = 0
    
    for file_path in path_obj.rglob('*'):
        if file_path.is_file():
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if file_mtime < cutoff_date:
                file_size = file_path.stat().st_size
                if dry_run:
                    click.echo(f"Would delete: {file_path} ({file_size} bytes)")
                else:
                    file_path.unlink()
                    click.echo(f"Deleted: {file_path}")
                deleted_count += 1
                total_size += file_size
    
    action = "Would delete" if dry_run else "Deleted"
    click.echo(f"{action} {deleted_count} files ({total_size // 1024} KB total)")

@file.command()
@click.argument('path')
@click.option('--dry-run', is_flag=True, help='Show duplicates without removing them')
def deduplicate(path, dry_run):
    """Remove duplicate files based on content hash."""
    path_obj = Path(path)
    file_hashes = defaultdict(list)
    
    # Calculate hashes for all files
    for file_path in path_obj.rglob('*'):
        if file_path.is_file():
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
                file_hashes[file_hash].append(file_path)
    
    # Find and handle duplicates
    duplicates_found = 0
    for file_hash, files in file_hashes.items():
        if len(files) > 1:
            click.echo(f"Duplicate files (hash: {file_hash[:8]}...):")
            for i, file_path in enumerate(files):
                if i == 0:
                    click.echo(f"  KEEP: {file_path}")
                else:
                    if dry_run:
                        click.echo(f"  WOULD DELETE: {file_path}")
                    else:
                        file_path.unlink()
                        click.echo(f"  DELETED: {file_path}")
                    duplicates_found += 1
    
    action = "Would remove" if dry_run else "Removed"
    click.echo(f"{action} {duplicates_found} duplicate files")

@file.command()
@click.argument('path')
@click.option('--top', default=10, help='Number of largest files to show')
def bigfiles(path, top):
    """Find the largest files in a directory."""
    path_obj = Path(path)
    files_with_size = []
    
    for file_path in path_obj.rglob('*'):
        if file_path.is_file():
            size = file_path.stat().st_size
            files_with_size.append((size, file_path))
    
    files_with_size.sort(reverse=True)
    
    click.echo(f"Top {top} largest files in {path}:")
    for i, (size, file_path) in enumerate(files_with_size[:top]):
        size_mb = size / (1024 * 1024)
        click.echo(f"{i+1:2}. {size_mb:8.1f} MB - {file_path}")

@file.command()
@click.argument('folder_path')
@click.option('--format', 'archive_format', default='zip', type=click.Choice(['zip', 'tar']), help='Archive format')
def archive(folder_path, archive_format):
    """Compress a folder into an archive."""
    folder_path_obj = Path(folder_path)
    if not folder_path_obj.exists() or not folder_path_obj.is_dir():
        click.echo("Error: Folder does not exist or is not a directory.")
        return
    
    if archive_format == 'zip':
        archive_name = f"{folder_path_obj.name}.zip"
        with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in folder_path_obj.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(folder_path_obj.parent)
                    zipf.write(file_path, arcname)
    else:  # tar
        archive_name = f"{folder_path_obj.name}.tar.gz"
        with tarfile.open(archive_name, 'w:gz') as tarf:
            tarf.add(folder_path_obj, arcname=folder_path_obj.name)
    
    click.echo(f"Created archive: {archive_name}")

@file.command()
@click.argument('archive_path')
def extract(archive_path):
    """Extract a .zip or .tar.gz archive."""
    archive_path_obj = Path(archive_path)
    if not archive_path_obj.exists():
        click.echo("Error: Archive file does not exist.")
        return
    
    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            zipf.extractall('.')
            click.echo(f"Extracted {archive_path}")
    elif archive_path.endswith('.tar.gz') or archive_path.endswith('.tgz'):
        with tarfile.open(archive_path, 'r:gz') as tarf:
            tarf.extractall('.')
            click.echo(f"Extracted {archive_path}")
    else:
        click.echo("Error: Unsupported archive format. Use .zip or .tar.gz files.")

# Developer Toolkit Group
@cli.group()
def dev():
    """Developer toolkit commands."""
    pass

@dev.command()
@click.argument('name')
@click.option('--type', 'project_type', default='python', type=click.Choice(['python', 'web', 'node']), help='Project type')
def init(name, project_type):
    """Initialize a new project with boilerplate code."""
    project_path = Path(name)
    if project_path.exists():
        click.echo(f"Error: Directory {name} already exists.")
        return
    
    project_path.mkdir()
    
    if project_type == 'python':
        # Create Python project structure
        (project_path / "main.py").write_text('#!/usr/bin/env python3\n\ndef main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()\n')
        (project_path / "requirements.txt").write_text('# Add your dependencies here\n')
        (project_path / ".gitignore").write_text('__pycache__/\n*.pyc\n*.pyo\n*.pyd\n.Python\nbuild/\ndevelop-eggs/\ndist/\ndownloads/\neggs/\n.eggs/\nlib/\nlib64/\nparts/\nsdist/\nvar/\nwheels/\n*.egg-info/\n.installed.cfg\n*.egg\nMANIFEST\n\n# PyInstaller\n*.manifest\n*.spec\n\n# Unit test / coverage reports\nhtmlcov/\n.tox/\n.coverage\n.coverage.*\n.cache\nnosetests.xml\ncoverage.xml\n*.cover\n.hypothesis/\n.pytest_cache/\n\n# Environments\n.env\n.venv\nenv/\nvenv/\nENV/\nenv.bak/\nvenv.bak/\n')
        click.echo(f"Created Python project: {name}")
        
    elif project_type == 'web':
        # Create web project structure
        (project_path / "index.html").write_text('<!DOCTYPE html>\n<html lang="en">\n<head>\n    <meta charset="UTF-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n    <title>New Web Project</title>\n    <link rel="stylesheet" href="style.css">\n</head>\n<body>\n    <h1>Hello, World!</h1>\n    <script src="script.js"></script>\n</body>\n</html>\n')
        (project_path / "style.css").write_text('body {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n    background-color: #f4f4f4;\n}\n\nh1 {\n    color: #333;\n    text-align: center;\n}\n')
        (project_path / "script.js").write_text('console.log("Hello, World!");\n\ndocument.addEventListener("DOMContentLoaded", function() {\n    console.log("Page loaded!");\n});\n')
        click.echo(f"Created web project: {name}")
        
    elif project_type == 'node':
        # Create Node.js project structure
        package_json = {
            "name": name,
            "version": "1.0.0",
            "description": "",
            "main": "index.js",
            "scripts": {
                "start": "node index.js",
                "test": "echo \"Error: no test specified\" && exit 1"
            },
            "keywords": [],
            "author": "",
            "license": "ISC"
        }
        (project_path / "package.json").write_text(json.dumps(package_json, indent=2))
        (project_path / "index.js").write_text('console.log("Hello, World!");\n')
        (project_path / ".gitignore").write_text('node_modules/\nnpm-debug.log*\nyarn-debug.log*\nyarn-error.log*\n.env\n')
        click.echo(f"Created Node.js project: {name}")

@dev.command()
@click.option('--port', default=8000, help='Port to serve on')
def serve(port):
    """Start a local HTTP server."""
    import http.server
    import socketserver
    
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            click.echo(f"Serving at http://localhost:{port}")
            click.echo("Press Ctrl+C to stop the server")
            httpd.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nServer stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            click.echo(f"Error: Port {port} is already in use. Try a different port.")
        else:
            click.echo(f"Error starting server: {e}")

@dev.command()
@click.argument('path')
def cloc(path):
    """Count Lines of Code in a project."""
    path_obj = Path(path)
    if not path_obj.exists():
        click.echo("Error: Path does not exist.")
        return
    
    # Define language extensions
    language_extensions = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.java': 'Java',
        '.c': 'C',
        '.cpp': 'C++',
        '.h': 'C Header',
        '.css': 'CSS',
        '.html': 'HTML',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.go': 'Go',
        '.rs': 'Rust',
        '.sh': 'Shell',
        '.sql': 'SQL'
    }
    
    stats = defaultdict(lambda: {'files': 0, 'lines': 0, 'blank': 0, 'comments': 0})
    
    for file_path in path_obj.rglob('*'):
        if file_path.is_file() and file_path.suffix in language_extensions:
            language = language_extensions[file_path.suffix]
            stats[language]['files'] += 1
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    stats[language]['lines'] += len(lines)
                    
                    for line in lines:
                        stripped = line.strip()
                        if not stripped:
                            stats[language]['blank'] += 1
                        elif stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('/*'):
                            stats[language]['comments'] += 1
            except:
                continue
    
    if not stats:
        click.echo("No code files found.")
        return
    
    click.echo("Lines of Code Summary:")
    click.echo(f"{'Language':<12} {'Files':<6} {'Lines':<8} {'Blank':<6} {'Comments':<8}")
    click.echo("-" * 50)
    
    total_files = total_lines = total_blank = total_comments = 0
    
    for language, data in sorted(stats.items()):
        click.echo(f"{language:<12} {data['files']:<6} {data['lines']:<8} {data['blank']:<6} {data['comments']:<8}")
        total_files += data['files']
        total_lines += data['lines']
        total_blank += data['blank']
        total_comments += data['comments']
    
    click.echo("-" * 50)
    click.echo(f"{'Total':<12} {total_files:<6} {total_lines:<8} {total_blank:<6} {total_comments:<8}")

@dev.command()
@click.argument('path')
def find_todos(path):
    """Find TODO and FIXME comments in code files."""
    path_obj = Path(path)
    if not path_obj.exists():
        click.echo("Error: Path does not exist.")
        return
    
    code_extensions = {'.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.css', '.html', '.php', '.rb', '.go', '.rs', '.sh'}
    todos_found = 0
    
    for file_path in path_obj.rglob('*'):
        if file_path.is_file() and file_path.suffix in code_extensions:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        line_lower = line.lower()
                        if 'todo:' in line_lower or 'fixme:' in line_lower:
                            relative_path = file_path.relative_to(path_obj)
                            click.echo(f"{relative_path}:{line_num}: {line.strip()}")
                            todos_found += 1
            except:
                continue
    
    if todos_found == 0:
        click.echo("No TODO or FIXME comments found.")
    else:
        click.echo(f"\nFound {todos_found} TODO/FIXME comments.")

@dev.command()
def git_summary():
    """Show Git repository summary."""
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True, check=True)
        
        # Get current branch
        branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                     capture_output=True, text=True)
        current_branch = branch_result.stdout.strip() or "detached HEAD"
        
        # Get status
        status_result = subprocess.run(['git', 'status', '--porcelain'], 
                                     capture_output=True, text=True)
        uncommitted_changes = len(status_result.stdout.strip().split('\n')) if status_result.stdout.strip() else 0
        
        # Get last 3 commits
        log_result = subprocess.run(['git', 'log', '--oneline', '-3'], 
                                  capture_output=True, text=True)
        
        click.echo("=== Git Repository Summary ===")
        click.echo(f"Current branch: {current_branch}")
        click.echo(f"Uncommitted changes: {uncommitted_changes} files")
        click.echo("\nLast 3 commits:")
        if log_result.stdout.strip():
            for line in log_result.stdout.strip().split('\n'):
                click.echo(f"  {line}")
        else:
            click.echo("  No commits found")
            
    except subprocess.CalledProcessError:
        click.echo("Error: Not a git repository or git not available.")
    except FileNotFoundError:
        click.echo("Error: Git command not found. Please install Git.")

# Conversion Group
@cli.group()
def convert():
    """Content conversion commands."""
    pass

@convert.command()
@click.argument('path')
@click.option('--to', 'target_format', required=True, type=click.Choice(['png', 'jpg', 'webp']), help='Target format')
@click.option('--quality', default=95, type=int, help='Quality for lossy formats (1-100)')
def img(path, target_format, quality):
    """Convert images to different formats."""
    try:
        from PIL import Image
    except ImportError:
        click.echo("Error: Pillow library not installed. Run 'pip install Pillow'")
        return
    
    path_obj = Path(path)
    if not path_obj.exists():
        click.echo("Error: Path does not exist.")
        return
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'}
    converted_count = 0
    
    files_to_process = []
    if path_obj.is_file():
        files_to_process = [path_obj]
    else:
        files_to_process = [f for f in path_obj.rglob('*') if f.is_file() and f.suffix.lower() in image_extensions]
    
    for file_path in files_to_process:
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB for formats that don't support transparency
                if target_format in ['jpg'] and img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                
                output_path = file_path.with_suffix(f'.{target_format}')
                
                save_kwargs = {}
                if target_format in ['jpg', 'webp']:
                    save_kwargs['quality'] = quality
                    save_kwargs['optimize'] = True
                
                img.save(output_path, format=target_format.upper(), **save_kwargs)
                click.echo(f"Converted: {file_path.name} -> {output_path.name}")
                converted_count += 1
                
        except Exception as e:
            click.echo(f"Error converting {file_path}: {e}")
    
    click.echo(f"Converted {converted_count} images to {target_format}")

@convert.command()
@click.argument('video_file')
@click.option('--output', default=None, help='Output audio file name')
def extract_audio(video_file, output):
    """Extract audio track from video file."""
    try:
        from moviepy.editor import VideoFileClip
    except ImportError:
        click.echo("Error: moviepy library not installed. Run 'pip install moviepy'")
        return
    
    video_path = Path(video_file)
    if not video_path.exists():
        click.echo("Error: Video file does not exist.")
        return
    
    if output is None:
        output = video_path.with_suffix('.mp3').name
    
    try:
        with VideoFileClip(str(video_path)) as video:
            audio = video.audio
            audio.write_audiofile(output)
            click.echo(f"Extracted audio: {video_file} -> {output}")
    except Exception as e:
        click.echo(f"Error extracting audio: {e}")

@convert.command()
@click.option('--output', required=True, help='Output PDF file name')
def pdf_merge(output):
    """Merge multiple PDF files into one."""
    try:
        import PyPDF2
    except ImportError:
        click.echo("Error: PyPDF2 library not installed. Run 'pip install PyPDF2'")
        return
    
    pdf_files = []
    click.echo("Enter PDF file paths (press Enter with empty line to finish):")
    
    while True:
        file_path = click.prompt("PDF file", default="", show_default=False)
        if not file_path:
            break
        
        path_obj = Path(file_path)
        if path_obj.exists() and path_obj.suffix.lower() == '.pdf':
            pdf_files.append(path_obj)
        else:
            click.echo("File not found or not a PDF. Skipping.")
    
    if not pdf_files:
        click.echo("No valid PDF files provided.")
        return
    
    try:
        merger = PyPDF2.PdfMerger()
        
        for pdf_file in pdf_files:
            merger.append(str(pdf_file))
            click.echo(f"Added: {pdf_file}")
        
        with open(output, 'wb') as output_file:
            merger.write(output_file)
        
        merger.close()
        click.echo(f"Merged {len(pdf_files)} PDFs into: {output}")
        
    except Exception as e:
        click.echo(f"Error merging PDFs: {e}")

@convert.command()
@click.argument('text')
@click.option('--output', required=True, help='Output image file name')
def qr(text, output):
    """Generate QR code from text."""
    try:
        import qrcode
    except ImportError:
        click.echo("Error: qrcode library not installed. Run 'pip install qrcode[pil]'")
        return
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output)
    click.echo(f"QR code generated: {output}")

# Data Dashboard Group
@cli.group()
def data():
    """Data dashboard commands for fetching external data."""
    pass

@data.command()
@click.argument('city')
def weather(city):
    """Get current weather for a city."""
    config_data = load_config()
    api_key = config_data['api_keys']['weather_api_key']
    
    if not check_api_key(config_data, 'api_keys.weather_api_key', 'Weather'):
        return
    
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        weather_desc = data['weather'][0]['description'].title()
        temp = data['main']['temp']
        feels_like = data['main']['feels_like']
        humidity = data['main']['humidity']
        
        click.echo(f"Weather in {city}:")
        click.echo(f"  Description: {weather_desc}")
        click.echo(f"  Temperature: {temp}°C (feels like {feels_like}°C)")
        click.echo(f"  Humidity: {humidity}%")
        
    except requests.exceptions.RequestException as e:
        click.echo(f"Error fetching weather data: {e}")
    except KeyError:
        click.echo("Error: Invalid city name or API response format.")

@data.command()
@click.argument('tickers', nargs=-1, required=True)
def stock(tickers):
    """Get current stock prices for one or more tickers."""
    config_data = load_config()
    api_key = config_data['api_keys']['alpha_vantage_api_key']
    
    if not check_api_key(config_data, 'api_keys.alpha_vantage_api_key', 'Alpha Vantage'):
        return
    
    try:
        from alpha_vantage.timeseries import TimeSeries
        ts = TimeSeries(key=api_key, output_format='pandas')
        
        for ticker in tickers:
            try:
                data, meta_data = ts.get_quote_endpoint(symbol=ticker)
                price = float(data['05. price'])
                change = float(data['09. change'])
                change_percent = float(data['10. change percent'].rstrip('%'))
                
                change_sign = "+" if change >= 0 else ""
                click.echo(f"{ticker.upper()}: ${price:.2f} ({change_sign}{change:.2f}, {change_sign}{change_percent:.2f}%)")
                
            except Exception as e:
                click.echo(f"Error fetching data for {ticker}: {e}")
                
    except ImportError:
        click.echo("Error: alpha_vantage library not installed. Run 'pip install alpha_vantage'")

@data.command()
@click.option('--query', default=None, help='Search query for news')
@click.option('--country', default='us', type=click.Choice(['us', 'gb', 'ca', 'au']), help='Country for top headlines')
def news(query, country):
    """Get top news headlines."""
    config_data = load_config()
    api_key = config_data['api_keys']['news_api_key']
    
    if not check_api_key(config_data, 'api_keys.news_api_key', 'News API'):
        return
    
    try:
        from newsapi import NewsApiClient
        newsapi = NewsApiClient(api_key=api_key)
        
        if query:
            articles = newsapi.get_everything(q=query, language='en', sort_by='relevancy', page_size=5)
        else:
            articles = newsapi.get_top_headlines(country=country, page_size=5)
        
        if articles['status'] == 'ok' and articles['articles']:
            click.echo(f"Top {'search results' if query else 'headlines'}:")
            for i, article in enumerate(articles['articles'], 1):
                click.echo(f"{i}. {article['title']}")
                click.echo(f"   Source: {article['source']['name']}")
                if article.get('description'):
                    click.echo(f"   {article['description'][:100]}...")
                click.echo()
        else:
            click.echo("No articles found.")
            
    except ImportError:
        click.echo("Error: newsapi-python library not installed. Run 'pip install newsapi-python'")
    except Exception as e:
        click.echo(f"Error fetching news: {e}")

@data.command()
@click.argument('url')
def shorten_url(url):
    """Shorten a URL using a public API."""
    # Using TinyURL as a simple, free API
    api_url = f"http://tinyurl.com/api-create.php?url={url}"
    
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            short_url = response.text.strip()
            if short_url.startswith('http'):
                click.echo(f"Original: {url}")
                click.echo(f"Shortened: {short_url}")
            else:
                click.echo(f"Error: {short_url}")
        else:
            click.echo("Error: Failed to shorten URL")
    except requests.exceptions.RequestException as e:
        click.echo(f"Error: {e}")

# Cloud Integration Group
@cli.group()
def cloud():
    """Cloud storage integration commands."""
    pass

def get_s3_client(config_data):
    """Get configured S3 client."""
    aws_config = config_data['aws_credentials']
    
    if (not check_api_key(config_data, 'aws_credentials.aws_access_key_id', 'AWS Access Key') or
        not check_api_key(config_data, 'aws_credentials.aws_secret_access_key', 'AWS Secret Key') or
        not check_api_key(config_data, 'aws_credentials.default_s3_bucket', 'Default S3 Bucket')):
        return None, None
    
    try:
        import boto3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_config['aws_access_key_id'],
            aws_secret_access_key=aws_config['aws_secret_access_key']
        )
        return s3_client, aws_config['default_s3_bucket']
    except ImportError:
        click.echo("Error: boto3 library not installed. Run 'pip install boto3'")
        return None, None

@cloud.command()
@click.argument('s3_path', default='')
def ls(s3_path):
    """List files in S3 bucket."""
    config_data = load_config()
    s3_client, default_bucket = get_s3_client(config_data)
    
    if not s3_client:
        return
    
    # Parse s3_path
    if s3_path.startswith('s3://'):
        parts = s3_path[5:].split('/', 1)
        bucket = parts[0]
        prefix = parts[1] if len(parts) > 1 else ''
    else:
        bucket = default_bucket
        prefix = s3_path
    
    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        
        if 'Contents' in response:
            click.echo(f"Files in s3://{bucket}/{prefix}:")
            for obj in response['Contents']:
                size = obj['Size']
                modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                click.echo(f"  {size:>10} {modified} {obj['Key']}")
        else:
            click.echo("No files found.")
            
    except Exception as e:
        click.echo(f"Error listing S3 files: {e}")

@cloud.command()
@click.argument('local_file')
@click.argument('s3_path', default='')
def upload(local_file, s3_path):
    """Upload a file to S3."""
    config_data = load_config()
    s3_client, default_bucket = get_s3_client(config_data)
    
    if not s3_client:
        return
    
    local_path = Path(local_file)
    if not local_path.exists():
        click.echo("Error: Local file does not exist.")
        return
    
    # Parse s3_path
    if s3_path.startswith('s3://'):
        parts = s3_path[5:].split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else local_path.name
    else:
        bucket = default_bucket
        key = s3_path if s3_path else local_path.name
    
    try:
        s3_client.upload_file(str(local_path), bucket, key)
        click.echo(f"Uploaded: {local_file} -> s3://{bucket}/{key}")
    except Exception as e:
        click.echo(f"Error uploading file: {e}")

@cloud.command()
@click.argument('s3_path')
@click.argument('local_path', default='')
def download(s3_path, local_path):
    """Download a file from S3."""
    config_data = load_config()
    s3_client, default_bucket = get_s3_client(config_data)
    
    if not s3_client:
        return
    
    # Parse s3_path
    if s3_path.startswith('s3://'):
        parts = s3_path[5:].split('/', 1)
        bucket = parts[0]
        key = parts[1]
    else:
        bucket = default_bucket
        key = s3_path
    
    if not local_path:
        local_path = Path(key).name
    
    try:
        s3_client.download_file(bucket, key, local_path)
        click.echo(f"Downloaded: s3://{bucket}/{key} -> {local_path}")
    except Exception as e:
        click.echo(f"Error downloading file: {e}")

# Security & Crypto Group
@cli.group()
def crypto():
    """Security and cryptographic commands."""
    pass

@crypto.command()
@click.argument('input_data')
@click.option('--algo', default='sha256', type=click.Choice(['sha256', 'md5']), help='Hash algorithm')
def hash(input_data, algo):
    """Calculate hash of a file or string."""
    path_obj = Path(input_data)
    
    if path_obj.exists() and path_obj.is_file():
        # Hash a file
        hash_obj = hashlib.sha256() if algo == 'sha256' else hashlib.md5()
        
        with open(path_obj, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        hash_value = hash_obj.hexdigest()
        click.echo(f"{algo.upper()} hash of file '{input_data}': {hash_value}")
    else:
        # Hash a string
        hash_obj = hashlib.sha256() if algo == 'sha256' else hashlib.md5()
        hash_obj.update(input_data.encode('utf-8'))
        hash_value = hash_obj.hexdigest()
        click.echo(f"{algo.upper()} hash of string: {hash_value}")

@crypto.command()
@click.option('--length', default=16, help='Password length')
def passwd(length):
    """Generate a strong random password."""
    if length < 4:
        click.echo("Error: Password length must be at least 4 characters.")
        return
    
    # Ensure we have at least one character from each category
    uppercase = string.ascii_uppercase
    lowercase = string.ascii_lowercase
    digits = string.digits
    symbols = "!@#$%^&*"
    
    password = [
        secrets.choice(uppercase),
        secrets.choice(lowercase),
        secrets.choice(digits),
        secrets.choice(symbols)
    ]
    
    # Fill the rest randomly
    all_chars = uppercase + lowercase + digits + symbols
    for _ in range(length - 4):
        password.append(secrets.choice(all_chars))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    final_password = ''.join(password)
    
    click.echo(f"Generated password: {final_password}")

@crypto.command()
@click.argument('domain')
def whois(domain):
    """Perform WHOIS lookup for a domain."""
    try:
        import whois as whois_lib
        
        w = whois_lib.whois(domain)
        
        click.echo(f"WHOIS information for {domain}:")
        click.echo(f"Registrar: {w.registrar}")
        click.echo(f"Creation date: {w.creation_date}")
        click.echo(f"Expiration date: {w.expiration_date}")
        click.echo(f"Name servers: {w.name_servers}")
        
        if w.emails:
            click.echo(f"Contact emails: {', '.join(w.emails)}")
            
    except ImportError:
        click.echo("Error: python-whois library not installed. Run 'pip install python-whois'")
    except Exception as e:
        click.echo(f"Error performing WHOIS lookup: {e}")

if __name__ == '__main__':
    cli()