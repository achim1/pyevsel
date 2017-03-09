import pytest

import pyevsel.plotting as plt
import pyevsel.plotting.plotting as pltplt

from pyevsel.plotting import plotcolors as pc
from pyevsel.plotting import canvases as cv

@pytest.fixture(scope='session')
def png_file(tmpdir_factory):
    png = tmpdir_factory.mktemp('data').join("testplot.png")
    return png

def colordictfactory():
    testdict = {1 : "red", 2: "blue"}
    return testdict
    assert config is not None 


def test_plotcolors_ColorDict():
    cd = pc.ColorDict()
    testdict = colordictfactory()
    cd.update(testdict)
    assert cd[1] == "red"
    assert cd["nan"] == "nan"


def test_plotcolors_get_color_palette():
    cd = pc.get_color_palette()
    assert isinstance(cd, pc.ColorDict)


def test_YStackedCanvas(png_file):
    import pylab as p
    import os.path

    canvas = cv.YStackedCanvas()
    assert isinstance(canvas.figure, p.Figure)
    xlim = (1, 10)
    ylim = (10, 100)
    canvas.limit_xrange(*xlim)
    assert canvas.axes[0].get_xlim() == pytest.approx(xlim, abs=1e-2)
    canvas.limit_yrange(*ylim)
    assert canvas.axes[0].get_ylim() == pytest.approx(ylim, abs=1e-2)
    canvas.eliminate_lower_yticks()
    canvas.global_legend()
    pngfilename, path = os.path.split(str(png_file.realpath()))
    canvas.save(path, pngfilename)
    assert os.path.exists(canvas.png_filename)
    canvas.show()


def test_create_arrow():
    import pylab as p
    import matplotlib

    fig = p.figure()
    ax = fig.gca()
    ax = pltplt.create_arrow(ax, 1, 1, .2, .2, 5,\
                 width = .1, shape="right",\
                 fc="k", ec="k",\
                 alpha=1., log=False)
    assert len(ax.artists) == 1
    assert isinstance(ax.artists[0], matplotlib.patches.FancyArrow)

def test_VariableDistributionPlot():
    pltplt.VariableDistributionPlot()




