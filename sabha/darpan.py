# -*- coding: utf-8 -*-
"""दर्पण — सभा की खिड़की.

सभा वैसी की वैसी रहती है. यह उसके ऊपर बैठा एक आईना भर है: वही Sabhapati
चलाता है जो `sabha.py chalao` चलाता है, और वही Karyasuchi और Nireekshak
पढ़कर दिखाता है.

tkinter इसलिए कि सभा stdlib-only है और रहनी चाहिए. कोई नई चीज़ install
नहीं करनी पड़ती.

दो बातें जो इस file का आकार तय करती हैं:

  १. tkinter एक ही thread का है. काम पीछे चलता है, पर खिड़की को छूता नहीं —
     पीछे वाला thread सिर्फ़ एक queue में डालता है, और खिड़की `after()` से
     उसे पढ़ती है.

  २. सभा का काम मिनटों चल सकता है. इसलिए "चलाओ" दबाते ही खिड़की जमती नहीं;
     वो चलती रहती है और बीच में रोका भी जा सकता है.
"""

from __future__ import unicode_literals

import os
import queue
import threading
import traceback

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:            # pragma: no cover - headless
    tk = None


# काम के हाल — नाम karyasuchi.py से लिए हैं, अंदाज़े से नहीं.
HALAT_RANG = {
    "chal-raha": "#d9a55b",
    "chhoda": "#cccccc",
    "hua": "#5bd97e",
    "nakaam": "#d95b5b",
    "ruka": "#8a8a8a",
    "taiyar": "#5b8dd9",
}


