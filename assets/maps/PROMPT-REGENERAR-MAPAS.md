# Prompt para regenerar los mapas SVG (pegar en otra IA)

Copiar todo lo que sigue y pegarlo en la IA de arte/código que vaya a dibujar el mapa.

---

Necesito que generes un **archivo SVG completo** de un mapa de guerra por territorios
(estilo TEG/Risk) para un juego web. El SVG que te paso de referencia funciona pero los
países son cuadriláteros feos; quiero **formas orgánicas de mapa verdadero** (costas
irregulares, países que encastran entre sí como un mapa real estilizado), manteniendo
EXACTAMENTE el contrato técnico de abajo porque el juego lo consume de forma programática.

## Contrato técnico OBLIGATORIO (si no se cumple, el juego se rompe)

1. Raíz: `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2560 1440" id="map-base-tactical-50-001">`.
2. Cada país es UN `<path>` con:
   - `class="territory"` (exactamente esa clase)
   - `id` EXACTO de la lista de abajo (no inventar, no traducir, no renombrar)
3. Los países vecinos según la tabla de fronteras deben **tocarse o estar visualmente
   conectados** (si hay mar de por medio, dibujar una línea punteada de conexión con
   `class="sea-route"`, decorativa, `pointer-events: none`).
4. Cada país lleva su nombre en un `<text class="territory-label">` posicionado en la
   **mitad superior** del país (la mitad inferior la usa el juego para inyectar la
   insignia de tropas — dejarla despejada).
5. Cada continente se agrupa en `<g id="continent-<id>">` con un
   `<text class="continent-title">` con su nombre.
6. Conservar el `<style>` del archivo de referencia dentro de `<defs>` (clases
   `.territory`, `.territory:hover`, `.territory.selected`, `.territory.attack-source`,
   `.territory.attack-target`, `.territory-label`, `.continent-title`). Se puede
   mejorar la estética de los valores pero NO renombrar clases.
7. El fill de `.territory` debe quedar en un color neutro oscuro: el juego lo pisa en
   runtime con el color de cada jugador vía `path.style.fill`. No pintar países con
   colores propios ni gradientes en el fill del path.
8. Sin imágenes externas, sin `<script>`, sin fuentes remotas. Un solo archivo SVG
   autocontenido. Tamaño objetivo < 200 KB.
9. Fondo océano incluido dentro del SVG (gradiente azul oscuro + retícula sutil ya
   existe en la referencia; se puede mejorar).

## Los 26 territorios (id exacto → nombre visible)

### continent-south-america — América del Sur
- territory-south-america-colombia → Colombia
- territory-south-america-peru → Perú
- territory-south-america-brazil → Brasil
- territory-south-america-chile → Chile
- territory-south-america-argentina → Argentina

### continent-north-america — América del Norte
- territory-north-america-mexico → México
- territory-north-america-usa → EE. UU.
- territory-north-america-canada → Canadá
- territory-north-america-alaska → Alaska

### continent-europe — Europa
- territory-europe-uk → Reino Unido
- territory-europe-france → Francia
- territory-europe-spain → España
- territory-europe-germany → Alemania
- territory-europe-russia → Rusia

### continent-africa — África
- territory-africa-sahara → Sáhara
- territory-africa-egypt → Egipto
- territory-africa-congo → Congo
- territory-africa-south-africa → Sudáfrica

### continent-asia — Asia
- territory-asia-middle-east → Oriente Medio
- territory-asia-india → India
- territory-asia-china → China
- territory-asia-siberia → Siberia
- territory-asia-kamchatka → Kamchatka
- territory-asia-japan → Japón

### continent-oceania — Oceanía
- territory-australia-western → Australia Occidental
- territory-australia-eastern → Australia Oriental

## Fronteras (deben verse conectadas en el dibujo)

- colombia ↔ brazil, peru, mexico
- peru ↔ argentina, brazil, chile, colombia
- brazil ↔ argentina, colombia, peru
- chile ↔ argentina, peru
- mexico ↔ colombia, usa
- usa ↔ mexico, canada
- canada ↔ usa, alaska, uk (ruta marítima)
- alaska ↔ canada, kamchatka (ruta marítima, cruza el borde del mapa si queda lindo)
- uk ↔ canada (marítima), france, germany
- france ↔ uk, spain, germany
- spain ↔ france, sahara (estrecho)
- germany ↔ france, uk, russia
- russia ↔ germany, middle-east, siberia
- sahara ↔ spain, egypt, congo
- egypt ↔ sahara, congo, middle-east
- congo ↔ sahara, egypt, south-africa
- south-africa ↔ congo
- middle-east ↔ russia, egypt, india
- india ↔ middle-east, china
- china ↔ india, siberia, japan (marítima), australia-western (marítima)
- siberia ↔ russia, china, kamchatka
- kamchatka ↔ siberia, japan (marítima), alaska (marítima)
- japan ↔ china, kamchatka (marítimas)
- australia-western ↔ australia-eastern, china (marítima)
- australia-eastern ↔ australia-western

## Dirección de arte

- Mapa mundial estilizado tipo "war room": planisferio reconocible pero simplificado,
  costas con curvas orgánicas (usar curvas Bézier en los paths, no solo rectas).
- Paleta base oscura (el océano ya es azul noche); los países en gris azulado neutro.
- Estética coherente con un juego de estrategia entre amigos: seria pero con carácter.
- Los países chicos (Reino Unido, Japón, España) deben ser lo bastante grandes para
  contener el nombre y una insignia circular de ~90px de diámetro del viewBox.

## Entregable

Tres variantes (se pueden pedir de a una):
- `map-base-tactical-26-001.svg` (`id="map-base-tactical-26-001"`): los 26 países listados arriba. YA EXISTE una versión aceptable.
- `map-base-tactical-50-001.svg` y `map-base-tactical-100-001.svg`: usar las listas de IDs y fronteras de los apéndices de abajo. Son las que faltan dibujar.

