class User:
    def __init__(self, id, email, nombre, rol):
        self.id = id
        self.email = email
        self.nombre = nombre
        self.rol = rol

    def validate_email(self):
        # Basic email validation logic
        return '@' in self.email

    def validate_nombre(self):
        # Validate that nombre is not empty
        return bool(self.nombre)

    def validate_rol(self):
        # Validate rol against allowed roles
        allowed_roles = ['admin', 'user', 'guest']
        return self.rol in allowed_roles

    def is_valid(self):
        # Check if all fields are valid
        return all([self.validate_email(), self.validate_nombre(), self.validate_rol()])