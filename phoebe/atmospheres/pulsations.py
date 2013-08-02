"""
Calculate the stellar surface displacements due to pulsations.

Main conventions:

    - :math:`\theta` is the colatitude, and runs between 0 (north pole) over
    :math:`\pi/2` (equator) to :math:`\pi` (south pole).
    - :math:`\phi` is the longitude, and runs between 0 and :math:`2\pi`.
    - :math:`m` is the azimuthal order of the mode. A positive :math:`m` means
    the mode is prograde (in the direction of the rotation), a negative
    value means the mode is retrograde (against the direction of rotation).

**Basic quantities:**

.. autosummary::

    radial
    colatitudinal
    longitudinal
    surface
    observables
    
**Helper functions:**

.. autosummary::
    
    sph_harm
    dsph_harm_dtheta
    dsph_harm_dphi
    norm_J
    norm_atlp1
    norm_atlm1
    legendre_

Main references: [Aerts1993]_, [Zima2006]_, [Townsend2003]_.

The surface displacements and perturbations of observables are computable in the
nonrotating case, slow rotation with first order Coriolis effects taken into
account (and slow rotation in the traditional approximation, as these are
just linear combinations of the nonrotating case).
"""
import logging
import numpy as np
from numpy import sqrt,pi,sin,cos,exp
from scipy.special import lpmv,legendre
from scipy.special import sph_harm as sph_harm0
from scipy.misc.common import factorial
from scipy.integrate import dblquad,quad
from scipy.spatial import Delaunay
from phoebe.utils import Ylm
from phoebe.utils import coordinates
from phoebe.units import constants

logger = logging.getLogger("PULS")
logger.addHandler(logging.NullHandler())

#{ Helper functions

def legendre_(l,m,x):
    r"""
    Associated Legendre function.
    
    For positive m, we define
    
    .. math::
    
        P_\ell^m(x) = (-1)^{m} (1-x^2)^{\frac{m}{2}} \frac{d^{m} P_\ell(x)}{dx^{m}}
        
    with :math:`x=\cos\theta` and :math:`P_\ell` the Legendre polynomial of
    degree :math:`\ell`. For negative :math:`m`, we use Eq. (3) from [Townsend2003]_:
    
    .. math::
    
        P_\ell^{-m}(x) = (-1)^m \frac{(\ell-m)!}{(\ell+m)!} P_l^m(x)
        
    **Example usage**
    
    >>> ls,x = [0,1,2,3,4,5],cos(linspace(0,pi,100))
    >>> check = 0
    >>> for l in ls:
    ...     for m in range(-l,l+1,1):
    ...         Ppos = legendre_(l,m,x)
    ...         Pneg = legendre_(l,-m,x)
    ...         mycheck = Pneg,(-1)**m * factorial(l-m)/factorial(l+m) * Ppos
    ...         check += sum(abs(mycheck[0]-mycheck[1])>1e-10)
    >>> print check
    0
    
    @param l: degree
    @type l: int
    @param m: order
    @type m: int
    @param x: argument of function (between -1 and 1)
    @type x: array
    """
    m_ = abs(m)
    legendre_poly = legendre(l)
    deriv_legpoly_ = legendre_poly.deriv(m=m_)
    deriv_legpoly = np.polyval(deriv_legpoly_,x)
    P_l_m = (-1)**m_ * (1.-x**2)**(m_/2.) * deriv_legpoly
    if m<0:
        P_l_m = (-1)**m_ * float(factorial(l-m_)/factorial(l+m_)) * P_l_m
    return P_l_m

