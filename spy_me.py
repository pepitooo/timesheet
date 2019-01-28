import argparse
import logging
import logging.config
import sys
import subprocess
import time

from model import Device, Scan


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

    bluetooth_ping_cmd = ['l2ping', mac_address, '-c', '1']
    ret = subprocess.call(bluetooth_ping_cmd, shell=False)

    devices = Device.selectBy(mac_address=mac_address)
    if devices.count():
        device = devices.getOne()
    else:
        device = Device(mac_address=mac_address)
    Scan(timestamp=float(time.time()), device=device, present=not ret)
    if ret == 0:
        logging.debug("Device is present")
    else:
        logging.debug("Device is absent")


if __name__ == '__main__':
    main(sys.argv[1:])
