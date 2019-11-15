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

#Get the compute partitions
computePartitions = proxy.getPartitions()

radialStyle = False
if radialStyle:
    #Radial Style
    for i in computePartitions:
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

        gaugeContainer = html.Div(className = 'bar-collection-container', children = gaugeDivs)

else:
    #Bar Style
    for i in computePartitions:
        idName = 'gauge-part-' + str(i)

        gauge = daq.GraduatedBar(
            id = idName,
            color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
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
        html.H1(children='Vitis Application Telemetry Dashboard'),
        html.P('''This dashboard presents telemetry data refreshed every 1 sec from a Vitis application.  
        Telemetry must be enabled and set to dump to files for this dashboard to function.''')
    ]),

    #Live Gauges Container 
    html.Div(className = 'container', children = [
        html.H2(children = 'Live Utilization:', id = 'live-util'),
        gaugeContainer
    ]),


    #History Plot Container
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

    html.Div( className = 'container footer', children = [
        html.P(children = ['Developed using ', html.A('Plotly Dash', href='https://plot.ly/dash')])
    ]),

    #Hidden divs
    html.Div(style={'display': 'none'}, children = [
        dcc.Interval(
            id='interval-component',
            interval=10000, # in milliseconds
            n_intervals=0
        )
    ]),

    html.Div('0', style={'display': 'none'}, id='refresh-ind')

])

#Callbacks
#Update the elements
@app.callback(gaugeCallbackOutputs+[Output('hist-plot', 'figure'), Output('refresh-ind', 'children')],
              [Input('interval-component', 'n_intervals')],
              [State('refresh-ind', 'children')])
def interval_update(intervals, refresh_ind):
    current_ind = int(refresh_ind)

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
    timeRangeSec = 10

    history_traces = []
    first = True
    minX = 0
    maxX = 0
    for i in range(0, len(computePartitions)):
        hist = proxy.getComputeTimePercentHistory(i, new_ind, timeRangeSec)
        x = hist['time']
        y = hist['percent']

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
        history_traces.append(go.Scatter(
                x=x,
                y=y,
                #text=[], #This is the label for each point
                mode='lines+markers',
                opacity=0.7,
                marker={
                    'size': 15,
                    'line': {'width': 0.5, 'color': 'white'}
                },
                name=txt
            ))
    
    new_fig = {
        'data': history_traces,
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

    #Return everything
    return tuple(gaugeCurrentVals) + tuple([new_fig]) + tuple([str(new_ind)]) #Array in tuple required to prevent string or dict from being broken apart

if __name__ == '__main__':
    app.run_server(debug=True, host='172.16.248.148')