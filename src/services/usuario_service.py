class UsuarioService:
    def __init__(self):
        # Initialize user management
        self.users = {}
        self.user_id_counter = 1

    def create_user(self, name, email):
        user_id = self.user_id_counter
        self.users[user_id] = {'id': user_id, 'name': name, 'email': email}
        self.user_id_counter += 1
        return self.users[user_id]

    def read_user(self, user_id):
        return self.users.get(user_id, None)

    def update_user(self, user_id, name=None, email=None):
        user = self.users.get(user_id)
        if user:
            if name:
                user['name'] = name
            if email:
                user['email'] = email
            return user
        return None

    def delete_user(self, user_id):
        return self.users.pop(user_id, None)