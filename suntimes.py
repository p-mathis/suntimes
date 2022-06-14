from datetime import datetime, timedelta
from jdcal import gcal2jd, jd2gcal
from math import sin, cos, asin, acos, pi
from tzlocal import get_localzone
import pytz
from pytz import timezone

local_tz = get_localzone() 

"""Different constants
Différentes constantes apparaissant dans les équations."""
# Equivalent Julian year of Julian days for 2000, 1, 1.5, noon
JULIAN_DAYS_2000 = 2451545.0    

# Fractionnal Julian Day for leap seconds and terrestrial time
JULIAN_DAYS_LEAP = 0.00084 

# Mean Solar Anomaly Constants
MEAN_M0 = 357.5291
MEAN_M1 = 0.98560028

# Equation of Center Constants
CENTER_C0 = 1.9148
CENTER_C1 = 0.0200
CENTER_C2 = 0.0003

# Ecliptic longitude : argument of perihelion
PERIHELION_ARGUMENT = 102.9372

# Equation of time (solar transit)
TIME_0 = 0.0053
TIME_1 = 0.0069

# Earth's maximal tilt toward the sun (degrees)
OBLIQUITY = 23.44

# Hour Angle ; corrections for atmospherical refraction and solar disc diameter (degrees)
# Correction for elevation (altitude : meters ; correction : degrees)
CORRECTION_REFRACTION = -0.833
CORRECTION_ELEVATION = -2.076

# Functions
def fraction_day_to_hms(f):
    # convert a fraction of a day in hours, minutes, seconds
    # convertit une fraction de jour en heures, minutes et secondes
    hms = f * 24 *3600
    h = hms // 3600
    m = (hms - 3600*h) // 60
    s = hms - 3600*h - 60*m
    return (int(h), int(m), int(s), int(s%1*1000))
    
def round_fractionDay_toHM(f):
    # round a fraction of a day into hours and minutes
    #arrondit une fraction de jour en h et mn (arrondi à la minute plus ou moins selon valeur secondes)
    h = int(f*24)
    m = round(f*60*24 - h*60)
    if m < 60:
        h = h
        m = m
    else:
        m = 0
        h = h+1
        if h == 24:
            m = 59
            h = 23
    return (h, m)

def hms_to_fraction_day(h, m, s=0):
    # return fraction of a day (float betwenne 0 and 1) from time of the day
    # Renvoie une fraction de jour (float entre 0 et 1) à partir d'une heure et une minute donnée
    return (h*60*60 + m*60 + s)/(24*60*60)

def is_leap_year(y):
    # Return True if year y is leap, False if not.
    # Renvoie True si l'année y est bissextile, False si non bissextile.
    if (y % 4 != 0) or((y % 100 == 0) and (y % 400 != 0)):
        return False
    else: 
        return True 

def len_year(year):
    # Return number of days of the year year
    # Renvoie le nombre de jours dans l'année year
    if is_leap_year(year):
        return 366
    else:
        return 365  

def length_month(year):
    # Return nombre of days for each month of the year year as a list : [31, 28, 31, 30...]
    # Renvoie le nombre de jours pour chaque mois de l'année year sous forme de liste : [31, 28, 31, 30...]
    if is_leap_year(year):
        return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    else:
        return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def days_year(year):
    # Return a list of all the days of the year : list of tuples (year, month, day)
    # Renvoie la liste de tous les jours de l'année : mois, jour sous forme de liste de tuples (an, mois, jour)
    days = []
    for m in range(12):
        for d in range(length_month(year)[m]):
            day = (year, m+1, d+1)
            days.append(day)
    return days

def seconds_to_hhmm(seconds):
    # return duration of a day (0 <= seconds <= 86400) from seconds to hour and minutes, rounded
    hh = seconds // 3600
    seconds %= 3600
    if seconds % 60 <= 30:
        mm = seconds // 60
    else:
        mm = seconds // 60 +1
    if mm == 60:
        mm = 0
        hh = hh +1 
    if hh >= 24:
        hh = 24
        mm = 0
    return [hh, mm]

