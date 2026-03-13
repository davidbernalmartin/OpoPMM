import sqlite3
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://viglgksnpajdgpfprmqg.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZpZ2xna3NucGFqZGdwZnBybXFnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMzNDkzNDcsImV4cCI6MjA4ODkyNTM0N30.k2o2KzYnRvg3fSjMA5fCvn2-VAJVZMJiUW1_UKFNZiA"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)


def obtener_cliente():
    """Retorna la instancia de conexión para usarla en cualquier parte."""
    return supabase

def cargar_temas_nube():
    """Descarga la lista de temas desde la nube para usarla en los desplegables."""
    try:
        # Traemos ID y Nombre, ordenados por ID
        res = supabase.table("temas").select("id, nombre").order("id").execute()
        return res.data # Esto devuelve una lista de diccionarios [{'id': 1, 'nombre': '...'}, ...]
    except Exception as e:
        print(f"Error al conectar con Supabase: {e}")
        return []
    
def obtener_temas_nube():
    """
    Descarga los temas de Supabase y devuelve:
    1. Una lista de nombres (para los ComboBox).
    2. Un diccionario {'Nombre': ID} (para guardar preguntas).
    """
    try:
        # Consultamos la tabla 'temas' ordenada por el ID
        res = supabase.table("temas").select("id, nombre").order("id").execute()
        
        # Extraemos los nombres para las interfaces (ComboBox, Checkboxes)
        nombres = [t['nombre'] for t in res.data]
        
        # Creamos un mapa de búsqueda rápida
        mapa = {t['nombre']: t['id'] for t in res.data}
        
        return nombres, mapa
    except Exception as e:
        print(f"❌ Error al conectar con Supabase: {e}")
        # Devolvemos listas vacías para que el programa no "explote" si falla el WiFi
        return [], {}
