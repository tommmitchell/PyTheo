import numpy as np
import pdb  # python debugger
from theomethods import *
import tomutils as tu
global KB
global THEOtraceGetValues0
global THEOmaintainInverses
THEOtraceGetValues0=False
THEOmaintainInverses=True

"""
This is a barebones implementation of Theo in Python.
Each entity is represented by a Python dictionary, with slots and their values stored as key:value pairs.

The entire KB is also a dictionary, with entity names as keys, whose values are dictionaries.
In the future, might consider making each entity simply a global variable in the theo namespace...  or as is a string, or both
But probably won't need to.  Seems dictionaries are optimized to use hash tables, an namespaces implemented by dictionaries...

Global variables:
- KB: the knowledge base
- THEOtraceGetValues0=False   if set to True, display will show all calls to getValues0
- THEOmaintainInverses=True   if set to True, addValue(e,s,v) and deleteValue(e,s,v) assert and delete inverse triples

Created 7/21/2020,  tommmitchell@gmail.com

Status: as of 7/24, this works.  
        todo: extend loadKB_hft() to read in lists of values  (extended it to input lines to eval in Python...)
        next: add implementation for availableMethods, including inherit, useDefaultValue, plus python functions (lambda expressions?)
        possibly: add explicit names for implicit entities like queries and beliefs.  
                  e.g., ((bill founded microsoft) probability 0.7) == (LPbill_founded_microsoftRP probability 0.7)
                  e.g., ((bill founded) availableMethods) = (LPbill_founded availableMethods)

see theo_test.py for examples that exercise these functions

Different levels of Theo's getValue(s) functions:
 getValues0(entity, slot) is lowest level, just retrieves the stored value.  Can be traced via THEOtraceGetValues0=True
 addValue0(entity,slot,value) is lowest level.  Just adds values
 deleteValue0(e,s,v) is lowest level.  Just removes values

 getValues(e,s) is same as getValues0(e,s)
 getValue(e,s) essentially returns just the first value in getValues(e,s)
 addValue(e,s,v) also maintains Generalization/specializations bidirectional links, and Inverse statements
 deleteValue(e,s,v) also maintains Generalization/specializations bidirectional links, and Inverse statements
 deleteEntity(e) also maintains Generalization/specializations bidirectional links
 deleteSlot(e,s) should possibly be called deleteQuery since it applies to (e,s) pairs

 getValues1(e,s) uses getValues, and also infers slot values using (s availableMethods)
 getValue(e,s)  convenience function that calls getValues1
 deleteValue(e,s,v) SHOULD be written to remove any cached infered slot values that depend on the deleted value. requires logging dependencies

 HOW SHOULD WE handle inference via slot inverses?  
   - special case it like gens/specs?  <-- YES. FOR NOW, WE DO THIS
   - make useInverse an availableMethod, cache answers and track dependencies as part of inference and truth maintenance? 

"""


KB={}

def isEntity0(e):
    return e in KB   # very cool implementation, no?

def isEntity(e):
    return isEntity0(e) 

def ie(e):
    return isEntity0(e)

def isTheoValue(v):
    return ((v != '*NOTHEOVALUE*') and (v != []))

def createEntity0(e,gens):
    """
    create a new Theo entity with one or more generalizations.
    if it already exists, prints a warning to the screen, and returns it.

    Side effects:
    - adds the generalizations and specializations links

    Returns: the dict which represents the entity

    Created: 7/20/20, tommmitchell@gmail.com
    """
    if isEntity0(e):
        print("***WARNING from createEntity0: entity "+ str(e) + " already exists!  I'm doing nothing.")
        return e
    else:
        KB[e]= {'generalizations' : gens}
        for g in gens:
            addValue0(g,'specializations',e)
        return e

def ce(e,gens):
    return createEntity0(e,gens)

def getValues0(e,s):
    """
    This is the lowest level access function to stored slot values.  You can trace every call to 
    it by setting THEOtraceGetValues0 = True.
    """
    if THEOtraceGetValues0 : print('getValues0('+str(e)+','+str(s)+')= ',end='')
    if isEntity0(e):
        if THEOtraceGetValues0 :
            v=KB[e].get(s,'*NOTHEOVALUE*')  # return slot value if exists, else *NOTHEOVALUE*
            print(str(v))
            return v
        else:
            return KB[e].get(s,'*NOTHEOVALUE*')  # return slot value if exists, else *NOTHEOVALUE*
    else:
        if THEOtraceGetValues0 : print('*NOTHEOVALUE*')
        return '*NOTHEOVALUE*'
    
def gvs(e,s):
    return getValues0(e,s)

def getValue0(e,s):
    """ 
    Convenience function.  This returns just the first value of the list of values, or '*NOTHEOVALUE*' if none exist.  
    Handy if you have a slot with nrOfValues=1, because this pulls the value out of the list its stored in
    """
    vs=getValues0(e,s)
    if isTheoValue(vs):
        return vs[0]
    else:
        return '*NOTHEOVALUE*'


def gv(e,s):
    return getValue0(e,s)

def getKnownSlots(e):
    """
    return the list of slots whose values are known for entity e
    """
    return list(KB[e].keys())

