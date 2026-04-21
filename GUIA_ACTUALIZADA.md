# GUÍA ACTUALIZADA - Asistente Auditivo Raspberry Pi Pico

## 📋 Resumen de cambios

Este proyecto ha sido actualizado con las siguientes mejoras:

✅ **Pantalla LCD 1.14"**: Ahora funciona correctamente con el driver `Pico-LCD-1.14-V2.py`
✅ **Tiempo transcurrido**: Se muestra en tiempo real durante la alarma (MM:SS)
✅ **Control de alarma**: Botón central (GP3) para detener la alarma
✅ **Historial de sonidos**: Navega por los 5 últimos sonidos detectados con botones izquierda/derecha
✅ **Información visual**: Muestra claramente estado actual, detecciones y historial

---

## 🛠️ Hardware requerido

### Componentes principales:
- **Raspberry Pi Pico** (RP2040)
- **Pantalla LCD 1.14"** (ST7735, 240x135 pixels) - Pico-LCD-1.14 V2
- **Micrófono digital** INMP441 o analógico MAX4466/KY-037
- **Tira NeoPixel** WS2812B (5-8 LEDs, recomendado 5)
- **Botones** (5x): arriba, abajo, izquierda, derecha, centro
- **Cables de conexión** y **protoboard**

### Conexiones de hardware:

#### Pantalla LCD (Pico-LCD-1.14-V2):
```
GP13  → BL (Backlight)
GP12  → RST (Reset)
GP11  → MOSI (SPI Data)
GP10  → SCK (SPI Clock)
GP9   → CS (Chip Select)
GP8   → DC (Data/Command)
GND   → GND
3V3   → VCC
```

#### LEDs NeoPixel (WS2812B):
```
GP15  → DIN (Data In)
GND   → GND
5V    → VCC (con capacitor 100µF en paralelo)
```

#### Botones (Pull-up interno):
```
GP2   → Botón Arriba
GP3   → Botón Centro (DETENER ALARMA) ⭐
GP4   → Botón Izquierda (NAVEGAR HISTORIAL ←)
GP5   → Botón Abajo
GP6   → Botón Derecha (NAVEGAR HISTORIAL →)
GND   → Otro lado de cada botón
```

#### Micrófono (modo ADC - analógico):
```
GP26  → Salida analógica del micrófono (MAX4466/KY-037)
GND   → GND
3V3   → VCC (para micrófono)
```

**Alternativa I2S (micrófono digital INMP441):**
```
GP10  → SCK (BCLK)
GP11  → WS (LRCLK)
GP12  → SD (Data)
GND   → GND
3V3   → VCC
```

---

## 📦 Instalación

### 1. Preparar la Raspberry Pi Pico

1. Descarga **MicroPython** para Raspberry Pi Pico desde:
   https://micropython.org/download/rp2-pico/

2. Conecta tu Pico a la computadora mientras mantienes presionado el botón BOOTSEL

3. Copia el archivo `.uf2` descargado a la unidad que aparece (RPI-RP2)

4. El Pico se reiniciará con MicroPython instalado

### 2. Cargar archivos al Pico

Usa **Thonny IDE** (recomendado) o **ampy**:

**Con Thonny:**
1. Descarga Thonny desde https://thonny.org/
2. Conecta tu Pico
3. En Thonny: Herramientas → Opciones → Intérprete → MicroPython (Raspberry Pi Pico)
4. En la ventana de Archivos, copia estos archivos al Pico:
   - `main.py` (⭐ punto de entrada)
   - `audio_sampler.py`
   - `sound_classifier.py`
   - `visual_response.py`
   - `Pico_LCD_1inch14_V2.py` (copia del driver LCD)

**Con ampy (línea de comandos):**
```bash
ampy --port COM3 put main.py
ampy --port COM3 put audio_sampler.py
ampy --port COM3 put sound_classifier.py
ampy --port COM3 put visual_response.py
ampy --port COM3 put Pico_LCD_1inch14_V2.py
```

---

## ▶️ Ejecución

### Opción 1: Ejecutar directamente desde Thonny
1. Abre `main.py` en Thonny
2. Presiona F5 o el botón Play
3. Verás mensajes de inicialización en la consola

