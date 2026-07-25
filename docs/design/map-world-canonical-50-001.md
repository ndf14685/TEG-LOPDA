# Mapa canónico Modo 50 — map-world-canonical-50-001.svg

Fecha: 2026-07-25
Rol: Dirección de Arte Cartográfico
Estado: **entregado con hallazgo bloqueante** (ver "Alineación")

## Qué se entregó

`assets/maps/base/map-world-canonical-50-001.svg` = base cartográfica V3
(costas reales lon/lat → Mercator) + masas geográficas **no jugables** nuevas +
las capas jugables del export táctico copiadas literalmente.

Generado por `design/tools/gen-map-canonical-v1.py` (reproducible).

### Masas no jugables agregadas

| Elemento | Tratamiento |
|---|---|
| Antártida | Costa autoral de 69 vértices (península antártica, mar de Weddell, Tierra de la Reina Maud, bahía de Prydz, Tierra de Wilkes, mar de Ross), cerrada contra el borde inferior del lienzo. Latitudes bajo −58° se comprimen linealmente porque Mercator diverge en el polo. |
| Casquete ártico | Borde de banquisa irregular (lat 73°–79°) cerrado contra el borde superior, con línea de hielo punteada. Cubre el tope de Groenlandia y Siberia, que antes quedaba cortado en seco por el lienzo. |
| Islas secundarias | 35 masas nuevas: Svalbard, Severnaya Zemlya, Nuevas Siberianas, Feroe, Azores, Canarias, Cabo Verde, Malvinas, Georgia del Sur, Jamaica, Puerto Rico, Antillas Menores, Trinidad, Aleutianas, Hawái, Galápagos, Chiloé, Sicilia, Cerdeña, Córcega, Creta, Chipre, Baleares, Hainan, Shikoku, Timor, Flores-Sumbawa, Halmahera, Seram, Kerguelen, Nueva Caledonia, Salomón, Vanuatu, Fiji. |

Antártida y Ártico usan clase `.geo-ice`: relleno más apagado que la tierra
jugable, sin borde nítido, con trama diagonal y línea punteada. **No compiten
visualmente ni se leen como territorio seleccionable.**

### viewBox

`0 0 2560 1720`. Mismo origen y misma escala que el canónico 2560×1440: es una
extensión hacia abajo, ningún punto cambia de coordenada. Se necesita porque la
geometría jugable ya llegaba a y=1620 (se recortaba) y para alojar la franja
antártica. Es el mismo saneo que `MapPanel.tsx` calcula hoy en runtime.

### Ajuste de contraste de la capa jugable

El export táctico rellena los territorios con `rgba(15,23,42,0.75)`, que tapa la
geografía. En el canónico se los baja al rango pedido (0.30–0.35) con la
propiedad leída por borde. Es **solo CSS**: no cambia geometría, ids, hitboxes
ni adyacencias, y replica lo que `MapPanel.tsx` ya hace en runtime
(`fillOpacity` 0.34/0.35).

## Verificación del contrato (automatizada)

```
XML válido: True | viewBox: 0 0 2560 1720
layer-1 pointer-events: none
layer-1 limpio: sin hitboxes, sin ids de territorio, sin labels, sin tropas, sin clases de jugador
ids de territorio idénticos al export táctico: True | n = 50
hitboxes idénticas: True | n = 50
geometría jugable sin cambios: True
geometría de hitboxes sin cambios: True
masas no jugables: 74 paths geográficos
```

Backend, adyacencias, reglas e ids: intactos. No se tocó ningún archivo del juego.

## Capturas

| Vista | Archivo |
|---|---|
| 1366×768 con labels | `test-results/canonical-1366x768-labels.png` |
| 1366×768 sin labels | `test-results/canonical-1366x768-nolabels.png` |
| 1920×1080 con labels | `test-results/canonical-1920x1080-labels.png` |
| 1920×1080 sin labels | `test-results/canonical-1920x1080-nolabels.png` |
| 2560×1440 sin labels | `test-results/canonical-2560x1440-nolabels.png` |
| 3840×2160 sin labels | `test-results/canonical-3840x2160-nolabels.png` |
| Seis jugadores | `test-results/canonical-six-players-1920x1080.png` |
| Selección + ataque posible | `test-results/canonical-attack-state-1920x1080.png` |
| Diagnóstico de alineación | `test-results/canonical-alignment-diagnostic.png` |

