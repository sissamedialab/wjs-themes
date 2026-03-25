#!/usr/bin/env bash

cd ../janeway-upstream/src
echo "Compile frontend"
python manage.py build_assets
while inotifywait -r -e modify ../../wjs-themes/wjs/themes/JCOM-theme/assets ../../wjs-themes/wjs/themes/wjs-bootstrap/assets; do
  python manage.py build_assets
done
