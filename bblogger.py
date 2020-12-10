#!/usr/bin/env python

"""Broadband modem stats logger.

usage: bblogger [-h] [-d hours] [-o dump|csv] [-t minutes]

-h  Display this help.
-d  How long to log modem stats (default 24)
-o  Output format (default dump)
-t  Time between checks in minutes (default 15)
"""

import copy
import csv
import datetime
import getopt
import getpass
import os.path
import re
import sys
import telnetlib
import time

# Utility product information
__product__ = 'Broadband modem stats logger'
__copyright__ = 'Copyright 2020 Mike Williams. All rights reserved.'
version_info = (0, 1, 0, 'alpha', 0)
__version__ = '%d.%d.%d' % version_info[:3]
if version_info[3] != 'final':
    __version__ += ' %s.%d' % version_info[3:]

__description__ = '%s %s.\n%s' % (__product__, __version__, __copyright__)

USAGE = re.search('^usage:.*\n\n', __doc__,
                  re.MULTILINE | re.DOTALL).group().strip()


def usage(mesg):
    sys.exit('%s\n%s' % (mesg, USAGE))


class HoursDelta(datetime.timedelta):

    def __str__(self):
        total_seconds = self.total_seconds()
        hours = total_seconds//3600
        minutes = (total_seconds % 3600)//60
        return "%d:%02d" % (hours, minutes)


class TelnetConnection(object):

    def __init__(self):
        self.tn = telnetlib.Telnet()
        self.prompt = ''
        self.account = ''
        self.password = ''

    def set_prompt(self, prompt):
        self.prompt = prompt.encode('ascii')

    def set_login(self, account, password):
        self.account = account.encode('ascii')
        self.password = password.encode('ascii')

    def login(self, host, user, password):
        self.tn.open(host)

        self.tn.read_until(self.account)
        self.tn.write(user.encode('ascii') + b'\n')

        self.tn.read_until(self.password)
        self.tn.write(password.encode('ascii') + b'\n')

        self.tn.read_until(self.prompt)

    def read_command(self, command):
        self.tn.write(command.encode('ascii') + b'\n')
        return self.tn.read_until(self.prompt)

    def exit(self):
        self.tn.write(b"exit\n")
        self.tn.read_all()
        self.tn.close()


class ConnectionStats(object):

    UPTIME = 'Uptime'
    DS_ACTUAL = 'DS Actual'
    DS_ATTAINABLE = 'DS Attainable'
    US_ACTUAL = 'US Actual'
    US_ATTAINABLE = 'US Attainable'
    NE_SNR_MARGIN = 'NE SNR Margin'
    NE_CRC_COUNT = 'NE CRC Count'
    NE_ES_COUNT = 'NE ES Count'
    FE_SNR_MARGIN = 'FE SNR Margin'
    FE_CRC_COUNT = 'FE CRC Count'
    FE_ES_COUNT = 'FE ES Count'
    RESET_TIMES = 'Reset Times'
    LINK_TIMES = 'Link Times'

    ALL_STATS = [
        UPTIME,
        RESET_TIMES,
        LINK_TIMES,
        DS_ACTUAL,
        DS_ATTAINABLE,
        US_ACTUAL,
        US_ATTAINABLE,
        NE_SNR_MARGIN,
        NE_CRC_COUNT,
        NE_ES_COUNT,
        FE_SNR_MARGIN,
        FE_CRC_COUNT,
        FE_ES_COUNT,
    ]

    def __init__(self, modem, reporter):
        self._modem = modem
        self._reporter = reporter
        self._duration = 24 # hours
        self._interval = 15 # minutes

    def set_periods(self, duration, interval):
        self._duration = duration
        self._interval = interval

    def log_stats(self):
        self._reporter.start(ConnectionStats.ALL_STATS)
        endtime = datetime.datetime.now() + \
                datetime.timedelta(hours=self._duration)
        while datetime.datetime.now() < endtime:
            self._modem.read_stats()
            self._reporter.log([self._modem[stat] for stat in
                                ConnectionStats.ALL_STATS])
            time.sleep(self._interval*60)


class BroadBandModem(object):

    def __init__(self):
        self._host = '192.168.1.1'
        self._user = 'admin'
        self._password = 'admin'
        self._stats = {}

    def get_login(self):
        self._host = input("Modem address: ")
        self._user = input("Account: ")
        self._password = getpass.getpass()

    def __getitem__(self, stat):
        return self._stats.get(stat, "Unknown")


