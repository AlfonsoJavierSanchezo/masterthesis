import sys
import time
import socketio
import json
import mysql.connector
from datetime import datetime
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from threading import Timer
import subprocess
from enum import Enum
import os
#Contains arrays, containing the name for the farm and the timer for the idle alarm
farmNames=[]
#Aggregated data will be stored as a list of dicts with numbers
#Keys:'PowerSum' 'IrradianceMean' 'IrradianceMax' 'IrradianceMin' 'PanelTemperatureMean' 'PanelTemperatureMax' 'PanelTemperatureMin' 
#'IntensityMean' 'IntensityMax' 'IntensityMin' 'VoltageMean' 'VoltageMax' 'VoltageMin'
aggrDay=[]
aggrMonth=[]
today=""
thisMonth=""

#To edit this please check database table named alertTypes
class alertType(Enum):
    BadFormat=1
    FarmIdle=2
    LowPower=3

sio=socketio.Client()
    
def calculatePrediction(irradiance, cellTemp, farm):
    if farm=='etsist1':
        return (5.5*irradiance*(1-0.0035*(cellTemp-25)))/1000
    elif farm =='etsist2':
        return (4.8*irradiance*(1-0.0035*(cellTemp-25)))/1000
    else: 
        return (5.1*irradiance*(1-0.0035*(cellTemp-25)))/1000

def getPowerRelation(real, prediction):
    if prediction==0:
        return 1
    percentage=(prediction-real)/prediction
    if percentage<0:
        percentage=-percentage
    return percentage

def maxf(n1,n2):
    if n1>n2:
        return n1
    else:
        return n2

def minf(n1,n2):
    if n1<n2:
        return n1
    else:
        return n2

def aggregateValues(data,dayormonth):
    #Data only contains an entry about a solar farm
    i=0
    global aggrDay
    global aggrMonth
    if dayormonth=="day":
        farms=aggrDay
    else:
        farms=aggrMonth
    for farm in farms:
        if farm[0]==data["FarmID"]:
            try:
                farms[i][1]['PowerSum']=farm[1]['PowerSum']+data['Power']
                farms[i][1]['PredictPowerSum']=farm[1]['PredictPowerSum']+data['predict_power']
                if data['Irradiance']!=0:
                    farms[i][1]['IrradianceMean']=farm[1]['IrradianceMean']+data['Irradiance']
                    farms[i][1]['IrradianceMax']=maxf(farm[1]['IrradianceMax'],data['Irradiance'])
                    farms[i][1]['IrradianceMin']=minf(farm[1]['IrradianceMin'],data['Irradiance'])
                    farms[i][1]['NumIrr']=farm[1]['NumIrr']+1
                if data['PanelTemperature']!=0:
                    farms[i][1]['PanelTemperatureMean']=farm[1]['PanelTemperatureMean']+data['PanelTemperature']
                    farms[i][1]['PanelTemperatureMax']=maxf(farm[1]['PanelTemperatureMax'],data['PanelTemperature'])
                    farms[i][1]['PanelTemperatureMin']=minf(farm[1]['PanelTemperatureMin'],data['PanelTemperature'])
                    farms[i][1]['NumTemp']=farm[1]['NumTemp']+1
                if data['Intensity']!=0:
                    farms[i][1]['IntensityMean']=farm[1]['IntensityMean']+data['Intensity']
                    farms[i][1]['IntensityMax']=maxf(farm[1]['IntensityMax'],data['Intensity'])
                    farms[i][1]['IntensityMin']=minf(farm[1]['IntensityMin'],data['Intensity'])
                    farms[i][1]['NumInt']=farm[1]['NumInt']+1
                if data['Voltage']!=0:
                    farms[i][1]['VoltageMean']=farm[1]['VoltageMean']+data['Voltage']
                    farms[i][1]['VoltageMax']=maxf(farm[1]['VoltageMax'],data['Voltage'])
                    farms[i][1]['VoltageMin']=minf(farm[1]['VoltageMin'],data['Voltage'])
                    farms[i][1]['NumVol']=farm[1]['NumVol']+1
                
            except Exception as e:
                print(f"ErrorF: "+repr(e))
                farms[i][1]['PowerSum']=data['Power']
                farms[i][1]['PredictPowerSum']=data['predict_power']
                farms[i][1]['IrradianceMean']=data['Irradiance']
                farms[i][1]['IrradianceMax']=data['Irradiance']
                farms[i][1]['IrradianceMin']=data['Irradiance']
                farms[i][1]['PanelTemperatureMean']=data['PanelTemperature']
                farms[i][1]['PanelTemperatureMax']=data['PanelTemperature']
                farms[i][1]['PanelTemperatureMin']=data['PanelTemperature']
                farms[i][1]['IntensityMean']=data['Intensity']
                farms[i][1]['IntensityMax']=data['Intensity']
                farms[i][1]['IntensityMin']=data['Intensity']
                farms[i][1]['VoltageMean']=data['Voltage']
                farms[i][1]['VoltageMax']=data['Voltage']
                farms[i][1]['VoltageMin']=data['Voltage']
                farms[i][1]['NumIrr']=1
                farms[i][1]['NumTemp']=1
                farms[i][1]['NumInt']=1
                farms[i][1]['NumVol']=1
            break
        i=i+1
        
