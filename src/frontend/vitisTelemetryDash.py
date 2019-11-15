#!/usr/bin/python3
# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import argparse

external_stylesheets = ['vitisTelemetry.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

gauges = []
gaugeDivs = []
gaugeIDs = []
gaugeCallbackOutputs = []
gaugeContainer = None

radialStyle = False
if radialStyle:
    #Radial Style
    for i in range(0, 31):
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
    for i in range(0, 31):
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
            interval=2000, # in milliseconds
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
    new_ind = (current_ind+5)%101

    #Gauge Updates
    rtnList = []
    for i in range(0, len(gaugeCallbackOutputs)):
        rtnList.append((new_ind+i)%101)

    #History Updates
    #Using Example from https://dash.plot.ly/getting-started-part-2
    numPts = 10
    x = list(range(0, numPts))
    history_traces = []
    for i in range(0, len(gaugeCallbackOutputs)):
        initVal = (new_ind+i)%101
        y = []
        for j in range(0, numPts):
            y.append(x[j]+initVal)

        txt = 'Compute Partition ' + str(i)
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
                   'range':[x[0], x[numPts-1]]},
            yaxis={'title': 'CPU Utilization', 'range': [0, 100]},
            margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
            legend={'x': 0, 'y': 1},
            hovermode='closest',
            #transition = {'duration': 500}
        )
    }

    #Return everything
    return tuple(rtnList) + tuple([new_fig]) + tuple([str(new_ind)]) #Array in tuple required to prevent string or dict from being broken apart

if __name__ == '__main__':
    app.run_server(debug=True, host='172.16.248.148')