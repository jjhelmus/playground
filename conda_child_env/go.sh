#!/bin/sh

echo "Cleaning up"
rm -rf ./parent
rm -rf ./child

echo "Creating parent"
conda create -y -p ./parent python=3.10 pip

echo "Creating child"
conda create -y -p ./child

echo "Preparing child"
conda run -p ./parent python -m venv --without-pip --system-site-packages ./child

for file in ./parent/conda-meta/*.json; do
    jq 'del(.files, .paths_data) | . + {"package_type":"virtual_system"}' "$file" > ./child/conda-meta/$(basename $file)
done
cp ./parent/conda-meta/history ./child/conda-meta/history
