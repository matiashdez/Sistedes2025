import qiskit
import math
import numpy as np
from qiskit.quantum_info import Statevector
import cmath
import math
from termcolor import colored
import random
from time import perf_counter
from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.visualization import plot_histogram
from qiskit_ibm_provider import IBMProvider
from qiskit.circuit.library import QFT
from colorama import Fore, Style

def get_extended_edges(nodes, edges):
    def get_neighbors(nodes, edges):
        neighbors = [[] for _ in range(nodes)]
        for edge in edges:
            node1, node2 = edge
            neighbors[node1].append(node2)
            neighbors[node2].append(node1)  
        return neighbors
    
    neighborsList = get_neighbors(nodes, edges)

    def convert_list(listed):
        result = []
        for i in range(len(listed)):
            neighbors = []
            for eachNeighbor in listed[i]:
                neighbors.extend(listed[eachNeighbor])
            neighbors = list(set(neighbors) - set([i]))
            result.append(neighbors)
        return result

    neighborsFromNeighbors = convert_list(neighborsList)

    def add_links(adjacencyList, linksList):
        transformedList = convert_list(adjacencyList)
        for node, neighbors in enumerate(transformedList):
            for eachNeighbor in neighbors:
                if (node, eachNeighbor) not in linksList and (eachNeighbor, node) not in linksList:
                    linksList.append((node, eachNeighbor))
        return linksList

    return add_links(neighborsList, edges)



def oracle_creator_Grover(nodes, edges, chromaticSpace, use_extendedEdges = False):

    if use_extendedEdges:
        extendedEdges = get_extended_edges(nodes, edges)
    else:
        extendedEdges = edges

    
    totalCircuitLength = (nodes * chromaticSpace) + nodes + (len(extendedEdges) * chromaticSpace) + 1
    numberOfEdges = len(extendedEdges)

    qubits = []
    start = 0
    for _ in range(nodes):
        end = start + chromaticSpace
        qubits.append(tuple(range(start, end)))  
        start = end

    def create_initial_quantum_circuit(numberOfEdges, chromaticSpace, nodes):
        initialQuantumCircuit = QuantumCircuit((nodes * chromaticSpace) + nodes + (numberOfEdges * chromaticSpace) + 1)
        return initialQuantumCircuit  

    initialCircuit = create_initial_quantum_circuit(numberOfEdges, chromaticSpace, nodes)

    # Add first color constraint
    ancillaPositions = []
    def generate_full_qubit_list(qubits):
        qubitsList = []
        for qubitSet in qubits:
            qubitList = list(qubitSet)
            qubitsList.append(qubitList)
        return qubitsList
    
    qubitsList = generate_full_qubit_list(qubits)
    ancillaQubitIndex = nodes * chromaticSpace

    for qubitGroup in qubitsList:
        for eachQubit in qubitGroup:
            initialCircuit.x(eachQubit)
        initialCircuit.mcx(list(qubitGroup), ancillaQubitIndex)  
        ancillaPositions.append(ancillaQubitIndex)
        for eachQubit in qubitGroup:
            initialCircuit.x(eachQubit)
        initialCircuit.x(ancillaQubitIndex)
        ancillaQubitIndex += 1

    # Add second color constraint  
    expandedEdges = []
    for eachEdge in extendedEdges:
        for i in range(chromaticSpace):
            expandedEdges.append((eachEdge[0] * chromaticSpace + i, eachEdge[1] * chromaticSpace + i))

    for eachExpandedEdge in expandedEdges:
        initialCircuit.ccx(eachExpandedEdge[0], eachExpandedEdge[1], ancillaQubitIndex)
        ancillaPositions.append(ancillaQubitIndex)
        initialCircuit.x(ancillaQubitIndex)
        ancillaQubitIndex += 1

    def create_middle_circuit(initialCircuit, ancillaPositions, ancillaQubitIndex):
        quantumSupportCircuit = QuantumCircuit(totalCircuitLength)
        quantumSupportCircuit.mcx(ancillaPositions, ancillaQubitIndex)
        return quantumSupportCircuit
    
    middleCircuit = create_middle_circuit(initialCircuit, ancillaPositions, ancillaQubitIndex)


    reversedCircuit = initialCircuit.reverse_ops()

    firstCircuitCombination = middleCircuit.compose(initialCircuit, range(0, totalCircuitLength), front=True)
    oracleCircuit = reversedCircuit.compose(firstCircuitCombination, range(0, totalCircuitLength), front=True)

    def create_diffuser(n):
        diffuser = QuantumCircuit(n)
        
        for qubit in range(n):
            diffuser.h(qubit)
        
        for qubit in range(n):
            diffuser.x(qubit)
        
        diffuser.h(n-1)
        diffuser.mcx(list(range(n-1)), n-1)
        diffuser.h(n-1)
        
        for qubit in range(n):
            diffuser.x(qubit)
        
        for qubit in range(n):
            diffuser.h(qubit)
        
        return diffuser
    
    diffuserCircuit = create_diffuser(nodes * chromaticSpace)

    oraclePlusDiffuser = oracleCircuit.compose(diffuserCircuit, range(0, (nodes * chromaticSpace)), front=False)

    return oraclePlusDiffuser



