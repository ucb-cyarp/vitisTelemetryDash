# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
import argparse
import json

#Parse CLI Arguments for Config File Location
# parser = argparse.ArgumentParser(description='Start vitis telemetry dashboard')
# parser.add_argument('config', type=str, required=True, help='Path to the telemetry configuration json file')
# parser.parse_args()

#Load the Config Json file.
#This file contains information about the application incuding
#   * Name
#   * IO Thread Telemetry File Location (if applicable)
#   * Compute Thread Telemetry File Locations
#   * Column Label of Compute Time Metric
#   * Column Lable of Total Time Metric
#   * Partition To CPU Number Mapping
#   * Generation Report Files (if applicable)
#        - Schedule GraphML file (if applicable)
#        - Communication Report
#        - Computation Report
#   

#For the telemetry files, we read them line by line

external_stylesheets = ['vitisTelemetry.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

gauges = []
gaugeDivs = []

for i in range(0, 4):
    # daq.GraduatedBar(
    # color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
    # showCurrentValue=True,
    # min=0,
    # max=100,
    # step=10,
    # value=38)    

    gauge = daq.Gauge(
        id = 'gauge-part-' + str(i),
        color = {"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
        showCurrentValue = True,
        units = "%",
        value = 0,
        label = 'Compute Partition ' + str(i),
        max=100,
        min=0,
        size=175
    ),
    gauges.append(gauge)

    gaugeDiv = html.Div(className = "guage-content", children = gauge)
    gaugeDivs.append(gaugeDiv)


app.layout = html.Div(children=[
    #Page Intro Container
    html.Div(className = 'container', children = [
        html.H1(children='Vitis Application Telemetry Dashboard'),
        html.P('''This dashboard presents telemetry data refreshed every 1 sec from a Vitis application.  
        Telemetry must be enabled and set to dump to files for this dashboard to function.''')
    ]),

    #Live Gauges Container 
    html.Div(className = 'container', children = [
        html.H2(children = 'Live Utilization:', id = 'live-util'),
        html.Div(className = 'gauge-container', children = gaugeDivs)
    ]),


    #History Plot Container
    html.Div(className = 'container', children = [
        html.H2(children = 'Historical Utilization:', id = 'hist-util'),
        html.Div(className = 'history-container', children = [
            dcc.Graph(
                id='hist',
                animate = True,
                config={
                    'showSendToCloud': False,
                }
            )
        ])
    ]),

    html.Div( className = 'container footer', children = [
        html.P(children = ['Developed using ', html.A('Plotly Dash', href='https://plot.ly/dash')])
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)