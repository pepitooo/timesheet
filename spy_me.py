import argparse
import configparser
import logging
import logging.config
import os
import sys
import subprocess
import time

from celery import Celery

from model import Device, Scan

app = Celery(
    'tirs_celery',
    broker='redis://localhost:6379/0',
    # ## add result backend here if needed.
    backend='redis://localhost:6379/0'
)
app.conf.timezone = 'Europe/Zurich'


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s.%(msecs)03d %(levelname)s %(name)s:%(filename)s:%(lineno)d %(message)s',
            'datefmt': "%Y-%m-%d %H:%M:%S",
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}


@app.on_after_configure.connect()
def setup_periodic_tasks(sender, **kwargs):
    config = configparser.ConfigParser()
    config['default'] = {
        'bluetooth_mac_address': 'xx:xx:xx:xx:xx'
    }
    config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'timesheet.conf'))
    bluetooth_mac_address = config['default']['bluetooth_mac_address']
    sender.add_periodic_task(1.00*60, check_bluetooth_presence.s(bluetooth_mac_address))


@app.task
def check_bluetooth_presence(mac_address):
    bluetooth_ping_cmd = ['l2ping', mac_address, '-c', '1']
    ret = subprocess.call(bluetooth_ping_cmd, shell=False)

    devices = Device.selectBy(mac_address=mac_address)
    if devices.count():
        device = devices.getOne()
    else:
        device = Device(mac_address=mac_address)
    Scan(timestamp=float(time.time()), device=device, present=not ret)


def define_logging_conf():
    logging.config.dictConfig(LOGGING)


def parse_args(args):
    """
    Parse command line parameters

    :param args: command line parameters as list of strings
    :return: command line parameters as :obj:`argparse.Namespace`
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '-m', '--mac-address',
            dest='mac_address',
            help='MAC address of the spied device', required=True)
    return parser.parse_args(args)


def main(args):
    define_logging_conf()
    args_parsed = parse_args(args)
    mac_address = args_parsed.mac_address

    check_bluetooth_presence(mac_address)


if __name__ == '__main__':
    main(sys.argv[1:])
