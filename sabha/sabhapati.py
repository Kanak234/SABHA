# -*- coding: utf-8 -*-
"""
सभापति (SABHAPATI) — सभा का अध्यक्ष.

यह क्या है:
    वो एक जगह जहाँ बाक़ी सब जुड़ते हैं. काम बाँटता है, सदस्यों को देता है,
    नतीजे इकट्ठे करता है, और आख़िर में एक जवाब बनाता है.

    तुम सिर्फ़ इससे बात करते हो. सदस्यों से सीधे नहीं.

एक चक्कर में क्या होता है:
    1. तैयार कामों की सूची उठाओ (कार्यसूची से)
    2. हर काम के लिए सही सदस्य चुनो
    3. रक्षा से पूछो — इसे काम देना चाहिए या नहीं
    4. सदस्य से जवाब लो
    5. जवाब जाँचो (पहले पक्के नियमों से, फिर ज़रूरत हो तो सदस्य से)
    6. नतीजा दर्ज करो, डाकिया चलाओ
    7. जब तक कुछ बचा है, दोहराओ

जाँच का क्रम — यही सबसे ज़रूरी सोच है:
    पहले पक्की जाँच (क्या file बनी? क्या code चला? क्या URL खुला?).
    यह मुफ़्त है, तुरंत है, और हमेशा सही है.

    सदस्य से जाँच सिर्फ़ तब जब सवाल का जवाब राय हो. और तब भी जाँचने वाला
    अलग परिवार का हो — qwen का काम qwen से मत जँचवाओ, क्योंकि उन दोनों
    की ग़लतियाँ एक जैसी होंगी और वो अपनी ही अंधी जगह पर अंधा रहेगा.
"""

import os
import time
from typing import Any, Dict, List, Optional

from karyasuchi import (CHHODA, HUA, NAKAAM, TAIYAR, Kaam, Karyasuchi)
from nireekshan import Nireekshak
from raksha import BAANDHO, ROKO, THEEK, TOKO, Raksha
from sadasya import Sadasya
from sandesh import KAAM, NATIJA, Dakkhana, Sandesh


