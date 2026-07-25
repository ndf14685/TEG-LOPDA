# Visual audit

## Impresión general
Salto notable de "formulario administrativo" a **UI de videojuego**: fondo oscuro de guerra, mapa protagonista con territorios coloreados por dueño, HUD superior de jugadores, dock lateral La Tribuna, viñeta ambiental con el color del jugador activo.

## Jerarquía y foco
- Foco claro en el mapa (centro, grande).
- Turno y fase arriba (TopHud + hud-phase).
- Acciones y contexto a la derecha (ESTADO DEL TURNO, Tribuna, Relator, Diplomacia, Bardeo, Chat).
- Instrucción persistente abajo-izquierda ("Tocá tus países: el menú radial coloca +1, +3 o el máximo").

## Legibilidad / contraste / escala
- Buen contraste general; números de tropas en círculos oscuros sobre países de color.
- **DEF-04**: en zonas densas el nombre del país y su insignia se solapan (Colombia/Perú, Chile/Argentina, Oriente Medio/India).

## Consistencia / assets
- Iconografía coherente (🪖 jugador, 👁️ espectador, dados por bando).
- Menú radial: en realidad es un popover lineal con el nombre del país + [+1][+3][MÁX (N)][✕]; claro, aunque "radial" es un nombre engañoso (nomenclatura, no bug).

## Resoluciones
- **1920x1080**: excelente, todo respira, sin overflow.
- **1366x768**: layout completo, sin scroll horizontal, legible. (`13-game-1366x768.png`)
- **390x844 (mobile)**: responsive sin overflow, pero el mapa queda chico y los toques serían fiddly (**DEF-05**). (`14-game-390x844.png`)

## Sensación de videojuego vs formulario
- Claramente del lado "videojuego". La Arena de combate, la viñeta ambiental, el HUD y La Tribuna aportan identidad. El único gran detractor de experiencia es el **modal bloqueante** de combate (DEF-01), que rompe la inmersión del que no ataca.

## Capturas
- `01-landing-1920.png`, `02-admin-cuartel-1920.png`, `04-lobby-*-1920.png`, `05-game-start-*-1920.png`, `06-radial-menu-nessi-1920.png`, `09..12-combat-*`, `13-game-1366x768.png`, `14-game-390x844.png`, `15-landing-390x844.png`.
