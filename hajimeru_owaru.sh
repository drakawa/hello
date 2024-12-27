#!/bin/bash

rsync -avz assets/ uploaded_files/
rsync -avz assets hello uploaded_files /home/ryuta/ryuut/Documents/at25_bak

refact=/home/ryuta/refenv/bin/activate
# shellcheck source=/dev/null
source ${refact}
