def saludar(nombre):
    print(f"hola,{nombre}")

saludar("Ariel")

def suma(a,b):
    return a+b

res = suma(10,20)
print(res)

def potencia(base, exponente=2):
    return base**exponente

print(potencia(2))
print(potencia(2,3))

class Perro:
    def __init__(self, nombre, edad):
        self.nombre = nombre
        self.edad = edad
    
    def ladrar(self):
        print("guau")

perro1 = Perro("Firulais", 3)
print(perro1.nombre)
perro1.ladrar()