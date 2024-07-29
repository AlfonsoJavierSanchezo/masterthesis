CREATE TABLE `solardata` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT NULL,
  `Irradiance` decimal(15,7) DEFAULT NULL,
  `PanelTemperature` decimal(15,7) DEFAULT NULL,
  `Intensity` decimal(15,7) DEFAULT NULL,
  `Voltage` decimal(15,7) DEFAULT NULL,
  `Power` decimal(15,7) DEFAULT NULL,
  `predict_power` decimal(15,7) DEFAULT NULL,
  `FarmID` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ID`)
);

CREATE TABLE `alertTypes` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Severity` varchar(20)NOT NULL, 
  `Description` varchar(200) NOT NULL,
  PRIMARY KEY (`ID`)
);

INSERT INTO alertTypes (Severity, Description) VALUES("Warning","Farm didn't send correct information, few fields");
INSERT INTO alertTypes (Severity, Description) VALUES("Warning","Farm did not send information in an hour now");
INSERT INTO alertTypes (Severity, Description) VALUES("Warning","Farm's power is too different from estimate");

CREATE TABLE `alerts` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Date` datetime NOT NULL,
  `alertType` int NOT NULL,
  `FarmID` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  FOREIGN KEY(`alertType`) REFERENCES (alertTypes.ID)
);

CREATE TABLE `activeAlerts` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Date` datetime NOT NULL,
  `alertType` int NOT NULL,
  `FarmID` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ID`),
  FOREIGN KEY(`alertType`) REFERENCES (alertTypes.ID),
  UNIQUE (alertType,FarmID)
);

CREATE TABLE `aggregated_day` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `PowerSum` decimal(15,7) DEFAULT NULL,
  `PredPowerSum` decimal(15,7) DEFAULT NULL,
  `IrradianceMean` decimal(15,7) DEFAULT NULL,
  `IrradianceMax` decimal(15,7) DEFAULT NULL,
  `IrradianceMin` decimal(15,7) DEFAULT NULL,
  `PanelTemperatureMean` decimal(15,7) DEFAULT NULL,
  `PanelTemperatureMax` decimal(15,7) DEFAULT NULL,
  `PanelTemperatureMin` decimal(15,7) DEFAULT NULL,
  `IntensityMean` decimal(15,7) DEFAULT NULL,
  `IntensityMax` decimal(15,7) DEFAULT NULL,
  `IntensityMin` decimal(15,7) DEFAULT NULL,
  `VoltageMean` decimal(15,7) DEFAULT NULL,
  `VoltageMax` decimal(15,7) DEFAULT NULL,
  `VoltageMin` decimal(15,7) DEFAULT NULL,
  `FarmID` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ID`)
);
CREATE TABLE `aggregated_month` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `date` date DEFAULT NULL,
  `PowerSum` decimal(15,7) DEFAULT NULL,
  `PredPowerSum` decimal(15,7) DEFAULT NULL,
  `IrradianceMean` decimal(15,7) DEFAULT NULL,
  `IrradianceMax` decimal(15,7) DEFAULT NULL,
  `IrradianceMin` decimal(15,7) DEFAULT NULL,
  `PanelTemperatureMean` decimal(15,7) DEFAULT NULL,
  `PanelTemperatureMax` decimal(15,7) DEFAULT NULL,
  `PanelTemperatureMin` decimal(15,7) DEFAULT NULL,
  `IntensityMean` decimal(15,7) DEFAULT NULL,
  `IntensityMax` decimal(15,7) DEFAULT NULL,
  `IntensityMin` decimal(15,7) DEFAULT NULL,
  `VoltageMean` decimal(15,7) DEFAULT NULL,
  `VoltageMax` decimal(15,7) DEFAULT NULL,
  `VoltageMin` decimal(15,7) DEFAULT NULL,
  `FarmID` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ID`)
);

grant insert on solardata to spark;
grant insert on aggregated_month to spark;
grant insert on aggregated_day to spark;
grant insert on alerts to spark;
grant insert on activeAlerts to spark;
grant update on activeAlerts to spark;
grant delete on activeAlerts to spark;
grant select on activeAlerts to spark;
grant insert on lastSolvedAlerts to spark;
grant update on lastSolvedAlerts to spark;

grant select on solardata to server;
grant select on aggregated_month to server;
grant select on aggregated_day to server;
grant select on alerts to server;
grant select on activeAlerts to server;
grant select on alertTypes to server;
grant select on lastSolvedAlerts to server;
