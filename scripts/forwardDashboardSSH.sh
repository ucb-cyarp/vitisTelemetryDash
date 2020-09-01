#!/bin/bash

#Forward port to dashboard to local system.  The first parameter is the hostname of the server with the dashboard.
echo "ssh -N -L 8000:localhost:8000 $1"
ssh -N -L 8000:localhost:8000 $1