class Darpan(object):
    """सभा की खिड़की."""

    def __init__(self, root, sabhapati_banao):
        """
        sabhapati_banao = एक function जो नया Sabhapati बनाकर देता है.

        Sabhapati सीधा नहीं लिया जाता क्योंकि हर बार "चलाओ" पर नई सभा
        बननी चाहिए — पुरानी का बजट और बही पिछले काम की होती है.
        """
        self.root = root
        self.banao = sabhapati_banao
        self.sp = None
        self.thread = None
        self.rokna = threading.Event()
        self.q = queue.Queue()

        root.title("सभा — दर्पण")
        root.geometry("980x640")
        self._banao_dhancha()
        self.root.after(120, self._queue_padho)

    # ---------------------------------------------------------------- ढाँचा

    def _banao_dhancha(self):
        upar = ttk.Frame(self.root, padding=8)
        upar.pack(fill="x")

        ttk.Label(upar, text="काम:").pack(side="left")
        self.kaam_box = ttk.Entry(upar)
        self.kaam_box.pack(side="left", fill="x", expand=True, padx=6)
        self.kaam_box.bind("<Return>", lambda e: self.chalao())

        self.chalao_btn = ttk.Button(upar, text="चलाओ", command=self.chalao)
        self.chalao_btn.pack(side="left")
        self.roko_btn = ttk.Button(upar, text="रोको", command=self.roko, state="disabled")
        self.roko_btn.pack(side="left", padx=(6, 0))

        beech = ttk.PanedWindow(self.root, orient="horizontal")
        beech.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # बाएँ — सदस्य
        baayen = ttk.Labelframe(beech, text="सदस्य", padding=6)
        self.sadasya_tree = ttk.Treeview(
            baayen, columns=("prakar", "halat"), show="tree headings", height=8)
        self.sadasya_tree.heading("#0", text="नाम")
        self.sadasya_tree.heading("prakar", text="प्रकार")
        self.sadasya_tree.heading("halat", text="हाल")
        self.sadasya_tree.column("#0", width=110)
        self.sadasya_tree.column("prakar", width=70)
        self.sadasya_tree.column("halat", width=90)
        self.sadasya_tree.pack(fill="both", expand=True)
        beech.add(baayen, weight=1)

        # दाएँ — काम और बही
        daayen = ttk.PanedWindow(beech, orient="vertical")

        kaam_frame = ttk.Labelframe(daayen, text="काम", padding=6)
        self.kaam_tree = ttk.Treeview(
            kaam_frame, columns=("halat", "kaun"), show="tree headings")
        self.kaam_tree.heading("#0", text="ब्योरा")
        self.kaam_tree.heading("halat", text="हाल")
        self.kaam_tree.heading("kaun", text="किसने")
        self.kaam_tree.column("#0", width=430)
        self.kaam_tree.column("halat", width=90)
        self.kaam_tree.column("kaun", width=100)
        for halat, rang in HALAT_RANG.items():
            self.kaam_tree.tag_configure(halat, foreground=rang)
        self.kaam_tree.pack(fill="both", expand=True)
        daayen.add(kaam_frame, weight=3)

        bahi_frame = ttk.Labelframe(daayen, text="बही", padding=6)
        self.bahi = tk.Text(bahi_frame, height=8, wrap="word", state="disabled")
        bar = ttk.Scrollbar(bahi_frame, command=self.bahi.yview)
        self.bahi.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        self.bahi.pack(fill="both", expand=True)
        daayen.add(bahi_frame, weight=2)

        beech.add(daayen, weight=3)

        self.sthiti = ttk.Label(self.root, text="तैयार", relief="sunken", anchor="w", padding=4)
        self.sthiti.pack(fill="x", side="bottom")

    # ---------------------------------------------------------------- चलाना

    def chalao(self):
        if self.thread and self.thread.is_alive():
            return
        kaam = self.kaam_box.get().strip()
        if not kaam:
            messagebox.showinfo("सभा", "पहले काम लिखो.")
            return

        self._bahi_saaf()
        self.kaam_tree.delete(*self.kaam_tree.get_children())
        self.rokna.clear()
        self.chalao_btn.configure(state="disabled")
        self.roko_btn.configure(state="normal")
        self._sthiti("सभा बैठ रही है…")

        self.thread = threading.Thread(target=self._pichhe_chalao, args=(kaam,), daemon=True)
        self.thread.start()

    def roko(self):
        """रोकने को कहता है. सभा मौजूदा काम पूरा करके रुकेगी — बीच में
        मारना बजट और बही दोनों को अधूरा छोड़ देता है."""
        self.rokna.set()
        self._sthiti("रोकने को कहा — मौजूदा काम पूरा होने दो…")
        self.roko_btn.configure(state="disabled")

    def _pichhe_chalao(self, kaam):
        """पीछे वाला thread. खिड़की को कभी नहीं छूता, सिर्फ़ queue में डालता है."""
        try:
            sp = self.banao()
            self.sp = sp
            self.q.put(("sadasya", sp.sadasya_jaancho()))
            sp.kaam_lo(kaam)
            self.q.put(("kaam", sp.karya))

            chakkar = 0
            while not self.rokna.is_set():
                bacha = sp.chalao(adhiktam_chakkar=1, dikhao=False)
                chakkar += 1
                self.q.put(("kaam", sp.karya))
                self.q.put(("bahi", sp.nireekshak.padho(kitne=40)))
                if not bacha:
                    break
                if chakkar >= 100:
                    self.q.put(("log", "सौ चक्कर हो गए — रोक रहा हूँ."))
                    break

            self.q.put(("jawab", sp.jawab_banao()))
        except Exception:
            self.q.put(("gadbad", traceback.format_exc()))
        finally:
            try:
                if self.sp:
                    self.sp.band()
            except Exception:
                pass
            self.q.put(("khatam", None))

    # ---------------------------------------------------------------- खिड़की

    def _queue_padho(self):
        """खिड़की वाले thread में चलता है. यही अकेला widget छूता है."""
        try:
            while True:
                kya, samagri = self.q.get_nowait()
                self._sambhalo(kya, samagri)
        except queue.Empty:
            pass
        self.root.after(120, self._queue_padho)

    def _sambhalo(self, kya, samagri):
        if kya == "sadasya":
            self._sadasya_dikhao(samagri)
        elif kya == "kaam":
            self._kaam_dikhao(samagri)
        elif kya == "bahi":
            self._bahi_dikhao(samagri)
        elif kya == "log":
            self._bahi_jodo(samagri)
        elif kya == "jawab":
            self._bahi_jodo("\n───── जवाब ─────\n" + str(samagri))
        elif kya == "gadbad":
            self._bahi_jodo("\n───── गड़बड़ ─────\n" + str(samagri))
            self._sthiti("गड़बड़ हुई — बही देखो")
        elif kya == "khatam":
            self.chalao_btn.configure(state="normal")
            self.roko_btn.configure(state="disabled")
            if "गड़बड़" not in self.sthiti.cget("text"):
                self._sthiti("सभा उठी")

    def _sadasya_dikhao(self, natija):
        self.sadasya_tree.delete(*self.sadasya_tree.get_children())
        if not isinstance(natija, dict):
            return
        for naam in sorted(natija):
            v = natija[naam]
            taiyar = v if isinstance(v, bool) else bool(v and v[0])
            prakar = ""
            if self.sp and naam in self.sp.sadasya:
                prakar = getattr(self.sp.sadasya[naam], "prakar", "")
            self.sadasya_tree.insert(
                "", "end", text=naam, values=(prakar, "तैयार" if taiyar else "नहीं"))
        self._sthiti("%d सदस्य तैयार" % sum(
            1 for n in natija if (natija[n] if isinstance(natija[n], bool) else bool(natija[n] and natija[n][0]))))

    def _kaam_dikhao(self, karya):
        self.kaam_tree.delete(*self.kaam_tree.get_children())
        # Karyasuchi काम एक dict में रखता है — self.kaam[id] = Kaam.
        for k in sorted(getattr(karya, "kaam", {}).values(), key=lambda x: getattr(x, "id", "")):
            d = k.dict_me() if hasattr(k, "dict_me") else {}
            halat = str(d.get("halat", ""))
            self.kaam_tree.insert(
                "", "end",
                text=str(d.get("vivaran", ""))[:90],
                values=(halat, str(d.get("kaun_kare") or "—")),
                tags=(halat,))

    def _bahi_dikhao(self, pankti):
        self._bahi_saaf()
        for p in (pankti or []):
            self._bahi_jodo(str(p), tal=False)
        self.bahi.see("end")

    def _bahi_jodo(self, text, tal=True):
        self.bahi.configure(state="normal")
        self.bahi.insert("end", text.rstrip() + "\n")
        self.bahi.configure(state="disabled")
        if tal:
            self.bahi.see("end")

    def _bahi_saaf(self):
        self.bahi.configure(state="normal")
        self.bahi.delete("1.0", "end")
        self.bahi.configure(state="disabled")

    def _sthiti(self, text):
        self.sthiti.configure(text=text)


def kholo(sabhapati_banao):
    """खिड़की खोलो. `sabha.py darpan` से बुलाया जाता है."""
    if tk is None:
        raise RuntimeError("tkinter नहीं मिला. Debian/Ubuntu पर: sudo apt install python3-tk")
    root = tk.Tk()
    Darpan(root, sabhapati_banao)
    root.mainloop()
