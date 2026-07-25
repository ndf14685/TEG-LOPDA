# Frontend Current Brief - Claude

Fecha: 2026-07-25

## Estado

No habilitado para implementar pantallas nuevas.

## Condiciones para habilitacion

- Diseno de Vertical 1 aprobado por producto.
- Contrato de snapshot/eventos/mensajes sincronizado.
- Assets reales o fallbacks aprobados.
- Criterios de aceptacion visual y E2E definidos.

## Trabajo permitido ahora

- Diagnostico puntual de brechas entre UI actual y mockups.
- Preparar lista de componentes/archivos afectados por Vertical 1.
- No inventar reglas, apuestas, dados ni estados no provistos por backend.

## Pruebas obligatorias al habilitar

- `pnpm test`
- `pnpm typecheck`
- `pnpm build`
- E2E multi-contexto para Vertical 1.
- Capturas 1366x768 y 1920x1080.
