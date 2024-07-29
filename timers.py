
import mysql.connector
from datetime import datetime, timedelta
import random

if __name__ == '__main__':
    sql=mysql.connector.connect(user='spark',password='sparkpass',host='localhost', database='tiempo')
    cursor=sql.cursor()
    '''
    query="INSERT INTO aggregated_day (date,PowerSum,PredPowerSum,IrradianceMean,IrradianceMax,IrradianceMin,\
        PanelTemperatureMean,PanelTemperatureMax,PanelTemperatureMin\
        ,IntensityMean,IntensityMax,IntensityMin,\
        VoltageMean,VoltageMax,VoltageMin,FarmID)\
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    date=datetime.strptime('2019-01-01','%Y-%m-%d')
    for i in range(1,32):
        args=[
                str(date),
                str(random.uniform(249.9005448-50,249.9005448+50)),#Powersum
                str(random.uniform(279.3636965-50,279.3636965+50)),#PredictPowerSum
                str(random.uniform(549.4458092-40,549.4458092+40)),#IrradianceMean
                str(random.uniform(834.5356400-50,834.5356400+50)),#IrradianceMax
                str(0),#IrradianceMin
                str(random.uniform(31.3993965-3,31.3993965+3)),#PanelTemperatureMean
                str(random.uniform(45.5309450-4,45.5309450+4)),#PanelTemperatureMax
                str(0),#PanelTemperatureMin
                str(random.uniform(4.4633820-1.5,4.4633820+1.5)),#IntensityMean
                str(random.uniform(20.2275900-5,20.2275900+5)),#IntensityMax
                str(0.0001269),#IntensityMin
                str(random.uniform(285.9741747-50,285.9741747+50)),#VoltageMean
                str(random.uniform(388.9050600-50,388.9050600+50)),#VoltageMax
                str(random.uniform(1.8512356-1,1.8512356+1)),#VoltageMin
                "etsist1"
                ]
        cursor.execute(query,args)
        date=date+timedelta(days=1)
    '''
    query="SELECT * FROM aggregated_day AS d \
                WHERE (d.FarmID = etsist2) \
                AND (MONTH(d.date) = 1)\
                AND (YEAR(d.date)=2019)"
    #Array of dicts
    result={}
    dbdata = [dict((cursor.description[i][0], value)for i, value in enumerate(row)) for row in cursor.fetchall()]
    for data in dbdata:
        try:
            result['PowerSum']=result['PowerSum']+data['Power']
            result['PredictPowerSum']=result['PredictPowerSum']+data['predict_power']
            if data['Irradiance']!=0:
                result['IrradianceMean']=result['IrradianceMean']+data['Irradiance']
                result['IrradianceMax']=max(result['IrradianceMax'],data['Irradiance'])
                result['IrradianceMin']=min(result['IrradianceMin'],data['Irradiance'])
                result['NumIrr']=result['NumIrr']+1
            if data['PanelTemperature']!=0:
                result['PanelTemperatureMean']=result['PanelTemperatureMean']+data['PanelTemperature']
                result['PanelTemperatureMax']=max(result['PanelTemperatureMax'],data['PanelTemperature'])
                result['PanelTemperatureMin']=min(result['PanelTemperatureMin'],data['PanelTemperature'])
                result['NumVTemp']=result['NumTemp']+1
            if data['Intensity']!=0:
                result['IntensityMean']=result['IntensityMean']+data['Intensity']
                result['IntensityMax']=max(result['IntensityMax'],data['Intensity'])
                result['IntensityMin']=min(result['IntensityMin'],data['Intensity'])
                result['NumInt']=result['NumInt']+1
            if data['Voltage']!=0:
                result['VoltageMean']=result['VoltageMean']+data['Voltage']
                result['VoltageMax']=max(result['VoltageMax'],data['Voltage'])
                result['VoltageMin']=min(result['VoltageMin'],data['Voltage'])
                result['NumVol']=result['NumVol']+1
            print("aggregated "+data["FarmID"])
            
        except Exception as e:
            print(f"ErrorF: "+repr(e))
            result['PowerSum']=data['Power']
            result['PredictPowerSum']=data['predict_power']
            result['IrradianceMean']=data['Irradiance']
            result['IrradianceMax']=data['Irradiance']
            result['IrradianceMin']=data['Irradiance']
            result['PanelTemperatureMean']=data['PanelTemperature']
            result['PanelTemperatureMax']=data['PanelTemperature']
            result['PanelTemperatureMin']=data['PanelTemperature']
            result['IntensityMean']=data['Intensity']
            result['IntensityMax']=data['Intensity']
            result['IntensityMin']=data['Intensity']
            result['VoltageMean']=data['Voltage']
            result['VoltageMax']=data['Voltage']
            result['VoltageMin']=data['Voltage']
            result['NumIrr']=1
            result['NumTemp']=1
            result['NumInt']=1
            result['NumVol']=1
        i=i+1
    print(result)