def sph_harm(theta,phi,l=2,m=1):
    r"""
    Spherical harmonic.
    
    We use the definition and normalisation from [Townsend2003]_.
    
    .. math::
    
        Y_\ell^m(\theta,\phi) = (-1)^m \sqrt{\frac{2\ell+1}{4\pi}\frac{(\ell-m)!}{(\ell+m)!}} P_\ell^m(\cos\theta)e^{im\phi}
    
    with :math:`\theta` the colatitude and :math:`\phi` the longitude. The
    normalisation is such that
    
    .. math::
    
        \int_0^{2\pi}\int_0^\pi Y_\ell^m\bar{Y_{\ell'}^{m'}}\sin\theta d\theta d\phi = \delta_{\ell,\ell'}\delta_{m,m'}
        
    with :math:`\delta_{ij}` the Kronecker :math:`\delta`.
    
    This function should be memoized: once a spherical harmonic is computed, the
    result can stored in memory
    
    >>> theta,phi = np.mgrid[0:np.pi:20j,0:2*np.pi:40j]
    >>> Ylm20 = sph_harm(theta,phi,2,0)
    >>> Ylm21 = sph_harm(theta,phi,2,1)
    >>> Ylm22 = sph_harm(theta,phi,2,2)
    >>> Ylm2_2 = sph_harm(theta,phi,2,-2)
    >>> p = plt.figure()
    >>> p = plt.gcf().canvas.set_window_title('test of function <sph_harm>')
    >>> p = plt.subplot(221);p = plt.title('l=2,m=0');p = plt.imshow(Ylm20.real,cmap=plt.cm.RdBu)
    >>> p = plt.subplot(222);p = plt.title('l=2,m=1');p = plt.imshow(Ylm21.real,cmap=plt.cm.RdBu)
    >>> p = plt.subplot(223);p = plt.title('l=2,m=2');p = plt.imshow(Ylm22.real,cmap=plt.cm.RdBu)
    >>> p = plt.subplot(224);p = plt.title('l=2,m=-2');p = plt.imshow(Ylm2_2.real,cmap=plt.cm.RdBu)
    
    .. image:: images/pulsations_sph_harm.png
       :width: 600px
       :align: center
       
    """
    #factor = (-1)**((m+abs(m))/2.) * sqrt( (2*l+1.)/(4*pi) * float(factorial(l-abs(m))/factorial(l+abs(m))))
    #Plm = legendre_(l,np.abs(m),cos(theta))
    #return factor*Plm*exp(1j*m*phi)
    #-- the above seems to be unstable for l~>30, but below is equivalent to:
    #if np.abs(m)>l:
    #    return np.zeros_like(phi)
    #return -sph_harm0(m,l,phi,theta)
    #-- due to vectorization, this seemed to be incredibly slow though. third
    #   try:
    if np.abs(m)>l:
        return np.zeros_like(phi)
    return -Ylm.Ylm(l,m,phi,theta)

def orthonormal(theta,phi,l1=2,m1=1,l2=2,m2=1):
    r"""
    Test the othornomal property of the spherical harmonic.
    
    According to [Townsend2003]_:
    
    .. math::
    
        \int_0^{2\pi}\int_0^\pi Y_\ell^m\bar{Y_{\ell'}^{m'}}\sin\theta d\theta d\phi = \delta_{\ell,\ell'}\delta_{m,m'}      
        
    with :math:`\delta_{ij}` the Kronecker :math:`\delta`.
    
    This can be checked via:
    
    >>> l1,m1 = 2,1 
    >>> l2,m2 = 2,0 
    >>> I1,e_I1 = scipy.integrate.dblquad(orthonormal,0,2*np.pi,lambda x:0, lambda x:np.pi,args=(l1,m1,l1,m1)) 
    >>> I2,e_I2 = scipy.integrate.dblquad(orthonormal,0,2*np.pi,lambda x:0, lambda x:np.pi,args=(l1,m1,l2,m2)) 
    >>> print '%.6f %.6f'%(I1,I2) 
    1.000000 0.000000
    
    (and yes, the first argument goes to :math:`2\pi`, this is the longitude).
 
    """
    inside = sph_harm(theta,phi,l1,m1) * sph_harm(theta,phi,l2,m2).conjugate() 
    return inside.real*np.sin(theta)

