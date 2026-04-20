"""
main.py
Punto de entrada principal del dispositivo wearable de asistencia auditiva.
Se ejecuta automáticamente al arrancar la Raspberry Pi Zero / Pico con MicroPython.

Flujo:
  1. Captura frame de audio (FFT_SIZE muestras)
  2. Clasifica el sonido con FFT + reglas
  3. Si hay detección → dispara respuesta visual (LEDs + pantalla)
  4. Actualiza animación en cada iteración (no bloqueante)
  5. Repite indefinidamente

Ajusta SAMPLER_MODE según tu micrófono:
  'adc' → micrófono analógico (MAX4466, KY-037) — más simple, menor calidad
  'i2s' → micrófono digital   (INMP441)          — recomendado
"""

import utime
import gc

from audio_sampler    import AudioSampler
from sound_classifier import SoundClassifier
from visual_response  import VisualResponse

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────

SAMPLER_MODE = 'adc'    # 'adc' | 'i2s'  ← cambia según tu hardware
DEBUG        = True     # Imprime detecciones por UART (desactiva en producción)


# ──────────────────────────────────────────────
#  LOOP PRINCIPAL
# ──────────────────────────────────────────────

def main():
    print("=== Wearable Auditivo — Iniciando ===")

    sampler    = AudioSampler(mode=SAMPLER_MODE)
    classifier = SoundClassifier()
    visual     = VisualResponse()

    print(f"Modo micrófono : {SAMPLER_MODE.upper()}")
    print(f"FFT_SIZE       : {256} muestras")
    print(f"Sample rate    : {8000} Hz")
    print("Escuchando...\n")

    frame_count = 0

    while True:
        try:
            # 1. Captura de audio
            samples = sampler.read_frame()

            # 2. Clasificación
            result = classifier.classify(samples)

            # 3. Respuesta visual si hay detección
            if result is not None:
                if DEBUG:
                    print(f">> SONIDO: {result['label']:20s} "
                          f"| {result['category']:5s} "
                          f"| prioridad {result['priority']} "
                          f"| {result['peak_db']} dB")
                visual.trigger(result)

            # 4. Actualizar animación (no bloqueante)
            visual.update()

            # 5. Gestión de memoria cada 100 frames
            frame_count += 1
            if frame_count % 100 == 0:
                gc.collect()
                frame_count = 0

        except KeyboardInterrupt:
            print("\nDetenido por el usuario.")
            visual.clear()
            sampler.deinit()
            break

        except Exception as e:
            # En dispositivo embebido, loguear y continuar en lugar de crashear
            print(f"[ERROR] {e}")
            utime.sleep_ms(200)


# ──────────────────────────────────────────────
#  ARRANQUE
# ──────────────────────────────────────────────

if __name__ == "__main__":
    main()
