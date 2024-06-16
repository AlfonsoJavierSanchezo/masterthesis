document.addEventListener('DOMContentLoaded', function() {
var myChart = Highcharts.chart('target_div',
{
  series: [{
  data: [[1546935300000.0,
347.73743],
[1546935600000.0,
371.48083],
[1546935900000.0,
347.07632],
[1546936200000.0,
345.6294],
[1546936500000.0,
355.67508]],
  name: 'Voltage',
  type: 'line'
}],
  title: {
  text: 'etsist1'
},
  xAxis: {
  dateTimeLabelFormats: {
  day: '%e %b %Y',
  second: '%e %b %Y %H:%M:%S'
},
  type: 'datetime'
}
},
);
});