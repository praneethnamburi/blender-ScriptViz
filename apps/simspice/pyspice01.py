import PySpice.Logging.Logging as Logging
logger = Logging.setup_logging()


from PySpice.Spice.Netlist import Circuit, SubCircuit, SubCircuitFactory
from PySpice.Unit import *

class ParallelResistor(SubCircuitFactory):
    __name__ = 'parallel_resistor'
    __nodes__ = ('n1', 'n2')
    def __init__(self, R1=1@u_Ω, R2=2@u_Ω):
        super().__init__()
        self.R(1, 'n1', 'n2', R1)
        self.R(2, 'n1', 'n2', R2)

circuit = Circuit('Test')

circuit.subcircuit(ParallelResistor(R2=3@u_Ω))
circuit.X('1', 'parallel_resistor', 1, circuit.gnd)

print(circuit)
# simulator = circuit.simulator(temperature=25)
# analysis = simulator.dc()

# print(analysis)