def dsph_harm_dtheta(theta,phi,l=2,m=1):
    r"""
    Derivative of spherical harmonic wrt colatitude.
    
    Using :math:`Y_\ell^m(\theta,\phi)`.
    
    .. math::
        
        \sin\theta\frac{dY}{d\theta} = \ell J_{\ell+1}^m Y_{\ell+1}^m - (\ell+1) J_\ell^m  Y_{\ell-1,m}
        
    E.g.: Phd thesis of Joris De Ridder
    
    .. image:: images/pulsations_dsph_harm_dtheta01.png
       :width: 600px
       :align: center
       
    .. image:: images/pulsations_dsph_harm_dtheta02.png
       :width: 600px
       :align: center
       
    """
    if abs(m)>l:
        Y = 0.
    else:
        factor = 1./sin(theta)
        term1 = l     * norm_J(l+1,m) * sph_harm(theta,phi,l+1,m)
        term2 = (l+1) * norm_J(l,m)   * sph_harm(theta,phi,l-1,m)
        Y = factor * (term1 - term2)
    return Y

def dsph_harm_dphi(theta,phi,l=2,m=1):
    r"""
    Derivative of spherical harmonic wrt longitude.
    
    Using :math:`Y_\ell^m(\theta,\phi)`.
    
    .. math::
        
        \frac{dY}{d\phi} = imY
    
    .. image:: images/pulsations_dsph_harm_dphi01.png
       :width: 600px
       :align: center
       
    .. image:: images/pulsations_dsph_harm_dphi02.png
       :width: 600px
       :align: center
    
    """
    return 1j*m*sph_harm(theta,phi,l,m)
    

def norm_J(l,m):
    r"""
    Normalisation factor
    
    .. math::
    
        J = \sqrt{ \frac{\ell^2-m^2}{4\ell^2-1}}
    
    if :math:`|m|<\ell`, else :math:`J=0`.
    """
    if abs(m)<l:
        J = sqrt( (l**2.-m**2.)/(4*l**2-1.))
    else:
        J = 0.
    return J

def norm_atlp1(l,m,spin,k):
    r"""
    Amplitude of toroidal component.
    
    .. math::
    
        a_{t,\ell+1} = a_{s,\ell} \frac{\Omega}{\omega}\frac{\ell-|m|+1}{\ell+1}\frac{2}{2\ell+1}(1-\ell k)
    
    Here, :math:`\Omega` is the angular rotation frequency of the star and
    :math:`\omega` the angular pulsation frequency. Thus,
    
    .. math::
    
        s = \frac{\Omega}{\omega}
        
    is the spin parameter.
    
    We neglect the factor :math:`a_{s,\ell}` because this factor is
    present in all the components, so we apply it afterwards.
    
    """
    return spin * (l-abs(m)+1.)/(l+1.) * 2./(2*l+1.) * (1-l*k)

def norm_atlm1(l,m,spin,k):
    r"""
    Amplitude of toroidal component.
    
    .. math::
    
        a_{t,\ell-1} = a_{s,\ell} \frac{\Omega}{\omega}\frac{\ell+|m|}{\ell}\frac{2}{2\ell+1}(1+(\ell+1) k)
    
    Here, :math:`\Omega` is the angular rotation frequency of the star and
    :math:`\omega` the angular pulsation frequency. Thus,
    
    .. math::
    
        s = \frac{\Omega}{\omega}
        
    is the spin parameter.
    
    We neglect the factor :math:`a_{s,\ell}` because this factor is
    present in all the components, so we apply it afterwards.
    
    """
    return spin * (l+abs(m))/l * 2./(2*l+1.) * (1 + (l+1)*k)
    
#}

#{ Displacement fields