def grover_search(oracle, m, n):
    


    GroverCircuit = QuantumCircuit(oracle.num_qubits, n)
    GroverCircuit.x(-1)
    GroverCircuit.h(-1)

    for qubit in range(n):
        GroverCircuit.h(qubit)
    

    numberOfRepetitions = math.ceil(math.pi/4 * math.sqrt(oracle.num_qubits/m))

    oracle_gate = oracle.to_gate()
    

    for _ in range(numberOfRepetitions):
        GroverCircuit.append(oracle_gate, range(oracle.num_qubits))
     
    GroverCircuit.measure(range(n), range(n))

    return GroverCircuit




def oracle_creator(nodes, edges, chromaticSpace, use_extendedEdges = False):

    if use_extendedEdges:
        extendedEdges = get_extended_edges(nodes, edges)
    else:
        extendedEdges = edges
    
    totalCircuitLength = (nodes * chromaticSpace) + nodes + (len(extendedEdges) * chromaticSpace) + 1
    numberOfEdges = len(extendedEdges)

    qubits = []
    start = 0
    for _ in range(nodes):
        end = start + chromaticSpace
        qubits.append(tuple(range(start, end))) 
        start = end

    def create_initial_quantum_circuit(numberOfEdges, chromaticSpace, nodes):
        initialQuantumCircuit = QuantumCircuit((nodes * chromaticSpace) + nodes + (numberOfEdges * chromaticSpace) + 1, 1)
        return initialQuantumCircuit  

    initialCircuit = create_initial_quantum_circuit(numberOfEdges, chromaticSpace, nodes)
    initialCircuit.barrier()

    ancillaPositions = []
    def generate_full_qubit_list(qubits):
        qubitsList = []
        for qubitSet in qubits:
            qubitList = list(qubitSet)
            qubitsList.append(qubitList)
        return qubitsList
    
    qubitsList = generate_full_qubit_list(qubits)
    ancillaQubitIndex = nodes * chromaticSpace

    for qubitGroup in qubitsList:
        for eachQubit in qubitGroup:
            initialCircuit.x(eachQubit)
        initialCircuit.mcx(qubitGroup, ancillaQubitIndex)
        ancillaPositions.append(ancillaQubitIndex)
        for eachQubit in qubitGroup:
            initialCircuit.x(eachQubit)
        initialCircuit.x(ancillaQubitIndex)
        ancillaQubitIndex += 1
        initialCircuit.barrier()

    expandedEdges = []
    for eachEdge in extendedEdges:
        for i in range(chromaticSpace):
            expandedEdges.append((eachEdge[0] * chromaticSpace + i, eachEdge[1] * chromaticSpace + i))

    for eachExpandedEdge in expandedEdges:
        initialCircuit.ccx(eachExpandedEdge[0], eachExpandedEdge[1], ancillaQubitIndex)
        ancillaPositions.append(ancillaQubitIndex)
        initialCircuit.x(ancillaQubitIndex)
        ancillaQubitIndex += 1
        initialCircuit.barrier()

    def create_middle_circuit(initialCircuit, ancillaPositions, ancillaQubitIndex):
        quantumSupportCircuit = QuantumCircuit(totalCircuitLength)
        quantumSupportCircuit.mcx(ancillaPositions, ancillaQubitIndex)
        quantumSupportCircuit.barrier()
        return quantumSupportCircuit
    
    middleCircuit = create_middle_circuit(initialCircuit, ancillaPositions, ancillaQubitIndex)

    finalCircuitCombination = middleCircuit.compose(initialCircuit, range(0, totalCircuitLength), front=True)
    finalCircuitCombination.z(-1)

    return finalCircuitCombination



