#!/usr/bin/env python3
import os
import sys

def print_tree(start_path, prefix="", exclude_file=None):
    """Rekursiv funktion som skriver ut filträdet."""
    items = sorted(os.listdir(start_path))
    if exclude_file and exclude_file in items:
        items.remove(exclude_file)

    pointers = ["├── "] * (len(items) - 1) + ["└── "]
    
    for pointer, item in zip(pointers, items):
        path = os.path.join(start_path, item)
        print(prefix + pointer + item)
        if os.path.isdir(path):
            extension = "│   " if pointer == "├── " else "    "
            print_tree(path, prefix + extension, exclude_file)

def main():
    start_dir = os.getcwd()  # aktuell mapp
    exclude_file = os.path.basename(sys.argv[0])  # namnet på detta skript
    print(f"Filträd för: {start_dir}\n")
    print_tree(start_dir, exclude_file=exclude_file)

if __name__ == "__main__":
    main()
