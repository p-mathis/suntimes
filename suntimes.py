from datetime import datetime
from jdcal import gcal2jd, jd2gcal
from math import sin, cos, asin, acos, pi
from tzlocal import get_localzone
import pytz
from pytz import timezone

local_tz = get_localzone() 

def fraction_day_to_hms(f):
    # Renvoie un tuple (heure, minute, seconde, microseconde) à partir d'une fraction de jour (float entre 0 et 1)
    # Return a tuple (hour, minute, second, microsecond) from a fraction of a day (float between 0 and 1)
    hms = f * 24 *3600
    h = hms // 3600
    m = (hms - 3600*h) // 60
    s = hms - 3600*h - 60*m

    return (int(h), int(m), int(s), int(s%1*1000))

def is_leap_year(y):
    # Renvoie True si l'année y est bissextile, False si non bissextile.
    # Return True if year y is leap, False if not.
    if (y % 4 != 0) or((y % 100 == 0) and (y % 400 != 0)):
        return False
    else: 
        return True    

class SunTimes():
    """Un lieu est caractérisé par longitude, latitude, altitude
    -longitude : float compris entre -180 et 180 ; négatif pour les longitudes ouest, positif pour les longitudes est
    -latitude : float compris entre -66.56 et +66.56 ; le calcul n'est valable qu'entre les deux cercles polaires. Positif si nord, négatif si sud
    -altitude : float, en mètres; supérieur ou égal à zéro
    -tz : timezone, par ex 'Europe/Paris'
    La date sera un datetimes rentrée au format (yyyy, mm, jj), l'heure n'important pas. Parx ex : datetime(2020 12 22)
    La liste timezone est disponible sur : https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568

    A place is characterized by longitude, latitude, altitude
    -longitude: float between -180 and 180; negative for west longitudes, positive for east longitudes
    -latitude: float between -66.56 and +66.56; the calculation is only valid between the two polar circles. Positive if north, negative if south
    - altitude: float, in meters; greater than or equal to zero
    -tz: timezone, eg 'Europe / Paris'
    The date will be a datetimes entered in the format (yyyy, mm, dd), the time not important. Eg : datetime(2020 12 22)
    The timezone list is available on : https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568
    """
    def __init__(self, longitude, latitude, altitude=0):
        if not (-180 <= longitude <= 180):
            raise ValueError("longitude must be between -180 and +180")
        if not (-66.56 <= latitude <= 66.56):
            raise ValueError("outside the polar circles ; latitude must be between -66.56 and +66.56")
        if altitude < 0:
            raise ValueError("altitude must be positive")
        self.longitude = longitude
        self.latitude   = latitude
        self.altitude = altitude

    def mean_solar_noon(self, date):

        Jdate = gcal2jd(date.year, date.month, date.day)
        Jdate = Jdate[0] + Jdate[1] + 0.5
        n = Jdate -2451545 + 0.00084
        JJ = n - self.longitude/360
        return JJ

    def solar_mean_anomaly(self, date):
        JJ = self.mean_solar_noon(date)
        M = (357.5291 + 0.98560028 * JJ) % 360
        return M

    def equation_center(self, date):
        M = self.solar_mean_anomaly(date)
        C = 1.9148 * sin(M*pi/180) + 0.02 * sin(2*M*pi/180) + 0.0003 * sin(3*M*pi/180)
        return C

    def ecliptic_longitude(self, date):
        M = self.solar_mean_anomaly(date)
        C = self.equation_center(date)
        le = (M + C + 180 + 102.9372) % 360
        return le

    def solar_transit(self, date):
        JJ = self.mean_solar_noon(date)
        M = self.solar_mean_anomaly(date)
        le = self.ecliptic_longitude(date)
        J_transit = 2451545 + JJ + 0.0053*sin(M*pi/180) - 0.0069*sin(2*le*pi/180)
        return J_transit

    def declination_sun(self, date):
        le = self.ecliptic_longitude(date)
        delta = asin(sin(le*pi/180) * sin(23.44*pi/180))
        return delta

    def hour_angle(self, date):
        elevation = -0.83 - 2.076*(self.altitude**(1/2))/60
        delta = self.declination_sun(date)
        omega0 = acos((sin(elevation*pi/180) - sin(self.latitude*pi/180)*sin(delta))/(cos(self.latitude*pi/180) * cos(delta)))
        return omega0

    def J_rise_set_greg(self, date):
        #renvoie le jour julien (avec l'heure) du lever et du coucher, sous forme de tuple (an, mois, jour, fraction de jour)4
        #return the Julian day (with time) of sunrise and sunset, as a tuple (year, month, day, fraction of day)
        J_transit = self.solar_transit(date)
        omega0 = self.hour_angle(date)
        J_rise = J_transit - (omega0*180/pi)/360
        J_set = J_transit + (omega0*180/pi)/360
        J_rise_greg = jd2gcal(int(J_rise), J_rise - int(J_rise))
        J_set_greg = jd2gcal(int(J_set), J_set - int(J_set))
        return [J_rise_greg, J_set_greg]

    # Renvoient une date au format datetime du jour avec h, mn, s. UTC ou heure locale de l'ordinateur.
    # Return a date in the datetime format of the day with h, mn, s. UTC or local computer time.
    def riseutc(self, date):
        j_day = self.J_rise_set_greg(date)[0]
        hms = fraction_day_to_hms(j_day[3])
        date_hms  = datetime(int(j_day[0]), int(j_day[1]), int(j_day[2]), hms[0], hms[1], hms[2], hms[3])
        return date_hms

    def setutc(self, date):
        j_day = self.J_rise_set_greg(date)[1]
        hms = fraction_day_to_hms(j_day[3])
        date_hms  = datetime(int(j_day[0]), int(j_day[1]), int(j_day[2]), hms[0], hms[1], hms[2], hms[3])
        return date_hms    

    def riselocal(self, date):
        utc_time = self.riseutc(date)
        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_time

    def setlocal(self, date):
        utc_time = self.setutc(date)
        local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_tz)
        return local_time

    # Renvoient les heures, les minutes et les secondes en heure locale de l'ordinateur du lever et du coucher
    # Return the hours, minutes and seconds local computer time for sunrise and sunset
    def hrise(self, date):
        return self.riselocal(date).hour

    def hset(self, date):
        return self.setlocal(date).hour

    def mrise(self, date):
        return self.riselocal(date).minute

    def mset(self, date):
        return self.setlocal(date).minute

    def srise(self, date):
        return self.riselocal(date).second

    def sset(self, date):
        return self.setlocal(date).second
    
    # Renvoie la durée du jour (deltatime ou tuple : h, m, s, millisec, ou verbeux)
    # Returns the duration of the day (deltatime or tuple: h, m, s, millisec, or verbose)
    def durationdelta(self, date):
        sunrise = self.riseutc(date)
        sunset = self.setutc(date)
        return (sunset - sunrise)

    def durationtuple(self, date):
        time = self.durationdelta(date).total_seconds()
        return fraction_day_to_hms(time / 86400)

    def durationverbose(self, date):
        h = self.durationtuple(date)[0]
        m = self.durationtuple(date)[1]
        s = self.durationtuple(date)[2]
        return "{}h {}mn {}s".format(h, m, s)
    
    # Renvoient le lever et coucher d'un lieu en choisissant la timezone.
    # Return sunrise and sunset of a place by choosing the timezone.
    def risewhere(self, date, elsewhere):
        try:
            utc_time = self.riseutc(date)
            else_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))
            return else_time
        except:
            raise ValueError('Vérifiez la timezone / Check the timezone')
    
    def setwhere(self, date, elsewhere):
        try:
            utc_time = self.setutc(date)
            else_time = utc_time.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))
            return else_time   
        except:
            raise ValueError('Vérifiez la timezone / Check the timezone')

