"""
sound_classifier.py
Clasificador de sonidos por FFT para dispositivo wearable de asistencia auditiva.
Hardware: Raspberry Pi Zero + MicroPython
Autor: Generado para proyecto wearable auditivo
"""

import array
import math
import utime

# ──────────────────────────────────────────────
#  CONFIGURACIÓN GLOBAL
# ──────────────────────────────────────────────

SAMPLE_RATE = 8000        # Hz — suficiente para voz y alarmas (máx ~4kHz útil)
FFT_SIZE    = 256          # Potencia de 2. Resolución: SAMPLE_RATE / FFT_SIZE = 31.25 Hz/bin
THRESHOLD_DB = 40          # dB mínimos para considerar que hay sonido real (evita ruido)
COOLDOWN_MS  = 1500        # ms entre detecciones del mismo sonido (evita repeticiones)


# ──────────────────────────────────────────────
#  PERFILES DE SONIDO
#  Cada perfil define:
#    bins_range  : (bin_min, bin_max) rango dominante de frecuencia
#    min_db      : energía mínima en ese rango para activar
#    pulse_pattern: característica temporal (para futuros refinamientos)
#    label       : nombre del evento
#    category    : 'home' | 'urban'
#    priority    : 1 (máxima urgencia) – 5 (informativa)
# ──────────────────────────────────────────────

def hz_to_bin(hz):
    """Convierte frecuencia Hz a índice de bin FFT."""
    return int(hz * FFT_SIZE / SAMPLE_RATE)


SOUND_PROFILES = [
    {
        "label":    "sirena_emergencia",
        "category": "urban",
        "priority": 1,
        # Sirenas ambulancia/policía: barrido 500–1500 Hz
        "bins_range": (hz_to_bin(500), hz_to_bin(1500)),
        "min_db":   52,
        "sweep":    True,   # esperar variación de frecuencia dominante
        "color_key": "red",
    },
    {
        "label":    "alarma_humo",
        "category": "home",
        "priority": 1,
        # Detectores de humo: tono puro ~3000–3400 Hz
        "bins_range": (hz_to_bin(2800), hz_to_bin(3500)),
        "min_db":   55,
        "sweep":    False,
        "color_key": "orange",
    },
    {
        "label":    "bocina_auto",
        "category": "urban",
        "priority": 2,
        # Bocinas: 400–800 Hz, energía alta y sostenida
        "bins_range": (hz_to_bin(350), hz_to_bin(900)),
        "min_db":   58,
        "sweep":    False,
        "color_key": "yellow",
    },
    {
        "label":    "timbre_puerta",
        "category": "home",
        "priority": 3,
        # Timbres domésticos: 800–1200 Hz, patrón corto
        "bins_range": (hz_to_bin(700), hz_to_bin(1300)),
        "min_db":   45,
        "sweep":    False,
        "color_key": "blue",
    },
    {
        "label":    "llanto_bebe",
        "category": "home",
        "priority": 2,
        # Llanto: fundamental 300–600 Hz + armónicos, duración sostenida
        "bins_range": (hz_to_bin(250), hz_to_bin(700)),
        "min_db":   42,
        "sweep":    True,   # varía en frecuencia como el llanto real
        "color_key": "purple",
    },
    {
        "label":    "telefono",
        "category": "home",
        "priority": 3,
        # Ringtone digital: 1000–2000 Hz
        "bins_range": (hz_to_bin(900), hz_to_bin(2100)),
        "min_db":   44,
        "sweep":    False,
        "color_key": "green",
    },
    {
        "label":    "perro_ladrando",
        "category": "urban",
        "priority": 4,
        # Ladrido: 200–800 Hz, ráfagas cortas repetidas
        "bins_range": (hz_to_bin(150), hz_to_bin(850)),
        "min_db":   48,
        "sweep":    False,
        "color_key": "pink",
    },
]


# ──────────────────────────────────────────────
#  FFT — implementación en punto fijo para MicroPython
# ──────────────────────────────────────────────

def fft(x_re, x_im):
    """
    FFT in-place de Cooley-Tukey (Decimación en tiempo).
    x_re, x_im : listas de floats de longitud potencia de 2.
    Modifica x_re y x_im en el lugar.
    """
    n = len(x_re)
    # Bit-reversal permutation
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            x_re[i], x_re[j] = x_re[j], x_re[i]
            x_im[i], x_im[j] = x_im[j], x_im[i]

    # Butterfly stages
    length = 2
    while length <= n:
        half = length >> 1
        ang  = -2.0 * math.pi / length
        wr   =  math.cos(ang)
        wi   =  math.sin(ang)
        for i in range(0, n, length):
            cur_wr, cur_wi = 1.0, 0.0
            for k in range(half):
                ur = x_re[i + k + half] * cur_wr - x_im[i + k + half] * cur_wi
                ui = x_re[i + k + half] * cur_wi + x_im[i + k + half] * cur_wr
                x_re[i + k + half] = x_re[i + k] - ur
                x_im[i + k + half] = x_im[i + k] - ui
                x_re[i + k] += ur
                x_im[i + k] += ui
                new_wr  = cur_wr * wr - cur_wi * wi
                cur_wi  = cur_wr * wi + cur_wi * wr
                cur_wr  = new_wr
        length <<= 1


