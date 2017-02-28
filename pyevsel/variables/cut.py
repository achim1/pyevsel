"""
Use with pyevsel.categories.Category to perfom cuts
"""

from builtins import object
from pyevsel.variables.variables import Variable as V
from pyevsel.utils.logger import Logger
from collections import defaultdict

import operator
operator_lookup = {\
    ">" : operator.gt,\
    "==" : operator.eq,\
    "<" : operator.lt,\
    ">=" : operator.ge,\
    "<=" : operator.le\
    }

inv_operator_lookup = {v: k for k, v in list(operator_lookup.items())}


class Cut(object):
    """
    Impose criteria on variables of a certain
    category to reduce its mightiness
    """

    def __init__(self,*cuts,**kwargs):
        """
        Create a new cut, with the variables and operations
        given in cuts

        Args:
            cuts (list): like this [("mc_p_energy",">=",5)]

        Keyword Args:
            condition (numpy.ndarry(bool)): where to apply the cut

        Returns:
            None
        """

        self.condition = None
        self.name = None
        if "condition" in kwargs:
            self.condition = kwargs["condition"]
        if 'name' in kwargs:
            self.name = kwargs['name']
        self.cutdict = defaultdict(list)
        for var,operation,value in cuts:
            if isinstance(var,V):
                name = var.name
            if isinstance(var,str):
                name = var
            self.cutdict[name].append((operator_lookup[operation],value))

    @property
    def variablenames(self):
        """
        Returns a list of strings with the names of the 
        variables
        """

        return list(self.cutdict.keys())


    def __iter__(self):
        """
        Return name, cutfunc pairs
        """
        # flatten out the cutdict
        for k in list(self.cutdict.keys()):
            for j in self.cutdict[k]:
                yield k,j

    def __repr__(self):
        if self.condition is not None:
            rep = """< Cut with condition | \n"""
        else:
            rep = """< Cut | \n"""
        for i,(j,k) in sorted(self):
            rep += """| {0} {1} {2} \n""".format(i,inv_operator_lookup[j],k)

        rep += """| >"""
        return rep




