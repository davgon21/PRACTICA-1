from multiprocessing import Process
from multiprocessing import BoundedSemaphore, Semaphore, Lock
from multiprocessing import current_process
from multiprocessing import Value, Array, Manager
from time import sleep
import random


N = 10 # Es el número de elementos que genera el productor
NPROD = 5 # Número de productores
NCONS = 1 # Número de consumidores


#Creamos una función para generar un tiempo de espera aleatorio
def delay(factor = 3):
    sleep(0.1)

#Creamos una función que añada los elementos que producen los productores al buffer compartido
def add_data(Buffer, ultimos_vals):
         pos= int(current_process().name.split('_')[1]) #preguntamos por el nombre del proceso actual
         nuevo_dato = ultimos_vals[pos] + random.randint(1,10)
         Buffer[pos] = nuevo_dato #añadimos en la posición correspondiente del buffer un elemento aleatorio entre 1 y 5
         ultimos_vals[pos] = Buffer[pos] #Actualizamos la lista de los últimos elementos producidos 
         delay(6)
         
         
def get_data(Buffer):
        pos_consumed = 0
        val_positivos = [x for x in Buffer if x >= 0] # nos quedamos únicamente con los valores positivos de los elementos del buffer
        for y in range(len(Buffer)):  
             if Buffer[y] == min(val_positivos): #de los elementos producidos por los consumidores, nos quedamos con el más pequeño
                  pos_consumed = y
                  menor = [pos_consumed, min(val_positivos)]
                  print(f"Cogemos {min(val_positivos)} del productor {pos_consumed}")
                  break
        delay()
        return menor
       
       
def quedan_productores(Buffer): # tenemos que comprobar si en cada casilla del buffer aparece un -1
    for i in range(NPROD):
        if Buffer[i] != -1 :
        	return True

    return False # si se llega a este caso se acaba    
       

def producer(Buffer, empty, non_empty, ultimos_vals):
    pos= int(current_process().name.split('_')[1])
    for v in range(N):
        print (f"productor {current_process().name} produciendo")
        delay(6)
        empty.acquire()
        add_data(Buffer, ultimos_vals)
        non_empty.release()
        print (f"productor {current_process().name} almacenado {v}")
    empty.acquire()
    Buffer[pos] = -1
    print(f"El Buffer actual es {Buffer[:]}")
    print (f"productor {current_process().name} almacenado {-1}")  
    non_empty.release()     
       

def consumer(Buffer, empty, non_empty, vals_consumidos, ultimos_vals):
       for v in range(NPROD):
           non_empty[v].acquire()
       a = quedan_productores(Buffer)
       print(f"{a}")
       while a:
           print (f"{current_process().name} consumiendo")
           [ind,min_val] = get_data(Buffer)
           vals_consumidos.append(min_val)
           Buffer[ind] = -2
           empty[ind].release()
           print (f"{current_process().name} consumiendo {min_val} del productor {ind}")
           non_empty[ind].acquire()
           delay()
           a = quedan_productores(Buffer)
       print(f"Los valores consumidos son {vals_consumidos}")
   
def main():
    Buffer = Array('i', NPROD) #Array con los mismos elementos que el nÃºmero de productores.#
    for i in range(NPROD):#Empieza con -2s.#
        Buffer[i] = -2
    print ("almacen inicial", Buffer[:])
    # Inicializamos las variables compartidas entre los productores y el consumidor

    manager = Manager()
    vals_consumidos = manager.list()
    ultimos_vals = Array('i', NPROD)
    # Tenemos para cada productor un semáforo general, un semáforo acotado y un mutex
    # non_empty: semáforo que avisa al consumidor que hay un elemento disponible
    # empty: semáforo que avisa al productor de que ya puede almacenar un nuevo elemento

   
    non_empty = [Semaphore(0) for _ in range(NPROD)]
    empty = [Lock() for _ in range(NPROD)]

    productores = [Process(target=producer, name=f'prod_{i}', args=(Buffer, empty[i], non_empty[i],ultimos_vals))   
                   for i in range(NPROD) ]

    consumidor = Process(target=consumer,
                        name=f'consumidor',
                        args=(Buffer, empty, non_empty,vals_consumidos,ultimos_vals))

    for p in productores :
        print(f"arrancando productor {p.name}")
        p.start()
    print(f"arrancando {consumidor.name}")
    consumidor.start()
   
    for p in productores :
        p.join()
    consumidor.join()


if __name__ == '__main__':
    main()
