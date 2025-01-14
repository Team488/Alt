#!/usr/bin/env bash
set -e

# This script assumes you have edited the `requirements.txt`
# file in the current directory with a new dependency.
# It will create a new python environment and then it will
# do a fresh install with all transitive dependencies, freezing
# the resulting packages and overwrriting `requirements.txt`
print_usage() {
  echo "Usage: $0 /path/to/requirements.txt [optional python version] [optional venv name]"
}

echo $1

if [ -n "$1" ] && [ -f "$1" ]; then
  requirements_path="$1"
  echo "Using requirements.txt-like file from $requirements_path"
else
  echo "Path to requirements.txt file was not provided or file does not exist"
  print_usage
  exit 1
fi

if [ -n "$2" ]; then
  python_version="$2"
else
  python_version='3.9.19'
fi
if [ -n "$3" ]; then
  venv_name="$3"
else
  venv_name=$(mktemp -d tmp-${python_version}-$RANDOM-XXXX)
fi

export PYTHON_VERSION="${python_version}"

pyenv virtualenv "${python_version}" "${venv_name}"

echo "Created temporary virtualenv '${venv_name}' (${python_version})."

echo "Activating environment '${venv_name}'"
. "${PYENV_ROOT}/versions/${venv_name}/bin/activate"

perl -p -i -e 'm/^## The following requirements were added by pip freeze:/ and exit' "$requirements_path"
# Wheel is used to install other packages from requirements.txt
# So we install is first, before everything else.
pip install wheel==0.41.1
pip install -r "$requirements_path"
pip freeze -r "$requirements_path" > requirements-new.txt
mv requirements-new.txt "$requirements_path"

echo "Destroying temporary virtualenv '${venv_name}'."
pyenv virtualenv-delete -f "${venv_name}"
# It seems to leave an empty directory behind, so we'll remove that too
rmdir "${venv_name}"

echo Requirements file "$requirements_path" updated.
