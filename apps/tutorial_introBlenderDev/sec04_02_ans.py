from bpn_init import * #pylint: disable=wildcard-import, unused-wildcard-import

env.reset()

Props = env.Props

# Instantiating a class using parenthesis
print(Props())

# Calling an object. Intro do Python magic methods.
print(Props()())

# More magic methods. 
a = Props()
new.cube()
b = Props()
print((b-a)())

# a | b - union
# a & b - intersection
# a - b
# a ^ b
