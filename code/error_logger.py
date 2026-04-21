"""
error_logger.py
Sistema robusto de logging de errores para Asistente Auditivo.

Registra todos los errores, warnings e información importante en archivos
para diagnóstico posterior. Útil para detectar problemas de reinicio,
energía insuficiente, o fallos recurrentes.

Características:
  - Logging en archivo + memoria
  - Niveles de severidad (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Información de timestamp y memoria
  - Detección de reinicios
  - Sin dependencias externas
"""

import gc
import os

import utime

# ──────────────────────────────────────────────
#  CONFIGURACIÓN
# ──────────────────────────────────────────────

LOG_FILE = "error_log.txt"
MAX_LOG_SIZE = 50000  # bytes máximo antes de rotación
MAX_MEMORY_ENTRIES = 100  # máximo de entradas en memoria
LOG_LEVEL = "DEBUG"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Niveles de severidad
LEVELS = {
    "DEBUG": 0,
    "INFO": 1,
    "WARNING": 2,
    "ERROR": 3,
    "CRITICAL": 4,
}

# ──────────────────────────────────────────────
#  CLASE LOGGER
# ──────────────────────────────────────────────


class ErrorLogger:
    """
    Sistema de logging robusto para diagnóstico de errores.

    Uso:
        logger = ErrorLogger()
        logger.info("Inicializando sistema...")
        try:
            # código
        except Exception as e:
            logger.error(f"Error en código: {e}")

        # Ver logs almacenados
        logger.print_memory_log()
    """

    def __init__(self, log_file=LOG_FILE):
        self.log_file = log_file
        self.memory_log = []  # buffer en memoria
        self.start_time = utime.ticks_ms()
        self.error_count = 0
        self.warning_count = 0
        self.restart_count = self._read_restart_count()

        # Log de inicio
        self._write_header()
        self.info(f"Logger inicializado (Reinicio #{self.restart_count})")

    def _get_free_memory(self):
        """Obtiene memoria libre en bytes."""
        try:
            gc.collect()
            import micropython

            return micropython.mem_info()
        except:
            return "N/A"

    def _get_uptime(self):
        """Obtiene tiempo de operación en segundos."""
        elapsed_ms = utime.ticks_diff(utime.ticks_ms(), self.start_time)
        return elapsed_ms // 1000

    def _read_restart_count(self):
        """Lee el contador de reinicios del archivo."""
        try:
            if self.log_file in os.listdir():
                with open(self.log_file, "r") as f:
                    content = f.read()
                    # Buscar "Reinicio #" en el archivo
                    count = 0
                    for line in content.split("\n"):
                        if "Reinicio #" in line:
                            count += 1
                    return count + 1
        except:
            pass
        return 1

    def _write_header(self):
        """Escribe encabezado en el archivo de log."""
        try:
            # Verificar tamaño del archivo y rotar si es necesario
            try:
                if self.log_file in os.listdir():
                    stat = os.stat(self.log_file)
                    if stat[6] > MAX_LOG_SIZE:
                        # Rotar archivo
                        backup_file = f"{self.log_file}.bak"
                        try:
                            os.remove(backup_file)
                        except:
                            pass
                        try:
                            os.rename(self.log_file, backup_file)
                        except:
                            pass
            except:
                pass

            # Escribir encabezado
            timestamp = utime.localtime(utime.time())
            header = (
                "\n"
                + "=" * 60
                + "\n"
                + f"[{timestamp[0]:04d}-{timestamp[1]:02d}-{timestamp[2]:02d} "
                f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}]\n"
                + f"Reinicio #{self.restart_count}\n"
                + "=" * 60
                + "\n"
            )

            mode = "a" if self.log_file in os.listdir() else "w"
            with open(self.log_file, mode) as f:
                f.write(header)
        except Exception as e:
            # Si falla escribir en archivo, al menos registrar en memoria
            self.memory_log.append(f"[ERROR] No se pudo escribir header: {e}")

    def _format_message(self, level, message, uptime=True):
        """Formatea un mensaje de log."""
        timestamp = utime.localtime(utime.time())
        time_str = f"{timestamp[3]:02d}:{timestamp[4]:02d}:{timestamp[5]:02d}"

        if uptime:
            uptime_sec = self._get_uptime()
            msg = f"[{time_str}] +{uptime_sec:5d}s [{level:8s}] {message}"
        else:
            msg = f"[{time_str}] [{level:8s}] {message}"

        return msg

    def _write_to_file(self, message):
        """Escribe mensaje en archivo de log."""
        try:
            with open(self.log_file, "a") as f:
                f.write(message + "\n")
        except Exception as e:
            # Si falla, solo agregar a memoria
            pass

    def _add_to_memory(self, message):
        """Agrega mensaje al buffer en memoria."""
        self.memory_log.append(message)
        if len(self.memory_log) > MAX_MEMORY_ENTRIES:
            self.memory_log = self.memory_log[-MAX_MEMORY_ENTRIES:]

    def log(self, level, message):
        """Log genérico con nivel especificado."""
        if LEVELS.get(level, 0) < LEVELS.get(LOG_LEVEL, 0):
            return

        # Formatear mensaje
        msg = self._format_message(level, message)

        # Escribir en archivo
        self._write_to_file(msg)

        # Agregar a memoria
        self._add_to_memory(msg)

        # Actualizar contadores
        if level == "ERROR":
            self.error_count += 1
        elif level == "WARNING":
            self.warning_count += 1

        # Imprimir en consola
        print(msg)

    def debug(self, message):
        """Log de nivel DEBUG."""
        self.log("DEBUG", message)

    def info(self, message):
        """Log de nivel INFO."""
        self.log("INFO", message)

    def warning(self, message):
        """Log de nivel WARNING."""
        self.log("WARNING", message)

    def error(self, message):
        """Log de nivel ERROR."""
        self.log("ERROR", message)

    def critical(self, message):
        """Log de nivel CRITICAL."""
        self.log("CRITICAL", message)

    def exception(self, title, exception):
        """Log de una excepción capturada."""
        error_msg = f"{title}: {str(exception)}"
        self.error(error_msg)
        self.debug(f"  Tipo: {type(exception).__name__}")

    def checkpoint(self, name):
        """Registra un checkpoint importante."""
        self.info(f"CHECKPOINT: {name}")

    def memory_status(self):
        """Log del estado de memoria."""
        gc.collect()
        try:
            import micropython

            free = micropython.mem_info()
            msg = f"MEMORIA: Free heap (bytes) - no disponible"
        except:
            msg = "MEMORIA: No disponible"
        self.debug(msg)

    def print_memory_log(self):
        """Imprime el buffer de memoria en consola."""
        print("\n" + "=" * 60)
        print("BUFFER DE MEMORIA (últimas entradas)")
        print("=" * 60)
        for entry in self.memory_log:
            print(entry)
        print("=" * 60)
        print(f"Total de errores: {self.error_count}")
        print(f"Total de warnings: {self.warning_count}")
        print(f"Reinicios registrados: {self.restart_count}")
        print("=" * 60 + "\n")

    def read_file_log(self):
        """Lee y devuelve el contenido del archivo de log."""
        try:
            if self.log_file in os.listdir():
                with open(self.log_file, "r") as f:
                    return f.read()
        except:
            pass
        return "No hay archivo de log disponible"

    def print_file_log(self, lines=50):
        """Imprime las últimas líneas del archivo de log."""
        try:
            if self.log_file in os.listdir():
                with open(self.log_file, "r") as f:
                    content = f.read()
                    log_lines = content.split("\n")
                    last_lines = log_lines[-lines:]

                    print("\n" + "=" * 60)
                    print(f"ARCHIVO DE LOG (últimas {lines} líneas)")
                    print("=" * 60)
                    for line in last_lines:
                        print(line)
                    print("=" * 60 + "\n")
                    return

        except Exception as e:
            print(f"Error leyendo archivo de log: {e}")

        print("No hay archivo de log disponible")

    def clear_log(self):
        """Limpia el archivo de log (con cuidado)."""
        try:
            if self.log_file in os.listdir():
                os.remove(self.log_file)
                self.info("Archivo de log limpiado")
        except Exception as e:
            self.error(f"Error limpiando log: {e}")

    def get_statistics(self):
        """Retorna estadísticas del sistema."""
        return {
            "errors": self.error_count,
            "warnings": self.warning_count,
            "uptime_seconds": self._get_uptime(),
            "restarts": self.restart_count,
            "memory_log_entries": len(self.memory_log),
        }

    def print_statistics(self):
        """Imprime estadísticas del sistema."""
        stats = self.get_statistics()
        print("\n" + "=" * 60)
        print("ESTADÍSTICAS DEL SISTEMA")
        print("=" * 60)
        print(f"Errores encontrados: {stats['errors']}")
        print(f"Warnings encontrados: {stats['warnings']}")
        print(f"Tiempo de operación: {stats['uptime_seconds']} segundos")
        print(f"Reinicios detectados: {stats['restarts']}")
        print(f"Entradas en buffer: {stats['memory_log_entries']}")
        print("=" * 60 + "\n")


