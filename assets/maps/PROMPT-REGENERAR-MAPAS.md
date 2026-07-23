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

El archivo `map-base-tactical-50-001.svg` completo (siguiendo todo lo anterior).
Si te pido la variante de 100 territorios (`map-base-tactical-100-001.svg`,
`id="map-base-tactical-100-001"`), te pasaré la lista de IDs adicional en ese momento.

---

**Nota para quien use este prompt**: adjuntar también el archivo actual
`assets/maps/base/map-base-tactical-50-001.svg` como referencia del contrato.
Al recibir el SVG nuevo, reemplazar el archivo, correr
`docker compose build frontend && docker compose up -d frontend` y refrescar.
El juego valida los IDs contra `backend/src/teg_backend/domain/map.py`.
