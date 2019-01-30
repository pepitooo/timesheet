import os
from collections import defaultdict

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

    if active_scans.count() == 0:
        return jsonify({})

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
            current_period['date'] = pendulum.from_timestamp(last_active_scan_timestamp).to_date_string()
            periods.append(current_period)
            current_period = {'start': scan.timestamp}
        last_active_scan_timestamp = scan.timestamp

    # last in progress event
    current_period['end'] = last_active_scan_timestamp
    current_period['date'] = pendulum.from_timestamp(last_active_scan_timestamp).to_date_string()
    periods.append(current_period)

    pivot = defaultdict(list)
    for item in periods:
        time_period = pendulum.from_timestamp(item['end']) - pendulum.from_timestamp(item['start'])
        pivot[item['date']].append(time_period.in_minutes())

    daily_summary = [{'start': k, 'total_duration': sum(values)} for k, values in pivot.items()]

    pivot_no_break = defaultdict(list)
    for item in periods:
        pivot_no_break[item['date']].append(item['start'])
        pivot_no_break[item['date']].append(item['end'])

    daily_no_break_summary = [{'start': k, 'start_ts': min(values), 'end_ts': max(values)} for k, values in pivot_no_break.items()]

    final_summary_duration = pendulum.duration(minutes=0)
    for item in daily_summary:
        duration = pendulum.duration(minutes=item['total_duration'])
        item['title'] = "Daily total : {hours:02}:{minutes:02}".format(hours=duration.hours, minutes=duration.minutes),
        item['color'] = '#257e4a'
        final_summary_duration += duration

    final_no_break_summary_duration = pendulum.duration(minutes=0)
    for item in daily_no_break_summary:
        time_period = pendulum.from_timestamp(item['end_ts']) - pendulum.from_timestamp(item['start_ts'])
        duration = pendulum.duration(minutes=time_period.in_minutes())
        item['title'] = "No break : {hours:02}:{minutes:02}".format(hours=duration.hours, minutes=duration.minutes)
        item['color'] = '#FF6600'
        del item['start_ts']
        del item['end_ts']
        final_no_break_summary_duration += duration

    for period in periods:
        time_period = pendulum.from_timestamp(period['end']) - pendulum.from_timestamp(period['start'])
        duration = pendulum.duration(minutes=time_period.in_minutes())
        period['title'] = "{hours:02}:{minutes:02}".format(hours=duration.hours, minutes=duration.minutes)
        period['start'] = pendulum.from_timestamp(period['start']).isoformat()
        period['end'] = pendulum.from_timestamp(period['end']).isoformat()

    final_summary = [
        {
            'start': end_dt.subtract(days=1).to_date_string(),
            'title': ' Total : {hours:02}:{minutes:02}'.format(
                hours=final_summary_duration.hours + final_summary_duration.days * 24,
                minutes=final_summary_duration.minutes),
            'color': '#FF0000'
        },
        {
            'start': end_dt.subtract(days=1).to_date_string(),
            'title': 'No beak : {hours:02}:{minutes:02}'.format(
                hours=final_no_break_summary_duration.hours + final_no_break_summary_duration.days * 24,
                minutes=final_no_break_summary_duration.minutes),
            'color': '#FF0000'
        }
    ]
    return jsonify(periods + daily_summary + daily_no_break_summary + final_summary)


if __name__ == '__main__':
    app.run()
