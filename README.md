# La Escena 1: El Traslado (1976) — Experiencia 3D Cinemática Web & Godot 4

Experiencia interactiva 3D cinemática y juego de sigilo narrativo ambientado en un camino rural clandestino durante los años 70 en Argentina. Construido con **Three.js (r160)**, **Pipeline PBR Cinemático**, **Web Audio API** y optimizado para despliegue directo en **Vercel** y desarrollo en **Godot 4**.

---

## 🎨 Pipeline Gráfico & Calibración PBR (Technical Art)

Intervención sobre calidad visual, shaders e iluminación con estética cinematográfica testimonial (estilo *Garage Olimpo* y *La Noche de los Lápices*):

1. **Iluminación y Entorno (World Environment):**
   * **HDRI Rural Nocturno:** Integración de mapa de entorno (`moonlit_night.hdr`) para reflejos físicos especulares en metales y charcos.
   * **Luz de Luna (DirectionalLight):** Tono frío desaturado (`#8faac9`), intensidad calibrada (0.38) y sombras suaves PCF.
   * **Niebla Volumétrica Baja (FogExp2):** Tono oscuro (`#0a0d12`) que funde la vegetación y el camino en la penumbra pampeana.
   * **Linterna Militar en "L":** Tinte tungsteno sucio (`#c99a4e`), atenuación cuadrática real (`decay = 2.0`), cono difuso y parpadeo diegético.

2. **Calibración de Materiales PBR:**
   * **Capuchas de arpillera (Burlap):** Rugosidad 0.98, metalicidad 0.0 y mapa de normales marcado resaltando la trama áspera de saco.
   * **Caja y tablones de madera:** Textura con marcado contraste de rugosidad entre vetas secas (0.88) y zonas húmedas/grasa (0.38) con relieve de astillado.
   * **Chasis y herrajes oxidados:** Metalicidad 0.72 con pintura verde oliva militar descascarada y micro-relieve de herrumbre.
   * **Barro con charcos reflectantes:** Rugosidad de 0.12 a 0.18 en las hendiduras/huellas de neumáticos para generar reflejos especulares de la luna y las luces traseras.
   * **Toldo de lona militar:** Rugosidad 0.92 con mapa de normales simulando arrugas pesadas y pliegues tensados entre arcos.

3. **Post-Procesado Cinematográfico (`EffectComposer`):**
   * **SSAO (Screen Space Ambient Occlusion):** Contacto sutil de figuras y objetos con el suelo entablonado y profundidad en pliegues.
   * **UnrealBloom:** Resplandor sutil en filamentos incandescentes y luces distantes.
   * **Color Grading de Época:** Negros lavados/aplastados teñidos hacia azul petróleo (`#141b1f`) y medios tonos verdosos oliva (`#1f2824`).
   * **Film Grain Monocromático:** Granulado analógico procedural de 16mm/35mm que rompe la estética digital limpia.
   * **Vignette:** Oscurecimiento perimetral óptico para acentuar el encierro bajo el toldo.

4. **Compatibilidad Godot 4.x:**
   * Scripts y shaders incluidos en `godot/` (`acto1_setup_visual.gd` y `film_grain_vignette.gdshader`) para replicar 1:1 el pipeline en el motor de juego Godot.

---

## 🚀 Despliegue en Vercel

El proyecto está configurado con `vercel.json` optimizado para la entrega de modelos binarios 3D `.glb` y mapas `.hdr` con compresión y caché de borde.

### Opción A: Conectar repositorio en Vercel Dashboard (Recomendado)
1. Ingresa a [vercel.com](https://vercel.com) -> **Add New Project**.
2. Conecta tu cuenta e importa el repositorio `estamos-sanando/nnn`.
3. Vercel detectará el sitio estático automáticamente.
4. Haz clic en **Deploy**.

### Opción B: Despliegue con CLI
```bash
npx vercel --prod
```

---

## 💻 Ejecución y Prueba Local

```bash
# Con Node / npx:
npx serve .

# O con Python:
python -m http.server 8000
```
Abre en tu navegador `http://localhost:8000` o `http://localhost:3000`.

---

## 🎮 Controles e Interactividad

* **Selector de Cámaras de Dirección Cinemática:**
  * `[01] VISTA GENERAL`: Plano general de 3/4 trasero con el camión, niebla rasante y el puesto militar lejano.
  * `[02] CAUTIVO HERO`: Plano medio dramático sobre el cautivo central sentado en la compuerta.
  * `[03] INTERIOR DE CAJA`: Perspectiva claustrofóbica mirando hacia los cautivos de fondo.
  * `[04] INSPECCIÓN PROPS`: Enfoque sobre la zapatilla Flecha, la libreta clandestina y la linterna en L.
  * `[05] MODO LIBRE`: Control orbital 360° con ratón o gestos táctiles.
* **Inspección de Evidencia 3D (Raycasting):**
  * Haz clic en los objetos o cautivos para abrir las fichas desclasificadas históricas.
* **Paisaje Sonoro Diegético (Web Audio API):**
  * Botón `🔊 AUDIO`: Síntesis procedural en tiempo real del viento nocturno y el motor diesel en ralentí.
