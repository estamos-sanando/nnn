# La Escena 1: El Traslado (1976) — Experiencia 3D Cinemática Web

Experiencia interactiva 3D cinemática y juego de sigilo narrativo ambientado en un camino rural clandestino durante los años 70 en Argentina. Construido con **Three.js (r160)**, **Pipeline PBR WebGL**, **Web Audio API** y optimizado para despliegue directo de alto rendimiento en **Vercel**.

---

## 🎨 Pipeline Gráfico & Calibración PBR (100% WebGL)

Intervención sobre calidad visual, shaders e iluminación con estética cinematográfica testimonial (estilo *Garage Olimpo* y *La Noche de los Lápices*):

1. **Iluminación y Entorno (World Environment):**
   * **Cielo Nocturno PMREM Procedural:** Generación instantánea en memoria sin descargas pesadas para cálculo físico de reflejos especulares en metales, charcos y lona.
   * **Luz de Luna (DirectionalLight):** Tono frío desaturado (`#8faac9`), intensidad calibrada (`0.38`) y sombras suaves PCF.
   * **Niebla Volumétrica Baja (FogExp2):** Tono oscuro (`#0a0d12`) que funde la vegetación y el camino en la penumbra pampeana.
   * **Linterna Militar en "L":** Tinte tungsteno sucio (`#c99a4e`), atenuación cuadrática real (`decay = 2.0`), cono difuso y parpadeo diegético.

2. **Calibración de Materiales PBR:**
   * **Capuchas de arpillera (Burlap):** Rugosidad 0.98, metalicidad 0.0 y mapa de normales marcado resaltando la trama áspera de saco.
   * **Caja y tablones de madera:** Textura con marcado relieve de vetas longitudinales y astillado.
   * **Chasis y herrajes oxidados:** Metalicidad 0.72 con pintura verde oliva militar descascarada y micro-relieve de herrumbre.
   * **Barro con charcos reflectantes:** Rugosidad de 0.12 a 0.18 en las hendiduras/huellas de neumáticos para generar reflejos especulares de la luna y las luces traseras.
   * **Toldo de lona militar:** Rugosidad 0.92 con mapa de normales simulando arrugas pesadas y pliegues tensados entre arcos.

3. **Atmósfera y Grano Fílmico:**
   * **Film Grain Monocromático:** Granulado analógico procedural de 16mm/35mm que rompe la estética digital limpia a 60 FPS sin sobrecargar la GPU.
   * **Vignette Óptico:** Caída de luz perimetral suave para intensificar el encierro bajo el toldo.

---

## 🚀 Despliegue en Vercel

El proyecto está configurado con `vercel.json` optimizado para la entrega de modelos binarios 3D `.glb` con compresión y caché de borde.

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