# Apéndices: listas de IDs para las variantes 50 y 100

## Mapa de 50 países (`map-base-tactical-50-001.svg`, `id="map-base-tactical-50-001"`)

### continent-south-america — América del Sur (bonus 4)
- territory-south-america-argentina → Argentina
- territory-south-america-bolivia → Bolivia
- territory-south-america-brazil → Brasil
- territory-south-america-chile → Chile
- territory-south-america-colombia → Colombia
- territory-south-america-peru → Perú
- territory-south-america-uruguay → Uruguay
- territory-south-america-venezuela → Venezuela

### continent-north-america — América del Norte (bonus 5)
- territory-north-america-alaska → Alaska
- territory-north-america-california → California
- territory-north-america-canada → Canadá
- territory-north-america-greenland → Groenlandia
- territory-north-america-mexico → México
- territory-north-america-new-york → Nueva York
- territory-north-america-newfoundland → Terranova
- territory-north-america-oregon → Oregón
- territory-north-america-yukon → Yukón

### continent-europe — Europa (bonus 5)
- territory-europe-france → Francia
- territory-europe-germany → Alemania
- territory-europe-great-britain → Gran Bretaña
- territory-europe-iceland → Islandia
- territory-europe-italy → Italia
- territory-europe-poland → Polonia
- territory-europe-russia → Rusia
- territory-europe-spain → España
- territory-europe-sweden → Suecia

### continent-africa — África (bonus 4)
- territory-africa-egypt → Egipto
- territory-africa-ethiopia → Etiopía
- territory-africa-kenya → Kenia
- territory-africa-madagascar → Madagascar
- territory-africa-nigeria → Nigeria
- territory-africa-sahara → Sáhara
- territory-africa-south-africa → Sudáfrica
- territory-africa-zaire → Zaire

### continent-asia — Asia (bonus 7)
- territory-asia-arabia → Arabia
- territory-asia-aral → Aral
- territory-asia-china → China
- territory-asia-gobi → Gobi
- territory-asia-india → India
- territory-asia-iran → Irán
- territory-asia-japan → Japón
- territory-asia-kamchatka → Kamchatka
- territory-asia-malaysia → Malasia
- territory-asia-mongolia → Mongolia
- territory-asia-siberia → Siberia
- territory-asia-turkey → Turquía

### continent-oceania — Oceanía (bonus 2)
- territory-oceania-australia → Australia
- territory-oceania-borneo → Borneo
- territory-oceania-java → Java
- territory-oceania-sumatra → Sumatra

Fronteras (todas deben verse conectadas; las de distinto continente pueden ser rutas marítimas):

- territory-africa-egypt ↔ territory-africa-ethiopia
- territory-africa-egypt ↔ territory-africa-sahara
- territory-africa-egypt ↔ territory-asia-arabia
- territory-africa-egypt ↔ territory-europe-italy
- territory-africa-ethiopia ↔ territory-africa-kenya
- territory-africa-ethiopia ↔ territory-africa-zaire
- territory-africa-kenya ↔ territory-africa-madagascar
- territory-africa-kenya ↔ territory-africa-south-africa
- territory-africa-kenya ↔ territory-africa-zaire
- territory-africa-madagascar ↔ territory-africa-south-africa
- territory-africa-nigeria ↔ territory-africa-sahara
- territory-africa-nigeria ↔ territory-africa-zaire
- territory-africa-sahara ↔ territory-europe-spain
- territory-africa-sahara ↔ territory-south-america-brazil
- territory-africa-south-africa ↔ territory-africa-zaire
- territory-asia-arabia ↔ territory-asia-india
- territory-asia-arabia ↔ territory-asia-iran
- territory-asia-arabia ↔ territory-asia-turkey
- territory-asia-aral ↔ territory-asia-china
- territory-asia-aral ↔ territory-asia-iran
- territory-asia-aral ↔ territory-asia-siberia
- territory-asia-aral ↔ territory-europe-russia
- territory-asia-china ↔ territory-asia-gobi
- territory-asia-china ↔ territory-asia-india
- territory-asia-china ↔ territory-asia-japan
- territory-asia-china ↔ territory-asia-malaysia
- territory-asia-china ↔ territory-asia-siberia
- territory-asia-gobi ↔ territory-asia-mongolia
- territory-asia-gobi ↔ territory-asia-siberia
- territory-asia-india ↔ territory-asia-iran
- territory-asia-india ↔ territory-asia-malaysia
- territory-asia-iran ↔ territory-asia-turkey
- territory-asia-japan ↔ territory-asia-kamchatka
- territory-asia-kamchatka ↔ territory-asia-siberia
- territory-asia-kamchatka ↔ territory-north-america-alaska
- territory-asia-malaysia ↔ territory-oceania-borneo
- territory-asia-malaysia ↔ territory-oceania-sumatra
- territory-asia-mongolia ↔ territory-asia-siberia
- territory-asia-siberia ↔ territory-europe-russia
- territory-asia-turkey ↔ territory-europe-poland
- territory-asia-turkey ↔ territory-europe-russia
- territory-europe-france ↔ territory-europe-germany
- territory-europe-france ↔ territory-europe-great-britain
- territory-europe-france ↔ territory-europe-italy
- territory-europe-france ↔ territory-europe-spain
- territory-europe-germany ↔ territory-europe-great-britain
- territory-europe-germany ↔ territory-europe-italy
- territory-europe-germany ↔ territory-europe-poland
- territory-europe-germany ↔ territory-europe-sweden
- territory-europe-great-britain ↔ territory-europe-iceland
- territory-europe-iceland ↔ territory-europe-sweden
- territory-europe-iceland ↔ territory-north-america-greenland
- territory-europe-poland ↔ territory-europe-russia
- territory-europe-russia ↔ territory-europe-sweden
- territory-north-america-alaska ↔ territory-north-america-yukon
- territory-north-america-california ↔ territory-north-america-mexico
- territory-north-america-california ↔ territory-north-america-new-york
- territory-north-america-california ↔ territory-north-america-oregon
- territory-north-america-canada ↔ territory-north-america-new-york
- territory-north-america-canada ↔ territory-north-america-newfoundland
- territory-north-america-canada ↔ territory-north-america-oregon
- territory-north-america-canada ↔ territory-north-america-yukon
- territory-north-america-greenland ↔ territory-north-america-newfoundland
- territory-north-america-mexico ↔ territory-south-america-colombia
- territory-north-america-new-york ↔ territory-north-america-newfoundland
- territory-north-america-new-york ↔ territory-north-america-oregon
- territory-north-america-oregon ↔ territory-north-america-yukon
- territory-oceania-australia ↔ territory-oceania-borneo
- territory-oceania-australia ↔ territory-oceania-java
- territory-oceania-australia ↔ territory-south-america-chile
- territory-oceania-java ↔ territory-oceania-sumatra
- territory-south-america-argentina ↔ territory-south-america-bolivia
- territory-south-america-argentina ↔ territory-south-america-brazil
- territory-south-america-argentina ↔ territory-south-america-chile
- territory-south-america-argentina ↔ territory-south-america-uruguay
- territory-south-america-bolivia ↔ territory-south-america-brazil
- territory-south-america-bolivia ↔ territory-south-america-chile
- territory-south-america-bolivia ↔ territory-south-america-peru
- territory-south-america-brazil ↔ territory-south-america-colombia
- territory-south-america-brazil ↔ territory-south-america-peru
- territory-south-america-brazil ↔ territory-south-america-uruguay
- territory-south-america-brazil ↔ territory-south-america-venezuela
- territory-south-america-chile ↔ territory-south-america-peru
- territory-south-america-colombia ↔ territory-south-america-peru
- territory-south-america-colombia ↔ territory-south-america-venezuela


