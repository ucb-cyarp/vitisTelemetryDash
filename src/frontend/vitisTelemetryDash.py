# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash.dependencies import Input, Output, State
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
gaugeIDs = []
gaugeCallbackOutputs = []

for i in range(0, 4):
    # daq.GraduatedBar(
    # color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
    # showCurrentValue=True,
    # min=0,
    # max=100,
    # step=10,
    # value=38)    

    idName = 'gauge-part-' + str(i)

    gauge = daq.Gauge(
        id = idName,
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

    gaugeIDs.append(idName)

    gaugeCallbackOutputs.append(Output(idName, 'value'))


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
    ]),

    #Hidden divs
    html.Div(style={'display': 'none'}, children = [
        dcc.Interval(
            id='interval-component',
            interval=1*1000, # in milliseconds
            n_intervals=0
        )
    ]),

    html.Div('0', style={'display': 'none'}, id='refresh-ind')

])

#Callbacks
#Update the elements
@app.callback(gaugeCallbackOutputs+[Output('refresh-ind', 'children')],
              [Input('interval-component', 'n_intervals')],
              [State('refresh-ind', 'children')])
def interval_update(intervals, refresh_ind):
    current_ind = int(refresh_ind)
    new_ind = (current_ind+5)%101

    rtnList = []
    for i in range(0, len(gaugeCallbackOutputs)):
        rtnList.append((new_ind+i)%101)

    return tuple(rtnList) + tuple([str(new_ind)])

if __name__ == '__main__':
    app.run_server(debug=True)