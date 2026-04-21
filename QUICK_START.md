# ⚡ INICIO RÁPIDO - Asistente Auditivo Pico

## 1️⃣ Verificar Hardware (2 minutos)

Asegúrate de tener estos componentes conectados:
- ✓ Pantalla LCD 1.14" (Pico-LCD-1.14-V2)
- ✓ 5 LEDs NeoPixel en GP15
- ✓ Micrófono en GP26 (ADC)
- ✓ 5 Botones en GP2, GP3, GP4, GP5, GP6

**Conexión rápida:**
```
Pantalla (LCD):        Micrófono:         Botones:
GP10 → SCK             GP26 → salida      GND ← todos
GP11 → MOSI            3.3V → VCC         GP2, 3, 4, 5, 6 → pulsadores
GP8  → DC
GP9  → CS
GP12 → RST
GP13 → BL

LEDs:
GP15 → DIN
```

## 2️⃣ Instalar Archivos (1 minuto)

Copia estos 5 archivos a tu Raspberry Pi Pico usando Thonny:

1. `main.py` ⭐ (punto de entrada)
2. `audio_sampler.py`
3. `sound_classifier.py`
4. `visual_response.py`
5. `Pico_LCD_1inch14_V2.py` (driver LCD)

## 3️⃣ Probar Hardware (2 minutos)

Ejecuta el script de diagnóstico:

```python
# En Thonny: F5 (ejecutar)
exec(open('test_hardware.py').read())
```

Debe mostrar:
- ✅ Colores en pantalla
- ✅ Animación de LEDs
- ✅ Detección de botones
- ✅ Lectura del micrófono

## 4️⃣ Ejecutar Programa (Inmediato)

```python
# En Thonny: F5
python main.py
```

Verás:
```
==================================================
  ASISTENTE AUDITIVO — INICIANDO
==================================================
✓ Componentes inicializados
¡LISTO! Escuchando sonidos...
```

## 5️⃣ Usar el Dispositivo

### Durante la detección:
- **Pantalla**: Muestra el sonido detectado + tiempo
- **LEDs**: Animan con colores
- **Botones**: 
  - Centro (GP3) = Detener alarma
  - Izquierda (GP4) = Historial atrás
  - Derecha (GP6) = Historial adelante

### Prueba:
1. Haz un ruido fuerte (silbido, aplauso, etc.)
2. La pantalla debe mostrar el sonido detectado
3. Los LEDs deben animar
4. Presiona Centro para detener
5. Usa Izq/Der para navegar historial

## 🎯 7 Sonidos que Detecta

1. 🚨 **Sirena** (ambulancia/policía) - Rojo brillante
2. 🔥 **Alarma de humo** - Naranja
3. 🚗 **Bocina de auto** - Amarillo
4. 🚪 **Timbre** - Azul
5. 👶 **Llanto de bebé** - Púrpura
6. ☎️ **Teléfono** - Verde
7. 🐕 **Perro ladrando** - Rosa

## ⚙️ Si algo no funciona

### Pantalla solo muestra luz:
```python
# En Thonny (Terminal):
from machine import Pin, PWM
pwm = PWM(Pin(13))
pwm.duty_u16(32768)  # Ajusta brillo
```

### LEDs no se encienden:
```python
# Verifica que GP15 está libre en visual_response.py
LED_PIN = 15  # ← este debe ser tu pin
```

### Micrófono no capta:
- ¿Micrófono conectado a GP26?
- ¿Tiene voltaje (3.3V o 5V)?
- Sube el volumen alrededor del dispositivo

### Botones no funcionan:
- Verifica pines: GP2, GP3, GP4, GP5, GP6
- Todos a GND cuando se presionan
- Sin cable suelto

## 📊 Estructura de Pantalla

```
00:25                     ← Tiempo transcurrido
>> DETECTADO <<           ← Notificación
SIRENA_EMERGENCIA         ← Sonido detectado
DB: 65.3                  ← Nivel de sonido
─────────────────────────
ULTIMOS SONIDOS:          ← Historial
>>> SIRENA               ← Seleccionado (amarillo)
    TIMBRE
    LLANTO
    ALARMA_HUMO
    BOCINA
```

## 🚀 Comandos Útiles (Terminal Thonny)

```python
# Ver mensajes de depuración
DEBUG = True  # En main.py

# Ejecutar programa
python main.py

# Probar hardware
exec(open('test_hardware.py').read())

# Detener (Ctrl+C en terminal)

# Ver errores en consola (F8 en Thonny)
```

## ✅ Checklist de Inicio

- [ ] Hardware conectado
- [ ] Archivos copiados al Pico
- [ ] test_hardware.py ejecutado sin errores
- [ ] main.py ejecutado
- [ ] Sonido detectado en pantalla
- [ ] LEDs animando
- [ ] Botón Centro detiene alarma
- [ ] Historial funciona

## 💡 Consejos Rápidos

1. **Comienza en silencio**: Usa test_hardware.py primero
2. **Controla brillo**: Si los LEDs son muy brillantes, baja LED_BRIGHT
3. **Ajusta sensibilidad**: THRESHOLD_DB en sound_classifier.py
4. **Calibra micrófono**: Prueba con DEBUG = True
5. **Anti-rebote**: Los botones ya tienen integrado

## 📞 Problemas Comunes

| Problema | Solución |
|----------|----------|
| Pantalla en blanco | Verifica conexión LCD (SPI1) |
| LEDs no se encienden | Verifica GP15 y alimentación |
| Sin detecciones | Aumenta volumen + baja THRESHOLD_DB |
| Botones flojos | Verifica conexión a GND |
| Pantalla lenta | Normal, actualiza cada 100ms |

## 🎉 ¡Listo!

Tu Asistente Auditivo está funcional. Ahora:
- Prueba con diferentes sonidos
- Personaliza en sound_classifier.py si quieres
- Experimenta con los controles
- ¡Disfruta! 🎵

---

**Documentación completa**: Ver `GUIA_ACTUALIZADA.md`
**Cambios realizados**: Ver `CAMBIOS_REALIZADOS.md`
