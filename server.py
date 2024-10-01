from flask import Flask, render_template,make_response,url_for,request
import socketio
import json
import mysql.connector
from pandas import DataFrame,concat
from highcharts_core.chart import Chart
from highcharts_core.options.series.area import LineSeries
from datetime import datetime, timedelta
from tabulate import tabulate
clients = []
farms = []
farmNames = []
now=""#"Today's" date, according to the data
#app= Flask(__name__)
#app.config['SECRET_KEY']= 'AEIOU'
#We are gonna need socketio to communicate 
sio = socketio.Server()
app = Flask(__name__)
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)
app.config['SECRET_KEY'] = 'secret!'
mywebname="http://localhost:5000/"
generalRoom="room"
roomPerUser={}
activeAlerts=[]

@app.route("/", methods=["GET","POST"])
def welcomePage():
    if request.method=='POST':
        monthOrLive=request.form.get('data-type')
        selectedFarm=request.form.get('selected-option')
        index=farmNames.index(selectedFarm)
        df=farms[index]
        if monthOrLive=="live":
            values=df[['date', 'Power']].values.tolist()
            predvalues=df[['date', 'predict_power']].values.tolist()
            series=[{'name':selectedFarm, 'data':values},{'name':"Pred-"+selectedFarm, 'data':predvalues}]
            response=make_response(render_template("day-view.html",farms=farmNames, DayData=series,title=selectedFarm,nAlerts=len(activeAlerts)))
            response.set_cookie('farm',selectedFarm)
            return response
        else:
            #We should take all the info from the database. Take this month from the first until what would be yesterday and plot everything, as well as the stats, calculated here below
            #They are calculated here as the month is not yet finished. Would be nice to switch months with a click on previous and next...But let's give that job to the database view
            #Would be nice to send the info to the spark script so not everything is calculated in the server
            query="SELECT * FROM aggregated_day AS agg\
                    WHERE MONTH(agg.date) = %s\
                    AND agg.FarmID = %s"
            try:
                sql=mysql.connector.connect(user='server',password='serverpass',host='localhost', database='tiempo')
                cursor=sql.cursor()
                print(now.month)
                cursor.execute(query,[now.month,selectedFarm])
                #Now, depending on the day of the data, complete the array that will be finally delivered
                realseries=[]#List of pairs [Date,Powersum]
                rawlist=cursor.fetchall()
                wholeset=[]
                for elem in rawlist:
                    #Transform all the decimal into floats and the datetime into a string
                    newelem=[]
                    i=1#Skip the index column
                    for field in elem:
                        if i==1:
                            newelem.append(str(elem[i]))
                        elif i==len(elem)-1:
                            continue
                        else:
                            newelem.append(float(elem[i]))
                        i=i+1
                    wholeset.append(newelem)
                                     #Datestr   Powersum       predictedSum
                    realseries.append([elem[1],float(elem[2]),float(elem[3])])
                result=[{'name': selectedFarm, 'data':[]},{'name': 'Pred-'+selectedFarm,'data':[]}]
                sum=[]
                sumPred=[]
                for i in range(1,32):
                    value=0
                    valuePred=0
                    for elem in realseries:
                        if elem[0].day==i:
                            value=elem[1]
                            valuePred=elem[2]
                            break
                    sum.append(value)
                    sumPred.append(valuePred)
                result[0]['data']=sum
                result[1]['data']=sumPred
            except Exception as e:
                print(f"ErrorF: "+repr(e))
                return render_template("month-view.html",farms=farmNames, errormsg="Could not connect to the database",nAlerts=len(activeAlerts))
            return render_template("month-view.html",farms=farmNames,title=selectedFarm,wholedata=wholeset ,MonthData=result,nAlerts=len(activeAlerts))
    if request.method=='GET':
        return render_template("day-view.html",farms=farmNames,nAlerts=len(activeAlerts))

@app.route("/database", methods=["GET","POST"])#It doesn't need post but I should remove the form in "templates/db_connector.html"
def plotFilteredData():
    return render_template("db_connector.html",farms=farmNames,nAlerts=len(activeAlerts))

@app.route("/alerts")
def showAlerts():
    query="select * from activeAlerts inner join alertTypes on activeAlerts.alertType=alertTypes.ID"
    query2="select * from lastSolvedAlerts inner join alertTypes on lastSolvedAlerts.alertType=alertTypes.ID"
    #No try/except for this to trigger err 500 if fails
    sql=mysql.connector.connect(user='server',password='serverpass',host='localhost', database='tiempo')
    cursor=sql.cursor()
    cursor.execute(query)
    result1 = [dict((cursor.description[i][0], value)for i, value in enumerate(row)) for row in cursor.fetchall()]
    cursor.execute(query2)
    result2 = [dict((cursor.description[i][0], value)for i, value in enumerate(row)) for row in cursor.fetchall()]
    #https://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
    #Transform sql response into array of json objects
    
    i=0
    for data in result1:
        result1[i]['Date']=str(result1[i]['Date'])
        i=i+1
    i=0
    for data in result2:
        result2[i]['Date']=str(result2[i]['Date'])
        i=i+1
    return render_template("alerts.html",activeAlerts=result1, solvedAlerts=result2)
    
    
    
