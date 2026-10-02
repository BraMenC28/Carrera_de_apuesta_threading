# ==========================================
# 1. IMPORTACIÓN DE LIBRERÍAS
# ==========================================
import tkinter as tk           # Librería principal para crear la interfaz gráfica (Ventanas, botones, etiquetas)
from tkinter import messagebox # Submódulo de Tkinter para mostrar ventanas emergentes (alertas y mensajes)
import random                  # Librería nativa para generar números aleatorios (usada para variar la velocidad)
import time                    # Librería nativa para pausar la ejecución de los hilos y medir tiempos reales
import threading               # Librería nativa para manejar múltiples hilos (procesos paralelos) simultáneos

# ==========================================
# 2. DEFINICIÓN DE CLASES (Orientación a Objetos)
# ==========================================
# Definimos la "plantilla" o "molde" para instanciar cada uno de los caballos.
class Caballo:
    def __init__(self, id_caballo, y_pos, ventana, img_caballo):
        # --- Atributos de Identificación y Posición ---
        self.id_caballo = id_caballo  # Número identificador del caballo (0 al 9)
        self.y_pos = y_pos            # Coordenada 'y' fija para mantenerlo en su carril respectivo
        self.ventana = ventana        # Referencia a la ventana de Tkinter donde se dibujará
        
        # --- Atributos de Estado de Movimiento ---
        self.x_inicial = 33           # Posición 'x' inicial (Línea de salida en la imagen de la pista)
        self.x = self.x_inicial       # Posición 'x' actual que irá cambiando durante la carrera
        self.direccion = 1            # Vector de dirección: 1 (Hacia la derecha), -1 (Hacia la izquierda)
        self.vueltas_completadas = 0  # Contador acumulativo de idas y vueltas terminadas
        self.corriendo = False        # Bandera booleana: Indica si el caballo está en movimiento o detenido
        
        # --- Atributos de Tiempo y Velocidad ---
        self.tiempo_inicio = 0        # Almacena el timestamp (tiempo exacto) en el que arranca
        self.tiempo_fin = 0           # Almacena el timestamp en el que completa todas sus vueltas
        self.velocidad_actual = random.randint(10, 40) # Asigna un valor de velocidad aleatorio para iniciar
        
        # --- Atributos Gráficos (Objeto Visual) ---
        # Creamos un widget tk.Label que contendrá la imagen renderizada del caballo
        self.label = tk.Label(ventana, image=img_caballo, bg="white")
        # Posicionamos la imagen en las coordenadas iniciales usando el gestor de geometría .place()
        self.label.place(x=self.x, y=self.y_pos)

    def reiniciar(self):
        # Método encargado de devolver al caballo a su estado y posición original para una nueva carrera.
        self.corriendo = False
        self.x = self.x_inicial
        self.direccion = 1
        self.vueltas_completadas = 0
        self.label.place(x=self.x, y=self.y_pos) # Retorna el elemento gráfico a la línea de salida

    def ciclo_movimiento(self, total_vueltas, slider_tiempo, callback_llegada):
        # Este es el bucle principal que ejecutará el hilo secundario asignado a este caballo específico.
        # Funciona de manera independiente al resto del programa para no congelar la interfaz.
        
        while self.corriendo and self.vueltas_completadas < total_vueltas:

            # 1. ACTUALIZAR POSICIÓN FÍSICA
            paso_pixeles = 10 # Cantidad fija de píxeles que avanza en cada ciclo
            self.x += paso_pixeles * self.direccion # Desplaza la posición según la dirección actual

            # 2. DETECCIÓN DE COLISIONES EN LOS BORDES (Rebotes)
            # Verifica si el caballo alcanzó el extremo derecho de la pista (meta de ida)
            if self.x >= 800 and self.direccion == 1:
                self.direccion = -1 # Invierte la dirección para que el caballo retroceda
                self.velocidad_actual = random.randint(10, 40) # Recalcula la velocidad tras el giro
                
            # Verifica si el caballo regresó al extremo izquierdo de la pista (meta de vuelta)
            elif self.x <= 33 and self.direccion == -1:
                self.direccion = 1 # Vuelve a orientarlo hacia adelante
                self.vueltas_completadas += 1 # Registra que se ha completado un ciclo de ida y vuelta
                self.velocidad_actual = random.randint(10, 40) # Recalcula la velocidad para la nueva vuelta

            # 3. DIBUJAR EN PANTALLA MEDIANTE EL HILO PRINCIPAL
            # Tkinter requiere que cualquier actualización visual se haga desde su hilo principal.
            # Usamos after(0, ...) para enviarle la instrucción de redibujar la posición del caballo de forma segura.
            self.ventana.after(0, lambda x_act=self.x: self.label.place(x=x_act, y=self.y_pos))

            # 4. TEMPORIZADOR DEL HILO (Control de velocidad real)
            # Extraemos el valor actual del slider para ajustar la velocidad general de la simulación
            factor_slider = slider_tiempo.get() / 100.0 
            # Calculamos los milisegundos que este hilo específico debe esperar antes del siguiente paso
            tiempo_espera_ms = int(self.velocidad_actual * factor_slider)
            
            # time.sleep pausa únicamente el hilo actual de este caballo, permitiendo 
            # que los demás hilos y la ventana gráfica sigan funcionando sin interrupciones.
            time.sleep(tiempo_espera_ms / 1000.0) # Se divide entre 1000 porque time.sleep requiere segundos

        # 5. CONDICIÓN DE VICTORIA (El bucle ha finalizado)
        # Si el caballo detiene su ciclo por haber completado las vueltas requeridas:
        if self.corriendo: 
            self.corriendo = False # Desactiva el estado de movimiento
            self.tiempo_fin = time.time() # Registra la marca de tiempo exacta de llegada
            
            # Envía la notificación de llegada al hilo principal mediante la función callback
            self.ventana.after(0, lambda: callback_llegada(self))

