# 🔄 TEG LOPDA: UX Flow & Screen Architecture
> **Lead UI/UX Designer**  
> *Versión 1.0.0 — Mapa Completo de Flujos y 24 Pantallas del Sistema*

---

## 1. Arquitectura de Estados de Pantalla

El sistema de juego se estructura en **24 pantallas/estados de interfaz**, agrupados en 5 macro-etapas de la experiencia:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CICLO DE VIDA DEL JUGADOR                           │
├───────────────┬────────────────┬────────────────┬───────────────────────────┤
│ 1. INGRESO    │ 2. LOBBY       │ 3. BATALLA     │ 4. TRIBUNA & APUESTAS     │
│ (Pantallas    │ (Pantallas     │ (Pantallas     │ (Pantallas 15-20)         │
│  1-4)         │  5-6)          │  7-14)         │                           │
└───────────────┴────────────────┴────────────────┴───────────────────────────┘
```

---

## 2. Definición Detallada de las 24 Pantallas

### 1. Landing (`screen-landing-001`)
* **Propósito**: Bienvenida épica a la sala de mando.
* **Componentes**: Fondo 3D animado de mapa táctico con niebla, botón "Crear Partida de Guerra", input de código de invitación rápida.

### 2. Creación de Partida (`screen-game-create-001`)
* **Propósito**: Configuración del organizador.
* **Componentes**: Selector de modo de juego (*Clásico 50* vs *Mega World 100*), toggle de Nivel de Humor del Comentarista (0 a 4), toggle de Modo Caos (Apuestas tácticas).

### 3. Administración de Jugadores (`screen-admin-players-001`)
* **Propósito**: Gestión de plazas para el organizador.
* **Componentes**: Lista de 4 a 10 asientos con roles (Player, Spectator, AI Player), botón de expulsar (Kick), copiar link.

### 4. Link Personalizado / Join (`screen-player-join-001`)
* **Propósito**: Aterrizaje del invitado.
* **Componentes**: Tarjeta de invitación heráldica con apodo editable, selección de color/avatar, confirmación de ingreso a la mesa.

### 5. Lobby de Espera (`screen-lobby-room-001`)
* **Propósito**: Concentración previa a la guerra.
* **Componentes**: Avatares 3D con estado "Listo / Preparado", chat de sala con soundboard de bardeo rápido, botón "Iniciar Guerra" para el admin.

### 6. Inicio de Partida (`screen-game-init-001`)
* **Propósito**: Animación de repartición del mundo.
* **Componentes**: Cámara cinematográfica descendente sobre el tablero, asignación animada de territorios y entrega de Objetivo Secreto holográfico.

### 7. Turno Propio (`screen-turn-own-001`)
* **Propósito**: Interfaz de mando para el jugador activo.
* **Componentes**: Vignette dorada ambiental, resplandor en países propios, barra de fase superior, menú radial al hacer click.

### 8. Turno Ajeno (`screen-turn-other-001`)
* **Propósito**: Vista de espectador/espera activa.
* **Componentes**: Mensaje explícito de quién juega en la marquesina superior, acceso desplegable a La Tribuna y Mercado de Apuestas.

### 9. Fase de Refuerzos (`screen-phase-reinforcement-001`)
* **Propósito**: Colocación táctica de tropas.
* **Componentes**: Contador de tropas disponibles en la parte superior, resplandor verde en países propios, click o tap para sumar +1, +3 o Máximo.

### 10. Selección de Ataque (`screen-phase-attack-select-001`)
* **Propósito**: Definición del objetivo de conquista.
* **Componentes**: Arrastrar desde país de origen (mínimo 2 ejércitos) hacia país enemigo adyacente. Flecha roja de puntería con probabilidad estimada.

### 11. Arena de Combate (`screen-combat-arena-001`)
* **Propósito**: Tensión de la batalla en tiempo real.
* **Componentes**: Desenfoque de mapa de fondo, bandeja metálica de dados en el centro, retratos de Atacante vs Defensor con tropas restantes.

### 12. Resultado de Dados (`screen-combat-dice-result-001`)
* **Propósito**: Revelado dramático de tiradas.
* **Componentes**: Física de dados chocando, orden de mayor a menor par a par, chispas y explosiones de partículas en las tropas perdidas.

### 13. Conquista de Territorio (`screen-territory-conquered-001`)
* **Propósito**: Celebración de victoria territorial.
* **Componentes**: Estandarte del conquistador clavándose en el país ocupado, fanfarria sonora, diálogo para deslizar ejércitos de ocupación.

### 14. Fase de Reagrupamiento (`screen-phase-fortify-001`)
* **Propósito**: Movimiento táctico de fin de turno.
* **Componentes**: Ruta azul brillante entre territorios propios conectados, control deslizante (slider) de tropas a mover dejando al menos 1 en origen.

### 15. La Tribuna (`screen-tribune-main-001`)
* **Propósito**: Módulo social de espera activa.
* **Componentes**: Chat de bardeo rápido, panel de Monedas LOPDA, ranking de apostadores en tiempo real, soundboard de audios.

### 16. Apuesta Abierta (`screen-bet-open-001`)
* **Propósito**: Mercado de predicciones pre-combate.
* **Componentes**: Popup efímero: *"¿Conquista Argentina este turno?"*, opciones con cuotas (1.5x, 3.0x), temporizador de 5 segundos para cerrar apuesta.

### 17. Resultado de Apuesta (`screen-bet-result-001`)
* **Propósito**: Recompensa de la predicción.
* **Componentes**: Lluvia de Monedas LOPDA animadas para los ganadores, aviso dramático *"¡Toda la mesa se equivocó!"* si fallan.

### 18. Propuesta de Negociación / Pacto (`screen-pact-propose-001`)
* **Propósito**: Diplomacia de pasillo entre jugadores.
* **Componentes**: Envió de propuesta de pacto de no agresión con apretón de manos animado e indicador en el avatar de ambos jugadores.

### 19. La Traición (`screen-pact-break-001`)
* **Propósito**: Evento dramático de ruptura diplomática.
* **Componentes**: Pantalla en tono carmesí/violeta, sonido de daga apuñalando, aviso del Relator IA: *"¡TRAICIÓN! [Nessi] rompió el pacto con [Daro]"*.

### 20. Eliminación de Jugador (`screen-player-eliminated-001`)
* **Propósito**: Muerte de una potencia en la guerra.
* **Componentes**: El avatar del jugador eliminado se quema en cenizas con marcha fúnebre, sus tarjetas pasan al conquistador.

### 21. Victoria de Partida (`screen-victory-celebration-001`)
* **Propósito**: Climax y coronación del campeón.
* **Componentes**: Explosión de fuegos artificiales tácticos, estandarte gigante del ganador, cámara orbitando el mapa dominado.

### 22. Infografía de Estadísticas Finales (`screen-postgame-stats-001`)
* **Propósito**: Resumen histórico del bardeo.
* **Componentes**: Tablas comparativas: *"El más traidor"*, *"El rey de los dados"*, *"El mejor apostador"*, *"El más mufado"*.

### 23. Pantalla de Reconexión (`screen-reconnect-sync-001`)
* **Propósito**: Recuperación transparente de sesión.
* **Componentes**: Banner discreto en la parte superior *"Sincronizando estado con el servidor..."* sin bloquear la vista del mapa.

### 24. Partida Pausada / Error (`screen-game-paused-001`)
* **Propósito**: Estado de pausa administrativa.
* **Componentes**: Cortina de cuero sobre el tablero con reloj congelado y mensaje del administrador.
