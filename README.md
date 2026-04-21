# 🎵 Asistente Auditivo para Raspberry Pi Pico

Un dispositivo wearable inteligente que **detecta sonidos en tiempo real** y proporciona **retroalimentación visual instantánea** mediante una pantalla LCD, LEDs animados y controles por botones.

## ✨ Características Principales

### 🎨 Pantalla LCD 1.14" (240x135 píxeles)
- ⏱️ **Tiempo transcurrido** en formato MM:SS
- 🔔 **Información en tiempo real** del sonido detectado
- 📝 **Historial** de los 5 últimos sonidos detectados
- 🎯 **Navegación intuitiva** con botones izquierda/derecha
- 📊 **Nivel de dB** del sonido actual

### ⚡ LEDs NeoPixel con Animaciones
- 🔴 **Destello alternado** - Emergencias (Prioridad máxima)
- 💡 **Flash rápido** - Eventos urgentes (Prioridad alta)
- 〜 **Onda de luz** - Notificaciones normales (Prioridad media)
- 🔆 **Pulsación suave** - Información (Prioridad baja)

### 🎮 Control Total con Botones
- **Centro (GP3)**: Detiene inmediatamente la alarma
- **Izquierda (GP4)**: Navega hacia sonidos anteriores
- **Derecha (GP6)**: Navega hacia sonidos posteriores
- **Arriba/Abajo (GP2/GP5)**: Reservados para futuro

### 🎤 Detección de 7 Tipos de Sonidos
1. 🚨 **Sirena de Emergencia** - Ambulancia, policía, bomberos
2. 🔥 **Alarma de Humo** - Detectores de incendio
3. 🚗 **Bocina de Auto** - Vehículos en la calle
4. 🚪 **Timbre de Puerta** - Entrada
5. 👶 **Llanto de Bebé** - Infantes llorando
6. ☎️ **Teléfono** - Llamadas entrantes
7. 🐕 **Perro Ladrando** - Ladridos

## 🆕 Mejoras Realizadas (v2.0)

| Característica | Antes | Ahora |
|---|---|---|
| **Pantalla LCD** | ❌ Solo luz | ✅ Información clara |
| **Tiempo visible** | ❌ No | ✅ MM:SS en tiempo real |
| **Control de alarma** | ❌ No | ✅ Botón Centro |
| **Historial** | ❌ No existe | ✅ Últimos 5 sonidos |
| **Navegación** | ❌ No | ✅ Botones Izq/Der |
| **Nivel dB** | ❌ No mostrado | ✅ Visible en pantalla |
| **Anti-rebote** | ❌ No | ✅ Integrado |
| **Diagnóstico** | ❌ No | ✅ test_hardware.py |

## 🛠️ Hardware Requerido

### Componentes Principales
- **Raspberry Pi Pico** (RP2040) con MicroPython
- **Pantalla LCD ST7735 1.14"** (240x135 píxeles) - Pico-LCD-1.14-V2
- **Tira NeoPixel WS2812B** (5 LEDs mínimo)
- **Micrófono** (analógico MAX4466/KY-037 o digital INMP441)
- **Botones táctiles** (5 unidades)
- **Capacitor 100µF** (para NeoPixel)
- **Protoboard y cables de conexión**

### Diagrama de Conexiones

