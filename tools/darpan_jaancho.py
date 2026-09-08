# -*- coding: utf-8 -*-
"""दर्पण की जाँच.

असली Tk खिड़की बनती है (दिखती नहीं), असली queue चलती है, और असली
Treeview पढ़ा जाता है. कोई नक़ली widget नहीं.

जिस मशीन पर display न हो, वहाँ यह पूरी जाँच छोड़ दी जाती है और वही
बताया जाता है — चुपचाप पास नहीं होती.
"""

from __future__ import unicode_literals

import os
import sys

YAHAN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(YAHAN, "sabha"))

PASS = [0]
FAIL = [0]


def kehna(kya, chahiye, mila):
    if chahiye == mila:
        PASS[0] += 1
        print("  [ पास ]  %s" % kya)
    else:
        FAIL[0] += 1
        print("  [ फेल ]  %s\n           चाहिए %r, मिला %r" % (kya, chahiye, mila))


class NakliKaam(object):
    def __init__(self, id, vivaran, halat, kaun=None):
        self.id, self.vivaran, self.halat, self.kaun_kare = id, vivaran, halat, kaun

    def dict_me(self):
        return {"id": self.id, "vivaran": self.vivaran,
                "halat": self.halat, "kaun_kare": self.kaun_kare}


class NakliKaryasuchi(object):
    def __init__(self, kaam_suchi):
        self.kaam = {k.id: k for k in kaam_suchi}


class NakliSadasya(object):
    def __init__(self, prakar):
        self.prakar = prakar


class NakliSabhapati(object):
    def __init__(self):
        self.sadasya = {"ved-1": NakliSadasya("ollama"), "ved-2": NakliSadasya("aujaar")}
        self.karya = NakliKaryasuchi([])
        self.banda = False

    def band(self):
        self.banda = True


def main():
    try:
        import tkinter as tk
    except ImportError:
        print("\n  tkinter नहीं है — दर्पण की जाँच छोड़ी जा रही है.")
        print("  Debian/Ubuntu पर: sudo apt install python3-tk\n")
        return 0

    try:
        root = tk.Tk()
        root.withdraw()
    except Exception as e:
        print("\n  display नहीं मिला (%s) — दर्पण की जाँच छोड़ी जा रही है." % type(e).__name__)
        print("  यह पास नहीं हुई, चली ही नहीं.\n")
        return 0

    from darpan import HALAT_RANG, Darpan
    from karyasuchi import CHAL_RAHA, HUA, NAKAAM, RUKA, TAIYAR

    print("\n  दर्पण")
    d = Darpan(root, lambda: NakliSabhapati())
    d.sp = NakliSabhapati()

    # -- हाल के रंग karyasuchi से मेल खाते हैं ------------------------------
    for halat in (RUKA, TAIYAR, CHAL_RAHA, HUA, NAKAAM):
        kehna("हाल '%s' का रंग तय है" % halat, True, halat in HALAT_RANG)

    # -- सदस्य -------------------------------------------------------------
    d._sambhalo("sadasya", {"ved-1": True, "ved-2": False})
    rows = d.sadasya_tree.get_children()
    kehna("दोनों सदस्य दिखे", 2, len(rows))
    naam = sorted(d.sadasya_tree.item(r, "text") for r in rows)
    kehna("नाम सही", ["ved-1", "ved-2"], naam)
    haal = {d.sadasya_tree.item(r, "text"): d.sadasya_tree.item(r, "values")[1] for r in rows}
    kehna("तैयार सदस्य 'तैयार' दिखा", "तैयार", haal["ved-1"])
    kehna("अतैयार सदस्य 'नहीं' दिखा", "नहीं", haal["ved-2"])
    kehna("प्रकार दिखा", "ollama",
          [d.sadasya_tree.item(r, "values")[0] for r in rows
           if d.sadasya_tree.item(r, "text") == "ved-1"][0])

    # -- काम ---------------------------------------------------------------
    d._sambhalo("kaam", NakliKaryasuchi([
        NakliKaam("k1", "पहला काम", HUA, "ved-1"),
        NakliKaam("k2", "दूसरा काम", NAKAAM, "ved-2"),
        NakliKaam("k3", "तीसरा काम", RUKA, None),
    ]))
    rows = d.kaam_tree.get_children()
    kehna("तीनों काम दिखे", 3, len(rows))
    kehna("हाल सही उतरा", HUA, d.kaam_tree.item(rows[0], "values")[0])
    kehna("हाल tag लगा (रंग के लिए)", (NAKAAM,), d.kaam_tree.item(rows[1], "tags"))
    kehna("बिना किसी के काम पर — दिखा", "—", d.kaam_tree.item(rows[2], "values")[1])

    # दोबारा भेजने पर दोगुना न हो
    d._sambhalo("kaam", NakliKaryasuchi([NakliKaam("k1", "अकेला", TAIYAR, "ved-1")]))
    kehna("दोबारा भेजने पर सूची ताज़ा होती है, जुड़ती नहीं",
          1, len(d.kaam_tree.get_children()))

    # -- बही ---------------------------------------------------------------
    d._sambhalo("bahi", ["पहली पंक्ति", "दूसरी पंक्ति"])
    text = d.bahi.get("1.0", "end")
    kehna("बही में दोनों पंक्तियाँ", True, "पहली पंक्ति" in text and "दूसरी पंक्ति" in text)
    kehna("बही पढ़ने-भर की रहती है", "disabled", str(d.bahi.cget("state")))

    d._sambhalo("jawab", "यह रहा जवाब")
    kehna("जवाब बही में आया", True, "यह रहा जवाब" in d.bahi.get("1.0", "end"))

    # -- गड़बड़ --------------------------------------------------------------
    d._sambhalo("gadbad", "कुछ टूटा")
    kehna("गड़बड़ बही में आई", True, "कुछ टूटा" in d.bahi.get("1.0", "end"))
    kehna("गड़बड़ स्थिति-पट्टी पर दिखी", True, "गड़बड़" in d.sthiti.cget("text"))

    # -- ख़ात्मा -------------------------------------------------------------
    d.chalao_btn.configure(state="disabled")
    d._sambhalo("khatam", None)
    kehna("ख़त्म होने पर 'चलाओ' फिर चालू", "normal", str(d.chalao_btn.cget("state")))
    kehna("गड़बड़ के बाद स्थिति नहीं बदली", True, "गड़बड़" in d.sthiti.cget("text"))

    # -- ख़ाली काम पर सभा नहीं बैठती ------------------------------------------
    d.kaam_box.delete(0, "end")
    before = d.thread
    d.chalao()
    kehna("ख़ाली काम पर कोई thread नहीं चला", before, d.thread)

    root.destroy()

    print("\n  नतीजा:  %d पास,  %d फेल\n" % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
