from flask import Blueprint, jsonify, render_template
import pandas as pd
import plotly.express as px

main = Blueprint("main", __name__)

# Sample data
statistics_data = {
    "population": {"2020": 19237691, "2021": 19119880},
    "gdp": {"2020": 250.6, "2021": 260.0},  # GDP in billion EUR
}


@main.route("/")
def home():
    return render_template("index.html")


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


# ------------------------------------------------
# Plotly routes
@main.route("/plot")
def plot():
    # Sample data
    df = pd.DataFrame(
        {"Year": [2020, 2021, 2022], "Population": [19237691, 19119880, 19000000]}
    )

    # Create a Plotly chart
    fig = px.bar(df, x="Year", y="Population", title="Population Over Time")

    # Convert the chart to HTML
    chart_html = fig.to_html(full_html=False)

    return render_template("plot.html", chart_html=chart_html)
