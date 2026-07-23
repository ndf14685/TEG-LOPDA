"""Datos de los mapas jugables.

Formato: territorio -> (nombre visible, continente, vecinos).
Las fronteras son un mapa mundial aproximado "inspirado en el TEG", NO una
copia exacta del tablero oficial. Se validan simetría y conectividad en
tests; editar acá si el grupo quiere ajustar límites.
"""

from __future__ import annotations

# --- tactical-26: el mapa original del MVP -------------------------------

CONTINENTS_26 = {
    "south-america": ("América del Sur", 3),
    "north-america": ("América del Norte", 5),
    "europe": ("Europa", 5),
    "africa": ("África", 3),
    "asia": ("Asia", 7),
    "oceania": ("Oceanía", 2),
}

TERRITORIES_26 = {
    "territory-south-america-colombia": ("Colombia", "south-america", {"territory-south-america-brazil", "territory-south-america-peru", "territory-north-america-mexico"}),
    "territory-south-america-peru": ("Perú", "south-america", {"territory-south-america-argentina", "territory-south-america-brazil", "territory-south-america-chile", "territory-south-america-colombia"}),
    "territory-south-america-brazil": ("Brasil", "south-america", {"territory-south-america-argentina", "territory-south-america-colombia", "territory-south-america-peru"}),
    "territory-south-america-chile": ("Chile", "south-america", {"territory-south-america-argentina", "territory-south-america-peru"}),
    "territory-south-america-argentina": ("Argentina", "south-america", {"territory-south-america-brazil", "territory-south-america-chile", "territory-south-america-peru"}),
    "territory-north-america-mexico": ("México", "north-america", {"territory-south-america-colombia", "territory-north-america-usa"}),
    "territory-north-america-usa": ("EE. UU.", "north-america", {"territory-north-america-mexico", "territory-north-america-canada"}),
    "territory-north-america-canada": ("Canadá", "north-america", {"territory-north-america-usa", "territory-north-america-alaska", "territory-europe-uk"}),
    "territory-north-america-alaska": ("Alaska", "north-america", {"territory-north-america-canada", "territory-asia-kamchatka"}),
    "territory-europe-uk": ("Reino Unido", "europe", {"territory-north-america-canada", "territory-europe-france", "territory-europe-germany"}),
    "territory-europe-france": ("Francia", "europe", {"territory-europe-uk", "territory-europe-spain", "territory-europe-germany"}),
    "territory-europe-spain": ("España", "europe", {"territory-europe-france", "territory-africa-sahara"}),
    "territory-europe-germany": ("Alemania", "europe", {"territory-europe-france", "territory-europe-uk", "territory-europe-russia"}),
    "territory-europe-russia": ("Rusia", "europe", {"territory-europe-germany", "territory-asia-middle-east", "territory-asia-siberia"}),
    "territory-africa-sahara": ("Sáhara", "africa", {"territory-europe-spain", "territory-africa-egypt", "territory-africa-congo"}),
    "territory-africa-egypt": ("Egipto", "africa", {"territory-africa-sahara", "territory-africa-congo", "territory-asia-middle-east"}),
    "territory-africa-congo": ("Congo", "africa", {"territory-africa-sahara", "territory-africa-egypt", "territory-africa-south-africa"}),
    "territory-africa-south-africa": ("Sudáfrica", "africa", {"territory-africa-congo"}),
    "territory-asia-middle-east": ("Oriente Medio", "asia", {"territory-europe-russia", "territory-africa-egypt", "territory-asia-india"}),
    "territory-asia-india": ("India", "asia", {"territory-asia-middle-east", "territory-asia-china"}),
    "territory-asia-china": ("China", "asia", {"territory-asia-india", "territory-asia-siberia", "territory-asia-japan", "territory-australia-western"}),
    "territory-asia-siberia": ("Siberia", "asia", {"territory-europe-russia", "territory-asia-china", "territory-asia-kamchatka"}),
    "territory-asia-kamchatka": ("Kamchatka", "asia", {"territory-asia-siberia", "territory-asia-japan", "territory-north-america-alaska"}),
    "territory-asia-japan": ("Japón", "asia", {"territory-asia-china", "territory-asia-kamchatka"}),
    "territory-australia-western": ("Australia Occidental", "oceania", {"territory-australia-eastern", "territory-asia-china"}),
    "territory-australia-eastern": ("Australia Oriental", "oceania", {"territory-australia-western"}),
}

# --- world-50: mundo extendido -------------------------------------------

