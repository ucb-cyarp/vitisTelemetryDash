#!/bin/bash
#BASE_DIR=~/git/vitis/build-demo-stdatomic
#BASE_DIR=~/git/vitis/build-demo
BASE_DIR=~/multirate-demo-work/vitis/build-multirate-demo
#CONFIG_FILE=${BASE_DIR}/cOut_rx_combined_man_partition_fewerLuts_demo_raisedcos1_fastslim2_fast3_slow3/rx_demo_telemDump_telemConfig.json
CONFIG_FILE=${BASE_DIR}/cOut_rx_rate_transition_1_2_2_pipeline384/rx_demo_telemDump_telemConfig.json
TELEM_DIR=${BASE_DIR}/demoRun/rx
echo "python3 vitisTelemetryWatcher.py --config ${CONFIG_FILE} --telem-path ${TELEM_DIR}"
python3 vitisTelemetryWatcher.py --config ${CONFIG_FILE} --telem-path ${TELEM_DIR}
