# Asistente-Auditivo-Raspberry-Pi

Un dispositivo wearable de asistencia auditiva con Raspberry Pi Zero y MicroPython. 

# Wearable Auditivo — Clasificador de Sonidos
### Raspberry Pi Zero / Pico + MicroPython

---

## Estructura de archivos

```
/
├── main.py              ← Punto de entrada (se ejecuta al arrancar)
├── audio_sampler.py     ← Captura de audio (ADC o I2S)
├── sound_classifier.py  ← FFT + motor de reglas
├── visual_response.py   ← LEDs NeoPixel + pantalla ST7789
└── README.md
```

---

## Componentes de hardware

| Componente         | Modelo sugerido          | Precio aprox. |
|--------------------|--------------------------|---------------|
| Microcontrolador   | Raspberry Pi Pico W      | $6 USD        |
| Micrófono analógico| MAX4466 breakout         | $2 USD        |
| Micrófono digital  | INMP441 (I2S) — mejor    | $3 USD        |
| LEDs               | WS2812B (tira 5–8 LEDs)  | $3 USD        |
| Pantalla           | ST7789 2" 240×135 SPI    | $8 USD        |
| Batería            | LiPo 1000 mAh + módulo   | $5 USD        |
| Carcasa            | Impresión 3D / custom    | variable      |

---

## Conexiones GPIO (Raspberry Pi Pico)

### Micrófono analógico (MAX4466)
```
MAX4466 VCC  → 3.3V
MAX4466 GND  → GND
MAX4466 OUT  → GP26 (ADC0)
```

### Micrófono digital (INMP441 — recomendado)
```
INMP441 VDD  → 3.3V
INMP441 GND  → GND
INMP441 SD   → GP12 (I2S DATA)
INMP441 SCK  → GP10 (I2S BCLK)
INMP441 WS   → GP11 (I2S LRCLK)
INMP441 L/R  → GND  (canal izquierdo)
```

### LEDs NeoPixel WS2812B
```
NeoPixel VCC → 5V (o VBUS)
NeoPixel GND → GND
NeoPixel DIN → GP15
```
> Añade un resistor de 300–470 Ω en serie en la línea DIN.

### Pantalla ST7789 2"
```
TFT VCC  → 3.3V
TFT GND  → GND
TFT SCK  → GP18 (SPI0 SCK)
TFT SDA  → GP19 (SPI0 MOSI)
TFT CS   → GP17
TFT DC   → GP16
TFT RST  → GP20
TFT BL   → 3.3V (o GP con PWM para control de brillo)
```

---

## Instalación

### 1. Flash de MicroPython
Descarga el firmware más reciente para tu placa desde:
- https://micropython.org/download/RPI_PICO/

Flashea con:
```bash
# Con picotool o arrastrando el .uf2 al Pico en modo BOOTSEL
```

### 2. Librerías necesarias
Instala desde REPL con `mip` (MicroPython package manager):
```python
import mip
mip.install("neopixel")          # incluida en MicroPython estándar
# Para st7789: clonar y copiar manualmente
# https://github.com/russhughes/st7789_mpy
```

O copia las librerías `.py` directamente al dispositivo.

### 3. Copiar archivos al dispositivo
```bash
# Con mpremote (pip install mpremote)
mpremote cp main.py              :main.py
mpremote cp audio_sampler.py     :audio_sampler.py
mpremote cp sound_classifier.py  :sound_classifier.py
mpremote cp visual_response.py   :visual_response.py
```

### 4. Configurar modo de micrófono
En `main.py`, cambia:
```python
SAMPLER_MODE = 'adc'   # micrófono analógico
# o
SAMPLER_MODE = 'i2s'   # micrófono digital (recomendado)
```

### 5. Ejecutar
```bash
mpremote run main.py
# o simplemente reinicia el Pico — main.py arranca automáticamente
```

---

## Cómo funciona el clasificador

```
Audio crudo → Ventana Hann → FFT 256 puntos → Magnitud dB por bin
     ↓
Para cada perfil de sonido:
  - ¿Hay suficiente energía en el rango de frecuencia? (min_db)
  - ¿Varía la frecuencia dominante? (para sonidos con sweep=True)
  - ¿Ha pasado el tiempo de cooldown? (evita repeticiones)
     ↓
Candidatos ordenados por prioridad → Ganador → Respuesta visual
```

### Resolución frecuencial
- Tasa de muestreo: 8000 Hz
- Tamaño FFT: 256 muestras
- Resolución: **31.25 Hz por bin**
- Frecuencia máxima útil: 4000 Hz (Nyquist)

---

## Ajuste de sensibilidad

En `sound_classifier.py`, modifica `THRESHOLD_DB` y `min_db` por perfil:
```python
THRESHOLD_DB = 40   # Subir si hay muchas falsas alarmas por ruido ambiente
                    # Bajar si el micrófono está muy lejos de la fuente

# Por perfil:
"min_db": 55        # Más alto = menos sensible (requiere sonido más fuerte)
                    # Más bajo = más sensible (puede captar ruidos similares)
```

---

## Expansiones futuras

- [ ] Modo BLE: enviar notificaciones al teléfono
- [ ] Perfil de usuario: calibración del umbral por entorno
- [ ] ML lite: reemplazar reglas con modelo TensorFlow Lite Micro
- [ ] Vibración háptica: motor de vibración como canal adicional
- [ ] App companion: configurar mapeos desde el teléfono vía BLE

---

## Licencia

- GPLv3 (GNU General Public License v3): Para tu código en MicroPython. Obliga a cualquiera que modifique o use tu código en su propio proyecto a publicar también su código bajo la misma licencia. Nadie puede llevarse tu código y cerrarlo.
- CERN-OHL-S (Strongly Reciprocal): Para el diseño del hardware (esquemas, diseño de PCB, archivos STL de la carcasa). Es el equivalente a la GPL pero para hardware creado en el CERN. Obliga a compartir los diseños físicos si los modifican.