class Vigor130Modem(BroadBandModem):

    STATUS_STATS = {
        ConnectionStats.UPTIME:        rb"System Uptime:(\d+):(\d+)"
    }
    ADSL_STATS = {
        ConnectionStats.DS_ACTUAL:     rb"DS Actual Rate +: +(\d+)",
        ConnectionStats.DS_ATTAINABLE: rb"DS Attainable Rate +: +(\d+)",
        ConnectionStats.US_ACTUAL:     rb"US Actual Rate +: +(\d+)",
        ConnectionStats.US_ATTAINABLE: rb"US Attainable Rate +: +(\d+)",
        ConnectionStats.NE_SNR_MARGIN: rb"Cur SNR Margin +: +(\d+)",
        ConnectionStats.NE_CRC_COUNT:  rb"NE CRC Count +: +(\d+)",
        ConnectionStats.NE_ES_COUNT:   rb"NE ES Count +: +(\d+)",
        ConnectionStats.FE_SNR_MARGIN: rb"Far SNR Margin +: +(\d+)",
        ConnectionStats.FE_CRC_COUNT:  rb"FE CRC Count +: +(\d+)",
        ConnectionStats.FE_ES_COUNT:   rb"FE  ES Count +: +(\d+)",
        ConnectionStats.RESET_TIMES:   rb"Xdsl Reset Times +: +(\d+)",
        ConnectionStats.LINK_TIMES:    rb"Xdsl Link  Times +: +(\d+)"
    }

    def __init__(self):
        super(Vigor130Modem, self).__init__()
        self._connection = TelnetConnection()
        self._connection.set_login('Account:', 'Password: ')
        self._connection.set_prompt('> ')

    def read_stats(self):
        self._connection.login(self._host, self._user, self._password)

        status = self._connection.read_command("show status")

        for stat, pattern in Vigor130Modem.STATUS_STATS.items():
            match = re.search(pattern, status)
            if match:
                self._stats[stat] = \
                    HoursDelta(hours=int(match.group(1)),
                               minutes=int(match.group(2)))
            else:
                print("Did not find status: %s" % stat, file=sys.stderr)

        adsl = self._connection.read_command("show adsl")
        for stat, pattern in Vigor130Modem.ADSL_STATS.items():
            match = re.search(pattern, adsl)
            if match:
                self._stats[stat] = int(match.group(1))
            else:
                print("Did not find status: %s" % stat, file=sys.stderr)

        self._connection.exit()


class StatsLogger(object):

    def __init__(self, output):
        self._output = output

    def start(self, fields):
        self._fields = copy.copy(fields)

    def _str_data(self, data):
        return [str(d) for d in data]

    def log_time(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    def log(self, data):
        self._output.write("Timestamp: %s\n" % self.log_time())
        for field, data in zip(self._fields, self._str_data(data)):
            self._output.write("%s: %s\n" % (field, data))
        self._output.flush()


class CSVStatsLogger(StatsLogger):

    def __init__(self, csvfile):
        self._csvfile = csvfile
        self._csv = csv.writer(self._csvfile)

    def start(self, fields):
        self._csv.writerow(["Timestamp"] + fields)

    def log(self, data):
        self._csv.writerow([self.log_time()] + self._str_data(data))
        self._csvfile.flush()


try:
    options, pargs = getopt.getopt(sys.argv[1:], "hd:o:t:")
except getopt.GetoptError as err:
    usage(str(err))

FFORMATS = {
    'dump': StatsLogger,
    'csv': CSVStatsLogger
}

fformat = 'dump'
outfile = sys.stdout
sleeptime = 15
duration = 24

for option, value in options:
    if option == '-h':
        print('%s\n%s' % (__description__, __doc__))
        sys.exit()

    elif option == '-d':
        try:
            duration = int(value)
            if duration < 1:
                raise ValueError
        except ValueError:
            usage("Log duration must be integer value greater than 0.")

    elif option == '-o':
        if value not in FFORMATS:
            usage("Log format is not recognised.")
        fformat = value

    elif option == '-t':
        try:
            sleeptime = int(value)
            if sleeptime < 1:
                raise ValueError
        except ValueError:
            usage("Time between checks must be integer value greater than 0.")

if len(pargs) > 0:
    usage("Unknown arguments given: - %s", " ".join(pargs))

modem = Vigor130Modem()
modem.get_login()

logger = FFORMATS[fformat](outfile)

cs = ConnectionStats(modem, logger)
cs.set_periods(duration, sleeptime)
cs.log_stats()

# eof