@app.route("/solardata_day", methods=['POST'])
def getDayData():
    query=("SELECT Power,predict_power,FarmID,date FROM solardata AS d \
            WHERE (d.FarmID = %s) \
            AND (DATE(d.date) = STR_TO_DATE(%s,'%Y-%m-%d'))")
    obj = request.json
    try:
        sql=mysql.connector.connect(user='server',password='serverpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        cursor.execute(query,[obj['Farm'],obj['Day']])
        #https://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
        #Transform sql response into array of json objects
        result = [dict((cursor.description[i][0], value)for i, value in enumerate(row)) for row in cursor.fetchall()]
        return result
    except:
        return "Error on the query or the db is down"

@app.route("/aggregated_day/single", methods=['POST'])
def getAggDay():
    query=("SELECT * FROM aggregated_day AS d \
                WHERE (d.FarmID = %s)\
                AND (d.Date = STR_TO_DATE(%s,'%Y-%m-%d'))")
    obj = request.json
    try:
        sql=mysql.connector.connect(user='server',password='serverpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        cursor.execute(query,[obj['Farm'],obj['Day']])
        #https://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
        #Transform sql response into array of json objects
        result = [dict((cursor.description[i][0], value)for i, value in enumerate(row)) for row in cursor.fetchall()]
        result =list(result[0].values())
        return result
    except:
        return "Error on the query or the db is down"
    
@app.route("/aggregated_day/month", methods=['POST'])
def getAggDaysMonth():
    query="SELECT PowerSum,predPowerSum,FarmID,date FROM aggregated_day AS d \
                WHERE (d.FarmID = %s) \
                AND (MONTH(d.date) = %s)\
                AND (YEAR(d.date)=%s)"
    obj = request.json
    print(obj)
    try:
        sql=mysql.connector.connect(user='server',password='serverpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        d = datetime.strptime(obj['Month'],'%Y-%m')
        cursor.execute(query,[obj['Farm'],d.month,d.year])
        #https://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
        #Transform sql response into array of json objects
        result = [dict((cursor.description[i][0], value)for i, value in enumerate(row)) for row in cursor.fetchall()]
        return result
    except:
        return "Error on the query or the db is down"

@app.route("/aggregated_month", methods=['POST'])
def getMonth():
    query="SELECT * FROM aggregated_month AS d WHERE (d.FarmID = %s) AND (MONTH(d.Date)=%s) AND (YEAR(d.date)=%s)"
    obj = request.json
    try:
        sql=mysql.connector.connect(user='server',password='serverpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        print("Execute")
        d = datetime.strptime(obj['Month'],'%Y-%m')
        print(d.month,d.year)
        cursor.execute(query,[obj['Farm'],d.month,d.year])
        print("Executed")
        #https://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
        #Transform sql response into array of json objects
        print(cursor._executed)
        result = [dict((cursor.description[i][0], value)for i, value in enumerate(row)) for row in cursor.fetchall()]
        result =list(result[0].values())
        return result
    except Exception as e:
        print(f"ErrorF: "+repr(e))
        return "Error on the query or the db is down"

@app.errorhandler(404)
def page_not_found(a):
    return render_template('404.html')

@sio.on('NewSolarData')
def handle_message(id,data):
    print('Received mesage: ')
    #print(str(data))
    #Data is a jsonString with all the info
    #Treat the data and add it to the list of data that highcharts will show
    formatted=json.loads(data)
    #To match format of: 2019-01-01T01:10:00
    try:
        formatted["date"]=datetime.strptime(formatted["date"],'%Y-%m-%dT%H:%M:%S')
        global now
        if now=="":
            now=formatted["date"].date()#Type date, day-month-year
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
    formatted["date"]=formatted["date"].timestamp()*1000+7200000
    sio.emit("liveData",json.dumps(formatted),to=formatted["FarmID"])
    try:
        index=farmNames.index(formatted["FarmID"])
        formatted.pop("FarmID")
        farms[index]=concat([farms[index],DataFrame(formatted,index=[0])],ignore_index=True)
    except ValueError:
        farmNames.append(formatted["FarmID"])
        formatted.pop("FarmID")
        newdf=DataFrame(formatted,index=[0])
        newdf["date"].astype('int64')
        farms.append(newdf)
        #print(tabulate(newdf,headers='keys',tablefmt='sql'))
    
@sio.on("activateAlert")
def activateAlert(id,newAlert):
    print("***Alert:"+str(newAlert))
    i=0
    for alert in activeAlerts:
        if(alert["alertType"]==newAlert["alertType"] and alert["FarmID"]==newAlert["FarmID"]):
            activeAlerts[i]["date"]=newAlert["date"]
            return
        i=i+1
    activeAlerts.append(newAlert)

@sio.on("deactivateAlert")
def deactivateAlert(id, toDeactivate):
    i=0
    for alert in activeAlerts:
        if(alert["alertType"]==toDeactivate["alertType"] and alert["FarmID"]==toDeactivate["FarmID"]):
            activeAlerts.pop(i)
        i=i+1


@sio.event
def disconnect(sid):
    try:
    #If the user was never connected to a room, this function would raise a valueError because a join would have never been performed
        sio.leave_room(sid, roomPerUser[sid])
        roomPerUser.pop(sid)
    except:
        return

@sio.on('join')
def prueba(sid,data):
    roomPerUser[sid]=data
    sio.enter_room(sid, data)

if __name__ == '__main__':
    #Would be nice to initialize farms to the strings of a table in the db to have them from the beginning
    app.run(host="0.0.0.0")
