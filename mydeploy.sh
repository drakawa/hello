#!/bin/bash

CURRENT=$(cd "$(dirname "$0")" || return ;pwd)
cd uploaded_files/ || return
for f in *.mp4 ; do
    rm -f "${f}"
done

cd "$CURRENT" || return
pwd
echo "$CURRENT"
reflex deploy --project b88f7e50-9f73-4222-9e47-cb5f6a6f08ba
