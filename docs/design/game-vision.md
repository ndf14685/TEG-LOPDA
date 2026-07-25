# ⚔️ TEG LOPDA: Game Vision & Core Philosophy Document
> **Director Creativo & Lead UI/UX Designer**  
> *Versión 1.0.0 — Documento de Visión de Producto*

---

## 1. Visión General del Juego

**TEG LOPDA** no es una aplicación web de nicho ni un simulador administrativo de mapas. Es un **videojuego social de estrategia táctica y competencia entre amigos**, diseñado para transformar las sesiones nocturnas de escritorio en experiencias memorables de bardeo, tensión, negociación, apuestas y traición.

El juego toma los principios tácticos y la claridad comunicativa de los grandes videojuegos de estrategia en tiempo real (RTS clasicos), combinándolos con la jugosidad visual, el suspense de dados en 3D y la capa social de tribuna activa vista en títulos AAA modernos.

---

## 2. El Principio Rector de los 2 Segundos

Cualquier jugador (activo, espectador o recién conectado) debe poder responder intuitivamente a estas 6 preguntas en **menos de 2 segundos**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EL PRINCIPIO RECTOR DE LOS 2 SEGUNDOS                    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. ¿De quién es el turno?   ──► Indicador de estandarte brillante + borde   │
│ 2. ¿Qué fase se juega?     ──► Insignia de fase (Refuerzo/Ataque/Fortify)  │
│ 3. ¿Qué hace el activo?     ──► Flechas animadas / Resplandor táctico       │
│ 4. ¿Qué pasa en el mapa?   ──► Banderines de tropas y fronteras en tensión │
│ 5. ¿Qué hago si espero?    ──► Panel de La Tribuna: Apuestas y Bardeo       │
│ 6. ¿Qué acaba de pasar?    ──► Zócalo del Relator IA + Historial en Vivo    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Pilares Fundamentales de Diseño

### Pilar 1: El Mapa como Protagonista Táctico
El tablero de guerra ocupa entre el **75% y el 85% del área útil de pantalla**. No hay paneles laterales que tapen los territorios. Toda la información clave (propietario, tropas, fronteras de conflicto) vive integrada en la topografía del mapa con estandartes y relieves.

### Pilar 2: Cero Formularios, 100% Interacción Directa
Se eliminan los selectores `<select>`, los inputs aislados y los botones de formulario. Todas las acciones se realizan mediante:
* **Drag-and-drop** (arrastrar flecha de ataque o ruta de reagrupamiento).
* **Menú Radial Táctico** flotante alrededor del país seleccionado.
* **Controles táctiles directos** (+1, +3, Máximo).

### Pilar 3: La Tribuna Activa (Active Waiting)
Estar esperando el turno ajeno deja de ser un tiempo muerto pasivo. Los jugadores en espera forman parte de la **Tribuna**, donde pueden:
* Apostar **Monedas LOPDA** a los resultados de las batallas.
* Disparar reacciones visuales y audios de bardeo sobre el mapa en vivo.
* Proponer pactos, alianzas y recompensas públicas sobre territorios.

### Pilar 4: Transmisión & Relator Deportivo Militar
La IA Comentarista actúa como un relator de transmisión deportiva en vivo. Con zócalo animado, retrato expresivo y síntesis de voz, reacciona a los combates, traiciones, rachas de dados y victorias dramáticas.

---

## 4. Filosofía de Monetización y Fairness

* **Cero Pay-to-Win**: No existen microtransacciones ni ventajas comprables con dinero real.
* **Monedas LOPDA**: Se ganan 100% dentro de la partida mediante predicciones acertadas, participaciones y rachas.
* **Modo Clásico vs Modo Caos**:
  * *Modo Clásico*: Las Monedas LOPDA son puramente cosméticas y sociales.
  * *Modo Caos*: Las Monedas permiten adquirir recursos tácticos mundanos (tropas mercenarias limitadas, inteligencia de mapa) con límites estrictos configurables por el administrador.