def apply_hann_window(samples):
    """Aplica ventana de Hann para reducir leakage espectral."""
    n = len(samples)
    for i in range(n):
        w = 0.5 * (1.0 - math.cos(2.0 * math.pi * i / (n - 1)))
        samples[i] *= w
    return samples


def compute_magnitude_db(x_re, x_im):
    """
    Calcula magnitud en dB para cada bin del espectro positivo.
    Retorna lista de longitud FFT_SIZE // 2.
    """
    half = len(x_re) // 2
    mags = []
    for i in range(half):
        mag_sq = x_re[i] * x_re[i] + x_im[i] * x_im[i]
        if mag_sq > 0:
            db = 10.0 * math.log10(mag_sq)
        else:
            db = -120.0
        mags.append(db)
    return mags


def peak_bin_in_range(mags_db, bin_min, bin_max):
    """Devuelve (bin_pico, db_pico) dentro del rango dado."""
    best_bin = bin_min
    best_db  = mags_db[bin_min]
    for b in range(bin_min + 1, min(bin_max + 1, len(mags_db))):
        if mags_db[b] > best_db:
            best_db  = mags_db[b]
            best_bin = b
    return best_bin, best_db


def energy_in_range(mags_db, bin_min, bin_max):
    """Energía promedio (dB) dentro del rango de bins."""
    total = 0.0
    count = 0
    for b in range(bin_min, min(bin_max + 1, len(mags_db))):
        total += mags_db[b]
        count += 1
    return total / count if count else -120.0


# ──────────────────────────────────────────────
#  CLASIFICADOR PRINCIPAL
# ──────────────────────────────────────────────

class SoundClassifier:
    """
    Clasificador de sonidos basado en FFT + reglas de frecuencia.

    Uso:
        clf = SoundClassifier()
        result = clf.classify(samples_list)
        if result:
            print(result['label'], result['color_key'])
    """

    def __init__(self):
        self._last_trigger = {}   # label -> timestamp_ms de última detección
        self._sweep_history = {}  # label -> historial de bin dominante para detección de sweep

    def _cooldown_ok(self, label):
        now = utime.ticks_ms()
        last = self._last_trigger.get(label, 0)
        return utime.ticks_diff(now, last) >= COOLDOWN_MS

    def _update_sweep(self, label, peak_bin, window=4):
        """
        Para sonidos con sweep=True, verifica variación de frecuencia dominante.
        Devuelve True si el peak_bin ha variado suficientemente entre frames.
        """
        hist = self._sweep_history.get(label, [])
        hist.append(peak_bin)
        if len(hist) > window:
            hist = hist[-window:]
        self._sweep_history[label] = hist
        if len(hist) < 2:
            return False
        variation = max(hist) - min(hist)
        return variation >= 2  # al menos 2 bins de variación ≈ 62.5 Hz

    def classify(self, samples):
        """
        Clasifica un frame de audio.

        Parámetros
        ----------
        samples : list[float] o array — FFT_SIZE muestras normalizadas [-1.0, 1.0]

        Retorna
        -------
        dict con keys: label, category, priority, color_key, peak_db
        o None si no se detectó ningún sonido conocido.
        """
        if len(samples) < FFT_SIZE:
            return None

        # Convertir a float y aplicar ventana
        x_re = [float(s) for s in samples[:FFT_SIZE]]
        x_im = [0.0] * FFT_SIZE
        apply_hann_window(x_re)

        # FFT
        fft(x_re, x_im)

        # Magnitudes en dB
        mags_db = compute_magnitude_db(x_re, x_im)

        # Nivel global — descartar frames muy silenciosos
        global_peak = max(mags_db)
        if global_peak < THRESHOLD_DB:
            return None

        # Evaluar cada perfil de sonido
        candidates = []
        for profile in SOUND_PROFILES:
            b_min = profile["bins_range"][0]
            b_max = profile["bins_range"][1]

            peak_bin, peak_db = peak_bin_in_range(mags_db, b_min, b_max)
            avg_db = energy_in_range(mags_db, b_min, b_max)

            if peak_db < profile["min_db"]:
                continue  # energía insuficiente en este rango

            if profile.get("sweep"):
                sweep_ok = self._update_sweep(profile["label"], peak_bin)
                if not sweep_ok:
                    continue

            if not self._cooldown_ok(profile["label"]):
                continue

            candidates.append({
                "label":     profile["label"],
                "category":  profile["category"],
                "priority":  profile["priority"],
                "color_key": profile["color_key"],
                "peak_db":   round(peak_db, 1),
                "avg_db":    round(avg_db, 1),
            })

        if not candidates:
            return None

        # Seleccionar el candidato de mayor prioridad (menor número) y más energía
        candidates.sort(key=lambda c: (c["priority"], -c["peak_db"]))
        winner = candidates[0]

        # Registrar tiempo de última detección
        self._last_trigger[winner["label"]] = utime.ticks_ms()

        return winner