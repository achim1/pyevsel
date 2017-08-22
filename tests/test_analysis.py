import pytest
import numpy as np
from HErmes.analysis import calculus

def test_opening_angle():

    z1 = np.zeros(5)
    a1 = np.zeros(5)

    z2 = (np.pi/2)*np.ones(5)
    a2 = np.zeros(5)

    z3 = -(np.pi/2)*np.ones(5)
    

    print calculus.opening_angle(0,0,np.pi/2,0)     
    print calculus.opening_angle(z1,a1,z2,a2)
    assert (calculus.opening_angle(z1, a1, z1, a1)).sum() == 0
    assert (calculus.opening_angle(z1, a1, z2, a2)).sum() == 5*90.
    assert (calculus.opening_angle(z2, a2, z3, a2)).sum() == 5*180