def addValue0(e,s,v):
    """
    adds value v to slot s of entity e.
    if slot doesn't exist, creates it and adds value, else appends to the list of values.
    if value is already there, does not add it
    """
    current=getValues0(e,s)
    if current == '*NOTHEOVALUE*':
        if isEntity0(e):
            KB[e][s]=[v]
        else:
            return '*NOTHEOVALUE*'
    elif v not in getValues0(e,s):
        KB[e][s].append(v)

def addValue(e,s,v):
    addValue0(e,s,v)
    if s=='generalizations':   # special case for generalization/specialization bidirectional links
        addValue0(v,'specializations',e)
    elif s=='specializations':
        addValue0(v,'generalizations',e)
    if THEOmaintainInverses:
        si=getValue0(s,'inverse')
        if isTheoValue(si) and isEntity(v):
            addValue0(v,si,e)

def av(e,s,v):
    addValue(e,s,v)


def deleteValue0(e,s,v):
    """
    Deletes the value v of slot s of entity e.
    If value doesn't exist, does nothing.  If this is the only value, removes the slot.
    """
    current=getValues0(e,s)
    if type(current)==list and current.count(v)!=0 :
        current.remove(v)
    if np.shape(current)[0] == 0 :  # just removed the last value of s of e
        KB[e].pop(s)                # so remove the key-value field of s from the dict defining e    

def deleteValue(e,s,v):
    deleteValue0(e,s,v)
    if s=='generalizations':   # special case for generalization/specialization bidirectional links
        deleteValue0(v,'specializations',e)
    elif s=='specializations':
        deleteValue0(v,'generalizations',e)
    if THEOmaintainInverses:
        si=getValue0(s,'inverse')
        if isTheoValue(si) and isEntity(v):
            deleteValue0(v,si,e)
            
def dv(e,s,v):
    deleteValue(e,s,v)
    

def deleteEntity0(e):
    if isEntity0(e):
        KB.pop(e)
    return e

def deleteEntity(e):   # to be tested
    """
    if this is an entity with specializations, also connect those to this entities generalizations
    then delete each value of each slot (to assure inverse side effects occur), then remove from KB.
    """
    specs=getValues0(e,'specializations')
    if specs != '*NOTHEOVALUE*':
        for s in specs:
            deleteValue0(s,'generalizations',e)
            for g in getValues0(e,'generalizations'):
                addValue(s,'generalizations',g)
    ent=KB[e]
    slots=list(ent.key)
    for s in slots:
        deleteSlot(e,s)
    return deleteEntity0(e)

def de(e):
    return deleteEntity(e)

def deleteSlot0(e,s): 
    KB[e].pop(s)

def deleteSlot(e,s):  
    vals=getValues0(e,s)  # first delete each of the slot's values (and in future, meta info)
    if vals != '*NOTHEOVALUE*':
        for v in vals:
            deleteValue(e,s,v)
    # this is unnecessary because deleteValue removes slot when deleting it's last value:  deleteSlot0(e,s)

def ds(e,s):
    deleteSlot(e,s)


def putValues0(e,s,v,maintainInverse=None):   #NOT TESTED, OR NEEDED?
    if maintainInverse is None: maintainInverse='ifRangeEntityExists'
    if isEntity0(e):
        KB[e][s]=v
        inv=getValues0(s,'inverse')
        if inv != '*NOTHEOVALUE*' and maintainInverse == 'ifRangeEntityExists':
            for val in v:
                if isEntity0(val):
                    KB[val][inv]=[e]
                    putValue0(val,inv,e)
    else:
        print('***WARNING from putValues0: entity '+str(e)+ ' does not exist!!')
        return FALSE

def pvs(e,s,v):
    return putValues0(e,s,v)

def saveKB(filename):
    import datetime
    import pickle
    saveDir='/Users/mitchell/lib/python/TheoKBs/'
    savefile=saveDir+filename+' '+str(datetime.datetime.now())+'.pkl'   # need to create filenames without / in them!!!
    with open(savefile, 'wb+') as f:
        pickle.dump(KB, f, pickle.HIGHEST_PROTOCOL)
    return 

def loadKB_pkl(filename):
    import pickle
    saveDir='/Users/mitchell/lib/python/TheoKBs/'
    with open(saveDir+filename, 'rb') as f:
        KB = pickle.load(f)

