import os
import sys

def tree(directory, prefix="", exclude=None, show_files=True):
    if exclude is None:
        exclude = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', '.idea', '.vscode', '.DS_Store'}
    try:
        items = sorted(os.listdir(directory))
    except PermissionError:
        return
    for i, item in enumerate(items):
        path = os.path.join(directory, item)
        # Excluir directorios/archivos no deseados
        if item in exclude or (os.path.isdir(path) and item.startswith('.')):
            continue
        connector = "├── " if i < len(items)-1 else "└── "
        print(prefix + connector + item)
        if os.path.isdir(path):
            extension = "│   " if i < len(items)-1 else "    "
            tree(path, prefix + extension, exclude, show_files)

if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    print(os.path.basename(os.path.abspath(root)) + "/")
    tree(root)