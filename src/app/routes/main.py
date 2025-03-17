from flask import Blueprint, jsonify, request

main = Blueprint("main", __name__)

# Sample data
statistics_data = {
    "population": {"2020": 19237691, "2021": 19119880},
    "gdp": {"2020": 250.6, "2021": 260.0},  # GDP in billion EUR
}


@main.route("/")
def home():
    return "Welcome to the Romania Public Statistics Dashboard!"


@main.route("/about")
def about():
    return "This is a dashboard for exploring public statistics in Romania."


@main.route("/statistics")
def get_statistics():
    return jsonify(statistics_data)


@main.route("/statistics/<string:metric>")
def get_metric(metric):
    if metric in statistics_data:
        return jsonify(statistics_data[metric])
    else:
        return jsonify({"error": "Metric not found"}), 404


@main.route("/statistics/<string:metric>/<string:year>")
def get_metric_year(metric, year):
    if metric in statistics_data and year in statistics_data[metric]:
        return jsonify({year: statistics_data[metric][year]})
    else:
        return jsonify({"error": "Metric or year not found"}), 404