def check_solution(colors, color_assignment, oracle):
    circuit = QuantumCircuit(oracle.num_qubits, oracle.num_clbits)  

    
    for node, color in enumerate(color_assignment):
        qubit_index = node * colors + color  
        circuit.x(qubit_index) 
    

    circuit.compose(oracle, inplace=True)

    circuit.measure(oracle.num_qubits - 1, 0)
    
    return circuit



def oracle_creator_CdC_OH(nodes, colors, edges, use_extendedEdges = False):

    degree_count = {i: 0 for i in range(nodes)}

    # Contar los enlaces de cada nodo
    for edge in edges:
        degree_count[edge[0]] += 1
        degree_count[edge[1]] += 1

    # Encontrar el grado máximo
    max_degree = max(degree_count.values())

    if use_extendedEdges:
        extendedEdges = get_extended_edges(nodes, edges)
    else:
        extendedEdges = edges



    circuitLength = (nodes * colors) + max(math.floor(math.log2(nodes)), math.floor(math.log2(max_degree))) + 3
    qcaux = QuantumCircuit(circuitLength, 1)
    qcaux2 = QuantumCircuit(circuitLength, 1)
    qc = QuantumCircuit(circuitLength, 1)

    for qubit in range(nodes * colors):
        qc.h(qubit)

    sum1 = (nodes * colors) 
    sum2 = (nodes * colors) + 1
    sum3 = (nodes * colors) + 2

    control_qubit = (nodes * colors)  
    start_qubit = sum2 + 1 
    last_target_qubits = [] 

    qc.barrier()

    for node in range(nodes):
        node_adjusted = node + 1
        node_qubit = node * colors  
        qc.cx(node_qubit, control_qubit)

        for color in range(1, colors):
            qc.ccx(node_qubit + color, control_qubit, sum2)
            qc.cx(node_qubit + color, control_qubit)

        qc.barrier()

        qc.x(sum2)
    

        level = 0
        current_qubits = [sum1, sum2]
      
        if node_adjusted == 1:
            target_qubit = start_qubit
            qc.ccx(sum1, sum2, target_qubit)
            last_target_qubits = [target_qubit]
          
        else:
      
            while (1 << level) <= node_adjusted:
                if level > 0:
                    current_qubits.append(start_qubit + level - 1)

                target_qubit = start_qubit + level

   
                if len(current_qubits) == 2:
                    qcaux.ccx(current_qubits[0], current_qubits[1], target_qubit)
                else:
                    qcaux.mcx(current_qubits, target_qubit)

                level += 1
            qcaux_inverse = qcaux.inverse()
            qc = qc.compose(qcaux_inverse)
            qcaux.data = []
          

            if node_adjusted == nodes:

                current_qubits = [qubit + 1 for qubit in current_qubits]
                last_target_qubits = current_qubits[-(level):] 

        
        if node_adjusted == nodes:
            
            for i, bit in enumerate(reversed(f"{nodes:b}".zfill(len(last_target_qubits)))):
                if bit == '0':
                    qc.x(last_target_qubits[i])

            

        qc.x(sum2)
        qc.barrier()

        
        for color in range(colors - 1, 0, -1):
            qc.cx(node_qubit + color, control_qubit)
            qc.ccx(node_qubit + color, control_qubit, sum2)

        
        
        qc.cx(node_qubit, control_qubit)
        qc.barrier()

    
    qc.mcx(last_target_qubits, sum1)
    for qubit in range(sum3, circuitLength):
        qc.x(qubit)

    
    
    
    qc.barrier()
    primera_comparacion = True  


    # Segunda condición
    for edge in extendedEdges:
        node_a, node_b = edge
        for color in range(colors):
            node_a_qubit = node_a * colors + color
            node_b_qubit = node_b * colors + color
            current_qubits = [node_a_qubit, node_b_qubit, sum2]

            # Evitar duplicados en current_qubits
            current_qubits = list(set(current_qubits))

            if primera_comparacion:
                qc.ccx(node_a_qubit, node_b_qubit, sum2)
                primera_comparacion = False
            else:
                # Número de qubits necesarios para la puerta mcx según el max_degree
                num_qubits = math.ceil(math.log2(max_degree + 2))  # +1 para ajustarse correctamente
                levels_qubits = []

                for level in range(num_qubits):
                    target_qubit = start_qubit + level

                    # Evitar duplicados en niveles
                    levels_qubits = list(set(levels_qubits))
                    
                    control_qubits = list(range(sum2+1, target_qubit))

                    if level == 0:
                        qcaux2.mcx(current_qubits, target_qubit)
                    else:

                        qcaux2.mcx(current_qubits + levels_qubits + control_qubits, target_qubit)
                        
                
                qcaux2_inverse = qcaux2.inverse()
                qc = qc.compose(qcaux2_inverse)
                qc.ccx(node_a_qubit, node_b_qubit, sum2)
                qcaux2.data = []
                levels_qubits.append(target_qubit)

            qc.barrier()
            

    for qubit in range(sum2, target_qubit+1):
        qc.x(qubit)
    qc.mcp(math.pi, list(range(sum1, (target_qubit))),  target_qubit)
    
    
    

    
    

    return qc



