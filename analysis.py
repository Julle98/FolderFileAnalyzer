import os
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import zipfile
import tempfile
import shutil

KIELET = {
    "finnish": {
        "select_folder": "Valitse kansio",
        "start_analysis": "Aloita analyysi",
        "language": "Kieli",
        "results": "Tulokset",
        "files": "Tiedostoja",
        "filename": "Tiedostonimi",
        "chars": "Merkkejä",
        "lines": "Rivejä",
        "save_csv": "Tallenna CSV",
        "analysis_done": "Analyysi valmis!",
        "error": "Virhe",
        "no_folder": "Kansiota ei valittu.",
        "csv_saved": "CSV tallennettu onnistuneesti.",
        "reset": "Tyhjennä",
        "dark_mode": "Tumma teema",
        "settings": "Asetukset",
        "zip_support": "Zip-tuki",
        "blur_path": "Piilota tiedostosijainti",
        "cleanup_after_analysis": "Siivoa temp-kansio analyysin jälkeen",
        "clear_cache": "Tyhjennä välimuisti",
        "cleanup_temp": "Siivoa väliaikaiset tiedostot" 
    },
    "english": {
        "select_folder": "Select Folder",
        "start_analysis": "Start Analysis",
        "language": "Language",
        "results": "Results",
        "files": "Files",
        "filename": "Filename",
        "chars": "Characters",
        "lines": "Lines",
        "save_csv": "Save CSV",
        "analysis_done": "Analysis complete!",
        "error": "Error",
        "no_folder": "No folder selected.",
        "csv_saved": "CSV saved successfully.",
        "reset": "Reset",
        "dark_mode": "Dark Theme",
        "settings": "Settings",
        "zip_support": "Zip support",
        "blur_path": "Blur file path",
        "cleanup_after_analysis": "Cleanup temp folder after analysis",
        "clear_cache": "Clear cache",
        "cleanup_temp": "Clean up temporary files"
    }
}

SALLITUT_PÄÄTTEET = {'.py', '.js', '.css', '.html', '.json'}

class TiedostoAnalyysiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Analyzer")
        self.lataa_asetukset()
        self.teema = self.tumma_teema
        self.temp_siivous = tk.BooleanVar(value=False)
        self.kansio = ""
        self.tulokset = [] 
        self.analyysi_laskuri = 0
        self.csv_laskuri = 0

        self.style = ttk.Style()
        self.luo_käyttöliittymä()
        self.päivitä_teema()

    def teksti(self, avain):
        return KIELET[self.kieli.get()][avain]

    def luo_asetukset_menu(self):
        menubar = tk.Menu(self.root)
        asetukset_menu = tk.Menu(menubar, tearoff=0)
        asetukset_menu.add_checkbutton(label=self.teksti("dark_mode"), variable=self.teema, command=self.päivitä_teema)
        asetukset_menu.add_checkbutton(label=self.teksti("zip_support"), variable=self.zip_tuki)
        asetukset_menu.add_checkbutton(label=self.teksti("blur_path"), variable=self.blur_sijainti)
        asetukset_menu.add_checkbutton(label=self.teksti("cleanup_after_analysis"), variable=self.temp_siivous)
        asetukset_menu.add_command(label=self.teksti("reset"), command=self.reset)
        menubar.add_cascade(label=self.teksti("settings"), menu=asetukset_menu)
        self.root.config(menu=menubar)

    def luo_käyttöliittymä(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        self.luo_asetukset_menu()

        ylapaneeli = ttk.Frame(self.root, padding=10)
        ylapaneeli.grid(row=0, column=0, sticky="ew")
        ylapaneeli.columnconfigure(0, weight=0)
        ylapaneeli.columnconfigure(1, weight=0)

        self.cache_nappi = ttk.Button(ylapaneeli, text=self.teksti("clear_cache"), command=self.tyhjenna_cache)
        self.cache_nappi.grid(row=0, column=4, sticky="ew")

        ttk.Label(ylapaneeli, text=self.teksti("language")).grid(row=0, column=0, sticky="w", padx=(0, 5))

        kielivalinta = ttk.Combobox(
            ylapaneeli,
            textvariable=self.kieli,
            values=["finnish", "english"],
            state="readonly",
            width=10
        )
        kielivalinta.grid(row=0, column=1, sticky="w")
        kielivalinta.bind("<<ComboboxSelected>>", lambda e: [self.päivitä_tekstit(), self.tallenna_asetukset()])

        self.analyysi_nappi = ttk.Button(ylapaneeli, text=self.teksti("start_analysis"), command=self.analysoi)
        self.analyysi_nappi.grid(row=0, column=2, sticky="ew")

        self.tallenna_nappi = ttk.Button(ylapaneeli, text=self.teksti("save_csv"), command=self.tallenna_csv)
        self.tallenna_nappi.grid(row=0, column=3, sticky="ew")

        kansio_frame = ttk.Frame(self.root, padding=(10, 0))
        kansio_frame.grid(row=1, column=0, sticky="ew")
        kansio_frame.columnconfigure(0, weight=1)

        self.kansio_label = ttk.Label(kansio_frame, text=self.teksti("select_folder"))
        self.kansio_label.grid(row=0, column=0, sticky="w")
        ttk.Button(kansio_frame, text="📁", command=self.valitse_kansio).grid(row=0, column=1, sticky="e")

        tulos_frame = ttk.Frame(self.root)
        tulos_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
        tulos_frame.rowconfigure(0, weight=1)
        tulos_frame.columnconfigure(0, weight=1)

        self.tulos_taulukko = ttk.Treeview(tulos_frame, columns=("filename", "chars", "lines"), show="headings")
        self.tulos_taulukko.heading("filename", text=self.teksti("filename"))
        self.tulos_taulukko.heading("chars", text=self.teksti("chars"))
        self.tulos_taulukko.heading("lines", text=self.teksti("lines"))
        self.tulos_taulukko.column("filename", anchor="w")
        self.tulos_taulukko.column("chars", anchor="center", width=100)
        self.tulos_taulukko.column("lines", anchor="center", width=100)
        self.tulos_taulukko.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(tulos_frame, orient="vertical", command=self.tulos_taulukko.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tulos_taulukko.configure(yscrollcommand=scrollbar.set)

    def päivitä_tekstit(self):
        if self.kansio:
            polku = self.kansio
            if self.blur_sijainti.get():
                osat = polku.split(os.sep)
                polku = os.sep.join(["...", *osat[-2:]]) if len(osat) > 1 else "..." + os.sep + os.path.basename(polku)
            self.kansio_label.config(text=f"{self.teksti('select_folder')}: {polku}")
        else:
            self.kansio_label.config(text=f"{self.teksti('select_folder')}:")

        self.root.title("Tiedostoanalyysi" if self.kieli.get() == "finnish" else "File Analyzer")
        self.analyysi_nappi.config(text=self.teksti("start_analysis"))
        self.tallenna_nappi.config(text=self.teksti("save_csv"))
        self.cache_nappi.config(text=self.teksti("clear_cache"))
        self.tulos_taulukko.heading("filename", text=self.teksti("filename"))
        self.tulos_taulukko.heading("chars", text=self.teksti("chars"))
        self.tulos_taulukko.heading("lines", text=self.teksti("lines"))

        self.luo_asetukset_menu()

    def päivitä_teema(self):
        if self.teema.get():
            self.style.theme_use("clam")
            dark_bg = "#2e2e2e"
            button_bg = "#444"

            self.style.configure("TFrame", background=dark_bg)
            self.style.configure("TLabel", background=dark_bg, foreground="white")
            self.style.configure("TButton", background=button_bg, foreground="white")
            self.style.configure("Treeview", background=dark_bg, foreground="white", fieldbackground=dark_bg)
            self.style.configure("Treeview.Heading", background=button_bg, foreground="white")

            for frame in [self.root]:
                try:
                    frame.configure(bg=dark_bg)
                except tk.TclError:
                    pass
        else:
            self.style.theme_use("default")
            self.style.configure("Treeview", background="white", foreground="black", fieldbackground="white")
            self.style.configure("Treeview.Heading", background="SystemButtonFace", foreground="black")

            for frame in [self.root]:
                try:
                    frame.configure(bg="SystemButtonFace")
                except tk.TclError:
                    pass

    def valitse_kansio(self):
        if self.zip_tuki.get():
            tiedosto = filedialog.askopenfilename(
                initialdir=self.viime_kansio or os.getcwd(),
                filetypes=[("Zip files", "*.zip")]
            )
            if tiedosto and tiedosto.endswith(".zip"):
                self.temp_kansio = tempfile.mkdtemp()
                with zipfile.ZipFile(tiedosto, 'r') as zip_ref:
                    zip_ref.extractall(self.temp_kansio)
                self.kansio = self.temp_kansio
                näytettävä = tiedosto
                if self.blur_sijainti.get():
                    osat = tiedosto.split(os.sep)
                    näytettävä = os.sep.join(["...", *osat[-2:]]) if len(osat) > 1 else "..." + os.sep + os.path.basename(tiedosto)
                self.kansio_label.config(text=f"{self.teksti('select_folder')}: {näytettävä} (ZIP)")
                self.viime_kansio = os.path.dirname(tiedosto)
                self.tallenna_asetukset()
            else:
                kansio = filedialog.askdirectory(initialdir=self.viime_kansio or os.getcwd())
                if kansio:
                    self.kansio = kansio
                    näytettävä = kansio
                    if self.blur_sijainti.get():
                        osat = kansio.split(os.sep)
                        näytettävä = os.sep.join(["...", *osat[-2:]]) if len(osat) > 1 else "..." + os.sep + os.path.basename(kansio)
                    self.kansio_label.config(text=f"{self.teksti('select_folder')}: {näytettävä}")
                    self.viime_kansio = kansio
                    self.tallenna_asetukset()
        else:
            kansio = filedialog.askdirectory(initialdir=self.viime_kansio or os.getcwd())
            if kansio:
                self.kansio = kansio
                näytettävä = kansio
                if self.blur_sijainti.get():
                    osat = kansio.split(os.sep)
                    näytettävä = os.sep.join(["...", *osat[-2:]]) if len(osat) > 1 else "..." + os.sep + os.path.basename(kansio)
                self.kansio_label.config(text=f"{self.teksti('select_folder')}: {näytettävä}")
                self.viime_kansio = kansio
                self.tallenna_asetukset()

    def analysoi(self):
        if not self.kansio:
            messagebox.showerror(self.teksti("error"), self.teksti("no_folder"))
            return

        self.analyysi_laskuri += 1
        self.tulokset = []
        tiedosto_maara = 0
        merkit = 0
        rivit = 0

        for juuri, _, tiedostot in os.walk(self.kansio):
            for tiedosto in tiedostot:
                if os.path.splitext(tiedosto)[1] in SALLITUT_PÄÄTTEET:
                    polku = os.path.join(juuri, tiedosto)
                    try:
                        with open(polku, 'r', encoding='utf-8') as f:
                            sisältö = f.read()
                            tiedosto_maara += 1
                            merkit += len(sisältö)
                            rivit += sisältö.count('\n') + 1
                            näytettävä_nimi = tiedosto
                            if self.blur_sijainti.get():
                                polku_osat = polku.split(os.sep)
                                if len(polku_osat) > 2:
                                    näytettävä_nimi = os.sep.join(["...", *polku_osat[-2:]])
                                else:
                                    näytettävä_nimi = "..." + os.sep + tiedosto

                            self.tulokset.append([näytettävä_nimi, len(sisältö), sisältö.count('\n') + 1])
                    except Exception as e:
                        print(f"⚠️ {polku}: {e}")

        self.tulos_taulukko.delete(*self.tulos_taulukko.get_children())

        for nimi, m, r in self.tulokset:
            self.tulos_taulukko.insert("", "end", values=(nimi, m, r))

        if hasattr(self, "yhteenveto"):
            self.yhteenveto.config(text=f"{self.teksti('files')}: {tiedosto_maara} | {self.teksti('chars')}: {merkit} | {self.teksti('lines')}: {rivit}")

        if hasattr(self, "temp_kansio") and self.temp_kansio and os.path.exists(self.temp_kansio):
            try:
                shutil.rmtree(self.temp_kansio)
            except Exception as e:
                print(f"⚠️ Vanhan temp-kansion siivous epäonnistui: {e}")
        self.temp_kansio = tempfile.mkdtemp()

        if self.temp_siivous.get():
            if hasattr(self, "temp_kansio") and self.temp_kansio and os.path.exists(self.temp_kansio):
                try:
                    shutil.rmtree(self.temp_kansio)
                    self.temp_kansio = None
                except Exception as e:
                    print(f"⚠️ Temp-kansion automaattinen siivous epäonnistui: {e}")

        messagebox.showinfo(self.teksti("results"), self.teksti("analysis_done"))

    def tallenna_csv(self):
        if not self.tulokset:
            return
        polku = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if polku:
            with open(polku, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Filename", "Characters", "Lines"])
                for rivi in self.tulokset:
                    writer.writerow(rivi)
            messagebox.showinfo(self.teksti("results"), self.teksti("csv_saved"))

        self.csv_laskuri += 1
        self.tulos_taulukko.insert("", "end", values=(f"💾 {self.csv_laskuri} {self.teksti('save_csv')}", "", ""))

    def tallenna_asetukset(self):
        asetukset = {
            "kieli": self.kieli.get(),
            "tumma_teema": str(self.tumma_teema.get()),
            "zip_tuki": str(self.zip_tuki.get()),
            "blur_sijainti": str(self.blur_sijainti.get()),
            "ikkuna_koko": f"{self.root.winfo_width()}x{self.root.winfo_height()}",
            "ikkuna_sijainti": f"{self.root.winfo_x()},{self.root.winfo_y()}",
            "viime_kansio": getattr(self, "viime_kansio", ""),
            "temp_siivous": str(self.temp_siivous.get())
        }
        with open("asetukset.txt", "w", encoding="utf-8") as f:
            for avain, arvo in asetukset.items():
                f.write(f"{avain}={arvo}\n")

    def lataa_asetukset(self):
        oletukset = {
            "kieli": "english",
            "tumma_teema": "False",
            "zip_tuki": "False",
            "blur_sijainti": "False",
            "temp_siivous": "False"
        }
        try:
            with open("asetukset.txt", "r", encoding="utf-8") as f:
                for rivi in f:
                    if "=" in rivi:
                        avain, arvo = rivi.strip().split("=", 1)
                        oletukset[avain] = arvo
        except FileNotFoundError:
            pass

        self.kieli = tk.StringVar(value=oletukset["kieli"])
        self.tumma_teema = tk.BooleanVar(value=oletukset["tumma_teema"] == "True")
        self.zip_tuki = tk.BooleanVar(value=oletukset["zip_tuki"] == "True")
        self.blur_sijainti = tk.BooleanVar(value=oletukset["blur_sijainti"] == "True")
        self.temp_siivous = tk.BooleanVar(value=oletukset["temp_siivous"] == "True")

        if "ikkuna_koko" in oletukset:
            self.root.geometry(oletukset["ikkuna_koko"])
        if "ikkuna_sijainti" in oletukset:
            try:
                x, y = map(int, oletukset["ikkuna_sijainti"].split(","))
                self.root.geometry(f"+{x}+{y}")
            except:
                pass

        self.viime_kansio = oletukset.get("viime_kansio", "")

    def tyhjenna_cache(self):
        if self.temp_kansio is not None and os.path.exists(self.temp_kansio):
            try:
                shutil.rmtree(self.temp_kansio)
                self.temp_kansio = None
                messagebox.showinfo(self.teksti("settings"), self.teksti("cleanup_temp"))
            except Exception as e:
                messagebox.showerror(self.teksti("error"), f"{self.teksti('cleanup_temp')}:\n{e}")
        else:
            messagebox.showinfo(self.teksti("settings"), self.teksti("cleanup_temp"))

    def reset(self):
        self.kansio = ""
        self.tulokset = []
        self.analyysi_laskuri = 0
        self.csv_laskuri = 0
        self.kansio_label.config(text=f"{self.teksti('select_folder')}:")
        self.tulos_taulukko.delete(*self.tulos_taulukko.get_children())
        if hasattr(self, "yhteenveto"):
            self.yhteenveto.config(text="")
        self.tallenna_asetukset()

if __name__ == "__main__":
    root = tk.Tk()
    app = TiedostoAnalyysiApp(root)
    root.mainloop()