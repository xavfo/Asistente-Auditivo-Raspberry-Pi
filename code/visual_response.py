"""
visual_response.py
Módulo de respuesta visual para el dispositivo wearable auditivo.
Controla LEDs NeoPixel (WS2812B) y pantalla TFT de 2" (ST7789).

Hardware esperado:
  - NeoPixel: GP15 (ajustable), tira de 5–8 LEDs
  - Pantalla ST7789 2": SPI0 — SCK=GP18, MOSI=GP19, CS=GP17, DC=GP16, RST=GP20
"""

import utime

# ──────────────────────────────────────────────
#  NEOPIXEL (WS2812B)
# ──────────────────────────────────────────────

try:
    from machine import Pin
    import neopixel
    _HAS_NEOPIXEL = True
except ImportError:
    _HAS_NEOPIXEL = False

NUM_LEDS    = 5       # Número de LEDs en tu tira
LED_PIN     = 15      # GP15
LED_BRIGHT  = 0.4     # Brillo global 0.0–1.0 (reduce consumo de batería)

# ──────────────────────────────────────────────
#  PANTALLA ST7789 2"
# ──────────────────────────────────────────────

try:
    from machine import SPI, Pin
    import st7789          # Librería: https://github.com/russhughes/st7789_mpy
    import vga1_bold_16x32 as font  # Fuente incluida con st7789_mpy
    _HAS_DISPLAY = True
except ImportError:
    _HAS_DISPLAY = False

DISPLAY_WIDTH  = 240
DISPLAY_HEIGHT = 135   # Para pantalla 2" Waveshare/Adafruit 240×135

# ──────────────────────────────────────────────
#  PALETA DE COLORES  (R, G, B) para NeoPixel
# ──────────────────────────────────────────────

def _scale(color, brightness):
    return tuple(int(c * brightness) for c in color)

COLORS_RGB = {
    "red":    (255, 0,   0),
    "orange": (255, 80,  0),
    "yellow": (220, 180, 0),
    "blue":   (0,   100, 255),
    "purple": (160, 0,   220),
    "green":  (0,   200, 60),
    "pink":   (220, 0,   120),
    "off":    (0,   0,   0),
}

# Colores para pantalla ST7789 (formato 16-bit 565)
COLORS_565 = {
    "red":    st7789.RED    if _HAS_DISPLAY else 0xF800,
    "orange": 0xFD00,
    "yellow": st7789.YELLOW if _HAS_DISPLAY else 0xFFE0,
    "blue":   st7789.BLUE   if _HAS_DISPLAY else 0x001F,
    "purple": 0x780F,
    "green":  st7789.GREEN  if _HAS_DISPLAY else 0x07E0,
    "pink":   0xF81F,
    "off":    st7789.BLACK  if _HAS_DISPLAY else 0x0000,
}

# ──────────────────────────────────────────────
#  EMOJIS / ICONOS (texto ASCII para pantalla)
# ──────────────────────────────────────────────

SOUND_ICONS = {
    "sirena_emergencia": ("SIRENA", "!!!"),
    "alarma_humo":       ("HUMO",   ">>>"),
    "bocina_auto":       ("AUTO",   "---"),
    "timbre_puerta":     ("PUERTA", "~~"),
    "llanto_bebe":       ("BEBE",   ":-("),
    "telefono":          ("LLAMA",  ")))"),
    "perro_ladrando":    ("PERRO",  "wof"),
}


# ──────────────────────────────────────────────
#  CLASE PRINCIPAL
# ──────────────────────────────────────────────

