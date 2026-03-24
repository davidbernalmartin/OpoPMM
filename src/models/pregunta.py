class Pregunta:
    def __init__(self, id, texto, opciones, respuesta_correcta, tipo="multiple"):
        self.id = id
        self.texto = texto
        self.opciones = opciones  # List of options
        self.respuesta_correcta = respuesta_correcta
        self.tipo = tipo  # 'multiple', 'verdadero_falso', 'abierta'

    def validar_pregunta(self):
        """Validate that the question has all required fields"""
        return bool(self.texto and self.opciones and self.respuesta_correcta)

    def verificar_respuesta(self, respuesta_usuario):
        """Check if user's answer is correct"""
        return respuesta_usuario == self.respuesta_correcta

    def get_opciones(self):
        """Return list of options"""
        return self.opciones

    def __str__(self):
        return f"Pregunta({self.id}: {self.texto})"