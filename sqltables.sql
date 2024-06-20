CREATE TABLE `solardata` (
  `ID` int NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT NULL,
  `Irradiance` decimal(15,7) DEFAULT NULL,
  `PanelTemperature` decimal(15,7) DEFAULT NULL,
  `Intensity` decimal(15,7) DEFAULT NULL,
  `Voltage` decimal(15,7) DEFAULT NULL,
  `Power` decimal(15,7) DEFAULT NULL,
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
