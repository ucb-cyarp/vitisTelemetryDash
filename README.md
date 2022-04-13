# Laminar Telemetry Dashboard
A Web Based Telemetry Dashboard for Laminar (previously Vitis) Apps

## A Note on the Repository Name:
The initial name of the Laminar compiler was *vitis*, referencing the genus of grape vines.  After the announcement of the Xilinx Vitis suite of tools, it was decided to rename the compiler to Laminar in order to avoid confusion.  This repository has retained the name *vitisTelemetryDash* to preserve versioning in repositories such as [ucb-cyarp/cyclopsDemo](https://github.com/ucb-cyarp/cyclopsDemo) which rely on it as a submodule.

To clarify, there is *no relationship* between this tool and the Xilinx Vitis suite of tools.

## Installation
This application uses [Ploty Dash](https://plot.ly/dash), a python based dashboard framework.  While Dash can be run under python 2 or 3, python 3 is required for this application.

1. Install python3 and pip3:

    On ubuntu, this can be accomplished with:
    ```bash
    sudo apt install python3 python3-pip
    ```
2. Install the prerequisites using pip3:
    ```bash
    pip3 install -r requirements.txt
    ```

## Vitis Prerequisites
Before the dashboard can monitor a vitis application, that application must be configured to dump telemetry data to files.
To do this, add the following CLI option to vitis
```bash
./multiThreadedGenerator ... --telemDumpPrefix telemDump_
```

The generated files should contain a telemetry configuration file of the form `designName_telemDump_telemConfig.json`.

## Dashboard Prerequisites
Modify the IP address in `src/frontend/vitisTelemetryDash.py` to be either 127.0.0.1 or the IP address of one of your NICs.

## Running the dashboard
The dashboard is separated into 2 components: the backend (which monitors the telemetry log files) and the frontend (which displays the parsed telemetry).  Because of the dependences between the different components of the dashboard, there is an order in which they should be started:

1. Compile and start the vitis application.  Make note of the directory in which the application was started.
2. Start the backend by executing the following command:
    ```bash
    python3 ./src/backend/vitisTelemetryWatcher.py --config ${CONFIG_FILE} --telem-path ${TELEM_DIR}
    ```
    `${CONFIG_FILE}` should be replaced with a path to the `designName_telemDump_telemConfig.json` file that was generated in the [Vitis Prerequisites](#vitis-prerequisites) stage.

    `${TELEM_DIR}` should be the working directory in which the vitis application was started
3. Start the frontend by executing the following command:
    ```bash
    python3 ./src/frontend/vitisTelemetryDash.py
    ```
4. Connect to the dashboard using a web browser to the IP address printed to the console
