koch
====

Python utility for gathering Pagerduty incident and incident note data from the previous 7 days for later analysis.  It lets you know how you're doing.

![Ed Koch - How am I doing?](http://media.nbcnewyork.com/images/485*273/koch+howm+i+doing.JPG)

Currently there are hooks for putting data into [New Relic Insights](http://newrelic.com/insights) but other data stores are in the works, including [MongoDB](http://www.mongodb.org/) and [InfluxDB](http://influxdb.com/).

This script was inspired by [insights-about-pagerduty](https://github.com/newrelic/insights-about-pagerduty).

# Configuration

The driver.py script expects configuration values to be present in app.cfg.  A sample file app.cfg.example has been provided but will need to be updated and renamed appropriately.

# Syntax

```bash

python driver.py
```