def radial(theta,phi,l,m,freq,phase,t):
    r"""
    Radial displacement.
    
    See [Zima2006]_.
    
    t in period units (t=1/freq equals 2pi radians, end of one cycle)
    
    .. math::
    
        \xi_r & = Y_\ell^m(\theta,\phi) e^{2\pi i (ft+\phi)}
    """
    return sph_harm(theta,phi,l,m) * exp(1j*2*pi*(freq*t+phase))

def colatitudinal(theta,phi,l,m,freq,phase,t,spin,k):
    r"""
    Colatitudinal displacement.
    
    See [Zima2006]_.
    
    .. math::
    
        \xi_\theta & = a_{s,l}       k          \frac{\partial Y^m_\ell}{\partial\theta}  e^{2\pi i (ft+\phi)} \\ 
           &  +   \frac{a_{t,l+1}}{\sin\theta} \frac{\partial Y^m_{\ell+1}}{\partial\phi} e^{2\pi i (ft+\phi+\frac{1}{4})} \\
           &  +   \frac{a_{t,l-1}}{\sin\theta} \frac{\partial Y^m_{\ell-1}}{\partial\phi} e^{2\pi i (ft+\phi-\frac{1}{4})}
    
    Here, :math:`a_{s,l}` is the amplitude of the spheroidal component and
    :math:`a_{t,l+1}` and :math:`a_{t,l-1}` are those of the toroidal components.
    Also, :math:`k` is the ratio of the amplitudes of the horizontal to vertical
    component.
    
    @param theta: colatitude
    @type theta: float or array
    @param phi: longitude
    @type phi: float or array
    @param l: mode degree
    @type l: int
    @param m: mode order
    @type m: int
    @param freq: cyclical frequency (e.g. cy/d)
    @type freq: float
    @param phase: cyclical phase (e.g. between 0 and 1)
    @type phase: float
    @param t: time
    @type t: float
    @param spin: spin parameter, :math:`\Omega/\omega`.
    @type spin: float
    @param k: amplitude ratio of horizontal to vertical component
    @type k: float
    """
    term1 = k * dsph_harm_dtheta(theta,phi,l,m)                                     * exp(1j*2*pi*(freq*t+phase))
    term2 = norm_atlp1(l,m,spin,k) / sin(theta) * dsph_harm_dphi(theta,phi,l+1,m)  * exp(1j*2*pi*(freq*t+phase + 0.25))
    term3 = norm_atlm1(l,m,spin,k) / sin(theta) * dsph_harm_dphi(theta,phi,l-1,m)  * exp(1j*2*pi*(freq*t+phase - 0.25))
    return term1 + term2 + term3

def longitudinal(theta,phi,l,m,freq,phase,t,spin,k):
    r"""
    Longitudinal displacement.
    
    See [Zima2006]_.
    
    .. math::
    
        \xi_\phi & = a_{s,l} \frac{k}{\sin\theta} \frac{\partial Y^m_\ell}{\partial\phi}  e^{2\pi i (ft+\phi)} \\ 
           &  -   a_{t,l+1}                       \frac{\partial Y^m_{\ell+1}}{\partial\theta} e^{2\pi i (ft+\phi+\frac{1}{4})} \\
           &  -   a_{t,l-1}                       \frac{\partial Y^m_{\ell-1}}{\partial\theta} e^{2\pi i (ft+\phi-\frac{1}{4})}
    
    Here, :math:`a_{s,l}` is the amplitude of the spheroidal component and
    :math:`a_{t,l+1}` and :math:`a_{t,l-1}` are those of the toroidal components.
    Also, :math:`k` is the ratio of the amplitudes of the horizontal to vertical
    component.
    
    @param theta: colatitude
    @type theta: float or array
    @param phi: longitude
    @type phi: float or array
    @param l: mode degree
    @type l: int
    @param m: mode order
    @type m: int
    @param freq: cyclical frequency (e.g. cy/d)
    @type freq: float
    @param phase: cyclical phase (e.g. between 0 and 1)
    @type phase: float
    @param t: time
    @type t: float
    @param spin: spin parameter, :math:`\Omega/\omega`.
    @type spin: float
    @param k: amplitude ratio of horizontal to vertical component
    @type k: float
    """
    term1 = k /sin(theta) * dsph_harm_dphi(theta,phi,l,m)*exp(1j*2*pi*(freq*t+phase))
    term2 = -norm_atlp1(l,m,spin,k) * dsph_harm_dtheta(theta,phi,l+1,m)*exp(1j*2*pi*(freq*t+phase+0.25))
    term3 = -norm_atlm1(l,m,spin,k) * dsph_harm_dtheta(theta,phi,l-1,m)*exp(1j*2*pi*(freq*t+phase-0.25))
    return term1 + term2 + term3