# ──────────────────────────────────────────────
#  INSTANCIA GLOBAL
# ──────────────────────────────────────────────

# Crear logger global para facilitar uso
_global_logger = None


def init_logger(log_file=LOG_FILE):
    """Inicializa el logger global."""
    global _global_logger
    _global_logger = ErrorLogger(log_file)
    return _global_logger


def get_logger():
    """Obtiene el logger global."""
    global _global_logger
    if _global_logger is None:
        init_logger()
    return _global_logger


# ──────────────────────────────────────────────
#  FUNCIONES DE CONVENIENCIA
# ──────────────────────────────────────────────


def log_debug(message):
    """Log debug global."""
    get_logger().debug(message)


def log_info(message):
    """Log info global."""
    get_logger().info(message)


def log_warning(message):
    """Log warning global."""
    get_logger().warning(message)


def log_error(message):
    """Log error global."""
    get_logger().error(message)


def log_critical(message):
    """Log critical global."""
    get_logger().critical(message)


def log_checkpoint(name):
    """Checkpoint global."""
    get_logger().checkpoint(name)


def log_exception(title, exception):
    """Excepción global."""
    get_logger().exception(title, exception)


# ──────────────────────────────────────────────
#  EJEMPLO DE USO
# ──────────────────────────────────────────────

if __name__ == "__main__":
    print("Prueba del sistema de logging\n")

    # Inicializar logger
    logger = ErrorLogger()

    # Ejemplos de logging
    logger.debug("Este es un mensaje de debug")
    logger.info("Sistema inicializado correctamente")
    logger.warning("Advertencia: memoria baja")
    logger.error("Error en componente X")

    # Checkpoint
    logger.checkpoint("Prueba completada")

    # Información de memoria
    logger.memory_status()

    # Simular una excepción
    try:
        x = 1 / 0
    except Exception as e:
        logger.exception("Error en cálculo", e)

    # Mostrar estadísticas
    logger.print_statistics()

    # Mostrar buffer en memoria
    logger.print_memory_log()
