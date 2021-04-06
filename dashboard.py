import io
import datetime

import requests
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


ACTIVITY_NAMES = ['break', 'meeting', 'chat', 'confluence', 'gitlab', 'jira', 'terminal', 'outlook', 'other']


@st.cache
def load_data():
    resp = requests.get("https://raw.githubusercontent.com/mlesniew/activity-logger-data/master/data.csv")
    return pd.read_csv(
        io.StringIO(resp.text),
        header=0,
        parse_dates=["timestamp"],
        index_col=0,
    )


@st.cache(allow_output_mutation=True)
def get_activities(start_date, end_date):
    data = load_data()
    data = data.loc[data.index <= np.datetime64(end_date)]
    data = data.loc[data.index >= np.datetime64(start_date)]
    return data


@st.cache
def get_activity_time(start_date, end_date):
    data = get_activities(start_date, end_date)
    ret = pd.DataFrame()

    # convert binary columns to hour count
    for name in ACTIVITY_NAMES:
        ret[name] = data[name] * data["timedelta"] / (60 * 60)

    return ret


@st.cache
def get_work_hours(start_date, end_date, aggregation="24h"):
    data = get_activities(start_date, end_date)
    data = data["timedelta"].to_frame()
    data = data.resample(aggregation, label="left").sum() / (60 * 60)
    return data


@st.cache
def get_activity_start_and_duration(activity, start_date, end_date):
    data = get_activities(start_date, end_date)

    meeting_start = data[activity].diff() & data[activity]
    meeting_number = meeting_start.astype(int).cumsum()
    meeting_end = data[activity].diff() & ~data[activity]
    meetings = pd.concat(
        [
            meeting_number.rename("number"),
            meeting_start.rename("start"),
            meeting_end.rename("end"),
        ],
        axis=1,
    )
    meetings = meetings.loc[meetings["start"] | meetings["end"]]
    del meetings["start"]
    del meetings["end"]
    meetings.reset_index(inplace=True)
    meetings = meetings.groupby("number").agg(["min", "max"])
    meetings.columns = ["start", "end"]

    return meetings


st.title("Work time")

if st.sidebar.checkbox("Specify time range"):
    start_date = st.sidebar.date_input(
        "Start date",
        min_value=datetime.date(2021, 1, 1),
        max_value=datetime.date(2021, 12, 31),
        value=datetime.date.today() - datetime.timedelta(days=8),
    )

    end_date = st.sidebar.date_input(
        "End date",
        min_value=datetime.date(2021, 1, 1),
        max_value=datetime.date(2021, 12, 31),
        value=datetime.date.today() - datetime.timedelta(days=1),
    )
else:
    start_date = datetime.date(1970, 1, 1)
    end_date = datetime.date.today() + datetime.timedelta(days=365)

if end_date <= start_date:
    st.sidebar.text("Invalid time range!")


total_time = get_activity_time(start_date, end_date)[ACTIVITY_NAMES].sum().reset_index()
total_time.columns = ["activity", "hours"]
total_hours = total_time["hours"].sum().astype(float)
st.header(f"Total time worked: {total_hours:.1f} hours")
st.plotly_chart(
    px.pie(
        total_time,
        names="activity",
        values="hours",
    )
)

if st.checkbox("Show data", key="checkbox1"):
    total_time.index = total_time["activity"]
    total_time.sort_values("hours", ascending=False, inplace=True)
    del total_time["activity"]
    st.table(total_time)

######

if end_date - start_date >= datetime.timedelta(days=14):
    st.header("Work time per week")
    work_hours = get_work_hours(start_date, end_date, "W-SUN")
    st.plotly_chart(px.bar(work_hours.reset_index(), x="timestamp", y="timedelta"))

######

st.header("Activities by day")

daily = get_activity_time(start_date, end_date).resample("24h").sum()
st.plotly_chart(px.bar(daily.reset_index(), x="timestamp", y=ACTIVITY_NAMES))
daily["total"] = daily.sum(axis=1)

if st.checkbox("Show data", key="checkbox2"):
    st.table(daily)

######

st.header("Activities by time of day")

resolution = st.selectbox("Resolution",
                          options=[5, 10, 15, 20, 30, 60],
                          index=4,
                          format_func=lambda x: f"{x} minutes")

time_histogram = (
    get_activity_time(start_date, end_date)
    .resample(f"{resolution}T")
    .sum()
    .reset_index()
)
time_histogram["timestamp"] = time_histogram["timestamp"].apply(
    lambda t: t.replace(year=2021, month=3, day=1)
)
time_histogram = time_histogram.groupby("timestamp").sum() * (60 / resolution)
chart = px.area(time_histogram.reset_index(), x="timestamp", y=ACTIVITY_NAMES)
chart.update_xaxes(tickformat="%H:%M")
st.plotly_chart(chart)

######

st.header("Meeting duration distribution")

meetings = get_activity_start_and_duration("meeting", start_date, end_date)
durations = (meetings["end"] - meetings["start"]) / np.timedelta64(1, "m")

bins = st.slider("Number of bins", 5, 50, 20, 1)
chart = px.histogram(durations, nbins=bins, marginal="rug")
chart.update_layout(showlegend=False, xaxis_title="Meeting duration [minutes]")
st.plotly_chart(chart)