### Opción 2: Auto-ejecutar al encender
1. Renombra `main.py` a `boot.py`
2. El Pico ejecutará automáticamente el código al encender

### Opción 3: Línea de comandos (Thonny)
```python
import main
```

---

## 🎮 Controles del dispositivo

| Botón | Función | Pin |
|-------|---------|-----|
| **Centro** | Detener alarma activa | GP3 |
| **Izquierda** | Navegar historial ← | GP4 |
| **Derecha** | Navegar historial → | GP6 |
| **Arriba** | Reservado para futuro | GP2 |
| **Abajo** | Reservado para futuro | GP5 |

### Flujo de uso:

1. **Inicio**: Dispositivo en modo escucha
   - Pantalla: mostrará "En espera..." + Tiempo transcurrido
   - LEDs: apagados

2. **Detección de sonido**: Al detectar un sonido registrado
   - Pantalla: mostrará nombre del sonido + nivel dB
   - LEDs: animación según prioridad del sonido
   - Historial: se agrega automáticamente

3. **Durante alarma**: 
   - Presiona **Botón Centro** para detener
   - LEDs se apagarán
   - Pantalla mostrará "HISTORIAL" con navegación

4. **Navegación del historial**:
   - Presiona **Botón Izquierda** para sonido anterior
   - Presiona **Botón Derecha** para sonido siguiente
   - El sonido seleccionado se marca en amarillo

---

## 📊 Información en pantalla

### Pantalla en modo "Escucha":
```
┌─────────────────────────────────┐
│ 00:45 (Tiempo transcurrido)     │
│                                 │
│ >> DETECTADO <<                 │
│ SIRENA (Nombre del sonido)      │
│ DB: 65.2                        │
│ ─────────────────────────────── │
│ ULTIMOS SONIDOS:                │
│ >>> SIRENA (más reciente)       │
│     TIMBRE                      │
│     LLANTO_BEBE                 │
│     ALARMA_HUMO                 │
│     BOCINA_AUTO                 │
└─────────────────────────────────┘
```

### Pantalla en modo "Historial":
- Selecciona con botones izquierda/derecha
- Presiona Centro para volver a escucha

---

## 🔊 Sonidos detectables

El sistema puede detectar 7 tipos de sonidos:

1. **SIRENA** (Ambulancia/Policía) - Prioridad 🔴 MÁXIMA
   - Rango: 500-1500 Hz
   - LEDs: Parpadeo rojo alternado muy rápido

2. **ALARMA HUMO** - Prioridad 🔴 MÁXIMA
   - Rango: 2800-3500 Hz
   - LEDs: Parpadeo naranja alternado

3. **BOCINA AUTO** - Prioridad 🟠 ALTA
   - Rango: 350-900 Hz
   - LEDs: Destello rojo
   
4. **TIMBRE PUERTA** - Prioridad 🟡 MEDIA
   - Rango: 700-1300 Hz
   - LEDs: Onda de luz azul

5. **LLANTO BEBE** - Prioridad 🟠 ALTA
   - Rango: 250-700 Hz
   - LEDs: Destello púrpura

6. **TELÉFONO** - Prioridad 🟡 MEDIA
   - Rango: 900-2100 Hz
   - LEDs: Onda de luz verde

7. **PERRO LADRANDO** - Prioridad 🟢 BAJA
   - Rango: 150-850 Hz
   - LEDs: Onda de luz rosa

---

## 🐛 Pruebas y solución de problemas

### Script de prueba de hardware:

Ejecuta `test_hardware.py` para verificar todos los componentes:

```python
# En Thonny, ejecuta:
exec(open('test_hardware.py').read())
```

Este script probará:
- ✅ Pantalla LCD (muestra colores)
- ✅ LEDs NeoPixel (anima LEDs)
- ✅ Botones (espera presiones)
- ✅ Micrófono (mide nivel de audio)

### Problemas comunes:

#### La pantalla solo muestra luz de fondo (nada visible)
**Causa**: Conexión incorrecta o pin de backlight (BL) no está encendido
**Solución**:
```python
# En la terminal Thonny, verifica:
from machine import Pin, PWM
pwm = PWM(Pin(13))
pwm.freq(1000)
pwm.duty_u16(32768)  # 50% de brillo
```

