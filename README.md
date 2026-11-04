# La Escena 1: El Traslado (1976) — Experiencia 3D Web PBR

Experiencia interactiva 3D cinemática y juego de sigilo narrativo ambientado en un camino rural clandestino durante los años 70 en Argentina. Construido con **Three.js (r160)**, **Pipeline PBR Fotográfico Real**, **Web Audio API** y optimizado para despliegue directo en **Vercel**.

---

## 🎨 Paquetes de Texturas PBR Fotográficas Integradas

Se integraron los 5 paquetes de texturas PBR (mapas *Diffuse*, *Normal* y *Roughness* a 1K) procedentes de **ambientCG** y **Poly Haven**:

1. **Arpillera / Burlap (Capuchas de los cautivos):**
   * Asset: `fabric_pattern_07` (Poly Haven) / `Fabric048` (ambientCG).
   * Trama gruesa, fibras abiertas y porosidad áspera de tela de saco.
2. **Madera Astillada / Tablones Viejos (Caja de carga y cajones):**
   * Asset: `weathered_planks` (Poly Haven) / `Wood049` (ambientCG).
   * Vetas erosionadas, hendiduras longitudinales y astillado por intemperie.
3. **Metal Oxidado / Pintura Militar Desgastada (Chasis, cabina y parantes):**
   * Asset: `green_metal_rust` (Poly Haven) / `Metal007` (ambientCG).
   * Pintura verde oliva militar descascarada con corrosión y herrumbre.
4. **Tierra y Barro Húmedo (Camino rural y huellas de rodadura):**
   * Asset: `brown_mud` / `muddy_tracks` (Poly Haven) / `Ground037` (ambientCG).
   * Barro oscuro pampeano con reflectividad especular en charcos.
5. **Lona Militar Arrugada (Toldo superior del camión):**
   * Asset: `Fabric026` (ambientCG).
   * Tejido de lona pesado, arrugas tensadas y pliegues entre arcos.

---

## 💡 Iluminación Cinemática Equilibrada

* **Luz de Luna (DirectionalLight):** Color plateado frío (`#8faac9`), intensidad `1.15`, con ángulo semi-lateral que baña el camino, el toldo y el entablonado.
* **Relleno Hemisférico (`HemisphereLight`):** Bóveda celeste azul noche (`0x28384a`) y rebote de tierra (`0.42`), asegurando que las sombras no se empasten en negro y revelando todos los volúmenes.
* **Linterna en "L" de la Compuerta (`SpotLight`):** Haz cálido tungsteno ámbar (`#ffb554`, intensidad `8.5`) enfocado sobre la zapatilla *Flecha*, la libreta y el Cautivo Hero.
* **Faros Delanteros y Luces Traseras:** Haces cálidos proyectados hacia adelante en la niebla y destellos rojos sobre neumáticos y barro.

---

## 🚀 Despliegue en Vercel

```bash
npx vercel --prod
```
O conecta tu repositorio en [vercel.com](https://vercel.com) importando `estamos-sanando/nnn`.

---

## 💻 Ejecución Local

```bash
# Con Node:
npx serve .

# O con Python:
python -m http.server 8000
```
Abre en tu navegador `http://localhost:8000` o `http://localhost:3000`.
