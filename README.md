Broadband Modem Stats Logger
============================

There are various programs out there that log useful information from popular
brands of broadband modems but I have not found one for DrayTek modems, in
particular the Vigor 130.
This is a simple Python script that will periodically log into the modem to read
various stats and write them to a log file for later analysis.

How to Use the Logger
=====================
The script runs from the command line.
This means it has to be left running once it has started, your computer cannot
be turned off.

You can use the -h option to see the script options:
```console
$ ./bblogger.py -h
Broadband modem stats logger 0.2.0 alpha.0.
Copyright 2020-2021 Mike Williams. All rights reserved.
Broadband modem stats logger.

usage: bblogger [-h] [-u user] [-p password] [-d hours] [-f] [-o dump|csv] [-t minutes] [modem]

-h  Display this help.
-d  How long to log modem stats (default 24)
-f  Log stats to daily log files
-o  Output format (default dump)
-p  Modem user password (NOT RECOMMENDED)
-t  Time between checks in minutes (default 15)
-u  User id on modem (default admin)
modem Network address.
$
```

The simplest use is to just provide the network address for the modem to start
seeing simple stat reporting:

```console
$ ./bblogger.py 192.168.1.1
Password:

Logging period ends: 2021-03-28 16:33:08

Timestamp: 2021-03-27 16:33
Uptime: 603:23
Reset Times: 0
Link Times: 5
DS Actual: 12515000
DS Attainable: 12768000
DS PSD: 19.9
NE Attenuation: 34
NE SNR Margin: 8
NE Rcvd Cells: 1250290338
NE Xmitted Cells: 63339753
NE CRC Count: 20380
NE ES Count: 11246
US Actual: 1083000
US Attainable: 1080000
US PSD: 12.4
FE Attenuation: 18
FE SNR Margin: 6
FE CRC Count: 0
FE ES Count: 0
^C
$ 
```

If no network address is given for the modem then the script will use the
default IP address of `192.168.1.1`.

The script will prompt you for the password to use with the admin account and
then start reporting the modem stats.
By default it will report the modem stats every 15 minutes for the next 24
hours, it starts off by reporting when logging will end so you know for sure.

The default logging format is in an easy to read but it is not so useful for
analysing stats over a long time.
To help with analysis the logger can generate a csv file of the modem stats that
can be imported into a spreadsheet for processing.
This is done by using the `-o csv` command line option:

```console
$ ./bblogger.py -o csv 192.168.1.1
Password:

Logging period ends: 2021-03-28 16:54:00

Timestamp,Uptime,Reset Times,Link Times,DS Actual,DS Attainable,DS PSD,NE Attenuation,NE SNR Margin,NE Rcvd Cells,NE Xmitted Cells,NE CRC Count,NE ES Count,US Actual,US Attainable,US PSD,FE Attenuation,FE SNR Margin,FE CRC Count,FE ES Count
2021-03-27 16:54:00,603:44,0,5,12515000,12752000,19.9,34,8,1252103783,63395802,20406,11271,1083000,1080000,12.4,18,6,0,0
^C
$ 
```

If you want to log more than 24 hours of stats (using the `-d hours` command
line option) then it is possible to have the script write the modem stats to a
file per day.
Use the `-f` command line option to log the modem stats to daily files.

The plain logging format files use the `.log` extension while the csv logging
format files use the `.csv` extension.
If logging is stopped and started again then the new stats will be appended to
any existing logging file for that day.

If you are using a different account to log into the modem then give the account
name with the `-u` command line option.
If you want to script invoking the logging script you can also provide the
password using the `-p` command line option, although this is not recommended.

INI Configuration File
======================
To avoid having to always type in the logging parameters when repeatedly logging
modem stats you can use the `bblogger.ini` file to capture all the parameters.
The logging parameters for a modem are recorded in named sections of the INI
file.

See the example INI file `bblogger.ini.sample` for the supported section entries
to use for logging.
Multiple entries can be used to support different forms of logging for a modem,
or for logging of multiple modems if required.

The modem name given to the script is used to look for a section in the INI
file,
If there is no matching section name then the given modem name is used as is.
Any command line options override any entries in the INI file section for the
named modem.