#### LEDs no se encienden
**Causa**: Pin incorrecto o biblioteca neopixel no disponible
**Solución**:
```python
# Verifica el pin en visual_response.py (línea ~15):
LED_PIN = 15  # Debe coincidir con tu conexión
```

#### El micrófono no capta audio
**Causa**: Pin ADC incorrecto o muy bajo gain del micrófono
**Solución**:
- Verifica que el micrófono está en GP26 (ADC0)
- Comprueba que MAX4466 tiene ajuste de sensibilidad (potenciómetro)
- Aumenta el threshold en `sound_classifier.py` si hay mucho ruido

#### Los botones no funcionan
**Causa**: Pines incorrectos o conexión débil
**Solución**:
```python
# Verifica pines en visual_response.py:
BTN_CENTER = 3   # GP3
BTN_LEFT = 4     # GP4
BTN_RIGHT = 6    # GP6
```

---

## 📝 Configuración personalizada

### Cambiar modo de micrófono (ADC vs I2S):

En `main.py`, línea ~33:
```python
SAMPLER_MODE = 'adc'  # Cambia a 'i2s' si usas INMP441
```

### Ajustar sensibilidad:

En `sound_classifier.py`, línea ~19:
```python
THRESHOLD_DB = 40  # Sube a 50 si hay mucho ruido falso
```

### Modificar número de LEDs:

En `visual_response.py`, línea ~48:
```python
NUM_LEDS = 5  # Cambia según tu tira
```

### Agregar más sonidos:

Edita `sound_classifier.py` y agrega a `SOUND_PROFILES`:
```python
{
    "label": "tu_sonido",
    "category": "home",
    "priority": 2,
    "bins_range": (hz_to_bin(500), hz_to_bin(1500)),
    "min_db": 50,
    "sweep": False,
    "color_key": "white",
}
```

---

## 🔧 Estructura del proyecto

```
Asistente-Auditivo-Raspberry-Pi/
├── code/
│   ├── main.py                      ← PUNTO DE ENTRADA
│   ├── audio_sampler.py             ← Captura de audio
│   ├── sound_classifier.py          ← Clasificación FFT
│   ├── visual_response.py           ← Pantalla + LEDs + Botones
│   ├── Pico-LCD-1.14-V2.py         ← Driver LCD original
│   ├── Pico_LCD_1inch14_V2.py      ← Copia para importación
│   └── test_hardware.py             ← Script de diagnóstico
├── PicoLCD-Python/
│   └── Pico-LCD-1.14-V2/           ← Bibliotecas de referencia
└── README.md
```

---

## 📚 Referencias útiles

- **MicroPython Docs**: https://docs.micropython.org/
- **Raspberry Pi Pico**: https://www.raspberrypi.com/products/raspberry-pi-pico/
- **NeoPixel Guide**: https://learn.adafruit.com/adafruit-neopixel-uberguide
- **FFT en MicroPython**: https://en.wikipedia.org/wiki/Cooley%E2%80%93Tukey_FFT_algorithm

---

## 💡 Consejos finales

1. **Comienza con el script de prueba**: `test_hardware.py` te dirá qué funciona
2. **Usa DEBUG = True** en `main.py` para ver detecciones en consola
3. **Calibra el micrófono**: Ajusta el threshold según tu entorno
4. **Protege tu dispositivo**: Usa una caja 3D impresa
5. **Prueba sonidos reales**: Descarga archivos de audio de los sonidos a detectar
6. **Personaliza prioridades**: Ajusta las alertas según tus necesidades

---

## 📞 Soporte

Si encuentras problemas:

1. Revisa la consola (Thonny) para mensajes de error
2. Ejecuta `test_hardware.py` para diagnosticar
3. Verifica las conexiones físicas con un multímetro
4. Aumenta `LOOP_INTERVAL_MS` en `main.py` si hay lag
5. Redondea los números en `sound_classifier.py` si hay errores de memoria

¡Diviértete con tu Asistente Auditivo! 🎵🔊