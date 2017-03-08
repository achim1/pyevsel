"""
Some basic plot routines for plots which occur over and 
over in eventselections
"""
from __future__ import print_function

from builtins import range
from builtins import object

try:
    import yaml
except ImportError:
    import ruamel.yaml as yaml
import os
import os.path

import numpy as n
import dashi as d
d.visual()

from .plotcolors import get_color_palette
from .canvases import YStackedCanvas
from pyevsel.utils.logger import Logger
from pyevsel.plotting import GetCategoryConfig,LoadConfig

import pylab as p

STD_CONF=os.path.join(os.path.split(__file__)[0],"plotsconfig.yaml")

STYLE = os.path.join(os.path.split(__file__)[0],"pyevseldefault.mplstyle")
p.style.use(STYLE)

###############################################


def create_arrow(ax, x_0, y_0, dx, dy, length,\
                 width = .1, shape="right",\
                 fc="k", ec="k",\
                 alpha=1., log=False):
    """
    Create an arrow object for plots. This is typically a large
    arrow, which can used to indicate a region in the plot which
    is excluded by a cut.

    Args:
        ax (matplotlib.axes._subplots.AxesSubplot): The axes where the arrow
                                                    will be attached to
        x_0 (float): x-origin of the arrow
        y_0 (float): y-origin of the arrow
        dx (float): x length of the arrow
        dy (float): y length of the arrow
        length (float): additional scaling parameter to scale
                        the length of the arrow

    Keyword Args:
        width (float): thickness of arrow
        shape (str): either "full", "left" or "right"
        fc (str): facecolor
        ec (str): edgecolor
        alpha (float): 0 -1 alpha value of the arrow
        log (bool): Ifor logscale, the proportion can be
                     automatically adjust

    Returns:
        matplotlib.axes._subplots.AxesSubplot
    """
    head_starts_at_zero = False
    head_width = width*5
    head_length = length*0.1
    if log: # slightly bigger arrow
        head_width = width*6
        head_length = length*0.2

    arrow_params={'length_includes_head':False,\
                  'shape':shape,\
                  'head_starts_at_zero':head_starts_at_zero}
    arr = ax.arrow(x_0, y_0, dx*length,\
                   dy*length, fc=fc, ec=ec,\
                   alpha=alpha, width=width,\
                   head_width=head_width,\
                   head_length=head_length,\
                   **arrow_params)
    return ax

###########################


def PlotVariableDistribution(categories, name, ratio = ([],[])):
    """
    One shot short-cut for one of the most used
    plots in eventselections.

    Args:
        categories (list): A list of categories which should be plotted
        name (string): The name of the variable to plot

    Keyword Args:
        ratio (tuple): A ratio plot of these categories will be crated
    """
    plot = VariableDistributionPlot()
    for cat in categories:
        plot.add_variable(cat,name)
        plot.add_cumul(cat.name)
    plot.add_ratio(ratio[0],ratio[1])
    plot.plot(heights=[.4,.2,.2])
    return plot

###############################################


