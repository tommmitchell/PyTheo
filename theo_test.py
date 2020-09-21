
import numpy as np
import importlib as il   # later, reload with :   il.reload(rd)
import theo as t
#from theo import *
# import pdb  # python debugger

#t.loadKB('TheoBareKB.hft')

# BASIC ADDVALUE, DELETEVALUE FUNCTIONS:
t.ce('person',['entity'])
t.ce('male',['person'])
t.ce('female',['person'])
t.ce('musician',['person'])
t.ce('tom',['male'])
t.av('tom','generalizations','musician')
t.ce('joan',['female','musician'])
t.ce('spouse',['slot'])
t.av('spouse','inverse','spouse')
t.av('tom','spouse','joan')
t.av(['tom','spouse','joan'],'probability',1.0)   # we can assert belieffs about beliefs
t.av([['tom','spouse','joan'],'probability',1.0],'source','tom')  # nested as deeply as we like

t.dv('tom','spouse','joan')  # if we delete a slot value then meta-assertions, like the above two, will be deleted too
t.av(['tom','spouse'],'canBeAutomaticallyInfered',False)  # and we can assert values about queries as well as beliefs

# ANY STRING CAN BE USED AS A SLOT NAME
# note we can add slot values without creating an entity to define them, eg., plays
# we usually create explicit entities to define slots only if we want to assert information about the slot (e.g., it's inverse, availableMethods)
t.av('tom','plays','poker')
t.pre('tom')  # print the entity tom, to see the slot value has been added

# AUTOMATICALLY MAINTAINING (ADDING AND DELETING) INVERSES OF VALUES
# we can define slots, to get more support, if we like, e.g., define child, parent as inverses
t.ce('hasChild',['slot'])
t.ce('hasParent',['slot'])
t.av('hasChild','inverse','hasParent')
# now if we assert (tom,child,meghan), and meghan is an entity in the kb, then Theo will assert (meghan parent tom)
t.ce('meghan',['female'])
t.av('tom','hasChild','meghan')
t.pre('meghan')  # as this shows, Theo also stored the assertion (meghan hasParent tom)
# Theo also deletes these inverses automatically if appropriate
t.dv('tom','hasChild','meghan')  # note this also deletes (meghan hasParent tom)
# a slot can also be its own inverse (if the relation it defines is symmetric) like 'hasSpouse'
t.ce('hasSpouse',['slot'])
t.av('hasSpouse','inverse','hasSpouse')
t.av('tom','hasSpouse','joan')
t.pre('joan')  # note Theo asserted also that (joan hasSpouse tom)

# each entity is stored in a Python dictionary called KB, indexed by its string name, the entity is also a dictionary
t.KB['tom']
t.dv('tom','generalizations','musician')
t.KB['tom']

# print the generalization hierarchy below any entity of interest
t.printHierarchy('anything')
t.prh('person')
# print every entity in the KB:
for e in t.KB.keys():
    t.printEntity(e)


# ASSERTING BELIEFS ABOUT BELIEFS, AND ABOUT QUERIES


# SAVING AND RELOADING THE KB:
t.saveKB('test')  # save the entire KB into a .pkl file, test.pkl
t.loadKB('test.pkl')  # load that kb file
# you can also load files written by  hand in .hft (Human-Friendly Theo) format
t.loadKB('TheoBareKB.hft') # this loads the Theo initial KB.  Take a look at it in the editor for instructions on how to easily write a .hft KB file





