#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
 Consumes messages from one or more topics in Kafka and does wordcount.
 Usage: structured_kafka_wordcount.py <bootstrap-servers> <subscribe-type> <topics>
   <bootstrap-servers> The Kafka "bootstrap.servers" configuration. A
   comma-separated list of host:port.
   <subscribe-type> There are three kinds of type, i.e. 'assign', 'subscribe',
   'subscribePattern'.
   |- <assign> Specific TopicPartitions to consume. Json string
   |  {"topicA":[0,1],"topicB":[2,4]}.
   |- <subscribe> The topic list to subscribe. A comma-separated list of
   |  topics.
   |- <subscribePattern> The pattern used to subscribe to topic(s).
   |  Java regex string.
   |- Only one of "assign, "subscribe" or "subscribePattern" options can be
   |  specified for Kafka source.
   <topics> Different value format depends on the value of 'subscribe-type'.

 Run the example
    `$ bin/spark-submit examples/src/main/python/sql/streaming/structured_kafka_wordcount.py \
    host1:port1,host2:port2 subscribe topic1,topic2`
"""

import sys
import time
import socketio
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *

def write_to_sql(df, batchID):
    df.write\
            .format("jdbc")\
            .option("url","jdbc:mysql://localhost:3306/tiempo")\
            .option("driver","com.mysql.jdbc.Driver")\
            .option("dtable","solardata")\
            .option("user","spark")\
            .option("password","sparkpass")
    print("##DEBUG##ALERT##  :Supposedly sent data to database")
    try:
        rows=df.toJSON().collect()
        sio=socketio.SimpleClient()
        sio.connect("http://localhost:5000")
        sio.emit('NewSolarData',rows)
    except:
        print("Could not connect to server")
    finally:
        sio.disconnect()
    print(rows)
    
    #db_properties={"user":"spark","password":"sparkpass"}
    #df.write.jdbc(url="jdbc:mysql://localhost:3306/tiempo", table="solardata", driver="com.mysql.jdbc.Driver",properties=db_properties)

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
        .appName("StructuredKafkaWordCount")\
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    jsonSchema=StructType([ StructField("FechaHora", StringType()),StructField("G", FloatType()),StructField("Tc",FloatType()),StructField("I", FloatType()),StructField("V", FloatType()),StructField("P", FloatType()),StructField("Inst",StringType())])

    
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
