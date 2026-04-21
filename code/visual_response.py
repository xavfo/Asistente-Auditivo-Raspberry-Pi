"""
visual_response.py
Módulo de respuesta visual para el dispositivo wearable auditivo.
Controla LEDs NeoPixel (WS2812B) y pantalla LCD de 1.14" (ST7735).

Hardware esperado:
  - NeoPixel: GP15 (ajustable), tira de 5–8 LEDs
  - Pantalla LCD 1.14": Pico-LCD-1.14-V2 (driver incluido)
  - Botones: centro (GP3), izquierda (GP16), derecha (GP20), arriba (GP2), abajo (GP18)
"""

import utime
from machine import Pin

# Importar el driver LCD
_HAS_LCD = False
LCD_1inch14 = None

try:
    from Pico_LCD_1inch14_V2 import LCD_1inch14

    _HAS_LCD = True
except ImportError:
    try:
        # Fallback: intentar con guiones en el nombre
        from Pico_LCD_1_14_V2 import LCD_1inch14

        _HAS_LCD = True
    except ImportError:
        print("[ADVERTENCIA] No se pudo importar driver LCD - modo simulación")
        _HAS_LCD = False

# Importar NeoPixel si está disponible
try:
    import neopixel

    _HAS_NEOPIXEL = True
except ImportError:
    _HAS_NEOPIXEL = False

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────

NUM_LEDS = 5
LED_PIN = 15
LED_BRIGHT = 0.4

NUM_HISTORY = 5  # Últimos 5 sonidos

# Pines de botones
BTN_CENTER = 3  # Detener alarma
BTN_LEFT = 16  # Navegar izquierda
BTN_RIGHT = 20  # Navegar derecha
BTN_UP = 2  # Arriba
BTN_DOWN = 18  # Abajo

# Colores RGB para NeoPixel
COLORS_RGB = {
    "red": (255, 0, 0),
    "orange": (255, 80, 0),
    "yellow": (220, 180, 0),
    "blue": (0, 100, 255),
    "purple": (160, 0, 220),
    "green": (0, 200, 60),
    "pink": (220, 0, 120),
    "off": (0, 0, 0),
}

# Colores para pantalla LCD (RGB565 - formato del driver)
COLORS_565 = {
    "red": 0xF800,
    "orange": 0xFD00,
    "yellow": 0xFFE0,
    "blue": 0x001F,
    "purple": 0x780F,
    "green": 0x07E0,
    "pink": 0xF81F,
    "white": 0xFFFF,
    "black": 0x0000,
}


def _scale(color, brightness):
    """Escala un color RGB por un factor de brillo."""
    return tuple(int(c * brightness) for c in color)


