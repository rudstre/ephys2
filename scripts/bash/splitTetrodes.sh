#!/bin/bash
for tetrode in {0..14}; do
   echo "tetrode $tetrode:"
   python -m ephys2.copy_channel_groups \
    -i "/n/holylabs/LABS/olveczky_lab/Users/rudygb/eth1_new/eth1_final_40uv.h5" \
    -o "/n/holylabs/LABS/olveczky_lab/Users/rudygb/eth2_new/eth1_tet${tetrode}.h5" \
    -g "${tetrode}"
done
