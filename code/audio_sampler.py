"""
audio_sampler.py
Captura de audio desde micrófono para Raspberry Pi Zero con MicroPython.

Soporta dos modos:
  - ADC analógico (micrófono MAX4466 / KY-037 en pin GP26/ADC0)
  - I2S digital    (micrófono INMP441 / SPH0645 — recomendado para mejor calidad)

Selecciona el modo según tu hardware en AudioSampler.__init__()
"""

import array
import utime

# ──────────────────────────────────────────────
#  MODO ADC ANALÓGICO
#  Compatible con: MAX4466, KY-037, cualquier mic con salida analógica.
#  Pin: GP26 = ADC0 en Raspberry Pi Pico / RP2040
# ──────────────────────────────────────────────

try:
    from machine import ADC, Pin
    _HAS_ADC = True
except ImportError:
    _HAS_ADC = False

# ──────────────────────────────────────────────
#  MODO I2S DIGITAL
#  Compatible con: INMP441, SPH0645LM4H
#  Requiere MicroPython con módulo I2S (disponible en rp2 port)
# ──────────────────────────────────────────────

try:
    from machine import I2S
    _HAS_I2S = True
except ImportError:
    _HAS_I2S = False


FFT_SIZE    = 256
SAMPLE_RATE = 8000   # Hz


class AudioSampler:
    """
    Captura FFT_SIZE muestras de audio normalizadas a [-1.0, 1.0].

    Parámetros
    ----------
    mode : 'adc' | 'i2s'
        'adc' — micrófono analógico (más sencillo, menor calidad)
        'i2s' — micrófono digital   (recomendado, 24-bit, menos ruido)
    """

    def __init__(self, mode='adc'):
        self.mode = mode
        self._sample_interval_us = int(1_000_000 / SAMPLE_RATE)

        if mode == 'adc':
            self._init_adc()
        elif mode == 'i2s':
            self._init_i2s()
        else:
            raise ValueError("mode debe ser 'adc' o 'i2s'")

    # ── ADC ──────────────────────────────────

    def _init_adc(self):
        if not _HAS_ADC:
            raise RuntimeError("Módulo ADC no disponible en esta plataforma")
        # GP26 = ADC0. Cambia a ADC(1) o ADC(2) según tu conexión.
        self._adc = ADC(Pin(26))
        # El ADC del RP2040 devuelve valores 0–65535
        self._adc_midpoint = 32768
        self._adc_scale    = 32768.0

    def _read_adc_frame(self):
        """Lee FFT_SIZE muestras a la tasa SAMPLE_RATE usando busy-wait."""
        samples = []
        t0 = utime.ticks_us()
        for i in range(FFT_SIZE):
            raw = self._adc.read_u16()
            normalized = (raw - self._adc_midpoint) / self._adc_scale
            samples.append(normalized)
            # Esperar hasta el siguiente instante de muestreo
            target = utime.ticks_add(t0, i * self._sample_interval_us)
            while utime.ticks_diff(target, utime.ticks_us()) > 0:
                pass
        return samples

    # ── I2S ──────────────────────────────────

    def _init_i2s(self):
        """
        Configuración para INMP441 (I2S estándar, 16-bit, mono).
        Pines por defecto para Raspberry Pi Pico / RP2040:
          SCK (BCLK) = GP10
          WS  (LRCLK)= GP11
          SD  (DATA) = GP12
        Ajusta según tu cableado.
        """
        if not _HAS_I2S:
            raise RuntimeError("Módulo I2S no disponible. Usa MicroPython rp2 port >= 1.20")

        BITS     = 16
        BUF_LEN  = FFT_SIZE * 2  # 2 bytes por muestra de 16 bits

        self._i2s = I2S(
            0,                        # I2S ID: 0 o 1
            sck  = Pin(10),           # BCLK
            ws   = Pin(11),           # LRCLK
            sd   = Pin(12),           # SD (datos)
            mode = I2S.RX,
            bits = BITS,
            format     = I2S.MONO,
            rate       = SAMPLE_RATE,
            ibuf       = BUF_LEN * 4,
        )
        self._i2s_buf = bytearray(BUF_LEN)
        self._i2s_scale = 32768.0  # 2^15 para 16-bit signed

    def _read_i2s_frame(self):
        """Lee FFT_SIZE muestras desde el bus I2S."""
        num_read = self._i2s.readinto(self._i2s_buf)
        # Interpretar bytes como int16 signed (little-endian)
        samples = []
        for i in range(0, num_read - 1, 2):
            raw = self._i2s_buf[i] | (self._i2s_buf[i + 1] << 8)
            if raw >= 32768:
                raw -= 65536   # convertir a signed
            samples.append(raw / self._i2s_scale)
        # Rellenar con ceros si el buffer quedó corto
        while len(samples) < FFT_SIZE:
            samples.append(0.0)
        return samples[:FFT_SIZE]

    # ── API pública ───────────────────────────

    def read_frame(self):
        """
        Retorna una lista de FFT_SIZE floats normalizados [-1.0, 1.0].
        Llama a este método en el loop principal.
        """
        if self.mode == 'adc':
            return self._read_adc_frame()
        else:
            return self._read_i2s_frame()

    def deinit(self):
        """Libera recursos de hardware."""
        if self.mode == 'i2s' and _HAS_I2S:
            self._i2s.deinit()