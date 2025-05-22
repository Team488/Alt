import shutil
from pathlib import Path

NAMESPACE_PKGS = [
    "Alt-Core",
    "Alt-Cameras",
    "Alt-Dashboard",
    "Alt-ObjectLocalization",
    "Alt-Pathplanning",
]

OUTPUT_ROOT = Path("docs/source/api")
SHOW_PRIVATE = False

def strip_alt_prefix(pkg_path: Path):
    return pkg_path.name.replace("Alt-", "")

def get_module_path(src_dir: Path, py_file: Path):
    return py_file.relative_to(src_dir).with_suffix("")  # Path object

def should_skip(py_file: Path):
    return py_file.name == "__init__.py" or (not SHOW_PRIVATE and py_file.name.startswith("_"))

def write_module_rst(file_name, full_module_name: str, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""{file_name}
{'=' * len(file_name)}

.. automodule:: {full_module_name}
   :members:
   :undoc-members:
   :show-inheritance:
"""
    out_path.write_text(content, encoding="utf-8")

def write_index_rst(folder_path: Path):
    """Generates an index.rst inside `folder_path` that links all .rst files and subfolders."""
    index_path = folder_path / "index.rst"
    title = folder_path.name
    content = f"""{title}
{'=' * len(title)}
.. toctree::
   :maxdepth: 2
   :caption: {title}

"""

    # List .rst files (excluding index.rst)
    for f in sorted(folder_path.glob("*.rst")):
        if f.name != "index.rst":
            content += f"   {f.stem}\n"

    # List subfolders with their own index.rst
    for subdir in sorted(folder_path.iterdir()):
        if subdir.is_dir() and (subdir / "index.rst").exists():
            content += f"   {subdir.name}/index\n"

    index_path.write_text(content, encoding="utf-8")

def write_package_tree(pkg_path: Path, namespace_name: str, src_dir: Path):
    out_root = OUTPUT_ROOT

    for py_file in src_dir.rglob("*.py"):
        if should_skip(py_file):
            continue
        rel_path = get_module_path(src_dir, py_file)
        file_name = rel_path.name
        full_module_name = ".".join(["Alt"] + list(rel_path.parts))  # full dotted path
        rst_out_path = out_root / rel_path.with_suffix(".rst")
        write_module_rst(file_name, full_module_name, rst_out_path)

    # Create index.rst recursively
    for dir_path in sorted(out_root.rglob("*"), key=lambda p: -len(p.parts)):
        if dir_path.is_dir():
            write_index_rst(dir_path)

    # Use README.md at the namespace level as the top-level description
#     readme = pkg_path / "README.md"
#     if readme.exists():
#         readme_rst = f""".. include:: {readme.resolve()}
#    :parser: markdown

# """
#         top_index = out_root / "index.rst"
#         try:
#             existing = top_index.read_text(encoding="utf-8")
#         except FileNotFoundError:
#             existing = ""
#         top_index.write_text(readme_rst + "\n" + existing, encoding="utf-8")

def write_global_index(namespace_names: list[str]):
    index_path = OUTPUT_ROOT / "index.rst"
    content = """API Reference
=============

.. toctree::
   :maxdepth: 1
   :caption: Namespaces

"""
    for name in namespace_names:
        content += f"   {name}/index\n"

    index_path.write_text(content, encoding="utf-8")

# Main process
if __name__ == "__main__":
    # try delete old api dir
    try:
        shutil.rmtree(str(OUTPUT_ROOT))
    except Exception as e:
        pass


    namespace_names = []

    for pkg_str in NAMESPACE_PKGS:
        pkg_path = Path(pkg_str).resolve()
        namespace_name = strip_alt_prefix(pkg_path)
        namespace_names.append(namespace_name)

        src_dir = pkg_path / "src" / "Alt"
        if not src_dir.exists():
            print(f"⚠️ Skipping {namespace_name}, no Alt/ found in {src_dir}")
            continue

        write_package_tree(pkg_path, namespace_name, src_dir)

    write_global_index(namespace_names)
    print(f"\n✅ Done. Full recursive structure built in: {OUTPUT_ROOT.resolve()}")
