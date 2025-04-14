#!/bin/bash
SCRIPTPATH="$1"
echo "Running $SCRIPTPATH"

micromamba run -n base "$SCRIPTPATH" "${@:2}"