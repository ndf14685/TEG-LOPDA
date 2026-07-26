# Mapa canónico Modo 50 — map-world-canonical-50-003.svg

Fecha: 2026-07-26
Rol: Dirección de Arte Cartográfico
Sucede a `map-world-canonical-50-002.svg`. Cierra los dos pendientes que dejó esa
entrega: solapes de rótulo y adyacencias que el backend permite pero el mapa no
comunicaba.

## 1. Las 5 adyacencias pendientes

Se atacaron en dos niveles. Primero se intentó recuperarlas como **frontera real**
moviendo semillas (búsqueda exhaustiva en `design/tools/tune-seeds2.py`, con la
restricción dura de que cada territorio siga conteniendo su ubicación geográfica
real). Lo que no se pudo, se comunica con **enlace táctico explícito**.

| Adyacencia | Estado en -002 | Estado en -003 |
|---|---|---|
| Chile ↔ Perú | sin comunicar | **frontera común real** (Bolivia dejó de tocar el Pacífico) |
| Arabia ↔ India | sin comunicar | **frontera común real** (Irán se corrió al norte) |
| Argentina ↔ Brasil | sin comunicar | **corredor terrestre** dibujado |
| Aral ↔ China | sin comunicar | **corredor terrestre** dibujado |
| China ↔ Siberia | sin comunicar | **corredor terrestre** dibujado |

La búsqueda de semillas sin restricción llegaba a 61/63 fronteras, pero lo hacía
mandando la semilla de Polonia a los Balcanes y la de Uruguay adentro de Brasil.
Se descartó: la honestidad geográfica vale más que dos fronteras. Con la
restricción activa el resultado es **60/63 fronteras reales** y los 50
territorios siguen conteniendo su ubicación real.

## 2. Cobertura visual completa de la adyacencia

Al revisarlo apareció algo más grande que las 5 señaladas: **las adyacencias
marítimas tampoco se comunicaban**. El backend declara 85 adyacencias en total y
-002 solo mostraba 67. Alaska↔Kamchatka, Brasil↔Sáhara, Chile↔Australia o
España↔Sáhara eran ataques legales sin ninguna marca en el mapa.

```
Adyacencias declaradas en total : 85
  visibles como frontera común  : 67
  visibles como enlace táctico  : 18
  sin comunicar                 :  0
```

Los enlaces viven en `<g id="layer-2b-adjacency-links" pointer-events="none">`,
sobre los territorios y bajo los rótulos. Son decorativos: sin ids de territorio,
sin hitboxes, sin labels. **No alteran ninguna adyacencia**; solo dibujan lo que
el backend ya permitía.

Alaska↔Kamchatka y Chile↔Australia se resuelven **envolviendo por el
antimeridiano**: el enlace sale por un borde del lienzo y entra por el opuesto,
como en cualquier mapa de mesa. Antes el trazo cruzaba el planeta entero por el
océano equivocado.

### Los 18 enlaces tácticos

| Adyacencia declarada | Cómo se comunica |
|---|---|
| China ↔ Siberia | corredor terrestre |
| Argentina ↔ Brasil | corredor terrestre |
| Aral ↔ China | corredor terrestre |
| Sáhara ↔ Brasil | paso marítimo |
| Islandia ↔ Suecia | paso marítimo |
| Groenlandia ↔ Terranova | paso marítimo |
| Gran Bretaña ↔ Islandia | paso marítimo |
| Australia ↔ Borneo | paso marítimo |
| Australia ↔ Java | paso marítimo |
| Islandia ↔ Groenlandia | paso marítimo |
| Madagascar ↔ Sudáfrica | paso marítimo |
| Alemania ↔ Gran Bretaña | paso marítimo |
| Japón ↔ Kamchatka | paso marítimo |
| Malasia ↔ Borneo | paso marítimo |
| Kenia ↔ Madagascar | paso marítimo |
| Egipto ↔ Italia | paso marítimo |
| Australia ↔ Chile | paso marítimo por el antimeridiano |
| Kamchatka ↔ Alaska | paso marítimo por el antimeridiano |

## 3. Rótulos

- Los badges de tropas quedan **siempre** dentro del territorio, sobre el polo de
  inaccesibilidad: son información de juego y no pueden migrar.
- El rótulo sí se mueve: primero busca lugar dentro del territorio y, si el
  racimo es muy denso, sale al mar con **línea de conducción** (4 casos).
- Cuerpo tipográfico proporcional al área (15–24 px).

Medición sobre el SVG final, cajas de texto reales:

```
rótulos: 50 | pares que se pisan: 0
```

Europa (España, Francia, Italia, Alemania, Polonia, Gran Bretaña, Suecia,
Islandia) e Insulindia (Malasia, Sumatra, Borneo, Java, Australia) quedan
legibles a 1366×768, que era el caso peor.

## 4. Contrato preservado (verificado)

```
XML válido: True | viewBox: 0 0 2560 1720 | viewBox único: True | sin transform: True
ids 50 | hitboxes 50
ids == TERRITORIES_50 del backend .............. True
data-territory == ids .......................... True
nombres visibles == nombres del backend ........ True
geometría de hitbox == geometría del territorio  True
layer-1-geo-base            pointer-events=none
layer-2-playable-territories pointer-events=none
layer-2b-adjacency-links     pointer-events=none
layer-3-hitboxes             pointer-events=all
layer-4-overlays             pointer-events=none
capa de enlaces sin ids/hitboxes/labels ........ True
layer-1 sigue no jugable, con Antártida y Ártico  True
los 50 territorios contienen su ubicación real .. 50/50
```

Backend, adyacencias y reglas: sin tocar. No se crearon ni eliminaron
territorios. Antártida y casquete ártico siguen no jugables.

## 5. Capturas

| Vista | Archivo |
|---|---|
| 1366×768 con labels | `test-results/canonical-v3-1366x768-labels.png` |
| 1366×768 sin labels | `test-results/canonical-v3-1366x768-nolabels.png` |
| 1920×1080 con labels | `test-results/canonical-v3-1920x1080-labels.png` |
| 1920×1080 sin labels | `test-results/canonical-v3-1920x1080-nolabels.png` |
| 2560×1440 sin labels | `test-results/canonical-v3-2560x1440-nolabels.png` |
| 3840×2160 sin labels | `test-results/canonical-v3-3840x2160-nolabels.png` |
| Seis jugadores | `test-results/canonical-v3-six-players.png` |
| Seleccionado + atacable | `test-results/canonical-v3-attack-state.png` |

## 6. Tabla de los 50 IDs preservados

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