# ==========================================
# 3. LÓGICA PRINCIPAL DEL JUEGO (Controlador)
# ==========================================
caballos_lista = []  # Lista global que almacena las instancias (objetos) de todos los caballos
orden_llegada = []   # Lista global que registrará el orden secuencial en que los caballos cruzan la meta

def iniciar_carrera():
    global orden_llegada
    
    # Bloqueo de seguridad: Evita iniciar una nueva carrera si ya hay una en curso
    if len(orden_llegada) > 0 and len(orden_llegada) < 10:
        return 
        
    orden_llegada = [] # Vacía el registro de llegadas de carreras anteriores
    vueltas = int(spin_vueltas.get()) # Obtiene la cantidad de rondas definidas por el usuario en la interfaz
    tiempo_arranque = time.time() # Establece el punto de partida temporal (tiempo cero) para la carrera
    
    cuadro_resultados.delete("1.0", tk.END) # Limpia el historial de texto de la tabla de posiciones
    
    hilos_carrera = [] # Lista temporal para agrupar y administrar los hilos de ejecución generados

    # Recorremos la lista de caballos instanciados para encenderlos y asignarles un hilo
    for c in caballos_lista:
        c.tiempo_inicio = tiempo_arranque
        c.corriendo = True
        c.velocidad_actual = random.randint(10, 40)
        
        # Configuración del hilo (Thread) individual para cada caballo:
        # - target: Indica el método que el hilo va a ejecutar de forma aislada.
        # - args: Pasa los argumentos necesarios que requiere el método 'ciclo_movimiento'.
        # - daemon=True: Define el hilo como proceso en segundo plano, asegurando que se cierre al cerrar la ventana.
        hilo = threading.Thread(target=c.ciclo_movimiento, args=(vueltas, slider_velocidad, registrar_llegada), daemon=True)
        hilos_carrera.append(hilo) # Almacenamos la referencia del hilo creado
        hilo.start()               # Iniciamos la ejecución del hilo de manera concurrente

def registrar_llegada(caballo_termino):
    # Función de retorno (Callback) que cada caballo llama al finalizar su ciclo.
    orden_llegada.append(caballo_termino) # Registra al caballo en la lista de llegadas
    
    # Verifica si la lista ya contiene a los 10 competidores, indicando el fin de la carrera
    if len(orden_llegada) == 10:
        mostrar_tabla_y_apuesta() # Desencadena la visualización de resultados

def mostrar_tabla_y_apuesta():
    # Ordena la lista de llegadas basada en el tiempo real que tardó cada caballo.
    # Se calcula restando el tiempo de inicio al tiempo de finalización.
    orden_llegada.sort(key=lambda c: (c.tiempo_fin - c.tiempo_inicio))
    
    cuadro_resultados.insert(tk.END, " POSICIONES FINALES \n\n")
    
    # Itera sobre los caballos ya ordenados para imprimirlos en la caja de texto
    for i, c in enumerate(orden_llegada):
        tiempo_total = c.tiempo_fin - c.tiempo_inicio # Calcula la duración exacta
        # Formatea el texto para mostrar la posición (i+1), el número de caballo y el tiempo en segundos (2 decimales)
        cuadro_resultados.insert(tk.END, f"{i+1}º - Caballo {c.id_caballo} ({tiempo_total:.2f} seg)\n")
    
    # Lógica de validación de apuestas
    caballo_ganador = orden_llegada[0].id_caballo # Extrae el ID del caballo en la primera posición [0]
    mi_apuesta = int(spin_apuesta.get())          # Lee el valor apostado en el panel de control
    
    # Compara la apuesta con el ganador y muestra una alerta emergente (messagebox) con el resultado
    if mi_apuesta == caballo_ganador:
        messagebox.showinfo("¡Felicidades!", f"¡El caballo {caballo_ganador} ganó!\nTu apuesta fue correcta.")
    else:
        messagebox.showinfo("Fin de la carrera", f"Ganó el caballo {caballo_ganador}.\nSuerte en la próxima.")

