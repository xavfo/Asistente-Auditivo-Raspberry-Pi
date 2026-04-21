"""
boot.py
Archivo de boot mejorado para Asistente Auditivo.
Se ejecuta automáticamente al encender el Pico.

Características:
  - Logging de reinicioses y errores
  - Detección de problemas de energía
  - Modo seguro si hay fallas repetidas
  - Recuperación automática
  - Información detallada de diagnóstico
"""

import gc
import os

import utime
from machine import ADC, Pin

# Intentar importar logger
try:
    from error_logger import ErrorLogger

    HAS_LOGGER = True
except ImportError:
    HAS_LOGGER = False


class BootSequence:
    """Maneja la secuencia de boot segura del Pico."""

    def __init__(self):
        self.logger = None
        if HAS_LOGGER:
            self.logger = ErrorLogger()
        self.boot_attempts = self._read_boot_attempts()
        self.max_boot_attempts = 3

    def _print(self, message):
        """Imprime mensaje y lo registra."""
        print(message)
        if self.logger:
            self.logger.info(message)

    def _print_error(self, message):
        """Imprime error y lo registra."""
        print(f"[ERROR] {message}")
        if self.logger:
            self.logger.error(message)

    def _read_boot_attempts(self):
        """Lee el número de intentos de boot."""
        try:
            if "boot_attempts.txt" in os.listdir():
                with open("boot_attempts.txt", "r") as f:
                    attempts = int(f.read().strip())
                    return attempts
        except:
            pass
        return 0

    def _write_boot_attempts(self, attempts):
        """Escribe el número de intentos de boot."""
        try:
            with open("boot_attempts.txt", "w") as f:
                f.write(str(attempts))
        except:
            pass

    def _reset_boot_attempts(self):
        """Resetea contador de intentos."""
        try:
            if "boot_attempts.txt" in os.listdir():
                os.remove("boot_attempts.txt")
        except:
            pass

    def check_power(self):
        """Verifica si hay voltaje suficiente."""
        self._print("[BOOT] Verificando energía...")

        try:
            # Leer voltaje de VSYS (GP29 conectado a VSYS/3)
            adc_vsys = ADC(3)
            vsys_raw = adc_vsys.read_u16()
            vsys_voltage = (vsys_raw / 65535.0) * 3.3 * 3

            self._print(f"[BOOT] Voltaje VSYS: {vsys_voltage:.2f}V")

            if vsys_voltage < 2.8:
                self._print_error("Voltaje muy bajo - revisar conexión o batería")
                return False
            elif vsys_voltage < 3.5:
                self._print("[BOOT] ⚠️  Voltaje bajo - batería débil")
                return True
            else:
                self._print("[BOOT] ✓ Voltaje OK")
                return True

        except Exception as e:
            self._print(f"[BOOT] No se pudo leer voltaje: {e}")
            return True

    def check_memory(self):
        """Verifica memoria disponible."""
        self._print("[BOOT] Verificando memoria...")

        gc.collect()
        mem_free = gc.mem_free()
        mem_alloc = gc.mem_alloc()

        self._print(
            f"[BOOT] Memoria - Libre: {mem_free} bytes | Asignada: {mem_alloc} bytes"
        )

        if mem_free < 10000:
            self._print_error(f"Memoria crítica: {mem_free} bytes")
            return False
        elif mem_free < 20000:
            self._print("[BOOT] ⚠️  Memoria baja")
            return True
        else:
            self._print("[BOOT] ✓ Memoria OK")
            return True

    def check_gpio_basic(self):
        """Verifica pins GPIO básicos."""
        self._print("[BOOT] Verificando pines GPIO...")

        critical_pins = {
            "LCD_BL": 13,
            "NeoPixel": 15,
            "ADC_Mic": 26,
            "Btn_Center": 3,
        }

        problems = []
        for name, pin_num in critical_pins.items():
            try:
                pin = Pin(pin_num, Pin.OUT)
                pin(0)
                self._print(f"[BOOT] ✓ GP{pin_num} ({name})")
            except Exception as e:
                self._print_error(f"GP{pin_num} ({name}): {e}")
                problems.append(name)

        if problems:
            return False
        else:
            self._print("[BOOT] ✓ GPIO OK")
            return True

    def check_lcd(self):
        """Verifica LCD."""
        self._print("[BOOT] Verificando LCD...")

        try:
            from Pico_LCD_1inch14_V2 import LCD_1inch14

            lcd = LCD_1inch14()
            self._print("[BOOT] ✓ LCD inicializado")

            # Mostrar mensaje en pantalla
            lcd.fill(0x0000)
            lcd.text("BOOT", 100, 60, 0xFFFF)
            lcd.show()

            return True

        except ImportError:
            self._print_error("No se puede importar driver LCD")
            return False
        except Exception as e:
            self._print_error(f"Error LCD: {e}")
            return False

    def run_diagnostics(self):
        """Ejecuta diagnósticos básicos."""
        print("\n" + "=" * 60)
        print("DIAGNÓSTICOS DE BOOT")
        print("=" * 60 + "\n")

        results = {
            "Energía": self.check_power(),
            "Memoria": self.check_memory(),
            "GPIO": self.check_gpio_basic(),
            "LCD": self.check_lcd(),
        }

        print("\n" + "=" * 60)
        print("RESUMEN")
        print("=" * 60)
        for name, result in results.items():
            status = "✓ OK" if result else "✗ ERROR"
            print(f"{name:15s}: {status}")
        print("=" * 60 + "\n")

        return all(results.values())

    def safe_mode(self):
        """Modo seguro de diagnóstico."""
        print("\n" + "=" * 60)
        print("MODO SEGURO ACTIVADO")
        print("=" * 60)
        print("\nDispositivo en modo de diagnóstico.")
        print("Ejecuta test_hardware.py para verificar componentes.\n")

        if HAS_LOGGER:
            self.logger.print_statistics()
            self.logger.print_memory_log()
            print("\nÚltimos logs guardados en error_log.txt\n")

        print("Esperando diagnóstico manual...")
        print("Presiona Ctrl+C para salir o reinicia el Pico.\n")

        # Mantener el dispositivo en modo seguro
        try:
            while True:
                utime.sleep(1)
        except KeyboardInterrupt:
            print("\nSaliendo del modo seguro...\n")

    def boot_main(self):
        """Intenta ejecutar main.py."""
        self._print("[BOOT] Iniciando aplicación principal...")

        self.boot_attempts += 1
        self._write_boot_attempts(self.boot_attempts)

        if self.boot_attempts > self.max_boot_attempts:
            self._print_error(f"Demasiados intentos de boot ({self.boot_attempts})")
            self._print("[BOOT] Activando modo seguro...")
            self.safe_mode()
            return False

        try:
            # Limpiar memoria antes de ejecutar main
            gc.collect()

            # Importar y ejecutar main
            import main

            self._print("[BOOT] ¡Aplicación iniciada exitosamente!")
            self._reset_boot_attempts()
            return True

        except ImportError as e:
            self._print_error(f"No se puede importar main.py: {e}")
            self.safe_mode()
            return False

        except Exception as e:
            self._print_error(f"Error ejecutando main: {e}")

            if HAS_LOGGER:
                self.logger.exception("Error en main", e)

            if self.boot_attempts >= self.max_boot_attempts:
                self._print("[BOOT] Máximo de intentos alcanzado - modo seguro")
                self.safe_mode()
            else:
                self._print(f"[BOOT] Reintentando... (intento {self.boot_attempts})")
                utime.sleep(2)
                return self.boot_main()

            return False

    def run(self):
        """Ejecuta la secuencia completa de boot."""
        print("\n" + "=" * 60)
        print("ASISTENTE AUDITIVO - SECUENCIA DE BOOT")
        print("=" * 60 + "\n")

        # Ejecutar diagnósticos
        diag_ok = self.run_diagnostics()

        if not diag_ok:
            self._print("\n[BOOT] ⚠️  Problemas detectados en diagnósticos")
            self._print("[BOOT] Verificando energía y memoria...")

            if not self.check_power():
                self._print_error("Problema de energía - revisar batería")
                self.safe_mode()
                return

            if not self.check_memory():
                self._print_error("Problema de memoria")
                self.safe_mode()
                return

        # Intentar iniciar aplicación
        self.boot_main()


# ──────────────────────────────────────────────
#  PUNTO DE ENTRADA
# ──────────────────────────────────────────────

if __name__ == "__main__":
    boot = BootSequence()
    boot.run()