class VisualResponse:
    """
    Gestiona la respuesta visual (LEDs + pantalla LCD) ante sonidos detectados.

    Características:
    - Muestra tiempo transcurrido en pantalla
    - Anima LEDs según tipo de sonido detectado
    - Mantiene historial de 5 últimos sonidos
    - Permite navegar con botones izquierda/derecha
    - Detiene alarma con botón central
    """

    def __init__(self):
        self._init_leds()
        self._init_display()
        self._init_buttons()

        # Historial de sonidos
        self.sound_history = []  # Lista de dicts con info de sonidos
        self.history_index = 0  # Índice del sonido mostrado en pantalla

        # Estado de alarma
        self.alarm_active = False
        self.alarm_start_time = 0
        self.current_detection = None

        # Animación
        self._anim_state = None
        self._anim_start = 0
        self._anim_step = 0

        # Control de botones (anti-rebote)
        self.btn_center_pressed = False
        self.btn_left_pressed = False
        self.btn_right_pressed = False
        self.btn_up_pressed = False
        self.btn_down_pressed = False

        # Tiempo de inicio del programa
        self.start_time = utime.ticks_ms()

        print("[VisualResponse] Inicializado correctamente")

    # ── Inicialización ───────────────────────

    def _init_leds(self):
        """Inicializa la tira NeoPixel."""
        if not _HAS_NEOPIXEL:
            self._np = None
            print("[VisualResponse] NeoPixel no disponible")
            return

        try:
            self._np = neopixel.NeoPixel(Pin(LED_PIN), NUM_LEDS)
            self._led_off()
            print("[VisualResponse] NeoPixel inicializado en GP15")
        except Exception as e:
            self._np = None
            print(f"[VisualResponse] Error al inicializar NeoPixel: {e}")

    def _init_display(self):
        """Inicializa la pantalla LCD."""
        if not _HAS_LCD or LCD_1inch14 is None:
            self.lcd = None
            print("[VisualResponse] Driver LCD no disponible")
            return

        try:
            self.lcd = LCD_1inch14()
            # Mostrar pantalla inicial
            self.lcd.fill(COLORS_565["black"])
            self.lcd.text("Inicializando...", 20, 50, COLORS_565["white"])
            self.lcd.show()
            print("[VisualResponse] Display LCD 1.14 inicializado")
        except Exception as e:
            self.lcd = None
            print(f"[VisualResponse] Error al inicializar LCD: {e}")

    def _init_buttons(self):
        """Inicializa los botones."""
        try:
            self.btn_center = Pin(BTN_CENTER, Pin.IN, Pin.PULL_UP)
            self.btn_left = Pin(BTN_LEFT, Pin.IN, Pin.PULL_UP)
            self.btn_right = Pin(BTN_RIGHT, Pin.IN, Pin.PULL_UP)
            self.btn_up = Pin(BTN_UP, Pin.IN, Pin.PULL_UP)
            self.btn_down = Pin(BTN_DOWN, Pin.IN, Pin.PULL_UP)
            print("[VisualResponse] Botones inicializados")
        except Exception as e:
            print(f"[VisualResponse] Error al inicializar botones: {e}")

    # ── LEDs ─────────────────────────────────

    def _led_off(self):
        """Apaga todos los LEDs."""
        if self._np:
            for i in range(NUM_LEDS):
                self._np[i] = (0, 0, 0)
            self._np.write()

    def _led_set_all(self, color_key):
        """Enciende todos los LEDs con un color."""
        if not self._np:
            return
        rgb = _scale(COLORS_RGB.get(color_key, (0, 0, 0)), LED_BRIGHT)
        for i in range(NUM_LEDS):
            self._np[i] = rgb
        self._np.write()

    def _led_set_pattern(self, color_key, pattern):
        """
        Enciende LEDs según un patrón.
        pattern: lista de bool, longitud NUM_LEDS
        """
        if not self._np:
            return
        rgb = _scale(COLORS_RGB.get(color_key, (0, 0, 0)), LED_BRIGHT)
        for i in range(NUM_LEDS):
            self._np[i] = rgb if pattern[i] else (0, 0, 0)
        self._np.write()

    # ── Pantalla ──────────────────────────────

    def _display_refresh(self):
        """Refresca la pantalla con la información actual."""
        if not self.lcd:
            return

        try:
            # Limpiar pantalla
            self.lcd.fill(COLORS_565["black"])

            # Obtener tiempo transcurrido
            elapsed_ms = utime.ticks_diff(utime.ticks_ms(), self.start_time)
            elapsed_sec = elapsed_ms // 1000
            minutes = elapsed_sec // 60
            seconds = elapsed_sec % 60
            time_str = f"{minutes:02d}:{seconds:02d}"

            # ─ Línea 1: Tiempo ─
            self.lcd.text(time_str, 10, 5, COLORS_565["yellow"])

            # ─ Línea 2-3: Estado actual ─
            if self.alarm_active and self.current_detection:
                label = self.current_detection.get("label", "Desconocido")
                # Truncar label si es muy largo
                if len(label) > 20:
                    label = label[:17] + "..."
                color_key = self.current_detection.get("color_key", "white")
                color = COLORS_565.get(color_key, COLORS_565["white"])
                peak_db = self.current_detection.get("peak_db", "?")

                self.lcd.text(">> DETECTADO <<", 10, 20, COLORS_565["yellow"])
                self.lcd.text(label, 10, 30, color)
                self.lcd.text(f"DB: {peak_db}", 10, 40, COLORS_565["white"])
            else:
                self.lcd.text("En espera...", 10, 25, COLORS_565["green"])

            # ─ Línea 4: Separador ─
            self.lcd.hline(5, 50, 230, COLORS_565["white"])

            # ─ Línea 5+: Historial de últimos 5 sonidos ─
            self.lcd.text("ULTIMOS SONIDOS:", 10, 55, COLORS_565["white"])

            y_pos = 65
            if len(self.sound_history) == 0:
                self.lcd.text("(ninguno aun)", 10, y_pos, COLORS_565["white"])
            else:
                # Mostrar últimos 5 sonidos en orden inverso (más reciente arriba)
                displayed = 0
                for i in range(min(5, len(self.sound_history))):
                    idx = len(self.sound_history) - 1 - i
                    sound = self.sound_history[idx]
                    label = sound.get("label", "?")

                    # Truncar si es muy largo
                    if len(label) > 18:
                        label = label[:15] + "..."

                    # Resaltar el sonido actualmente seleccionado
                    if idx == self.history_index and len(self.sound_history) > 0:
                        marker = ">>>"
                        color = COLORS_565["yellow"]
                    else:
                        marker = "   "
                        color = COLORS_565["white"]

                    self.lcd.text(f"{marker} {label}", 10, y_pos, color)
                    y_pos += 10
                    displayed += 1

                    if y_pos > 125:  # Evitar escribir fuera de pantalla
                        break

            self.lcd.show()
        except Exception as e:
            print(f"[ERROR] Error al refrescar LCD: {e}")

    # ── Animaciones ───────────────────────────

    def _anim_flash(self, color_key, times=3, on_ms=120, off_ms=100):
        """Destello rápido — urgencia alta."""
        for _ in range(times):
            self._led_set_all(color_key)
            yield on_ms
            self._led_off()
            yield off_ms

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
        """LEDs pares / impares alternados — máxima urgencia."""
        for i in range(steps):
            pattern = [(j % 2 == i % 2) for j in range(NUM_LEDS)]
            self._led_set_pattern(color_key, pattern)
            yield step_ms
        self._led_off()

    # ── API pública ───────────────────────────

    def trigger(self, detection):
        """
        Inicia respuesta visual para un evento de sonido detectado.

        Parámetros
        ----------
        detection : dict
            Diccionario retornado por SoundClassifier con keys:
            - label: nombre del sonido
            - color_key: color para LEDs y pantalla
            - priority: 1-5 (1=máxima urgencia)
            - peak_db: nivel de dB detectado
        """
        self.current_detection = detection
        self.alarm_active = True
        self.alarm_start_time = utime.ticks_ms()

        # Agregar al historial
        self.sound_history.append(
            {
                "label": detection.get("label", "Desconocido"),
                "color_key": detection.get("color_key", "white"),
                "peak_db": detection.get("peak_db", 0),
                "priority": detection.get("priority", 3),
                "timestamp": utime.ticks_ms(),
            }
        )

        # Mantener solo los últimos 5
        if len(self.sound_history) > NUM_HISTORY:
            self.sound_history = self.sound_history[-NUM_HISTORY:]

        self.history_index = len(self.sound_history) - 1

        # Iniciar animación según prioridad
        priority = detection.get("priority", 3)
        color_key = detection.get("color_key", "white")

        if priority == 1:
            gen = self._anim_alternate(color_key, steps=8)
        elif priority == 2:
            gen = self._anim_flash(color_key, times=4)
        elif priority == 3:
            gen = self._anim_wave(color_key, cycles=2)
        else:
            gen = self._anim_pulse(color_key, pulses=2)

        self._anim_state = gen
        self._anim_start = utime.ticks_ms()
        self._anim_step = 0

        print(
            f"[VISUAL] {detection.get('label')} | Prioridad: {priority} | DB: {detection.get('peak_db')}"
        )

    def stop_alarm(self):
        """Detiene la alarma actual."""
        if self.alarm_active:
            print("[VISUAL] Alarma detenida por usuario")
        self.alarm_active = False
        self._led_off()
        self._anim_state = None

    def update(self):
        """
        Actualiza animación, interfaz y estado de botones.
        Llamar en cada iteración del loop principal.
        """
        # ─ Verificar botón CENTRAL (detener alarma) ─
        if self.btn_center.value() == 0:
            if not self.btn_center_pressed:
                self.btn_center_pressed = True
                self.stop_alarm()
        else:
            self.btn_center_pressed = False

        # ─ Verificar botón IZQUIERDA (navegar historial) ─
        if self.btn_left.value() == 0:
            if not self.btn_left_pressed:
                self.btn_left_pressed = True
                if self.history_index > 0:
                    self.history_index -= 1
        else:
            self.btn_left_pressed = False

        # ─ Verificar botón DERECHA (navegar historial) ─
        if self.btn_right.value() == 0:
            if not self.btn_right_pressed:
                self.btn_right_pressed = True
                if self.history_index < len(self.sound_history) - 1:
                    self.history_index += 1
        else:
            self.btn_right_pressed = False

        # ─ Avanzar animación ─
        if self._anim_state is not None and self.alarm_active:
            now = utime.ticks_ms()
            elapsed = utime.ticks_diff(now, self._anim_start)

            if elapsed >= self._anim_step:
                try:
                    delay_ms = next(self._anim_state)
                    self._anim_step = elapsed + delay_ms
                except StopIteration:
                    self._anim_state = None
                    self._led_off()

        # ─ Refrescar pantalla ─
        self._display_refresh()

    def clear(self):
        """Apaga todo inmediatamente."""
        self._led_off()
        self.alarm_active = False
        self._anim_state = None
        if self.lcd:
            self.lcd.fill(COLORS_565["black"])
            self.lcd.show()