def surface(radius,theta,phi,t,l,m,freq,phases,spin,k,asl):
    """
    Compute surface displacements.
    
    Here we norm with the factor :math:`\sqrt{4\pi}` such that the amplitude
    :math:`a_{s,\ell}` means the fractional radius amplitude for a radial mode.
    
    See [Zima2006]_.
    """
    ksi_r = 0.
    ksi_theta = 0.
    ksi_phi = 0.
    velo_r = 0.
    velo_theta = 0.
    velo_phi = 0.
    zero = np.zeros_like(theta,complex)
    
    for il,im,ifreq,iphase,ispin,ik,iasl in zip(l,m,freq,phases,spin,k,asl):
        #-- radial perturbation
        ksi_r_ = iasl*radius*sqrt(4*pi)*radial(theta,phi,il,im,ifreq,iphase,t)
        #-- add to the total perturbation of the radius and velocity
        ksi_r += ksi_r_
        velo_r += 1j*2*pi*ifreq*ksi_r_
        #-- colatitudinal and longitudonal perturbation when l>0
        norm = sqrt(4*pi)
        if il>0:
            ksi_theta_ = iasl*norm*colatitudinal(theta,phi,il,im,ifreq,iphase,t,ispin,ik)
            ksi_phi_   = iasl*norm* longitudinal(theta,phi,il,im,ifreq,iphase,t,ispin,ik)
            ksi_theta += ksi_theta_
            ksi_phi += ksi_phi_
            velo_theta += 1j*2*pi*ifreq*ksi_theta_
            velo_phi   += 1j*2*pi*ifreq*ksi_phi_
        else:
            ksi_theta += zero
            ksi_phi += zero
            velo_theta += zero
            velo_phi += zero
    
    return (radius+ksi_r.real),\
           (theta + ksi_theta.real),\
           (phi + ksi_phi.real),\
           velo_r.real,velo_theta.real,velo_phi.real

def observables(radius,theta,phi,teff,logg,t,l,m,freq,phases,spin,k,asl,delta_T,delta_g):
    """
    Good defaults:
    
    spin = 0.1
    k = 1.0
    asl = 0.2
    radius = 1.
    delta_T=0.05+0j
    delta_g=0.0001+0.5j
    """
    gravity = 10**(logg-2)
    ksi_r = 0.
    ksi_theta = 0.
    ksi_phi = 0.
    velo_r = 0.
    velo_theta = 0.
    velo_phi = 0.
    ksi_grav = 0.
    ksi_teff = 0.
    zero = np.zeros_like(phi,complex)
    
    for il,im,ifreq,iphase,ispin,ik,iasl,idelta_T,idelta_g in \
       zip(l,m,freq,phases,spin,k,asl,delta_T,delta_g):
        rad_part = radial(theta,phi,il,im,ifreq,iphase,t)
        ksi_r_ = iasl*sqrt(4*pi)*rad_part#radial(theta,phi,il,im,ifreq,t)
        ksi_r += ksi_r_*radius
        velo_r += 1j*2*pi*ifreq*ksi_r_*radius
        if il>0:
            ksi_theta_ = iasl*sqrt(4*pi)*colatitudinal(theta,phi,il,im,ifreq,iphase,t,ispin,ik)
            ksi_phi_ = iasl*sqrt(4*pi)*longitudinal(theta,phi,il,im,ifreq,iphase,t,ispin,ik)
            ksi_theta += ksi_theta_
            ksi_phi += ksi_phi_
            velo_theta += 1j*2*pi*ifreq*ksi_theta_
            velo_phi += 1j*2*pi*ifreq*ksi_phi_
        else:
            ksi_theta += zero
            ksi_phi += zero
            velo_theta += zero
            velo_phi += zero
        ksi_grav += idelta_g*rad_part*gravity
        ksi_teff += idelta_T*rad_part*teff   
        
    return (radius+ksi_r.real),\
           (theta + ksi_theta.real),\
           (phi + ksi_phi.real),\
           velo_r.real,velo_theta.real,velo_phi.real,\
           (teff + ksi_teff.real),\
           np.log10(gravity+ksi_grav.real)+2








