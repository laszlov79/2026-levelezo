Parkolóház-szimulátor

Hallgató: Vajda László
Tantárgy: Szkript nyelvek – Python
Monogram: VL

Feladat leírása

A program egy 20 helyes parkolóház működését szimulálja grafikus felületen.

Az autók véletlenszerűen érkeznek. Az érkezés gyakorisága a napszaktól függ: reggel (7–9 óra) és délután (16–18 óra) csúcsidő van, éjjel alig jön autó.
Minden autó egy véletlen szabad helyre áll be, és egy véletlenszerűen választott tervezett idő után távozik. Ha a ház tele van, az érkező autót a program elküldi, és számolja az elutasított autókat.
Távozáskor a program kiszámolja a parkolási díjat: az első 15 perc ingyenes, utána megkezdett óránként 400 Ft (az óradíj a felületen módosítható). Az elektromos autók (zöldek, ⚡ jellel) megkezdett óránként további 250 Ft töltési díjat fizetnek.
Minden lezárt parkolás SQLite adatbázisba kerül. Az adatokból a program statisztikát készít, CSV fájlba exportálja őket, és a napló törölhető.
A szimulált idő 5 perces lépésekben halad, a sebesség csúszkával állítható.

A program futtatásához nem szükséges semmilyen külső csomag, a program csak a python beépített moduljait használja.
main.py				grafikus felület és eseménykezelés
vl_parkolohaz.py	saját modul: osztályok, függvények, adatbázis, statisztika
requirements.txt	a szükséges csomagok listája (virtuális környezethez)
parkolohaz.db		az első indításkor jön létre (SQLite)

Modulok és a modulokban használt függvények
Tanult modulok
tkinter				Tk(), Canvas, Button, Label, Entry, Scale, Listbox, Frame,
					bind(), after(), after_cancel(), create_rectangle(), create_text()
					→ a grafikus felület és a parkolóház kirajzolása

tkinter.messagebox	showinfo(), showerror(), askyesno()
					→ üzenetek, hibaüzenetek, megerősítés

tkinter.filedialog	asksaveasfilename()
					→ a CSV mentési helyének kiválasztása

random				random(), randint(), choice()
					→ érkezések, rendszámok, autószínek, tervezett parkolási idő

math				ceil()
					→ a megkezdett órák kiszámítása

sqlite3				connect(), execute(), fetchall(), sqlite3.Error
					→ a parkolások mentése és kiolvasása

csv					writer(), writerow(), writerows()
					→ exportálás CSV fájlba
Bemutatandó modul: statistics

A Python beépített statisztikai modulja. A program a VLParkolohaz.statisztika() metódusban az adatbázisból kiolvasott parkolásokra négy függvényét használja:

statistics.mean(lista)		az átlagos parkolási idő és az átlagos díj
statistics.median(lista)	a medián parkolási idő (kevésbé érzékeny a ritka,
							nagyon hosszú parkolásokra, mint az átlag)
statistics.stdev(lista)		a parkolási idők szórása (legalább 2 adat kell hozzá)
statistics.mode(lista)		a leggyakoribb érkezési óra, vagyis a csúcsidő

Példa:

python
import statistics

percek = [30, 45, 60, 60, 240]
print(statistics.mean(percek))    # 87
print(statistics.median(percek))  # 60
print(statistics.mode(percek))    # 60
print(statistics.stdev(percek))   # 86.43...

Kiegészítésként a datetime modul is szerepel: a datetime.now(), timedelta(), strftime() és strptime() kezeli a szimulált órát és az időpontok mentését.

Saját modul: vl_parkolohaz.py
vl_parkolasi_dij(perc, oradij)	kiszámolja a díjat (15 perc ingyenes, utána
								megkezdett óránként); negatív időre ValueError
vl_rendszam_generalas()			véletlen magyar rendszámot ad, pl. AA BC-123
vl_veletlen_auto(most)			véletlen autót hoz létre, 20% eséllyel elektromosat
vl_erkezesi_esely(ora)			egy autó érkezésének esélye az adott órában
kezdo_ido()						a szimuláció kezdő időpontja (aznap 6:00)
Kivételkezelés
Hibás óradíj (betű, nulla vagy negatív szám): ValueError → hibaüzenet, a régi érték marad.
Adatbázishiba mentéskor vagy statisztikánál: sqlite3.Error → hibaüzenet.
Sikertelen fájlmentés: OSError → hibaüzenet.
Osztály(ok)
VLAuto (vl_parkolohaz.py)

Egy parkoló autó.

rendszam, erkezes,		az autó adatai
tervezett_perc, szin
tipus					osztályváltozó, értéke "Benzines"
eltelt_perc(most)		hány perce parkol az autó
tavozik_e(most)			lejárt-e a tervezett parkolási idő
dij(perc, oradij)		a fizetendő díj
__str__()				szöveges megjelenítés, pl. AA BC-123 (Benzines)
VLElektromosAuto(VLAuto) (vl_parkolohaz.py)

Az VLAuto leszármazottja (öröklődés). A konstruktor a super() hívással használja az ősosztályét, és zöldre állítja a színt. A dij() metódust felülírja (többalakúság): az alapdíjhoz hozzáadja a töltési díjat.

VLParkolohaz (vl_parkolohaz.py)

A parkolóház állapota és adatkezelése.

__init__(helyek_szama, db_fajl)	létrehozza a helyeket és az adatbázistáblát
szabad_helyek()					a szabad helyek listája
foglalt_db()					a foglalt helyek száma
beenged(auto)					véletlen szabad helyre teszi az autót; ha tele van, None
kienged(hely, most)				kiengedi az autót, kiszámolja a díjat és elmenti
osszes_parkolas()				az összes mentett parkolás (SELECT + fetchall())
statisztika()					a statistics modullal számolt összesítés
export_csv(fajlnev)				az adatbázis tartalmát CSV fájlba írja
naplo_torlese()					törli a mentett parkolásokat
ParkolohazApp (main.py)

A grafikus felület osztálya: felépíti az ablakot, hozzárendeli az eseménykezelőket, kirajzolja a parkolóházat a Canvas-ra, és az időzítővel lépteti a szimulációt. A logikát a VLParkolohaz osztálytól kéri.