import ephem, math
from datetime import datetime, timedelta

TITHI_NAMES = [
    'Prathama','Dvitiya','Tritiya','Chaturthi','Panchami',
    'Shashthi','Saptami','Ashtami','Navami','Dashami',
    'Ekadashi','Dvadashi','Trayodashi','Chaturdashi','Purnima'
]

def get_tithi_at(year, month, day, ist_hour=6):
    utc_dt = datetime(year, month, day, ist_hour) - timedelta(hours=5.5)
    moon = ephem.Moon(); sun = ephem.Sun()
    obs  = ephem.Observer()
    obs.date = utc_dt.strftime('%Y/%m/%d %H:%M:%S')
    moon.compute(obs); sun.compute(obs)
    elong = (math.degrees(moon.hlong) - math.degrees(sun.hlong)) % 360
    n = int(elong / 12)
    paksha = 'Shukla' if n < 15 else 'Krishna(Bahula)'
    name   = TITHI_NAMES[n % 15]
    return paksha, name, n + 1, elong

print("Date        Day  Paksha              Tithi            Elong")
print("-" * 68)
d = datetime(1997, 1, 1)
while d <= datetime(1997, 3, 31):
    paksha, name, num, elong = get_tithi_at(d.year, d.month, d.day)
    note = ""
    if name == "Ekadashi":
        note = "  <<< EKADASHI"
    if name == "Purnima" and "Shukla" in paksha:
        note = "  [PURNIMA]"
    print("%s %s  %-20s %-16s %6.1f%s" % (
        d.strftime("%Y-%m-%d"), d.strftime("%a"), paksha, name, elong, note))
    d += timedelta(days=1)
