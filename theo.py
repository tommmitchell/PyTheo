import numpy as np
#import pdb  # python debugger
from theomethods import *
import tomutils as tu
global KB
global THEOtraceGetValues0  # if True, the most primitive GetValues0 prints trace info
global THEOtraceDeleteValue0
global THEOmaintainInverses # if True, addValue, deleteValue maintain inverses of beliefs
global THEOdebugTrace  # if True, various functions print diagnostic info
THEOtraceGetValues0=False
THEOtraceDeleteValue0=True
THEOmaintainInverses=True
THEOdebugTrace=False

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

 HOW SHOULD WE handle inference via slot inverses?  For now we special case it like gens/specs

 HOW SHOULD WE handle beliefs and queries as entities?
 - call these complex entities, as opposed to primitive entities repr. by string tokens
 - complex entities represented two ways:
 -- as a list of 3 items (beliefs) or 2 items (queries), where item two is a simple slot 
 -- also as a string which is calculated as str(list representation). 
 -- we have ability to translate back and forth: complexEntity2string, string2complexEntity

TO DO NEXT: edit
- av, so if it is given a complex entity that doesn't yet exist, it creates it, then adds the vlue
- av, dv, getEntity?, etc., so that if they happen to be given a complex entity they do the right thing (convert the string to list if needed, and list to string if needed)
- check all calls to isEntity to make sure they now do the right thing

"""


KB={}

def isLegalComplexEntityString(e):
    return type(e) is str and e.startswith('[') and isLegalComplexEntityList(string2complexEntity(e))

def isLegalComplexEntityList(e):
    return type(e) is list and len(e)<=3 and type(e[1]) is str

def isPrimitiveEntity0(e):
    """
    returns True if e is primitive entity, and exists in the KB
    """
    return type(e) is str and (not e.startswith('[')) and  e in KB   # very cool implementation, no?

def isComplexEntity0(e):
    """
    returns True if e is a complex entity, and exists in the KB
    input can be either a string name of an entity, or a list name of an entity
    """
    if type(e) is list:
        e=complexEntity2string(e)
    return e in KB

def isEntity0(e):
    """
    returns True if entity e exists in the KB. Entity e can be primitive or complex.
    """
    return type(e) is str and e in KB   # very cool implementation, no?

    
def isEntity(e):
    return isPrimitiveEntity0(e) or isComplexEntity0(e)

def ie(e):
    return isEntity(e)

def isLegalBeliefString(e):
    """
    return True is this string refers to a belief triple (which need not be in the KB)
    NOTE A MORE EFFICIENT IMPLEMENTATION IS POSSIBLE - without converting to a list
    """
    if e.startswith('['):
        e=string2complexEntity(e)
        return len(e)==3
    else:
        return False


def isQueryString(e):
    """
    return True is this string refers to a query pair
    NOTE A MORE EFFICIENT IMPLEMENTATION IS POSSIBLE - without converting to a list
    """
    e=string2complexEntity(e)
    return len(e)==2


def isTheoValue(v):
    return ((v != '*NOTHEOVALUE*') and (v != []))

def createEntity0(e,gens):
    """
    Inputs:
    - e: the entity to be created (if a complex entity, can be represented either by its string or list representation)
    - gens: a list of the intended generalizations of e
    Effects:
    Creates a new Theo entity with the specified generalizations
    if it already exists, prints a warning to the screen, and returns it.

    Side effects:
    - adds the generalizations and specializations links

    Returns: the dict which represents the entity

    Created: 7/20/20, tommmitchell@gmail.com
     Tom: 7/31/20: extended this to accept complex entities
    """
    if type(e) is list:
        e=complexEntity2string(e)
    if isEntity(e):
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
    if type(e) is list:
        e=complexEntity2string(e)
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
    Handy if you have a slot with nrOfValues=1, because this pulls the value out of the list it is stored in
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
    return the list of slots of entity e that have known values.
    If e is not in the KB, return empty list []
    """
    if type(e) is list:
        e=complexEntity2string(e)
    if isEntity0(e):
        return list(KB[e].keys())
    else:
        return []
    
