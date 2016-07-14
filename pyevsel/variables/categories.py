"""
Categories of data, like "signal" of "background" etc
"""

from pyevsel.utils.files import harvest_files,DS_ID,EXP_RUN_ID
from pyevsel.utils.logger import Logger

from magic_keywords import  MC_P_EN,\
                            MC_P_TY,\
                            MC_P_ZE,\
                            MC_P_WE,\
                            MC_P_GW,\
                            MC_P_TS,\
                            RUN_START,\
                            RUN_STOP, \
                            RUN,\
                            EVENT,\
                            DATASETS
import variables
import pandas as pd
import inspect
import numpy as n
import numpy as np
import abc
import tqdm
import multiprocessing as mp
import threading as thr
import concurrent.futures as fut

from copy import deepcopy

class AbstractBaseCategory(object):
    """
    Stands for a specific type of data, e.g.
    detector data in a specific configuarion,
    simulated data etc.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self,name):
        self.name = name
        self.datasets = dict()
        self.vardict = dict()
        self._weightfunction = lambda x : x
        self.cuts = []
        self.cutmask = np.array([])
        self.plot = True
        self.show_in_table = True
        self._weights = pd.Series()
        self._is_harvested = False

    def __repr__(self):
        return """<{0}: {1}>""".format(self.__class__,self.name)

    def __hash__(self):
        return hash((self.name,"".join(map(str,self.datasets.keys()))))

    def __eq__(self,other):
        if (self.name == other.name) and (self.datasets.keys() == other.datasets.keys()):
            return True
        else:
            return False

    def __len__(self):
        """
        Return the longest variable element
        FIXME: introduce check?
        """

        lengths = np.array([len(self.vardict[v].data) for v in self.vardict.keys()])
        lengths = lengths[lengths > 0]
        selflen = list(set(lengths))
        assert len(selflen) == 1, "Different variable lengths!"
        return selflen[0]

    @property
    def raw_count(self):
        assert self.is_harvested,"Please read out variables first"
        return len(self.get(RUN,uncut=True))

    @property
    def variablenames(self):
        return self.vardict.keys()

    @property
    def is_harvested(self):
        return self._is_harvested

    def set_weightfunction(self,func):
        """
        Register a function used for weighting

        Args:
            func (func): the function to be used
        """
        self._weightfunction = func

    def add_cut(self,cut):
        """
        Add a cut without applying it yet

        Args:
            cut (pyevsel.variables.cut.Cut): Append this cut to the internal cutlist

        """

        self.cuts.append(cut)

    def apply_cuts(self,inplace=False):
        """
        Apply the added cuts

        Keyword Args:
            inplace (bool): If True, cut the internal variable buffer
                           (Can not be undone except variable is reloaded)
        """
        self.undo_cuts()
        mask = n.ones(self.raw_count)
        
        # only apply the condition to the mask
        # created for the cut with the condition
        # not the others
        cond_masks = []
        for cut in self.cuts:
            cond_mask = n.ones(self.raw_count)
            if cut.condition is None:
                continue
            for varname,(op,value) in cut:
                s = self.get(varname)
                cond_mask = n.logical_and(cond_mask,op(s,value) )
            cond_mask = n.logical_or(cond_mask,n.logical_not(cut.condition[self.name]))
            cond_masks.append(cond_mask)

        # finish the conditional part
        for m in cond_masks:
            mask = n.logical_and(mask,m)

        for cut in self.cuts:
            if cut.condition is not None:
                continue
            for varname,(op,value) in cut:
                s = self.get(varname)
                mask = n.logical_and(mask,op(s,value) )
        if inplace:
            for k in self.vardict.keys():
                self.vardict[k].data = self.vardict[k].data[mask]
        else:
            self.cutmask = n.array(mask,dtype=bool)

    def undo_cuts(self):
        """
        Conveniently undo a previous "apply_cuts"
        """

        self.cutmask = n.array([])

    def delete_cuts(self):
        """
        Get rid of previously added cuts and undo them
        """

        self.undo_cuts()
        self.cuts = []

    @staticmethod
    def _ds_regexp(filename):
        """
        A container for matching a dataset number against a filename

        Args:
            filename (str): An filename of a datafile
        Returns:
            dataset (int): A dataset number extracted from the filename
        """
        return DS_ID(filename)

    def load_vardefs(self,module):
        """
        Load the variable definitions from a module

        Args:
            module (python module): Needs to contain variable definitions
        """

        all_vars = inspect.getmembers(module)
        all_vars = [x[1] for x in all_vars if isinstance(x[1],variables.AbstractBaseVariable)]
        for v in all_vars:
            if v.name in self.vardict:
                Logger.debug("Variable %s already defined,skipping!" %v.name)
                continue
            self.add_variable(v)

    def add_variable(self,variable):
        """
        Add a variable to this category

        Args:
            variable (pyevsel.variables.variables.Variable): A Variable instalce
        """
        tmpvar = deepcopy(variable)
        self.vardict[tmpvar.name] = tmpvar

    def get_files(self,*args,**kwargs):
        """
        Load files for this category
        uses pyevsel.utils.files.harvest_files

        Args:
            *args (list of strings): Path to possible files

        Keyword Args:
            datasets (dict(dataset_id : nfiles)): i given, load only files from dataset dataset_id  set nfiles parameter to amount of L2 files the loaded files will represent
            force (bool): forcibly reload filelist (pre-readout vars will be lost)
            all other kwargs will be passed to
            utils.files.harvest_files
        """
        force = False
        if "force" in kwargs:
            force = kwargs.pop("force")
        if self.is_harvested:
            Logger.info("Variables have already been harvested!\
                         if you really want to reload the filelist,\
                         use 'force=True'.\
                         If you do so, all your harvested variables will be deleted!")
            if not force:
                return
            else:
                Logger.warning("..using force..")

        if "datasets" in kwargs:
            filtered_files = []
            self.datasets = kwargs.pop("datasets")
            files = harvest_files(*args,**kwargs)
            datasets = [self._ds_regexp(x) for x in files]

            assert len(datasets) == len(files)

            ds_files = zip(datasets,files)
            for k in self.datasets.keys():
                filtered_files.extend([x[1] for x in ds_files if x[0] == k])

            files = filtered_files
        else:
            files = harvest_files(*args,**kwargs)

        self.files = files

    def get(self,varkey,uncut=False):
        """
        Retrieve the data of a variable

        Args:
            varkey (str): The name of the variable

        Keyword Args:
            uncut (bool): never return cutted values
        """

        if varkey not in self.vardict:
            raise KeyError("%s not found!" %varkey)

        if len(self.cutmask) and not uncut:
            return self.vardict[varkey].data[self.cutmask]
        else:
            return self.vardict[varkey].data

    def read_variables(self,names=None):
        """
        Harvest the variables in self.vardict

        Keyword Args:
            names (list): havest only these variables
        """

        if names is None:
            names = self.vardict.keys()
        compound_variables = [] #harvest them later

        def work(variablename,func_args,func_kwargs):

            return variablename,variables.harvest(*func_args,**func_kwargs)

        #workers = mp.Pool(processes=4) # 4 is random
        threads = []
        #executor = fut.ProcessPoolExecutor(max_workers=4)
        for varname in tqdm.tqdm(names,desc="Reading {0} variables".format(self.name), leave=True):
            try:
                if isinstance(self.vardict[varname],variables.CompoundVariable):
                    compound_variables.append(varname)
                    continue

                if isinstance(self.vardict[varname],variables.VariableList):
                    compound_variables.append(varname)
                    continue
            except KeyError:
                Logger.warning("Cannot find %s in variables!" %varname)
                continue

            #workers.apply_async(self.vardict[varname].harvest,args=self.files)
            self.vardict[varname].harvest(*self.files)
            #thefuture.result()
            #threads.append(thefuture)            
    
        for t in threads:
            t.result()
        #fut.as_completed(*threads)
        #workers.close()
        #workers.join()
        for varname in compound_variables:
            #FIXME check if this causes a memory leak
            self.vardict[varname].rewire_variables(self.vardict)
            self.vardict[varname].harvest()
        self._is_harvested = True

    @abc.abstractmethod
    def get_weights(self,model,model_kwargs=None):
        return

    def get_datacube(self):
        cube = dict()
        for k in self.vardict.keys():
            cube[k] = self.get(k)

        return pd.DataFrame(cube)

    @property
    def weights(self):
        if len(self.cutmask):
            return self._weights[self.cutmask]
        else:
            return self._weights

    @property
    def integrated_rate(self):
        """
        Calculate the total eventrate of this category
        (requires weights)

        Returns (tuple): rate and quadratic error
        """

        rate  = self.weights.sum()
        error = n.sqrt((self.weights**2).sum())
        return (rate,error)

    def add_livetime_weighted(self,other,self_livetime=None,other_livetime=None):
        """
        Combine two datasets livetime weighted. If it is simulated data,
        then in general it does not know about the detector livetime.
        In this case the livetimes for the two datasets can be given

        Args:
            other (pyevsel.categories.Category): Add this dataset

        Keyword Args:
            self_livetime (float): the data livetime for this dataset
            other_livetime (float): the data livetime for the other dataset

        """

        assert self.vardict.keys() == other.vardict.keys(),"Must have the same variables to be combined"

        if isinstance(self,Data):
            self_livetime = self.livetime

        if isinstance(other,Data):
            other_livetime = other.livetime

        for k in other.datasets.keys():
            self.datasets.update({k : other.datasets[k]})
        self.files.extend(other.files)
        if self.cuts or other.cuts:
            self.cuts.extend(other.cuts)
        if len(self.cutmask) or len(other.cutmask):
            self.cutmask = n.hstack((self.cutmask,other.cutmask))

        for name in self.variablenames:
            self.vardict[name].data = pd.concat([self.vardict[name].data,other.vardict[name].data])

        self_weight = (self_livetime/(self_livetime + other_livetime))
        other_weight = (other_livetime/(self_livetime + other_livetime))

        self._weights = pd.concat([self_weight*self._weights,other_weight*other._weights])
        if isinstance(self,Data):
            self.set_livetime(self.livetime + other.livetime)


class Simulation(AbstractBaseCategory):
    """
    An interface to variables from simulated data
    Allows to weight the events
    """
    _mc_p_readout = False

    def __init__(self,name):
        AbstractBaseCategory.__init__(self,name)

    @property
    def mc_p_readout(self):
        return self._mc_p_readout

    def read_mc_primary(self,energy_var=MC_P_EN,\
                       type_var=MC_P_TY,\
                       zenith_var=MC_P_ZE,\
                       weight_var=MC_P_WE):
        """
        Trigger the readout of MC Primary information
        Rename variables to magic keywords if necessary

        Keyword Args:
            energy_var (str): simulated primary energy
            type_var (str): simulated primary type
            zenith_var (str): simulated primary zenith
            weight_var (str): a weight, e.g. interaction propability
        """
        self.read_variables([energy_var,type_var,zenith_var,weight_var])
        for varname,defaultname in [(energy_var,MC_P_EN),\
                                    (type_var,MC_P_TY),\
                                    (zenith_var,MC_P_ZE),
                                    (weight_var,MC_P_WE)]:
            if varname != defaultname:
                Logger.warning("..renaming %s to %s.." %(varname,defaultname))
                self.vardict[varname].name = defaultname

        self._mc_p_readout = True

    def get_weights(self,model,model_kwargs = None):
        """
        Calculate weights for the variables in this category

        Args:
            model (callable): A model to be evaluated

        Keyword Args:
            model_kwargs (dict): Will be passed to model
        """
        if not self._mc_p_readout:
            self.read_mc_primary()

        if model_kwargs is None:
            model_kwargs = dict()
        func_kwargs = {MC_P_EN : self.get(MC_P_EN),\
                       MC_P_TY : self.get(MC_P_TY),\
                       MC_P_WE : self.get(MC_P_WE)}

        for key in MC_P_ZE,MC_P_GW,MC_P_TS,DATASETS:
            reg = key
            if key == DATASETS:
                reg = 'mc_datasets'
            try:
                func_kwargs[reg] = self.get(key)
            except KeyError:
                Logger.warning("No MCPrimary {0} informatiion! Trying to omit..".format(key))

        func_kwargs.update(model_kwargs)
        Logger.info("Getting weights for datasets %s" %self.datasets.__repr__())
        self._weights = pd.Series(self._weightfunction(model,self.datasets,\
                                 **func_kwargs))

    @property
    def livetime(self):
        return self.weights.sum() / n.power(self.weights, 2).sum()

class ReweightedSimulation(Simulation):
    """
    A proxy for simulation dataset, when only the weighting differs
    """

    def __init__(self,name,mother):
        Simulation.__init__(self,name)
        self._mother = mother

    # proxies
    @property
    def mother(self):
        return self._mother

    setter = lambda self,other : None
    vardict       = property(lambda self: self.mother.vardict,\
                        setter)
    datasets      = property(lambda self: self.mother.datasets,\
                        setter)
    files         = property(lambda self: self.mother.files,\
                        setter)
    _is_harvested = property(lambda self: self.mother.is_harvested,\
                             setter)
    _mc_p_readout = property(lambda self: self.mother.mc_p_readout,\
                             setter)

    @property
    def raw_count(self):
        return self.mother.raw_count

    def read_variables(self,names=None):
        return self.mother.read_variables(names=names)

    def read_mc_primary(self,energy_var=MC_P_EN,\
                       type_var=MC_P_TY,\
                       zenith_var=MC_P_ZE,\
                       weight_var=MC_P_WE):
        return self.mother.read_mc_primary(energy_var,type_var,zenith_var, weight_var)

    def add_livetime_weighted(self,other):
        raise ValueError('ReweightedSimulation datasets can not be combined! Instanciate after adding mothers instead!')

    def get(self,varkey,uncut=False):
        data = self.mother.get(varkey,uncut=True)

        if len(self.cutmask) and not uncut:
            return data[self.cutmask]
        else:
            return data


class Data(AbstractBaseCategory):
    """
    An interface to real time event data
    Simplified weighting only
    """

    def __init__(self,name):
        """
        Instanciate a Data dataset. Provide livetime in **kwargs.
        Special keyword "guess" for livetime allows to guess the livetime later on

        Args:
            name: a unique identifier

        Returns:

        """
        AbstractBaseCategory.__init__(self,name)
        self._runstartstop_set = False

    @staticmethod
    def _ds_regexp(filename):
        return EXP_RUN_ID(filename)

    def set_weightfunction(self,func):
        return

    def set_livetime(self,livetime):
        """
        Override the private _livetime member

        Args:
            livetime: The time needed for data-taking

        Returns:
             None

        """
        self._livetime = livetime

    # livetime is read-only
    @property
    def livetime(self):
        return self._livetime

    def set_run_start_stop(self,runstart_var=variables.Variable(None),runstop_var=variables.Variable(None)):
        """
        Let the simulation category know which 
        are the paramters describing the primary

        Keyword Args:
            runstart_var (pyevself.variables.variables.Variable): beginning of a run
            runstop_var (pyevself.variables.variables.Variable): beginning of a run

        """
        #FIXME
        for var,name in [(runstart_var,RUN_START),(runstop_var,RUN_STOP)]:
            if var.name is None:
                Logger.warning("No {0} available".format(name))
            elif name in self.vardict:
                Logger.info("..{0} already defined, skipping...".format(name))
                continue
            
            else:
                if var.name != name:
                    Logger.info("..renaming {0} to {1}..".format(var.name,name))
                    var.name = name
                newvar = deepcopy(var)
                self.vardict[name] = newvar

        self._runstartstop_set = True

    def estimate_livetime(self,force=False):
        """
        Calculate the livetime from run start/stop times, account for gaps
        
        Keyword Args:
            force (bool): overide existing livetime
        """
        if self.livetime and (not self.livetime=="guess"):
            Logger.warning("There is already a livetime of %4.2f " %self.livetime)
            if force:
                Logger.warning("Applying force...")
            else:
                Logger.warning("If you really want to do this, use force = True")
                return
        
        if not self._runstartstop_set:
            if (RUN_STOP in self.vardict.keys()) and (RUN_START in self.vardict.keys()):
                self._runstartstop_set = True
            else:
                Logger.warning("Need to set run start and stop times first! use object.set_run_start_stop")
                return

        Logger.warning("This is a crude estimate! Rather use a good run list or something!")
        lengths = self.get(RUN_STOP) - self.get(RUN_START)
        gaps    = self.get(RUN_START)[1:] - self.get(RUN_STOP)[:-1] #trust me!
        #h = self.nodes["header"].read()
        #h0 = h[:-1]
        #h1 = h[1:]
        ##FIXME
        #lengths = ((h["time_end_mjd_day"] - h["time_start_mjd_day"]) * 24. * 3600. +
        #           (h["time_end_mjd_sec"] - h["time_start_mjd_sec"]) +
        #           (h["time_end_mjd_ns"] - h["time_start_mjd_ns"])*1e-9 )
 
        #gaps = ((h1["time_start_mjd_day"] - h0["time_end_mjd_day"]) * 24.  * 3600. +
        #        (h1["time_start_mjd_sec"] - h0["time_end_mjd_sec"]) +
        #        (h1["time_start_mjd_ns"] - h0["time_end_mjd_ns"])*1e-9)
 

        # detector livetime is the duration of all events + the length of      all
        # gaps between events that are short enough to be not downtime. (     guess: 30s)
        est_ltime =  ( lengths.sum() + gaps[(0<gaps) & (gaps<30)].sum() )
        self.set_livetime(est_ltime)
        return 

    def get_weights(self,livetime):
        """
        Calculate weights as rate, that is number of
        events per livetime
        """
        #FIXME: Move lifetime to arguments? It would make sense...

        self.set_livetime(livetime)
        if self.livetime == "guess":
            self.estimate_livetime()
        self._weights = pd.Series(n.ones(self.raw_count,dtype=n.float64)/self.livetime)

