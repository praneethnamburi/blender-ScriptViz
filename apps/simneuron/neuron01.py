"""
NEURON tutorial code. To check if it is working in this environment.
"""

from bpn_init import * #pylint: disable=wildcard-import, unused-wildcard-import

sys.path.append('c:\\nrn\\lib\\python')
from neuron import h

env.reset()

h.load_file('stdrun.hoc')
soma = h.Section(name='soma')
soma.insert('pas')
mech = soma(0.5).pas
asyn = h.AlphaSynapse(soma(0.5))
asyn.onset = 20
asyn.gmax = 1
v_vec = h.Vector()
t_vec = h.Vector()
v_vec.record(soma(0.5)._ref_v)
t_vec.record(h._ref_t)
h.tstop = 40.0
h.run()

plt = new.mesh(name='neuronSim', x=np.array(t_vec)/10, z=(np.array(v_vec)+70)/10, y=np.zeros_like(np.array(t_vec)))
