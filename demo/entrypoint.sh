#!/bin/sh -xe

yaml_requests --version
yaml_requests wait-until-api-ready.yml || true

export PASSWORD=$(cat ${PHOTO_OBJECTS_HOME:-$HOME/.photo_objects}/initial_admin_password || echo "")

# Check if initialization has been done
if [ -f /work/initialized ] && [ "$1" != "clean" ]; then
  echo "Demo content already initialized."
  exit 0
fi

# Run initialization and write file to indicate initialization has been done
if [ "$1" = "clean" ]; then
  yaml_requests cleanup-demo.yml
  rm -f /work/initialized
else
  yaml_requests initialize-demo.yml
  touch /work/initialized
fi