## Mega mapa de 100 territorios (`map-base-tactical-100-001.svg`, `id="map-base-tactical-100-001"`)

### continent-south-america — América del Sur (bonus 8)
- territory-south-america-argentina-north → Argentina Norte
- territory-south-america-argentina-south → Argentina Sur
- territory-south-america-bolivia-north → Bolivia Norte
- territory-south-america-bolivia-south → Bolivia Sur
- territory-south-america-brazil-north → Brasil Norte
- territory-south-america-brazil-south → Brasil Sur
- territory-south-america-chile-north → Chile Norte
- territory-south-america-chile-south → Chile Sur
- territory-south-america-colombia-north → Colombia Norte
- territory-south-america-colombia-south → Colombia Sur
- territory-south-america-peru-north → Perú Norte
- territory-south-america-peru-south → Perú Sur
- territory-south-america-uruguay-north → Uruguay Norte
- territory-south-america-uruguay-south → Uruguay Sur
- territory-south-america-venezuela-north → Venezuela Norte
- territory-south-america-venezuela-south → Venezuela Sur

### continent-north-america — América del Norte (bonus 10)
- territory-north-america-alaska-north → Alaska Norte
- territory-north-america-alaska-south → Alaska Sur
- territory-north-america-california-north → California Norte
- territory-north-america-california-south → California Sur
- territory-north-america-canada-north → Canadá Norte
- territory-north-america-canada-south → Canadá Sur
- territory-north-america-greenland-north → Groenlandia Norte
- territory-north-america-greenland-south → Groenlandia Sur
- territory-north-america-mexico-north → México Norte
- territory-north-america-mexico-south → México Sur
- territory-north-america-new-york-north → Nueva York Norte
- territory-north-america-new-york-south → Nueva York Sur
- territory-north-america-newfoundland-north → Terranova Norte
- territory-north-america-newfoundland-south → Terranova Sur
- territory-north-america-oregon-north → Oregón Norte
- territory-north-america-oregon-south → Oregón Sur
- territory-north-america-yukon-north → Yukón Norte
- territory-north-america-yukon-south → Yukón Sur

### continent-europe — Europa (bonus 10)
- territory-europe-france-north → Francia Norte
- territory-europe-france-south → Francia Sur
- territory-europe-germany-north → Alemania Norte
- territory-europe-germany-south → Alemania Sur
- territory-europe-great-britain-north → Gran Bretaña Norte
- territory-europe-great-britain-south → Gran Bretaña Sur
- territory-europe-iceland-north → Islandia Norte
- territory-europe-iceland-south → Islandia Sur
- territory-europe-italy-north → Italia Norte
- territory-europe-italy-south → Italia Sur
- territory-europe-poland-north → Polonia Norte
- territory-europe-poland-south → Polonia Sur
- territory-europe-russia-north → Rusia Norte
- territory-europe-russia-south → Rusia Sur
- territory-europe-spain-north → España Norte
- territory-europe-spain-south → España Sur
- territory-europe-sweden-north → Suecia Norte
- territory-europe-sweden-south → Suecia Sur

### continent-africa — África (bonus 8)
- territory-africa-egypt-north → Egipto Norte
- territory-africa-egypt-south → Egipto Sur
- territory-africa-ethiopia-north → Etiopía Norte
- territory-africa-ethiopia-south → Etiopía Sur
- territory-africa-kenya-north → Kenia Norte
- territory-africa-kenya-south → Kenia Sur
- territory-africa-madagascar-north → Madagascar Norte
- territory-africa-madagascar-south → Madagascar Sur
- territory-africa-nigeria-north → Nigeria Norte
- territory-africa-nigeria-south → Nigeria Sur
- territory-africa-sahara-north → Sáhara Norte
- territory-africa-sahara-south → Sáhara Sur
- territory-africa-south-africa-north → Sudáfrica Norte
- territory-africa-south-africa-south → Sudáfrica Sur
- territory-africa-zaire-north → Zaire Norte
- territory-africa-zaire-south → Zaire Sur

