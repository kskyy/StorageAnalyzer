################################################################################################################
#                                                   author: kskyy                                              #
#                                                                                                              #
#       This script scans a chosen directory and calculates how much disk space each folder or file takes.     #
#       It lists them sorted from largest to smallest, and you can set how many levels deep it should analyze. #   
#       The result shows a clear overview of which folders use the most space.                                 #          
#                                                                                                              #
#                                              USAGE: StorageAnalyzer.py -d [depth] path                       @
#                                                                                                              #
################################################################################################################

import os
import argparse
from tqdm import tqdm

def count_files(root):
    total = 0
    for _, _, files in os.walk(root):
        total += len(files)
    return total

def compute_dir(path, children_map, dir_size_map, pbar=None):
    """Zwraca łączny rozmiar dir i buduje mapę dzieci (do późniejszego drukowania)."""
    total = 0
    items = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        child_total = compute_dir(entry.path, children_map, dir_size_map, pbar)
                        items.append((entry.name, child_total, entry.path, True))
                        total += child_total
                    else:
                        size = entry.stat(follow_symlinks=False).st_size
                        items.append((entry.name, size, None, False))
                        total += size
                        if pbar:
                            pbar.update(1)
                except (PermissionError, FileNotFoundError):
                    continue
    except (PermissionError, FileNotFoundError):
        pass
    children_map[path] = items
    dir_size_map[path] = total
    return total

def print_tree(root, children_map, max_depth, indent=0, current_depth=1):
    items = children_map.get(root, [])
    items.sort(key=lambda x: x[1], reverse=True)
    for name, size, child_path, is_dir in items:
        print(" " * indent + f"{name:30} {size / (1024*1024):10.2f} MB")
        if is_dir and current_depth < max_depth:
            print_tree(child_path, children_map, max_depth, indent + 4, current_depth + 1)

def main():
    parser = argparse.ArgumentParser(description="Disk usage analyzer with progress bar")
    parser.add_argument("path", help="Starting path")
    parser.add_argument("-d", "--depth", type=int, default=1, help="Max depth (default 1)")
    args = parser.parse_args()

    root = os.path.abspath(args.path)
    total_files = count_files(root)
    children_map, dir_size_map = {}, {}

    # Pasek postępu działa na liczbie plików (każdy liczony raz)
    with tqdm(total=total_files or 1, desc="Scanning files", unit="file") as pbar:
        compute_dir(root, children_map, dir_size_map, pbar)

    print(f"\nAnaliza: {root} (poziom={args.depth})\n")
    print_tree(root, children_map, args.depth)

    total_bytes = dir_size_map.get(root, 0)
    print(f"\nŁączny rozmiar pod korzeniem: {total_bytes / (1024*1024):.2f} MB")

if __name__ == "__main__":
    main()