def reiniciar_carrera():
    # Restablece todas las variables y posiciones visuales a sus valores por defecto
    global orden_llegada
    orden_llegada = []
    cuadro_resultados.delete("1.0", tk.END) # Borra los datos del cuadro de texto
    
    # Ejecuta el método de reinicio interno de cada objeto caballo
    for c in caballos_lista:
        c.reiniciar()

# ==========================================
# 4. CONFIGURACIÓN DE LA INTERFAZ GRÁFICA (Tkinter GUI)
# ==========================================
ventana = tk.Tk()
ventana.title("Simulador de Carrera - Múltiples Hilos")
ventana.geometry("1150x644") # Dimensiones ajustadas para alojar la pista y el panel lateral

# Bloque de captura de errores para la carga de imágenes requeridas
try:
    imagenPista = tk.PhotoImage(file="Camino.png") # Carga el fondo de la pista
    pista = tk.Label(ventana, image=imagenPista)
    pista.place(x=0, y=0)
    imagencaballo = tk.PhotoImage(file="Caballo.png") # Carga el sprite o imagen del caballo
except:
    print("Advertencia: Asegúrate de tener 'Camino.png' y 'Caballo.png' en la misma ruta del script.")
    imagencaballo = None

# Definición de las coordenadas 'Y' fijas para delimitar cada uno de los 10 carriles en pantalla
y_posiciones = [0, 64, 128, 192, 256, 320, 384, 448, 512, 576] 

# Bucle generador de los 10 objetos Caballo
for i in range(10):
    nuevo_caballo = Caballo(id_caballo=i, y_pos=y_posiciones[i], ventana=ventana, img_caballo=imagencaballo)
    caballos_lista.append(nuevo_caballo) # Los almacena en la lista global para poder iterarlos más adelante

# --- SECCIÓN DERECHA: PANEL DE CONTROLES ---
# Crea un marco o sub-ventana lateral para agrupar todas las opciones de interacción del usuario
panel_controles = tk.Frame(ventana, width=250, bg="lightgray")
panel_controles.place(x=900, y=0, height=644, width=250)

# Encabezado del panel
tk.Label(panel_controles, text="--- PANEL DE CONTROL ---", bg="lightgray", font=("Arial", 10, "bold")).pack(pady=10)

# Widget Spinbox para definir la apuesta (limita los valores entre 0 y 9)
tk.Label(panel_controles, text="Caballo al que apuestas desde 0 - 9:", bg="lightgray").pack(pady=5)
spin_apuesta = tk.Spinbox(panel_controles, from_=0, to=9, width=10)
spin_apuesta.pack()

# Widget Spinbox para definir la cantidad de vueltas que dura la simulación
tk.Label(panel_controles, text="# de idas y vueltas (Rondas):", bg="lightgray").pack(pady=5)
spin_vueltas = tk.Spinbox(panel_controles, from_=1, to=10, width=10)
spin_vueltas.pack()

# Widget Scale (Slider horizontal) que actúa como multiplicador para la velocidad global
tk.Label(panel_controles, text="Modificador del Tiempo general:\n(Menos % = Más veloz)", bg="lightgray").pack(pady=10)
slider_velocidad = tk.Scale(panel_controles, from_=10, to=200, orient="horizontal", bg="lightgray", length=150)
slider_velocidad.set(100) # Establece el parámetro central por defecto (100%)
slider_velocidad.pack()

# Botones de control con vinculación a las funciones de lógica principal mediante el parámetro 'command'
btn_iniciar = tk.Button(panel_controles, text="INICIAR CARERA", bg="lightgreen", command=iniciar_carrera)
btn_iniciar.pack(pady=15, fill="x", padx=20)

btn_reiniciar = tk.Button(panel_controles, text="REINICIAR TABLERO", bg="lightcoral", command=reiniciar_carrera)
btn_reiniciar.pack(pady=5, fill="x", padx=20)

# Cuadro de texto multilínea (Text) para registrar y mostrar la tabla de posiciones final de los competidores
tk.Label(panel_controles, text="Tabla de Poiciones:", bg="lightgray").pack(pady=10)
cuadro_resultados = tk.Text(panel_controles, width=25, height=12)
cuadro_resultados.pack(padx=10)

# ==========================================
# 5. BUCLE DE EJECUCIÓN (Mainloop)
# ==========================================
# Inicia el bucle infinito de Tkinter que mantiene la ventana abierta y escucha los eventos del usuario
ventana.mainloop()