class Sabhapati(object):
    """सभा का अध्यक्ष."""

    def __init__(self, jad, sadasya_suchi, adhiktam_gehrai=3,
                 adhiktam_kaam=200, apne_aap_manzoori=False):
        """
        jad           = SABHA folder
        sadasya_suchi = Sadasya objects की सूची
        """
        self.jad = jad
        self.sadasya = {s.naam: s for s in sadasya_suchi}

        self.nireekshak = Nireekshak(os.path.join(jad, "bahi"))
        self.raksha = Raksha(self.nireekshak, apne_aap_manzoori)
        self.dakkhana = Dakkhana(os.path.join(jad, "sabha-kaksh"))
        self.karya = Karyasuchi(adhiktam_gehrai, adhiktam_kaam)

        for naam in self.sadasya:
            self.dakkhana.dibba_banao(naam)
            self.raksha.budget_do(naam)
        self.dakkhana.dibba_banao("sabhapati")

        self.ruke_hue = set()      # जिन सदस्यों को रक्षा ने रोक दिया

    # -- सदस्यों की जाँच ----------------------------------------------------------

    def sadasya_jaancho(self):
        """
        सभा शुरू करने से पहले हर सदस्य से पूछता है कि वो ज़िंदा है या नहीं.

        यह पहले करना ज़रूरी है. दस मिनट काम चलाने के बाद पता चले कि Ollama
        बंद था — यह सबसे चिढ़ाने वाली बात होती है, और होती अक्सर है.
        """
        theek = []
        gadbad = []
        for naam, s in self.sadasya.items():
            zinda, vajah = s.zinda_hai()
            if zinda:
                theek.append(naam)
            else:
                gadbad.append((naam, vajah))
        return theek, gadbad

    # -- काम बाँटना ---------------------------------------------------------------

    def kaam_lo(self, mool_kaam, tukde=None):
        """
        मुख्य काम लेता है और उसे टुकड़ों में डालता है.

        tukde = अगर तुमने ख़ुद बाँटकर दिया है तो वो सूची.
                None दो तो सभापति पहले सदस्य से बँटवाएगा.
        """
        self.nireekshak.darj("sabhapati", "sabha-shuru", {"kaam": mool_kaam})

        mool = Kaam(mool_kaam)
        self.karya.jodo(mool)

        if tukde is None:
            tukde = self._banto_poochho(mool_kaam)

        if tukde:
            bane = self.karya.khud_baanto(mool.id, tukde)
            self.nireekshak.darj("sabhapati", "kaam-banta",
                                 {"kitne": len(bane), "tukde": tukde})
        return mool

    def _banto_poochho(self, kaam):
        """
        पहले उपलब्ध सदस्य से पूछता है कि इस काम को कैसे बाँटें.

        जान-बूझकर कहा गया है कि 3 से 12 टुकड़े बनाओ. वजह — छोड़ दो तो
        model या तो दो टुकड़े बनाता है (बेकार) या तीस (जिनमें से बीस
        एक ही बात होती है). यह सीमा उसे सोचने पर मजबूर करती है कि
        सचमुच अलग-अलग हिस्से कौन से हैं.
        """
        koi = self._koi_sadasya()
        if koi is None:
            return []

        sawal = (
            "इस काम को अलग-अलग हिस्सों में बाँटो. हर हिस्सा अपने आप में "
            "पूरा हो और दूसरों से अलग हो.\n\n"
            "काम: " + kaam + "\n\n"
            "3 से 12 हिस्से बनाओ — उतने ही जितने इस काम में सचमुच हैं. "
            "हर हिस्सा एक लाइन में लिखो, शुरू में '- ' लगाकर. "
            "और कुछ मत लिखो."
        )
        r = koi.poochho(sawal)
        self.raksha.kharch_darj(koi.naam, r["akshar"], r["second"])
        if not r["safal"]:
            return []

        tukde = []
        for line in r["jawab"].split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                t = line[2:].strip()
                if t:
                    tukde.append(t)
        return tukde[:12]

    def _koi_sadasya(self):
        for naam, s in self.sadasya.items():
            if naam not in self.ruke_hue:
                return s
        return None

    def _sadasya_chuno(self, kaam):
        """
        इस काम के लिए कौन सा सदस्य.

        अगर काम में किसी का नाम लिखा है तो वही. वरना जिसके डिब्बे में
        सबसे कम पड़ा है — यानी जो सबसे खाली है.

        यह सादा तरीक़ा है और जान-बूझकर सादा रखा है. सदस्य चुनने के लिए
        model से पूछना महँगा भी है और भरोसेमंद भी नहीं. जब तक साफ़ न दिखे
        कि इससे नतीजा बेहतर होता है, यही ठीक है.
        """
        if kaam.kaun_kare and kaam.kaun_kare in self.sadasya:
            if kaam.kaun_kare not in self.ruke_hue:
                return self.sadasya[kaam.kaun_kare]

        khali = None
        kam = None
        for naam, s in self.sadasya.items():
            if naam in self.ruke_hue:
                continue
            bhaar = self.dakkhana.kitne_pade_hain(naam)
            if kam is None or bhaar < kam:
                kam = bhaar
                khali = s
        return khali

    # -- असली चक्कर ---------------------------------------------------------------

    def chalao(self, adhiktam_chakkar=100, dikhao=True):
        """
        सभा चलाता है जब तक काम बचा है या चक्कर ख़त्म न हो जाएँ.

        adhiktam_chakkar एक पक्की सीमा है. बिना इसके किसी गड़बड़ में यह
        हमेशा चलता रह सकता है — और ऐसी गड़बड़ रात को पता चलती है, सुबह
        मशीन गर्म मिलती है.
        """
        chakkar = 0
        while chakkar < adhiktam_chakkar:
            chakkar += 1

            taiyar = self.karya.taiyar_kaam()
            if not taiyar:
                if self.karya.poora_hua():
                    break
                # कुछ तैयार नहीं पर सभा ख़त्म भी नहीं — सब रुके हुए हैं.
                # यह गतिरोध है; आगे चलने का कोई रास्ता नहीं.
                self.nireekshak.darj("sabhapati", "gatirodh",
                                     self.karya.haal())
                break

            kaam = taiyar[0]
            s = self._sadasya_chuno(kaam)
            if s is None:
                self.nireekshak.darj("sabhapati", "koi-sadasya-nahi",
                                     {"kaam": kaam.id})
                self.karya.nakaam(kaam.id, "कोई सदस्य बचा नहीं", dobara=False)
                continue

            # रक्षा से पूछो
            sidhi, vajah = self.raksha.lagam(s.naam)
            if sidhi == ROKO:
                self.ruke_hue.add(s.naam)
                self.nireekshak.darj("raksha", "sadasya-roka",
                                     {"sadasya": s.naam, "vajah": vajah})
                if dikhao:
                    print("  [रोका] %s — %s" % (s.naam, vajah))
                continue
            if sidhi in (TOKO, BAANDHO) and dikhao:
                print("  [%s] %s — %s" % (sidhi, s.naam, vajah))

            self._ek_kaam(kaam, s, dikhao)
            self.dakkhana.baanto()

        self.nireekshak.darj("sabhapati", "sabha-khatam",
                             {"chakkar": chakkar, "haal": self.karya.haal()})
        return self.karya.haal()

    def _ek_kaam(self, kaam, s, dikhao):
        """एक काम एक सदस्य से करवाता है."""
        self.karya.shuru(kaam.id)
        self.raksha.naya_kaam(s.naam)

        if dikhao:
            print("  %s -> %s" % (s.naam, kaam.vivaran[:58]))

        # नीचे वालों के नतीजे साथ भेजो — बिना इसके सदस्य अंधेरे में काम करेगा
        sandarbh = ""
        niche = self.karya.nirbhar_natije(kaam.id)
        if niche:
            hisse = ["पहले जो पता चला:"]
            for n in niche:
                hisse.append("- %s: %s" % (n["vivaran"],
                                           str(n["natija"])[:800]))
            sandarbh = "\n".join(hisse)

        self.dakkhana.bhejo(Sandesh("sabhapati", s.naam, KAAM,
                                    kaam.vivaran, sutra=kaam.id))

        r = s.poochho(kaam.vivaran, sandarbh)
        self.raksha.kharch_darj(s.naam, r["akshar"], r["second"])
        self.nireekshak.darj(s.naam, "natija-aaya", {
            "kaam": kaam.id, "akshar": r["akshar"],
            "second": round(r["second"], 2), "safal": r["safal"],
            "galti": r["galti"],
        })

        if not r["safal"]:
            self.karya.nakaam(kaam.id, r["galti"])
            self.raksha.lagam(s.naam, safal=False)
            if dikhao:
                print("     नाकाम: " + r["galti"][:70])
            return

        # जाँच — पहले पक्की, फिर ज़रूरत हो तो राय वाली
        theek, vajah = self._natija_jaancho(kaam, r["jawab"])
        if not theek:
            self.karya.nakaam(kaam.id, vajah)
            self.raksha.lagam(s.naam, natija=r["jawab"], safal=False)
            if dikhao:
                print("     जाँच में फेल: " + vajah[:70])
            return

        self.karya.hua(kaam.id, r["jawab"])
        self.raksha.lagam(s.naam, natija=r["jawab"], safal=True)
        self.dakkhana.bhejo(Sandesh(s.naam, "sabhapati", NATIJA,
                                    "हो गया", {"natija": r["jawab"][:2000]},
                                    sutra=kaam.id))

    def _natija_jaancho(self, kaam, jawab):
        """
        नतीजा सही है या नहीं.

        सारी जाँचें पक्की हैं — इनमें कोई model नहीं चलता. यही असली बात है.
        काम की 'jaanch' में जो लिखा हो, वही यहाँ परखा जाता है:

            {"kam_se_kam": 100}          -> कम से कम इतने अक्षर
            {"shabd_hone_chahiye": [..]} -> ये शब्द होने चाहिए
            {"file_bane": "रास्ता"}       -> यह file बननी चाहिए
            {"json_ho": true}            -> जवाब वैध JSON हो

        फ़ाइल बनी या नहीं — यह जाँच model से पूछने से हज़ार गुना बेहतर है.
        model कह सकता है "हाँ बना दी"; os.path.exists झूठ नहीं बोलता.
        """
        j = kaam.jaanch or {}

        if not jawab or not jawab.strip():
            return False, "जवाब ख़ाली है"

        kam = j.get("kam_se_kam")
        if kam and len(jawab.strip()) < kam:
            return False, "जवाब बहुत छोटा (%d < %d अक्षर)" % (
                len(jawab.strip()), kam)

        shabd = j.get("shabd_hone_chahiye")
        if shabd:
            nahi = [w for w in shabd if w.lower() not in jawab.lower()]
            if nahi:
                return False, "ये शब्द नहीं मिले: " + ", ".join(nahi[:3])

        f = j.get("file_bane")
        if f and not os.path.exists(f):
            return False, "file बनी नहीं: " + f

        if j.get("json_ho"):
            import json as _j
            saaf = jawab.strip()
            # model अक्सर JSON को ``` में लपेट देता है — वो हटा दो
            if saaf.startswith("```"):
                saaf = saaf.split("```")[1] if "```" in saaf[3:] else saaf[3:]
                if saaf.startswith("json"):
                    saaf = saaf[4:]
            try:
                _j.loads(saaf.strip())
            except ValueError as e:
                return False, "वैध JSON नहीं: " + str(e)[:60]

        return True, ""

    # -- आख़िरी जवाब -----------------------------------------------------------

    def jawab_banao(self):
        """सारे पूरे हुए कामों को जोड़कर एक जवाब बनाता है."""
        hue = [k for k in self.karya.kaam.values() if k.halat == HUA]
        hue.sort(key=lambda k: (k.gehrai, k.banaa))

        hisse = []
        for k in hue:
            if k.natija:
                hisse.append("## " + k.vivaran + "\n\n" + str(k.natija))
        return "\n\n".join(hisse)

    def haal_chhapo(self):
        """सभा का हाल परदे पर."""
        h = self.karya.haal()
        print()
        print("  काम: %d कुल" % h["kul"])
        for halat, ginti in sorted(h["halat"].items()):
            print("     %-12s %d" % (halat, ginti))
        print()
        print("  सदस्यों का हिसाब:")
        for b in self.raksha.haal():
            print("     %-12s %6d अक्षर  %6.1f सेकंड  %3d बार  (बचा %.0f%%)" % (
                b["naam"], b["akshar"], b["second"], b["bulaya"],
                b["bacha"] * 100))
        if self.ruke_hue:
            print()
            print("  रोके गए: " + ", ".join(sorted(self.ruke_hue)))

    def band(self):
        self.nireekshak.band()