Las vistas "sin labels" quitan las clases demo `p-*` igual que hace el frontend
en runtime, para juzgar la lectura del mapamundi y no un reparto ficticio.
Los estados de selección/ataque se inyectan en la página de captura
(`design/tools/capture-canonical.mjs`): **no están horneados en el asset**.

## Alineación: hallazgo bloqueante

Al componer base real + territorios jugables por primera vez queda demostrado
que **los 50 territorios del Modo 50 no están dibujados sobre coordenadas
geográficas**. Medición (`design/tools/diag-territory-alignment.py`, compara el
centroide de cada territorio contra la posición real del lugar que nombra):

```
Territorios medidos : 50
Error medio         : 191 px
Error mediano       : 194 px
Error máximo        : 362 px
Dentro de 150 px    : 13/50
```

Peores corrimientos: Mongolia 362 px, Aral 308, Madagascar 306, Japón 303,
Kamchatka 281, Chile 280, Argentina 272, Gobi 262, Perú 259, Siberia 254.

Consecuencias visibles en `canonical-1366x768-labels.png`:

- **Sudáfrica** cae en el Atlántico Sur, fuera del continente.
- **Australia** flota al sudeste de Australia, sobre el mar de Tasmania.
- **Madagascar** queda en el océano Índico, a ~300 px de la isla real.
- **India** se apoya sobre el Tíbet; **China** sobre Mongolia; **Japón** sobre el Pacífico.
- **Chile** y **Argentina** se extienden bajo el continente, hacia la franja antártica.
- **Alaska, Yukón y Canadá** se apoyan sobre el casquete ártico, no sobre tierra.

Es un defecto **preexistente** de `map-base-tactical-50-001.svg`, no introducido
por este entregable: los blobs siempre estuvieron ahí, pero sin base geográfica
detrás nadie podía verlo. Añadir Antártida, Ártico e islas mejora la lectura del
mundo, pero **no puede compensar que la capa jugable contradiga la geografía**.

### Criterio de aceptación: resultado honesto

- «Antártida y Ártico no parecen territorios seleccionables ni compiten
  visualmente» → **cumple**.
- «Con labels apagados la captura se lee inmediatamente como mapamundi completo»
  → **cumple la base**; con la capa jugable encima, 37 de 50 territorios
  desmienten la geografía que hay debajo.

### Decisión que corresponde al PO

Tres caminos, ninguno se ejecuta sin su visto bueno:

1. **Reproyectar la geometría de los 50 territorios** sobre la base V3,
   preservando los 50 ids, las 50 hitboxes y las adyacencias del backend (solo
   cambian los atributos `d`). Es la única opción que alcanza el criterio de
   «mapamundi terminado». `diag-territory-alignment.py` ya contiene la tabla
   lon/lat de los 50 lugares, que es justamente el insumo de ese trabajo.
2. **Aceptar el corrimiento** como estilización de tablero y documentarlo, con
   la base geográfica como ambientación, no como referencia.
3. **Ocultar la base bajo los territorios** (volver al fondo plano) y cerrar el
   P0 por otra vía.

Recomendación de Arte: opción 1. Es la única que hace que el mapa se lea como
tablero mundial terminado sin explicación, que es el criterio que se fijó.

## Nota de integración (no ejecutada)

`MapPanel.tsx` hoy oculta `#layer-1-geo-base` del export táctico cuando carga
una base geográfica aparte. Si en algún momento se usa este canónico como mapa
del Modo 50, esa lógica debe revisarse para no apagar la geografía que el propio
archivo ya trae. **No se tocó nada de Frontend.**
