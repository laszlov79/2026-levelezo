import math
import random
import sqlite3
import csv
import statistics
from datetime import datetime, timedelta

ORADIJ = 400
INGYENES_PERC = 15
TOLTESI_DIJ = 250

AUTO_SZINEK = ["#e74c3c", "#3498db", "#f1c40f", "#9b59b6",
               "#1abc9c", "#e67e22", "#95a5a6", "#2c3e50"]


def vl_parkolasi_dij(perc, oradij=ORADIJ):
    if perc < 0:
        raise ValueError("A parkolási idő nem lehet negatív!")
    if perc <= INGYENES_PERC:
        return 0
    return math.ceil(perc / 60) * oradij


def vl_rendszam_generalas():
    betuk = "ABCDEFGHIJKLMNOPRSTUVZ"
    eleje = "A" + random.choice(betuk)
    kozepe = random.choice(betuk) + random.choice(betuk)
    szam = random.randint(100, 999)
    return f"{eleje} {kozepe}-{szam}"


class VLAuto:
    tipus = "Benzines"

    def __init__(self, rendszam, erkezes, tervezett_perc):
        self.rendszam = rendszam
        self.erkezes = erkezes
        self.tervezett_perc = tervezett_perc
        self.szin = random.choice(AUTO_SZINEK)

    def eltelt_perc(self, most):
        return int((most - self.erkezes).total_seconds() // 60)

    def tavozik_e(self, most):
        return self.eltelt_perc(most) >= self.tervezett_perc

    def dij(self, perc, oradij=ORADIJ):
        return vl_parkolasi_dij(perc, oradij)

    def __str__(self):
        return f"{self.rendszam} ({self.tipus})"


class VLElektromosAuto(VLAuto):
    tipus = "Elektromos"

    def __init__(self, rendszam, erkezes, tervezett_perc):
        super().__init__(rendszam, erkezes, tervezett_perc)
        self.szin = "#2ecc71"

    def dij(self, perc, oradij=ORADIJ):
        alap = super().dij(perc, oradij)
        toltes = math.ceil(perc / 60) * TOLTESI_DIJ
        return alap + toltes


class VLParkolohaz:
    def __init__(self, helyek_szama=20, db_fajl="parkolohaz.db"):
        self.helyek = [None] * helyek_szama
        self.db_fajl = db_fajl
        self.elutasitott = 0
        self.oradij = ORADIJ
        self._adatbazis_letrehozasa()

    def _adatbazis_letrehozasa(self):
        with sqlite3.connect(self.db_fajl) as kapcsolat:
            kapcsolat.execute("""
                CREATE TABLE IF NOT EXISTS parkolasok (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rendszam TEXT,
                    tipus TEXT,
                    erkezes TEXT,
                    tavozas TEXT,
                    perc INTEGER,
                    dij INTEGER
                )""")

    def _mentes(self, auto, tavozas, perc, dij):
        with sqlite3.connect(self.db_fajl) as kapcsolat:
            kapcsolat.execute(
                "INSERT INTO parkolasok "
                "(rendszam, tipus, erkezes, tavozas, perc, dij) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (auto.rendszam, auto.tipus,
                 auto.erkezes.strftime("%Y-%m-%d %H:%M"),
                 tavozas.strftime("%Y-%m-%d %H:%M"), perc, dij))

    def osszes_parkolas(self):
        with sqlite3.connect(self.db_fajl) as kapcsolat:
            kurzor = kapcsolat.execute(
                "SELECT rendszam, tipus, erkezes, tavozas, perc, dij "
                "FROM parkolasok ORDER BY id")
            return kurzor.fetchall()

    def naplo_torlese(self):
        with sqlite3.connect(self.db_fajl) as kapcsolat:
            kapcsolat.execute("DELETE FROM parkolasok")
        self.elutasitott = 0

    def export_csv(self, fajlnev):
        sorok = self.osszes_parkolas()
        with open(fajlnev, "w", newline="", encoding="utf-8") as f:
            iro = csv.writer(f, delimiter=";")
            iro.writerow(["Rendszám", "Típus", "Érkezés",
                          "Távozás", "Perc", "Díj (Ft)"])
            iro.writerows(sorok)
        return len(sorok)

    def szabad_helyek(self):
        return [i for i, a in enumerate(self.helyek) if a is None]

    def foglalt_db(self):
        return len(self.helyek) - len(self.szabad_helyek())

    def beenged(self, auto):
        szabad = self.szabad_helyek()
        if not szabad:
            self.elutasitott += 1
            return None
        hely = random.choice(szabad)
        self.helyek[hely] = auto
        return hely

    def kienged(self, hely, most):
        auto = self.helyek[hely]
        if auto is None:
            raise ValueError("Ezen a helyen nem áll autó!")
        perc = auto.eltelt_perc(most)
        dij = auto.dij(perc, self.oradij)
        self._mentes(auto, most, perc, dij)
        self.helyek[hely] = None
        return auto, perc, dij

    def statisztika(self):
        sorok = self.osszes_parkolas()
        if not sorok:
            return None
        percek = [s[4] for s in sorok]
        dijak = [s[5] for s in sorok]
        orak = [datetime.strptime(s[2], "%Y-%m-%d %H:%M").hour
                for s in sorok]
        return {
            "darab": len(sorok),
            "bevetel": sum(dijak),
            "atlag_perc": statistics.mean(percek),
            "median_perc": statistics.median(percek),
            "szoras_perc": statistics.stdev(percek) if len(percek) > 1 else 0,
            "atlag_dij": statistics.mean(dijak),
            "csucsora": statistics.mode(orak),
            "elektromos": sum(1 for s in sorok if s[1] == "Elektromos"),
        }


def vl_veletlen_auto(most):
    rendszam = vl_rendszam_generalas()
    tervezett = random.choice([10, 30, 45, 60, 90, 120, 180, 240, 480])
    if random.random() < 0.2:
        return VLElektromosAuto(rendszam, most, tervezett)
    return VLAuto(rendszam, most, tervezett)


def vl_erkezesi_esely(ora):
    if 7 <= ora <= 9 or 16 <= ora <= 18:
        return 0.7
    if 10 <= ora <= 15:
        return 0.4
    if 19 <= ora <= 22:
        return 0.2
    return 0.05


def kezdo_ido():
    ma = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
    return ma


LEPES = timedelta(minutes=5)
