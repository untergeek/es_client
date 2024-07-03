#!/bin/bash

# Source the common.bash file from the same path as the script
source $(dirname "$0")/common.bash

# Test to see if we were passed a VERSION
if [ "x${1}" == "x" ]; then
  echo "Error! No Elasticsearch version provided."
  echo "VERSION must be in Semver format, e.g. X.Y.Z, 8.6.0"
  echo "USAGE: ${0} VERSION"
  exit 1
fi

# Set the version
VERSION=${1}

######################################
### Setup snapshot repository path ###
######################################

# Nuke it from orbit, just to be sure
rm -rf ${REPOLOCAL}
mkdir -p ${REPOLOCAL}

#####################
### Run Container ###
#####################

# Start the container
echo -en "\rStarting ${NAME} container... "
docker run -d -it --name ${NAME} -m ${HEAP} \
  -p ${LOCAL_PORT}:${DOCKER_PORT} \
  -v ${REPOLOCAL}:${REPODOCKER} \
  -e "discovery.type=single-node" \
  -e "cluster.name=local-cluster" \
  -e "node.name=local-node" \
  -e "xpack.monitoring.templates.enabled=false" \
  -e "path.repo=${REPODOCKER}" \
${IMAGE}:${VERSION}


# Set up the curl config file, first line creates a new file, all others append
echo "-o /dev/null" > ${CURLCFG}
echo "-s" >> ${CURLCFG}
echo '-w "%{http_code}\n"' >> ${CURLCFG}

# Do the xpack_fork function, passing the container name and the .env file path
xpack_fork "${NAME}" "${ENVCFG}"

# Did we get a bad return code?
if [ $? -eq 1 ]; then

  # That's an error, and we need to exit
  echo "ERROR! Unable to get/reset elastic user password. Unable to continue. Exiting..."
  exit 1
fi

# Set the URL
URL=https://${URL_HOST}:${LOCAL_PORT}

# Write the TEST_ES_SERVER environment variable to the .env file
echo "export TEST_ES_SERVER=${URL}" >> ${ENVCFG}

# We expect a 200 HTTP rsponse
EXPECTED=200

# Set the NODE var
NODE="${NAME} instance"

# Start with an empty value
ACTUAL=0

# Initialize loop counter
COUNTER=0

# Loop until we get our 200 code
while [ "${ACTUAL}" != "${EXPECTED}" ] && [ ${COUNTER} -lt ${LIMIT} ]; do

  # Get our actual response
  ACTUAL=$(curl -K ${CURLCFG} ${URL})

  # Report what we received
  echo -en "\rHTTP status code for ${NODE} is: ${ACTUAL}"

  # If we got what we expected, we're great!
  if [ "${ACTUAL}" == "${EXPECTED}" ]; then
    echo " --- ${NODE} is ready!"

  else
    # Otherwise sleep and try again 
    sleep 1
    ((++COUNTER))
  fi

done
# End while loop

# If we still don't have what we expected, we hit the LIMIT
if [ "${ACTUAL}" != "${EXPECTED}" ]; then
  
  echo "Unable to connect to ${URL} in ${LIMIT} seconds. Unable to continue. Exiting..." 
  exit 1

fi

##################
### Wrap it up ###
##################

echo
echo "${NAME} container is up using image elasticsearch:${VERSION}"

echo
echo "Environment variables are in \$PROJECT_ROOT/.env"

echo
echo "Ready to test!"
