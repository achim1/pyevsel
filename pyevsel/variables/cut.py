"""
Use with pyevsel.categories.Category to perfom cuts
"""

from pyevsel.variables.variables import Variable as V

import operator

def create_func(operation,value):
    """operator_lookup
    Create conditional function for the provide operator
    value pair

    Args:
        operation (str): an operator string, '<', '==", etc
        value (float): goes with operation

    Returns:
        func
    """
    operator_lookup = {\
    ">" : operator.gt,\
    "==" : operator.eq,\
    "<" : operator.lt,\
    ">=" : operator.ge,\
    "<=" : operator.le\
    }

    def func(x):
        return operator_lookup[operation](x,value)
    return func

class Cut(object):
    """
    Impose criteria on variables of a certain
    category to reduce its mightiness
    """
    cutdict = dict()
    compiled_cuts = dict()
    #_condition_map = {">" : "gt","<" : "lt",">=" : "ge","<=" : "le"}

    def __init__(self,variables=[("mc_p_energy",">=",5)],condition=[]):

        self.condition = condition
        for var,operation,value in variables:
            if isinstance(var,V):
                name = var.name
            if isinstance(var,str):
                name = var
            self.cutdict[name] = (operation,value)
            self.compiled_cuts[name] = create_func(operation,value)

    def __iter__(self):
        """
        Return name, cutfunc pairs
        """

        for k in self.cutdict.keys():
            yield k,self.compiled_cuts[k]

    def __repr__(self):
        rep = """<Cut """
        for k in self.cutdict.keys():
            rep += """|%s %s %4.2f """ %(k,self.cutdict[k][0],self.cutdict[k][1])

        rep += """>"""
        return rep

    #def __call__(self,category):
    #    """
    #    do it!
    #    """
    #    newcat = category
    #    total_mask = n.ones(len(category),dtype=n.bool)
    #    for v in self._cutdict.keys():
    #        ops = self._cutdict[v]
    #        if not callable(ops):
    #            ops = self._condition_map[ops]
    #            newcat.vardict[v].data = category.vardict[v].data.__getattribute__(ops)()
    #        else:
    #            mask = category.vardict[v].data.map(ops)
    #            self.maskdict[v] = mask
    #            total_mask = n.logical_and(total_mask,mask)
    #    print len(total_mask) == len(total_mask[n.isfinite(total_mask)])
    #    print total_mask
    #    total_mask = n.array(total_mask)
    #    for v in category.vardict.keys():
    #        print v
    #        print category.vardict[v].data
    #        newcat.vardict[v].data = category.vardict[v].data.where(total_mask)
    #    return newcat


