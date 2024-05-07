#!/bin/bash

# Source the common.bash file from the same path as the script
source $(dirname "$0")/common.bash

# Stop and remove the docker container
echo "Stopping container ${NAME}..."
echo "$(docker stop ${NAME}) stopped."

echo "Removing container ${NAME}..."
echo "$(docker rm ${NAME}) deleted."

# Delete .env file and curl config file
echo "Deleting remaining files and directories"
rm -rf ${REPOLOCAL}
rm -f ${SCRIPTPATH}/${REPOJSON}
rm -f ${ENVCFG}
rm -f ${CURLCFG}
rm -f ${PROJECT_ROOT}/http_ca.crt

echo "Cleanup complete."
