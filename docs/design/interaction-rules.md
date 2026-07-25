# 🖱️ TEG LOPDA: Reglas de Interacción y Menú Radial Contextual
> **Lead UI/UX Designer**  
> *Versión 1.0.0 — Manual de Interacción Directa sobre el Mapa*

---

## 1. Eliminación Total de Formularios Web

En **TEG LOPDA** está estrictamente prohibido usar elementos de formulario tradicional (`<select>`, `<input type="number">` aislados, `<form>`). Toda acción del jugador se ejecuta mediante **gestos directos sobre los territorios del mapa**.

---

## 2. El Menú Radial Táctico (Radial Context Menu)

Al hacer click o tap sobre un territorio propio en tu turno, aparece un **Menú Radial flotante de 3 a 4 opciones** alrededor del centro geométrico del país:

```
                      [ 🪖 REFORZAR ]
                             │
     [ 🛡️ FORTIFICAR ] ─── ( PAÍS ) ─── [ ⚔️ ATACAR ]
                             │
                      [ 🃏 VER TARJETA ]
```

### Opciones y Comportamiento del Menú Radial:
1. **🪖 Reforzar (Solo en Fase de Refuerzos)**:
   * Muestra botones rápidos: `+1`, `+3`, `MÁXIMO`.
   * Al tocar, la tropa cae en el país con sonido háptico `Clank` y partículas de brillo.
2. **⚔️ Atacar (Solo en Fase de Ataque)**:
   * Al presionar el botón de ataque (o arrastrar directo desde el país), se activa la **Flecha de Puntería Táctica (Vector Targeting Arrow)**.
3. **🛡️ Fortificar (Solo en Fase de Reagrupamiento)**:
   * Al seleccionar, se iluminan únicamente los territorios aliados limítrofes conectados por frontera o mar.

---

## 3. Vector Targeting (Flecha de Puntería por Arrastre)

Los jugadores acostumbrados a RTS o MOBAs pueden simplemente **hacer click y arrastrar** desde un territorio propio hacia un territorio enemigo:

```
  [ ARGENTINA (5) ] ═════════════════════════► 💥 [ BRASIL (3) ]
  (País Origen)          Flecha Roja               (País Objetivo)
                       Animada con Arco
```

* **Validación Visual**:
  * Si el destino es un enemigo válido: La flecha se vuelve **Rojo Fuego** con el indicador *"3 Dados vs 3 Dados"*.
  * Si el destino es un aliado: La flecha se vuelve **Azul Táctico** indicando *"Reagrupar Tropas"*.
  * Si el destino es inválido (no limítrofe): La flecha se vuelve **Gris Punteado** y no permite soltar el click.