def writeAggrDatabase(db_name):
    query="INSERT INTO "+db_name+" (date,PowerSum,PredPowerSum,IrradianceMean,IrradianceMax,IrradianceMin,\
        PanelTemperatureMean,PanelTemperatureMax,PanelTemperatureMin\
        ,IntensityMean,IntensityMax,IntensityMin,\
        VoltageMean,VoltageMax,VoltageMin,FarmID)\
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    global aggrMonth
    global aggrDay
    if db_name=="aggregated_month":
        farms=aggrMonth
        date=thisMonth
    else:
        farms=aggrDay
        date=today
    try:
        sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        i=0
        for farm in farms:
            args=[
                str(date),
                str(farms[i][1]['PowerSum']),
                str(farms[i][1]['PredictPowerSum']),
                str(farms[i][1]['IrradianceMean']/farm[1]['NumIrr']),
                str(farms[i][1]['IrradianceMax']),
                str(farms[i][1]['IrradianceMin']),
                str(farms[i][1]['PanelTemperatureMean']/farm[1]['NumTemp']),
                str(farms[i][1]['PanelTemperatureMax']),
                str(farms[i][1]['PanelTemperatureMin']),
                str(farms[i][1]['IntensityMean']/farm[1]['NumInt']),
                str(farms[i][1]['IntensityMax']),
                str(farms[i][1]['IntensityMin']),
                str(farms[i][1]['VoltageMean']/farm[1]['NumVol']),
                str(farms[i][1]['VoltageMax']),
                str(farms[i][1]['VoltageMin']),
                farms[i][0]
                ]
            
            cursor.execute(query,args)
            i=i+1
    except Exception as e:
        print(f"ErrorF: "+repr(e))
        sql.rollback()
    finally:
        sql.commit()
        cursor.close()
        sql.close()

def deactivateAlert(alertType, farmID):
    try:
        sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        query="INSERT INTO lastSolvedAlerts SELECT * FROM activeAlerts AS a where a.FarmID=%s and a.alertType=%s ON DUPLICATE KEY UPDATE Date=a.Date;"
        query2="DELETE from activeAlerts as a where a.FarmID=%s and a.alertType=%s"
        data=[farmID,alertType]
        cursor.execute(query,data)
        cursor.execute(query2,data)
        sql.commit()
        sio.emit("deactivateAlert",{"alertType":alertType,"FarmID":farmID})
    except Exception as e:
        print(f"ErrorF: "+repr(e))
        sql.rollback()
    finally:
        cursor.close()
        sql.close()

def sendAlert(alertType, rawData):
    try:
        sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        query1="INSERT INTO alerts (Date,alertType,FarmID) VALUES(%s,%s,%s)"
        query2="INSERT INTO activeAlerts (Date,alertType,FarmID) VALUES(%s,%s,%s) \
                ON DUPLICATE KEY UPDATE Date=%s"
        data=[rawData["date"],\
                alertType,\
                rawData["FarmID"]]
        cursor.execute(query1,data)
        data.append(rawData["date"])
        cursor.execute(query2,data)
        sql.commit()
        sio.emit("activateAlert",{"alertType":alertType,"FarmID":rawData["FarmID"],"date":rawData["date"]})
    except Exception as e:
        print(f"ErrorF: "+repr(e))
        print("Alarm not saved")
        sql.rollback()
    finally:
        cursor.close()
        sql.close()

