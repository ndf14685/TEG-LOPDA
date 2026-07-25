# Reproyección canónica de los 50 territorios — map-world-canonical-50-002.svg

Fecha: 2026-07-25
Rol: Dirección de Arte Cartográfico
Reemplaza como mapa canónico a `map-world-canonical-50-001.svg`, que ya traía
Antártida/Ártico pero conservaba los territorios desalineados.

## Resultado en una línea

Los 50 territorios pasan de estar a 191 px de promedio de su ubicación real a
**contener los 50 su propia ubicación geográfica** (antes: 4 de 50).

| Métrica | canónico -001 (blobs del export) | canónico -002 (reproyectado) |
|---|---|---|
| Territorios que contienen su punto geográfico real | 4/50 | **50/50** |
| Error medio del centro | 191 px | **38 px** |
| Error máximo | 362 px | **103 px** |

Sudáfrica ya no está en el Atlántico, Australia está en Australia, India está en
India y América del Sur no queda descalzada: el borde exterior de cada territorio
*es* la línea de costa, así que ninguno puede flotar en el mar.

## Método

No se movieron los blobs viejos: se generó geometría nueva desde la geografía.

1. **La costa real como fuente.** Cada masa continental de la base V3 se densifica
   muestreando su curva Catmull-Rom hasta obtener el polígono real de la costa.
2. **Una semilla por territorio** en su posición geográfica real (lon/lat).
3. **Partición de Voronoi recortada contra la costa.** Cada territorio es la
   intersección de su celda de Voronoi con la masa continental, por recorte
   sucesivo de semiplanos (Sutherland-Hodgman). Las fronteras internas nacen de
   la geografía; las externas son la costa.
4. **Islas que son un territorio completo** (Groenlandia, Islandia, Gran Bretaña,
   Japón, Madagascar, Sumatra, Borneo, Java, Australia) toman el polígono de la
   isla. Japón usa cuatro subtrazos (Honshu, Hokkaido, Kyushu, Shikoku) en un
   único path con un único id. Terranova suma su isla a la celda de Labrador;
   Italia suma Sicilia y Cerdeña; España, Baleares; Gran Bretaña, Irlanda.
5. **Semillas afinadas** (`design/tools/tune-seeds.py`): ascenso de colina sobre
   una retícula de 5 px que maximiza las adyacencias declaradas por el backend,
   con tope de 7° de desvío respecto de la posición real, para que ningún
   territorio deje de ser geográficamente honesto.

Generador: `design/tools/gen-map-canonical-v2.py`, determinista y reproducible.

### Defecto de la base corregido de paso

El contorno de Honshu estaba mal cerrado: el trazo de vuelta corría por las
mismas latitudes que el de ida, así que la isla era un lazo delgado y hueco
(el centro de Honshu quedaba *fuera* del polígono). Se reescribió el contorno
—bajada por la costa del Pacífico, regreso por la del mar del Japón— y se
agregaron Kyushu y Shikoku. Esto también corrige
`map-world-geographic-base-50-003.svg`.

## Contrato preservado (verificado automáticamente)

```
XML válido: True | viewBox: 0 0 2560 1720 | viewBox único: True | sin transform: True
ids 50 | hitboxes 50
ids == TERRITORIES_50 del backend .......... True
data-territory == ids ...................... True
nombres visibles == nombres del backend .... True
geometría de hitbox == geometría del territorio (1:1) ... True
layer-1 sin hitboxes, sin ids, sin labels, sin tropas ... True
Antártida y casquete ártico dentro de layer-1 .......... True
```

Base, territorios, hitboxes y overlays comparten **un único viewBox**
`0 0 2560 1720` y el archivo **no contiene ningún `transform`**: no hay ajuste
manual por resolución. Backend, adyacencias y reglas: intactos, ni un archivo
tocado. No se crearon ni eliminaron territorios. Antártida, casquete ártico e
islas secundarias siguen siendo no jugables.

## Adyacencias

De las **63 adyacencias terrestres** que declara el backend (pares en la misma
masa continental), la geometría nueva reproduce **58**. Las 5 restantes tienen un
tercer territorio en el medio:

| Par declarado | Por qué no se tocan |
|---|---|
| Arabia ↔ India | En la realidad tampoco son limítrofes: el mar Arábigo e Irán están en el medio. Es un puente marítimo del diseño de juego. |
| Aral ↔ China | Frontera real, pero Gobi e India ocupan el corredor en la partición. |
| China ↔ Siberia | Frontera real, pero Mongolia y Gobi ocupan el corredor. |
| Argentina ↔ Brasil | Frontera real corta (Misiones); Uruguay y Bolivia la cubren. |
| Chile ↔ Perú | Frontera real; Bolivia llega a la costa en la partición. |

Es una limitación de una partición de Voronoi (celdas convexas) frente a un grafo
de adyacencias arbitrario. **El grafo no se tocó**: el backend sigue siendo la
autoridad y esos ataques siguen permitidos; simplemente no se ven como frontera
común. Resolverlo exigiría varias semillas por territorio y unión de polígonos;
se puede hacer en una iteración posterior si el PO lo pide.

Hay además 15 contactos geométricos que el backend no declara (por ejemplo
Turquía ↔ Italia a través de los Balcanes). No habilitan nada: el juego solo
permite lo que declara el backend.

## Legibilidad de etiquetas

