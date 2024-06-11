Here's the source code for my master's thesis.

The project needs the python libraries, most importantly, pyspark, mysql, flask and highchart\_core

As a dependency, we need to install Apache kafka in our computer for this to work. Start a cluster and create the topic "tiempo"

The script startSpark.sh downloads 2 libraries and connects to kafka and listens on the topic "tiempo". It expects to receive a json file with information of solar farms. It must contain at least data about date and the power in MWatts deployed for the application to work. Then it sends the information into a mysql database, as well as to the flask server on port 5000. The names for the feilds of the expected json are on the file. Edit these freely if you want the application compatible with your environment

The flask server has its own file on server.py, and it delivers an interface where people can see the daily statistics of all their solar farms in a (supposedly) intuitive way. The "/" page delivers links to the different solar farms inferred from the information received and, as well, a link to a filter page that asks the database about historic data.

THIS PROJECT IS NOT YET FINNISHED