def write_to_sql(df, batchID):
    if(not sio.connected):
        try:
            sio.connect("http://localhost:5000")
        except:
            print("Could not connect to the server")
    rows=df.toJSON().collect()
    for row in rows:
        #Fill the values that aren't present but necesary with null
        schema=["date","Irradiance","PanelTemperature","Voltage","Intensity","Power","FarmID"]
        formatted=json.loads(row)
        keys=list(formatted.keys())
        global today
        global thisMonth
        global aggrDay
        global aggrMonth
        if today=="":
            today=datetime.strptime(formatted["date"],'%Y-%m-%dT%H:%M:%S').date()
            thisMonth=today
        global farmNames
        alert=False
        for elem in schema:
            if elem not in keys:
                #If there's a element not defined, send alert and skip
                alert=True
                break
        if alert:
            sendAlert(alertType.BadFormat.value,formatted)
            continue
        try:
            formatted['predict_power']=calculatePrediction(formatted['Irradiance'],formatted['PanelTemperature'],formatted['FarmID'])
        except:
            formatted['predict_power']=0
        #If we're at night, the power might be too low to take correct predictions and send alarms
        if formatted['Power']>0.2:
            perc=getPowerRelation(formatted['Power'],formatted['predict_power'])
            if perc>0.25:
                sendAlert(alertType.LowPower.value,formatted)
            else:
                deactivateAlert(alertType.LowPower.value,formatted['FarmID'])
        newFarm=True
        i=0
        for pair in farmNames:#Setup of timers
            if farmNames[i][0]==formatted["FarmID"]:
                if farmNames[i][1]!= None:
                    farmNames[i][1].cancel()
                farmNames[i][1]=Timer(3600.0,sendAlert,[alertType.FarmIdle.value,formatted])
                farmNames[i][1].start()
                deactivateAlert(alertType.FarmIdle.value,formatted['FarmID'])
                deactivateAlert(alertType.BadFormat.value,formatted['FarmID'])
                newFarm=False
                break
            i=i+1
        if newFarm:
            aggrDay.append([formatted["FarmID"],{}])
            aggrMonth.append([formatted["FarmID"],{}])
            t=Timer(3600,sendAlert,[alertType.FarmIdle.value,formatted])
            farmNames.append([formatted["FarmID"],t.start()])

        try:
            sio.emit('NewSolarData',json.dumps(formatted))
        except Exception as e:
            print("Error sio "+repr(e))
            print("Could not connect to server")
        
        #Store the rows in the database, 'formatted' is a dictionary with all the json fields accessible by formatted["field"]
        try:
            sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
            cursor=sql.cursor()
            add_data="INSERT INTO solardata (date,Irradiance,PanelTemperature,Intensity,Voltage,Power, predict_power,FarmID) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)"
            now=datetime.strptime(formatted["date"],'%Y-%m-%dT%H:%M:%S')
            data=(now,\
                    str(formatted["Irradiance"]),\
                    str(formatted["PanelTemperature"]),\
                    str(formatted["Intensity"]),\
                    str(formatted["Voltage"]),\
                    str(formatted["Power"]),\
                    str(formatted["predict_power"]),\
                    str(formatted["FarmID"]))
            cursor.execute(add_data,data)
            sql.commit()
            now=now.date()
            if today != now:
                #If a day passed, reset the aggregated data and store them in the database
                writeAggrDatabase('aggregated_day')
                print(aggrDay)
                today=now
                i=0
                #Reset the variables
                for dicts in aggrDay:
                    aggrDay[i]=[farmNames[i][0],{}]
                    i=i+1
                i=0
                if now.month!=thisMonth.month:
                    writeAggrDatabase('aggregated_month')
                    thisMonth=now
                    for dicts in aggrMonth:
                        aggrMonth[i]=[farmNames[i][0],{}]
                        i=i+1
            #If the day didn't pass yet, continue calculating the aggregated values
            else:
                aggregateValues(formatted,"day")
                aggregateValues(formatted,"month")
        
        except Exception as e:
            sql.rollback()
            print(f"Error: {e}")
        finally:
            cursor.close()
            sql.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("""
        Usage: structured_kafka_wordcount.py <bootstrap-servers> <subscribe-type> <topics>
        """, file=sys.stderr)
        sys.exit(-1)

    bootstrapServers = sys.argv[1]
    subscribeType = sys.argv[2]
    topics = sys.argv[3]
    try:
        sio.connect("http://localhost:5000")
    except:
        print("Could not connect to the server")   
    try:
        files = subprocess.Popen(['ls','-t','checkpoint/offsets'], stdout=subprocess.PIPE)
        latest_file = subprocess.check_output(['head','-n','1'], stdin=files.stdout)
        files.wait()
        latest_file=int(latest_file)
        latest_file=str(latest_file)
        print("File: "+latest_file)
        file= open("checkpoint/offsets/"+latest_file, mode='r', encoding='utf-8-sig')
        lines= file.readlines()
        cpoint=lines[-1]
    except Exception as e:
        print("Error getting file: "+repr(e))
        #Maybe there are no checkpoints yet. In this case let spark start with the latest index
        #https://spark.apache.org/docs/latest/structured-streaming-kafka-integration.html
        cpoint='{"'+topics+'":{"0":-1}}'
    
    spark = SparkSession\
        .builder\
        .appName("Get&FormatSolarData")\
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    jsonSchema=StructType([StructField("FechaHora", StringType()),\
                           StructField("G", FloatType()),\
                           StructField("Tc",FloatType()),\
                           StructField("I", FloatType()),\
                           StructField("V", FloatType()),\
                           StructField("P", FloatType()),\
                           StructField("Inst",StringType())\
                         ])

    #Create DataSet representing the stream of input lines from kafka
    print("***"+cpoint)
    datastream = spark\
        .readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", bootstrapServers)\
        .option("failOnDataLoss", "false")\
        .option(subscribeType, topics)\
        .option("startingOffsets",cpoint)\
        .load()\
        .select(from_json(col("value").cast("string"),jsonSchema).alias("stats"))\
        .select(col("stats.*"))\
        .withColumnRenamed("FechaHora","date")\
        .withColumnRenamed("G","Irradiance")\
        .withColumnRenamed("Tc","PanelTemperature")\
        .withColumnRenamed("I","Intensity")\
        .withColumnRenamed("V","Voltage")\
        .withColumnRenamed("P","Power")\
        .withColumnRenamed("Inst","FarmID")

 #For debug, we'll put this into a database afterwards
    todatabase= datastream.writeStream\
            .foreachBatch(write_to_sql)\
            .option('checkpointLocation', 'checkpoint')\
            .start()
    
    todatabase.awaitTermination()
