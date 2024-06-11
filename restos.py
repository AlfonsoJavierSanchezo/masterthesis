
    def write_to_sql(row):
        sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
        cursor=sql.cursor()
        try:
            insert=("INSERT INTO etsist1 (date,Irradiance,PanelTemperature,Intensity,Voltage,Power,Inst) VALUES ("+x["FechaHora"]+","+x["G"]+","+x["Tc"]+","+x["I"]+","+x["V"]+","+x["P"]+")")
            print(insert)
            cursor.exeucte(insert)
            sql.commit()
        except Exception as e:
            sql.rollback()
            print(f"Error: {e}")
        finally:
            cursor.close()
            sql.close()


    sql=spark.sparkContext.addPyFile(path="/home/alfonso/tfm/lib64/python3.11/site-packages/mysql.zip")


def write_to_sql(row):
    sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
    cursor=sql.cursor()
    try:
        insert=("INSERT INTO etsist1 (date,Irradiance,PanelTemperature,Intensity,Voltage,Power,Inst) VALUES ("+x["FechaHora"]+","+x["G"]+","+x["Tc"]+","+x["I"]+","+x["V"]+","+x["P"]+x["Inst"]+")")
        print(insert)
        cursor.exeucte(insert)
        sql.commit()
    except Exception as e:
        sql.rollback()
        print(f"Error: {e}")
    finally:
        cursor.close()
        sql.close()