```
╔════════════════════════════════════════════════════════╗
║          RASPBERRY PI PICO (RP2040)                    ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  PANTALLA LCD (SPI1):        NEOPIXEL:                 ║
║  GP10 → SCK                  GP15 → DIN                ║
║  GP11 → MOSI                 GND → GND                 ║
║  GP8  → DC                   5V → VCC (+100µF cap)     ║
║  GP9  → CS                                             ║
║  GP12 → RST                  MICRÓFONO (ADC):          ║
║  GP13 → BL                   GP26 → Salida             ║
║                              3V3 → VCC                 ║
║  BOTONES (todos a GND):                                ║
║  GP2 (Arriba)                                          ║
║  GP3 (Centro) ← DETENER ALARMA                        ║
║  GP4 (Izquierda) ← NAVEGAR                            ║
║  GP5 (Abajo)                                           ║
║  GP6 (Derecha) ← NAVEGAR                              ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

## 📦 Instalación

### 1. Instalar MicroPython en Pico
```bash
# Descarga desde: https://micropython.org/download/rp2-pico/
# Mantén presionado BOOTSEL y conecta al PC
# Copia el archivo .uf2 a la unidad RPI-RP2
```

### 2. Copiar Archivos al Pico
Usa **Thonny IDE** (recomendado):

1. Descarga Thonny desde https://thonny.org/
2. Conecta tu Pico a USB
3. En Thonny: Herramientas → Opciones → MicroPython (RP2)
4. Copia estos 5 archivos al Pico:
   - `main.py` ⭐ (punto de entrada)
   - `audio_sampler.py`
   - `sound_classifier.py`
   - `visual_response.py`
   - `Pico_LCD_1inch14_V2.py` (driver LCD)

### 3. Ejecutar

**Opción A - Desde Thonny (Recomendado):**
```python
# Abre main.py en Thonny
# Presiona F5 (Run)
```

**Opción B - Auto-inicio al encender:**
```bash
# Renombra main.py a boot.py en el Pico
# Se ejecutará automáticamente al encender
```

## ▶️ Uso del Dispositivo

### Flujo Normal de Operación

1. **Inicio**: Pantalla muestra "Inicializando...", LEDs apagados
2. **Escucha**: Pantalla muestra tiempo transcurrido + "En espera..."
3. **Detección**: 
   - Pantalla: ">> DETECTADO <<" + nombre del sonido + dB
   - LEDs: Animación según prioridad
   - Historial: Se agrega automáticamente
4. **Control**:
   - Presiona **Centro** para detener alarma
   - Presiona **Izquierda/Derecha** para navegar historial

### Información Mostrada en Pantalla

```
╔─────────────────────────────────╗
│ 00:15                           │  ← Tiempo transcurrido
│                                 │
│ >> DETECTADO <<                 │  ← Notificación
│ SIRENA_EMERGENCIA               │  ← Sonido actual
│ DB: 65.2                        │  ← Nivel de dB
├─────────────────────────────────┤
│ ULTIMOS SONIDOS:                │  ← Historial
│ >>> SIRENA_EMERGENCIA           │  ← Más reciente (amarillo)
│     TIMBRE_PUERTA               │
│     LLANTO_BEBE                 │
│     ALARMA_HUMO                 │
│     BOCINA_AUTO                 │  ← Más antiguo
└─────────────────────────────────┘
```

## 🐛 Pruebas y Solución de Problemas

### Script de Diagnóstico
```python
# En Thonny, ejecuta:
exec(open('test_hardware.py').read())
```

Esto probará:
- ✅ Pantalla LCD (mostrar colores)
- ✅ LEDs NeoPixel (animar LEDs)
- ✅ Botones (detectar presiones)
- ✅ Micrófono ADC (medir audio)

### Problemas Comunes

#### La pantalla solo muestra luz de fondo (nada visible)
```python
# Verificar conexión LCD y brillo:
from machine import Pin, PWM
pwm = PWM(Pin(13))
pwm.freq(1000)
pwm.duty_u16(32768)  # 50% brillo
```

#### LEDs no se encienden
```python
# Verificar NeoPixel:
import neopixel
from machine import Pin
np = neopixel.NeoPixel(Pin(15), 5)
for i in range(5):
    np[i] = (255, 0, 0)  # Rojo
np.write()
```

#### Micrófono no detecta sonidos
- Verifica que está en GP26
- Sube el volumen alrededor del dispositivo
- En `sound_classifier.py`, baja `THRESHOLD_DB = 40` (aumenta sensibilidad)

#### Botones no funcionan
- Verifica pines: GP2, GP3, GP4, GP5, GP6
- Todos deben conectarse a GND
- Verifica cables sin conexión suelta

## ⚙️ Configuración Personalizada

### Cambiar Sensibilidad del Micrófono
En `sound_classifier.py`:
```python
THRESHOLD_DB = 40    # Aumentar = menos sensible
```

### Ajustar Brillo de LEDs
En `visual_response.py`:
```python
LED_BRIGHT = 0.4     # 0.0-1.0 (reduce consumo)
```

### Cambiar Modo de Micrófono (ADC → I2S)
En `main.py`:
```python
SAMPLER_MODE = 'i2s'  # Cambia de 'adc'
```

Luego configura pines I2S en `audio_sampler.py`:
```python
sck = Pin(10)   # BCLK
ws  = Pin(11)   # LRCLK
sd  = Pin(12)   # SD
```

## 📁 Estructura del Proyecto

```
Asistente-Auditivo-Raspberry-Pi/
├── code/
│   ├── main.py                      ← PUNTO DE ENTRADA ⭐
│   ├── audio_sampler.py             ← Captura de audio
│   ├── sound_classifier.py          ← Clasificación FFT
│   ├── visual_response.py           ← Pantalla + LEDs + Botones
│   ├── Pico-LCD-1.14-V2.py         ← Driver LCD original
│   ├── Pico_LCD_1inch14_V2.py      ← Driver LCD (importable)
│   └── test_hardware.py             ← Script de diagnóstico
├── PicoLCD-Python/
│   └── Pico-LCD-1.14-V2/           ← Referencia de drivers
├── README.md                        ← Este archivo
├── QUICK_START.md                   ← Inicio rápido
├── GUIA_ACTUALIZADA.md             ← Documentación completa
├── CAMBIOS_REALIZADOS.md           ← Historial de cambios
└── LICENSE
```

## 🚀 Inicio Rápido (5 minutos)

```bash
# 1. Verificar hardware
exec(open('test_hardware.py').read())

