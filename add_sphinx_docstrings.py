#!/usr/bin/env python3
"""
Script to add Sphinx docstrings to files in the Alt codebase.

This script helps automate the process of adding Sphinx-compatible docstrings 
to Python files in the Alt codebase, following these guidelines:

1. Module docstrings at the top of each file
2. Class docstrings with Attributes sections
3. Method docstrings with Args, Returns, Raises sections
4. Enum docstrings with descriptions of each value

Usage:
    python add_sphinx_docstrings.py [directory]

If no directory is specified, it defaults to the current src/ directory.
"""

import os
import sys
import argparse
import re
from typing import List, Dict, Optional, Tuple


def is_already_documented(file_content: str) -> bool:
    """
    Check if a file already has Sphinx-style docstrings.
    
    Args:
        file_content: Content of the file to check
        
    Returns:
        bool: True if file appears to have Sphinx docstrings
    """
    # Look for triple-quote docstrings with module-level documentation at the start
    module_docstring_pattern = r'^\s*"""[\s\S]+?"""'
    has_module_docstring = bool(re.match(module_docstring_pattern, file_content))
    
    # For smaller files like scripts, just having a module docstring is enough
    if has_module_docstring and len(file_content.splitlines()) < 50:
        return True
        
    # For more complex files, we also want to see class or function docstrings
    if has_module_docstring:
        # Look for Sphinx-specific patterns in the module docstring
        sphinx_patterns = [
            r'Args:', r'Returns:', r'Raises:', r'Attributes:', 
            r':param', r':return', r':raises', r':type', r':rtype',
            r'.. note::', r'.. warning::', r'.. seealso::'
        ]
        
        for pattern in sphinx_patterns:
            if re.search(pattern, file_content):
                return True
        
        # Check if any class has a docstring
        class_pattern = r'class\s+\w+[^:]*:'
        docstring_after_pattern = r'\s+"""[\s\S]+?"""'
        
        classes = re.finditer(class_pattern, file_content)
        for match in classes:
            pos = match.end()
            # Check for a docstring following the class declaration
            docstring_match = re.match(docstring_after_pattern, file_content[pos:])
            if docstring_match:
                # If we found a class docstring, check if it has Sphinx patterns
                docstring_text = docstring_match.group(0)
                for pattern in sphinx_patterns:
                    if re.search(pattern, docstring_text):
                        return True
                
        # Check if any function has a docstring
        function_pattern = r'def\s+\w+\s*\([^)]*\)\s*[->]?[^:]*:'
        functions = re.finditer(function_pattern, file_content)
        for match in functions:
            pos = match.end()
            # Check for a docstring following the function declaration
            docstring_match = re.match(docstring_after_pattern, file_content[pos:])
            if docstring_match:
                # If we found a function docstring, check if it has Sphinx patterns
                docstring_text = docstring_match.group(0)
                for pattern in sphinx_patterns:
                    if re.search(pattern, docstring_text):
                        return True
    
    return False


def find_py_files(directory: str) -> List[str]:
    """
    Find all Python files in a directory and its subdirectories.
    
    Args:
        directory: Root directory to search
        
    Returns:
        List[str]: List of file paths
    """
    if not os.path.isdir(directory):
        # If input is a single file, just return that file if it's a Python file
        if os.path.isfile(directory) and directory.endswith('.py'):
            return [directory]
        return []
        
    py_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))
    return py_files


def create_module_docstring(filename: str) -> str:
    """
    Create a module-level docstring based on the filename.
    
    Args:
        filename: Name of the Python file
        
    Returns:
        str: Generated module docstring
    """
    module_name = os.path.splitext(os.path.basename(filename))[0]
    
    # Convert snake_case to Title Case
    title = ' '.join(word.capitalize() for word in module_name.split('_'))
    
    docstring = f'''"""
{title} Module - [Brief description of module purpose]

This module provides [detailed description of what the module does and its purpose].

[Additional details about usage, examples, or notes if applicable]
"""
'''
    return docstring


def check_file_documentation_status(file_path: str) -> Tuple[bool, str]:
    """
    Check if a file has Sphinx docstrings.
    
    Args:
        file_path: Path to the Python file to check
        
    Returns:
        Tuple[bool, str]: (is_documented, error_message)
        First value is True if the file has Sphinx docstrings, False otherwise.
        Second value contains any error message (empty string if no error).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return is_already_documented(content), ""
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(description='Add Sphinx docstrings to Python files')
    parser.add_argument('directory', nargs='?', default='src',
                        help='Directory to search for Python files (default: src)')
    parser.add_argument('--output', '-o', default=None,
                        help='Output file to write list of undocumented files')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Print detailed information')
    parser.add_argument('--check', '-c', action='store_true',
                        help='Check documentation status without modifying files')
    parser.add_argument('--update-status', '-u', default=None,
                        help='Output file to write updated documentation status')
    args = parser.parse_args()
    
    py_files = find_py_files(args.directory)
    if args.verbose:
        print(f"Found {len(py_files)} Python files")
    
    undocumented_files = []
    documented_files = []
    error_files = []
    
    for file_path in py_files:
        is_documented, error = check_file_documentation_status(file_path)
        
        if error:
            error_files.append((file_path, error))
            if args.verbose:
                print(f"Error processing {file_path}: {error}")
            continue
            
        if is_documented:
            documented_files.append(file_path)
            if args.verbose:
                print(f"Skipping {file_path} - already documented")
        else:
            undocumented_files.append(file_path)
            if args.verbose:
                print(f"Need to document: {file_path}")
    
    # Print summary
    print(f"Total files: {len(py_files)}")
    print(f"Documented files: {len(documented_files)}")
    print(f"Undocumented files: {len(undocumented_files)}")
    print(f"Error files: {len(error_files)}")
    
    # Output undocumented files to file if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            for file_path in undocumented_files:
                f.write(f"{file_path}\n")
        print(f"Undocumented file list written to {args.output}")
    
    # Output updated status if requested
    if args.update_status:
        with open(args.update_status, 'w', encoding='utf-8') as f:
            f.write("# Documentation Status\n\n")
            f.write(f"Last updated: {sys.argv[0]} at {sys.argv}\n\n")
            
            f.write("## Documented Files\n\n")
            for file_path in sorted(documented_files):
                f.write(f"- {file_path}\n")
                
            f.write("\n## Undocumented Files\n\n")
            for file_path in sorted(undocumented_files):
                f.write(f"- {file_path}\n")
                
            if error_files:
                f.write("\n## Files with Errors\n\n")
                for file_path, error in sorted(error_files):
                    f.write(f"- {file_path} - {error}\n")
                    
        print(f"Updated documentation status written to {args.update_status}")
    
    # Print undocumented files to stdout if no output file
    if not args.output and not args.check:
        for file_path in undocumented_files:
            print(file_path)


if __name__ == '__main__':
    main()