class VariableDistributionPlot(object):
    """
    A container class to hold histograms
    and ratio plots for variables
    """

    def __init__(self, cuts=None,\
                 color_palette="dark",\
                 bins=None):
        """
        A plot which shows the distribution of a certain variable.
        Cuts can be indicated with lines and arrows. This class defines
        (and somehow enforces) a certain style.

        Keyword Args:
            bins (array-like): desired binning, if None use default
            cuts (pyevsel.variables.cut.Cut):
            color_palette (str): use this palette for the plotting
        """
        self.histograms = {}
        self.histratios = {}
        self.cumuls     = {}
        self.plotratio  = False
        self.plotcumul  = False
        self.canvas     = None
        self.label      = ''
        self.dataname   = ''
        self.bins       = bins
        if cuts is None:
            cuts = []
        self.cuts       = cuts
        self.color_palette = get_color_palette(color_palette)

    def add_data(self, dataname,\
                  variable_data, bins,\
                  weights=None,label=''):
        """
        Histogram the added data and store internally
        
        Args:
            dataname (string): the name of a category
            variable_data (array): the actual data
            bins (array): histogram binning
        
        Keyword Args:
            weights (array): weights for the histogram
        """
        if weights is None:
            weights = n.ones(len(variable_data))
        self.histograms[dataname] = d.factory.hist1d(variable_data,bins,weights=weights)
        self.label = label
        self.name = dataname

    def add_variable(self, category, variable_name):
        """
        Convenience interface if data is sorted in categories already

        Args:
           category (pyevsel.variables.category.Category): Get variable from this category
           variable_name (string): The name of the variable

        """
        if self.bins is None:
            self.bins = category.vardict[variable_name].bins
        self.dataname = variable_name
        self.add_data(category.name, category.get(variable_name),\
                       self.bins, weights=category.weights,\
                       label=category.vardict[variable_name].label)

    def indicate_cut(self, ax, arrow=True):
        """
        If cuts are given, indicate them by lines

        Args:
            ax (pylab.axes): axes to draw on

        """
        vmin, vmax = ax.get_ylim()
        hmin, hmax = ax.get_xlim()
        for cut in self.cuts:
            for name, (operator, value) in cut:

                # there might be more than one
                # cut which should be
                # drawn on this plot
                # so go through ALL of them.
                if name != self.dataname:
                    continue

                Logger.debug('Found cut! {0} on {1}'.format(name,value))
                width = vmax/50.

                # create a line a cut position
                ax.vlines(value, ymin=vmin, ymax=vmax, linestyle=':')
                length = (hmax - hmin)*0.1

                # mark part of the plot as "forbidden"
                # and create arrow if desired
                if operator in ('>','>='):
                    shape = 'right'
                    ax.axvspan(value, hmax,\
                               facecolor=self.color_palette["prohibited"],\
                               alpha=0.5)
                else:
                    shape = 'left'
                    ax.axvspan(hmin, value,\
                               facecolor=self.color_palette["prohibited"],\
                               alpha=0.5)

                if arrow:
                    ax = create_arrow(ax, value, vmax*0.1,\
                                      -1., 0, length, width=width,\
                                      shape=shape, log=True)

    def add_ratio(self, nominator, denominator,\
                  total_ratio=None, total_ratio_errors=None, \
                  log=False, label="data/$\Sigma$ bg"):
        """
        Add a ratio plot to the canvas

        Args:
            nominator (list or str): name(s) of the categorie(s) which
                                     will be the nominator in the ratio
            denominator (list or str): name(s) of the categorie(s) which
                                     will be the nominator in the ratio

        Keyword Args:
            total_ratio (bool): Indicate the total ratio with a line in the plot
            total_ratio_errors (bool): Draw error region around total ratio
            log (bool): draw ratio plot in log-scale
            label (str): y-label for the ratio plot

        """
        if not isinstance(nominator, list):
            nominator = [nominator]
        if not isinstance(denominator, list):
            denominator = [denominator]

        name = "".join(nominator) + "_" + "".join(denominator)
        first_nominator = nominator.pop()
        nominator_hist = self.histograms[first_nominator]
        nominator_ws   = self.histograms[first_nominator].stats.weightsum
        for name in nominator:
            nominator_hist += self.histograms[name]
            nominator_ws   += self.histograms[name].stats.weightsum

        first_denominator = denominator.pop()
        denominator_hist = self.histograms[first_denominator]
        denominator_ws = self.histograms[first_denominator].stats.weightsum
        for name in denominator:
            denominator_hist += self.histograms[name]
            denominator_ws   += self.histograms[name].stats.weightsum
    
        nominator_hist.normalized()
        denominator_hist.normalized()
        ratio = d.histfuncs.histratio(nominator_hist, denominator_hist,\
                                      log=False, ylabel=label)
        if total_ratio is None:
            total_ratio = nominator_ws/denominator_ws
            Logger.info("Calculated scalar ratio of {:4.2f} from histos".format(total_ratio))

        #ratio.y[ratio.y > 0] = ratio.y[ratio.y > 0] + total_ratio -1
        self.histratios[name] = (ratio, total_ratio, total_ratio_errors,\
                                 label)
        return name

    def add_cumul(self, name):
        """
        Add a cumulative distribution to the plto

        Args:
            name (str): the name of the category
        """
        self.cumuls[name] = self.histograms[name].normalized()

    def _draw_distribution(self, ax, name, log=True,\
                           cumulative=False,\
                           configfilename=STD_CONF):
        """
        Paint the histograms!
        """
        cfg = GetCategoryConfig(name)
        color = cfg["dashistyle"].pop('color')
        if 'dashistylescatter' in cfg:
            scattercolor = cfg["dashistylescatter"].pop('color')
            if isinstance(scattercolor,int):
                scattercolor = self.color_palette[scattercolor]
        if isinstance(color,int):
            color = self.color_palette[color]

        if cumulative:
            histograms = self.cumuls
            log = False # no log, no way!
        else:
            histograms = self.histograms

        if cfg['histscatter'] == 'scatter':
            histograms[name].scatter(log=log,cumulative=cumulative,label=cfg["label"],color=scattercolor,**cfg["dashistylescatter"])
        elif cfg['histscatter'] == "line":
            histograms[name].line(log=log,cumulative=cumulative,label=cfg["label"],color=color,**cfg["dashistyle"])
        elif cfg['histscatter'] == "overlay":
            histograms[name].line(log=log,cumulative=cumulative,label=cfg["label"],color=color,**cfg["dashistyle"])
            histograms[name].scatter(log=log,cumulative=cumulative,color=scattercolor,**cfg["dashistylescatter"])
        if cumulative:
            ax.set_ylabel('fraction')
        else:
            ax.set_ylabel('rate/bin [1/s]')

    def _draw_histratio(self, name, axes, ylim=(0.1,2.5)):
        """
        Plot on of the ratios
        """
        ratio,total_ratio,total_ratio_errors,label = self.histratios[name]
        ratio.scatter(c="k",marker="o",markersize=3)
        axes.hlines(total_ratio,axes.get_xlim()[0],axes.get_xlim()[1],linestyle="--")
        if total_ratio_errors is not None:
            axes.hlines(total_ratio + total_ratio_errors,axes.get_xlim()[0],axes.get_xlim()[1],linestyle=":")
            axes.hlines(total_ratio - total_ratio_errors,axes.get_xlim()[0],axes.get_xlim()[1],linestyle=":")
            xs = n.linspace(axes.get_xlim()[0],axes.get_xlim()[1],200)
            axes.fill_between(xs,total_ratio - total_ratio_errors, total_ratio + total_ratio_errors,facecolor="grey",alpha=0.3)
        axes.set_ylim(ylim)
        axes.set_ylabel(label)
        axes.grid(1)

    def _locate_axes(self,combined_cumul,combined_ratio,combined_distro):
        axes_locator = []
        if self.cumuls:
            if combined_cumul:
                axes_locator.append((0,"c"))
            else:
                axes_locator += [(x,"c") for x in range(len(self.cumuls))]

        if self.histratios:
            if combined_ratio:
                if axes_locator:
                    axes_locator.append((axes_locator[-1] + 1,"r"))
                else:
                    axes_locator.append((0,"r"))
            else:
                if axes_locator:
                    axes_locator +=[(x+ len(axes_locator),"r") for x  in range(len(self.histratios))]

        if self.histograms:
            if combined_distro:
                if axes_locator:
                    axes_locator.append((axes_locator[-1] + 1,"h"))
                else:
                    axes_locator.append((0,"h"))
            else:
                if axes_locator:
                    axes_locator +=[(x+ len(axes_locator),"h") for x  in range(len(self.histograms))]
        return axes_locator

    def plot(self,heights=(.5, .2, .2),\
             axes_locator=((0, "c"), (1, "r"), (2, "h")),\
             combined_distro=True,\
             combined_ratio=True,\
             combined_cumul=True,
             log=True):
        """
        Create the plot

        Args:
            heights:
            axes_locator:
            combined_distro:
            combined_ratio:
            combined_cumul:
            log:

        Returns:

        """

        Logger.info("Found {} distributions".format(len(self.histograms)))
        Logger.info("Found {} ratios".format(len(self.histratios)))
        Logger.info("Found {} cumulative distributions".format(len(self.cumuls)))
        if not axes_locator:
            axes_locator = self._locate_axes(combined_cumul,combined_ratio,combined_distro)

        # calculate the amount of needed axes
        assert len(axes_locator) == len(heights), "Need to specify exactly as many heights as plots you want to have"

        self.canvas = YStackedCanvas(subplot_yheights=heights)
        
        cu_axes = [x for x in axes_locator if x[1] == "c"]
        h_axes = [x for x in axes_locator if x[1] == "h"]
        r_axes = [x for x in axes_locator if x[1] == "r"]
        maxheights = []
        minheights = []
        for ax in cu_axes:
            cur_ax = self.canvas.select_axes(ax[0])
            if combined_cumul:
                for k in list(self.cumuls.keys()):
                    self._draw_distribution(cur_ax,k,cumulative=True,log=log)
                break
            else:
                k = self.cumuls[list(self.cumuls.keys())[ax[0]]]
                self._draw_distribution(cur_ax,cumulative=True,log=log)
        for ax in r_axes:
            cur_ax = self.canvas.select_axes(ax[0])
            if combined_ratio:
                for k in list(self.histratios.keys()):
                    self._draw_histratio(k,cur_ax)
                break
            else:
                k = self.histratios[list(self.histratios.keys())[ax[0]]]
                self._draw_histratio(k,cur_ax)    

        for ax in h_axes:
            cur_ax = self.canvas.select_axes(ax[0])
            if combined_distro:
                for k in list(self.histograms.keys()):
                    print("drawing..",k)
                    self._draw_distribution(cur_ax,k,log=log)
                break
            else:
                k = self.histograms[list(self.histograms.keys())[ax[0]]]
                ymax, ymin = self._draw_distribution(cur_ax,k,log=log)
            cur_ax.set_ylim(ymin=ymin - 0.1*ymin,ymax=1.1*ymax)
        lgax = self.canvas.select_axes(-1)#most upper one
        lg = lgax.legend(**LoadConfig()['legend'])
        legendwidth = LoadConfig()
        legendwidth = legendwidth['legendwidth']
        lg.get_frame().set_linewidth(legendwidth)
        # plot the cuts
        if self.cuts:
            for ax in h_axes:
                self.indicate_cut(ax,arrow=True)
            for ax in r_axes + cu_axes:
                self.indicate_cut(ax,arrow=False)
        # cleanup
        leftplotedge = n.inf
        rightplotedge = -n.inf
        minplotrange = n.inf
        maxplotrange = -n.inf
        for h in list(self.histograms.values()):
            if not h.bincenters[h.bincontent > 0].sum():
                continue
            if h.bincenters[h.bincontent > 0][0] < leftplotedge:
                leftplotedge = h.bincenters[h.bincontent > 0][0]
            if h.bincenters[h.bincontent > 0][-1] > rightplotedge:
                rightplotedge = h.bincenters[h.bincontent > 0][-1]
            if min(h.bincontent[h.bincontent > 0]) < minplotrange:
                minplotrange = min(h.bincontent[h.bincontent > 0])
            if max(h.bincontent[h.bincontent > 0]) > maxplotrange:
                maxplotrange = max(h.bincontent[h.bincontent > 0])

        if log:
            maxplotrange *= 8
        else:
            maxplotrange *= 1.2
        if n.isfinite(leftplotedge):
            self.canvas.limit_xrange(xmin=leftplotedge)
        if n.isfinite(rightplotedge):
            self.canvas.limit_xrange(xmax=rightplotedge)
        for ax in h_axes:
            self.canvas.select_axes(ax[0]).set_ylim(ymax=maxplotrange,ymin=minplotrange)

        #if n.isfinite(minplotrange):
        #    self.canvas.limit_yrange(ymin=minplotrange - 0.1*minplotrange)
        #if n.isfinite(maxplotrange):
        #    self.canvas.limit_yrange(ymax=maxplotrange)
        self.canvas.eliminate_lower_yticks()
        # set the label on the lowest axes
        self.canvas.axes[0].set_xlabel(self.label)


    def add_legend(self,**kwargs):
        """
        Add a legend to the plot
        
        Keyword Args:
             will be passed to pylab.legend
        """
        if not kwargs:
            kwargs = {"bbox_to_anchor" :(0.,1.0, 1., .102), "loc" : 3, "ncol" :3, "mode" :"expand", "borderaxespad":0., "handlelength": 2,"numpoints" :1}
        self.canvas.global_legend(**kwargs)
 