### continent-asia — Asia (bonus 14)
- territory-asia-arabia-north → Arabia Norte
- territory-asia-arabia-south → Arabia Sur
- territory-asia-aral-north → Aral Norte
- territory-asia-aral-south → Aral Sur
- territory-asia-china-north → China Norte
- territory-asia-china-south → China Sur
- territory-asia-gobi-north → Gobi Norte
- territory-asia-gobi-south → Gobi Sur
- territory-asia-india-north → India Norte
- territory-asia-india-south → India Sur
- territory-asia-iran-north → Irán Norte
- territory-asia-iran-south → Irán Sur
- territory-asia-japan-north → Japón Norte
- territory-asia-japan-south → Japón Sur
- territory-asia-kamchatka-north → Kamchatka Norte
- territory-asia-kamchatka-south → Kamchatka Sur
- territory-asia-malaysia-north → Malasia Norte
- territory-asia-malaysia-south → Malasia Sur
- territory-asia-mongolia-north → Mongolia Norte
- territory-asia-mongolia-south → Mongolia Sur
- territory-asia-siberia-north → Siberia Norte
- territory-asia-siberia-south → Siberia Sur
- territory-asia-turkey-north → Turquía Norte
- territory-asia-turkey-south → Turquía Sur

### continent-oceania — Oceanía (bonus 4)
- territory-oceania-australia-north → Australia Norte
- territory-oceania-australia-south → Australia Sur
- territory-oceania-borneo-north → Borneo Norte
- territory-oceania-borneo-south → Borneo Sur
- territory-oceania-java-north → Java Norte
- territory-oceania-java-south → Java Sur
- territory-oceania-sumatra-north → Sumatra Norte
- territory-oceania-sumatra-south → Sumatra Sur

Fronteras (todas deben verse conectadas; las de distinto continente pueden ser rutas marítimas):