CONTINENTS_50 = {
    "south-america": ("América del Sur", 4),
    "north-america": ("América del Norte", 5),
    "europe": ("Europa", 5),
    "africa": ("África", 4),
    "asia": ("Asia", 7),
    "oceania": ("Oceanía", 2),
}


def _t(continent: str, slug: str) -> str:
    return f"territory-{continent}-{slug}"


# (slug, nombre, [vecinos como (continente, slug)])
_RAW_50: dict[str, list[tuple[str, str, list[tuple[str, str]]]]] = {
    "south-america": [
        ("colombia", "Colombia", [("south-america", "venezuela"), ("south-america", "peru"), ("south-america", "brazil"), ("north-america", "mexico")]),
        ("venezuela", "Venezuela", [("south-america", "colombia"), ("south-america", "brazil")]),
        ("peru", "Perú", [("south-america", "colombia"), ("south-america", "brazil"), ("south-america", "bolivia"), ("south-america", "chile")]),
        ("brazil", "Brasil", [("south-america", "colombia"), ("south-america", "venezuela"), ("south-america", "peru"), ("south-america", "bolivia"), ("south-america", "argentina"), ("south-america", "uruguay"), ("africa", "sahara")]),
        ("bolivia", "Bolivia", [("south-america", "peru"), ("south-america", "brazil"), ("south-america", "argentina"), ("south-america", "chile")]),
        ("chile", "Chile", [("south-america", "peru"), ("south-america", "bolivia"), ("south-america", "argentina"), ("oceania", "australia")]),
        ("argentina", "Argentina", [("south-america", "chile"), ("south-america", "bolivia"), ("south-america", "brazil"), ("south-america", "uruguay")]),
        ("uruguay", "Uruguay", [("south-america", "argentina"), ("south-america", "brazil")]),
    ],
    "north-america": [
        ("alaska", "Alaska", [("north-america", "yukon"), ("asia", "kamchatka")]),
        ("yukon", "Yukón", [("north-america", "alaska"), ("north-america", "canada"), ("north-america", "oregon")]),
        ("canada", "Canadá", [("north-america", "yukon"), ("north-america", "oregon"), ("north-america", "new-york"), ("north-america", "newfoundland")]),
        ("newfoundland", "Terranova", [("north-america", "canada"), ("north-america", "new-york"), ("north-america", "greenland")]),
        ("greenland", "Groenlandia", [("north-america", "newfoundland"), ("europe", "iceland")]),
        ("oregon", "Oregón", [("north-america", "yukon"), ("north-america", "canada"), ("north-america", "new-york"), ("north-america", "california")]),
        ("new-york", "Nueva York", [("north-america", "canada"), ("north-america", "newfoundland"), ("north-america", "oregon"), ("north-america", "california")]),
        ("california", "California", [("north-america", "oregon"), ("north-america", "new-york"), ("north-america", "mexico")]),
        ("mexico", "México", [("north-america", "california"), ("south-america", "colombia")]),
    ],
    "europe": [
        ("iceland", "Islandia", [("north-america", "greenland"), ("europe", "great-britain"), ("europe", "sweden")]),
        ("great-britain", "Gran Bretaña", [("europe", "iceland"), ("europe", "france"), ("europe", "germany")]),
        ("sweden", "Suecia", [("europe", "iceland"), ("europe", "russia"), ("europe", "germany")]),
        ("germany", "Alemania", [("europe", "great-britain"), ("europe", "sweden"), ("europe", "poland"), ("europe", "france"), ("europe", "italy")]),
        ("poland", "Polonia", [("europe", "germany"), ("europe", "russia"), ("asia", "turkey")]),
        ("russia", "Rusia", [("europe", "sweden"), ("europe", "poland"), ("asia", "turkey"), ("asia", "aral"), ("asia", "siberia")]),
        ("france", "Francia", [("europe", "great-britain"), ("europe", "germany"), ("europe", "spain"), ("europe", "italy")]),
        ("spain", "España", [("europe", "france"), ("africa", "sahara")]),
        ("italy", "Italia", [("europe", "france"), ("europe", "germany"), ("africa", "egypt")]),
    ],
    "africa": [
        ("sahara", "Sáhara", [("europe", "spain"), ("south-america", "brazil"), ("africa", "egypt"), ("africa", "nigeria")]),
        ("nigeria", "Nigeria", [("africa", "sahara"), ("africa", "zaire")]),
        ("egypt", "Egipto", [("africa", "sahara"), ("europe", "italy"), ("africa", "ethiopia"), ("asia", "arabia")]),
        ("ethiopia", "Etiopía", [("africa", "egypt"), ("africa", "kenya"), ("africa", "zaire")]),
        ("kenya", "Kenia", [("africa", "ethiopia"), ("africa", "zaire"), ("africa", "madagascar"), ("africa", "south-africa")]),
        ("zaire", "Zaire", [("africa", "nigeria"), ("africa", "ethiopia"), ("africa", "kenya"), ("africa", "south-africa")]),
        ("south-africa", "Sudáfrica", [("africa", "zaire"), ("africa", "kenya"), ("africa", "madagascar")]),
        ("madagascar", "Madagascar", [("africa", "kenya"), ("africa", "south-africa")]),
    ],
    "asia": [
        ("turkey", "Turquía", [("europe", "poland"), ("europe", "russia"), ("asia", "arabia"), ("asia", "iran")]),
        ("arabia", "Arabia", [("asia", "turkey"), ("africa", "egypt"), ("asia", "iran"), ("asia", "india")]),
        ("iran", "Irán", [("asia", "turkey"), ("asia", "arabia"), ("asia", "aral"), ("asia", "india")]),
        ("aral", "Aral", [("europe", "russia"), ("asia", "iran"), ("asia", "siberia"), ("asia", "china")]),
        ("india", "India", [("asia", "arabia"), ("asia", "iran"), ("asia", "china"), ("asia", "malaysia")]),
        ("china", "China", [("asia", "aral"), ("asia", "india"), ("asia", "malaysia"), ("asia", "gobi"), ("asia", "siberia"), ("asia", "japan")]),
        ("gobi", "Gobi", [("asia", "china"), ("asia", "mongolia"), ("asia", "siberia")]),
        ("mongolia", "Mongolia", [("asia", "gobi"), ("asia", "siberia")]),
        ("siberia", "Siberia", [("europe", "russia"), ("asia", "aral"), ("asia", "china"), ("asia", "gobi"), ("asia", "mongolia"), ("asia", "kamchatka")]),
        ("kamchatka", "Kamchatka", [("asia", "siberia"), ("asia", "japan"), ("north-america", "alaska")]),
        ("japan", "Japón", [("asia", "china"), ("asia", "kamchatka")]),
        ("malaysia", "Malasia", [("asia", "india"), ("asia", "china"), ("oceania", "borneo"), ("oceania", "sumatra")]),
    ],
    "oceania": [
        ("sumatra", "Sumatra", [("asia", "malaysia"), ("oceania", "java")]),
        ("borneo", "Borneo", [("asia", "malaysia"), ("oceania", "australia")]),
        ("java", "Java", [("oceania", "sumatra"), ("oceania", "australia")]),
        ("australia", "Australia", [("oceania", "borneo"), ("oceania", "java"), ("south-america", "chile")]),
    ],
}


