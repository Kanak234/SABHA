# -*- coding: utf-8 -*-
"""
कार्यसूची (KARYASUCHI) — कामों का जाल.

यह क्या है:
    एक बड़े काम को छोटे टुकड़ों में बाँटकर रखता है, और यह याद रखता है कि
    कौन सा टुकड़ा किस पर निर्भर है.

    यह सिर्फ़ सूची नहीं है, जाल (graph) है. 'क' पूरा हो तभी 'ख' शुरू हो —
    यह रिश्ता यहीं दर्ज होता है.

यह ऐसा क्यों — और यह पंद्रह सौ वाले सवाल का असली जवाब है:
    सदस्यों की गिनती पहले से तय नहीं होती. होनी भी नहीं चाहिए.

    सभापति सवाल को उतने टुकड़ों में बाँटता है जितने उसमें सचमुच हैं.
    अगर कोई टुकड़ा अभी भी बहुत बड़ा है, तो वो अपने आप और बँट जाता है
    (khud_baanto). तीन परत नीचे जाकर यह अपने आप 15 -> 60 -> 240 तक
    फैल सकता है.

    यानी अगर सवाल सचमुच पंद्रह सौ टुकड़ों का हुआ, तो पंद्रह सौ टुकड़े बनेंगे.
    पर वो संख्या सवाल से निकलेगी, तुम्हारी इच्छा से थोपी नहीं जाएगी.

    और अगर सवाल असल में बारह टुकड़ों का है, तो बारह ही बनेंगे — बाक़ी 1488
    सदस्य वही काम दोहराते, बिजली जलाते, और सभापति का दिमाग़ भर देते.

एक और ज़रूरी चीज़ — दोहराव रोकना:
    दो सदस्य एक ही खोज न करें, इसके लिए हर काम की एक छाप बनती है. वही
    छाप दोबारा आए तो नया काम नहीं बनता. बिना इसके बड़े जाल में आधा काम
    दोहरा होता है.

यह कहाँ जाता है:
    sabhapati.py इसे भरता है और इसी से अगला काम उठाता है.
"""

import hashlib
import json
import os
import time
import uuid
from typing import Any, Dict, List, Optional

# काम की हालतें
RUKA = "ruka"          # निर्भरता पूरी नहीं हुई, इंतज़ार में
TAIYAR = "taiyar"      # उठाया जा सकता है
CHAL_RAHA = "chal-raha"
HUA = "hua"
NAKAAM = "nakaam"
CHHODA = "chhoda"      # छोड़ दिया (जिस पर टिका था वो नाकाम हो गया)


class Kaam(object):
    """जाल का एक टुकड़ा."""

    def __init__(self, vivaran, kis_par_nirbhar=None, gehrai=0,
                 kaun_kare=None, jaanch=None):
        """
        vivaran         = क्या करना है, साफ़ शब्दों में
        kis_par_nirbhar = किन कामों के id पर टिका है
        gehrai          = जाल में कितना नीचे है (0 = सबसे ऊपर)
        kaun_kare       = किस सदस्य को देना है (None = सभापति चुने)
        jaanch          = इसका नतीजा सही है या नहीं, यह जाँचने का तरीक़ा
        """
        self.id = uuid.uuid4().hex[:10]
        self.vivaran = vivaran
        self.kis_par_nirbhar = list(kis_par_nirbhar or [])
        self.gehrai = gehrai
        self.kaun_kare = kaun_kare
        self.jaanch = jaanch or {}

        self.halat = RUKA if self.kis_par_nirbhar else TAIYAR
        self.natija = None
        self.galti = ""
        self.koshish = 0
        self.banaa = time.time()
        self.hua_samay = None

    def chhap(self):
        """
        काम की पहचान-छाप — दोहराव पकड़ने के लिए.

        सिर्फ़ vivaran से बनती है, id से नहीं. इसीलिए दो अलग सदस्य अगर
        एक ही काम बनाएँ, तो दोनों की छाप एक होगी और दूसरा नहीं बनेगा.
        """
        saaf = " ".join(self.vivaran.lower().split())
        return hashlib.sha256(saaf.encode("utf-8")).hexdigest()[:16]

    def dict_me(self):
        return {
            "id": self.id, "vivaran": self.vivaran,
            "kis_par_nirbhar": self.kis_par_nirbhar, "gehrai": self.gehrai,
            "kaun_kare": self.kaun_kare, "halat": self.halat,
            "natija": self.natija, "galti": self.galti,
            "koshish": self.koshish, "banaa": self.banaa,
            "hua_samay": self.hua_samay, "jaanch": self.jaanch,
        }

    def __repr__(self):
        return "<काम %s [%s] %s>" % (self.id, self.halat, self.vivaran[:40])