class VisualResponse:
    """
    Gestiona la respuesta visual (LEDs + pantalla) ante un sonido detectado.

    Uso:
        vr = VisualResponse()
        vr.trigger(result_dict)   # result_dict viene del SoundClassifier
        vr.update()               # llamar en cada iteración del loop para animar
    """

    def __init__(self):
        self._init_leds()
        self._init_display()
        self._anim_state   = None   # estado de la animación activa
        self._anim_start   = 0
        self._anim_step    = 0
        self._current_color_key = "off"

    # ── Inicialización ───────────────────────

    def _init_leds(self):
        if _HAS_NEOPIXEL:
            self._np = neopixel.NeoPixel(Pin(LED_PIN), NUM_LEDS)
            self._led_off()
        else:
            self._np = None
            print("[VisualResponse] NeoPixel no disponible — modo simulación")

    def _init_display(self):
        if _HAS_DISPLAY:
            spi = SPI(0, baudrate=40_000_000,
                      sck=Pin(18), mosi=Pin(19))
            self._tft = st7789.ST7789(
                spi,
                DISPLAY_HEIGHT,
                DISPLAY_WIDTH,
                reset     = Pin(20, Pin.OUT),
                cs        = Pin(17, Pin.OUT),
                dc        = Pin(16, Pin.OUT),
                rotation  = 1,
            )
            self._tft.init()
            self._tft.fill(st7789.BLACK)
        else:
            self._tft = None
            print("[VisualResponse] Display no disponible — modo simulación")

    # ── LEDs ─────────────────────────────────

    def _led_off(self):
        if self._np:
            for i in range(NUM_LEDS):
                self._np[i] = (0, 0, 0)
            self._np.write()

    def _led_set_all(self, color_key):
        if not self._np:
            return
        rgb = _scale(COLORS_RGB.get(color_key, (0, 0, 0)), LED_BRIGHT)
        for i in range(NUM_LEDS):
            self._np[i] = rgb
        self._np.write()

    def _led_set_pattern(self, color_key, pattern):
        """
        pattern: lista de bool, longitud NUM_LEDS.
        True = LED encendido con color_key, False = apagado.
        """
        if not self._np:
            return
        rgb = _scale(COLORS_RGB.get(color_key, (0, 0, 0)), LED_BRIGHT)
        for i in range(NUM_LEDS):
            self._np[i] = rgb if pattern[i] else (0, 0, 0)
        self._np.write()

    # ── Pantalla ──────────────────────────────

    def _display_event(self, color_key, label):
        if not self._tft:
            print(f"[PANTALLA] {label} | color={color_key}")
            return

        bg   = COLORS_565.get(color_key, 0x0000)
        fg   = st7789.WHITE
        icon, short = SOUND_ICONS.get(label, ("???", ""))

        self._tft.fill(bg)

        # Línea 1: ícono grande centrado
        x = (DISPLAY_WIDTH  - len(icon) * 16) // 2
        y = (DISPLAY_HEIGHT - 64) // 2
        self._tft.text(font, icon,  x, y,      fg, bg)
        self._tft.text(font, short, (DISPLAY_WIDTH - len(short)*16)//2,
                       y + 36, fg, bg)

    def _display_clear(self):
        if self._tft:
            self._tft.fill(st7789.BLACK)

    # ── Animaciones ───────────────────────────

    # Cada animación es un generador que devuelve el delay en ms hasta el
    # siguiente paso. El método update() lo avanza.

    def _anim_flash(self, color_key, times=3, on_ms=120, off_ms=100):
        """Destello rápido N veces — urgencia alta."""
        for _ in range(times):
            self._led_set_all(color_key)
            yield on_ms
            self._led_off()
            yield off_ms
        # Dejar un LED encendido como indicador residual
        if self._np:
            rgb = _scale(COLORS_RGB.get(color_key, (0,0,0)), LED_BRIGHT * 0.3)
            self._np[0] = rgb
            self._np.write()

    def _anim_wave(self, color_key, cycles=2, step_ms=80):
        """Ola de LEDs de izquierda a derecha."""
        for _ in range(cycles):
            for i in range(NUM_LEDS):
                pattern = [j == i for j in range(NUM_LEDS)]
                self._led_set_pattern(color_key, pattern)
                yield step_ms
        self._led_off()

    def _anim_pulse(self, color_key, pulses=2, on_ms=300, off_ms=200):
        """Pulsación lenta — notificación suave."""
        for _ in range(pulses):
            self._led_set_all(color_key)
            yield on_ms
            self._led_off()
            yield off_ms

    def _anim_alternate(self, color_key, steps=6, step_ms=100):
        """LEDs pares / impares alternados — alta urgencia."""
        for i in range(steps):
            pattern = [(j % 2 == i % 2) for j in range(NUM_LEDS)]
            self._led_set_pattern(color_key, pattern)
            yield step_ms
        self._led_off()

    # ── API pública ───────────────────────────

    def trigger(self, detection):
        """
        Inicia respuesta visual para un evento de sonido detectado.

        detection: dict retornado por SoundClassifier.classify()
        """
        label     = detection["label"]
        priority  = detection["priority"]
        color_key = detection["color_key"]
        self._current_color_key = color_key

        # Mostrar en pantalla
        self._display_event(color_key, label)

        # Seleccionar animación según prioridad
        if priority == 1:
            gen = self._anim_alternate(color_key)
        elif priority == 2:
            gen = self._anim_flash(color_key)
        elif priority == 3:
            gen = self._anim_pulse(color_key)
        else:
            gen = self._anim_wave(color_key)

        self._anim_state = gen
        self._anim_start = utime.ticks_ms()
        self._anim_step  = 0

        print(f"[VISUAL] {label} | prioridad={priority} | color={color_key} | {detection['peak_db']} dB")

    def update(self):
        """
        Avanza la animación activa. Llamar en cada iteración del loop principal.
        No es bloqueante.
        """
        if self._anim_state is None:
            return

        now   = utime.ticks_ms()
        elapsed = utime.ticks_diff(now, self._anim_start)

        if elapsed >= self._anim_step:
            try:
                delay_ms       = next(self._anim_state)
                self._anim_step = elapsed + delay_ms
            except StopIteration:
                self._anim_state = None
                self._display_clear()

    def clear(self):
        """Apaga todo inmediatamente."""
        self._led_off()
        self._display_clear()
        self._anim_state = None
