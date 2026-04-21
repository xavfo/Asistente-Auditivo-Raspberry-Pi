"""
test_hardware.py
Script de diagnóstico avanzado para detectar problemas de reinicio y hardware.

Detecta:
  - Problemas de energía (USB vs Batería)
  - Reinicios inesperados
  - Memory leaks
  - Conflictos de pines
  - Problemas de componentes
  - Voltajes incorrectos
"""

import gc
import os

import utime
from machine import ADC, SPI, Pin

# ──────────────────────────────────────────────
#  FUNCIONES DE DIAGNÓSTICO
# ──────────────────────────────────────────────


def print_header(title):
    """Imprime encabezado de sección."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(name, ok, details=""):
    """Imprime resultado de una prueba."""
    status = "✅ OK" if ok else "❌ ERROR"
    print(f"  {name:40s} {status:10s} {details}")


def check_voltages():
    """Verifica voltajes del sistema."""
    print_header("1. VERIFICACIÓN DE VOLTAJES")

    try:
        # Voltaje VSYS
        adc_vsys = ADC(3)
        vsys_raw = adc_vsys.read_u16()
        vsys_voltage = (vsys_raw / 65535.0) * 3.3 * 3

        print(f"\n  Voltaje VSYS (entrada): {vsys_voltage:.2f}V")

        ok_vsys = vsys_voltage >= 3.0

        if vsys_voltage < 2.5:
            print("    ⚠️  CRÍTICO: Voltaje muy bajo - sin energía")
            print(f"    SOLUCIÓN: Conecta USB o carga la batería")
            return False
        elif vsys_voltage < 3.2:
            print("    ⚠️  ADVERTENCIA: Voltaje bajo")
            print(f"    SOLUCIÓN: Usa USB en lugar de batería o carga batería")
        else:
            print("    ✓ Voltaje correcto")

        # Voltaje 3.3V
        adc_3v3 = ADC(2)
        v3v3_raw = adc_3v3.read_u16()
        v3v3 = (v3v3_raw / 65535.0) * 3.3

        print(f"  Voltaje 3.3V (regulador): {v3v3:.2f}V")

        if v3v3 < 3.0 or v3v3 > 3.6:
            print("    ⚠️  ADVERTENCIA: Voltaje 3.3V fuera de rango")
            print(f"    ESPERADO: 3.0-3.6V")
            print(f"    ACTUAL: {v3v3:.2f}V")

        return ok_vsys

    except Exception as e:
        print(f"  ❌ Error leyendo voltajes: {e}")
        return False


def check_memory_state():
    """Verifica estado de memoria."""
    print_header("2. VERIFICACIÓN DE MEMORIA")

    gc.collect()
    mem_free = gc.mem_free()
    mem_alloc = gc.mem_alloc()
    total_mem = mem_free + mem_alloc

    print(f"\n  Memoria libre:      {mem_free:8d} bytes")
    print(f"  Memoria asignada:   {mem_alloc:8d} bytes")
    print(f"  Memoria total:      {total_mem:8d} bytes")
    print(f"  Porcentaje libre:   {(mem_free / total_mem * 100):.1f}%")

    if mem_free < 10000:
        print("\n  ❌ CRÍTICO: Memoria muy baja")
        print("     El dispositivo se reiniciará por falta de memoria")
        return False
    elif mem_free < 20000:
        print("\n  ⚠️  ADVERTENCIA: Memoria baja")
        print("     Posible reinicio durante operación")
        return True
    else:
        print("\n  ✓ Memoria OK")
        return True


def check_gpio_conflicts():
    """Verifica conflictos de pines GPIO."""
    print_header("3. VERIFICACIÓN DE CONFLICTOS GPIO")

    pins_required = {
        "LCD_BL": 13,
        "LCD_RST": 12,
        "LCD_MOSI": 11,
        "LCD_SCK": 10,
        "LCD_CS": 9,
        "LCD_DC": 8,
        "NeoPixel": 15,
        "ADC_Mic": 26,
        "Btn_Up": 2,
        "Btn_Center": 3,
        "Btn_Left": 4,
        "Btn_Down": 5,
        "Btn_Right": 6,
    }

    print("\n  Verificando pines requeridos:\n")

    problems = []
    for name, pin_num in pins_required.items():
        try:
            # Intentar usar el pin
            pin = Pin(pin_num, Pin.OUT)
            pin(0)
            pin(1)
            pin(0)
            print(f"    GP{pin_num:2d} ({name:15s}) ✓")
        except Exception as e:
            print(f"    GP{pin_num:2d} ({name:15s}) ❌ {e}")
            problems.append(name)

    if problems:
        print(f"\n  ❌ Problemas encontrados: {', '.join(problems)}")
        return False
    else:
        print("\n  ✓ Todos los pines OK")
        return True


def check_spi_interface():
    """Verifica interfaz SPI."""
    print_header("4. VERIFICACIÓN DE SPI (para LCD)")

    try:
        print("\n  Inicializando SPI1...")
        spi = SPI(
            1,
            10000_000,
            polarity=0,
            phase=0,
            sck=Pin(10),
            mosi=Pin(11),
            miso=None,
        )
        print("    ✓ SPI1 inicializado correctamente")

        print("\n  Intentando comunicación SPI...")
        try:
            # Intentar escritura de prueba
            test_data = bytearray([0xAA, 0x55, 0xAA, 0x55])
            spi.write(test_data)
            print("    ✓ Escritura SPI exitosa")
        except Exception as e:
            print(f"    ⚠️  Escritura SPI: {e}")

        return True

    except Exception as e:
        print(f"  ❌ Error SPI: {e}")
        return False


def check_lcd_hardware():
    """Verifica pantalla LCD."""
    print_header("5. VERIFICACIÓN DE PANTALLA LCD")

    try:
        print("\n  Importando driver LCD...")
        from Pico_LCD_1inch14_V2 import LCD_1inch14

        print("    ✓ Driver importado")

        print("  Inicializando pantalla...")
        lcd = LCD_1inch14()
        print("    ✓ Pantalla inicializada")

        print("  Escribiendo en pantalla...")
        lcd.fill(0x0000)
        lcd.text("TEST", 50, 50, 0xFFFF)
        lcd.show()
        print("    ✓ Pantalla funcionando")

        utime.sleep_ms(500)

        # Mostrar colores
        colors = [
            (0xF800, "ROJO"),
            (0x07E0, "VERDE"),
            (0x001F, "AZUL"),
        ]

        for color, name in colors:
            lcd.fill(color)
            lcd.text(name, 80, 60, 0xFFFF)
            lcd.show()
            utime.sleep_ms(200)

        lcd.fill(0x0000)
        lcd.show()

        print("\n  ✓ Pantalla LCD OK")
        return True

    except ImportError as e:
        print(f"  ❌ No se puede importar driver: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error LCD: {e}")
        return False


def check_neopixel():
    """Verifica LEDs NeoPixel."""
    print_header("6. VERIFICACIÓN DE LEDS NEOPIXEL")

    try:
        print("\n  Importando librería NeoPixel...")
        import neopixel

        print("    ✓ Librería importada")

        print("  Inicializando NeoPixel...")
        np = neopixel.NeoPixel(Pin(15), 5)
        print("    ✓ NeoPixel inicializado")

        print("  Probando colores...")

        colors = [
            ((255, 0, 0), "ROJO"),
            ((0, 255, 0), "VERDE"),
            ((0, 0, 255), "AZUL"),
            ((255, 255, 0), "AMARILLO"),
            ((0, 0, 0), "APAGADO"),
        ]

        for color, name in colors:
            for i in range(5):
                np[i] = color
            np.write()
            print(f"    {name}... ", end="")
            utime.sleep_ms(200)
            print("✓")

        print("\n  ✓ LEDs NeoPixel OK")
        return True

    except ImportError:
        print("  ⚠️  Librería NeoPixel no disponible")
        return False
    except Exception as e:
        print(f"  ❌ Error NeoPixel: {e}")
        return False


def check_buttons():
    """Verifica botones."""
    print_header("7. VERIFICACIÓN DE BOTONES")

    buttons = {
        "Up": 2,
        "Center": 3,
        "Left": 4,
        "Down": 5,
        "Right": 6,
    }

    print("\n  Esperando presiones de botones (10 segundos)...\n")

    detected = {name: False for name in buttons.items()}
    start_time = utime.ticks_ms()

    while utime.ticks_diff(utime.ticks_ms(), start_time) < 10000:
        for name, pin_num in buttons.items():
            btn = Pin(pin_num, Pin.IN, Pin.PULL_UP)
            if btn.value() == 0:
                if not detected[(name, pin_num)]:
                    detected[(name, pin_num)] = True
                    print(f"    ✓ Botón {name:8s} (GP{pin_num}) detectado")
                utime.sleep_ms(200)

    ok = any(detected.values())

    if ok:
        print("\n  ✓ Botones detectados correctamente")
    else:
        print("\n  ⚠️  Ningún botón presionado - verifica conexiones")

    return ok


def check_microphone():
    """Verifica micrófono."""
    print_header("8. VERIFICACIÓN DE MICRÓFONO (ADC)")

    try:
        print("\n  Leyendo entrada ADC (50 muestras)...")

        adc = ADC(Pin(26))

        samples = []
        for i in range(50):
            samples.append(adc.read_u16())
            utime.sleep_ms(10)

        min_val = min(samples)
        max_val = max(samples)
        avg_val = sum(samples) // len(samples)
        rango = max_val - min_val

        print(f"  Valor mínimo:  {min_val:5d}")
        print(f"  Valor máximo:  {max_val:5d}")
        print(f"  Valor promedio: {avg_val:5d}")
        print(f"  Rango:         {rango:5d}")

        if rango < 1000:
            print("\n  ⚠️  Rango muy pequeño - posible micrófono desconectado")
            return False
        else:
            print("\n  ✓ Micrófono funcionando")
            return True

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_restart_detection():
    """Verifica detección de reinicios."""
    print_header("9. DETECCIÓN DE REINICIOS")

    try:
        # Leer contador de reinicios
        if "restart_count.txt" in os.listdir():
            with open("restart_count.txt", "r") as f:
                restart_count = int(f.read().strip())
        else:
            restart_count = 0

        print(f"\n  Reinicios detectados: {restart_count}")

        # Incrementar contador
        with open("restart_count.txt", "w") as f:
            f.write(str(restart_count + 1))

        if restart_count > 5:
            print("  ⚠️  ADVERTENCIA: Muchos reinicios detectados")
            print("      Posible problema de energía o memoria")
            return False
        else:
            print("  ✓ Contador de reinicio funcionando")
            return True

    except Exception as e:
        print(f"  ⚠️  Error en contador de reinicios: {e}")
        return True


def check_stack_usage():
    """Verifica uso de stack."""
    print_header("10. VERIFICACIÓN DE STACK")

    try:
        import micropython

        print("\n  Información de memoria:")

        # Mostrar estadísticas
        micropython.mem_info()

        print("\n  ✓ Stack verificado")
        return True

    except Exception as e:
        print(f"  ⚠️  No se puede verificar stack: {e}")
        return True


def run_stress_test():
    """Ejecuta prueba de estrés."""
    print_header("11. PRUEBA DE ESTRÉS (30 segundos)")

    print("\n  Esta prueba simula carga del sistema...")
    print("  Monitorea reinicioses, memoria y componentes.\n")

    start_time = utime.ticks_ms()
    iterations = 0
    errors = 0

    try:
        import neopixel

        np = neopixel.NeoPixel(Pin(15), 5)

        while utime.ticks_diff(utime.ticks_ms(), start_time) < 30000:
            # Incrementar contador
            iterations += 1

            # Probar memoria
            gc.collect()
            mem_free = gc.mem_free()

            if mem_free < 15000:
                print(f"  ⚠️  Iteración {iterations}: Memoria baja ({mem_free})")
                errors += 1

            # Probar LEDs
            try:
                color = ((iterations % 256), ((iterations * 2) % 256), 0)
                for i in range(5):
                    np[i] = color
                np.write()
            except Exception as e:
                print(f"  ⚠️  Error LED: {e}")
                errors += 1

            # Probar ADC
            try:
                adc = ADC(Pin(26))
                val = adc.read_u16()
            except Exception as e:
                print(f"  ⚠️  Error ADC: {e}")
                errors += 1

            utime.sleep_ms(100)

        print(f"\n  Iteraciones completadas: {iterations}")
        print(f"  Errores encontrados: {errors}")

        if errors == 0:
            print("\n  ✓ Prueba de estrés exitosa")
            return True
        else:
            print(f"\n  ⚠️  {errors} errores durante prueba")
            return False

    except Exception as e:
        print(f"  ❌ Error en prueba de estrés: {e}")
        return False


def print_recommendations():
    """Imprime recomendaciones basadas en resultados."""
    print_header("RECOMENDACIONES")

    print("""
