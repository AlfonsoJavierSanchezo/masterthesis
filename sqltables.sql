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
CREATE TABLE `alerts` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `Date` datetime NOT NULL,
  `Severity` varchar(10) NOT NULL,
  `Description` varchar(200) DEFAULT NULL,
  `FarmID` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`ID`)
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
