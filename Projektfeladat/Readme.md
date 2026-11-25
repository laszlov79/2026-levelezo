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