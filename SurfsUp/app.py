# Import the dependencies.
import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite", echo=False)

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station

# Create our session (link) from Python to the DB
# Resulted in invalid session closings for all API routes

#################################################
# Flask Setup
#################################################
app = Flask(__name__)
app.json.sort_keys = False

#################################################
# Flask Routes
#################################################
@app.route("/")
def homepage():
    """List all available API routes."""
    return (
        f"Available API Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/20161225<br/>"
        f"/api/v1.0/20161225/20170314"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return a list of precipitation in the last 12 months"""

    session = Session(engine)

    recent_date_raw = session.query(measurement.date).order_by(measurement.date.desc()).first()
    recent_date = dt.datetime.strptime(recent_date_raw['date'], '%Y-%m-%d')
    year_before_recent_date = recent_date - dt.timedelta(days=366)

    prcp_query = session.query(measurement.date, measurement.prcp)\
                        .filter((measurement.date >= year_before_recent_date) & (measurement.date <= recent_date))
    
    session.close()

    precipitation_12_months = []
    for date, prcp in prcp_query:
        precipitation_dict = {}
        precipitation_dict[date] = prcp
        precipitation_12_months.append(precipitation_dict)

    return jsonify(precipitation_12_months)


@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations"""
    session = Session(engine)

    stations_query = session.query(station.station).all()

    session.close()

    stations_all = list(np.ravel(stations_query))

    return jsonify(stations_all)


@app.route("/api/v1.0/tobs")
def tobs():
    """Return a list of temperature observations in the last 12 months"""

    session = Session(engine)

    recent_date_raw = session.query(measurement.date).order_by(measurement.date.desc()).first()
    recent_date = dt.datetime.strptime(recent_date_raw['date'], '%Y-%m-%d')
    year_before_recent_date = recent_date - dt.timedelta(days=366)

    active_stations = session.query(measurement.station, func.count(measurement.station))\
                            .group_by(measurement.station)\
                            .order_by(func.count(measurement.station).desc()).all()
    tobs_query = session.query(measurement.date, measurement.tobs)\
                        .filter(measurement.station == active_stations[0]['station'])\
                        .filter((measurement.date >= year_before_recent_date) & (measurement.date <= recent_date)).all()

    session.close()

    tobs_12_months = []
    for date, tobs in tobs_query:
        tobs_dict = {}
        tobs_dict[date] = tobs
        tobs_12_months.append(tobs_dict)

    return jsonify(tobs_12_months)


@app.route("/api/v1.0/<start>")
def start_date(start):
    """Return a list of the minimum temperature, the average temperature, and the maximum temperature
       for a specified start date, or a 404 if date is invalid<br/>"""
    "The date format is YYYYMMDD"

    session = Session(engine)

    try:
        normalized_date = start.replace('-', '').replace(' ', '')
        formatted_date = dt.datetime.strptime(normalized_date, '%Y%m%d')
        start_date_query = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs))\
                                .filter(measurement.date >= formatted_date).all()
        
        session.close()

        min_avg_max = list(np.ravel(start_date_query))
        tobs_start_date_dict = {}
        tobs_start_date_dict['Minimum Temperature'] = min_avg_max[0]
        tobs_start_date_dict['Average Temperature'] = min_avg_max[1]
        tobs_start_date_dict['Maximum Temperature'] = min_avg_max[2]

        return jsonify(tobs_start_date_dict)
    
    except ValueError:
        return jsonify(f"Error 404: {start} is not a valid date or date format (YYYYMMDD)")


@app.route("/api/v1.0/<start>/<end>")
def start_end_dates(start, end):
    """Return a list of the minimum temperature, the average temperature, and the maximum temperature
       for a specified start-end range, or a 404 if either date is invalid<br/>"""
    "The date format is YYYYMMDD"

    session = Session(engine)

    try:
        normalized_start_date = start.replace('-', '').replace(' ', '')
        normalized_end_date = end.replace('-', '').replace(' ', '')
        formatted_start_date = dt.datetime.strptime(normalized_start_date, '%Y%m%d')
        formatted_end_date = dt.datetime.strptime(normalized_end_date, '%Y%m%d')
        start_end_date_query = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs))\
                                .filter((measurement.date >= formatted_start_date) & (measurement.date <= formatted_end_date)).all()

        session.close()

        min_avg_max = list(np.ravel(start_end_date_query))
        tobs_start_end_date_dict = {}
        tobs_start_end_date_dict['Minimum Temperature'] = min_avg_max[0]
        tobs_start_end_date_dict['Average Temperature'] = min_avg_max[1]
        tobs_start_end_date_dict['Maximum Temperature'] = min_avg_max[2]

        return jsonify(tobs_start_end_date_dict)
    
    except ValueError:
        return jsonify(f"Error 404: {start} or {end} is not a valid date or date format (YYYYMMDD)")


if __name__ == '__main__':
    app.run(debug=True)
