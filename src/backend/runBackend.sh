#!/bin/bash
BASE_DIR=../../../../build
# --- Rx ---
CONFIG_FILE=${BASE_DIR}/cOut_rev1BB_receiver/rx_demo_telemDump_telemConfig.json
TELEM_DIR=${BASE_DIR}/demoRun/rx
# --- Tx ---
# CONFIG_FILE=${BASE_DIR}/cOut_rev1BB_transmitter/tx_demo_telemDump_telemConfig.json
# TELEM_DIR=${BASE_DIR}/demoRun/tx
echo "python3 vitisTelemetryWatcher.py --config ${CONFIG_FILE} --telem-path ${TELEM_DIR}"
python3 vitisTelemetryWatcher.py --config ${CONFIG_FILE} --telem-path ${TELEM_DIR}