def _build_50() -> dict[str, tuple[str, str, set[str]]]:
    out: dict[str, tuple[str, str, set[str]]] = {}
    for continent, items in _RAW_50.items():
        for slug, name, neighbors in items:
            out[_t(continent, slug)] = (
                name,
                continent,
                {_t(c, s) for c, s in neighbors},
            )
    return out


TERRITORIES_50 = _build_50()

# --- mega-100: cada país del mundo-50 dividido en Norte y Sur -------------
# Vecinos: la otra mitad del mismo país + las dos mitades de cada vecino
# original. Bonus de continente duplicado (hay el doble de países).

CONTINENTS_100 = {cid: (name, bonus * 2) for cid, (name, bonus) in CONTINENTS_50.items()}


def _build_100() -> dict[str, tuple[str, str, set[str]]]:
    out: dict[str, tuple[str, str, set[str]]] = {}
    for tid, (name, continent, neighbors) in TERRITORIES_50.items():
        for half, label in (("north", "Norte"), ("south", "Sur")):
            other = f"{tid}-south" if half == "north" else f"{tid}-north"
            linked = {other}
            for nb in neighbors:
                linked.add(f"{nb}-north")
                linked.add(f"{nb}-south")
            out[f"{tid}-{half}"] = (f"{name} {label}", continent, linked)
    return out


TERRITORIES_100 = _build_100()

MAPS = {
    "tactical-26": (CONTINENTS_26, TERRITORIES_26),
    "world-50": (CONTINENTS_50, TERRITORIES_50),
    "mega-100": (CONTINENTS_100, TERRITORIES_100),
}