# loadKB_hft('TheoBareKB.hft')
def loadKB_hft(filename):
    """
    TO DO: update this to use the more general function 
    """
    saveDir='/Users/mitchell/lib/python/TheoKBs/'
    fh = open(saveDir+filename, mode='r')
    for line in fh:
        if line.startswith('ce ') :  # createEntity
            print(line,end='')
            line=line.strip().split()
            ent=line[1]
            theRest=line[2:]
            gens=[]
            for s in theRest:
                v=s.strip('[]')
                if v != '':
                    gens.append(v)
            ce(ent, gens)
        elif line.startswith('av ') : # addValue
            print(line,end='')
            strippedline=line.strip()
            splitline=strippedline.split()
            ent=splitline[1]
            slot=splitline[2]
            lineAfterEnt=line[(line.find(ent)+len(ent)):].strip() # first take the command and entity off the string
            valstr = lineAfterEnt[(lineAfterEnt.find(slot)+len(slot)):].strip()  # rest of the string after slot, stripped
            if (valstr.startswith("'") and valstr.endswith("'")) or (valstr.startswith('"') and valstr.endswith('"')):
                val=valstr[1:-1]
            elif valstr.startswith('['):
                print("*** WARNING: in loadKB_hft I cannot yet handle lists as slot values. Extend me please!")
                val=valstr[1:-1]
            else:
                val=strToken2val(valstr)
            av(ent,slot,val)
        elif line.startswith('ev') :  # eval the rest of the line in Python
            print(line,end='')
            evalstr=line[3:].strip()
            eval(evalstr)            
    fh.close()

def strToken2val(str):
    if str.isnumeric():  
        return int(str)
    elif str.replace('.','').isnumeric():  # integer once we remove decimal point
        return float(str)
    elif str.startswith('"'):
        return str.replace('"','')
    elif str.startswith("'"):
        return str.replace("'","")
    else:
        return str


def loadKB(filename):
    if filename[-3:]=='pkl':
        loadKB_pkl(filename)
    elif filename[-3:]=='hft':
        loadKB_hft(filename)
    else:
        print('I do not recognize files with extension'+filename[-3:])


        
def printEntity(e, offset=None):
    """
    print entity e to the current display.  
    Optional arg offset='' indents the entire print by that string

    Example:  printEntity('generalizations')
    """
    if offset is None: offset=''
    
    ind='  '  # indent for printing slots
    print('\r\n'+str(e))
    for s in KB[e].keys():
        print(offset+ind+s+': '+str(getValues0(e,s)))

def pre(e):
    printEntity(e)


def printHierarchy(e, printSlotVals=None, avoidPrintingSlots=None, offset=None, alreadyPrinted=None):
    """
    Prints the generalization hierarchy of entities below the input entity e.
    Recursive function.

    If entity e appears mult times in hierarchy, it's children shown only once, subsequent occurences marked with *
    """
    if printSlotVals is None : printSlotVals=True
    if avoidPrintingSlots is None : avoidPrintingSlots=['generalizations','specializations']
    if offset is None: offset=''
    if alreadyPrinted is None : alreadyPrinted=[]
    if not isEntity(e):
        print('**Warning from printHierarchy: '+str(e)+' is not an entity!')
        return
    if e in alreadyPrinted :
        print(offset+e+' *')
    else:
        print(offset+e)
        alreadyPrinted.append(e)
        # Here print the slot values if printSlotVals==True
        if printSlotVals:
            for s in getKnownSlots(e):
                if s not in avoidPrintingSlots:
                    print(offset+' |'+ s +': '+ str(getValues0(e,s)))
        specs=getValues0(e,'specializations')
        if type(specs)==list:
            for s in specs:
                printHierarchy(s,printSlotVals,avoidPrintingSlots, offset+'  ',alreadyPrinted)

def prh(e):
    printHierarchy(e)
        

loadKB('TheoBareKB.hft')
# printHierarchy('anything')

###############################################################
"""
This part of the file handles converting beliefs (triples) and queries (pairs) into entities, recursively so...
"""

def belief2Estring(belief):
    Estring='['+belief[0]+" "+belief[1]+" "+belief(2)+']'
    return Estring

###############################################################
"""
This part of the file supplies the inference methods used in Theo.
So far, these include:
- inherit  done
- useDefaultValue  done
- pythonCode  TBD
- dropContext, dropAllContext  TBD
- nnet  TBD  (Pytorch, from other slots and reachable values)
- prolog TBD
"""
# test:

def getValues1(e,s):
    v=getValues0(e,s)
    if isTheoValue(v): return v
    am = getValues0(s,'availableMethods')
    if isTheoValue(am):
        for m in am:
            print(m)
            v=eval(m+'(e,s)')
            if isTheoValue(v): return v
    return '*NOTHEOVALUE*'

def gvs1(e,s):
    return getValues1(e,s)

def getValue1(e,s):
    v=getValues1(e,s)
    if isTheoValue(v):
        return v[0]
    else:
        return v

def gv1(e,s):
    return getValue1(e,s)

def inherit(e,s):
    """
    searches up the generalization hierarchy of entities to get values.
    Stops searching as soon as it finds any entity for which there is at least one value.
    Returns a list of values, but not necessarily every reachable value (except in the case
    where generalizations forms a chain rather than a branching tree).

    One possible future extension: use (s domain) to bound how high up the gen. hierarchy to search
    """
    for g in getValues0(e,'generalizations'):
        vs=getValues0(g,s)
        if isTheoValue(vs):
            return vs
        else:
            vs=inherit(g,s)
            if isTheoValue(vs): return vs
    # if inheritance fails, then
    return '*NOTHEOVALUE*'

def useDefaultValue(e,s):
    vs=getValues0(s,'defaultValue')
    if isTheoValue(vs):
        return vs
    else:
        return '*THEONOVALUE*'

        
