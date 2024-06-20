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
farmNames=[]

def idleAlert(farmID):
    try:
        sio=socketio.SimpleClient()
        sio.connect("http://localhost:5000")
        sio.emit('Alerts',farmID+" has not send information for an hour now, check its state")
    except:
        print("Error while emitting an alert")
    try:
        sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        add_data="INSERT INTO alerts (Date,Severity,Description,FarmID) VALUES(%s,%s,%s,%s)"
        data=(datetime.now(),\
                "Warning",\
                "Farm did not send information in an hour now",\
                str(formatted["FarmID"]))
        cursor.execute(add_data,data)
        sql.commit()
    except:
        sql.rollback()
    finally:
        sio.disconnect()
        cursor.close()
        sql.close()
        print("Handled alert")

def write_to_sql(df, batchID):#The idle alert does not work yet
    rows=df.toJSON().collect()
    for row in rows:
        #Fill the values that aren't present but necesary with null
        schema=["date","Irradiance","PanelTemperature","Voltage","Intensity","Power","FarmID"]
        formatted=json.loads(row)
        keys=list(formatted.keys())
        global farmNames
        for elem in schema:
            if elem not in keys:
                formatted[elem]=None
        if len(farmNames)==0:
            #ONLY FOR TESTING, WE NEED TO CHANGE "etisst3" BY formatted["farmID"]
            #farmNames.append(["etsist3",Timer(30,idleAlert,["etsist3"]).start()])
        else:
            newelem=True
            i=0
            for pair in farmNames:
                if farmNames[i][0]==formatted["FarmID"]:
                    if farmNames[i][1]!= None:
                        farmNames[i][1].cancel()
                    farmNames[i][1]=Timer(3600.0,idleAlert,formatted["FarmID"]).start()
                    newelem=False
                    break
                i=i+1
            if newelem:
                farmNames.append([formatted["FarmID"],Timer(3600,idleAlert,[formatted["FarmID"]]).start()])

        try:
            sio=socketio.SimpleClient()
            sio.connect("http://localhost:5000")
            sio.emit('NewSolarData',json.dumps(formatted))
        except:
            print("Could not connect to server")
        finally:
            sio.disconnect()
        #Store the rows in the database, x is a dictionary with all the json fields accessible by x["field"]
        try:
            sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
            cursor=sql.cursor()
            add_data="INSERT INTO solardata (date,Irradiance,PanelTemperature,Intensity,Voltage,Power,FarmID) VALUES(%s,%s,%s,%s,%s,%s,%s)"

            data=(datetime.strptime(formatted["date"],'%Y-%m-%dT%H:%M:%S'),\
                    str(formatted["Irradiance"]),\
                    str(formatted["PanelTemperature"]),\
                    str(formatted["Intensity"]),\
                    str(formatted["Voltage"]),\
                    str(formatted["Power"]),\
                    str(formatted["FarmID"]))
            cursor.execute(add_data,data)
            sql.commit()
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
    datastream = spark\
        .readStream\
        .format("kafka")\
        .option("kafka.bootstrap.servers", bootstrapServers)\
        .option(subscribeType, topics)\
        .load()\
        .select(from_json(col("value").cast("string"), jsonSchema ).alias("stats"))\
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
            .start()
    
    todatabase.awaitTermination()

#TODO Add a function that calculates monthly statistics and sends it to the MonthlyAggregation table in the database
#The database will have the same structure as the Solardata one but it will store means, max and mins (not for all the data)
#We need global variables for each data and when a month passes, the aggregated data will be stored in the database
