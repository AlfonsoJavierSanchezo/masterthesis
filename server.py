from flask import Flask, render_template,redirect,url_for,request
from flask_socketio import SocketIO
import json
import mysql.connector
from pandas import DataFrame,concat
from highcharts_core.chart import Chart
from highcharts_core.options.series.area import LineSeries
from datetime import datetime, timedelta
from tabulate import tabulate

farms = []
farmNames = []
now=""
#We are gonna need socketio to communicate 
app= Flask(__name__)
app.config['SECRET_KEY']= 'AEIOU'
socketio=SocketIO(app)
mywebname="http://localhost:5000/"

def generateChart(df, title):
    chart=Chart.from_pandas(df,
                  property_map = {
                      'x': 'date',
                      'y': 'Voltage',
                      #'name': ['Intensity','Voltage','PanelTemperature','Irradiance']
                      },
                  chart_kwargs={'container': 'target_div','variable_name': 'myChart'},
                  options_kwargs={'title': {'text': title},'x_axis': {'type': 'datetime','dateTimeLabelFormats': {'day': '%e %b %Y','second': '%e %b %Y %H:%M:%S'}}}
                  #,options_kwargs={'x_axis':{'type':'datetime','dateTimeLabelFormats':{'year':%Y}}}
                  )
    return chart 

@app.route("/")
def welcomePage():
    res=""
    if len(farmNames)==0:
        res="No data was loaded yet, please wait"
    else:
        for graphs in farmNames:
            res=res+"<a href="+mywebname+graphs+">"+graphs+"</a>"+"\n"
    return "<h1>Click on the solar farm whose data you want to see</h1>\n\n"+res+\
            "\n\n Or click <a href="+mywebname+"database>here</a> to search for historic data"

@app.route("/database", methods=["GET","POST"])
def plotFilteredData():
    if request.method=='POST':
        start_date = request.form.get('start-date')
        end_date = request.form.get('end-date')
        farm = request.form.get('options')
        month_range = request.form.get('date-range')
        #End and Start date can come as "None" if the "month_range" is some value. 
        #If the radiobutton is selected as none, month_range will contain an empty string.
        query=("SELECT * FROM solardata AS d "\
                "WHERE (d.FarmID = %s) "\
                "AND (d.date BETWEEN %s AND %s)")
        if start_date!=None and end_date!=None:
            start_date=datetime.strptime(start_date,'%Y-%m-%d')
            end_date=datetime.strptime(end_date,'%Y-%m-%d')
        elif month_range!="":
            end_date=datetime.today()
            if month_range=='last-month':
                start_date=end_date - datetime.timedelta(months=1)
            elif month_range=='last-2-months':
                start_date=end_date - datetime.timedelta(months=2)
        else:
            return render_template("db_connector.html",farms=farmNames, errormsg="Bad request, inconsistency in the dates")
        try:
            sql=mysql.connector.connect(user='server',password='serverpass',host='localhost', database='tiempo')
            cursor=sql.cursor()
            cursor.execute(query,(farm,start_date,end_date))
            column_names = cursor.description
            result=[{column_names[index][0]:column for index, column in enumerate(value)} for value in cursor.fetchall()]#Mention stackoverflow?
            df=DataFrame(result)
            my_chart=generateChart(df,'Generated chart')
            as_js_literal=my_chart.to_js_literal()
            return render_template("db_connector.html",farms=farmNames, graph=as_js_literal)
        except:
            return render_template("db_connector.html",farms=farmNames, errormsg="Could not connect to the database")
    elif request.method=='GET':
        return render_template("db_connector.html",farms=farmNames)

@app.route("/<path:text>")
def deliverGraphs(text):
    try:
        index=farmNames.index(text)
    except ValueError:
        return render_template('404.html')
    my_chart=generateChart(farms[index], text)
    as_js_literal=my_chart.to_js_literal()
    my_chart.to_js_literal("literal.js")
    return render_template("index.html",js_literal=as_js_literal)

@app.errorhandler(404)
def page_not_found():
    return render_template('404.html')

@socketio.on('NewSolarData')
def handle_message(data):
    print('Received mesage: '+str(data))
    #Data is a jsonString with all the info
    #Treat the data and add it to the list of data that highcharts will show
    formatted=json.loads(data)
    #To match format of: 2019-01-01T01:10:00
    try:
        formatted["date"]=datetime.strptime(formatted["date"],'%Y-%m-%dT%H:%M:%S')
        global now
        if now=="":
            now=formatted["date"].date()
        elif now!=formatted["date"].date():
            now = formatted["date"].date()
            i=0
            for df in farms:
                #If a day has passed, reset the dataframe, we'll only show the information of the actual day by default
                #Everything else will be managed via database
                farms[i]=df.iloc[0:0]
                i=i+1

    except ValueError:
        #The data must have a date value, skip if it there isn't or its format is incorrect
        return
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