class SunFiles():
    def __init__(self, place, year, place_verbose=""):
        # place est une instance de SunTimes() ; place_verbose est le nom verbeux du lieu (par ex : "Paris Notre-Dame").
        # place in an instance of SunTimes() ; place_verbose is the verbose_name of the place (i.e. "Paris Notre-Dame")
        if not isinstance(year, int):
            raise ValueError("l'année doit être un entier / year must be an integer")
        self.place = place        
        self.year = year
        self.place_verbose = place_verbose
    
    def get_days(self):
        # Renvoie le nombre de jours pour chaque mois de l'année year sous forme de liste : [31, 28, 31, 30...]
        # Return nombre of days for each month of the year year as a list : [31, 28, 31, 30...]
        if is_leap_year(self.year):
            return [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        else:
            return [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    
    def get_list_days(self):
        # Renvoie tous les jours de l'année sous forme de liste de tuples du type (yyyy, mm, dd), c'est à dire [(2020,1,1), (2020,1,2)...(2020,12,31)]
        # Return all the days of the year as a liste of tuples format (yyyy, mm, dd), i.e. [(2020,1,1), (2020,1,2)...(2020,12,31)]
        days = self.get_days()
        list_days = []
        for m in range(12):
            for d in range(days[m]):
                day = (self.year, m+1, d+1)
                list_days.append(day)
        return list_days
    
    # Ces fonctions renvoient une liste de datetime(yyyy, mm, dd, h, mn, s, ms) pour les levers et couchers de toute l'année, heure utc, heure de l'ordinateur local
    # These methods return a list of datetime(yyyy, mm, dd, h, mn, s, ms) for sunrise and sunset of all the year, utc time and local computer time.
    def rise_datetime_utc(self):
        days = self.get_list_days()
        table = []
        for d in days:
            date_d = datetime(*d)
            time = self.place.riseutc(date_d)
            table.append(time)
        return table
            
    def set_datetime_utc(self):
        days = self.get_list_days()
        table = []
        for d in days:
            date_d = datetime(*d)
            time = self.place.setutc(date_d)
            table.append(time)
        return table 
    
    def rise_datetime_local(self):
        days = self.rise_datetime_utc()
        table = []
        for d in days:
            time = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
            table.append(time)
        return table
    
    def set_datetime_local(self):
        days = self.rise_datetime_utc()
        table = []
        for d in days:
            time = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
            table.append(time)
        return table
    
    def month_days(self, month):
        #renvoie les jours d'un mois au format datetime(an, mois, jour) ; le mois est un entier entre 1 et 12
        #return the days of the month in format datetime(year, month, day) ; month integer from 1 to 12
        if not isinstance(month, int):
            raise ValueError("le mois doit être un entier / month must be an integer")
        if not (1 <= month <= 12):
            raise ValueError("le mois doit être entre 1 et 12 / month must be >= 1 and <= 12")
        list_days = []
        for d in range(self.get_days()[month -1]):
            day = (self.year, month, d+1)
            list_days.append(day)
        return list_days

    # Ces fonctions renvoient une liste de datetime(yyyy, mm, dd, h, mn, s, ms) pour les levers et couchers d'un mois donné, heure utc, heure de l'ordinateur local, heure elsewhere (si elswhere=None, renvoie l'heure de l'ordinateur local)
    # These methods return a list of datetime(yyyy, mm, dd, h, mn, s, ms) for sunrise and sunset of a given month, utc time, local computer time, time elsewhere (if elsewhere=None, return the local computer time)., elsewhere=None):
    def month_rise_utc(self, month):
        days = self.month_days(month)
        table = []
        for d in days:
            date_d = datetime(*d)
            time = self.place.riseutc(date_d)
            table.append(time)
        return table

    def month_set_utc(self, month):
        days = self.month_days(month)
        table = []
        for d in days:
            date_d = datetime(*d)
            time = self.place.setutc(date_d)
            table.append(time)
        return table

    def month_rise_local(self, month):
        days = self.month_rise_utc(month)
        table = []
        for d in days:
            time = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
            table.append(time)
        return table
    
    def month_set_local(self, month):
        days = self.month_set_utc(month)
        table = []
        for d in days:
            time = d.replace(tzinfo=pytz.utc).astimezone(local_tz)
            table.append(time)
        return table

    def month_rise_where(self, month, elsewhere=None):
        days = self.month_rise_utc(month)
        table = []
        try:
            if elsewhere is None:
                elsewhere = str(local_tz)
            for d in days:
                time = d.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))
                table.append(time)
            return table
        except:
            raise ValueError('Vérifiez la timezone / Check the timezone')
            
    def month_set_where(self, month, elsewhere=None):
        days = self.month_set_utc(month)
        table = []
        try:
            if elsewhere is None:
                elsewhere = str(local_tz)
            for d in days:
                time = d.replace(tzinfo=pytz.utc).astimezone(timezone(elsewhere))
                table.append(time)
            return table
        except:
            raise ValueError('Vérifiez la timezone / Check the timezone')
            
    def get_json(self, elsewhere=None):
        #Renvoie un tableau au format json avec les horaires de lever et coucher pour tous les jours d'une année donnée en un lieu donné
        #Returns a table in json format with the times of rising and setting for all the days of a given year in a given place 
        json = '['
        for m in range(12):
            i = 0
            while i < self.get_days()[m]:
                rise_utc  = self.month_rise_utc(m+1)[i]
                set_utc = self.month_set_utc(m+1)[i]
                rise_local = self.month_rise_local(m+1)[i]
                set_local = self.month_set_local(m+1)[i]
                verbose_rise_utc = '"{} h {} mn {} s"'.format(rise_utc.hour, rise_utc.minute, rise_utc.second)
                verbose_set_utc = '"{} h {} mn {} s"'.format(set_utc.hour, set_utc.minute, set_utc.second)
                verbose_rise_local = '"{} h {} mn {} s"'.format(rise_local.hour, rise_local.minute, rise_local.second)
                verbose_set_local = '"{} h {} mn {} s"'.format(set_local.hour, set_local.minute, set_local.second)
                rise_where = self.month_rise_where(m+1, elsewhere)[i]
                set_where = self.month_set_where(m+1, elsewhere)[i]
                verbose_rise_where = '"{} h {} mn {} s"'.format(rise_where.hour, rise_where.minute, rise_where.second)
                verbose_set_where = '"{} h {} mn {} s"'.format(set_where.hour, set_where.minute, set_where.second)
                json += '{{"month": {}, "day": {}, "hrise_utc": {}, "mrise_utc": {}, "srise_utc": {}, "hset_utc": {}, "mset_utc": {}, "sset_utc": {}, "vrise_utc": {}, "vset_utc": {},"hrise_local": {}, "mrise_local": {}, "srise_local": {}, "hset_local": {}, "mset_local": {}, "sset_local": {}, "vrise_local": {}, "vset_local": {}, "hrise_where":{}, "mrise_where":{}, "srise_where": {}, "hset_where": {}, "mset_where": {}, "sset_where": {}, "vrise_where": {}, "vset_where": {}}},'.format(rise_utc.month, rise_utc.day, rise_utc.hour, rise_utc.minute, rise_utc.second, set_utc.hour, set_utc.minute, set_utc.second, verbose_rise_utc, verbose_set_utc, rise_local.hour, rise_local.minute, rise_local.second, set_local.hour, set_local.minute, set_local.second, verbose_rise_local, verbose_set_local, rise_where.hour, rise_where.minute, rise_where.second, set_where.hour, set_where.minute, set_where.second, verbose_rise_where, verbose_set_where)
                i+=1
        
        json = json[:-1]
        json += ']'
        
        return json

    def register_json(self, path=None, file_name=None, elsewhere=None):
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
        if elsewhere is None:
            elsewhere = str(local_tz)
        file = path + file_name
        json = self.get_json(elsewhere)
        with open(file, "w") as f:
            f.write(json)
        f.close()

    def get_csv(self, elsewhere=None):
        #Renvoie un tableau au format csv avec les horaires de lever et coucher pour tous les jours d'une année donnée en un lieu donné ; séparateur = virgule
        #Returns a table in csv format with the times of rising and setting for all the days of a given year in a given place ; separator = coma
        csv = "month, day, hrise_utc, mrise_utc, srise_utc, hset_utc, mset_utc, sset_utc, vrise_utc, vset_utc, hrise_local, mrise_local, srise_local, hset_local, mset_local, sset_local, vrise_local, vset_local, hrise_where, mrise_where, srise_where, hset_where, mset_where, sset_where, vrise_where, vset_where\n"
        for m in range(12):
            i = 0
            while i < self.get_days()[m]:
                rise_utc  = self.month_rise_utc(m+1)[i]
                set_utc = self.month_set_utc(m+1)[i]
                rise_local = self.month_rise_local(m+1)[i]
                set_local = self.month_set_local(m+1)[i]
                verbose_rise_utc = "{} h {} mn {} s".format(rise_utc.hour, rise_utc.minute, rise_utc.second)
                verbose_set_utc = "{} h {} mn {} s".format(set_utc.hour, set_utc.minute, set_utc.second)
                verbose_rise_local = "{} h {} mn {} s".format(rise_local.hour, rise_local.minute, rise_local.second)
                verbose_set_local = "{} h {} mn {} s".format(set_local.hour, set_local.minute, set_local.second)
                rise_where = self.month_rise_where(m+1, elsewhere)[i]
                set_where = self.month_set_where(m+1, elsewhere)[i]
                verbose_rise_where = "{} h {} mn {} s".format(rise_where.hour, rise_where.minute, rise_where.second)
                verbose_set_where = "{} h {} mn {} s".format(set_where.hour, set_where.minute, set_where.second)
                csv += "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(rise_utc.month, rise_utc.day, rise_utc.hour, rise_utc.minute, rise_utc.second, set_utc.hour, set_utc.minute, set_utc.second, verbose_rise_utc, verbose_set_utc, rise_local.hour, rise_local.minute, rise_local.second, set_local.hour, set_local.minute, set_local.second, verbose_rise_local, verbose_set_local, rise_where.hour, rise_where.minute, rise_where.second, set_where.hour, set_where.minute, set_where.second, verbose_rise_where, verbose_set_where)
                i+=1
        
        return csv

    def register_csv(self, path=None, file_name=None, elsewhere=None):
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
        if elsewhere is None:
            elsewhere = str(local_tz)
        file = path + file_name
        csv = self.get_csv(elsewhere)
        with open(file, "w") as f:
            f.write(csv)
        f.close()    
