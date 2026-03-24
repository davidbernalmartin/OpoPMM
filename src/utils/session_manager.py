class SessionManager:
    def __init__(self):
        self.session_state = {}  # Initialize session state

    def cleanup(self):
        self.session_state.clear()  # Cleanup session state

# Example usage
if __name__ == '__main__':
    manager = SessionManager()
    print("Session initialized:", manager.session_state)
    manager.cleanup()
    print("Session after cleanup:", manager.session_state)