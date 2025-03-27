import quantum_f

class C_Ladder_Counter:
    """ 
    Esta clase facilita la creación, paso a paso, de contadores cuánticos optimizados 
    (es decir, que utilizan el mínimo número de qbits en cada 'paso' para llevar la cuenta) para contar los valores 
    de uno o varios QuantumRegister en escalera. En el artículo de las JISBD 2025, se corresponden con el primer 
    contador de la primera condición y el contador de la segunda condición. 
        
    En el constructor se le pasa una matriz con los registros que actúan como 'triggers' del contador de forma 
    escalonada, una lista flat de qbits que almacenan el valor del contador, el circuito cuántico en el que se 
    quieren generar (no se añade inplace, sino que se genera una copia vacía de la estructura de qbits del mismo 
    y se retorna únicamente la estructura del contador, para que el usuario decida qué hacer con ella) 
    y, opcionalmente, el valor por el comenzar la cuenta del contador (necesario para implementar el contador 
    de la segunda condición del artículo; el método 'get_count_value()' retorna el valor por el que se quedó 
    un contador, que se puede utilizar como parámetro del siguiente). El primer parámetro debe ser una lista, 
    donde cada elemento tiene a su vez que ser o bien un QuantumRegister, o bien una lista de Qubits. Un par 
    de ejemplos de creación de contadores son:
        cnt_qregister  = C_Ladder_Counter ([nodo0], ancillas[:3], qc) # cada uno de los qbits del registro 'nodo0' va a ser un trigger y la cuenta se almacena en los primeros 3 qbits del registro 'ancillas'. Observa que el primer parámetro es una lista (de un elemento solo, pero una lista)
        cnt_qregisters = C_Ladder_Counter ([nodo0, nodo1], ancillas[:3], qc) # los triggers ahora son, en secuencia, cada uno de los qbits de los registros 'nodo0' y 'nodo1'

    Una vez creado el contador, se invoca el método 'next()' para que te retorne el siguiente trozo de contador, que incluye siempre todos los triggers. El siguiente código muestra cómo añadir directamente el trozo de contador generado al circuito. Por último, el trozo de contador generado por 'next()' satura cuando, o bien ya no hay más qbits disponibles en el contador (segundo parámetro del constructor), o bien ya se han recorrido todos los triggers (primer parámetro del constructor). A partir de este momento, retorna el circuito vacío. El método 'is_exhausted()' se puede utilizar para detectar esta condición, que se puede utilizar en un 'while'.
    >>> circuito.compose(cnt_qregisters.next(), inplace=True)
    """

    def __init__(self, matrix_trigger_qbits, counter_qbits, qc, init_value=0):
        self.__current_pos=1
        self.__next_jump=1
        self.__n_ccx=1
        self.__triggers=matrix_trigger_qbits
        self.__counters=counter_qbits
        self.__is_exhausted = False # have all counter_qbits been generated for this counter?
        self.__n_available_cnt=2**len(counter_qbits)
        self.__column=0
        self.__qc=qc.copy_empty_like()
        if init_value!=0 :
            for _ in range(init_value):
                self.__incr()

    def next(self):
        tmp=self.__qc.copy_empty_like()
        if self.__is_exhausted : 
            return tmp
        list_controls=[]
        for j in range(len(self.__triggers)):
            list_controls.append(self.__triggers[j][self.__column])
        for i in range(self.__n_ccx, 0, -1) :
            tmp.mcx(control_qubits=list_controls+self.__counters[:i-1], target_qubit=self.__counters[i-1])
        self.__column+=1
        self.__incr()
        return tmp

    def __incr(self):
        self.__n_available_cnt-=1
        if self.__current_pos == self.__next_jump :
            self.__current_pos = 1
            self.__next_jump *= 2
            self.__n_ccx += 1
        else :
            self.__current_pos += 1
        if self.__n_available_cnt==1 or self.__column==len(self.__triggers[0]):
            self.__is_exhausted = True
    
    def is_exhausted (self):
        return self.__is_exhausted
    
    def get_count_value(self):
        return 2**len(self.__counters) - self.__n_available_cnt



class C_Counter:
    """ 
    Esta clase facilita la creación, paso a paso, de contadores cuánticos optimizados (es decir, que utilizan el mínimo número de qbits en cada 'paso' para llevar la cuenta) que siempre emplean los mismos qbits como triggers del contador. En el artículo de las JISBD 2025, se corresponden con el contador-de-contadores, o segundo contador, de la primera condición del coloreado de grafos ("cada nodo tiene asignado al menos 1 color").
    
    En el constructor se le pasa un lista flat de qbits que actúan como 'triggers' del contador, una lista flat de qbits que almacenan el valor del contador, y el circuito cuántico en el que se quieren generar (no se añade inplace, sino que se genera una copia vacía de la estructura de qbits del mismo y se retorna únicamente la estructura del contador, para que el usuario decida qué hacer con ella). Un par de ejemplos de creación de contadores son:
        cnt_qregister  = C_Counter (nodo0, ancillas[:3], qc) # los qbits del registro 'nodo0' son los triggers y la cuenta se almacena en los primeros 3 qbits del registro 'ancillas'
        cnt_qregisters = C_Counter (quantum_f.flatten_list([nodo0, nodo1]), ancillas[:3], qc) # los triggers son los registros 'nodo0' y 'nodo1'

    Una vez creado el contador, se invoca el método 'next()' para que te retorne el siguiente trozo de contador, que incluye siempre todos los triggers. El siguiente código muestra cómo añadir directamente el trozo de contador generado al circuito. Por último, el trozo de contador generado por 'next()' satura cuando ya no hay más qbits disponibles en el contador (segundo parámetro del constructor) y, a partir de este momento, retorna siempre el mismo trozo de circuito. El método 'is_exhausted()' se puede utilizar para detectar esta condición, que se puede utilizar en un 'while'.
    >>> circuito.compose(cnt_qregisters.next(), inplace=True)
    """

    def __init__(self, trigger_qbits, counter_qbits, qc):
        self.__current_pos=1
        self.__next_jump=1
        self.__n_ccx=1
        self.__triggers=trigger_qbits
        self.__counters=counter_qbits
        self.__is_exhausted = False # have all counter_qbits been generated for this counter?
        self.__n_available_cnt=2**len(counter_qbits)
        self.__exhausted_qc=0
        self.__qc=qc.copy_empty_like()

    def next(self):
        if self.__is_exhausted : 
            return self.__exhausted_qc
        tmp=self.__qc.copy_empty_like()
        for i in range(self.__n_ccx, 0, -1) :
            list_controls=quantum_f.flatten_list([self.__triggers, self.__counters[:i-1]])
            tmp.mcx(control_qubits=list_controls, target_qubit=self.__counters[i-1])
        self.__n_available_cnt-=1
        if self.__current_pos == self.__next_jump :
            self.__current_pos = 1
            self.__next_jump *= 2
            self.__n_ccx += 1
        else :
            self.__current_pos += 1
        if self.__n_available_cnt==1 :
            self.__is_exhausted = True
            self.__exhausted_qc = tmp
        return tmp
    
    def is_exhausted (self):
        return self.__is_exhausted
    