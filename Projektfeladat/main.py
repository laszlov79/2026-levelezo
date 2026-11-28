import random
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog

from vl_parkolohaz import (VLParkolohaz, vl_veletlen_auto, vl_erkezesi_esely,
                           kezdo_ido, LEPES, INGYENES_PERC)

OSZLOPOK = 5
SOROK = 4
HELY_SZ = 120
HELY_M = 80
MARGO = 20
SAV = 40


class ParkolohazApp:
    def __init__(self, ablak):
        self.ablak = ablak
        self.ablak.title("Parkolóház-szimulátor")
        self.ablak.resizable(False, False)

        self.haz = VLParkolohaz(helyek_szama=OSZLOPOK * SOROK)
        self.ido = kezdo_ido()
        self.fut = False
        self.idozito = None
        self.mai_bevetel = 0

        self._felulet_felepitese()
        self._esemenyek_kotese()
        self.rajzol()

    def _felulet_felepitese(self):
        szel = MARGO * 2 + OSZLOPOK * HELY_SZ
        mag = MARGO * 2 + SOROK * HELY_M + (SOROK // 2) * SAV + 30
        self.vaszon = tk.Canvas(self.ablak, width=szel, height=mag,
                                bg="#555b63", highlightthickness=0)
        self.vaszon.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        panel = tk.Frame(self.ablak)
        panel.grid(row=0, column=1, sticky="n", padx=10, pady=10)

        self.ora_cimke = tk.Label(panel, font=("Consolas", 28, "bold"))
        self.ora_cimke.pack(pady=(0, 5))

        self.info_cimke = tk.Label(panel, font=("Arial", 11),
                                   justify="left")
        self.info_cimke.pack(anchor="w", pady=5)

        self.inditas_gomb = tk.Button(panel, text="▶ Indítás", width=22,
                                      command=self.inditas_szunet)
        self.inditas_gomb.pack(pady=3)

        tk.Label(panel, text="Sebesség:").pack(anchor="w")
        self.sebesseg = tk.Scale(panel, from_=1, to=10,
                                 orient="horizontal", length=180)
        self.sebesseg.set(5)
        self.sebesseg.pack()

        dij_keret = tk.Frame(panel)
        dij_keret.pack(pady=5)
        tk.Label(dij_keret, text="Óradíj (Ft):").pack(side="left")
        self.dij_mezo = tk.Entry(dij_keret, width=7)
        self.dij_mezo.insert(0, str(self.haz.oradij))
        self.dij_mezo.pack(side="left", padx=3)
        tk.Button(dij_keret, text="Beállít",
                  command=self.oradij_beallitas).pack(side="left")

        tk.Button(panel, text="📊 Statisztika", width=22,
                  command=self.statisztika).pack(pady=3)
        tk.Button(panel, text="💾 Export CSV-be", width=22,
                  command=self.export).pack(pady=3)
        tk.Button(panel, text="🗑 Napló törlése", width=22,
                  command=self.naplo_torlese).pack(pady=3)

        tk.Label(panel, text="Események:").pack(anchor="w", pady=(10, 0))
        self.naplo = tk.Listbox(panel, width=38, height=12)
        self.naplo.pack()

        self.allapot = tk.Label(self.ablak, anchor="w", relief="sunken",
                                text="Vidd az egeret egy autó fölé, "
                                     "kattintással kiengedheted.")
        self.allapot.grid(row=2, column=0, columnspan=2, sticky="we")

    def _esemenyek_kotese(self):
        self.vaszon.bind("<Button-1>", self.kattintas)
        self.vaszon.bind("<Motion>", self.egermozgas)
        self.ablak.bind("<space>", lambda e: self.inditas_szunet())
        self.ablak.bind("<KeyPress-s>", lambda e: self.statisztika())
        self.dij_mezo.bind("<Return>", lambda e: self.oradij_beallitas())

    def hely_koordinata(self, index):
        sor, oszlop = divmod(index, OSZLOPOK)
        x = MARGO + oszlop * HELY_SZ
        y = MARGO + sor * HELY_M + ((sor + 1) // 2) * SAV
        return x, y

    def hely_index(self, x, y):
        for i in range(len(self.haz.helyek)):
            hx, hy = self.hely_koordinata(i)
            if hx <= x <= hx + HELY_SZ and hy <= y <= hy + HELY_M:
                return i
        return None

    def rajzol(self):
        v = self.vaszon
        v.delete("all")

        for i, auto in enumerate(self.haz.helyek):
            x, y = self.hely_koordinata(i)
            v.create_rectangle(x, y, x + HELY_SZ, y + HELY_M,
                               outline="white", width=2)
            v.create_text(x + 10, y + 10, text=str(i + 1),
                          fill="white", font=("Arial", 8))
            if auto is not None:
                self.auto_rajzolasa(x, y, auto)

        szel = int(v["width"])
        mag = int(v["height"])
        arany = self.haz.foglalt_db() / len(self.haz.helyek)
        szin = "#2ecc71" if arany < 0.7 else (
            "#f1c40f" if arany < 0.95 else "#e74c3c")
        v.create_rectangle(MARGO, mag - 25, szel - MARGO, mag - 10,
                           outline="white")
        v.create_rectangle(MARGO, mag - 25,
                           MARGO + (szel - 2 * MARGO) * arany, mag - 10,
                           fill=szin, outline="")
        v.create_text(szel // 2, mag - 17, fill="black",
                      font=("Arial", 9, "bold"),
                      text=f"Foglaltság: {arany:.0%}")

        self.ora_cimke.config(text=self.ido.strftime("%H:%M"))
        self.info_cimke.config(text=(
            f"Szabad helyek: {len(self.haz.szabad_helyek())} / "
            f"{len(self.haz.helyek)}\n"
            f"Mai bevétel: {self.mai_bevetel:,} Ft\n"
            f"Elutasított autók: {self.haz.elutasitott}"
        ).replace(",", " "))

    def auto_rajzolasa(self, x, y, auto):
        v = self.vaszon
        x1, y1 = x + 15, y + 15
        x2, y2 = x + HELY_SZ - 15, y + HELY_M - 12
        v.create_rectangle(x1, y1, x2, y2, fill=auto.szin, outline="black")
        v.create_rectangle(x1 + 15, y1 + 6, x2 - 15, y2 - 22,
                           fill="#cfe8ff", outline="")
        v.create_rectangle(x1 + 10, y2 - 15, x2 - 10, y2 - 3,
                           fill="white", outline="black")
        v.create_text((x1 + x2) / 2, y2 - 9, text=auto.rendszam,
                      font=("Arial", 7, "bold"))
        if auto.tipus == "Elektromos":
            v.create_text(x2 - 6, y1 + 7, text="⚡", font=("Arial", 9))

    def inditas_szunet(self):
        self.fut = not self.fut
        self.inditas_gomb.config(text="⏸ Szünet" if self.fut else "▶ Indítás")
        if self.fut:
            self.lepes()
        elif self.idozito:
            self.ablak.after_cancel(self.idozito)
            self.idozito = None

    def lepes(self):
        self.ido += LEPES

        for i, auto in enumerate(self.haz.helyek):
            if auto is not None and auto.tavozik_e(self.ido):
                self.kienged(i)

        if random.random() < vl_erkezesi_esely(self.ido.hour):
            auto = vl_veletlen_auto(self.ido)
            hely = self.haz.beenged(auto)
            if hely is None:
                self.esemeny(f"⛔ {auto.rendszam} – tele, elküldve")
            else:
                self.esemeny(f"→ {auto} beállt a {hely + 1}. helyre")

        if self.ido.hour == 0 and self.ido.minute == 0:
            self.mai_bevetel = 0
            self.esemeny("🌙 Új nap kezdődött")

        self.rajzol()
        if self.fut:
            kesleltetes = 1100 - self.sebesseg.get() * 100
            self.idozito = self.ablak.after(kesleltetes, self.lepes)

    def kienged(self, hely):
        try:
            auto, perc, dij = self.haz.kienged(hely, self.ido)
        except sqlite3.Error as hiba:
            messagebox.showerror("Adatbázis hiba", str(hiba))
            return None
        self.mai_bevetel += dij
        self.esemeny(f"← {auto.rendszam}  {perc} perc  {dij} Ft")
        return auto, perc, dij

    def esemeny(self, szoveg):
        self.naplo.insert(0, f"{self.ido.strftime('%H:%M')}  {szoveg}")
        if self.naplo.size() > 100:
            self.naplo.delete(100, tk.END)

    def kattintas(self, esemeny):
        hely = self.hely_index(esemeny.x, esemeny.y)
        if hely is None or self.haz.helyek[hely] is None:
            return
        auto = self.haz.helyek[hely]
        perc = auto.eltelt_perc(self.ido)
        dij = auto.dij(perc, self.haz.oradij)
        if messagebox.askyesno(
                "Kiengedés",
                f"{auto}\nParkolt: {perc} perc\nFizetendő: {dij} Ft\n\n"
                "Kiengeded az autót?"):
            self.kienged(hely)
            self.rajzol()

    def egermozgas(self, esemeny):
        hely = self.hely_index(esemeny.x, esemeny.y)
        if hely is None:
            return
        auto = self.haz.helyek[hely]
        if auto is None:
            self.allapot.config(text=f"{hely + 1}. hely – szabad")
        else:
            perc = auto.eltelt_perc(self.ido)
            self.allapot.config(text=(
                f"{hely + 1}. hely – {auto} | érkezett: "
                f"{auto.erkezes.strftime('%H:%M')} | {perc} perce áll | "
                f"eddigi díj: {auto.dij(perc, self.haz.oradij)} Ft"))

    def oradij_beallitas(self):
        try:
            uj = int(self.dij_mezo.get())
            if uj <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hibás érték",
                                 "Az óradíj pozitív egész szám legyen!")
            self.dij_mezo.delete(0, tk.END)
            self.dij_mezo.insert(0, str(self.haz.oradij))
            return
        self.haz.oradij = uj
        messagebox.showinfo("Óradíj", f"Az új óradíj: {uj} Ft "
                                      f"(az első {INGYENES_PERC} perc ingyenes)")

    def statisztika(self):
        try:
            s = self.haz.statisztika()
        except sqlite3.Error as hiba:
            messagebox.showerror("Adatbázis hiba", str(hiba))
            return
        if s is None:
            messagebox.showinfo("Statisztika", "Még nincs lezárt parkolás.")
            return
        messagebox.showinfo("Statisztika", (
            f"Lezárt parkolások: {s['darab']} db "
            f"(ebből elektromos: {s['elektromos']})\n"
            f"Összes bevétel: {s['bevetel']} Ft\n\n"
            f"Átlagos parkolási idő: {s['atlag_perc']:.1f} perc\n"
            f"Medián parkolási idő: {s['median_perc']:.0f} perc\n"
            f"Szórás: {s['szoras_perc']:.1f} perc\n"
            f"Átlagos díj: {s['atlag_dij']:.0f} Ft\n\n"
            f"Leggyakoribb érkezési óra: {s['csucsora']}:00"))

    def export(self):
        fajl = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV fájl", "*.csv")],
            initialfile="parkolasok.csv")
        if not fajl:
            return
        try:
            db = self.haz.export_csv(fajl)
        except (OSError, sqlite3.Error) as hiba:
            messagebox.showerror("Mentési hiba", str(hiba))
            return
        messagebox.showinfo("Export", f"{db} sor mentve:\n{fajl}")

    def naplo_torlese(self):
        if messagebox.askyesno("Napló törlése",
                               "Biztosan törlöd az összes mentett "
                               "parkolást?"):
            self.haz.naplo_torlese()
            self.naplo.delete(0, tk.END)
            self.mai_bevetel = 0
            self.rajzol()


if __name__ == "__main__":
    gyoker = tk.Tk()
    ParkolohazApp(gyoker)
    gyoker.mainloop()
