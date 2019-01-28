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

    events = []
    current_event = {}
    last_active_scan_timestamp = None
    for scan in active_scans:
        if not current_event:
            current_event['start'] = scan.timestamp
            last_active_scan_timestamp = scan.timestamp
        # delta between last present scan is more than x minutes
        if pendulum.from_timestamp(scan.timestamp).diff(pendulum.from_timestamp(last_active_scan_timestamp)).in_minutes() > 5:
            current_event['end'] = last_active_scan_timestamp
            events.append(current_event)
            current_event = {'start': scan.timestamp}
        last_active_scan_timestamp = scan.timestamp

    # last in progress event
    current_event['end'] = last_active_scan_timestamp
    events.append(current_event)
    daily_summary = []

    last_day = None
    last_duration = pendulum.duration(minutes=0)
    for event in events:
        period = pendulum.from_timestamp(event['end']) - pendulum.from_timestamp(event['start'])
        duration = pendulum.duration(minutes=period.in_minutes())
        event['title'] = "Total : {hours:02}:{minutes:02}".format(hours=duration.hours, minutes=duration.minutes)
        current_date_string = pendulum.from_timestamp(event['start']).to_date_string()

        if not last_day or last_day == current_date_string:
            last_duration += duration
        else:
            daily_summary.append(
                {
                    'title': "Daily total : {hours:02}:{minutes:02}".format(hours=duration.hours, minutes=duration.minutes),
                    'start': last_day
                 })

        last_day = current_date_string

        event['start'] = pendulum.from_timestamp(event['start']).isoformat()
        event['end'] = pendulum.from_timestamp(event['end']).isoformat()

    daily_summary.append(
        {
            'title': "Daily total : {hours:02}:{minutes:02}".format(hours=last_duration.hours, minutes=last_duration.minutes),
            'start': last_day
        })

    return jsonify(events + daily_summary)


if __name__ == '__main__':
    app.run()
