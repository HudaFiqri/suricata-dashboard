#!/usr/bin/env python3
"""
Split config.html into modular partial templates
"""
import re
from pathlib import Path

def extract_modal(lines, start_idx, modal_name):
    """Extract a modal from lines starting at start_idx"""
    modal_lines = []
    indent_level = 0
    found_start = False

    for i in range(start_idx, len(lines)):
        line = lines[i]

        # Track div depth
        if '<div' in line:
            if not found_start:
                found_start = True
            indent_level += line.count('<div')

        modal_lines.append(line)

        if '</div>' in line:
            indent_level -= line.count('</div>')
            if found_start and indent_level <= 0:
                break

    return modal_lines, i + 1

def split_config_html():
    """Split config.html into modular files"""
    config_path = Path('templates/config.html')

    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find all modals
    modals = {
        'app-layer': 'App Layer Config Modal',
        'outputs': 'Outputs Config Modal',
        'logging': 'Logging Modal',
        'detection': 'Detection Modal',
        'packet-capture': 'Packet Capture Modal',
        'stream': 'Stream Modal',
        'host': 'Host Modal',
        'ips': 'IPS/Preventive Modal',
        'interface': 'Interface Modal',
        'vars': 'Variables Modal'
    }

    modal_files = {}

    for modal_key, modal_comment in modals.items():
        # Find modal start
        for i, line in enumerate(lines):
            if f'<!-- {modal_comment} -->' in line:
                print(f"Found {modal_key} modal at line {i+1}")

                # Extract modal
                modal_lines, end_idx = extract_modal(lines, i, modal_key)

                # Save to file
                modal_file = Path(f'templates/config/modals/{modal_key}.html')
                with open(modal_file, 'w', encoding='utf-8') as f:
                    f.writelines(modal_lines)

                modal_files[modal_key] = {
                    'start': i,
                    'end': end_idx,
                    'file': modal_file,
                    'lines': len(modal_lines)
                }

                print(f"  Extracted {len(modal_lines)} lines to {modal_file}")
                break

    # Now create new config.html with includes
    new_lines = []
    skip_until = -1

    for i, line in enumerate(lines):
        if i < skip_until:
            continue

        # Check if this is a modal start
        is_modal = False
        for modal_key, info in modal_files.items():
            if i == info['start']:
                # Replace with include
                new_lines.append(
                    f"{{% include 'config/modals/{modal_key}.html' %}}\n"
                )
                skip_until = info['end']
                is_modal = True
                break

        if not is_modal:
            new_lines.append(line)

    # Save new config.html
    backup_path = Path('templates/config.html.backup')
    config_path.rename(backup_path)
    print(f"\nBackup created: {backup_path}")

    with open(config_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"\nNew config.html written: {len(new_lines)} lines")
    print(f"Original: {len(lines)} lines")
    print(f"Reduction: {len(lines) - len(new_lines)} lines")

    return modal_files

if __name__ == '__main__':
    modal_files = split_config_html()

    print("\n=== Summary ===")
    total_extracted = sum(info['lines'] for info in modal_files.values())
    print(f"Total modals extracted: {len(modal_files)}")
    print(f"Total lines extracted: {total_extracted}")
    print("\nModal files created:")
    for modal_key, info in modal_files.items():
        print(f"  - {info['file']} ({info['lines']} lines)")