def addValue0(e,s,v):
    """
    Inputs:
    - e: an entity (if a complex entity, can be either its string or list representation)
    - s: the slot (a string token)
    - v: the value to add.  If a string, please use single quotes, not double quotes
    adds value v to slot s of entity e.
    if slot s of e doesn't exist, adds it to e, and adds value, else appends to the list of values.
    if value is already there, does not add it.
    If e is a complex entity, and not yet a KB entity, then it creates it and adds the slot value.
    Created tommmitchell@gmail.com
    modified 7/31/2020: added automatic creation if needed for complex entities
    """
    if type(e)==str:
        complexEntity= (e[0]=='[')
        if complexEntity and isLegalBeliefString(e):
            entityType='belief'
        elif complexEntity:
            entityType='query'
    if type(e) is list:
        complexEntity=True
        if len(e)==2:
            entityType='query'
        elif len(e)==3:
            entityType='belief'
        e = complexEntity2string(e)
    current=getValues0(e,s)
    if current == '*NOTHEOVALUE*':
        if isEntity(e):
            KB[e][s]=[v]
        elif complexEntity:
            createEntity0(e,[entityType])
            KB[e][s]=[v]
        else:
            return '*NOTHEOVALUE*'
    elif v not in getValues0(e,s):
        KB[e][s].append(v)

def addValue(e,s,v):
    """
    Note entity e may be a complex entity described by either its string or list representation
    This is like addValue0, but includes also:
    - management of generalizations/specializations hierarchy
    - management of slot inverse values
    Through addValue0, this creates complex entities as needed to store their slot value
    """
    if isLegalComplexEntityList(e): # if given a list repr. of entity e, make it the entity string representation
        e= complexEntity2string(e)  # note string repr is essential when s is 'generalizations' or 'specializations'
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

def isa(e1,e2):
    """
    Returns True iff e2 is in the transitive closure of generalizations of e1.
    Assumes both e1 and e2 are entities represented by strings (either primitive or complex)
    """
    if isEntity0(e1):
        if e1==e2:
            return True
        else:
            for g in getValues0(e1,'generalizations'):
                if isa(g,e2):
                    return True
    return False
            
def deleteValue0(e,s,v):
    """
    Deletes the value v of slot s of entity e.
    If value doesn't exist, does nothing.  If this is the only value, removes the slot.
    Accepts complex entiteis, represented either by their string or list representation
    """
    if THEOtraceDeleteValue0:
        print('deleteValue0['+str(e)+','+s+','+str(v)+']')
    if isLegalComplexEntityList(e): # if given a list repr. of entity e, make it the entity string representation
        e= complexEntity2string(e)
    current=getValues0(e,s)
    if type(current)==list and current.count(v)!=0 :
        current.remove(v)
    if np.shape(current)[0] == 0 :  # just removed the last value of s of e
        KB[e].pop(s)                # so remove the key-value field of s from the dict defining e    
    deleteMetaBeliefsAbout([e,s,v]) # finally, remove any meta beliefs about the belief [e,s,v]
        
def deleteValue(e,s,v):
    if isLegalComplexEntityList(e): # if given a list repr. of entity e, make it the entity string representation
        e= complexEntity2string(e)  # note string repr is essential in case s is generalizations or specializations
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


# entAsList=['tom','spouse','joan']
def deleteMetaBeliefsAbout(entAsList):
    """
    This function deletes all beliefs about the belief [e,s,v], and recursively also deletes beliefs about those beliefs.
    Finally, it deletes the belief entity.
    This is intended to be used inside deleteValue
    Note if e is a complex entity, it is most efficient to represent it by its list representation, but you can input either
    the string representation or list representation of complex entities.
    """
    e=entAsList[0]  # note entAsList can be list of form [e, s, v], or [e, s]
    if isLegalComplexEntityString(e):
        e=string2complexEntity(e)
    s=entAsList[1]
    if len(entAsList)==3:
        v=entAsList[2]
        inputType='belief'
    else:
        inputType='query'
    if inputType=='belief':
        inputEnt=[e,s,v]
    else:
        inputEnt=[e,s]
    inputentStr=str(inputEnt)

    if isEntity0(inputentStr):  # this belief entity exists, so delete its meta beliefs, recursively
        metaBeliefs=getKnownBeliefsAbout(inputEnt)
        for mb in metaBeliefs:
            deleteMetaBeliefsAbout(mb)
            deleteValue(mb[0],mb[1],mb[2])
        deleteEntity(inputentStr) #finally, delete the belief entity itself

def getKnownBeliefsAbout(e):
    """
    return a list of belief triples about entity e.
    input e can be represented as string or complex entity list
    """
    if isLegalComplexEntityString(e):
        elistrep=string2complexEntity(e)
        estr=e
    elif isLegalComplexEntityList(e):
        elistrep=e
        estr= complexEntity2string(e)
    else:
        estr=e
        elistrep=e # this is really just a string token, which is the legal list repr for it
    allBeliefs=[]
    if isEntity0(estr):
        ent=KB[estr]
        slots=ent.keys()
        for s in slots:
            vs = getValues0(estr,s)
            if vs != '*THEONOVALUE*' and type(vs) is list:
                for v in vs:
                    allBeliefs.append([elistrep,s,v])
    return allBeliefs


