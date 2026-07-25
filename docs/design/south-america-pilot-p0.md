# 🗺️ P0 MAPA: Entregable de Geometría Realista — Región Piloto América del Sur
> **Director Creativo, Lead Game UI/UX Designer & Director de Arte**  
> *Versión 2.3.0 — Geometría Geográfica Encastada, Declaración de Alcance Modo 26 vs Modo 50 y Arquitectura en 4 Capas*

---

## 1. Declaración de Alcance de IDs: Modo 26 vs Modo 50

Aclaración explícita de alcance técnico de IDs para evitar ambigüedades:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ALCANCE DE IDS SEGÚN MODO DE MAPA                         │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🗺️ MODO 26 (TEG Estándar — 5 Países en América del Sur)                    │
│ 1. territory-south-america-colombia   ──► Colombia                         │
│ 2. territory-south-america-peru       ──► Perú                             │
│ 3. territory-south-america-brazil     ──► Brasil                           │
│ 4. territory-south-america-chile      ──► Chile                            │
│ 5. territory-south-america-argentina  ──► Argentina                        │
├─────────────────────────────────────────────────────────────────────────────┤
│ 🗺️ MODO 50 (TEG Extendido — 8 Países en América del Sur)                   │
│ 1. territory-south-america-colombia   ──► Colombia                         │
│ 2. territory-south-america-venezuela  ──► Venezuela (Nuevo en Modo 50)     │
│ 3. territory-south-america-peru       ──► Perú                             │
│ 4. territory-south-america-brazil     ──► Brasil                           │
│ 5. territory-south-america-bolivia    ──► Bolivia (Nuevo en Modo 50)       │
│ 6. territory-south-america-chile      ──► Chile                            │
│ 7. territory-south-america-argentina  ──► Argentina                        │
│ 8. territory-south-america-uruguay    ──► Uruguay (Nuevo en Modo 50)       │
└─────────────────────────────────────────────────────────────────────────────┘
```

*Estado de Compatibilidad*: **100% de IDs conservados sin renombrar ni modificar** dentro de sus respectivos modos.

---

## 🌎 2. Justificación Geográfica de la Nueva Geometría (Cero Blobs / Cero Cápsulas)

La nueva geometría abandona las formas ovoides confusas y se construye como un **rompecabezas geográfico encastado**:

1. **Brasil (`territory-south-america-brazil`)**: Se dibuja con el prominente abombamiento oriental sobre la costa Atlántica, bordeando a Venezuela, Colombia, Perú, Bolivia y Uruguay.
2. **Argentina (`territory-south-america-argentina`)**: Cono Sur real, amplio al norte (región pampeana/chaco) y afinándose hacia la Patagonia y Tierra del Fuego, lindando con Chile por los Andes.
3. **Chile (`territory-south-america-chile`)**: Franja andina delgada e icónica que corre paralela al Océano Pacífico al oeste de Argentina y Perú.
4. **Uruguay (`territory-south-america-uruguay`)**: Pieza pequeña y redondeada en la costa atlántica sobre el estuario del Río de la Plata entre Argentina y Brasil.
5. **Colombia / Venezuela**: Ocupan el borde norte Caribe/Pacífico conectando con América Central.
6. **Perú / Bolivia**: Ubicados en la franja andina del Pacífico (Perú) y el interior mediterráneo (Bolivia).

---

## 🎨 3. Disposición de Etiquetas vs Badges de Tropas (Sin Choques)

* **Etiquetas de Nombre (`.territory-label`)**: Posicionadas estrictamente en el **tercio superior** de cada polígono.
* **Badges de Ejércitos (`.badge-circle` + `.badge-text`)**: Posicionados estrictamente en el **tercio inferior**.
* **Limpieza de HUD**: Eliminados todos los textos genéricos de RTS tipo `GLOBAL DOMINATION` o recursos militares falsos. El HUD se limita a los datos autoritativos de TEG-LOPDA.

---

## 📱 4. Prototipo Navegable con Toggle de Modo (Modo 26 / Modo 50)

Acceso directo a la prueba interactiva de la región piloto:
👉 **Prototipo Piloto**: [`frontend/public/prototype/south-america-pilot.html`](file:///home/ndf/workspace/TEG-LOPDA/frontend/public/prototype/south-america-pilot.html)

**Nuevos Controles de Validación**:
* Botón `🗺️ Modo 50 (8 Países)` vs `🗺️ Modo 26 (5 Países)`: Permite conmutar en vivo entre el alcance de 5 y 8 territorios.
* Botón `🙈 Sin Etiquetas (<1s)`: Verificación de reconocibilidad inmediata.
* Botón `🚀 Ataque en Ejecución`: Muestra la flecha vectorial animada como overlay hacia África.
