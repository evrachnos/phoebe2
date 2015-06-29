"""
Simple Binary Animation
========================

Last updated: ***time***

This example shows more advanced figure creation using the bundle to create an animation of the binary in time

Initialisation
--------------

"""
# First we'll import phoebe and create a logger



import phoebe
import numpy as np
import matplotlib.pyplot as plt
import time
logger = phoebe.get_basic_logger()


# Bundle preparation
# ------------------

b = phoebe.Bundle()
b['atm@primary'] = 'blackbody'
b['atm@secondary'] = 'blackbody'
b['incl'] = 88.
b['syncpar@primary'] = 1.2
b['q'] = 0.8

# Create synthetic model
# ---------------------

b.lc_fromarrays(time=np.arange(0,1,0.01), dataref='lc')
b.rv_fromarrays(time=np.arange(0,1,0.01), objref=['primary','secondary'], dataref='rvs')
b.sp_fromarrays(time=np.arange(0,1,0.01), wavelength=np.linspace(399,401,500), dataref='spectra')

b.run_compute('preview')


# Plotting
# ---------


b.attach_plot_mesh(dataref='lc', select='teff', axesref='mesh', axesloc=(2,2,1), xlim=(-7,7), ylim=(-7,7), figref='fig')

b.attach_plot_syn('lc', fmt='k-', axesref='lc', axesloc=(2,2,2), highlight_fmt='ko')

b.attach_plot_syn('rvs@primary', fmt='b-', axesref='rvs', axesloc=(2,2,4), highlight_fmt='bo')
b.attach_plot_syn('rvs@secondary', fmt='r-', highlight_fmt='ro')

b.attach_plot_syn('spectra', fmt='k-', axesref='spectra', ylim=(0.955,1.005), axesloc=(2,2,3))

b.draw('fig', time=b['time@spectra@spsyn'], fname='binary_rv.gif', clf=True, tight_layout=True)

"""
.. image:: images_tut/binary_rv.gif
   :width: 750px    
"""