def deleteEntity0(e):
    if isLegalComplexEntityList(e): # if given a list repr. of entity e, make it the entity string representation
        e= complexEntity2string(e)
    if isEntity0(e):
        KB.pop(e)
    else:
        print('***WARNING from deleteEntity0: I cannot delete the non-existent entity '+e)
    return e

def deleteEntity(e):   # why doesn't this delete the specializations of "belief" correctly?
    """
    if this is an entity with specializations, also connect those to this entities generalizations
    then delete each value of each slot (to assure inverse side effects occur), then remove e from KB.
    """
    if isLegalComplexEntityList(e): # if given a list repr. of entity e, make it the entity string representation
        e= complexEntity2string(e)
        
    specs=getValues0(e,'specializations')
    if specs != '*NOTHEOVALUE*':
        for s in specs:
            deleteValue0(s,'generalizations',e)
            for g in getValues0(e,'generalizations'):
                addValue(s,'generalizations',g)
    gens=getValues0(e,'generalizations')
    if gens != '*NOTHEOVALUE*':
        for g in gens:
            deleteValue0(g,'specializations',e)
    ent=KB[e]
    slots=ent.keys()
    for s in slots:
        deleteSlot(e,s)
    return deleteEntity0(e)

def de(e):
    return deleteEntity(e)

def deleteSlot0(e,s):
    if isLegalComplexEntityList(e): # if given a list repr. of entity e, make it the entity string representation
        e= complexEntity2string(e)
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

    if isLegalComplexEntityList(e): # if given a list repr. of entity e, make it the entity string representation
        e= complexEntity2string(e)
    if isEntity0(e) is False:
        print('Sorry, but '+str(e)+' is not an entity in the knowledge base.')
        return
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

Design choices for now:
 1. make complex entities first class entities in the KB, with generalizations equal to 'belief' or 'query'
 2. complex entities have a representation as a list, e.g., [['tom','spouse','joan'],'source','joan']
 3. we also give complex entities a string representation to index into the KB. stringRepresentation = str(listRepresentation)
 4. use Python str function to translate complex entities to the string representing them in KB, and tu.str2list[0] to invert that translation
 4.1 but 4 depends critically on translating the *full* list representation using Python's str (i.e., *DO NOT* use the string representation for
     the entity in a belief or query, since this leads to nested quote marks inside strings).

Functions that need to be updated to handle beliefs about beliefs and queries:
IsEntity
AddValue - change: if input is a complexEntity that doesn't yet exist, create on the fly
DeleteValue
DeleteSlot
DeleteEntity

Questions:
 1. how do we track down and delete these whenever a belief or entity is deleted?  Seem to require a search over names of the KB keys?.  
  e.g., when dv(e,s,v), search KB.keys for beginswith(complexEntity2string(e,s,v), similar for [e,s].
 2. how to avoid nested types of parentheses like in b3str below?  Use list representaiton of complex ents, and convert full list to string when needed.  Require all Theo string values use single quotes.

examples:
bstr=str(['bill','plays','chess'])  =  "['bill', 'plays', 'chess']"
qstr=str(['bill','plays'])          =  "['bill', 'plays']"
zstr=str([[['bill', 'plays', 'chess'], 'probability', 'high'], 'source', 'jill']) = "[[['bill', 'plays', 'chess'], 'probability', 'high'], 'source', 'jill']"
"""

def complexEntity2string(complexEnt):
    if type(complexEnt) is list:
        return str(complexEnt)
    else:
        print('***WARNING complexEntity2Estring received nonlist as input: '+str(complexEnt))
        return None

def query2Estring(query):
    return str(query)

def string2complexEntity(str):
    """
    given a string defining a complex entity (eg. "[['tom', 'plays'], 'hardToInfer' 'yes']"), return the corresponding 
    list structure, including nested lists.
    This function is the inverse of complexEntity2string
    For a complex entity which is a belief, it should always return a list of length 3
    For a complex entity which is a query, it should always return a list of lenght 2
    """
    if str[0] != '[':
        print('**WARNING from string2complexEntity: '+str+' should begin with [')
        return str
    return tu.str2list(str)



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

        
