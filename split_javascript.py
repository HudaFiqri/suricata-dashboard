#!/usr/bin/env python3
"""
Split JavaScript sections from config.html into separate module files
"""
import re
from pathlib import Path

def find_js_sections(lines):
    """Find all JavaScript sections marked with // ===="""
    sections = []
    current_section = None

    for i, line in enumerate(lines):
        # Check for section header
        if line.strip().startswith('// ====='):
            # Extract section name
            match = re.search(r'// =+ (.*?) (Configuration|Config|\(Moved)', line)
            if match:
                section_name = match.group(1).strip()

                # Save previous section
                if current_section:
                    current_section['end'] = i
                    sections.append(current_section)

                # Start new section
                current_section = {
                    'name': section_name,
                    'start': i,
                    'end': None
                }

        # Check for end of script tag
        elif line.strip() == '</script>' and current_section:
            current_section['end'] = i
            sections.append(current_section)
            current_section = None

    return sections

def extract_js_section(lines, start, end):
    """Extract JavaScript code between start and end"""
    return lines[start:end]

def section_to_filename(section_name):
    """Convert section name to filename"""
    name_map = {
        'App Layer': 'app-layer',
        'Outputs': 'outputs',
        'Stream': 'stream',
        'Variables': 'vars',
        'Host': 'host',
        'IPS/Preventive': 'ips',
        'Interface': 'interfaces',
        'Logging': 'logging',
        'Detection': 'detection'
    }
    return name_map.get(section_name, section_name.lower().replace(' ', '-'))

def split_javascript():
    """Split JavaScript from config.html"""
    config_path = Path('templates/config.html')

    with open(config_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find JavaScript sections
    sections = find_js_sections(lines)

    print(f"Found {len(sections)} JavaScript sections:\n")

    extracted_sections = {}

    for section in sections:
        # Skip sections that are already moved
        if 'Moved' in lines[section['start']]:
            print(f"[OK] {section['name']}: Already moved")
            continue

        # Skip very small sections (< 50 lines)
        section_lines = section['end'] - section['start']
        if section_lines < 50:
            print(f"[OK] {section['name']}: Too small ({section_lines} lines), keeping inline")
            continue

        filename = section_to_filename(section['name'])

        # Extract JavaScript code
        js_code = extract_js_section(lines, section['start'], section['end'])

        # Create module structure
        module_code = f"""/**
 * {section['name']} Configuration Module
 * Extracted from config.html
 */

const {filename.replace('-', '').title()}Config = (function() {{
    'use strict';

"""

        # Add the extracted code (skip the header comment line)
        for line in js_code[1:]:
            module_code += line

        module_code += f"""
    // Public API
    return {{
        init: function() {{
            console.log('{section['name']} module initialized');
        }}
    }};
}})();

// Initialize when document is ready
$(document).ready(function() {{
    {filename.replace('-', '').title()}Config.init();
}});
"""

        # Save to file
        output_file = Path(f'static/js/config/{filename}.js')
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(module_code)

        extracted_sections[section['name']] = {
            'filename': filename,
            'file': output_file,
            'start': section['start'],
            'end': section['end'],
            'lines': section_lines
        }

        print(f"[OK] {section['name']}: Extracted {section_lines} lines to {output_file}")

    # Update config.html with script includes
    if extracted_sections:
        new_lines = []
        skip_until = -1

        for i, line in enumerate(lines):
            # Check if we should skip (inside an extracted section)
            if i < skip_until:
                continue

            # Check if this line starts an extracted section
            is_extracted = False
            for section_name, info in extracted_sections.items():
                if i == info['start']:
                    # Add comment indicating extraction
                    new_lines.append(
                        f"// {section_name} Configuration (Moved to "
                        f"{info['filename']}.js)\n"
                    )
                    skip_until = info['end']
                    is_extracted = True
                    break

            if not is_extracted:
                new_lines.append(line)

        # Add script includes before </script> tag
        script_includes = []
        for section_name, info in extracted_sections.items():
            script_includes.append(
                f"<script src=\"{{{{ url_for('static', "
                f"filename='js/config/{info['filename']}.js') }}}}\"></script>\n"
            )

        # Find {% block scripts %} and add includes there
        for i, line in enumerate(new_lines):
            if '{% block scripts %}' in line:
                # Insert after existing script includes
                insert_at = i + 3  # After utils.js and packet-capture.js
                new_lines = (
                    new_lines[:insert_at] +
                    script_includes +
                    new_lines[insert_at:]
                )
                break

        # Save updated config.html
        with open(config_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        print(f"\n[OK] Updated config.html: {len(new_lines)} lines (was {len(lines)})")
        print(f"     Reduction: {len(lines) - len(new_lines)} lines")

    return extracted_sections

if __name__ == '__main__':
    extracted = split_javascript()

    print("\n=== Summary ===")
    total_extracted = sum(info['lines'] for info in extracted.values())
    print(f"Total sections extracted: {len(extracted)}")
    print(f"Total lines extracted: {total_extracted}")
    print("\nJavaScript modules created:")
    for section_name, info in extracted.items():
        print(f"  - {info['file']} ({info['lines']} lines)")
