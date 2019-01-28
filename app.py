import os

import pendulum

from flask import Flask, render_template, jsonify, request
from sqlobject import AND

from model import Device, Scan

app = Flask(__name__, template_folder="templates", static_url_path="", static_folder="static")

db_filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bluetooth-scan.db')
db_scheme = 'sqlite:' + db_filename


@app.route('/')
def month():
    return render_template('calendar.j2')


@app.route('/events.json')
def get_events():
    start = request.args.get('start')
    end = request.args.get('end')
    if not start or not end:
        return jsonify({})
    else:
        start_dt = pendulum.parse(start)
        end_dt = pendulum.parse(end)

    active_scans = Scan.selectBy(present=True).filter(
            AND(Scan.q.timestamp>start_dt.float_timestamp, Scan.q.timestamp<end_dt.float_timestamp)
        ).orderBy('timestamp')

    periods = []
    current_period = {}
    last_active_scan_timestamp = None
    for scan in active_scans:
        if not current_period:
            current_period['start'] = scan.timestamp
            last_active_scan_timestamp = scan.timestamp
        # delta between last present scan is more than x minutes change the value
        # if you accept longer break far away of your computer,
        # otherwise it will create a new period
        if pendulum.from_timestamp(scan.timestamp).diff(pendulum.from_timestamp(last_active_scan_timestamp)).in_minutes() > 5:
            current_period['end'] = last_active_scan_timestamp
            periods.append(current_period)
            current_period = {'start': scan.timestamp}
        last_active_scan_timestamp = scan.timestamp

    # last in progress event
    current_period['end'] = last_active_scan_timestamp
    periods.append(current_period)
    daily_summary = []

    last_day = None
    last_duration = pendulum.duration(minutes=0)
    for period in periods:
        time_period = pendulum.from_timestamp(period['end']) - pendulum.from_timestamp(period['start'])
        duration = pendulum.duration(minutes=time_period.in_minutes())
        period['title'] = "Total : {hours:02}:{minutes:02}".format(hours=duration.hours, minutes=duration.minutes)
        current_date_string = pendulum.from_timestamp(period['start']).to_date_string()

        if not last_day or last_day == current_date_string:
            last_duration += duration
        else:
            daily_summary.append(
                {
                    'title': "Daily total : {hours:02}:{minutes:02}".format(hours=duration.hours, minutes=duration.minutes),
                    'start': last_day
                 })

        last_day = current_date_string

        period['start'] = pendulum.from_timestamp(period['start']).isoformat()
        period['end'] = pendulum.from_timestamp(period['end']).isoformat()

    daily_summary.append(
        {
            'title': "Daily total : {hours:02}:{minutes:02}".format(hours=last_duration.hours, minutes=last_duration.minutes),
            'start': last_day
        })

    return jsonify(periods + daily_summary)


if __name__ == '__main__':
    app.run()
