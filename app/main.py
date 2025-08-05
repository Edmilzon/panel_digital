# --- FUNCIÓN ---
def saludar(nombre):
    return f"¡Hola {nombre}! Bienvenido a tu primera app en Python."

# --- CLASE ---
class Usuario:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self.edad = edad
    
    def presentarse(self):
        print(f"Soy {self.nombre} y tengo {self.edad} años.")

# --- PROGRAMA PRINCIPAL ---
if __name__ == "__main__":
    print("=== MI PRIMERA APP ===")
    
    # Usar la función
    mensaje = saludar("edmilzon")
    print(mensaje)
    
    # Usar la clase
    usuario1 = Usuario("edmilzon", 30)
    usuario1.presentarse()