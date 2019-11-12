# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_daq as daq
import dash_html_components as html

external_stylesheets = ['vitisTelemetry.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

gauges = []
gaugeDivs = []

for i in range(0, 4):
    gauge = daq.Gauge(
    color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
    showCurrentValue=True,
    units="%",
    value=5,
    label='Compute Partition ' + str(i),
    max=100,
    min=0,
    size=175),
    gauges.append(gauge)

    gaugeDiv = html.Div(className = "guage-content", children = gauge)
    gaugeDivs.append(gaugeDiv)


app.layout = html.Div(children=[
    #Page Intro Container
    html.Div(className = 'container', children = [
        html.H1(children='Vitis Application Telemetry Dashboard'),
        html.P('''This dashboard presents telemetry data refreshed every 1 sec from a Vitis application.  
        Telemetry must be enabled and set to dump to files for this dashboard to function.''')]),

    #Gauges Container 
    html.Div(className = 'container', children = [
        html.H2(children = 'Partition Utilization of CPU Core:'),
        html.Div(className = 'gauge-container', id = 'gauges', children = gaugeDivs)]),

    # daq.Gauge(
    # color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
    # showCurrentValue=True,
    # units="%",
    # value=5,
    # label='Compute Partition 1',
    # max=100,
    # min=0,
    # size=175),

    # daq.GraduatedBar(
    # color={"gradient":True,"ranges":{"green":[0,60],"yellow":[60,80],"red":[80,100]}},
    # showCurrentValue=True,
    # min=0,
    # max=100,
    # step=10,
    # value=38)    

    html.Div( className = 'container footer', children = [
    html.P(children = ['Developed using ', html.A('Plotly Dash', href='https://plot.ly/dash')])
    ])
])

if __name__ == '__main__':
    app.run_server(debug=True)