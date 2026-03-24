class Examen:
    def __init__(self, notas):
        self.notas = notas  # List of grades

    def calcular_nota_final(self):
        if not self.notas:
            return 0  # No grades
        return sum(self.notas) / len(self.notas)  # Average of grades

    def agregar_nota(self, nota):
        self.notas.append(nota)  # Add a new grade