# -*- coding: utf-8 -*-
"""
निरीक्षण (NIREEKSHAN) — सब कुछ दर्ज करने वाला बही-खाता.

यह क्या है:
    सभा में जो कुछ होता है, वो सब यहाँ एक-एक लाइन करके लिखा जाता है.
    JSONL शक्ल में — हर लाइन एक पूरा JSON.

यह ऐसा क्यों — JSONL, कोई database क्यों नहीं:
    तीन वजहें.

    पहली — लिखना कभी नहीं टूटता. हर लाइन अलग है, इसलिए बीच में बिजली
    जाए तो सिर्फ़ आख़िरी लाइन अधूरी बचेगी. बाक़ी पूरी file पढ़ी जा सकेगी.
    एक बड़ी JSON file होती तो पूरी की पूरी बेकार हो जाती.

    दूसरी — बिना किसी tool के पढ़ी जा सकती है. grep, tail, less — सब चलते
    हैं. रात को कुछ अटका हो तो `tail -f` काफ़ी है.

    तीसरी — दो साल बाद भी खुलेगी. कोई schema नहीं, कोई migration नहीं,
    कोई version नहीं जो पुराना पड़े.

यह कहाँ से भरता है:
    raksha.py, sabhapati.py, sadasya.py — सब यहाँ दर्ज करते हैं.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional


class Nireekshak(object):
    """बही-खाता."""

    def __init__(self, folder, adhiktam_mb=50):
        """
        folder      = कहाँ लिखना है
        adhiktam_mb = file कितनी बड़ी होने पर नई शुरू करें

        सीमा इसलिए कि छह महीने चलने के बाद यह file gigabytes की हो सकती है,
        और तब उसे खोलना ही मुश्किल हो जाएगा. 50 MB पर काटने से हर file
        editor में खुलती रहेगी.
        """
        self.folder = folder
        os.makedirs(folder, exist_ok=True)
        self.adhiktam_byte = adhiktam_mb * 1024 * 1024
        self.rasta = os.path.join(folder, "sabha.jsonl")
        self._f = None
        self._kholo()

    def _kholo(self):
        if self._f:
            try:
                self._f.close()
            except Exception:
                pass
        # 'a' यानी जोड़ते जाओ — पुराना कभी नहीं मिटता
        self._f = open(self.rasta, "a", encoding="utf-8")

    def _kaato_agar_bada(self):
        """file बड़ी हो गई तो उसे तारीख़ के साथ किनारे रखकर नई शुरू करो."""
        try:
            if os.path.getsize(self.rasta) < self.adhiktam_byte:
                return
        except OSError:
            return

        self._f.close()
        purana = os.path.join(
            self.folder,
            "sabha-%s.jsonl" % time.strftime("%Y%m%d-%H%M%S"))
        try:
            os.rename(self.rasta, purana)
        except OSError:
            pass
        self._kholo()

    # -- दर्ज करना ---------------------------------------------------------------

    def darj(self, kaun, kya, samagri=None):
        """
        एक लाइन दर्ज करता है.

        kaun    = किसने किया ('sabhapati', 'ved-1', 'raksha')
        kya     = क्या हुआ ('kaam-diya', 'natija-aaya', 'khatra-roka')
        samagri = ब्योरा

        कभी exception नहीं फेंकता. दर्ज न हो पाना बुरा है, पर उसकी वजह से
        पूरी सभा रुक जाना उससे बहुत बुरा है.
        """
        try:
            self._kaato_agar_bada()
            line = {
                "samay": time.time(),
                "ghadi": time.strftime("%H:%M:%S"),
                "kaun": kaun,
                "kya": kya,
                "samagri": samagri if samagri is not None else {},
            }
            self._f.write(json.dumps(line, ensure_ascii=False, default=str)
                          + "\n")
            self._f.flush()      # तुरंत disk पर — बिजली गई तो भी बचे
        except Exception:
            pass

    def band(self):
        try:
            if self._f:
                self._f.close()
        except Exception:
            pass

    # -- पढ़ना --------------------------------------------------------------------

    def padho(self, kitne=100, kaun=None, kya=None):
        """
        आख़िरी कुछ लाइनें पढ़ता है, छानकर.

        पूरी file memory में नहीं लाता — लाइन-दर-लाइन पढ़ता है और सिर्फ़
        जितनी चाहिए उतनी रखता है. 50 MB file पर भी यह हल्का रहेगा.
        """
        if not os.path.exists(self.rasta):
            return []
        mile = []
        try:
            with open(self.rasta, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        d = json.loads(line)
                    except ValueError:
                        continue        # अधूरी लाइन छोड़ दो
                    if kaun and d.get("kaun") != kaun:
                        continue
                    if kya and d.get("kya") != kya:
                        continue
                    mile.append(d)
                    if len(mile) > kitne * 3:
                        mile = mile[-kitne:]
        except (IOError, OSError):
            return []
        return mile[-kitne:]

    def hisaab(self):
        """
        पूरी सभा का हिसाब — किसने कितना काम किया, कितना ख़र्च हुआ.

        यह वो चीज़ है जो तुम्हें बताएगी कि सदस्य बढ़ाने से फ़ायदा हो भी रहा
        है या नहीं. दस सदस्यों पर चलाओ, फिर तीस पर, और यहाँ का नतीजा
        मिलाओ. अगर नतीजा वही रहा और ख़र्च तिगुना हो गया, तो जवाब मिल गया.
        """
        h = {}
        for d in self.padho(kitne=100000):
            kaun = d.get("kaun", "?")
            if kaun not in h:
                h[kaun] = {"kaam": 0, "akshar": 0, "second": 0.0,
                           "nakaam": 0}
            s = d.get("samagri", {})
            if d.get("kya") == "natija-aaya":
                h[kaun]["kaam"] += 1
                h[kaun]["akshar"] += s.get("akshar", 0) or 0
                h[kaun]["second"] += s.get("second", 0) or 0
                if not s.get("safal", True):
                    h[kaun]["nakaam"] += 1
        for kaun in h:
            h[kaun]["second"] = round(h[kaun]["second"], 1)
        return h


# ---------------------------------------------------------------------------
# जाँच: python3 sabha/nireekshan.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile

    n = Nireekshak(tempfile.mkdtemp())
    n.darj("sabhapati", "sabha-shuru", {"kaam": "जाँच"})
    n.darj("ved-1", "natija-aaya", {"akshar": 500, "second": 2.5,
                                    "safal": True})
    n.darj("ved-1", "natija-aaya", {"akshar": 300, "second": 1.5,
                                    "safal": False})
    n.darj("ved-2", "natija-aaya", {"akshar": 100, "second": 0.5,
                                    "safal": True})

    sab = n.padho()
    assert len(sab) == 4, len(sab)

    sirf = n.padho(kaun="ved-1")
    assert len(sirf) == 2

    h = n.hisaab()
    assert h["ved-1"]["kaam"] == 2 and h["ved-1"]["akshar"] == 800
    assert h["ved-1"]["nakaam"] == 1
    assert h["ved-2"]["kaam"] == 1

    n.band()
    print("निरीक्षण ठीक है — सारी जाँच पास.")
