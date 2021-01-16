# SunTimes : longitude, latitude and altitude
Sunrise and sunset time calculation for a location (longitude, latitude, altitude) with python. Also available sunrise and sunset timetable for a whole year as a json or a csv file.
## Project description
This module contains functions to determine the time of sunset and the time of sunrise for a given day in a given location (longitude, latitude and altitude).  
Times are calculated using data from [Wikipedia](https://en.wikipedia.org/wiki/Sunrise_equation).  
The main functions return the times of sunset and sunrise in UTC or in local time. Additional functions return separately the hour, minute and second of sunrise and sunset. A function returns the length of the day. It is possible to obtain the timetables for a place in a different timezone, just by specifying this one.  
The SunFiles class allows you to create and save a json or csv file with the timetables for a whole year.
## Installation
### Required modules
suntimes module requires pytz, tzlocal, jdcal  
```sh
$ pip install pytz
```
```sh
$ pip install tzlocal
```
```sh
$ pip install jdcal
```
### Installation
The module can be installed using pip
```sh
$ pip install suntimes
 ```
## Usage
### Class SunTimes
```python
place = SunTimes(longitude, latitude, altitude=0)
```
A place is characterized by longitude, latitude, altitude
- longitude: float between -180 and 180; negative for west longitudes, positive for east longitudes
- latitude: float between -66.56 and +66.56; the calculation is only valid between the two polar circles. Positive if north, negative if south
- altitude: float, in meters; greater than or equal to zero. Default = 0.
### Methods
Most of mehtods take a date as an argument.  
The date will be a datetime.datetime in the format (yyyy, mm, dd), the time not important. Eg : datetime(2020, 12, 22).  
Methods risewhere and setwhere take timezone as a second argument.  
The timezone list is available on [github](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568).
### Examples
#### Main methods
Import modules. Create an instance.
```python
from datetime import datetime
from suntimes import SunTimes

#date
day = datetime(2021,1,6)
#location Paris Notre-Dame France
sun = SunTimes(2.349902, 48.852968, 35)
```
Return UTC time :  
```python
sun.riseutc(day)
datetime.datetime(2021, 1, 6, 7, 42, 52, 269)
```
```python
sun.setutc(day)
datetime.datetime(2021, 1, 6, 16, 12, 5, 630)
```
Return local computer time : 
```python
sun.riselocal(day)
datetime.datetime(2021, 1, 6, 8, 42, 52, 269, tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>)
```
```python
sun.setlocal(day)
datetime.datetime(2021, 1, 6, 17, 12, 5, 630, tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>)
```
#### Separately hour, minute, second (local computer time)
```python
sun.hrise(day)
8
sun.mrise(day)
42
sun.srise(day)
52
sun.hset(day)
17
sun.mset(day)
12
sun.sset(day)
5
```
#### Duration of the day
Return the length of the day in a datetime.timedelta format, a tuple or a verbose format
```python
sun.durationdelta(day)
datetime.timedelta(seconds=30553, microseconds=361)
sun.durationtuple(day)
(8, 29, 13, 0)
sun.durationverbose(day)
'8h 29mn 13s'
```
#### Suntimes choosing the timezone
Sunrise and sunset in Sao Paulo (Brazil)  
```python
#location Sao Paulo, Brazil
sun = SunTimes(-46.63611, -23.5475, 769)
#sunrise and sunset in Sao Paulo, local computer time (France)
sun.riselocal(day)
datetime.datetime(2021, 1, 6, 9, 23, 20, 849, tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>)
sun.setlocal(day)
datetime.datetime(2021, 1, 6, 23, 3, 37, 361, tzinfo=<DstTzInfo 'Europe/Paris' CET+1:00:00 STD>)
# sunrise and sunset in Sao Paulo, Sao Paulo time
sun.risewhere(day, 'America/Sao_Paulo')
datetime.datetime(2021, 1, 6, 5, 23, 20, 849, tzinfo=<DstTzInfo 'America/Sao_Paulo' -03-1 day, 21:00:00 STD>)
sun.setwhere(day, 'America/Sao_Paulo')
datetime.datetime(2021, 1, 6, 19, 3, 37, 361, tzinfo=<DstTzInfo 'America/Sao_Paulo' -03-1 day, 21:00:00 STD>)
```
#### Influence of altitude
Altitude can have an influence on the result.
For example considering Mount Everst :  
```python
# Mount Everest, altitude = default (zero)
sun_0 = SunTimes(86.9246, 27.9891)
# Mount Everest, altitude = 8848
sun_8848 = SunTimes(86.9246, 27.9891, 8848)
# duration of the day, sun_0 and sun_8848
sun_0.durationverbose(day)
'10h 26mn 33s'
sun_8848.durationverbose(day)
'10h 58mn 54s'  
```
A difference of more than half an hour for the calculation of the length of the day.
## Class SunFiles
file = SunFiles(place, year, place_verbose=""), where place is a SunTimes instance, year the year you choose and place_verbose the verbose name of the place.  
### Instantiation
```python
from suntimes import SunTimes, SunFiles

place = SunTimes(2.349902, 48.852968, 35)
file = SunFiles(place, 2020, "Notre-Dame de Paris")
```
### Methods
#### Get the data
```python
place = SunTimes(2.349902, 48.852968, 35)
file = SunFiles(place, 2020, "Notre-Dame de Paris")
# Get json data : get_json(self, elsewhere = None)
file.get_json()
# Get csv data : get_csv(self, elsewhere = None)
file.get_csv(elsewhere = "America/Sao_Paulo")
```
Return data with:
- month
- day
- hour, minute and second of sunrise and sunset in utc, local computer time and specific timezone. If elswhere not specified, return utc, local computer time, local computer time again.
- schedules in a verbose mode (i.e. 8 h 12 mn 7 s)
#### Create and save the file
The data is calculated and the file created and saved.
```python
register_json(self, path=None, file_name=None, elswhere=None)
register_csv(self, path=None, file_name=None, elswhere=None)
```
The path must be indicated correctly, otherwise an error is raised : "/home/foo/Desktop/" or "C:\Documents\Foo\Exercices\ for exemple.
If file_name is not specified, it is generated automatically. For example : "2020_Notre-Dame_de_Paris_sun_timetable.csv"
```python
file.register_json(path="/home/foo/Desktop/", file_name="2020.json")
file.register_csv(path="/home/foo/Desktop/", elsewhere="America/Sao_Paulo")
```
#### Read the file as a workbook
- CSV file is easy to open on a Excel xlsx or any other workbook.
- JSON file can be converted to xlsx [here](https://codebeautify.org/json-to-excel-converter).