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
