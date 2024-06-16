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

def write_to_sql(df, batchID):
    rows=df.toJSON().collect()
    for row in rows:
        #Fill the values that aren't present but necesary with null
        schema=["date","Irradiance","PanelTemperature","Voltage","Intensity","Power","FarmID"]
        formatted=json.loads(row)
        keys=list(formatted.keys())
        for elem in schema:
            if elem not in keys:
                formatted[elem]=None
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