- La etiqueta se ancla en el **polo de inaccesibilidad** del territorio (el punto
  interior más lejano del borde), no en el centroide: en formas alargadas como
  Chile ya no cae fuera.
- El cuerpo tipográfico escala con el área (15–24 px), así los territorios chicos
  no invaden a sus vecinos.
- Pasada de descolisión: los rótulos que se pisan se separan sin alejarse más de
  52 px de su ancla y sin salir nunca del territorio.

Quedan solapes menores en el racimo europeo (Alemania/Polonia, Gran Bretaña) y en
Insulindia (Sumatra/Java/Borneo), donde los territorios son chicos y están
pegados. Mejoró mucho respecto del export anterior, pero no está perfecto: si
molesta, el próximo paso es rotulado con líneas de conducción para esos racimos.

## Capturas

| Vista | Archivo |
|---|---|
| 1366×768 con labels | `test-results/canonical-v2-1366x768-labels.png` |
| 1366×768 sin labels | `test-results/canonical-v2-1366x768-nolabels.png` |
| 1920×1080 con labels | `test-results/canonical-v2-1920x1080-labels.png` |
| 1920×1080 sin labels | `test-results/canonical-v2-1920x1080-nolabels.png` |
| 2560×1440 sin labels | `test-results/canonical-v2-2560x1440-nolabels.png` |
| 3840×2160 sin labels | `test-results/canonical-v2-3840x2160-nolabels.png` |
| Seis jugadores | `test-results/canonical-v2-six-players.png` |
| Seleccionado + atacable + flecha | `test-results/canonical-v2-attack-state.png` |

Los estados (labels apagados, colores de jugador, selección, objetivo atacable,
flecha) se inyectan en la página de captura (`design/tools/capture-canonical.mjs`):
**no están horneados en el asset**.

## Tabla de los 50 IDs preservados

| # | ID preservado | Nombre visible | Continente |
|---|---|---|---|
| 1 | `territory-north-america-alaska` | Alaska | América del Norte |
| 2 | `territory-north-america-california` | California | América del Norte |
| 3 | `territory-north-america-canada` | Canadá | América del Norte |
| 4 | `territory-north-america-greenland` | Groenlandia | América del Norte |
| 5 | `territory-north-america-mexico` | México | América del Norte |
| 6 | `territory-north-america-new-york` | Nueva York | América del Norte |
| 7 | `territory-north-america-oregon` | Oregón | América del Norte |
| 8 | `territory-north-america-newfoundland` | Terranova | América del Norte |
| 9 | `territory-north-america-yukon` | Yukón | América del Norte |
| 10 | `territory-south-america-argentina` | Argentina | América del Sur |
| 11 | `territory-south-america-bolivia` | Bolivia | América del Sur |
| 12 | `territory-south-america-brazil` | Brasil | América del Sur |
| 13 | `territory-south-america-chile` | Chile | América del Sur |
| 14 | `territory-south-america-colombia` | Colombia | América del Sur |
| 15 | `territory-south-america-peru` | Perú | América del Sur |
| 16 | `territory-south-america-uruguay` | Uruguay | América del Sur |
| 17 | `territory-south-america-venezuela` | Venezuela | América del Sur |
| 18 | `territory-europe-germany` | Alemania | Europa |
| 19 | `territory-europe-spain` | España | Europa |
| 20 | `territory-europe-france` | Francia | Europa |
| 21 | `territory-europe-great-britain` | Gran Bretaña | Europa |
| 22 | `territory-europe-iceland` | Islandia | Europa |
| 23 | `territory-europe-italy` | Italia | Europa |
| 24 | `territory-europe-poland` | Polonia | Europa |
| 25 | `territory-europe-russia` | Rusia | Europa |
| 26 | `territory-europe-sweden` | Suecia | Europa |
| 27 | `territory-africa-egypt` | Egipto | África |
| 28 | `territory-africa-ethiopia` | Etiopía | África |
| 29 | `territory-africa-kenya` | Kenia | África |
| 30 | `territory-africa-madagascar` | Madagascar | África |
| 31 | `territory-africa-nigeria` | Nigeria | África |
| 32 | `territory-africa-south-africa` | Sudáfrica | África |
| 33 | `territory-africa-sahara` | Sáhara | África |
| 34 | `territory-africa-zaire` | Zaire | África |
| 35 | `territory-asia-arabia` | Arabia | Asia |
| 36 | `territory-asia-aral` | Aral | Asia |
| 37 | `territory-asia-china` | China | Asia |
| 38 | `territory-asia-gobi` | Gobi | Asia |
| 39 | `territory-asia-india` | India | Asia |
| 40 | `territory-asia-iran` | Irán | Asia |
| 41 | `territory-asia-japan` | Japón | Asia |
| 42 | `territory-asia-kamchatka` | Kamchatka | Asia |
| 43 | `territory-asia-malaysia` | Malasia | Asia |
| 44 | `territory-asia-mongolia` | Mongolia | Asia |
| 45 | `territory-asia-siberia` | Siberia | Asia |
| 46 | `territory-asia-turkey` | Turquía | Asia |
| 47 | `territory-oceania-australia` | Australia | Oceanía |
| 48 | `territory-oceania-borneo` | Borneo | Oceanía |
| 49 | `territory-oceania-java` | Java | Oceanía |
| 50 | `territory-oceania-sumatra` | Sumatra | Oceanía |
