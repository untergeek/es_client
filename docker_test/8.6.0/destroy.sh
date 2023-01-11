#!/bin/bash

# Stop and remove the docker container
docker stop es_client_test8
docker rm es_client_test8

echo "Cleanup complete."

