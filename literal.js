document.addEventListener('DOMContentLoaded', function() {
var myChart = Highcharts.chart('target_div',
{
  series: [{
  data: [[1547263980000.0,
null]],
  name: 'Intensity',
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