class Karyasuchi(object):
    """पूरा जाल."""

    def __init__(self, adhiktam_gehrai=3, adhiktam_kaam=500):
        """
        adhiktam_gehrai = जाल कितना नीचे जा सकता है
        adhiktam_kaam   = कुल कितने काम बन सकते हैं

        दोनों सीमाएँ ज़रूरी हैं. बिना इनके एक ग़लत बँटवारा जाल को अनंत तक
        फैला देगा — सभापति टुकड़े बनाता रहेगा, हर टुकड़ा और टुकड़े बनाएगा,
        और मशीन भर जाएगी. यह ऐसी गड़बड़ है जो रात भर चलने वाले काम में
        सुबह जाकर पता चलती है.
        """
        self.kaam = {}
        self.chhap_suchi = {}      # छाप -> काम का id
        self.adhiktam_gehrai = adhiktam_gehrai
        self.adhiktam_kaam = adhiktam_kaam

    # -- जोड़ना ------------------------------------------------------------------

    def jodo(self, kaam):
        """
        नया काम जोड़ता है.

        लौटाता है: (जुड़ा_या_नहीं, वजह)
        पहले से मौजूद छाप हो तो नहीं जोड़ता — यही दोहराव की रोक है.
        """
        if len(self.kaam) >= self.adhiktam_kaam:
            return False, "काम की अधिकतम गिनती (%d) पूरी" % self.adhiktam_kaam

        if kaam.gehrai > self.adhiktam_gehrai:
            return False, "गहराई की सीमा (%d) पार" % self.adhiktam_gehrai

        chhap = kaam.chhap()
        if chhap in self.chhap_suchi:
            return False, "यही काम पहले से है (%s)" % self.chhap_suchi[chhap]

        self.kaam[kaam.id] = kaam
        self.chhap_suchi[chhap] = kaam.id
        return True, ""

    def khud_baanto(self, kaam_id, tukde, kaun_kare=None):
        """
        एक काम को और टुकड़ों में बाँटता है.

        tukde = विवरणों की सूची

        नए टुकड़े एक गहराई नीचे बनते हैं. और मूल काम अब उन सब पर निर्भर
        हो जाता है — यानी वो तभी पूरा माना जाएगा जब उसके सारे टुकड़े हो जाएँ.
        यही वो जगह है जहाँ जाल अपने आप फैलता है.

        लौटाता है: बने हुए टुकड़ों की सूची
        """
        moolya = self.kaam.get(kaam_id)
        if moolya is None:
            return []

        bane = []
        for vivaran in tukde:
            t = Kaam(vivaran, gehrai=moolya.gehrai + 1, kaun_kare=kaun_kare)
            juda, vajah = self.jodo(t)
            if juda:
                bane.append(t)

        if bane:
            moolya.kis_par_nirbhar.extend([t.id for t in bane])
            moolya.halat = RUKA
        return bane

    # -- उठाना ------------------------------------------------------------------

    def taiyar_kaam(self):
        """
        अभी जो काम उठाए जा सकते हैं, उनकी सूची.

        'उठाया जा सकता है' का मतलब — जिन पर यह टिका है वो सब पूरे हो चुके.
        क्रम गहराई से तय होता है: गहरे काम पहले.

        गहरे पहले क्यों? क्योंकि ऊपर वाला काम उन्हीं पर टिका है. गहरे काम
        निपटेंगे तभी ऊपर वाला खुलेगा. उथले पहले करोगे तो जाल चौड़ा होता
        जाएगा और कुछ पूरा नहीं होगा.
        """
        self._halat_sudharo()
        taiyar = [k for k in self.kaam.values() if k.halat == TAIYAR]
        taiyar.sort(key=lambda k: (-k.gehrai, k.banaa))
        return taiyar

    def _halat_sudharo(self):
        """
        जिन कामों की निर्भरता पूरी हो गई, उन्हें तैयार कर देता है.
        और जिनकी निर्भरता नाकाम हो गई, उन्हें छोड़ देता है.
        """
        for k in self.kaam.values():
            if k.halat != RUKA:
                continue

            koi_nakaam = False
            sab_hue = True
            for n_id in k.kis_par_nirbhar:
                n = self.kaam.get(n_id)
                if n is None:
                    continue
                if n.halat in (NAKAAM, CHHODA):
                    koi_nakaam = True
                    break
                if n.halat != HUA:
                    sab_hue = False

            if koi_nakaam:
                # जिस पर यह टिका था वो गिर गया — इसे चलाने का मतलब नहीं.
                # यहाँ चुपचाप छोड़ना ज़रूरी है, वरना यह काम हमेशा RUKA में
                # पड़ा रहेगा और सभा कभी ख़त्म नहीं होगी.
                k.halat = CHHODA
                k.galti = "जिस काम पर टिका था वो नाकाम हुआ"
            elif sab_hue:
                k.halat = TAIYAR

    def nirbhar_natije(self, kaam_id):
        """
        जिन कामों पर यह टिका है, उनके नतीजे लौटाता है.

        यही वो चीज़ है जो एक टुकड़े का काम दूसरे तक पहुँचाती है — सदस्य को
        सिर्फ़ अपना विवरण नहीं, नीचे वालों का नतीजा भी मिलना चाहिए.
        """
        k = self.kaam.get(kaam_id)
        if k is None:
            return []
        out = []
        for n_id in k.kis_par_nirbhar:
            n = self.kaam.get(n_id)
            if n is not None and n.halat == HUA:
                out.append({"vivaran": n.vivaran, "natija": n.natija})
        return out

    # -- नतीजा दर्ज करना ----------------------------------------------------------

    def shuru(self, kaam_id):
        k = self.kaam.get(kaam_id)
        if k:
            k.halat = CHAL_RAHA
            k.koshish += 1

    def hua(self, kaam_id, natija):
        k = self.kaam.get(kaam_id)
        if k:
            k.halat = HUA
            k.natija = natija
            k.hua_samay = time.time()

    def nakaam(self, kaam_id, galti, dobara=True):
        """
        काम नाकाम हुआ.

        dobara=True और दो से कम कोशिशें हुई हों तो वापस तैयार कर देता है.
        तीसरी कोशिश पर पक्का नाकाम.

        दो कोशिशें इसलिए कि पहली नाकामी अक्सर कोई अस्थायी बात होती है
        (जाल टूटा, समय ख़त्म हुआ). तीसरी बार तक जाओ तो साफ़ है कि काम में
        ही गड़बड़ है, कोशिश में नहीं.
        """
        k = self.kaam.get(kaam_id)
        if not k:
            return
        k.galti = galti
        if dobara and k.koshish < 2:
            k.halat = TAIYAR
        else:
            k.halat = NAKAAM

    # -- हाल ---------------------------------------------------------------------

    def poora_hua(self):
        """पूरी सभा ख़त्म हुई या नहीं."""
        self._halat_sudharo()
        for k in self.kaam.values():
            if k.halat in (RUKA, TAIYAR, CHAL_RAHA):
                return False
        return True

    def haal(self):
        ginti = {}
        for k in self.kaam.values():
            ginti[k.halat] = ginti.get(k.halat, 0) + 1
        return {"kul": len(self.kaam), "halat": ginti}

    def bachao(self, rasta):
        """पूरा जाल file में लिखता है, ताकि बीच में रुककर आगे बढ़ा जा सके."""
        d = {"kaam": [k.dict_me() for k in self.kaam.values()],
             "adhiktam_gehrai": self.adhiktam_gehrai,
             "adhiktam_kaam": self.adhiktam_kaam}
        temp = rasta + ".tmp"
        with open(temp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
        if os.path.exists(rasta):
            os.remove(rasta)
        os.rename(temp, rasta)

    @staticmethod
    def uthao(rasta):
        """file से जाल वापस बनाता है."""
        with open(rasta, "r", encoding="utf-8") as f:
            d = json.load(f)
        ks = Karyasuchi(d.get("adhiktam_gehrai", 3), d.get("adhiktam_kaam", 500))
        for kd in d.get("kaam", []):
            k = Kaam(kd["vivaran"], kd.get("kis_par_nirbhar"),
                     kd.get("gehrai", 0), kd.get("kaun_kare"),
                     kd.get("jaanch"))
            k.id = kd["id"]
            k.halat = kd.get("halat", TAIYAR)
            k.natija = kd.get("natija")
            k.galti = kd.get("galti", "")
            k.koshish = kd.get("koshish", 0)
            k.banaa = kd.get("banaa", time.time())
            k.hua_samay = kd.get("hua_samay")
            ks.kaam[k.id] = k
            ks.chhap_suchi[k.chhap()] = k.id
        return ks


# ---------------------------------------------------------------------------
# जाँच: python3 sabha/karyasuchi.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tempfile

    ks = Karyasuchi()

    a = Kaam("पहला काम")
    b = Kaam("दूसरा काम")
    ks.jodo(a)
    ks.jodo(b)
    c = Kaam("तीसरा काम", kis_par_nirbhar=[a.id, b.id])
    ks.jodo(c)

    taiyar = ks.taiyar_kaam()
    assert len(taiyar) == 2, "निर्भर काम भी तैयार दिखा"

    # दोहराव
    juda, vajah = ks.jodo(Kaam("पहला   काम"))     # जगह अलग, बात वही
    assert juda is False, "दोहराव पकड़ा नहीं गया"

    ks.shuru(a.id); ks.hua(a.id, "क का जवाब")
    assert len(ks.taiyar_kaam()) == 1, "अभी भी ख पर टिका है"
    ks.shuru(b.id); ks.hua(b.id, "ख का जवाब")
    taiyar = ks.taiyar_kaam()
    assert len(taiyar) == 1 and taiyar[0].id == c.id, "ग खुला नहीं"

    natije = ks.nirbhar_natije(c.id)
    assert len(natije) == 2 and natije[0]["natija"] == "क का जवाब"

    # ख़ुद बँटना
    ks2 = Karyasuchi(adhiktam_gehrai=2)
    m = Kaam("बड़ा काम")
    ks2.jodo(m)
    tukde = ks2.khud_baanto(m.id, ["टुकड़ा १", "टुकड़ा २", "टुकड़ा ३"])
    assert len(tukde) == 3
    assert ks2.kaam[m.id].halat == RUKA, "बाँटने के बाद मूल काम रुकना चाहिए"
    assert len(ks2.taiyar_kaam()) == 3

    # गहराई की सीमा
    gehra = Kaam("बहुत गहरा", gehrai=5)
    juda, vajah = ks2.jodo(gehra)
    assert juda is False and "गहराई" in vajah

    # निर्भरता नाकाम -> ऊपर वाला छूट जाए
    ks3 = Karyasuchi()
    x = Kaam("नीचे वाला"); ks3.jodo(x)
    y = Kaam("ऊपर वाला", kis_par_nirbhar=[x.id]); ks3.jodo(y)
    ks3.shuru(x.id); ks3.nakaam(x.id, "टूट गया", dobara=False)
    ks3._halat_sudharo()
    assert ks3.kaam[y.id].halat == CHHODA, "ऊपर वाला छोड़ा नहीं गया"
    assert ks3.poora_hua() is True, "सभा ख़त्म नहीं मानी गई"

    # बचाना और उठाना
    f = os.path.join(tempfile.mkdtemp(), "jaal.json")
    ks.bachao(f)
    wapas = Karyasuchi.uthao(f)
    assert len(wapas.kaam) == len(ks.kaam)
    assert wapas.kaam[c.id].halat == ks.kaam[c.id].halat

    print("कार्यसूची ठीक है — सारी जाँच पास.")