Si el dispositivo solo funciona una vez y luego se reinicia:

1. PROBLEMA DE ENERGÍA (más común):
   - Si usas USB: prueba otro cable USB
   - Si usas batería: carga la batería completamente
   - El Pico necesita al menos 3.2V para funcionar
   - La pantalla LCD consume mucha energía

2. PROBLEMA DE MEMORIA:
   - Los LEDs y pantalla consumen mucha RAM
   - Reduce número de LEDs: NUM_LEDS = 3 en visual_response.py
   - Desactiva DEBUG en main.py

3. PROBLEMA DE COMPONENTES:
   - Verifica soldaduras en conectores
   - Verifica que no hay conexiones sueltas
   - Prueba sin la pantalla LCD primero
   - Prueba solo con micrófono y LEDs

4. PROBLEMA DE BOOT:
   - El archivo boot.py debe existir
   - Si hay error en boot.py, crea uno simple
   - Los reinicios continuos indican error en boot.py

5. SOLUCIÓN RÁPIDA:
   - Usa USB (mejor que batería)
   - Conecta solo LCD, LEDs y micrófono
   - Reduce sensibilidad: THRESHOLD_DB = 60
   - Monitorea logs: check logger.txt después de reinicio
    """)


# ──────────────────────────────────────────────
#  MAIN
# ──────────────────────────────────────────────


def main():
    print("\n" + "=" * 70)
    print("  DIAGNÓSTICO AVANZADO - Asistente Auditivo")
    print("=" * 70)

    results = {
        "Voltajes": check_voltages(),
        "Memoria": check_memory_state(),
        "GPIO": check_gpio_conflicts(),
        "SPI": check_spi_interface(),
        "LCD": check_lcd_hardware(),
        "NeoPixel": check_neopixel(),
        "Botones": check_buttons(),
        "Micrófono": check_microphone(),
        "Reinicio": check_restart_detection(),
        "Stack": check_stack_usage(),
    }

    # Prueba de estrés (opcional)
    print("\n\n¿Ejecutar prueba de estrés de 30 segundos? (presiona cualquier botón)")
    print("Esperando 5 segundos...")

    stress_test = False
    start = utime.ticks_ms()
    while utime.ticks_diff(utime.ticks_ms(), start) < 5000:
        for pin_num in [2, 3, 4, 5, 6]:
            btn = Pin(pin_num, Pin.IN, Pin.PULL_UP)
            if btn.value() == 0:
                stress_test = True
                break
        if stress_test:
            break

    if stress_test:
        results["Estrés"] = run_stress_test()

    # Resumen
    print_header("RESUMEN GENERAL")

    print("\n")
    for test, result in results.items():
        status = "✅ OK" if result else "❌ PROBLEMA"
        print(f"  {test:20s}: {status}")

    all_ok = all(results.values())
    print("\n")

    if all_ok:
        print("  ✅ ¡TODOS LOS COMPONENTES OK!")
        print("     El dispositivo está listo para usar.\n")
    else:
        print("  ⚠️  SE ENCONTRARON PROBLEMAS")
        print_recommendations()

    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
