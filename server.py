from flask import Flask, render_template,redirect,url_for
from flask_socketio import SocketIO
import json
from pandas import DataFrame,concat
from highcharts_core.chart import Chart
from highcharts_core.options.series.area import LineSeries
from datetime import datetime
from tabulate import tabulate

farms = []
farmNames = []
#We are gonna need socketio to communicate 
app= Flask(__name__)
app.config['SECRET_KEY']= 'AEIOU'
socketio=SocketIO(app)
mywebname="http://localhost:5000/"
@app.route("/")
def welcomePage():
    res=""
    if len(farmNames)==0:
        res="No data was loaded yet, please wait"
    else:
        for graphs in farmNames:
            res=res+"<a href="+mywebname+graphs+">"+graphs+"</a>"+"\n"
    return "<h1>This is the welcome page</h1>\n\n"+res

@app.route("/<path:text>")
def deliverGraphs(text):
    try:
        index=farmNames.index(text)
    except ValueError:
        return render_template('404.html')
    my_series=LineSeries.from_pandas(farms[index],
                                     property_map = {
                                         'x': 'date',
                                         'y': 'Power',
                                         #'name': ['Intensity','Voltage','PanelTemperature','Irradiance']
                                         })
    my_chart=Chart.from_series(my_series)
    as_js_literal=my_chart.to_js_literal()
    return render_template("index.html",message=as_js_literal)

@app.errorhandler(404)
def page_not_found():
    return render_template('404.html')

@socketio.on('NewSolarData')
def handle_message(data):
    print('Received mesage: '+str(data))
    #Data is a list of jsonStrings with all the info
    print(data[0])
    #Treat the data and add it to the list of data that highcharts will show
    for i in data:
        formatted=json.loads(i)
        #Now let's see if the format of this json is correct or we have less data than we should
        schema=["date","Irradiance","PanelTemperature","Voltage","Intensity","Power","FarmID"]
        keys=list(formatted.keys())
        for elem in schema:
            if elem not in keys:
                formatted[elem]=None
        #To match format of: 2019-01-01T01:10:00
        try:
            formatted["date"]=datetime.strptime(formatted["date"],'%Y-%m-%dT%H:%M:%S')
        except ValueError:
            #The data needs to have a date value, skip if it there isn't
            continue
        try:
            index=farmNames.index(formatted["FarmID"])
            formatted.pop("FarmID")
            farms[index]=concat([farms[index],DataFrame(formatted,index=[0])],ignore_index=True)
            print(tabulate(farms[index],headers='keys',tablefmt='psql'))
        except ValueError:
            farmNames.append(formatted["FarmID"])
            formatted.pop("FarmID")
            newdf=DataFrame(formatted,index=[0])
            farms.append(newdf)
            print(tabulate(newdf,headers='keys',tablefmt='psql'))

if __name__ == '__main__':
    socketio.run(app)
