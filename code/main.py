"""
main.py
Punto de entrada principal del dispositivo wearable de asistencia auditiva.
Se ejecuta automáticamente al arrancar la Raspberry Pi Pico con MicroPython.

Flujo:
  1. Captura frame de audio (FFT_SIZE muestras)
  2. Clasifica el sonido con FFT + reglas
  3. Si hay detección → dispara respuesta visual (LEDs + pantalla)
  4. Actualiza animación en cada iteración (no bloqueante)
  5. Maneja botones para parar alarma y navegar historial
  6. Repite indefinidamente

Requisitos:
  - audio_sampler.py: captura de audio
  - sound_classifier.py: clasificación de sonidos
  - visual_response.py: respuesta visual con pantalla LCD y LEDs
  - Pico_LCD_1inch14_V2.py: driver de pantalla LCD
"""

import gc
import sys

import utime
from audio_sampler import AudioSampler
from sound_classifier import SoundClassifier
from visual_response import VisualResponse

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────

SAMPLER_MODE = "adc"  # 'adc' | 'i2s'  ← cambia según tu hardware
DEBUG = True  # Imprime detecciones por UART
LOOP_INTERVAL_MS = 10  # Tiempo mínimo entre iteraciones (no bloquea)

# ──────────────────────────────────────────────
#  LOOP PRINCIPAL
# ──────────────────────────────────────────────


def main():
    print("=" * 50)
    print("  ASISTENTE AUDITIVO — INICIANDO")
    print("=" * 50)

    # Inicializar componentes
    try:
        print("\n[1/3] Inicializando captura de audio...")
        sampler = AudioSampler(mode=SAMPLER_MODE)
        print(
            f"      Modo: {SAMPLER_MODE.upper()} | FFT_SIZE: 256 | Sample rate: 8000 Hz"
        )

        print("[2/3] Inicializando clasificador de sonidos...")
        classifier = SoundClassifier()
        print("      7 tipos de sonidos configurados")

        print("[3/3] Inicializando respuesta visual...")
        visual = VisualResponse()
        print("      LEDs + Pantalla LCD + Botones")

    except Exception as e:
        print(f"\n[ERROR] Error en inicialización: {e}")
        print("Verifica las conexiones de hardware y los drivers")
        return

    print("\n" + "=" * 50)
    print("  ¡LISTO! Escuchando sonidos...")
    print("=" * 50)
    print("\nBotones:")
    print("  - Botón Centro (GP3): Detener alarma")
    print("  - Botón Izquierda (GP4): Navegar historial ←")
    print("  - Botón Derecha (GP6): Navegar historial →")
    print("\nPresiona Ctrl+C para detener\n")

    frame_count = 0
    last_loop_time = utime.ticks_ms()

    try:
        while True:
            loop_start = utime.ticks_ms()

            # ──────────────────────────────────────
            #  1. CAPTURA DE AUDIO
            # ──────────────────────────────────────
            try:
                samples = sampler.read_frame()
            except Exception as e:
                if DEBUG:
                    print(f"[ERROR] Error en captura de audio: {e}")
                utime.sleep_ms(LOOP_INTERVAL_MS)
                continue

            # ──────────────────────────────────────
            #  2. CLASIFICACIÓN DE SONIDO
            # ──────────────────────────────────────
            try:
                result = classifier.classify(samples)

                # Si se detectó un sonido, disparar respuesta visual
                if result is not None:
                    if DEBUG:
                        print(
                            f">> SONIDO DETECTADO: {result['label']:20s} "
                            f"| Prioridad: {result['priority']} "
                            f"| {result['peak_db']} dB"
                        )
                    visual.trigger(result)

            except Exception as e:
                if DEBUG:
                    print(f"[ERROR] Error en clasificación: {e}")
                utime.sleep_ms(LOOP_INTERVAL_MS)
                continue

            # ──────────────────────────────────────
            #  3. ACTUALIZAR ANIMACIÓN E INTERFAZ
            # ──────────────────────────────────────
            try:
                visual.update()
            except Exception as e:
                if DEBUG:
                    print(f"[ERROR] Error al actualizar visual: {e}")

            # ──────────────────────────────────────
            #  4. GESTIÓN DE MEMORIA
            # ──────────────────────────────────────
            frame_count += 1
            if frame_count % 100 == 0:
                gc.collect()
                frame_count = 0

            # ──────────────────────────────────────
            #  5. CONTROL DE VELOCIDAD DEL LOOP
            # ──────────────────────────────────────
            loop_elapsed = utime.ticks_diff(utime.ticks_ms(), loop_start)
            if loop_elapsed < LOOP_INTERVAL_MS:
                utime.sleep_ms(LOOP_INTERVAL_MS - loop_elapsed)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 50)
        print("  DETENIDO POR EL USUARIO")
        print("=" * 50)
        visual.clear()
        sampler.deinit()

    except Exception as e:
        print(f"\n[ERROR CRÍTICO] {e}")
        print("El programa se ha detenido")
        visual.clear()
        sampler.deinit()


# ──────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()
