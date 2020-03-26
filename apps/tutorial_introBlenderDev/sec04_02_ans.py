import bpn # pylint: disable=unused-import
from bpn import Props

bpy = bpn.bpy
bpn.env.reset()

# Instantiating a class using parenthesis
print(Props())

# Calling an object. Intro do Python magic methods.
print(Props()())

# More magic methods. 
a = Props()
bpn.new.cube()
b = Props()
print((b-a)())

# a | b - union
# a & b - intersection
# a - b
# a ^ b