def print_state(statevector, num_cols=0, print_0_prob=False, precision=6):
    ''' Prints the statevector (calculated as 'qiskit.quantum_info.Statevector(qc)' ) showing the kets and their probabilities
        The user can select whether states with 0 probability are to be shown, the number of columns to organize the output,
        and the number of decimal places for the probabilities.
        Numbers in blue have phase 0 and in yellow phase PI.
    '''
    num_cols = statevector.num_qubits // 2 if num_cols == 0 else num_cols
    for pos, val in enumerate(statevector.data):
        prob = abs(val) ** 2
        phase = cmath.phase(val)
        txt = f"|{pos:0{statevector.num_qubits}b}\u232A: {prob:.{precision}f}"  
        fin = '\n' if (pos + 1) % num_cols == 0 else '\t'
        if math.isclose(prob, 0, abs_tol=1e-6):
            if print_0_prob:
                print(colored(txt, 'white'), end=fin)
        elif math.isclose(phase, 0, abs_tol=1e-6):
            print(colored(txt, 'blue', attrs=["bold"]), end=fin)
        elif math.isclose(phase, math.pi, abs_tol=1e-6) or math.isclose(phase, -math.pi, abs_tol=1e-6):
            print(colored(txt, 'yellow', attrs=["bold"]), end=fin)
        else:
            print(colored(txt + f"({phase})", 'red', attrs=["bold"]), end=fin)