def roundTime(dt=None, roundTo=60):
   """Round a datetime object to any time laps in seconds
   dt : datetime.datetime object, default now.
   roundTo : Closest number of seconds to round to, default 1 minute.
   Author: Thierry Husson 2012 - Use it as you want but don't blame me.
   """
   if dt == None : dt = datetime.now()
   seconds = (dt - dt.min).seconds
   rounding = (seconds+roundTo/2) // roundTo * roundTo
   return dt + timedelta(0,rounding-seconds,-dt.microsecond) 


class SunTimes():
    """
    A place is characterized by longitude, latitude, altitude
    -longitude: float between -180 and 180; negative for west longitudes, positive for east longitudes
    -latitude: float between -66.56 and +66.56; the calculation is only valid between the two polar circles. Positive if north, negative if south
    - altitude: float, in meters; greater than or equal to zero
    -tz: timezone, eg 'Europe / Paris'
    The date will be a datetimes entered in the format (yyyy, mm, dd), the time not important. Eg : datetime(2020 12 22)
    The timezone list is available on : https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568

    Un lieu est caractérisé par longitude, latitude, altitude
    -longitude : float compris entre -180 et 180 ; négatif pour les longitudes ouest, positif pour les longitudes est
    -latitude : float compris entre -66.56 et +66.56 ; le calcul n'est valable qu'entre les deux cercles polaires. Positif si nord, négatif si sud
    -altitude : float, en mètres; supérieur ou égal à zéro
    -tz : timezone, par ex 'Europe/Paris'
    La date sera un datetimes rentrée au format (yyyy, mm, jj), l'heure n'important pas. Parx ex : datetime(2020 12 22)
    La liste timezone est disponible sur : https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
    """
    def __init__(self, longitude, latitude, altitude=0):
        if not (-180 <= longitude <= 180):
            raise ValueError("longitude must be between -180 and +180")
        if not (-90  <= latitude <= 90):
            raise ValueError("latitude must be between -90 and +90")
        if not (-66.56 <= latitude <= 66.56):
            print("Au-delà des cercles polaires / Beyond the polar circles ")
        if altitude < 0:
            raise ValueError("altitude must be positive")
        self.longitude = longitude
        self.latitude   = latitude
        self.altitude = altitude

    def mean_solar_noon(self, date):

        
        Jdate = gcal2jd(date.year, date.month, date.day)
        Jdate = Jdate[0] + Jdate[1] + 0.5
        n = Jdate - JULIAN_DAYS_2000 + JULIAN_DAYS_LEAP
        JJ = n - self.longitude/360
        return JJ

    def solar_mean_anomaly(self, date):
        JJ = self.mean_solar_noon(date)
        M = (MEAN_M0 + MEAN_M1 * JJ) % 360
        return M
    
    def equation_center(self, date):
        M = self.solar_mean_anomaly(date)
        C = CENTER_C0 * sin(M*pi/180) + CENTER_C1 * sin(2*M*pi/180) + CENTER_C2 * sin(3*M*pi/180)
        return C
    
    def ecliptic_longitude(self, date):
        M = self.solar_mean_anomaly(date)
        C = self.equation_center(date)
        le = (M + C + 180 + PERIHELION_ARGUMENT) % 360
        return le

    def solar_transit(self, date):
        JJ = self.mean_solar_noon(date)
        M = self.solar_mean_anomaly(date)
        le = self.ecliptic_longitude(date)
        J_transit = JULIAN_DAYS_2000 + JJ + TIME_0*sin(M*pi/180) - TIME_1*sin(2*le*pi/180)
        return J_transit

    def declination_sun(self, date):
        le = self.ecliptic_longitude(date)
        delta = asin(sin(le*pi/180) * sin(OBLIQUITY*pi/180))
        return delta

    def getOmega0(self, date):
        elevation = CORRECTION_REFRACTION + CORRECTION_ELEVATION*(self.altitude**(1/2))/60
        delta = self.declination_sun(date)
        cosOmega0 = (sin(elevation*pi/180) - sin(self.latitude*pi/180)*sin(delta))/(cos(self.latitude*pi/180) * cos(delta))
        return cosOmega0

    def hour_angle(self, date):
        # Return Omega0 angle if cosOmega0 between -1 and 1 ; otherwise return string Polar Night or Polar Day (PN, PD)
        # Renvoie l'angle Omega0 si cosOmega0 est compris entre -1 et 1 ; sinon renvoie un string Nuit Polaire ou Jour Polaire (PN, PD)
        cosOmega0 = self.getOmega0(date)
        if abs(cosOmega0) <= 1:
            return acos(cosOmega0)
        elif  cosOmega0 >1:
            return "PN"
        else:
            return "PD"

    def J_rise_set_greg(self, date):
        # Return julian day (with hour) of sunrise and sunset : tuple (year, month, day, fraction of the day)
        # Renvoie le jour julien (avec l'heure) du lever et du coucher, sous forme de tuple (an, mois, jour, fraction de jour)
        J_transit = self.solar_transit(date)
        omega0 = self.hour_angle(date)
        if not isinstance(omega0, str):
            J_rise = J_transit - (omega0*180/pi)/360
            J_set = J_transit + (omega0*180/pi)/360
            J_rise_greg = jd2gcal(int(J_rise), J_rise - int(J_rise))
            J_set_greg = jd2gcal(int(J_set), J_set - int(J_set))
            return [J_rise_greg, J_set_greg]
        else:
            # on renvoie un string, qui contient l'année, le mois, le jour et la qualité du polaire (jour ou nuit)  et pourra être transformé en liste par split("-")
            #return "{}-{}-{}-{}".format(date.year, date.month, date.day, omega0)
            # Renvoie une liste avec en [0] un datetime et en [1] un string
            # Return a list with datetime as first element and string as second
            return [date, omega0]
        
    # Return a date in the datetime format of the day with h, mn. UTC or local computer time. Minutes are rounded up or down, depending of the seconds. The seconds are not given: the precision of the calculations being beyond the minute. Seconds are zero in the datetime.
    # Renvoient une date au format datetime du jour avec h, mn. UTC ou heure locale de l'ordinateur. Les minutes sont arrondies à la minute sup ou inf selon les valeurs des secondes. Les secondes ne sont pas affichées : la précision des calculs rend inutile leur calcul. Les secondes sont donc à zéro dans la date time.
    def riseutc(self, date):
        j_greg = self.J_rise_set_greg(date)
        j_day = self.J_rise_set_greg(date)[0]
        if not isinstance(j_greg[-1], str):
            hms = round_fractionDay_toHM(j_day[3])
            date_hms  = datetime(int(j_day[0]), int(j_day[1]), int(j_day[2]), hms[0], hms[1])
            return date_hms
        else:
            return j_greg[-1]

    def setutc(self, date):
        j_greg = self.J_rise_set_greg(date)
        j_day = self.J_rise_set_greg(date)[1]
        if not isinstance(j_greg[-1], str):
            hms = round_fractionDay_toHM(j_day[3])
            date_hms  = datetime(int(j_day[0]), int(j_day[1]), int(j_day[2]), hms[0], hms[1])
            return date_hms
        else:
            return j_greg[-1]

    def riselocal(self, date):
        utc_time = self.riseutc(date)
        if not isinstance(utc_time, str):
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return local_time
        else:
            return utc_time

    def setlocal(self, date):
        utc_time = self.setutc(date)
        if not isinstance(utc_time, str):
            local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return local_time
        else:
            return utc_time

    # Return the hours, minutes local computer time for sunrise and sunset
    # Renvoient les heures, les minutes en heure locale de l'ordinateur du lever et du coucher
    def hrise(self, date):
        my_date = self.riselocal(date)
        if not isinstance(my_date, str):
            return my_date.hour
        else:
            return my_date

    def hset(self, date):
        my_date = self.setlocal(date)
        if not isinstance(my_date, str):
            return my_date.hour
        else:
            return my_date

    def mrise(self, date):
        my_date = self.riselocal(date)
        if not isinstance(my_date, str):
            return my_date.minute
        else:
            return my_date

    def mset(self, date):
        my_date = self.setlocal(date)
        if not isinstance(my_date, str):
            return my_date.minute
        else:
            return my_date

    # Renvoie la durée du jour (deltatime ou tuple : h, m ou verbeux)
    # Returns the duration of the day (deltatime or tuple: h, m or verbose)
    def durationdelta(self, date):
        sunrise = self.riseutc(date)
        sunset = self.setutc(date)
        if not isinstance(sunrise, str) and not isinstance(sunset, str):

            return (sunset - sunrise)
        elif isinstance(sunrise, str) and isinstance(sunset, str):
            return f'Not calculable : {sunrise}'
        else:
            return f'Not calculable : changement jour/nuit polaire'

    def durationtuple(self, date):
        delta = self.durationdelta(date)
        if not isinstance(delta, str):
            time = self.durationdelta(date).total_seconds()
            return round_fractionDay_toHM(time / 86400)
        else:
            return delta

    def durationverbose(self, date):
        delta = self.durationtuple(date)
        if not isinstance(delta, str):
            h = delta[0]
            m = delta[1]
            return "{}h {}mn".format(h, m)
        else:
            return delta
    
    # Return sunrise and sunset of a place by choosing the timezone.
    # Renvoient le lever et coucher d'un lieu en choisissant la timezone.
    def risewhere(self, date, elsewhere):
        utc_time = self.riseutc(date)
        if not isinstance(utc_time, str):
            else_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))
            return else_time
        else:
            return utc_time
    
    def setwhere(self, date, elsewhere):
        utc_time = self.setutc(date)

        if not isinstance(utc_time, str):
            else_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))
            return else_time
        else:
            return utc_time


