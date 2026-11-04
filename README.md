# La Escena 1: El Traslado (1976) — Experiencia 3D Cinemática Web

Experiencia interactiva 3D cinemática y juego de sigilo narrativo ambientado en un camino rural clandestino durante los años 70 en Argentina. Construido con **Three.js**, **GLTF/GLB PBR**, **Web Audio API** y optimizado para despliegue directo en **Vercel**.

---

## 🚀 Despliegue en Vercel

El proyecto está configurado con `vercel.json` optimizado para la entrega de modelos binarios 3D `.glb` con compresión y caché de borde.

### Opción A: Despliegue con 1 comando vía Vercel CLI
En la terminal de tu máquina (PowerShell o CMD), dentro de esta carpeta (`d:\jeugosnacho`):
```bash
npx vercel
```
* Sigue las instrucciones interactivas (Enter en todas las opciones por defecto).
* ¡Tu escena 3D estará en línea con HTTPS y CDN global en menos de 1 minuto!

Para desplegar a producción definitiva:
```bash
npx vercel --prod
```

### Opción B: Conectar repositorio en Vercel Dashboard
1. Sube esta carpeta a un repositorio de GitHub / GitLab.
2. Ingresa a [vercel.com](https://vercel.com) -> **Add New Project** -> Selecciona el repositorio.
3. Vercel detectará automáticamente el sitio estático (`index.html` + `public/`).
4. Haz clic en **Deploy**.

---

## 💻 Ejecución y Prueba Local

Para abrirlo en tu navegador localmente antes de desplegar:

### Con Node.js / NPX:
```bash
npx serve .
```
o con Vite:
```bash
npx vite
```
Abre en tu navegador `http://localhost:3000` o `http://localhost:5173`.

### Con Python:
```bash
python -m http.server 8000
```
Abre en tu navegador `http://localhost:8000`.

---

## 🎮 Controles e Interactividad en la Web

* **Selector de Cámaras de Dirección Cinemática:**
  * `[01] MASTER CINEMÁTICA`: Plano general de 3/4 trasero con el camión, la compuerta abatida, niebla rasante pampeana y resplandor de la base militar lejana.
  * `[02] CAUTIVO HERO`: Plano medio dramático enfocado en el cautivo central sentado en la compuerta, con la capucha de arpillera, soga al cuello, manos atadas a la espalda y la zapatilla *Flecha*.
  * `[03] INTERIOR CAJA`: Perspectiva claustrofóbica desde las profundidades del toldo rasgado mirando hacia los cautivos de fondo y la salida trasera.
  * `[04] INSPECCIÓN FLECHA`: Plano de inspección detallado sobre los objetos interactivos del piso de madera (zapatilla Flecha gastada, libreta de campo clandestina y linterna en L).
  * `[05] MODO LIBRE 360°`: Control orbital manual completo (rotar con clic izquierdo / arrastre táctil, paneo con clic derecho, zoom con rueda).
* **Inspección de Evidencia 3D (Raycasting):**
  * Haz clic sobre la **Zapatilla Flecha**, la **Libreta de Apuntes**, la **Linterna Militar**, el **Cautivo Central** o la **Radio de Campaña** para abrir el informe desclasificado con detalles históricos.
* **Paisaje Sonoro Diegético (Web Audio API):**
  * Botón `🔊 AUDIO`: Activa la síntesis procedural en tiempo real del viento nocturno pampeano y el murmullo grave del motor diesel en ralentí.
* **Pantalla Completa:**
  * Botón `⛶ PANTALLA COMPLETA` para una experiencia inmersiva cinematográfica.

---

## 📁 Estructura del Proyecto

* `index.html`: Aplicación web interactiva completa (Three.js r160, OrbitControls, GSAP, Web Audio API y HUD temático).
* `escena1_el_traslado.glb`: Modelo 3D ensamblado completo en formato binario GLTF (12.0 MB).
* `public/escena1_el_traslado.glb`: Copia para servido estático en Vite/Vercel.
* `vercel.json`: Configuración de headers MIME `model/gltf-binary` y caché inmutable para Vercel.
* `escena1_el_traslado.blend`: Escena fuente editable en Blender 5.x LTS.
* `renders/`: Renders cinemáticos de alta resolución de las 4 cámaras principales.
* `build/`: Scripts procedurales Python generadores de la escena completa.

