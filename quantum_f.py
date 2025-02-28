import qiskit
import math, cmath
from termcolor import colored

def or_gate (qc, input_qbits, output_qbit):
    qc.x(input_qbits)
    qc.x(output_qbit)
    qc.mcx(input_qbits, output_qbit)
    qc.x(input_qbits)

def nor_gate (qc, input_qbits, output_qbit):
    or_gate (qc, input_qbits, output_qbit)
    qc.x(output_qbit)

def and_gate (qc, input_qbits, output_qbit):
    qc.mcx(input_qbits, output_qbit)

def nand_gate (qc, input_qbits, output_qbit):
    and_gate (qc, input_qbits, output_qbit)
    qc.x(output_qbit)

def phase_and (qc, input_qbits):
    g = qiskit.circuit.library.ZGate()
    g = g.control(len(input_qbits)-1)
    qc.append(g,input_qbits)


def add_diffuser(qc, q_registers): # lo he probado con solo un valor para *q_registers
    for i in q_registers:
        qc.h(i)
        qc.x(i)
    phase_and(qc, q_registers) # multi-control-Z
    for i in q_registers:
        qc.x(i)
        qc.h(i)
    return qc

    
def simulate_qc(qc, n_qubits, n_shots=1024, plot_histogram=True) -> list:
    ''' Simulates the QuantumCircuit "qc", plots the histogram and return the results of the simulation 
    '''
    simulator_backend = qiskit.providers.fake_provider.GenericBackendV2(num_qubits=n_qubits)
    circuit_to_instruction = qiskit.compiler.transpile(qc, backend=simulator_backend)
    job = simulator_backend.run(qc, shots = n_shots)
    result = job.result()
    counts = result.get_counts(qc)
    if plot_histogram: qiskit.visualization.plot_histogram(counts)
    return counts

def flatten_list (list_of_lists):
    flat_list = []
    for l in list_of_lists:
        flat_list.extend(l)
    return flat_list


def print_state (statevector, num_cols=0, print_only_z=True, print_0_prob=False):
    ''' Prints the statevector (calculated as 'qiskit.quantum_info.Statevector(qc)' ) showing the kets and their probabilities
        The user can select whether states with 0 probability are to be shown and the number of columns to organize the output
        Numbers in blue have phase 0 and in yellow phase PI
    '''
    num_cols=statevector.num_qubits/2 if num_cols==0 else num_cols
    for pos, val in enumerate(statevector.data):
        prob=abs(val)**2
        phase=cmath.phase(val)
        txt=f"|{pos:0{statevector.num_qubits}b}\u232A: {prob*100:.3f}%"
        fin = '\n' if (pos+1)%num_cols==0 else '\t'
        if math.isclose(prob,0,abs_tol=1e-6): 
            if print_0_prob: 
                print(colored(txt, 'white'), end=fin)
        elif math.isclose(phase, 0, abs_tol=1e-6) and not print_only_z:
            print(colored(txt, 'blue',attrs=["bold"]), end=fin)
        elif math.isclose(phase,math.pi,abs_tol=1e-6) or math.isclose(phase,-math.pi,abs_tol=1e-6):
            print(colored(txt, 'yellow', attrs=["bold"]), end=fin)
        elif not print_only_z:
            print(colored(txt+f"({phase})", 'red', attrs=["bold"]), end=fin)


def get_rotated_combinations (statevector):
    lista=[]
    for pos, val in enumerate(statevector.data):
        prob=abs(val)**2
        phase=cmath.phase(val)
        if math.isclose(phase,math.pi,abs_tol=1e-6) or math.isclose(phase,-math.pi,abs_tol=1e-6):
            #lista.append(f"|{pos:0{statevector.num_qubits}b}\u232A: {prob:.3f}")
            lista.append([pos, prob])
    return lista


# retorna una pareja de valores
def max_prob_combinations(statevector):
    probabilidades = statevector.probabilities_dict()
    # Encontrar el valor máximo de probabilidad
    max_probabilidad = max(probabilidades.values())
    # Encontrar las combinaciones binarias que tienen el valor máximo de probabilidad
    combinaciones_max_prob = [estado for estado, prob in probabilidades.items() if math.isclose(prob,max_probabilidad,abs_tol=1e-6)  ]
    return max_probabilidad, combinaciones_max_prob