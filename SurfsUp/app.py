# Import the dependencies.

from flask import Flask, jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, and_
from datetime import datetime as dt
from dateutil.relativedelta import relativedelta

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
base = automap_base()

# reflect the tables
base.prepare(engine, reflect=True)

# Save references to each table
measurement = base.classes.measurement
station = base.classes.station

# Create our session (link) from Python to the DB
# Session is created within individual routes and closed
# as having common session throws an intermittent error
# "Objects created in a thread can only be used in that same thread"

#################################################
# Flask Setup
#################################################
app = Flask(__name__)
# Disable default sorting when Jsonify is used
app.config['JSON_SORT_KEYS'] = False

#################################################
# Global variable setup
#################################################
accepted_input_date_format = "%Y-%m-%d"


#################################################
# Flask Routes
#################################################

@app.route("/")
def home():
    """List all available api routes."""
    return (
        f"<b><u>Available Routes</u></b><br/>"
        f"<br/>"
        f"<br/>"
        f"1. Precipitation for last 12 months: &ltbase url&gt/api/v1.0/precipitation<br/>"
        f"<br/>"
        f"2. List of Stations: &ltbase url&gt/api/v1.0/stations<br/>"
        f"<br/>"
        f"3. Most active station's temperature for one year: &ltbase url&gt/api/v1.0/tobs<br/>"
        f"<br/>"
        f"4. Temperature stats (min,avg,max) for the given start date(yyyy-mm-dd): &ltbase url&gt/api/v1.0/&ltyyyy-mm-dd&gt<br/>"
        f"<br/>"
        f"5. Temperature stats (min,avg,max) for the date range between supplied start and end dates(yyyy-mm-dd): &ltbase url&gt/api/v1.0/&ltstart date&gt/&ltend date&gt"
    )


# Static Route 1. Precipitation for last 12 months
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    selection_columns = [measurement.date, measurement.prcp]

    # First find the most recent date available in the dataset
    most_recent_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]

    # Calculate the date one year from the last date in data set.
    date_year_before = (dt.strptime(most_recent_date, "%Y-%m-%d") - relativedelta(days=366)).strftime("%Y-%m-%d")

    # Perform a query to retrieve the data and precipitation values
    try:
        query_result = session.query(*selection_columns).filter(measurement.date > date_year_before). \
            order_by(measurement.date.desc()).all()

        # Store query result into dictionary
        results = []
        for date, prcp in query_result:
            precipitation_results = {"Date": date, "Precipitation": prcp}
            results.append(precipitation_results)
        # Return json representation of query result which is in dictionary now
        return jsonify(results)
    except Exception as e:
        return "Please try again. Something went wrong!"
    finally:
        session.close()


# Static Route 2. List of Stations
@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    selection_columns = [station.id, station.station]
    # Perform a query to retrieve the data and precipitation values
    try:
        query_result = session.query(*selection_columns).all()

        # Store query result into dictionary
        results = []
        for id, name in query_result:
            stations_results = {"ID": id, "Name": name}
            results.append(stations_results)

        # Return json representation of query result which is in dictionary now
        return jsonify(results)
    except Exception as e:
        return "Please try again. Something went wrong!"
    finally:
        session.close()


# Static Route 3. Most active station's temperature for one year
@app.route("/api/v1.0/tobs")
def temperature_observations():
    session = Session(engine)
    selection_columns = [measurement.station, measurement.date, measurement.tobs]

    # Query to find the most active station
    try:
        station_counts = func.count(measurement.station)
        most_active_station = session.query(measurement.station, station_counts). \
            order_by(station_counts.desc()). \
            group_by(measurement.station).first()[0]

        # Perform a query to retrieve the data and tobs values
        query_result = session.query(*selection_columns).filter(measurement.station == most_active_station). \
            order_by(measurement.date.desc()).all()

        # Store query result into dictionary
        results = []
        for name, date, tobs in query_result:
            tobs_results = {"Station": name, "Date": date, "Temperature Observations": tobs}
            results.append(tobs_results)
        # Return json representation of query result which is in dictionary now
        return jsonify(results)
    except Exception as e:
        return "Please try again. Something went wrong!"
    finally:
        session.close()


# Dynamic Route 4. Temperature stats (min,avg,max) for the given start date(yyyy-mm-dd)
@app.route("/api/v1.0/<start>")
def temp_stats_start_date(start):
    try:
        session = Session(engine)
        try:
            dt.strptime(start, accepted_input_date_format)
        except ValueError:
            raise Exception

        query_result = session.query(func.min(measurement.tobs), func.avg(measurement.tobs),
                                     func.max(measurement.tobs)). \
            filter(measurement.date >= start).all()
        print(query_result)
        # Store query result into dictionary
        results = []
        for min, avg, max in query_result:
            tobs_results = {"Min Temp": min, "Avg Temp": avg, "Max Temp": max}
            results.append(tobs_results)
        # Return json representation of query result which is in dictionary now
        session.close()
        return jsonify(results)
    except Exception as e:
        return "Please enter date in valid format YYYY-MM-DD"
    finally:
        if session:
            session.close()


# Dynamic Route 5. Temperature stats (min,avg,max) for the date range between supplied start and end dates(yyyy-mm-dd)
@app.route("/api/v1.0/<start>/<end>")
def temp_stats_range(start, end):
    try:
        session = Session(engine)
        try:
            dt.strptime(start, accepted_input_date_format)
            dt.strptime(end, accepted_input_date_format)
        except ValueError:
            raise Exception
        query_result = session.query(func.min(measurement.tobs), func.avg(measurement.tobs),
                                     func.max(measurement.tobs)). \
            filter(and_(measurement.date >= start, measurement.date <= end)).all()
        # Store query result into dictionary
        results = []
        for min, avg, max in query_result:
            tobs_results = {"Min Temp": min, "Avg Temp": avg, "Max Temp": max}
            results.append(tobs_results)
        # Return json representation of query result which is in dictionary now
        session.close()
        return jsonify(results)
    except Exception as e:
        return "Please enter dates in valid format YYYY-MM-DD"
    finally:
        if session:
            session.close()


if __name__ == "__main__":
    app.run(debug=True)