# 2. Ejecutar programa
python main.py

# 3. Hacer ruido para probar
# → Verás detección en pantalla
# → LEDs animarán
# → Presiona Centro para detener
```

## 📊 Especificaciones Técnicas

- **Tasa de muestreo**: 8000 Hz
- **Tamaño FFT**: 256 muestras (~32 ms de audio)
- **Resolución**: 31.25 Hz/bin
- **Latencia**: 50-100 ms desde detección a visualización
- **Consumo**: ~200 mA en funcionamiento
- **Historial**: 5 últimos sonidos
- **Actualización pantalla**: 100 ms
- **Ciclo principal**: 10 ms

## 🔧 Desarrollo

### Agregar un Nuevo Sonido
En `sound_classifier.py`, agrega a `SOUND_PROFILES`:

```python
{
    "label": "tu_nuevo_sonido",
    "category": "home",
    "priority": 2,
    "bins_range": (hz_to_bin(500), hz_to_bin(1500)),
    "min_db": 50,
    "sweep": False,
    "color_key": "white",
}
```

### Cambiar Animación de LEDs
En `visual_response.py`, modifica `_anim_flash()`, `_anim_wave()`, etc.

### Personalizar Colores
En `visual_response.py`, edita:
```python
COLORS_RGB = {
    "red": (255, 0, 0),
    # Agrega tus colores...
}
```

## 📚 Referencias

- [MicroPython Documentación](https://docs.micropython.org/)
- [Raspberry Pi Pico](https://www.raspberrypi.com/products/raspberry-pi-pico/)
- [Pico-LCD-1.14](https://www.waveshare.com/pico-lcd-1.14.htm)
- [NeoPixel Guide](https://learn.adafruit.com/adafruit-neopixel-uberguide)
- [FFT en MicroPython](https://en.wikipedia.org/wiki/Cooley%E2%80%93Tukey_FFT_algorithm)

## 💡 Consejos de Uso

1. **Comienza con diagnóstico**: Ejecuta `test_hardware.py` primero
2. **Usa DEBUG**: En `main.py`, pon `DEBUG = True` para ver detecciones
3. **Calibra micrófono**: Prueba diferentes niveles de `THRESHOLD_DB`
4. **Protege el dispositivo**: Considera una caja 3D impresa
5. **Experimenta**: Personaliza sonidos según tus necesidades
6. **Optimiza energía**: Reduce `LED_BRIGHT` si usas batería

## 📝 Cambios Recientes (v2.0)

✅ Driver LCD corregido - pantalla ahora funciona perfectamente
✅ Tiempo transcurrido visible en MM:SS
✅ Botón Centro para detener alarma
✅ Historial de 5 últimos sonidos
✅ Navegación izquierda/derecha
✅ Script de diagnóstico completo
✅ Documentación mejorada
✅ Anti-rebote integrado en botones
✅ Mejor manejo de excepciones
✅ Mensajes de inicialización claros

## 📄 Licencia

Este proyecto está disponible bajo licencia MIT.

## 🙋 Soporte

Si encuentras problemas:

1. Ejecuta `test_hardware.py` para diagnosticar
2. Verifica las conexiones físicas
3. Revisa la consola de Thonny para mensajes de error
4. Aumenta `LOOP_INTERVAL_MS` si hay lag
5. Consulta `GUIA_ACTUALIZADA.md` para más detalles

## 🎉 ¡Disfruta tu Asistente Auditivo!

Este dispositivo te ayudará a detectar sonidos importantes en tu entorno con retroalimentación visual clara y controles intuitivos.

---

**Documentación completa disponible en:**
- 📖 [GUIA_ACTUALIZADA.md](GUIA_ACTUALIZADA.md)
- ⚡ [QUICK_START.md](QUICK_START.md)
- 📋 [CAMBIOS_REALIZADOS.md](CAMBIOS_REALIZADOS.md)

**Última actualización**: 2024
**Versión**: 2.0 (Mejorada)