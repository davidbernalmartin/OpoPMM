class Estadistica:
    def __init__(self, usuario_id, examen_id, preguntas_correctas, preguntas_totales, tiempo_dedicado):
        self.usuario_id = usuario_id
        self.examen_id = examen_id
        self.preguntas_correctas = preguntas_correctas
        self.preguntas_totales = preguntas_totales
        self.tiempo_dedicado = tiempo_dedicado  # in seconds

    def calcular_porcentaje(self):
        """Calculate the percentage of correct answers"""
        if self.preguntas_totales == 0:
            return 0
        return (self.preguntas_correctas / self.preguntas_totales) * 100

    def obtener_calificacion(self):
        """Get the grade based on percentage"""
        porcentaje = self.calcular_porcentaje()
        if porcentaje >= 90:
            return 'A'
        elif porcentaje >= 80:
            return 'B'
        elif porcentaje >= 70:
            return 'C'
        elif porcentaje >= 60:
            return 'D'
        else:
            return 'F'

    def obtener_tiempo_formato(self):
        """Convert tiempo_dedicado to HH:MM:SS format"""
        horas = self.tiempo_dedicado // 3600
        minutos = (self.tiempo_dedicado % 3600) // 60
        segundos = self.tiempo_dedicado % 60
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    def __str__(self):
        return f"Estadistica(usuario={self.usuario_id}, examen={self.examen_id}, correctas={self.preguntas_correctas}/{self.preguntas_totales})"