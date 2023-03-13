from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array, Manager
from time import sleep
import random


N = 20 # Es el número de elementos que genera el productor
NPROD = 5 # Número de productores
NCONS = 1 # Número de consumidores
#tam_buff = 4 #Tamaño del buffer correspondiente a cada productor

#Creamos una función para generar un tiempo de espera aleatorio
def delay(factor = 3):
    sleep(0.05)

#Creamos una función que añada los elementos que producen los productores al buffer compartido
def add_data(Buffer, mutex, ultimos_vals, lista_indices):
     mutex.acquire()
     try:
         pos= int(current_process().name.split('_')[1]) #productor actual
         nuevo_dato = ultimos_vals[pos] + random.randint(1,10) #el productor "pos" produce un elemento y lo acumula en su buffer en la posición correspondiente
         Buffer[lista_indices[pos]] = nuevo_dato #añadimos en la posición correspondiente del buffer un elemento aleatorio entre 1 y 5
 
         lista_indices[pos] += 1
         ultimos_vals[pos] = nuevo_dato #acumulamos el nuevo elemento en la lista de ultimos valores de cada productor
         delay(6)
     finally:
         mutex.release()
         
         
def get_data(Buffer, mutex, lista_indices):
    mutex.acquire()
    try:
        lista_pos = [] #lista de productos mayores que 0
        for prod in range(NPROD):
            for j in range(N):
            	if Buffer[prod][j] >=0:
            		lista_pos += [Buffer[prod][j]]
        pos_consumed = 0
        for y in range(NPROD):
           for k in range(N):
             if Buffer[y][k] == min(lista_pos): #de los elementos producidos por los consumidores, nos quedamos con el más pequeño
                  pos_consumed = y
                  menor = [pos_consumed, min(lista_pos)]
                  print(f"Cogemos {min(lista_pos)} del productor {pos_consumed}")
                  delay(6)
                  return menor
    finally:
        mutex.release()
       
def quedan_productores(Buffer,mutex): # tenemos que comprobar si en cada casilla del buffer aparece un -1
    for i in range(NPROD):
       for j in range(N):
        if Buffer[i][j] != -1 :
        	return True
    return False # si se llega a este caso se acaba    
       

def producer(Buffer, empty, non_empty, mutex, ultimos_vals, lista_indices):
    pos= int(current_process().name.split('_')[1])
    for v in range(N):
        print (f"productor {current_process().name} produciendo")
        delay(6)
        empty.acquire()
        add_data(Buffer, mutex, ultimos_vals, lista_indices)
        non_empty.release()
        #print (f"productor {current_process().name} en la producción {v}")
    empty.acquire()
    for i in range(N):
    	Buffer[i] = -1 # En cuanto haya acabado de producir un productor, se cambia todo su buffer a -1
    print (f"productor {current_process().name} almacenado {-1}, y por tanto ya no produce más")   
    non_empty.release()     
       

def consumer(Buffer, empty, non_empty, mutex, vals_consumidos, ultimos_vals,lista_indices):
       for v in range(NPROD):
           non_empty[v].acquire()
       
       a = quedan_productores(Buffer, mutex)
       while a:
           print (f"{current_process().name} consumiendo")
           [prod,min_val] = get_data(Buffer, mutex, lista_indices)
           
           vals_consumidos.append(min_val)
           for i in range(len(Buffer[prod])-2):
           	Buffer[prod][i] = Buffer[prod][i+1]
           Buffer[prod][len(Buffer[prod])-1] = -2
           lista_indices[prod]-=1
           
           print (f"{current_process().name} consumiendo {min_val} del productor {prod}")
           empty[prod].release()
           non_empty[prod].acquire()
           delay()
           for i in range(NPROD):
           	print(Buffer[i][:])
           a = quedan_productores(Buffer, mutex)
       print(f"La lista de valores consumidos es {vals_consumidos}")
       for i in range(NPROD):
       		print(f"El buffer final del productor {i} es {Buffer[i][:]}")
   
def main():
    Buffers = [Array('i',N) for _ in range(NPROD)] #Lista de arrays para cada productor
    for i in range(NPROD):#Empieza con -2s
        for j in range(N):
           Buffers[i][j] = -2
    
    # Inicializamos las variables compartidas entre los productores y el consumidor
    
    #Usaré una lista de indices pq al tener un tamano fijo para el storage de cada productor
    #necesitare saber a que indice le corresponde introducir a cada productor
    lista_indices = Array('i', NPROD)
    for i in range(NPROD):
    	lista_indices[i] = 0
    
    manager = Manager()
    vals_consumidos = manager.list()
    ultimos_vals = Array('i', NPROD)
    # Tenemos para cada productor un semáforo general, un semáforo acotado y un mutex
    # non_empty: semáforo que avisa al consumidor que hay un elemento disponible
    # empty: semáforo de tamaño K que avisa al productor de que ya puede almacenar un nuevo elemento
    # mutex: protege la variable compartida Buffer
   
    non_empty = [Semaphore(0) for _ in range(NPROD)]
    empty = [Semaphore(N) for _ in range(NPROD)]
    mutex = Lock()

    productores = [Process(target=producer, name=f'prod_{i}', args=(Buffers[i], empty[i], non_empty[i], mutex,ultimos_vals, lista_indices))   
                   for i in range(NPROD) ]

    consumidor = Process(target=consumer,
                        name=f'consumidor',
                        args=(Buffers, empty, non_empty, mutex, vals_consumidos,ultimos_vals, lista_indices))

    for p in productores :
        print(f"comenzando productor {p.name}")
        p.start()
    print(f"comenzando {consumidor.name}")
    consumidor.start()
   
    for p in productores  :
        p.join()
    consumidor.join()
    


if __name__ == '__main__':
    main()