class SunFiles():
    def __init__(self, place, year, place_verbose=""):
        # place in an instance of SunTimes() ; place_verbose is the verbose_name of the place (i.e. "Paris Notre-Dame")
        # place est une instance de SunTimes() ; place_verbose est le nom verbeux du lieu (par ex : "Paris Notre-Dame").
        if not isinstance(year, int):
            raise ValueError("l'année doit être un entier / year must be an integer")
        self.place = place
        self.year = year
        self.place_verbose = place_verbose

    # These methods return a list of datetime(yyyy, mm, dd, h, mn) for sunrise and sunset of all the year, utc time and local computer time.
    # Ces fonctions renvoient une liste de datetime(yyyy, mm, dd, h, mn) pour les levers et couchers de toute l'année, heure utc, heure de l'ordinateur local
    def rise_days_year_utc(self):
        days = days_year(self.year)
        table = []
        for d in days:
            date_d = datetime(*d)
            time = self.place.riseutc(date_d)
            # print("type time : ", time, type(time))
            table.append(time)
        return table
            
    def set_days_year_utc(self):
        days = days_year(self.year)
        table = []
        for d in days:
            date_d = datetime(*d)
            time = self.place.setutc(date_d)
            table.append(time)
        return table 
    
    def rise_days_year_local(self):
        days = self.rise_days_year_utc()
        table = []
        for d in days:
            if not isinstance(d, str):
                time = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
            else:
                time = d
            table.append(time)
        return table
    
    def set_days_year_local(self):
        days = self.set_days_year_utc()
        table = []
        for d in days:
            if not isinstance(d, str):
                time = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
            else:
                time = d
            table.append(time)
        return table    

    def rise_days_year_elsewhere(self, elsewhere=None):
        days = self.rise_days_year_utc()
        table = []
        if elsewhere is None:
            elsewhere = str(local_tz)
        for d in days:
            if not isinstance(d, str):
                time = d.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))
                # print("time elsewhere : ", time, type(time))
            else:
                time = d
            table.append(time)
        return table

    def set_days_year_elsewhere(self, elsewhere=None):
        days = self.set_days_year_utc()
        table = []
        if elsewhere is None:
            elsewhere = str(local_tz)
        for d in days:
            if not isinstance(d, str):
                time = d.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))

            else:
                time = d
            table.append(time)
        return table

    # Renvoie les levers et couchers de soleil sous forme de fraction de jour, heure utc
    # Renvoie 0 si jour ou nuit polaire
    def rise_days_year_fraction_utc(self):
        days = days_year(self.year)
        table = []
        for d in days:
            date_d = datetime(*d)
            try:
                time = self.place.J_rise_set_greg(date_d)[0][3]
            except:
                time = 0
            table.append(time)
        return table

    def set_days_year_fraction_utc(self):
        days = days_year(self.year)
        table = []
        for d in days:
            date_d = datetime(*d)
            try:
                time = self.place.J_rise_set_greg(date_d)[1][3]
            except:
                time = 0
            table.append(time)
        return table    

    def get_json(self, elsewhere=None):
        #Renvoie un tableau au format json avec les horaires de lever et coucher pour tous les jours d'une année donnée en un lieu donné
        #Returns a table in json format with the times of rising and setting for all the days of a given year in a given place 

        bracketOpen = '{'
        bracketClose = '}'
        coma = '"'

        json = '['

        rise_U = self.rise_days_year_utc()
        set_U = self.set_days_year_utc()
        rise_L = self.rise_days_year_local()
        set_L = self.set_days_year_local()
        rise_W = self.rise_days_year_elsewhere(elsewhere)
        set_W = self.set_days_year_elsewhere(elsewhere)

        tuples = days_year(self.year)
        
        for i in range(len(tuples)):

            Mrise_utc = tuples[i][1]
            Drise_utc = tuples[i][2]

            hrise_utc = f'{coma}{rise_U[i]}{coma}' if isinstance(rise_U[i], str) else rise_U[i].hour
            mrise_utc = f'{coma}{rise_U[i]}{coma}' if isinstance(rise_U[i], str) else rise_U[i].minute
            hset_utc = f'{coma}{set_U[i]}{coma}' if isinstance(set_U[i], str) else set_U[i].hour
            mset_utc = f'{coma}{set_U[i]}{coma}' if isinstance(set_U[i], str) else set_U[i].minute

            hrise_local = f'{coma}{rise_L[i]}{coma}' if isinstance(rise_L[i], str) else rise_L[i].hour
            mrise_local = f'{coma}{rise_L[i]}{coma}' if isinstance(rise_L[i], str) else rise_L[i].minute
            hset_local = f'{coma}{set_L[i]}{coma}' if isinstance(set_L[i], str) else set_L[i].hour
            mset_local = f'{coma}{set_L[i]}{coma}' if isinstance(set_L[i], str) else set_L[i].minute

            verbose_rise_utc = f'{coma}{rise_U[i]}{coma}' if isinstance(rise_U[i], str) else f'{coma}{hrise_utc} h {mrise_utc} mn{coma}'
            verbose_set_utc = f'{coma}{set_U[i]}{coma}' if isinstance(set_U[i], str) else f'{coma}{hset_utc} h {mset_utc} mn{coma}'
            verbose_rise_local = f'{coma}{rise_L[i]}{coma}' if isinstance(rise_L[i], str) else f'{coma}{hrise_local} h {mrise_local} mn{coma}'
            verbose_set_local = f'{coma}{set_L[i]}{coma}' if isinstance(set_L[i], str) else f'{coma}{hset_local} h {mset_local} mn{coma}'

            hrise_where = f'{coma}{rise_W[i]}{coma}' if isinstance(rise_W[i], str) else rise_W[i].hour
            mrise_where = f'{coma}{rise_W[i]}{coma}' if isinstance(rise_W[i], str) else rise_W[i].minute
            hset_where = f'{coma}{set_W[i]}{coma}' if isinstance(set_W[i], str) else set_W[i].hour
            mset_where = f'{coma}{set_W[i]}{coma}' if isinstance(set_W[i], str) else set_W[i].minute
            verbose_rise_where = f'{coma}{rise_W[i]}{coma}' if isinstance(rise_W[i], str) else f'{coma}{hrise_where} h {mrise_where} mn{coma}'
            verbose_set_where = f'{coma}{set_W[i]}{coma}' if isinstance(set_W[i], str) else f'{coma}{hset_where} h {mset_where} mn{coma}'

            if hrise_utc == '"PN"' or hset_utc == '"PN':
                duration = "not calculable - Polar Night"
            elif hrise_utc == '"PD"' or hset_utc == '"PD"':
                duration = "not calculable - Polar Day"
            else:
                duration = f'{coma}{fraction_day_to_hms((set_U[i] - rise_U[i]).seconds/86400)[0]} h {fraction_day_to_hms((set_U[i] - rise_U[i]).seconds/86400)[1]} mn{coma}'

            json += f'{bracketOpen}"month": {Mrise_utc}, "day": {Drise_utc}, "hrise_utc": {hrise_utc}, "mrise_utc": {mrise_utc}, "hset_utc": {hset_utc}, "mset_utc": {mset_utc}, "verbose_rise_utc": {verbose_rise_utc}, "verbose_set_utc": {verbose_set_utc}, "duration": {duration}, "hrise_local": {hrise_local}, "mrise_local": {mrise_local}, "hset_local": {hset_local}, "mset_local": {mset_local}, "verbose_rise_local": {verbose_rise_local}, "verbose_set_local": {verbose_set_local}, "hrise_where": {hrise_where}, "mrise_where": {mrise_where}, "hset_where": {hset_where}, "mset_where": {mset_where}, "verbose_rise_where": {verbose_rise_where}, "verbose_set_where": {verbose_set_where}{bracketClose},'
        
        json = json[:-1]
        json += ']'
        return json

    def register_json(self, path=None, file_name=None):
        #Copie et enregistre le tableau json dans un fichier
        #Copy and register json table as a file
        if path is None:
            raise ValueError("Entrez un chemin pour le fichier / Give the path for the file")
        if not (path.endswith("/") or path.endswith("\\")):
            raise ValueError("Vérifiez le chemin : doit inclure / ou \ en fin de nom - Check the path: must include / or \ at the end of the name")            
        self.place_verbose = self.place_verbose.replace(" ", "_")
        self.place_verbose = self.place_verbose.replace("'", "-")
        if file_name is None:
            file_name = "{}_{}_sun_timetable.json".format(self.year, self.place_verbose)
        file = path + file_name
        json = self.get_json()
        with open(file, "w") as f:
            f.write(json)
        f.close()
        print("1 file : {}".format(file))

    def get_csv(self, elsewhere=None):
        #Renvoie un tableau au format csv avec les horaires de lever et coucher pour tous les jours d'une année donnée en un lieu donné ; séparateur = virgule
        #Returns a table in csv format with the times of rising and setting for all the days of a given year in a given place ; separator = coma
        csv = "month, day, hrise_utc, mrise_utc, hset_utc, mset_utc, vrise_utc, vset_utc, duration_day, hrise_local, mrise_local, hset_local, mset_local, vrise_local, vset_local, hrise_where, mrise_where, hset_where, mset_where, vrise_where, vset_where\n"

        bracketOpen = '{'
        bracketClose = '}'
        coma = '"'

        rise_U = self.rise_days_year_utc()
        set_U = self.set_days_year_utc()
        rise_L = self.rise_days_year_local()
        set_L = self.set_days_year_local()
        rise_W = self.rise_days_year_elsewhere(elsewhere)
        set_W = self.set_days_year_elsewhere(elsewhere)
        
        tuples = days_year(self.year)

        for i in range(len(tuples)):

            Mrise_utc = tuples[i][1]
            Drise_utc = tuples[i][2]

            hrise_utc = f'{coma}{rise_U[i]}{coma}' if isinstance(rise_U[i], str) else rise_U[i].hour
            mrise_utc = f'{coma}{rise_U[i]}{coma}' if isinstance(rise_U[i], str) else rise_U[i].minute
            hset_utc = f'{coma}{set_U[i]}{coma}' if isinstance(set_U[i], str) else set_U[i].hour
            mset_utc = f'{coma}{set_U[i]}{coma}' if isinstance(set_U[i], str) else set_U[i].minute

            hrise_local = f'{coma}{rise_L[i]}{coma}' if isinstance(rise_L[i], str) else rise_L[i].hour
            mrise_local = f'{coma}{rise_L[i]}{coma}' if isinstance(rise_L[i], str) else rise_L[i].minute
            hset_local = f'{coma}{set_L[i]}{coma}' if isinstance(set_L[i], str) else set_L[i].hour
            mset_local = f'{coma}{set_L[i]}{coma}' if isinstance(set_L[i], str) else set_L[i].minute

            verbose_rise_utc = f'{coma}{rise_U[i]}{coma}' if isinstance(rise_U[i], str) else f'{coma}{hrise_utc} h {mrise_utc} mn{coma}'
            verbose_set_utc = f'{coma}{set_U[i]}{coma}' if isinstance(set_U[i], str) else f'{coma}{hset_utc} h {mset_utc} mn{coma}'
            verbose_rise_local = f'{coma}{rise_L[i]}{coma}' if isinstance(rise_L[i], str) else f'{coma}{hrise_local} h {mrise_local} mn{coma}'
            verbose_set_local = f'{coma}{set_L[i]}{coma}' if isinstance(set_L[i], str) else f'{coma}{hset_local} h {mset_local} mn{coma}'

            hrise_where = f'{coma}{rise_W[i]}{coma}' if isinstance(rise_W[i], str) else rise_W[i].hour
            mrise_where = f'{coma}{rise_W[i]}{coma}' if isinstance(rise_W[i], str) else rise_W[i].minute
            hset_where = f'{coma}{set_W[i]}{coma}' if isinstance(set_W[i], str) else set_W[i].hour
            mset_where = f'{coma}{set_W[i]}{coma}' if isinstance(set_W[i], str) else set_W[i].minute
            verbose_rise_where = f'{coma}{rise_W[i]}{coma}' if isinstance(rise_W[i], str) else f'{coma}{hrise_where} h {mrise_where} mn{coma}'
            verbose_set_where = f'{coma}{set_W[i]}{coma}' if isinstance(set_W[i], str) else f'{coma}{hset_where} h {mset_where} mn{coma}'

            if hrise_utc == '"PN"' or hset_utc == '"PN':
                duration = "not calculable - Polar Night"
            elif hrise_utc == '"PD"' or hset_utc == '"PD"':
                duration = "not calculable - Polar Day"
            else:
                duration = f'{coma}{fraction_day_to_hms((set_U[i] - rise_U[i]).seconds/86400)[0]} h {fraction_day_to_hms((set_U[i] - rise_U[i]).seconds/86400)[1]} mn{coma}'

            csv += f'{Mrise_utc}, {Drise_utc}, {hrise_utc}, {mrise_utc}, {hset_utc}, {mset_utc}, {verbose_rise_utc}, {verbose_set_utc}, {duration}, {hrise_local}, { mrise_local}, {hset_local}, {mset_local}, {verbose_rise_local}, {verbose_set_local}, {hrise_where}, {mrise_where}, {hset_where}, {mset_where}, {verbose_rise_where}, {verbose_set_where}\n'
            
        return csv

    def register_csv(self, path=None, file_name=None):
        #Copie et enregistre le tableau json dans un fichier
        #Copy and register json table as a file
        if path is None:
            raise ValueError("Entrez un chemin pour le fichier / Give the path for the file")
        if not (path.endswith("/") or path.endswith("\\")):
            raise ValueError("Vérifiez le chemin : doit inclure / ou \ en fin de nom - Check the path: must include / or \ at the end of the name")       
        self.place_verbose = self.place_verbose.replace(" ", "_")
        self.place_verbose = self.place_verbose.replace("'", "-")
        if file_name is None:
            file_name = "{}_{}_sun_timetable.csv".format(self.year, self.place_verbose)
        file = path + file_name
        csv = self.get_csv()
        with open(file, "w") as f:
            f.write(csv)
        f.close()
        print("1 file : {}".format(file))


    def duration_days_year(self):
        # renvoie une suite de liste comprenant : année, mois, jour,et soit une liste avec [h, m] correspondant à la durée du jour heure et minute, soit un string de type "PN" ou "PD" ou "Changement Polaire" (si on est dans le cas où c'est un jour avec lever de soleil mais pas de coucher ou coucher mais sans lever)
        rise_U = self.rise_days_year_utc()
        set_U = self.set_days_year_utc() 

        tuples = days_year(self.year)
        duration_days = []

        for i in range(len(tuples)):

            M_utc = tuples[i][1]
            D_utc = tuples[i][2]

            if isinstance(rise_U[i], str):
                duration = [self.year, M_utc, D_utc, rise_U[i]]
            elif isinstance(set_U[i], str):
                duration = [self.year, M_utc, D_utc, set_U[i]]
            else:
                seconds = (set_U[i] - rise_U[i]).seconds
                hhmm = seconds_to_hhmm(seconds)
                duration = [self.year, M_utc, D_utc, hhmm[0], hhmm[1]]
            duration_days.append(duration)
            
        return duration_days    

    def PDPN_length(self):
        #returns the duration of the polar night and the duration of the polar day for a given year as a tuple: (duration of the polar day in 24-hour daytime, duration of the polar night in 24-hour daytime)
        # renvoie la durée de la nuit polaire et la durée du jour polaire pour une année donnée sous forme de tuple (durée du jour polaire en nycthémère, durée de la nuit polaire en nycthémère)
        duration_days = self.duration_days_year()
        listPN = [d for d in duration_days if 'PN' in d]
        listPD = [d for d in duration_days if 'PD' in d]
        durationPN = len(listPN)
        durationPD = len(listPD)
        return (durationPN, durationPD)

    def PDPN_dates(self):
        PDPN_list = self.duration_days_year()
        PN_index = []
        PD_index = []
        for i in range(len(PDPN_list)):
            if i == 0:
                if "PD" in PDPN_list[i]:
                    PD_index.append(i)
                else:
                    pass
            elif 0 < i < len(PDPN_list) -1:
                if "PD" in PDPN_list[i] and not "PD" in PDPN_list[i+1]:
                    PD_index.append(i)
                elif "PD" in PDPN_list[i] and not "PD" in PDPN_list[i-1]:
                    PD_index.append(i)
                else:
                    pass
            else:
                if "PD" in PDPN_list[i]:
                    PD_index.append(i)
                else:
                    pass

        for i in range(len(PDPN_list)):
            if i == 0:
                if "PN" in PDPN_list[i]:
                    PN_index.append(i)
                else:
                    pass
            elif 0 < i < len(PDPN_list) -1:
                if "PN" in PDPN_list[i] and not "PN" in PDPN_list[i+1]:
                    PN_index.append(i)
                elif "PN" in PDPN_list[i] and not "PN" in PDPN_list[i-1]:
                    PN_index.append(i)
                else:
                    pass
            else:
                if "PN" in PDPN_list[i]:
                    PN_index.append(i)
                else:
                    pass
        
        if len(PN_index) == 0:
            PN_begin = "No Polar Night"
            PN_end = "No Polar Night"
        elif len(PN_index) == 2:
            PN_begin_month = PDPN_list[PN_index[0]][1]
            PN_begin_day = PDPN_list[PN_index[0]][2]
            PN_end_month = PDPN_list[PN_index[1]][1]
            PN_end_day = PDPN_list[PN_index[1]][2]
            PN_begin = ( PN_begin_month,PN_begin_day)
            PN_end = ( PN_end_month,PN_end_day)
        elif  len(PN_index) == 4:
            PN_begin_month = PDPN_list[PN_index[2]][1]
            PN_begin_day = PDPN_list[PN_index[2]][2]
            PN_end_month = PDPN_list[PN_index[1]][1]
            PN_end_day = PDPN_list[PN_index[1]][2]
            PN_begin = ( PN_begin_month,PN_begin_day)
            PN_end = ( PN_end_month,PN_end_day)
        else:
            pass

        if len(PD_index) == 0:
            PD_begin = "No Polar Day"
            PD_end = "No Polar Day"
        elif len(PD_index) == 2:
            PD_begin_month = PDPN_list[PD_index[0]][1]
            PD_begin_day = PDPN_list[PD_index[0]][2]
            PD_end_month = PDPN_list[PD_index[1]][1]
            PD_end_day = PDPN_list[PD_index[1]][2]
            PD_begin = ( PD_begin_month,PD_begin_day)
            PD_end = ( PD_end_month,PD_end_day)
        elif  len(PD_index) == 4:
            PD_begin_month = PDPN_list[PD_index[2]][1]
            PD_begin_day = PDPN_list[PD_index[2]][2]
            PD_end_month = PDPN_list[PD_index[1]][1]
            PD_end_day = PDPN_list[PD_index[1]][2]
            PD_begin = ( PD_begin_month,PDN_begin_day)
            PD_end = ( PD_end_month,PD_end_day)
        else:
            pass

        return [PD_begin, PD_end, PN_begin, PN_end]