- territory-africa-egypt-north ↔ territory-africa-egypt-south
- territory-africa-egypt-north ↔ territory-africa-ethiopia-north
- territory-africa-egypt-north ↔ territory-africa-ethiopia-south
- territory-africa-egypt-north ↔ territory-africa-sahara-north
- territory-africa-egypt-north ↔ territory-africa-sahara-south
- territory-africa-egypt-north ↔ territory-asia-arabia-north
- territory-africa-egypt-north ↔ territory-asia-arabia-south
- territory-africa-egypt-north ↔ territory-europe-italy-north
- territory-africa-egypt-north ↔ territory-europe-italy-south
- territory-africa-egypt-south ↔ territory-africa-ethiopia-north
- territory-africa-egypt-south ↔ territory-africa-ethiopia-south
- territory-africa-egypt-south ↔ territory-africa-sahara-north
- territory-africa-egypt-south ↔ territory-africa-sahara-south
- territory-africa-egypt-south ↔ territory-asia-arabia-north
- territory-africa-egypt-south ↔ territory-asia-arabia-south
- territory-africa-egypt-south ↔ territory-europe-italy-north
- territory-africa-egypt-south ↔ territory-europe-italy-south
- territory-africa-ethiopia-north ↔ territory-africa-ethiopia-south
- territory-africa-ethiopia-north ↔ territory-africa-kenya-north
- territory-africa-ethiopia-north ↔ territory-africa-kenya-south
- territory-africa-ethiopia-north ↔ territory-africa-zaire-north
- territory-africa-ethiopia-north ↔ territory-africa-zaire-south
- territory-africa-ethiopia-south ↔ territory-africa-kenya-north
- territory-africa-ethiopia-south ↔ territory-africa-kenya-south
- territory-africa-ethiopia-south ↔ territory-africa-zaire-north
- territory-africa-ethiopia-south ↔ territory-africa-zaire-south
- territory-africa-kenya-north ↔ territory-africa-kenya-south
- territory-africa-kenya-north ↔ territory-africa-madagascar-north
- territory-africa-kenya-north ↔ territory-africa-madagascar-south
- territory-africa-kenya-north ↔ territory-africa-south-africa-north
- territory-africa-kenya-north ↔ territory-africa-south-africa-south
- territory-africa-kenya-north ↔ territory-africa-zaire-north
- territory-africa-kenya-north ↔ territory-africa-zaire-south
- territory-africa-kenya-south ↔ territory-africa-madagascar-north
- territory-africa-kenya-south ↔ territory-africa-madagascar-south
- territory-africa-kenya-south ↔ territory-africa-south-africa-north
- territory-africa-kenya-south ↔ territory-africa-south-africa-south
- territory-africa-kenya-south ↔ territory-africa-zaire-north
- territory-africa-kenya-south ↔ territory-africa-zaire-south
- territory-africa-madagascar-north ↔ territory-africa-madagascar-south
- territory-africa-madagascar-north ↔ territory-africa-south-africa-north
- territory-africa-madagascar-north ↔ territory-africa-south-africa-south
- territory-africa-madagascar-south ↔ territory-africa-south-africa-north
- territory-africa-madagascar-south ↔ territory-africa-south-africa-south
- territory-africa-nigeria-north ↔ territory-africa-nigeria-south
- territory-africa-nigeria-north ↔ territory-africa-sahara-north
- territory-africa-nigeria-north ↔ territory-africa-sahara-south
- territory-africa-nigeria-north ↔ territory-africa-zaire-north
- territory-africa-nigeria-north ↔ territory-africa-zaire-south
- territory-africa-nigeria-south ↔ territory-africa-sahara-north
- territory-africa-nigeria-south ↔ territory-africa-sahara-south
- territory-africa-nigeria-south ↔ territory-africa-zaire-north
- territory-africa-nigeria-south ↔ territory-africa-zaire-south
- territory-africa-sahara-north ↔ territory-africa-sahara-south
- territory-africa-sahara-north ↔ territory-europe-spain-north
- territory-africa-sahara-north ↔ territory-europe-spain-south
- territory-africa-sahara-north ↔ territory-south-america-brazil-north
- territory-africa-sahara-north ↔ territory-south-america-brazil-south
- territory-africa-sahara-south ↔ territory-europe-spain-north
- territory-africa-sahara-south ↔ territory-europe-spain-south
- territory-africa-sahara-south ↔ territory-south-america-brazil-north
- territory-africa-sahara-south ↔ territory-south-america-brazil-south
- territory-africa-south-africa-north ↔ territory-africa-south-africa-south
- territory-africa-south-africa-north ↔ territory-africa-zaire-north
- territory-africa-south-africa-north ↔ territory-africa-zaire-south
- territory-africa-south-africa-south ↔ territory-africa-zaire-north
- territory-africa-south-africa-south ↔ territory-africa-zaire-south
- territory-africa-zaire-north ↔ territory-africa-zaire-south
- territory-asia-arabia-north ↔ territory-asia-arabia-south
- territory-asia-arabia-north ↔ territory-asia-india-north
- territory-asia-arabia-north ↔ territory-asia-india-south
- territory-asia-arabia-north ↔ territory-asia-iran-north
- territory-asia-arabia-north ↔ territory-asia-iran-south
- territory-asia-arabia-north ↔ territory-asia-turkey-north
- territory-asia-arabia-north ↔ territory-asia-turkey-south
- territory-asia-arabia-south ↔ territory-asia-india-north
- territory-asia-arabia-south ↔ territory-asia-india-south
- territory-asia-arabia-south ↔ territory-asia-iran-north
- territory-asia-arabia-south ↔ territory-asia-iran-south
- territory-asia-arabia-south ↔ territory-asia-turkey-north
- territory-asia-arabia-south ↔ territory-asia-turkey-south
- territory-asia-aral-north ↔ territory-asia-aral-south
- territory-asia-aral-north ↔ territory-asia-china-north
- territory-asia-aral-north ↔ territory-asia-china-south
- territory-asia-aral-north ↔ territory-asia-iran-north
- territory-asia-aral-north ↔ territory-asia-iran-south
- territory-asia-aral-north ↔ territory-asia-siberia-north
- territory-asia-aral-north ↔ territory-asia-siberia-south
- territory-asia-aral-north ↔ territory-europe-russia-north
- territory-asia-aral-north ↔ territory-europe-russia-south
- territory-asia-aral-south ↔ territory-asia-china-north
- territory-asia-aral-south ↔ territory-asia-china-south
- territory-asia-aral-south ↔ territory-asia-iran-north
- territory-asia-aral-south ↔ territory-asia-iran-south
- territory-asia-aral-south ↔ territory-asia-siberia-north
- territory-asia-aral-south ↔ territory-asia-siberia-south
- territory-asia-aral-south ↔ territory-europe-russia-north
- territory-asia-aral-south ↔ territory-europe-russia-south
- territory-asia-china-north ↔ territory-asia-china-south
- territory-asia-china-north ↔ territory-asia-gobi-north
- territory-asia-china-north ↔ territory-asia-gobi-south
- territory-asia-china-north ↔ territory-asia-india-north
- territory-asia-china-north ↔ territory-asia-india-south
- territory-asia-china-north ↔ territory-asia-japan-north
- territory-asia-china-north ↔ territory-asia-japan-south
- territory-asia-china-north ↔ territory-asia-malaysia-north
- territory-asia-china-north ↔ territory-asia-malaysia-south
- territory-asia-china-north ↔ territory-asia-siberia-north
- territory-asia-china-north ↔ territory-asia-siberia-south
- territory-asia-china-south ↔ territory-asia-gobi-north
- territory-asia-china-south ↔ territory-asia-gobi-south
- territory-asia-china-south ↔ territory-asia-india-north
- territory-asia-china-south ↔ territory-asia-india-south
- territory-asia-china-south ↔ territory-asia-japan-north
- territory-asia-china-south ↔ territory-asia-japan-south
- territory-asia-china-south ↔ territory-asia-malaysia-north
- territory-asia-china-south ↔ territory-asia-malaysia-south
- territory-asia-china-south ↔ territory-asia-siberia-north
- territory-asia-china-south ↔ territory-asia-siberia-south
- territory-asia-gobi-north ↔ territory-asia-gobi-south
- territory-asia-gobi-north ↔ territory-asia-mongolia-north
- territory-asia-gobi-north ↔ territory-asia-mongolia-south
- territory-asia-gobi-north ↔ territory-asia-siberia-north
- territory-asia-gobi-north ↔ territory-asia-siberia-south
- territory-asia-gobi-south ↔ territory-asia-mongolia-north
- territory-asia-gobi-south ↔ territory-asia-mongolia-south
- territory-asia-gobi-south ↔ territory-asia-siberia-north
- territory-asia-gobi-south ↔ territory-asia-siberia-south
- territory-asia-india-north ↔ territory-asia-india-south
- territory-asia-india-north ↔ territory-asia-iran-north
- territory-asia-india-north ↔ territory-asia-iran-south
- territory-asia-india-north ↔ territory-asia-malaysia-north
- territory-asia-india-north ↔ territory-asia-malaysia-south
- territory-asia-india-south ↔ territory-asia-iran-north
- territory-asia-india-south ↔ territory-asia-iran-south
- territory-asia-india-south ↔ territory-asia-malaysia-north
- territory-asia-india-south ↔ territory-asia-malaysia-south
- territory-asia-iran-north ↔ territory-asia-iran-south
- territory-asia-iran-north ↔ territory-asia-turkey-north
- territory-asia-iran-north ↔ territory-asia-turkey-south
- territory-asia-iran-south ↔ territory-asia-turkey-north
- territory-asia-iran-south ↔ territory-asia-turkey-south
- territory-asia-japan-north ↔ territory-asia-japan-south
- territory-asia-japan-north ↔ territory-asia-kamchatka-north
- territory-asia-japan-north ↔ territory-asia-kamchatka-south
- territory-asia-japan-south ↔ territory-asia-kamchatka-north
- territory-asia-japan-south ↔ territory-asia-kamchatka-south
- territory-asia-kamchatka-north ↔ territory-asia-kamchatka-south
- territory-asia-kamchatka-north ↔ territory-asia-siberia-north
- territory-asia-kamchatka-north ↔ territory-asia-siberia-south
- territory-asia-kamchatka-north ↔ territory-north-america-alaska-north
- territory-asia-kamchatka-north ↔ territory-north-america-alaska-south
- territory-asia-kamchatka-south ↔ territory-asia-siberia-north
- territory-asia-kamchatka-south ↔ territory-asia-siberia-south
- territory-asia-kamchatka-south ↔ territory-north-america-alaska-north
- territory-asia-kamchatka-south ↔ territory-north-america-alaska-south
- territory-asia-malaysia-north ↔ territory-asia-malaysia-south
- territory-asia-malaysia-north ↔ territory-oceania-borneo-north
- territory-asia-malaysia-north ↔ territory-oceania-borneo-south
- territory-asia-malaysia-north ↔ territory-oceania-sumatra-north
- territory-asia-malaysia-north ↔ territory-oceania-sumatra-south
- territory-asia-malaysia-south ↔ territory-oceania-borneo-north
- territory-asia-malaysia-south ↔ territory-oceania-borneo-south
- territory-asia-malaysia-south ↔ territory-oceania-sumatra-north
- territory-asia-malaysia-south ↔ territory-oceania-sumatra-south
- territory-asia-mongolia-north ↔ territory-asia-mongolia-south
- territory-asia-mongolia-north ↔ territory-asia-siberia-north
- territory-asia-mongolia-north ↔ territory-asia-siberia-south
- territory-asia-mongolia-south ↔ territory-asia-siberia-north
- territory-asia-mongolia-south ↔ territory-asia-siberia-south
- territory-asia-siberia-north ↔ territory-asia-siberia-south
- territory-asia-siberia-north ↔ territory-europe-russia-north
- territory-asia-siberia-north ↔ territory-europe-russia-south
- territory-asia-siberia-south ↔ territory-europe-russia-north
- territory-asia-siberia-south ↔ territory-europe-russia-south
- territory-asia-turkey-north ↔ territory-asia-turkey-south
- territory-asia-turkey-north ↔ territory-europe-poland-north
- territory-asia-turkey-north ↔ territory-europe-poland-south
- territory-asia-turkey-north ↔ territory-europe-russia-north
- territory-asia-turkey-north ↔ territory-europe-russia-south
- territory-asia-turkey-south ↔ territory-europe-poland-north
- territory-asia-turkey-south ↔ territory-europe-poland-south
- territory-asia-turkey-south ↔ territory-europe-russia-north
- territory-asia-turkey-south ↔ territory-europe-russia-south
- territory-europe-france-north ↔ territory-europe-france-south
- territory-europe-france-north ↔ territory-europe-germany-north
- territory-europe-france-north ↔ territory-europe-germany-south
- territory-europe-france-north ↔ territory-europe-great-britain-north
- territory-europe-france-north ↔ territory-europe-great-britain-south
- territory-europe-france-north ↔ territory-europe-italy-north
- territory-europe-france-north ↔ territory-europe-italy-south
- territory-europe-france-north ↔ territory-europe-spain-north
- territory-europe-france-north ↔ territory-europe-spain-south
- territory-europe-france-south ↔ territory-europe-germany-north
- territory-europe-france-south ↔ territory-europe-germany-south
- territory-europe-france-south ↔ territory-europe-great-britain-north
- territory-europe-france-south ↔ territory-europe-great-britain-south
- territory-europe-france-south ↔ territory-europe-italy-north
- territory-europe-france-south ↔ territory-europe-italy-south
- territory-europe-france-south ↔ territory-europe-spain-north
- territory-europe-france-south ↔ territory-europe-spain-south
- territory-europe-germany-north ↔ territory-europe-germany-south
- territory-europe-germany-north ↔ territory-europe-great-britain-north
- territory-europe-germany-north ↔ territory-europe-great-britain-south
- territory-europe-germany-north ↔ territory-europe-italy-north
- territory-europe-germany-north ↔ territory-europe-italy-south
- territory-europe-germany-north ↔ territory-europe-poland-north
- territory-europe-germany-north ↔ territory-europe-poland-south
- territory-europe-germany-north ↔ territory-europe-sweden-north
- territory-europe-germany-north ↔ territory-europe-sweden-south
- territory-europe-germany-south ↔ territory-europe-great-britain-north
- territory-europe-germany-south ↔ territory-europe-great-britain-south
- territory-europe-germany-south ↔ territory-europe-italy-north
- territory-europe-germany-south ↔ territory-europe-italy-south
- territory-europe-germany-south ↔ territory-europe-poland-north
- territory-europe-germany-south ↔ territory-europe-poland-south
- territory-europe-germany-south ↔ territory-europe-sweden-north
- territory-europe-germany-south ↔ territory-europe-sweden-south
- territory-europe-great-britain-north ↔ territory-europe-great-britain-south
- territory-europe-great-britain-north ↔ territory-europe-iceland-north
- territory-europe-great-britain-north ↔ territory-europe-iceland-south
- territory-europe-great-britain-south ↔ territory-europe-iceland-north
- territory-europe-great-britain-south ↔ territory-europe-iceland-south
- territory-europe-iceland-north ↔ territory-europe-iceland-south
- territory-europe-iceland-north ↔ territory-europe-sweden-north
- territory-europe-iceland-north ↔ territory-europe-sweden-south
- territory-europe-iceland-north ↔ territory-north-america-greenland-north
- territory-europe-iceland-north ↔ territory-north-america-greenland-south
- territory-europe-iceland-south ↔ territory-europe-sweden-north
- territory-europe-iceland-south ↔ territory-europe-sweden-south
- territory-europe-iceland-south ↔ territory-north-america-greenland-north
- territory-europe-iceland-south ↔ territory-north-america-greenland-south
- territory-europe-italy-north ↔ territory-europe-italy-south
- territory-europe-poland-north ↔ territory-europe-poland-south
- territory-europe-poland-north ↔ territory-europe-russia-north
- territory-europe-poland-north ↔ territory-europe-russia-south
- territory-europe-poland-south ↔ territory-europe-russia-north
- territory-europe-poland-south ↔ territory-europe-russia-south
- territory-europe-russia-north ↔ territory-europe-russia-south
- territory-europe-russia-north ↔ territory-europe-sweden-north
- territory-europe-russia-north ↔ territory-europe-sweden-south
- territory-europe-russia-south ↔ territory-europe-sweden-north
- territory-europe-russia-south ↔ territory-europe-sweden-south
- territory-europe-spain-north ↔ territory-europe-spain-south
- territory-europe-sweden-north ↔ territory-europe-sweden-south
- territory-north-america-alaska-north ↔ territory-north-america-alaska-south
- territory-north-america-alaska-north ↔ territory-north-america-yukon-north
- territory-north-america-alaska-north ↔ territory-north-america-yukon-south
- territory-north-america-alaska-south ↔ territory-north-america-yukon-north
- territory-north-america-alaska-south ↔ territory-north-america-yukon-south
- territory-north-america-california-north ↔ territory-north-america-california-south
- territory-north-america-california-north ↔ territory-north-america-mexico-north
- territory-north-america-california-north ↔ territory-north-america-mexico-south
- territory-north-america-california-north ↔ territory-north-america-new-york-north
- territory-north-america-california-north ↔ territory-north-america-new-york-south
- territory-north-america-california-north ↔ territory-north-america-oregon-north
- territory-north-america-california-north ↔ territory-north-america-oregon-south
- territory-north-america-california-south ↔ territory-north-america-mexico-north
- territory-north-america-california-south ↔ territory-north-america-mexico-south
- territory-north-america-california-south ↔ territory-north-america-new-york-north
- territory-north-america-california-south ↔ territory-north-america-new-york-south
- territory-north-america-california-south ↔ territory-north-america-oregon-north
- territory-north-america-california-south ↔ territory-north-america-oregon-south
- territory-north-america-canada-north ↔ territory-north-america-canada-south
- territory-north-america-canada-north ↔ territory-north-america-new-york-north
- territory-north-america-canada-north ↔ territory-north-america-new-york-south
- territory-north-america-canada-north ↔ territory-north-america-newfoundland-north
- territory-north-america-canada-north ↔ territory-north-america-newfoundland-south
- territory-north-america-canada-north ↔ territory-north-america-oregon-north
- territory-north-america-canada-north ↔ territory-north-america-oregon-south
- territory-north-america-canada-north ↔ territory-north-america-yukon-north
- territory-north-america-canada-north ↔ territory-north-america-yukon-south
- territory-north-america-canada-south ↔ territory-north-america-new-york-north
- territory-north-america-canada-south ↔ territory-north-america-new-york-south
- territory-north-america-canada-south ↔ territory-north-america-newfoundland-north
- territory-north-america-canada-south ↔ territory-north-america-newfoundland-south
- territory-north-america-canada-south ↔ territory-north-america-oregon-north
- territory-north-america-canada-south ↔ territory-north-america-oregon-south
- territory-north-america-canada-south ↔ territory-north-america-yukon-north
- territory-north-america-canada-south ↔ territory-north-america-yukon-south
- territory-north-america-greenland-north ↔ territory-north-america-greenland-south
- territory-north-america-greenland-north ↔ territory-north-america-newfoundland-north
- territory-north-america-greenland-north ↔ territory-north-america-newfoundland-south
- territory-north-america-greenland-south ↔ territory-north-america-newfoundland-north
- territory-north-america-greenland-south ↔ territory-north-america-newfoundland-south
- territory-north-america-mexico-north ↔ territory-north-america-mexico-south
- territory-north-america-mexico-north ↔ territory-south-america-colombia-north
- territory-north-america-mexico-north ↔ territory-south-america-colombia-south
- territory-north-america-mexico-south ↔ territory-south-america-colombia-north
- territory-north-america-mexico-south ↔ territory-south-america-colombia-south
- territory-north-america-new-york-north ↔ territory-north-america-new-york-south
- territory-north-america-new-york-north ↔ territory-north-america-newfoundland-north
- territory-north-america-new-york-north ↔ territory-north-america-newfoundland-south
- territory-north-america-new-york-north ↔ territory-north-america-oregon-north
- territory-north-america-new-york-north ↔ territory-north-america-oregon-south
- territory-north-america-new-york-south ↔ territory-north-america-newfoundland-north
- territory-north-america-new-york-south ↔ territory-north-america-newfoundland-south
- territory-north-america-new-york-south ↔ territory-north-america-oregon-north
- territory-north-america-new-york-south ↔ territory-north-america-oregon-south
- territory-north-america-newfoundland-north ↔ territory-north-america-newfoundland-south
- territory-north-america-oregon-north ↔ territory-north-america-oregon-south
- territory-north-america-oregon-north ↔ territory-north-america-yukon-north
- territory-north-america-oregon-north ↔ territory-north-america-yukon-south
- territory-north-america-oregon-south ↔ territory-north-america-yukon-north
- territory-north-america-oregon-south ↔ territory-north-america-yukon-south
- territory-north-america-yukon-north ↔ territory-north-america-yukon-south
- territory-oceania-australia-north ↔ territory-oceania-australia-south
- territory-oceania-australia-north ↔ territory-oceania-borneo-north
- territory-oceania-australia-north ↔ territory-oceania-borneo-south
- territory-oceania-australia-north ↔ territory-oceania-java-north
- territory-oceania-australia-north ↔ territory-oceania-java-south
- territory-oceania-australia-north ↔ territory-south-america-chile-north
- territory-oceania-australia-north ↔ territory-south-america-chile-south
- territory-oceania-australia-south ↔ territory-oceania-borneo-north
- territory-oceania-australia-south ↔ territory-oceania-borneo-south
- territory-oceania-australia-south ↔ territory-oceania-java-north
- territory-oceania-australia-south ↔ territory-oceania-java-south
- territory-oceania-australia-south ↔ territory-south-america-chile-north
- territory-oceania-australia-south ↔ territory-south-america-chile-south
- territory-oceania-borneo-north ↔ territory-oceania-borneo-south
- territory-oceania-java-north ↔ territory-oceania-java-south
- territory-oceania-java-north ↔ territory-oceania-sumatra-north
- territory-oceania-java-north ↔ territory-oceania-sumatra-south
- territory-oceania-java-south ↔ territory-oceania-sumatra-north
- territory-oceania-java-south ↔ territory-oceania-sumatra-south
- territory-oceania-sumatra-north ↔ territory-oceania-sumatra-south
- territory-south-america-argentina-north ↔ territory-south-america-argentina-south
- territory-south-america-argentina-north ↔ territory-south-america-bolivia-north
- territory-south-america-argentina-north ↔ territory-south-america-bolivia-south
- territory-south-america-argentina-north ↔ territory-south-america-brazil-north
- territory-south-america-argentina-north ↔ territory-south-america-brazil-south
- territory-south-america-argentina-north ↔ territory-south-america-chile-north
- territory-south-america-argentina-north ↔ territory-south-america-chile-south
- territory-south-america-argentina-north ↔ territory-south-america-uruguay-north
- territory-south-america-argentina-north ↔ territory-south-america-uruguay-south
- territory-south-america-argentina-south ↔ territory-south-america-bolivia-north
- territory-south-america-argentina-south ↔ territory-south-america-bolivia-south
- territory-south-america-argentina-south ↔ territory-south-america-brazil-north
- territory-south-america-argentina-south ↔ territory-south-america-brazil-south
- territory-south-america-argentina-south ↔ territory-south-america-chile-north
- territory-south-america-argentina-south ↔ territory-south-america-chile-south
- territory-south-america-argentina-south ↔ territory-south-america-uruguay-north
- territory-south-america-argentina-south ↔ territory-south-america-uruguay-south
- territory-south-america-bolivia-north ↔ territory-south-america-bolivia-south
- territory-south-america-bolivia-north ↔ territory-south-america-brazil-north
- territory-south-america-bolivia-north ↔ territory-south-america-brazil-south
- territory-south-america-bolivia-north ↔ territory-south-america-chile-north
- territory-south-america-bolivia-north ↔ territory-south-america-chile-south
- territory-south-america-bolivia-north ↔ territory-south-america-peru-north
- territory-south-america-bolivia-north ↔ territory-south-america-peru-south
- territory-south-america-bolivia-south ↔ territory-south-america-brazil-north
- territory-south-america-bolivia-south ↔ territory-south-america-brazil-south
- territory-south-america-bolivia-south ↔ territory-south-america-chile-north
- territory-south-america-bolivia-south ↔ territory-south-america-chile-south
- territory-south-america-bolivia-south ↔ territory-south-america-peru-north
- territory-south-america-bolivia-south ↔ territory-south-america-peru-south
- territory-south-america-brazil-north ↔ territory-south-america-brazil-south
- territory-south-america-brazil-north ↔ territory-south-america-colombia-north
- territory-south-america-brazil-north ↔ territory-south-america-colombia-south
- territory-south-america-brazil-north ↔ territory-south-america-peru-north
- territory-south-america-brazil-north ↔ territory-south-america-peru-south
- territory-south-america-brazil-north ↔ territory-south-america-uruguay-north
- territory-south-america-brazil-north ↔ territory-south-america-uruguay-south
- territory-south-america-brazil-north ↔ territory-south-america-venezuela-north
- territory-south-america-brazil-north ↔ territory-south-america-venezuela-south
- territory-south-america-brazil-south ↔ territory-south-america-colombia-north
- territory-south-america-brazil-south ↔ territory-south-america-colombia-south
- territory-south-america-brazil-south ↔ territory-south-america-peru-north
- territory-south-america-brazil-south ↔ territory-south-america-peru-south
- territory-south-america-brazil-south ↔ territory-south-america-uruguay-north
- territory-south-america-brazil-south ↔ territory-south-america-uruguay-south
- territory-south-america-brazil-south ↔ territory-south-america-venezuela-north
- territory-south-america-brazil-south ↔ territory-south-america-venezuela-south
- territory-south-america-chile-north ↔ territory-south-america-chile-south
- territory-south-america-chile-north ↔ territory-south-america-peru-north
- territory-south-america-chile-north ↔ territory-south-america-peru-south
- territory-south-america-chile-south ↔ territory-south-america-peru-north
- territory-south-america-chile-south ↔ territory-south-america-peru-south
- territory-south-america-colombia-north ↔ territory-south-america-colombia-south
- territory-south-america-colombia-north ↔ territory-south-america-peru-north
- territory-south-america-colombia-north ↔ territory-south-america-peru-south
- territory-south-america-colombia-north ↔ territory-south-america-venezuela-north
- territory-south-america-colombia-north ↔ territory-south-america-venezuela-south
- territory-south-america-colombia-south ↔ territory-south-america-peru-north
- territory-south-america-colombia-south ↔ territory-south-america-peru-south
- territory-south-america-colombia-south ↔ territory-south-america-venezuela-north
- territory-south-america-colombia-south ↔ territory-south-america-venezuela-south
- territory-south-america-peru-north ↔ territory-south-america-peru-south
- territory-south-america-uruguay-north ↔ territory-south-america-uruguay-south
- territory-south-america-venezuela-north ↔ territory-south-america-venezuela-south



---

**Nota para quien use este prompt**: adjuntar también el archivo actual
`assets/maps/base/map-base-tactical-50-001.svg` como referencia del contrato.
Al recibir el SVG nuevo, reemplazar el archivo, correr
`docker compose build frontend && docker compose up -d frontend` y refrescar.
El juego valida los IDs contra `backend/src/teg_backend/domain/map.py`.
