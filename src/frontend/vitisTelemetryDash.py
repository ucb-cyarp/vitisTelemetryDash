#!/usr/bin/python3
# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import xmlrpc.client
import time

#Attempt to connect to RPC server
#Do not continue until connection is successful
rpcURL = 'http://localhost:8090/'

connected = False
proxy = None
while not connected:
    try:
        proxy = xmlrpc.client.ServerProxy(rpcURL)
        connected = True
    except xmlrpc.client.ProtocolError as error:
        time.sleep(1) #Retry in a second

external_stylesheets = ['vitisTelemetry.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

gauges = []
gaugeDivs = []
gaugeIDs = []
gaugeCallbackOutputs = []
gaugeContainer = None

#Get the design name
designName = proxy.getDesignName()

#Get the compute partitions
computePartitions = proxy.getPartitions()

radialStyle = False
if radialStyle:
    #Radial Style
    for i in computePartitions:
        idName = 'gauge-part-' + str(i)

        gauge = daq.Gauge(
            id = idName,
            #color = {"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
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

        gaugeContainer = html.Div(className = 'bar-collection-container', children = gaugeDivs)

else:
    #Bar Style
    for i in computePartitions:
        idName = 'gauge-part-' + str(i)

        gauge = daq.GraduatedBar(
            id = idName,
            # color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
            showCurrentValue=True,
            min=0,
            max=100,
            step=1,
            value=0)    

        gauges.append(gauge)

        gaugeDiv = html.Div(className = 'bar-container', children = [
            html.Div(className = "bar-label", children = 'Compute Partition ' + str(i) + ": "),
            html.Div(className = "bar-actual", children = gauge)
        ])
        gaugeDivs.append(gaugeDiv)

        gaugeIDs.append(idName)

        gaugeCallbackOutputs.append(Output(idName, 'value'))

        gaugeContainer = html.Div(className = 'gauge-container', children = gaugeDivs)

app.layout = html.Div(children=[
    #Page Intro Container
    html.Div(className = 'container', children = [
        html.H1(children=[ 'Vitis Application Telemetry Dashboard: ', html.Span(id = 'designName', children = designName) ]),
        html.P(['''This dashboard presents telemetry data refreshed every ''', html.Span(id = 'refresh-lbl', children = '1'), ''' sec from a Vitis application.  
        Telemetry must be enabled and set to dump to files for this dashboard to function.'''])
    ]),

    #Live Gauges Container 
    html.Div(className = 'container', children = [
        html.H2(children = 'Live Utilization:', id = 'live-util'),
        gaugeContainer
    ]),


    #History Util Plot Container
    html.Div(className = 'container', children = [
        html.H2(children = 'Historical Utilization:', id = 'hist-util'),
        html.Div(className = 'history-container', children = [
            dcc.Graph(
                id='hist-plot',
                # animate = True,
                config={
                    'showSendToCloud': False,
                }
            )
        ])
    ]),

    #History Throughput Plot Container
    html.Div(className = 'container', children = [
        html.H2(children = 'Historical Rate:', id = 'hist-throughput'),
        html.Div(className = 'history-container', children = [
            dcc.Graph(
                id='hist-rate-plot',
                # animate = True,
                config={
                    'showSendToCloud': False,
                }
            )
        ])
    ]),

    html.Div( className = 'container', children = [
        html.H3(children = 'Controls:'),
        html.Div( className  = 'control-container', children = [
            html.Div( className  = 'control-content', children = [
                html.Button('Stop', id='startstop-btn')
            ]),
            html.Div( className  = 'control-content', children = [
                daq.NumericInput(
                    id='refresh-period-input',
                    max=100,
                    value=1,
                    min=1,
                    label='Refresh Period (s)',
                    labelPosition='bottom'
                )  
            ]),
            html.Div( className  = 'control-content', children = [
                daq.NumericInput(
                    id='hist-input',
                    max=10000,
                    value=120,
                    min=1,
                    label='History (s)',
                    labelPosition='bottom'
                )  
            ])
        ])
    ]),

    html.Div( className = 'container footer', children = [
        html.P(children = ['Developed using ', html.A('Plotly Dash', href='https://plot.ly/dash')])
    ]),

    #Hidden divs
    html.Div(style={'display': 'none'}, children = [
        dcc.Interval(
            id='interval-component',
            interval=1000, # in milliseconds
            n_intervals=0
        )
    ]),

    html.Div('0', style={'display': 'none'}, id='refresh-ind'),
    html.Div('False', style={'display': 'none'}, id='enabled'), #Set default to false.  When refesh occurs, the button callback is called automaticall and will enable

])

#Callbacks
#Start/Stop Button
@app.callback([Output('interval-component', 'disabled'), Output('startstop-btn', 'children'), Output('enabled', 'children')],
              [Input('startstop-btn', 'n_clicks')],
              [State('enabled', 'children')])
def start_stop_update(n_clicks, enabled):
    currentlyEnabled = (enabled == 'True')
    currentlyEnabled = not currentlyEnabled
    btn_lbl = ''
    new_val = ''
    if currentlyEnabled:
        btn_lbl = 'Stop'
        new_val = 'True'
    else:
        btn_lbl = 'Start'
        new_val = 'False'
    return (not currentlyEnabled, btn_lbl, new_val)

#Update rate
@app.callback([Output('interval-component', 'interval'), Output('refresh-lbl', 'children')],
              [Input('refresh-period-input', 'value')],
              [])
def interval_update(interval_str):
    interval = int(interval_str)
    return (interval*1000, str(interval))

#Update the elements
@app.callback(gaugeCallbackOutputs+[Output('hist-plot', 'figure'), Output('hist-rate-plot', 'figure'), Output('refresh-ind', 'children')],
              [Input('interval-component', 'n_intervals')],
              [State('refresh-ind', 'children'), State('hist-input', 'value')])
def data_update(intervals, refresh_ind, hist_window_str):
    current_ind = int(refresh_ind)
    hist_window = int(hist_window_str)

    proxy_ind = proxy.getItter()

    if proxy_ind == current_ind:
        #The is no new data from the backend, do not update
        raise PreventUpdate

    new_ind = proxy_ind

    #Gauge Updates
    gaugeCurrentVals = proxy.getComputeTimePercent(new_ind)
    # print('GuageCurrentVals:' + str(gaugeCurrentVals))

    #History Updates
    #Using Example from https://dash.plot.ly/getting-started-part-2
    timeRangeSec = hist_window

    rate_history_traces = []
    compute_percent_history_traces = []
    first = True
    minX = 0
    maxX = 0
    for i in range(0, len(computePartitions)):
        hist = proxy.getHistory(i, new_ind, timeRangeSec)
        x = hist['time']
        y_percent = hist['percent']
        y_rate = hist['rate']

        if first:
            minX = x[0]
            maxX = x[len(x)-1]
            first = False
        else:
            if x[0] < minX:
                minX = x[0]
            if x[len(x)-1] > maxX:
                maxX = x[len(x)-1]

        txt = 'Compute Partition ' + str(computePartitions[i])
        compute_percent_history_traces.append(go.Scatter(
                x=x,
                y=y_percent,
                #text=[], #This is the label for each point
                mode='lines+markers',
                opacity=0.7,
                marker={
                    'size': 15,
                    'line': {'width': 0.5, 'color': 'white'}
                },
                name=txt
            ))

        rate_history_traces.append(go.Scatter(
                x=x,
                y=y_rate,
                #text=[], #This is the label for each point
                mode='lines+markers',
                opacity=0.7,
                marker={
                    'size': 15,
                    'line': {'width': 0.5, 'color': 'white'}
                },
                name=txt
            ))
    
    new_compute_percent_fig = {
        'data': compute_percent_history_traces,
        'layout': dict(
            xaxis={'type': 'linear', 'title': 'Time',
                   'range':[minX, maxX]},
            yaxis={'title': 'CPU Utilization'},
            # yaxis={'title': 'CPU Utilization', 'range': [0, 100]},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest',
            #transition = {'duration': 500}
        )
    }

    new_rate_fig = {
        'data': rate_history_traces,
        'layout': dict(
            xaxis={'type': 'linear', 'title': 'Time',
                   'range':[minX, maxX]},
            yaxis={'title': 'Rate (MSPS)'},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest',
            #transition = {'duration': 500}
        )
    }

    #Return everything
    return tuple(gaugeCurrentVals) + tuple([new_compute_percent_fig]) + tuple([new_rate_fig]) + tuple([str(new_ind)]) #Array in tuple required to prevent string or dict from being broken apart

if __name__ == '__main__':
    app.run_server(debug=True, host='128.32.62.244')