#{ Phoebe specific interface

def add_pulsations(self,time=None):
    if time is None:
        time = self.time
    
    #-- relevant stellar parameters
    try:
        rotfreq = 1./self.params['star'].request_value('rotperiod','d')
        R = self.params['star'].request_value('radius','m')
        M = self.params['star'].request_value('mass','kg')    
    except:
        logger.critical('Cannot figure out stellar parameters')
        rotfreq = 20.
        R = constants.Rsol
        M = constants.Msol
    
    #-- prepare extraction of pulsation parameters
    freqs = []
    freqs_Hz = []
    phases = []
    ampls = []
    ls = []
    ms = []
    deltaTs = []
    deltags = []
    ks = []
    spinpars = []
    
    #-- extract pulsation parameters, depending on their scheme
    for i,pls in enumerate(self.params['puls']):
        #-- extract information on the mode
        scheme = pls.get_value('scheme')
        l = pls.get_value('l')
        m = pls.get_value('m')
        k_ = pls.get_value('k')
        freq = pls.get_value('freq','cy/d')
        freq_Hz = freq / (24.*3600.)
        ampl = pls.get_value('ampl')
        deltaT = pls.get_value('amplteff')*np.exp(1j*2*pi*pls.get_value('phaseteff'))
        deltag = pls.get_value('amplgrav')*np.exp(1j*2*pi*pls.get_value('phasegrav'))
        phase = pls.get_value('phase')
        omega = 2*pi*freq_Hz
        k0 = constants.GG*M/omega**2/R**3    
        #-- if the pulsations are defined in the scheme of the traditional
        #   approximation, we need to expand the single frequencies into many.
        #   indeed, the traditional approximation approximates a mode as a
        #   linear combination of modes with different degrees.        
        if scheme=='traditional approximation':
            #-- extract some info on the B-vector
            bvector = pls.get_value('trad_coeffs')
            N = len(bvector)
            ljs = np.arange(N)
            for lj,Bjk in zip(ljs,bvector):
                if Bjk==0: continue
                #if lj>50: continue
                freqs.append(freq)
                freqs_Hz.append(freq_Hz)
                ampls.append(Bjk*ampl)
                phases.append(phase)
                ls.append(lj)
                ms.append(m)
                deltaTs.append(Bjk*deltaT)
                deltags.append(Bjk*deltag)
                ks.append(k0)
                spinpars.append(0.) # not applicable
        elif scheme=='nonrotating' or scheme=='coriolis':
            if scheme=='coriolis' and l>0:
                spinpar = rotfreq/freq
                Cnl = pls.get_value('ledoux_coeff')
                k = k0 + 2*m*spinpar*((1.+k0)/(l**2+l)-Cnl)
                logger.info('puls: adding Coriolis (rot=%.3f cy/d) effects for freq %.3f cy/d (l,m=%d,%d): ah/ar=%.3f, spin=%.3f'%(rotfreq,freq,l,m,k,spinpar))
            else:
                spinpar = 0.
                k = k_#k0
                logger.info('puls: no Coriolis (rot=%.3f cy/d) effects for freq %.3f cy/d (l,m=%d,%d): ah/ar=%.3f, spin=0'%(rotfreq,freq,l,m,k))
            freqs.append(freq)
            freqs_Hz.append(freq_Hz)
            ampls.append(ampl)
            phases.append(phase)
            ls.append(l)
            ms.append(m)
            deltaTs.append(deltaT)
            deltags.append(deltag)
            ks.append(k)
            spinpars.append(spinpar)
        else:
            raise ValueError('Pulsation scheme {} not recognised'.format(scheme))
        
    #-- then add displacements due to pulsations. When computing the centers,
    #   we also add the information on teff and logg
    #index = np.array([2,0,1])
    #index_inv = np.array([1,2,0])
    index = np.array([1,0,2])
    index_inv = np.array([1,0,2])
    puls_incl = self.params['puls'][0].get_value('incl','rad')
    r1,phi1,theta1 = coordinates.cart2spher_coord(*self.mesh['_o_triangle'][:,0:3].T[index])
    r2,phi2,theta2 = coordinates.cart2spher_coord(*self.mesh['_o_triangle'][:,3:6].T[index])
    r3,phi3,theta3 = coordinates.cart2spher_coord(*self.mesh['_o_triangle'][:,6:9].T[index])
    r4,phi4,theta4 = coordinates.cart2spher_coord(*self.mesh['_o_center'].T[index])
    r1,theta1,phi1,vr1,vth1,vphi1 = surface(r1,theta1,phi1,time,ls,ms,freqs,phases,spinpars,ks,ampls)        
    r2,theta2,phi2,vr2,vth2,vphi2 = surface(r2,theta2,phi2,time,ls,ms,freqs,phases,spinpars,ks,ampls)
    r3,theta3,phi3,vr3,vth3,vphi3 = surface(r3,theta3,phi3,time,ls,ms,freqs,phases,spinpars,ks,ampls)
    r4,theta4,phi4,vr4,vth4,vphi4,teff,logg = observables(r4,theta4,phi4,
                 self.mesh['teff'],self.mesh['logg'],time,ls,ms,freqs,phases,
                 spinpars,ks,ampls,deltaTs,deltags)
    self.mesh['triangle'][:,0:3] = np.array(coordinates.spher2cart_coord(r1,phi1,theta1))[index_inv].T
    self.mesh['triangle'][:,3:6] = np.array(coordinates.spher2cart_coord(r2,phi2,theta2))[index_inv].T
    self.mesh['triangle'][:,6:9] = np.array(coordinates.spher2cart_coord(r3,phi3,theta3))[index_inv].T
    #for iref in ref:
    #    ps,iref = self.get_parset(iref)
    #    self.mesh['velo_%s_'%(iref)] += np.array(coordinates.spher2cart((r4,phi4,theta4),(vr4,vphi4,vth4)))[index_inv].T
    self.mesh['velo___bol_'] += np.array(coordinates.spher2cart((r4,phi4,theta4),(vr4,vphi4,vth4)))[index_inv].T
    self.mesh['center'] = np.array(coordinates.spher2cart_coord(r4,phi4,theta4))[index_inv].T
    logger.info("puls: before {}<teff<{} (deltaT={})".format(self.mesh['teff'].min(), self.mesh['teff'].max(),deltaTs))
    self.mesh['teff'] = teff
    self.mesh['logg'] = logg
    logger.info("puls: computed pulsational displacement, velocity and teff/logg field")
    logger.info("puls: after {}<teff<{}".format(self.mesh['teff'].min(), self.mesh['teff'].max()))


#}