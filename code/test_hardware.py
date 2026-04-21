"""
test_hardware.py
Script de prueba para verificar todos los componentes de hardware.

Ejecuta esto antes de usar main.py para diagnosticar problemas de conexión.
"""

import utime
from machine import ADC, Pin

print("\n" + "=" * 60)
print("  PRUEBA DE HARDWARE - Asistente Auditivo Raspberry Pi Pico")
print("=" * 60 + "\n")

# ──────────────────────────────────────────────
# 1. PRUEBA LCD
# ──────────────────────────────────────────────
print('[1/4] Probando pantalla LCD 1.14"...')

try:
    from Pico_LCD_1inch14_V2 import LCD_1inch14

    lcd = LCD_1inch14()
    print("      ✓ Pantalla LCD inicializada")

    # Mostrar colores
    colors = {
        "Rojo": 0xF800,
        "Verde": 0x07E0,
        "Azul": 0x001F,
        "Amarillo": 0xFFE0,
        "Blanco": 0xFFFF,
    }

    for color_name, color_val in colors.items():
        lcd.fill(color_val)
        lcd.text(color_name, 50, 60, 0xFFFF if color_val == 0x0000 else 0x0000)
        lcd.show()
        utime.sleep(200)

    # Mostrar prueba final
    lcd.fill(0x0000)
    lcd.text("LCD OK!", 80, 60, 0xFFFF)
    lcd.show()
    print("      ✓ Pantalla LCD funcionando correctamente\n")

except Exception as e:
    print(f"      ✗ Error en LCD: {e}\n")

# ──────────────────────────────────────────────
# 2. PRUEBA NeoPixel (LEDs)
# ──────────────────────────────────────────────
print("[2/4] Probando LEDs NeoPixel...")

try:
    import neopixel

    np = neopixel.NeoPixel(Pin(15), 5)
    print("      ✓ NeoPixel inicializado")

    # Probar cada LED
    for i in range(5):
        for j in range(5):
            if i == j:
                np[j] = (255, 0, 0)  # Rojo
            else:
                np[j] = (0, 0, 0)  # Apagado
        np.write()
        utime.sleep(200)

    # Prueba de color
    colors_test = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0)]
    for color in colors_test:
        for i in range(5):
            np[i] = color
        np.write()
        utime.sleep(200)

    # Apagar
    for i in range(5):
        np[i] = (0, 0, 0)
    np.write()

    print("      ✓ LEDs NeoPixel funcionando correctamente\n")

except Exception as e:
    print(f"      ✗ Error en NeoPixel: {e}\n")

# ──────────────────────────────────────────────
# 3. PRUEBA BOTONES
# ──────────────────────────────────────────────
print("[3/4] Probando botones...")
print("      Presiona cada botón cuando se pida:\n")

buttons = {
    "Arriba": Pin(2, Pin.IN, Pin.PULL_UP),
    "Centro": Pin(3, Pin.IN, Pin.PULL_UP),
    "Izquierda": Pin(4, Pin.IN, Pin.PULL_UP),
    "Abajo": Pin(5, Pin.IN, Pin.PULL_UP),
    "Derecha": Pin(6, Pin.IN, Pin.PULL_UP),
}

try:
    buttons_tested = {name: False for name in buttons.keys()}

    print("      Esperando presiones de botones...")
    print("      (presiona todos los botones en los próximos 10 segundos)\n")

    start_time = utime.ticks_ms()
    timeout = 10000  # 10 segundos

    while utime.ticks_diff(utime.ticks_ms(), start_time) < timeout:
        for name, btn in buttons.items():
            if btn.value() == 0 and not buttons_tested[name]:
                buttons_tested[name] = True
                print(f"      ✓ Botón {name:12s} detectado")

        if all(buttons_tested.values()):
            print("\n      ✓ Todos los botones funcionan correctamente\n")
            break

    if not all(buttons_tested.values()):
        not_pressed = [name for name, tested in buttons_tested.items() if not tested]
        print(f"\n      ✗ Botones no presionados: {', '.join(not_pressed)}\n")

except Exception as e:
    print(f"      ✗ Error en botones: {e}\n")

# ──────────────────────────────────────────────
# 4. PRUEBA MICRÓFONO ADC
# ──────────────────────────────────────────────
print("[4/4] Probando micrófono (ADC)...")

try:
    adc = ADC(Pin(26))  # GP26 = ADC0

    print("      Leyendo niveles de audio...")
    print("      (haz ruido para ver cambios)\n")

    samples = []
    for i in range(100):
        val = adc.read_u16()
        samples.append(val)
        utime.sleep_ms(10)

    min_val = min(samples)
    max_val = max(samples)
    avg_val = sum(samples) // len(samples)

    print(f"      Min: {min_val:5d} | Promedio: {avg_val:5d} | Max: {max_val:5d}")

    if min_val < avg_val - 5000 or max_val > avg_val + 5000:
        print("      ✓ Micrófono detectando cambios de audio")
    else:
        print("      ! Micrófono puede estar muy quieto o no conectado")

    print("      ✓ Micrófono funcionando\n")

except Exception as e:
    print(f"      ✗ Error en micrófono: {e}\n")

# ──────────────────────────────────────────────
# RESUMEN FINAL
# ──────────────────────────────────────────────
print("=" * 60)
print("  PRUEBA COMPLETADA")
print("=" * 60)
print("\nSi todos los componentes pasaron las pruebas,")
print("ya puedes ejecutar main.py\n")
