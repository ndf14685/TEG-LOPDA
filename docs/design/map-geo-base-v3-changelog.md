# Changelog de geometría — map-world-geographic-base-50-003.svg (V3)

Fecha: 2026-07-25
Rol: Dirección de Arte Cartográfico
Estado: entregado para revisión del PO (bloqueo P0 Modo 50)

## Qué cambió respecto de V1/V2

V1/V2 dibujaban los seis continentes como 6 curvas Bézier cerradas de 4-5 puntos
de control (`path.continent-mass`): blobs sin geografía. La V3 **no reutiliza
ningún path de V1/V2**. Toda la geometría se generó de cero con otro método:

- Cada costa está definida como una polilínea de coordenadas lon/lat de autoría
  propia (simplificación cartográfica de memoria, sin calcar ningún mapa
  comercial ni copiar IP).
- Proyección Mercator sobre el canvas `viewBox="0 0 2560 1440"` (lat 80°N a 58°S).
- Suavizado Catmull-Rom → curvas cúbicas, para look de atlas simplificado.
- 31 masas de tierra + 4 aguas interiores (V2 tenía 6 blobs y 0 islas).

Comparación visual: `test-results/geo-base-002-vs-003.png`.

## Cambios de silueta por continente

### América del Norte (108 vértices; V2: 5 puntos de control)
- Alaska con península de Seward y cola aleutiana; costa ártica canadiense.
- Bahía de Hudson completa con bahía James; península de Quebec/Labrador.
- Costa este con golfo de San Lorenzo, Nueva Escocia, cabo Cod y cabo Hatteras.
- Florida como península real; golfo de México con delta del Mississippi.
- Península de Yucatán, istmo centroamericano hasta Darién.
- Golfo de California y península de Baja California.
- Islas nuevas: Groenlandia (silueta propia, ya no un blob dentro de "NA"),
  Baffin, Victoria, Terranova, Cuba y La Española. Grandes Lagos como agua interior.

### América del Sur (90 vértices; V2: 4 puntos de control — era una cápsula)
- Costa caribeña Colombia/Venezuela con península de la Guajira y delta del Orinoco.
- Saliente nordeste de Brasil (cabo São Roque) y desembocadura del Amazonas.
- Costa atlántica hasta el Río de la Plata (indentación explícita).
- Patagonia que se afina hacia el sur con golfos San Matías/San Jorge,
  Tierra del Fuego y archipiélago chileno.
- Costa del Pacífico con el codo de Arica y la saliente de Piura.
- Ya no es cápsula ni triángulo: es la silueta continental reconocible.

### Europa (parte de la masa euroasiática continua; V2: pieza flotante ovalada)
- Iberia con golfo de Vizcaya; Bretaña; canal de la Mancha.
- Península de Jutlandia, mar Báltico con golfos de Botnia y Finlandia,
  península escandinava completa con costa noruega y cabo Norte, mar Blanco.
- Italia como bota con Adriático; Grecia/Balcanes con Peloponeso; Anatolia.
- Mar Negro con Crimea y mar Caspio como aguas interiores.
- Islas: Gran Bretaña, Irlanda e Islandia con siluetas propias.

### África (76 vértices; V2: blob romo)
- Costa mediterránea con golfo de Sidra y delta del Nilo; separación real
  con Eurasia por el mar Rojo (Sinaí del lado asiático).
- Saliente de África Occidental con cabo Verde/Dakar y codo del golfo de Guinea.
- Cuerno de África (cabo Guardafui) explícito.
- Estrechamiento hacia el cabo (Agulhas/Buena Esperanza).
- Madagascar como isla separada.

### Asia (parte de la masa euroasiática continua; V2: pieza flotante)
- Costa ártica siberiana con Yamal, Taimyr y delta del Lena; Chukotka
  recortada en el borde este del canvas (convención Mercator estándar).
- Kamchatka, mar de Ojotsk, Sajalín, arco japonés (Hokkaido/Honshu/Kyushu).
- Península de Corea, golfo de Bohai, Shandong, costa china.
- Indochina con golfos de Tonkín/Tailandia y península malaya.
- Subcontinente indio triangular con Sri Lanka; deltas del Ganges e Irrawaddy.
- Península arábiga con golfo Pérsico, Qatar/Hormuz y costa de Omán.
- Sudeste insular: Borneo, Sumatra, Java, Célebes, Filipinas, Taiwán.

### Oceanía (54 vértices; V2: óvalo aislado)
- Australia con golfo de Carpentaria, cabo York, Gran Bahía Australiana,
  cabo Leeuwin y bahía Shark: silueta reconocible, no óvalo.
- Nueva Guinea, Tasmania y las dos islas de Nueva Zelanda como piezas propias.

## Estética

- Mesa de guerra táctica: océano azul profundo desaturado con viñeta radial,
  tierra en gris azulado con gradiente sutil, línea de costa acero desaturado,
  halo de plataforma continental difuminado, retícula de meridianos/paralelos
  al 5% y ecuador punteado.
- Sin labels, sin badges, sin hitboxes, sin clases `p-*`, sin HUD, sin brújula
  ni rutas decorativas: la geografía es la protagonista.
- Verificado bajo overlay de territorios al 32% de opacidad con los seis
  colores de jugador: las costas siguen leyéndose
  (`test-results/geo-base-003-overlay-32pct-1920x1080.png`).

## Evidencia

- `test-results/geo-base-003-pure-1366x768.png`
- `test-results/geo-base-003-pure-1920x1080.png`
- `test-results/geo-base-003-pure-2560x1440.png`
- `test-results/geo-base-003-pure-3840x2160.png`
- `test-results/geo-base-003-overlay-32pct-1920x1080.png`
- `test-results/geo-base-003-overlay-32pct-1366x768.png`
- `test-results/geo-base-002-vs-003.png`
