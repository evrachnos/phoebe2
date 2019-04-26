"""Parameters and ParameterSets.

General logic for all Parameters and ParameterSets which makeup the overall
framework of the PHOEBE 2.0 frontend.
"""

from phoebe.constraints.expression import ConstraintVar
# from phoebe.constraints import builtin
from phoebe.parameters.twighelpers import _uniqueid_to_uniquetwig
from phoebe.parameters.twighelpers import _twig_to_uniqueid
from phoebe.frontend import tabcomplete
from phoebe.dependencies import nparray
from phoebe.utils import parse_json

import sys
import random
import string
import functools
import itertools
import re
import sys
import os
import difflib
import time
import types
from collections import OrderedDict
from fnmatch import fnmatch
from copy import deepcopy
import readline
import numpy as np

import json
try:
    import ujson
except ImportError:
    _can_ujson = False
else:
    _can_ujson = True

import webbrowser
from datetime import datetime

if os.getenv('PHOEBE_ENABLE_EXTERNAL_JOBS', 'FALSE').upper() == 'TRUE':
    try:
        import requests
    except ImportError:
        _can_requests = False
    else:
        _can_requests = True
else:
    _can_requests = False

if sys.version_info[0] == 3:
  unicode = str


# things needed to be imported at top-level for constraints to solve:
from numpy import sin, cos, tan, arcsin, arccos, arctan, sqrt

from phoebe import u
from phoebe import conf
from phoebe import list_passbands, list_installed_passbands, list_online_passbands, download_passband

if os.getenv('PHOEBE_ENABLE_SYMPY', 'TRUE').upper() == 'TRUE':
    try:
        import sympy
    except ImportError:
        _use_sympy = False
    else:
        _use_sympy = True
else:
    _use_sympy = False

_use_sympy = False
_is_server = False

if os.getenv('PHOEBE_ENABLE_PLOTTING', 'TRUE').upper() == 'TRUE':
    try:
        from phoebe.dependencies import autofig
    except (ImportError, TypeError):
        _use_autofig = False
    else:
        _use_autofig = True
else:
    _use_autofig = False

import logging
logger = logging.getLogger("PARAMETERS")
logger.addHandler(logging.NullHandler())


_parameter_class_that_require_bundle = ['HistoryParameter', 'TwigParameter',
                                        'ConstraintParameter', 'JobParameter']

_meta_fields_twig = ['time', 'qualifier', 'history', 'feature', 'component',
                     'dataset', 'constraint', 'compute', 'model', 'fitting',
                     'feedback', 'plugin', 'kind',
                     'context']

_meta_fields_all = _meta_fields_twig + ['twig', 'uniquetwig', 'uniqueid']
_meta_fields_filter = _meta_fields_all + ['constraint_func', 'value']

_contexts = ['history', 'system', 'component', 'feature',
             'dataset', 'constraint', 'compute', 'model', 'fitting',
             'feedback', 'plugin', 'setting']

# define a list of default_forbidden labels
# an individual ParameterSet may build on this list with components, datasets,
# etc for labels
# components and datasets should also forbid this list
_forbidden_labels = deepcopy(_meta_fields_all)

# forbid all "contexts"
_forbidden_labels += _contexts
_forbidden_labels += ['lc', 'lc_dep', 'lc_syn',
                      'rv', 'rv_dep', 'rv_syn',
                      'lp', 'lp_dep', 'lp_syn',
                      'sp', 'sp_dep', 'sp_syn',
                      'orb', 'orb_dep', 'orb_syn',
                      'mesh', 'mesh_dep', 'mesh_syn']

# forbid all "methods"
_forbidden_labels += ['value', 'adjust', 'prior', 'posterior', 'default_unit',
                      'unit', 'timederiv', 'visible_if', 'description', 'result']
# _forbidden_labels += ['parent', 'child']
_forbidden_labels += ['protomesh', 'pbmesh']
_forbidden_labels += ['component']
_forbidden_labels += ['bol']



# we also want to forbid any possible qualifiers
# from system:
_forbidden_labels = ['t0', 'ra', 'dec', 'epoch', 'distance', 'vgamma']

# from setting:
_forbidden_labels = ['phoebe_version', 'log_history', 'dict_filter', 'dict_set_all']

# from dataset:
_forbidden_labels = ['times', 'fluxes', 'sigmas', 'ld_func', 'ld_coeffs',
                     'passband', 'intens_weighting', 'pblum_ref', 'pblum', 'l3',
                     'exptime', 'rvs', 'wavelengths',
                     'flux_densities', 'profile_func', 'profile_rest', 'profile_sv',
                     'Ns', 'time_ecls', 'time_ephems', 'etvs',
                     'us', 'vs', 'ws', 'vus', 'vvs', 'vws',
                     'include_times', 'columns',
                     'uvw_elements', 'xyz_elements',
                     'pot', 'rpole', 'volume',
                     'xs', 'ys', 'zs', 'vxs', 'vys', 'vzs',
                     'nxs', 'nys', 'nzs', 'nus', 'nvs', 'nws',
                     'areas', 'rs', 'rprojs', 'loggs', 'teffs', 'mus',
                     'visible_centroids', 'visibilities',
                     'intensities', 'normal_intensities', 'abs_normal_intensities',
                     'boost_factors', 'ldint', 'ptfarea', 'pblum', 'abs_pblum']

# from compute:
_forbidden_labels += ['enabled', 'dynamics_method', 'ltte',
                      'gr', 'stepsize', 'integrator',
                      'irrad_method', 'boosting_method', 'mesh_method', 'distortion_method',
                      'ntriangles',
                      'mesh_offset', 'mesh_init_phi', 'horizon_method', 'eclipse_method',
                      'atm', 'lc_method', 'rv_method', 'fti_method', 'etv_method',
                      'gridsize', 'refl_num', 'ie',
                      'stepsize', 'orbiterror', 'ringsize'
                      ]

# from feature:
_forbidden_labels += ['colat', 'long', 'radius', 'relteff',
                      'radamp', 'freq', 'l', 'm', 'teffext'
                      ]

# ? and * used for wildcards in twigs
_twig_delims = ' \t\n`~!#$%^&)-=+]{}\\|;,<>/:'


_singular_to_plural = {'time': 'times', 'flux': 'fluxes', 'sigma': 'sigmas',
                       'rv': 'rvs', 'flux_density': 'flux_densities',
                       'time_ecl': 'time_ecls', 'time_ephem': 'time_ephems', 'N': 'Ns',
                       'x': 'xs', 'y': 'ys', 'z': 'zs', 'vx': 'vxs', 'vy': 'vys',
                       'vz': 'vzs', 'nx': 'nxs', 'ny': 'nys', 'nz': 'nzs',
                       'u': 'us', 'v': 'vs', 'w': 'ws', 'vu': 'vus', 'vv': 'vvs',
                       'vw': 'vws', 'nu': 'nus', 'nv': 'nvs', 'nw': 'nws',
                       'cosbeta': 'cosbetas', 'logg': 'loggs', 'teff': 'teffs',
                       'r': 'rs', 'rproj': 'rprojs', 'mu': 'mus',
                       'visibility': 'visibilities'}
_plural_to_singular = {v:k for k,v in _singular_to_plural.items()}

def send_if_client(fctn):
    """Intercept and send to the server if bundle is in client mode."""
    @functools.wraps(fctn)
    def _send_if_client(self, *args, **kwargs):
        fctn_map = {'set_quantity': 'set_value'}
        b = self._bundle
        if b is not None and b.is_client:
            # TODO: self._filter???
            # TODO: args???
            method = fctn_map.get(fctn.__name__, fctn.__name__)
            d = self._filter if hasattr(self, '_filter') \
                else {'twig': self.twig}
            d['bundleid'] = b._bundleid
            for k, v in kwargs.items():
                d[k] = v

            logger.info('emitting to {}({}) to server'.format(method, d))
            b._socketio.emit(method, d)

            if fctn.__name__ in ['run_compute', 'run_fitting']:
                # then we're expecting a quick response with an added jobparam
                # let's add that now
                self._bundle.client_update()
        else:
            return fctn(self, *args, **kwargs)
    return _send_if_client


def update_if_client(fctn):
    """Intercept and check updates from server if bundle is in client mode."""
    @functools.wraps(fctn)
    def _update_if_client(self, *args, **kwargs):
        b = self._bundle
        if b is None or not hasattr(b, 'is_client'):
            return fctn(self, *args, **kwargs)
        elif b.is_client and \
                (b._last_client_update is None or
                (datetime.now() - b._last_client_update).seconds > 1):

            b.client_update()
        return fctn(self, *args, **kwargs)
    return _update_if_client


def _uniqueid(n=30):
    """Return a unique string with length n.

    :parameter int N: number of character in the uniqueid
    :return: the uniqueid
    :rtype: str
    """
    return ''.join(random.SystemRandom().choice(
                   string.ascii_uppercase + string.ascii_lowercase)
                   for _ in range(n))

def _is_unit(unit):
    return isinstance(unit, u.Unit) or isinstance(unit, u.CompositeUnit) or isinstance(unit, u.IrreducibleUnit)

def _value_for_constraint(item, constraintparam=None):
    if getattr(item, 'keep_in_solar_units', False):
        # for example, constants defined in the constraint itself can have
        # this attribute added to force them to stay in solar units in the constraint
        return item.value
    elif constraintparam is not None and constraintparam.in_solar_units:
        return u.to_solar(item).value
    else:
        return item.si.value


def parameter_from_json(dictionary, bundle=None):
    """Load a single parameter from a JSON dictionary.

    Arguments
    ----------
    * `parameter` (dict): the dictionarry containing the parameter information
    * `bundle` (<phoebe.frontend.bundle.Bundle>, optional): the bundle object
        that the parameter will be attached to

    Returns
    --------
    * an instantiated <phoebe.parameters.Parameter> object>
    """
    if isinstance(dictionary, str):
        dictionary = json.loads(dictionary, object_pairs_hook=parse_json)

    classname = dictionary.pop('Class')

    if classname not in _parameter_class_that_require_bundle:
        bundle = None

    # now let's do some dirty magic and get the actual classitself
    # from THIS module.  __name__ is a string to lookup this module
    # from the sys.modules dictionary
    cls = getattr(sys.modules[__name__], classname)

    return cls._from_json(bundle, **dictionary)

def _instance_in(obj, *types):
    for typ in types:
        if isinstance(obj, typ):
            return True

    return False


class ParameterSet(object):
    """ParameterSet.

    The ParameterSet is an abstract list of Parameters which can then be
    filtered into another ParameterSet or Parameter by filtering on set tags of
    the Parameter or on "twig" notation (a single string using '@' symbols to
    separate these same tags).
    """

    def __init__(self, params=[]):
        """Initialize a new ParameterSet.

        Arguments
        ---------
        * `params` (list, optional, default=[]): list of
            <phoebe.parameters.Parameter> objects.

        Returns:
        --------
        * an instantiated <phoebe.parameters.ParameterSet>.
        """
        self._bundle = None
        self._filter = {}

        if len(params) and not isinstance(params[0], Parameter):
            # then attempt to load as if json
            self._params = []
            for param_dict in params:
                self._params += [parameter_from_json(param_dict, self)]

            for param in self._params:
                param._bundle = self
        else:
            self._params = params

        self._qualifier = None
        self._time = None
        self._history = None
        self._component = None
        self._dataset = None
        self._constraint = None
        self._compute = None
        self._model = None
        self._fitting = None
        self._feedback = None
        self._plugin = None
        self._kind = None
        self._context = None

        # just as a dummy, this'll be filled and handled by to_dict()
        self._next_field = 'key'

        self._set_meta()

        # force an update to _next_field
        self.to_dict()

        # set tab completer
        readline.set_completer(tabcomplete.Completer().complete)
        readline.set_completer_delims(_twig_delims)
        readline.parse_and_bind("tab: complete")

    def __repr__(self):
        """Representation for the ParameterSet."""
        self.to_dict()  # <-- to force an update to _next_field
        if len(self._params):
            if len(self.keys()) and self.keys()[0] is not None:
                return "<ParameterSet: {} parameters | {}s: {}>"\
                    .format(len(self._params),
                            self._next_field,
                            ', '.join(self.keys()))
            else:
                return "<ParameterSet: {} parameters>"\
                    .format(len(self._params))
        else:
            return "<ParameterSet: EMPTY>"

    def __str__(self):
        """String representation for the ParameterSet."""
        if len(self._params):
            param_info = "\n".join([p.to_string_short() for p in self._params])
        else:
            param_info = "NO PARAMETERS"

        return "ParameterSet: {} parameters\n".format(len(self._params))+param_info

    @property
    def meta(self):
        """Dictionary of all meta-tags.

        This is a shortcut to the <phoebe.parameters.ParameterSet.get_meta> method.
        See <phoebe.parameters.ParameterSet.get_meta> for the ability to ignore
        certain keys.

        See all the meta-tag properties that are shared by ALL Parameters. If a
        given value is 'None', that means that it is not shared among ALL
        Parameters.  To see the different values among the Parameters, you can
        access that attribute.

        For example: if `ps.meta['context'] == None`, you can see all values
        through `ps.contexts`.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        Returns
        ----------
        * (dict) an ordered dictionary of all tag properties
        """
        return self.get_meta()

    def get_meta(self, ignore=['uniqueid']):
        """Dictionary of all meta-tags, with option to ignore certain tags.

        See all the meta-tag properties that are shared by ALL Parameters.
        If a given value is 'None', that means that it is not shared
        among ALL Parameters.  To see the different values among the
        Parameters, you can access that attribute.

        For example: if `ps.meta['context'] == None`, you can see all values
        through `ps.contexts`.

        See also:
        * <phoebe.parameters.ParameterSet.meta>
        * <phoebe.parameters.ParameterSet.tags>
        * <phoebe.parameters.Parameter.get_meta>

        Arguments
        -----------
        * `ignore` (list, optional, default=['uniqueid']): list of keys to exclude
            from the returned dictionary.

        Returns
        ----------
        * (dict) an ordered dictionary of all tag properties
        """
        return OrderedDict([(k, getattr(self, k))
                            for k in _meta_fields_twig
                            if k not in ignore])

    def set_meta(self, **kwargs):
        """Set the value of tags for all Parameters in this ParameterSet.

        Arguments
        -----------
        * `**kwargs`: tag value pairs to be set for all <phoebe.parameters.Parameter>
            objects in this <phoebe.parameters.ParameterSet>
        """
        for param in self.to_list():
            for k, v in kwargs.items():
                # Here we'll set the attributes (_context, _qualifier, etc)
                if getattr(param, '_{}'.format(k)) is None:
                    setattr(param, '_{}'.format(k), v)

    @property
    def tags(self):
        """Returns a dictionary that lists all available tags that can be used
        for further filtering.

        See also:
        * <phoebe.parameters.ParameterSet.meta>
        * <phoebe.parameters.Parameter.meta>

        Will include entries from the plural attributes:
        * <phoebe.parameters.ParameterSet.contexts>
        * <phoebe.parameters.ParameterSet.kinds>
        * <phoebe.parameters.ParameterSet.models>
        * <phoebe.parameters.ParameterSet.computes>
        * <phoebe.parameters.ParameterSet.constraints>
        * <phoebe.parameters.ParameterSet.datasets>
        * <phoebe.parameters.ParameterSet.components>
        * <phoebe.parameters.ParameterSet.features>
        * <phoebe.parameters.ParameterSet.times>
        * <phoebe.parameters.ParameterSet.qualifiers>

        Returns
        ----------
        * (dict) a dictionary of all plural tag attributes.
        """
        ret = {}
        for typ in _meta_fields_twig:
            if typ in ['uniqueid', 'plugin', 'feedback', 'fitting', 'history', 'twig', 'uniquetwig']:
                continue

            k = '{}s'.format(typ)
            ret[k] = getattr(self, k)

        return ret

    @property
    def uniqueids(self):
        """Return a list of all uniqueids in this ParameterSet.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        There is no singular version for uniqueid for a ParameterSet.  At the
        <phoebe.parameters.Parameter>, see <phoebe.parameters.Parameter.uniqueid>.

        Returns
        --------
        * (list) a list of all uniqueids for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return [p.uniqueid for p in self.to_list()]

    @property
    def twigs(self):
        """Return a list of all twigs in this ParameterSet.

        See also:
        * <phoebe.parameters.ParameterSet.common_twig>
        * <phoebe.parameters.ParameterSet.tags>

        There is no singular version for twig for a ParameterSet.  At the
        <phoebe.parameters.Parameter>, see <phoebe.parameters.Parameter.twig>.

        Returns
        --------
        * (list) a list of all twigs for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return [p.twig for p in self.to_list()]

    @property
    def common_twig(self):
        """
        The twig that is common between all items in this ParameterSet.
        This twig gives a single string which can point back to this ParameterSet
        (but may include other entries as well).

        See also:
        * <phoebe.parameters.ParameterSet.twigs>

        Returns
        -----------
        * (string) common twig of Parameters in the ParameterSet
        """
        return "@".join([getattr(self, k) for k in _meta_fields_twig if self.meta.get(k) is not None])

    @property
    def qualifier(self):
        """Return the value for qualifier if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.qualifiers>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.qualifier>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._qualifier

    @property
    def qualifiers(self):
        """Return a list of all qualifiers in this ParameterSet.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.qualifier>

        Returns
        --------
        * (list) a list of all qualifiers for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='qualifier').keys())

    @property
    def time(self):
        """Return the value for time if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.times>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.time>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return str(self._time) if self._time is not None else None

    @property
    def times(self):
        """Return a list of all the times of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.time>

        Returns
        --------
        * (list) a list of all times for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='time').keys())

    @property
    def history(self):
        """Return the value for history if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.histories>
        or <phoebe.parameters.ParameterSet.historys>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.history>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._history

    @property
    def histories(self):
        """Return a list of all the histories of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.history>

        Returns
        --------
        * (list) a list of all histories for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='history').keys())

    @property
    def historys(self):
        """Return a list of all the histories of the Parameters.

        Shortcut to <phoebe.parameters.ParameterSet.histories>

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.history>

        Returns
        --------
        * (list) a list of all twigs for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return self.histories


    @property
    def feature(self):
        """Return the value for feature if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.features>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.feature>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._feature

    @property
    def features(self):
        """Return a list of all this features of teh Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.feature>

        Returns
        --------
        * (list) a list of all features for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='feature').keys())


    # @property
    # def properties(self):
    #     """Return a list of all the properties of the Parameters.
    #
    #     :return: list of strings
    #     """
    #     return self.to_dict(field='feature').keys()

    @property
    def component(self):
        """Return the value for component if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.components>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.component>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._component

    @property
    def components(self):
        """Return a list of all the components of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.component>

        Returns
        --------
        * (list) a list of all components for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return [c for c in self.to_dict(field='component').keys() if c!='_default']

    @property
    def dataset(self):
        """Return the value for dataset if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.datasets>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.dataset>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._dataset

    @property
    def datasets(self):
        """Return a list of all the datasets of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.dataset>

        Returns
        --------
        * (list) a list of all datasets for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return [d for d in self.to_dict(field='dataset').keys() if d!='_default']

    @property
    def constraint(self):
        """Return the value for constraint if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.constraints>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.constraint>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._constraint

    @property
    def constraints(self):
        """Return a list of all the constraints of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.constraint>

        Returns
        --------
        * (list) a list of all constraints for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='constraint').keys())

    @property
    def compute(self):
        """Return the value for compute if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.computes>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.compute>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._compute

    @property
    def computes(self):
        """Return a list of all the computes of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.compute>

        Returns
        --------
        * (list) a list of all computes for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='compute').keys())

    @property
    def model(self):
        """Return the value for model if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.models>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.model>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._model

    @property
    def models(self):
        """Return a list of all the models of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.model>

        Returns
        --------
        * (list) a list of all models for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='model').keys())

    @property
    def fitting(self):
        """Return the value for fitting if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.fittings>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.fitting>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._fitting

    @property
    def fittings(self):
        """Return a list of all the fittings of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.fitting>

        Returns
        --------
        * (list) a list of all fittings for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='fitting').keys())

    @property
    def feedback(self):
        """Return the value for feedback if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.feedbacks>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.feedback>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._feedback

    @property
    def feedbacks(self):
        """Return a list of all the feedbacks of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.feedback>

        Returns
        --------
        * (list) a list of all feedbacks for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='feedback').keys())

    @property
    def plugin(self):
        """Return the value for plugin if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.plugins>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.plugin>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._plugin

    @property
    def plugins(self):
        """Return a list of all the plugins of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.plugin>

        Returns
        --------
        * (list) a list of all plugins for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='plugin').keys())

    @property
    def kind(self):
        """Return the value for kind if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.kinds>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.kind>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._kind

    @property
    def kinds(self):
        """Return a list of all the kinds of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.kind>

        Returns
        --------
        * (list) a list of all kinds for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='kind').keys())

    @property
    def context(self):
        """Return the value for context if shared by ALL Parameters.

        If the value is not shared by ALL, then None will be returned.  To see
        all the qualifiers of all parameters, see <phoebe.parameters.ParameterSet.contexts>.

        To see the value of a single <phoebe.parameters.Parameter> object, see
        <phoebe.parameters.Parameter.context>.

        Returns
        --------
        (string or None) the value if shared by ALL <phoebe.parameters.Parameter>
            objects in the <phoebe.parmaters.ParameterSet>, otherwise None
        """
        return self._context

    @property
    def contexts(self):
        """Return a list of all the contexts of the Parameters.

        See also:
        * <phoebe.parameters.ParameterSet.tags>

        For the singular version, see:
        * <phoebe.parameters.ParameterSet.context>

        Returns
        --------
        * (list) a list of all contexts for each <phoebe.parameters.Parameter>
            in this <phoebe.parmaeters.ParameterSet>
        """
        return list(self.to_dict(field='context').keys())

    def _set_meta(self):
        """
        set the meta fields of the ParameterSet as those that are shared
        by ALL parameters in the ParameterSet.  For any fields that are
        not
        """
        # we want to set meta-fields that are shared by ALL params in the PS
        for field in _meta_fields_twig:
            keys_for_this_field = set([getattr(p, field)
                                       for p in self.to_list()
                                       if getattr(p, field) is not None])
            if len(keys_for_this_field)==1:
                setattr(self, '_'+field, list(keys_for_this_field)[0])
            else:
                setattr(self, '_'+field, None)

    def _uniquetwig(self, twig, force_levels=['qualifier']):
        """
        get the least unique twig for the parameter given by twig that
        will return this single result for THIS PS

        :parameter str twig: a twig that will return a single Parameter from
                THIS PS
        :parameter list force_levels: (optional) a list of "levels"
            (eg. context) that should be included whether or not they are
            necessary
        :return: the unique twig
        :rtype: str
        """
        for_this_param = self.filter(twig, check_visible=False)

        metawargs = {}

        # NOTE: self.contexts is INCREDIBLY expensive
        # if len(self.contexts) and 'context' not in force_levels:
        if 'context' not in force_levels:
            # then let's force context to be included
            force_levels.append('context')

        for k in force_levels:
            metawargs[k] = getattr(for_this_param, k)

        prev_count = len(self)
        # just to fake in case no metawargs are passed at all
        ps_for_this_search = []
        for k in _meta_fields_twig:
            metawargs[k] = getattr(for_this_param, k)
            if getattr(for_this_param, k) is None:
                continue

            ps_for_this_search = self.filter(check_visible=False, **metawargs)

            if len(ps_for_this_search) < prev_count and k not in force_levels:
                prev_count = len(ps_for_this_search)
            elif k not in force_levels:
                # this didn't help us
                metawargs[k] = None

        if len(ps_for_this_search) != 1:
            # TODO: after fixing regex in twig (t0type vs t0)
            # change this to raise Error instead of return
            return twig

        # now we go in the other direction and try to remove each to make sure
        # the count goes up
        for k in _meta_fields_twig:
            if metawargs[k] is None or k in force_levels:
                continue

            ps_for_this_search = self.filter(check_visible=False,
                                             **{ki: metawargs[k]
                                                for ki in _meta_fields_twig
                                                if ki != k})

            if len(ps_for_this_search) == 1:
                # then we didn't need to use this tag
                metawargs[k] = None

        # and lastly, we make sure that the tag corresponding to the context
        # is present
        context = for_this_param.context
        if hasattr(for_this_param, context):
            metawargs[context] = getattr(for_this_param, context)

        return "@".join([metawargs[k]
                         for k in _meta_fields_twig
                         if metawargs[k] is not None])

    def _attach_params(self, params, **kwargs):
        """Attach a list of parameters (or ParameterSet) to this ParameterSet.

        :parameter list params: list of parameters, or ParameterSet
        :parameter **kwargs: attributes to set for each parameter (ie tags)
        """
        lst = params.to_list() if isinstance(params, ParameterSet) else params
        for param in lst:
            param._bundle = self

            for k, v in kwargs.items():
                # Here we'll set the attributes (_context, _qualifier, etc)
                if getattr(param, '_{}'.format(k)) is None:
                    setattr(param, '_{}'.format(k), v)
            self._params.append(param)

        self._check_copy_for()

        return

    def _check_copy_for(self):
        """Check the value of copy_for and make appropriate copies."""
        if not self._bundle:
            return

        # read the following at your own risk - I just wrote it and it still
        # confuses me and baffles me that it works
        for param in self.to_list():
            if param.copy_for:
                # copy_for tells us how to filter and what set of attributes
                # needs a copy of this parameter
                #
                # copy_for = {'kind': ['star', 'disk', 'custombody'], 'component': '*'}
                # means that this should exist for each component (since that has a wildcard) which
                # has a kind in [star, disk, custombody]
                #
                # copy_for = {'kind': ['rv_dep'], 'component': '*', 'dataset': '*'}
                # or
                # copy_for = {'component': {}, 'dataset': {'kind': 'rv_dep'}}
                # means that this should exist for each component/dataset pair with the
                # rv_dep kind
                #
                # copy_for = {'component': {'kind': 'star'}, 'dataset': {'kind': 'rv'}}
                # means that this should exist for each component/dataset pair
                # in which the component has kind='star' and dataset has kind='rv'


                attrs = [k for k,v in param.copy_for.items() if '*' in v or isinstance(v, dict)]
                # attrs is a list of the attributes for which we need a copy of
                # this parameter for any pair

                def force_list(v):
                    if isinstance(v, list):
                        return v
                    elif v=='*':
                        return v
                    else:
                        return [v]

                filter_ = {}
                for k,v in param.copy_for.items():
                    if isinstance(v,dict):
                        for dk,dv in v.items():
                            if dk in filter_.keys():
                                filter_[dk] += force_list(dv)
                            else:
                                filter_[dk] = force_list(dv)
                    else:
                        filter_[k] = force_list(v)

                ps = self._bundle.filter(check_visible=False,
                                         check_default=False,
                                         force_ps=True, **filter_)
                metawargs = {k:v for k,v in ps.meta.items() if v is not None and k in attrs}
                for k,v in param.meta.items():
                    if k not in ['twig', 'uniquetwig'] and k not in attrs:
                        metawargs[k] = v
                # metawargs is a list of the shared tags that will be used to filter for
                # existing parameters so that we know whether they already exist or
                # still need to be created

                # logger.debug("_check_copy_for {}: attrs={}".format(param.twig, attrs))
                for attrvalues in itertools.product(*(getattr(ps, '{}s'.format(attr)) for attr in attrs)):
                    # logger.debug("_check_copy_for {}: attrvalues={}".format(param.twig, attrvalues))
                    # for each attrs[i] (ie component), attrvalues[i] (star01)
                    # we need to look for this parameter, and if it does not exist
                    # then create it by copying param

                    valid = True

                    for attr, attrvalue in zip(attrs, attrvalues):
                        #if attrvalue=='_default' and not getattr(param, attr):
                        #    print "SKIPPING", attr, attrvalue
                        #    continue

                        # make sure valid from the copy_for dictionary
                        if isinstance(param.copy_for[attr], dict):
                            filter_ = {k:v for k,v in param.copy_for[attr].items()}
                            filter_[attr] = attrvalue
                            if not len(ps.filter(check_visible=False, check_default=False, check_advanced=False, check_single=False, force_ps=True, **filter_)):
                                valid = False

                        metawargs[attr] = attrvalue

                    # logger.debug("_check_copy_for {}: metawargs={}".format(param.twig, metawargs))
                    if valid and not len(self._bundle.filter(check_visible=False, **metawargs)):
                        # then we need to make a new copy
                        logger.debug("copying '{}' parameter for {}".format(param.qualifier, {attr: attrvalue for attr, attrvalue in zip(attrs, attrvalues)}))

                        newparam = param.copy()

                        for attr, attrvalue in zip(attrs, attrvalues):
                            setattr(newparam, '_{}'.format(attr), attrvalue)

                        newparam._copy_for = False
                        if newparam._visible_if and newparam._visible_if.lower() == 'false':
                            newparam._visible_if = None
                        newparam._bundle = self._bundle

                        self._params.append(newparam)


                    # Now we need to handle copying constraints.  This can't be
                    # in the previous if statement because the parameters can be
                    # copied before constraints are ever attached.
                    if valid and hasattr(param, 'is_constraint') and param.is_constraint:

                        param_constraint = param.is_constraint

                        copied_param = self._bundle.get_parameter(check_visible=False, check_default=False, **metawargs)

                        if not copied_param.is_constraint:
                            constraint_kwargs = param_constraint.constraint_kwargs.copy()
                            for attr, attrvalue in zip(attrs, attrvalues):
                                if attr in constraint_kwargs.keys():
                                    constraint_kwargs[attr] = attrvalue

                            logger.debug("copying constraint '{}' parameter for {}".format(param_constraint.constraint_func, {attr: attrvalue for attr, attrvalue in zip(attrs, attrvalues)}))
                            self.add_constraint(func=param_constraint.constraint_func, **constraint_kwargs)

        return

    def _check_label(self, label, allow_overwrite=False):
        """Check to see if the label is allowed."""

        if not isinstance(label, str):
            label = str(label)

        if label.lower() in _forbidden_labels:
            raise ValueError("'{}' is forbidden to be used as a label"
                             .format(label))
        if not re.match("^[a-z,A-Z,0-9,_]*$", label):
            raise ValueError("label '{}' is forbidden - only alphabetic, numeric, and '_' characters are allowed in labels".format(label))
        if len(self.filter(twig=label, check_visible=False)) and not allow_overwrite:
            raise ValueError("label '{}' is already in use.  Remove first or pass overwrite=True, if available.".format(label))
        if label[0] in ['_']:
            raise ValueError("first character of label is a forbidden character")

    def __add__(self, other):
        """Adding 2 PSs returns a new PS with items that are in either."""
        if isinstance(other, Parameter):
            other = ParameterSet([other])

        if isinstance(other, ParameterSet):
            # NOTE: used to have the following but doesn't work in python3
            # because the Parameters aren't hashable:
            # return ParameterSet(list(set(self._params+other._params)))
            lst = self._params
            for p in other._params:
                if p not in lst:
                    lst.append(p)

            ps = ParameterSet(lst)
            ps._bundle = self._bundle
            return ps
        else:
            raise NotImplementedError

    def __sub__(self, other):
        """Subtracting 2 PSs returns a new PS with items in the first but not second."""

        if isinstance(other, Parameter):
            other = ParameterSet([other])

        if isinstance(other, ParameterSet):
            ps = ParameterSet([p for p in self._params if p not in other._params])
            ps._bundle = self._bundle
            return ps
        else:
            raise NotImplementedError

    def __mul__(self, other):
        """
        multiplying 2 PSs should return a new PS with items that are in both (ie AND logic)

        this is the same as chaining filter calls
        """
        if isinstance(other, Parameter):
            other = ParameterSet([other])

        if isinstance(other, ParameterSet):
            ps = ParameterSet([p for p in self._params if p in other._params])
            ps._bundle = self._bundle
            return ps
        else:
            raise NotImplementedError

    @classmethod
    def open(cls, filename):
        """
        Open a ParameterSet from a JSON-formatted file.
        This is a constructor so should be called as:

        ```py
        ps = ParameterSet.open('test.json')
        ```

        See also:
        * <phoebe.parameters.Parameter.open>
        * <phoebe.frontend.bundle.Bundle.open>

        Arguments
        ---------
        * `filename` (string): relative or full path to the file

        Returns
        ---------
        * an instantiated <phoebe.parameters.ParameterSet> object
        """
        filename = os.path.expanduser(filename)
        f = open(filename, 'r')
        if _can_ujson:
            # NOTE: this will not parse the unicode.  Bundle.open always calls
            # json instead of ujson for this reason.
            data = ujson.load(f)
        else:
            data = json.load(f, object_pairs_hook=parse_json)
        f.close()
        return cls(data)

    def save(self, filename, incl_uniqueid=False, compact=False):
        """
        Save the ParameterSet to a JSON-formatted ASCII file.

        See also:
        * <phoebe.parameters.Parameter.save>
        * <phoebe.frontend.bundle.Bundle.save>

        Arguments
        ----------
        * `filename` (string): relative or full path to the file
        * `incl_uniqueid` (bool, optional, default=False): whether to include
            uniqueids in the file (only needed if its necessary to maintain the
            uniqueids when reloading)
        * `compact` (bool, optional, default=False): whether to use compact
            file-formatting (may be quicker to save/load, but not as easily readable)

        Returns
        --------
        * (string) filename
        """
        filename = os.path.expanduser(filename)
        f = open(filename, 'w')
        if compact:
            if _can_ujson:
                ujson.dump(self.to_json(incl_uniqueid=incl_uniqueid), f,
                           sort_keys=False, indent=0)
            else:
                logger.warning("for faster compact saving, install ujson")
                json.dump(self.to_json(incl_uniqueid=incl_uniqueid), f,
                          sort_keys=False, indent=0)
        else:
            json.dump(self.to_json(incl_uniqueid=incl_uniqueid), f,
                      sort_keys=True, indent=0, separators=(',', ': '))
        f.close()

        return filename

    def ui(self, client='http://localhost:4200', **kwargs):
        """
        [NOT IMPLEMENTED]

        The bundle must be in client mode in order to open the web-interface.
        See <phoebe.frontend.bundle.Bundle.as_client> to switch to client mode.

        :parameter str client: URL of the running client which must be connected
            to the same server as the bundle
        :return: URL of the parameterset of this bundle in the client (will also
            attempt to open webbrowser)
        :rtype: str
        """
        if self._bundle is None or not self._bundle.is_client:
            raise ValueError("bundle must be in client mode")

        if len(kwargs):
            return self.filter(**kwargs).ui(client=client)

        querystr = "&".join(["{}={}".format(k, v)
                             for k, v in self._filter.items()])
        # print self._filter
        url = "{}/{}?{}".format(client, self._bundle._bundleid, querystr)

        logger.info("opening {} in browser".format(url))
        webbrowser.open(url)
        return url

    def to_list(self, **kwargs):
        """
        Convert the <phoebe.parameters.ParameterSet> to a list of
        <phoebe.parameters.Parameter> objects.

        Arguments
        ---------
        * `**kwargs`: filter arguments sent to
            <phoebe.parameters.ParameterSet.filter>

        Returns
        --------
        * (list) list of <phoebe.parameter.Parameter> objects
        """
        if kwargs:
            return self.filter(**kwargs).to_list()
        return self._params

    def tolist(self, **kwargs):
        """
        Alias of <phoebe.parameters.ParameterSet.to_list>

        Arguments
        ---------
        * `**kwargs`: filter arguments sent to
            <phoebe.parameters.ParameterSet.filter>

        Returns
        --------
        * (list) list of <phoebe.parameter.Parameter> objects
        """
        return self.to_list(**kwargs)

    def to_list_of_dicts(self, **kwargs):
        """
        Convert the <phoebe.parameters.ParameterSet> to a list of the dictionary
        representation of each <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.Parameter.to_dict>

        Arguments
        ----------
        * `**kwargs`: filter arguments sent to
            <phoebe.parameters.ParameterSet.filter>

        Returns
        --------
        * (list of dicts) list of dictionaries, with each entry in the list
            representing a single <phoebe.parameters.Parameter> object converted
            to a dictionary via <phoebe.parameters.Parameter.to_dict>.
        """
        if kwargs:
            return self.filter(**kwargs).to_list_of_dicts()
        return [param.to_dict() for param in self._params]

    def __dict__(self):
        """Dictionary representation of a ParameterSet."""
        return self.to_dict()

    def to_flat_dict(self, **kwargs):
        """
        Convert the <phoebe.parameters.ParameterSet> to a flat dictionary, with
        keys being uniquetwigs to access the parameter and values being the
        <phoebe.parameters.Parameter> objects themselves.

        See also:
        * <phoebe.parameters.Parameter.uniquetwig>

        Arguments
        ----------
        * `**kwargs`: filter arguments sent to
            <phoebe.parameters.ParameterSet.filter>

        Returns
        --------
        * (dict) uniquetwig: Parameter pairs.
        """
        if kwargs:
            return self.filter(**kwargs).to_flat_dict()
        return {param.uniquetwig: param for param in self._params}

    def to_dict(self, field=None, **kwargs):
        """
        Convert the <phoebe.parameters.ParameterSet> to a structured (nested)
        dictionary to allow traversing the structure from the bottom up.

        See also:
        * <phoebe.parameters.ParameterSet.to_json>
        * <phoebe.parameters.ParameterSet.keys>
        * <phoebe.parameters.ParameterSet.values>
        * <phoebe.parameters.ParameterSet.items>

        Arguments
        ----------
        * `field` (string, optional, default=None): build the dictionary with
            keys at a given level/field.  Can be any of the keys in
            <phoebe.parameters.ParameterSet.meta>.  If None, the keys will be
            the lowest level in which Parameters have different values.

        Returns
        ---------
        * (dict) dictionary of <phoebe.parameters.ParameterSet> or
            <phoebe.parameters.Parameter> objects.
        """
        if kwargs:
            return self.filter(**kwargs).to_dict(field=field)

        if field is not None:
            keys_for_this_field = set([getattr(p, field)
                                       for p in self.to_list()
                                       if getattr(p, field) is not None])
            return {k: self.filter(check_visible=False, **{field: k}) for k in keys_for_this_field}

        # we want to find the first level (from the bottom) in which filtering
        # further would shorten the list (ie there are more than one unique
        # item for that field)

        # so let's go through the fields in reverse (context up to (but not
        # including) qualifier)
        for field in reversed(_meta_fields_twig[1:]):
            # then get the unique keys in this field among the params in this
            # PS
            keys_for_this_field = set([getattr(p, field)
                                       for p in self.to_list()
                                       if getattr(p, field) is not None])
            # and if there are more than one, then return a dictionary with
            # those keys and the ParameterSet of the matching items
            if len(keys_for_this_field) > 1:
                self._next_field = field
                return {k: self.filter(check_visible=False, **{field: k})
                        for k in keys_for_this_field}

        # if we've survived, then we're at the bottom and only have times or
        # qualifier left
        if self.context in ['hierarchy']:
            self._next_field = 'qualifier'
            return {param.qualifier: param for param in self._params}
        else:
            self._next_field = 'time'
            return {param.time: param for param in self._params}

    def keys(self):
        """
        Return the keys from <phoebe.parameters.ParameterSet.to_dict>

        Returns
        ---------
        * (list) list of strings
        """
        return list(self.__dict__().keys())

    def values(self):
        """
        Return the values from <phoebe.parmaeters.ParameterSet.to_dict>

        Returns
        -------
        * (list) list of <phoebe.paramters.ParameterSet> or
            <phoebe.parameters.Parameter> objects.
        """
        return self.__dict__().values()

    def items(self):
        """
        Returns the items (key, value pairs) from
        <phoebe.parmaeters.ParameterSet.to_dict>.

        :return: string, :class:`Parameter` or :class:`ParameterSet` pairs
        """
        return self.__dict__().items()

    def set(self, key, value, **kwargs):
        """
        Set the value of a <phoebe.parameters.Parameter> in the
        <phoebe.parameters.ParameterSet>.

        If <phoebe.parameters.ParameterSet.get> with the same value for
        `key`/`twig` and `**kwargs` would retrieve a single Parameter,
        this will set the value of that parameter.

        Or you can provide 'value@...' or 'default_unit@...', etc
        to specify what attribute to set.

        Arguments
        -----------
        * `key` (string): the twig (called key here to be analagous to a python
            dictionary) used for filtering.
        * `value` (valid value for the matching Parameter): value to set
        * `**kwargs`: other filter parameters

        Returns
        --------
        * (float/array/string/etc): the value of the <phoebe.parameters.Parameter>
            after setting the value (including converting units if applicable).
        """
        twig = key

        method = None
        twigsplit = re.findall(r"[\w']+", twig)
        if twigsplit[0] == 'value':
            twig = '@'.join(twigsplit[1:])
            method = 'set_value'
        elif twigsplit[0] == 'quantity':
            twig = '@'.join(twigsplit[1:])
            method = 'set_quantity'
        elif twigsplit[0] in ['unit', 'default_unit']:
            twig = '@'.join(twigsplit[1:])
            method = 'set_default_unit'
        elif twigsplit[0] in ['timederiv']:
            twig = '@'.join(twigsplit[1:])
            method = 'set_timederiv'
        elif twigsplit[0] in ['description']:
            raise KeyError("cannot set {} of {}".format(twigsplit[0], '@'.join(twigsplit[1:])))

        if self._bundle is not None and self._bundle.get_setting('dict_set_all').get_value() and len(self.filter(twig=twig, **kwargs)) > 1:
            # then we need to loop through all the returned parameters and call set on them
            for param in self.filter(twig=twig, **kwargs).to_list():
                self.set('{}@{}'.format(method, param.twig) if method is not None else param.twig, value)
        else:

            if method is None:
                return self.set_value(twig=twig, value=value, **kwargs)
            else:
                param = self.get_parameter(twig=twig, **kwargs)

                return getattr(param, method)(value)

    def __getitem__(self, key):
        """
        """
        if self._bundle is not None:
            kwargs = self._bundle.get_value(qualifier='dict_filter',
                                            context='setting',
                                            default={})
        else:
            kwargs = {}

        if isinstance(key, int):
            return self.filter(**kwargs).to_list()[key]

        return self.filter_or_get(twig=key, **kwargs)

    def __setitem__(self, twig, value):
        """
        """
        if self._bundle is not None:
            kwargs = self._bundle.get_setting('dict_filter').get_value()
        else:
            kwargs = {}

        self.set(twig, value, allow_value_as_first_arg=False, **kwargs)

    def __contains__(self, twig):
        """
        """
        # may not be an exact match with __dict__.keys()
        return len(self.filter(twig=twig))

    def __len__(self):
        """
        """
        return len(self._params)

    def __iter__(self):
        """
        """
        return iter(self.__dict__())

    def to_json(self, incl_uniqueid=False):
        """
        Convert the <phoebe.parameters.ParameterSet> to a json-compatible
        object.

        The resulting object will be a list, with one entry per-Parameter
        being the json representation of that Parameter from
        <phoebe.parameters.Parameter.to_json>.

        See also:
        * <phoebe.parameters.Parameter.to_json>
        * <phoebe.parameters.ParameterSet.to_dict>
        * <phoebe.parameters.ParameterSet.save>

        Arguments
        --------
        * `incl_uniqueid` (bool, optional, default=False): whether to include
            uniqueids in the file (only needed if its necessary to maintain the
            uniqueids when reloading)

        Returns
        -----------
        * (list of dicts)
        """
        lst = []
        for context in _contexts:
            lst += [v.to_json(incl_uniqueid=incl_uniqueid)
                    for v in self.filter(context=context,
                                         check_visible=False,
                                         check_default=False).to_list()]
        return lst
        # return {k: v.to_json() for k,v in self.to_flat_dict().items()}

    def filter(self, twig=None, check_visible=True, check_default=True, **kwargs):
        """
        Filter the <phoebe.parameters.ParameterSet> based on the meta-tags of the
        children <phoebe.parameters.Parameter> objects and return another
        <phoebe.parameters.ParameterSet>.

        Because another ParameterSet is returned, these filter calls are
        chainable.

        ```py
        b.filter(context='component').filter(component='starA')
        ```

        See also:
        * <phoebe.parameters.ParameterSet.filter_or_get>
        * <phoebe.parameters.ParameterSet.exclude>
        * <phoebe.parameters.ParameterSet.get>
        * <phoebe.parameters.ParameterSet.get_parameter>
        * <phoebe.parameters.ParameterSet.get_or_create>

        Arguments
        -----------
        * `twig` (str, optional, default=None): the search twig - essentially a single
            string with any delimiter (ie '@') that will be parsed
            into any of the meta-tags.  Example: instead of
            `b.filter(context='component', component='starA')`, you
            could do `b.filter('starA@component')`.
        * `check_visible` (bool, optional, default=True): whether to hide invisible
            parameters.  These are usually parameters that do not
            play a role unless the value of another parameter meets
            some condition.
        * `check_default` (bool, optional, default=True): whether to exclude parameters which
            have a _default tag (these are parameters which solely exist
            to provide defaults for when new parameters or datasets are
            added and the parameter needs to be copied appropriately).
            Defaults to True.
        * `**kwargs`:  meta-tags to search (ie. 'context', 'component',
            'model', etc).  See <phoebe.parameters.ParameterSet.meta>
            for all possible options.

        Returns
        ----------
        * the resulting <phoebe.parameters.ParameterSet>.
        """
        kwargs['check_visible'] = check_visible
        kwargs['check_default'] = check_default
        kwargs['force_ps'] = True
        return self.filter_or_get(twig=twig, **kwargs)

    def get(self, twig=None, check_visible=True, check_default=True, **kwargs):
        """
        Get a single <phoebe.parameters.Parameter> from this
        <phoebe.parameters.ParameterSet>.  This works exactly the
        same as <phoebe.parameters.ParameterSet.filter> except there must be only
        a single result, and the Parameter itself is returned instead of a
        ParameterSet.

        This is identical to <phoebe.parameters.ParameterSet.get_parameter>

        See also:
        * <phoebe.parameters.ParameterSet.filter>
        * <phoebe.parameters.ParameterSet.filter_or_get>
        * <phoebe.parameters.ParameterSet.exclude>
        * <phoebe.parameters.ParameterSet.get_or_create>

        Arguments
        -----------
        * `twig` (str, optional, default=None): the search twig - essentially a single
            string with any delimiter (ie '@') that will be parsed
            into any of the meta-tags.  Example: instead of
            `b.filter(context='component', component='starA')`, you
            could do `b.filter('starA@component')`.
        * `check_visible` (bool, optional, default=True): whether to hide invisible
            parameters.  These are usually parameters that do not
            play a role unless the value of another parameter meets
            some condition.
        * `check_default` (bool, optional, default=True): whether to exclude parameters which
            have a _default tag (these are parameters which solely exist
            to provide defaults for when new parameters or datasets are
            added and the parameter needs to be copied appropriately).
            Defaults to True.
        * `**kwargs`:  meta-tags to search (ie. 'context', 'component',
            'model', etc).  See <phoebe.parameters.ParameterSet.meta>
            for all possible options.

        Returns
        --------
        * the resulting <phoebe.parameters.Parameter>.

        Raises
        -------
        * ValueError: if either 0 or more than 1 results are found
            matching the search.
        """
        kwargs['check_visible'] = check_visible
        kwargs['check_default'] = check_default
        # print "***", kwargs
        ps = self.filter(twig=twig, **kwargs)
        if not len(ps):
            # TODO: custom exception?
            raise ValueError("0 results found")
        elif len(ps) != 1:
            # TODO: custom exception?
            raise ValueError("{} results found: {}".format(len(ps), ps.twigs))
        else:
            # then only 1 item, so return the parameter
            return ps._params[0]

    def filter_or_get(self, twig=None, autocomplete=False, force_ps=False,
                      check_visible=True, check_default=True, **kwargs):
        """

        Filter the <phoebe.parameters.ParameterSet> based on the meta-tags of its
        Parameters and return another <phoebe.parameters.ParameterSet> unless there is
        exactly 1 result, in which case the <phoebe.parameters.Parameter> itself is
        returned (set `force_ps=True` to avoid this from happening or call
        <phoebe.parameters.ParameterSet.filter> instead).

        In the case when another <phoebe.parameters.ParameterSet> is returned, these
        calls are chainable.

        ```py
        b.filter_or_get(context='component').filter_or_get(component='starA')
        ```

        See also:
        * <phoebe.parameters.ParameterSet.filter>
        * <phoebe.parameters.ParameterSet.exclude>
        * <phoebe.parameters.ParameterSet.get>
        * <phoebe.parameters.ParameterSet.get_parameter>
        * <phoebe.parameters.ParameterSet.get_or_create>

        Arguments
        -----------
        * `twig` (str, optional, default=None): the search twig - essentially a single
            string with any delimiter (ie '@') that will be parsed
            into any of the meta-tags.  Example: instead of
            `b.filter(context='component', component='starA')`, you
            could do `b.filter('starA@component')`.
        * `check_visible` (bool, optional, default=True): whether to hide invisible
            parameters.  These are usually parameters that do not
            play a role unless the value of another parameter meets
            some condition.
        * `check_default` (bool, optional, default=True): whether to exclude parameters which
            have a _default tag (these are parameters which solely exist
            to provide defaults for when new parameters or datasets are
            added and the parameter needs to be copied appropriately).
            Defaults to True.
        * `force_ps` (bool, optional, default=False): whether to force a
            <phoebe.parameters.ParameterSet> to be returned, even if more than
            1 result (see also: <phoebe.parameters.ParameterSet.filter>)
        * `**kwargs`:  meta-tags to search (ie. 'context', 'component',
            'model', etc).  See <phoebe.parameters.ParameterSet.meta>
            for all possible options.

        Returns
        ----------
        * the resulting <phoebe.parameters.Parameter> object if the length
            of the results is exactly 1 and `force_ps=False`, otherwise the
            resulting <phoebe.parameters.ParameterSet>.
        """

        if self._bundle is None:
            # then override check_default to False - its annoying when building
            # a ParameterSet say by calling datasets.lc() and having half
            # of the Parameters hidden by this switch
            check_default = False

        if not (twig is None or isinstance(twig, str)):
            raise TypeError("first argument (twig) must be of type str or None")

        if kwargs.get('component', None) == '_default' or\
                kwargs.get('dataset', None) == '_default' or\
                kwargs.get('uniqueid', None) is not None or\
                kwargs.get('uniquetwig', None) is not None:
            # then override the default for check_default and make sure to
            # return a result
            check_default = False

        time = kwargs.get('time', None)
        if hasattr(time, '__iter__') and not isinstance(time, str):
            # then we should loop here rather than forcing complicated logic
            # below
            kwargs['twig'] = twig
            kwargs['autocomplete'] = autocomplete
            kwargs['force_ps'] = force_ps
            kwargs['check_visible'] = check_visible
            kwargs['check_default'] = check_default
            return_ = ParameterSet()
            for t in time:
                kwargs['time'] = t
                return_ += self.filter_or_get(**kwargs)
            return return_

        params = self.to_list()

        def string_to_time(time):
            try:
                return float(time)
            except ValueError:
                # allow for passing a twig that needs to resolve a float
                if self._bundle is None:
                    return self.get_value(time, context=['system', 'component'])
                else:
                    return self._bundle.get_value(time, context=['system', 'component'])

        # TODO: replace with key,value in kwargs.items()... unless there was
        # some reason that won't work?
        for key in kwargs.keys():
            if len(params) and \
                    key in _meta_fields_filter and \
                    kwargs[key] is not None:

                #if kwargs[key] is None:
                #    params = [pi for pi in params if getattr(pi,key) is None]
                #else:
                if isinstance(kwargs[key], unicode):
                    # unicodes can cause all sorts of confusions with fnmatch,
                    # so let's just cast now and be done with it
                    kwargs[key] = str(kwargs[key])

                params = [pi for pi in params if (hasattr(pi,key) and getattr(pi,key) is not None) and
                    (getattr(pi,key)==kwargs[key] or
                    (isinstance(kwargs[key],list) and getattr(pi,key) in kwargs[key]) or
                    (isinstance(kwargs[key],list) and np.any([fnmatch(getattr(pi,key),keyi) for keyi in kwargs[key]])) or
                    (isinstance(kwargs[key],str) and isinstance(getattr(pi,key),str) and fnmatch(getattr(pi,key),kwargs[key])) or
                    (key=='kind' and isinstance(kwargs[key],str) and getattr(pi,key).lower()==kwargs[key].lower()) or
                    (key=='kind' and hasattr(kwargs[key],'__iter__') and getattr(pi,key).lower() in [k.lower() for k in kwargs[key]]) or
                    (key=='time' and abs(float(getattr(pi,key))-string_to_time(kwargs[key]))<1e-6))]
                    #(key=='time' and abs(float(getattr(pi,key))-float(kwargs[key]))<=abs(np.array([p._time for p in params])-float(kwargs[key]))))]

        # handle hiding _default (cheaper than visible_if so let's do first)
        if check_default:
            params = [pi for pi in params if pi.component != '_default' and pi.dataset != '_default']

        # handle visible_if
        if check_visible:
            params = [pi for pi in params if pi.is_visible]

        if isinstance(twig, int):
            # then act as a list index
            return params[twig]

        # TODO: handle isinstance(twig, float) as passing time?

        # TODO: smarter error if trying to slice on a PS instead of value (ie
        # b['value@blah'][::8] where b['value@blah'] is returning an empty PS
        # and ::8 is being passed here as twig)

        # now do twig matching
        method = None
        if twig is not None:
            _user_twig = deepcopy(twig)
            twigsplit = twig.split('@')
            if twigsplit[0] == 'value':
                twig = '@'.join(twigsplit[1:])
                method = 'get_value'
            elif twigsplit[0] == 'quantity':
                twig = '@'.join(twigsplit[1:])
                method = 'get_quantity'
            elif twigsplit[0] in ['unit', 'default_unit']:
                twig = '@'.join(twigsplit[1:])
                method = 'get_default_unit'
            elif twigsplit[0] in ['timederiv']:
                twig = '@'.join(twigsplit[1:])
                method = 'get_timederiv'
            elif twigsplit[0] == 'description':
                twig = '@'.join(twigsplit[1:])
                method = 'get_description'
            elif twigsplit[0] == 'choices':
                twig = '@'.join(twigsplit[1:])
                method = 'get_choices'
            elif twigsplit[0] == 'result':
                twig = '@'.join(twigsplit[1:])
                method = 'get_result'

            # twigsplit = re.findall(r"[\w']+", twig)
            twigsplit = twig.split('@')

            if autocomplete:
                # then we want to do matching based on all but the
                # last item in the twig and then try to autocomplete
                # based on the last item
                if re.findall(r"[^\w]", _user_twig[-1]):
                    # then we will autocomplete on an empty entry
                    twigautocomplete = ''
                else:
                    # the last item in twig is incomplete
                    twigautocomplete = twigsplit[-1]
                    twigsplit = twigsplit[:-1]

            for ti in twigsplit:
                # TODO: need to fix repeating twigs (ie
                # period@period@period@period still matches and causes problems
                # with the tabcomplete)
                params = [pi for pi in params if ti in pi.twig.split('@') or fnmatch(pi.twig, ti)]

            if autocomplete:
                # we want to provide options for what twigautomplete
                # could be to produce matches
                options = []
                for pi in params:
                    for twiglet in pi.twig.split('@'):
                        if twigautocomplete == twiglet[:len(twigautocomplete)]:
                            if len(twigautocomplete):
                                completed_twig = _user_twig.replace(twigautocomplete, twiglet)
                            else:
                                completed_twig = _user_twig + twiglet
                            if completed_twig not in options:
                                options.append(completed_twig)
                return options

        if len(params) == 1 and not force_ps:
            # then just return the parameter itself
            if method is None:
                return params[0]
            else:
                return getattr(params[0], method)()

        elif method is not None:
            raise ValueError("{} results found, could not call {}".format(len(params), method))

        # TODO: handle returning 0 results better

        ps = ParameterSet(params)
        ps._bundle = self._bundle
        ps._filter = self._filter.copy()
        for k, v in kwargs.items():
            if k in _meta_fields_filter:
                ps._filter[k] = v
        if twig is not None:
            # try to guess necessary additions to filter
            # twigsplit = twig.split('@')
            for attr in _meta_fields_twig:
                tag = getattr(ps, attr)
                if tag in twigsplit:
                    ps._filter[attr] = tag
        return ps

    def exclude(self, twig=None, check_visible=True, check_default=True, **kwargs):
        """
        Exclude the results from this filter from the current
        <phoebe.parameters.ParameterSet>.

        See also:
        * <phoebe.parameters.ParameterSet.filter>
        * <phoebe.parameters.ParameterSet.filter_or_get>
        * <phoebe.parameters.ParameterSet.get>
        * <phoebe.parameters.ParameterSet.get_parameter>
        * <phoebe.parameters.ParameterSet.get_or_create>

        Arguments
        -----------
        * `twig` (str, optional, default=None): the search twig - essentially a single
            string with any delimiter (ie '@') that will be parsed
            into any of the meta-tags.  Example: instead of
            `b.filter(context='component', component='starA')`, you
            could do `b.filter('starA@component')`.
        * `check_visible` (bool, optional, default=True): whether to hide invisible
            parameters.  These are usually parameters that do not
            play a role unless the value of another parameter meets
            some condition.
        * `check_default` (bool, optional, default=True): whether to exclude parameters which
            have a _default tag (these are parameters which solely exist
            to provide defaults for when new parameters or datasets are
            added and the parameter needs to be copied appropriately).
            Defaults to True.
        * `**kwargs`:  meta-tags to search (ie. 'context', 'component',
            'model', etc).  See <phoebe.parameters.ParameterSet.meta>
            for all possible options.

        Returns
        ----------
        * the resulting <phoebe.parameters.ParameterSet>.
        """
        return self - self.filter(twig=twig,
                                  check_visible=check_visible,
                                  check_default=check_default,
                                  **kwargs)

    def get_parameter(self, twig=None, **kwargs):
        """
        Get a <phoebe.parameters.Parameter> from this
        <phoebe.parameters.ParameterSet>.  This is identical to
        <phoebe.parameters.ParameterSet.get>.

        See also:
        * <phoebe.parameters.ParameterSet.filter>
        * <phoebe.parameters.ParameterSet.filter_or_get>
        * <phoebe.parameters.ParameterSet.exclude>
        * <phoebe.parameters.ParameterSet.get_or_create>

        Arguments
        -----------
        * `twig` (str, optional, default=None): the search twig - essentially a single
            string with any delimiter (ie '@') that will be parsed
            into any of the meta-tags.  Example: instead of
            `b.filter(context='component', component='starA')`, you
            could do `b.filter('starA@component')`.
        * `check_visible` (bool, optional, default=True): whether to hide invisible
            parameters.  These are usually parameters that do not
            play a role unless the value of another parameter meets
            some condition.
        * `check_default` (bool, optional, default=True): whether to exclude parameters which
            have a _default tag (these are parameters which solely exist
            to provide defaults for when new parameters or datasets are
            added and the parameter needs to be copied appropriately).
            Defaults to True.
        * `**kwargs`:  meta-tags to search (ie. 'context', 'component',
            'model', etc).  See <phoebe.parameters.ParameterSet.meta>
            for all possible options.

        Returns
        --------
        * the resulting <phoebe.parameters.Parameter>.

        Raises
        -------
        * ValueError: if either 0 or more than 1 results are found
            matching the search.
        """
        return self.get(twig=twig, **kwargs)

    def get_or_create(self, qualifier, new_parameter, **kwargs):
        """
        Get a <phoebe.parameters.Parameter> from the
        <phoebe.parameters.ParameterSet>. If it does not exist,
        create and attach it.

        Note: running this on a ParameterSet that is NOT a
        <phoebe.frontend.bundle.Bundle>,
        will NOT add the Parameter to the Bundle, but only the temporary
        ParameterSet.

        See also:
        * <phoebe.parameters.ParameterSet.filter>
        * <phoebe.parameters.ParameterSet.filter_or_get>
        * <phoebe.parameters.ParameterSet.exclude>
        * <phoebe.parameters.ParameterSet.get>
        * <phoebe.parameters.ParameterSet.get_parameter>

        Arguments
        ----------
        * `qualifier` (string): the qualifier of the Parameter.
            **NOTE**: this must be a qualifier, not a twig.
        * `new_parameter`: (<phoebe.parameters.Parameter>): the parameter to
            attach if no result is found.
        * `**kwargs`: meta-tags to use when filtering, including `check_visible` and
            `check_default`.  See <phoebe.parameters.ParameterSet.filter_or_get>.

        Returns
        ---------
        * (<phoebe.parameters.Parameter, bool): the Parameter object (either
            from filtering or newly created) and a boolean telling whether the
            Parameter was created or not.

        Raises
        -----------
        * ValueError: if more than 1 result was found using the filter criteria.
        """
        ps = self.filter_or_get(qualifier=qualifier, **kwargs)
        if isinstance(ps, Parameter):
            return ps, False
        elif len(ps):
            # TODO: custom exception?
            raise ValueError("more than 1 result was found")
        else:
            self._attach_params(ParameterSet([new_parameter]), **kwargs)

            logger.debug("creating and attaching new parameter: {}".format(new_parameter.qualifier))

            return self.filter_or_get(qualifier=qualifier, **kwargs), True

    def _remove_parameter(self, param):
        """
        Remove a Parameter from the ParameterSet

        :parameter param: the :class:`Parameter` object to be removed
        :type param: :class:`Parameter`
        """
        # TODO: check to see if protected (required by a current constraint or
        # by a backend)
        self._params = [p for p in self._params if p != param]

    def remove_parameter(self, twig=None, **kwargs):
        """
        Remove a <phoebe.parameters.Parameter> from the
        <phoebe.parameters.ParameterSet>.

        Note: removing Parameters from a ParameterSet will not remove
        them from any parent ParameterSets
        (including the <phoebe.fontend.bundle.Bundle>).

        Arguments
        --------
        * `twig` (string, optional, default=None): the twig to search for the
            parameter (see <phoebe.parameters.ParameterSet.get>)
        * `**kwargs`: meta-tags to use when filtering, including `check_visible` and
            `check_default`.  See <phoebe.parameters.ParameterSet.get>.

        Raises
        ------
        * ValueError: if 0 or more than 1 results are found using the
                provided filter criteria.
        """
        param = self.get(twig=twig, **kwargs)

        self._remove_parameter(param)

    def remove_parameters_all(self, twig=None, **kwargs):
        """
        Remove all <phoebe.parameters.Parameter> objects that match the filter
        from the <phoebe.parameters.ParameterSet>.

        Any Parameter that would be included in the resulting ParameterSet
        from a <phoebe.parameters.ParameterSet.filter> call with the same
        arguments will be removed from this ParameterSet.

        Note: removing Parameters from a ParameterSet will not remove
        them from any parent ParameterSets
        (including the <phoebe.frontend.bundle.Bundle>)

        Arguments
        --------
        * `twig` (string, optional, default=None): the twig to search for the
            parameter (see <phoebe.parameters.ParameterSet.get>)
        * `**kwargs`: meta-tags to use when filtering, including `check_visible` and
            `check_default`.  See <phoebe.parameters.ParameterSet.filter>.
        """
        params = self.filter(twig=twig, check_visible=False, check_default=False, **kwargs)

        for param in params.to_list():
            self._remove_parameter(param)

    def get_quantity(self, twig=None, unit=None,
                     default=None, t=None, **kwargs):
        """
        Get the quantity of a <phoebe.parameters.Parameter> in this
        <phoebe.parameters.ParameterSet>.

        Note: this only works for Parameter objects with a `get_quantity` method.
        These include:
        * <phoebe.parameters.FloatParameter> (see <phoebe.parameters.FloatParameter.get_quantity>)
        * <phoebe.parameters.FloatArrayParameter>

        See also:
        * <phoebe.parameters.ParameterSet.set_quantity>
        * <phoebe.parameters.ParameterSet.get_value>
        * <phoebe.parameters.ParameterSet.set_value>
        * <phoebe.parameters.ParameterSet.set_value_all>
        * <phoebe.parameters.ParameterSet.get_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit_all>

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameter.  See <phoebe.parameters.ParameterSet.get_parameter>.
        * `unit` (string or unit, optional, default=None): unit to convert the
            quantity.  If not provided or None, will use the default unit.  See
            <phoebe.parameters.ParameterSet.get_default_unit>.
        * `default` (quantity, optional, default=None): value to return if
            no results are returned by <phoebe.parameters.ParameterSet.get_parameter>
            given the value of `twig` and `**kwargs`.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter>.

        Returns
        --------
        * an astropy quantity object
        """
        # TODO: for time derivatives will need to use t instead of time (time
        # gets passed to twig filtering)

        if default is not None:
            # then we need to do a filter first to see if parameter exists
            if not len(self.filter(twig=twig, **kwargs)):
                return default

        param = self.get_parameter(twig=twig, **kwargs)

        if param.qualifier in kwargs.keys():
            # then we have an "override" value that was passed, and we should
            # just return that.
            # Example b.get_value('teff', teff=6000) returns 6000
            return kwargs.get(param.qualifier)

        return param.get_quantity(unit=unit, t=t)

    def set_quantity(self, twig=None, value=None, **kwargs):
        """
        Set the quantity of a <phoebe.parameters.Parameter> in the
        <phoebe.parameters.ParameterSet>.

        Note: this only works for Parameter objects with a `set_quantity` method.
        These include:
        * <phoebe.parameters.FloatParameter> (see <phoebe.parameters.FloatParameter>)
        * <phoebe.parameters.FloatArrayParameter>

        See also:
        * <phoebe.parameters.ParameterSet.get_quantity>
        * <phoebe.parameters.ParameterSet.get_value>
        * <phoebe.parameters.ParameterSet.set_value>
        * <phoebe.parameters.ParameterSet.set_value_all>
        * <phoebe.parameters.ParameterSet.get_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit_all>

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameter.  See <phoebe.parameters.ParameterSet.get_parameter>.
        * `value` (quantity, optional, default=None): quantity to set for the
            matched Parameter.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter> and `set_quantity`.

        Raises
        --------
        * ValueError: if a unique match could not be found via
            <phoebe.parameters.ParameterSet.get_parameter>
        """
        # TODO: handle twig having parameter key (value@, default_unit@, adjust@, etc)
        # TODO: does this return anything (update the docstring)?
        return self.get_parameter(twig=twig, **kwargs).set_quantity(value=value, **kwargs)

    def get_value(self, twig=None, unit=None, default=None, t=None, **kwargs):
        """
        Get the value of a <phoebe.parameters.Parameter> in this
        <phoebe.parameters.ParameterSet>.

        See also:
        * <phoebe.parameters.ParameterSet.get_quantity>
        * <phoebe.parameters.ParameterSet.set_quantity>
        * <phoebe.parameters.ParameterSet.set_value>
        * <phoebe.parameters.ParameterSet.set_value_all>
        * <phoebe.parameters.ParameterSet.get_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit_all>

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameter.  See <phoebe.parameters.ParameterSet.get_parameter>.
        * `unit` (string or unit, optional, default=None): unit to convert the
            value.  If not provided or None, will use the default unit.  See
            <phoebe.parameters.ParameterSet.get_default_unit>. `unit` will
            be ignored for Parameters that do not store quantities.
        * `default` (quantity, optional, default=None): value to return if
            no results are returned by <phoebe.parameters.ParameterSet.get_parameter>
            given the value of `twig` and `**kwargs`.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter>.

        Returns
        --------
        * (float/array/string) the value of the filtered
            <phoebe.parameters.Parameter>.
        """
        # TODO: for time derivatives will need to use t instead of time (time
        # gets passed to twig filtering)

        if default is not None:
            # then we need to do a filter first to see if parameter exists
            if not len(self.filter(twig=twig, **kwargs)):
                return default

        param = self.get_parameter(twig=twig, **kwargs)

        # if hasattr(param, 'default_unit'):
        # This breaks for constraint parameters
        if isinstance(param, FloatParameter) or\
                isinstance(param,FloatArrayParameter):
            return param.get_value(unit=unit, t=t, **kwargs)

        return param.get_value(**kwargs)

    def set_value(self, twig=None, value=None, **kwargs):
        """
        Set the value of a <phoebe.parameters.Parameter> in this
        <phoebe.parameters.ParameterSet>.

        Note: setting the value of a Parameter in a ParameterSet WILL
        change that Parameter across any parent ParameterSets (including
        the <phoebe.frontend.bundle.Bundle>).

        See also:
        * <phoebe.parameters.ParameterSet.get_quantity>
        * <phoebe.parameters.ParameterSet.set_quantity>
        * <phoebe.parameters.ParameterSet.get_value>
        * <phoebe.parameters.ParameterSet.set_value_all>
        * <phoebe.parameters.ParameterSet.get_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit_all>

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameter.  See <phoebe.parameters.ParameterSet.get_parameter>.
        * `value` (optional, default=None): valid value to set for the
            matched Parameter.
        * `index` (int, optional): only applicable for
            <phoebe.parmaeters.FloatArrayParameter>.  Passing `index` will call
            <phoebe.parameters.FloatArrayParameter.set_index_value> and pass
            `index` instead of <phoebe.parameters.FloatArrayParameter.set_value>.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter> and
            <phoebe.parameters.Parameter.set_value>.

        Raises
        --------
        * ValueError: if a unique match could not be found via
            <phoebe.parameters.ParameterSet.get_parameter>
        """
        # TODO: handle twig having parameter key (value@, default_unit@, adjust@, etc)
        # TODO: does this return anything (update the docstring)?
        if twig is not None and value is None and kwargs.get('allow_value_as_first_arg', True):
            # then try to support value as the first argument if no matches with twigs
            if not isinstance(twig, str):
                value = twig
                twig = None

            elif not len(self.filter(twig=twig, check_default=False, **kwargs)):
                value = twig
                twig = None

        if "index" in kwargs.keys():
            return self.get_parameter(twig=twig,
                                      **kwargs).set_index_value(value=value,
                                                                **kwargs)

        if "time" in kwargs.keys():
            if not len(self.filter(**kwargs)):
                # then let's try filtering without time and seeing if we get a
                # FloatArrayParameter so that we can use set_index_value instead
                time = kwargs.pop("time")

                param = self.get_parameter(twig=twig, **kwargs)
                if not isinstance(param, FloatArrayParameter):
                    raise TypeError

                # TODO: do we need to be more clever about time qualifier for
                # ETV datasets? TODO: is this robust enough... this won't search
                # for times outside the existing ParameterSet.  We could also
                # try param.get_parent_ps().get_parameter('time'), but this
                # won't work when outside the bundle (which is used within
                # backends.py to set fluxes, etc) print "***
                # get_parameter(qualifier='times', **kwargs)", {k:v for k,v in
                # kwargs.items() if k not in ['qualifier']}
                time_param = self.get_parameter(qualifier='times', **{k:v for k,v in kwargs.items() if k not in ['qualifier']})
                index = np.where(time_param.get_value()==time)[0]

                return param.set_index_value(value=value, index=index, **kwargs)

        return self.get_parameter(twig=twig,
                                  **kwargs).set_value(value=value,
                                                      **kwargs)

    def set_value_all(self, twig=None, value=None, check_default=False, **kwargs):
        """
        Set the value of all returned <phoebe.parameters.Parameter> objects
        in this <phoebe.parameters.ParameterSet>.

        Any Parameter that would be included in the resulting ParameterSet
        from a <phoebe.parameters.ParametSet.filter> call with the same arguments
        will have their value set.

        Note: setting the value of a Parameter in a ParameterSet WILL
        change that Parameter across any parent ParameterSets (including
        the <phoebe.frontend.bundle.Bundle>)

        See also:
        * <phoebe.parameters.ParameterSet.get_quantity>
        * <phoebe.parameters.ParameterSet.set_quantity>
        * <phoebe.parameters.ParameterSet.get_value>
        * <phoebe.parameters.ParameterSet.set_value>
        * <phoebe.parameters.ParameterSet.get_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit_all>

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameters.  See <phoebe.parameters.ParameterSet.filter>.
        * `value` (optional, default=None): valid value to set for each
            matched Parameter.
        * `index` (int, optional): only applicable for
            <phoebe.parmaeters.FloatArrayParameter>.  Passing `index` will call
            <phoebe.parameters.FloatArrayParameter.set_index_value> and pass
            `index` instead of <phoebe.parameters.FloatArrayParameter.set_value>.
        * `ignore_none` (bool, optional, default=False): if `ignore_none=True`,
            no error will be raised if the filter returns 0 results.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter> and
            <phoebe.parameters.Parameter.set_value>.

        Raises
        -------
        * ValueError: if the <phoebe.parameters.ParameterSet.filter> call with
            the given `twig` and `**kwargs` returns 0 results.  This error
            is ignored if `ignore_none=True`.
        """
        if twig is not None and value is None:
            # then try to support value as the first argument if no matches with twigs
            if not isinstance(twig, str):
                value = twig
                twig = None

            elif not len(self.filter(twig=twig, check_default=check_default, **kwargs)):
                value = twig
                twig = None

        params = self.filter(twig=twig,
                             check_default=check_default,
                             **kwargs).to_list()

        if not kwargs.pop('ignore_none', False) and not len(params):
            raise ValueError("no parameters found")

        for param in params:
            if "index" in kwargs.keys():
                return self.get_parameter(twig=twig,
                                          **kwargs).set_index_value(value=value,
                                                                    **kwargs)
            param.set_value(value=value, **kwargs)

    def get_default_unit(self, twig=None, **kwargs):
        """
        Get the default unit for a <phoebe.parameters.Parameter> in the
        <phoebe.parameters.ParameterSet>.

        Note: this only works for Parameter objects with a `get_default_unit` method.
        These include:
        * <phoebe.parameters.FloatParameter.get_default_unit>
        * <phoebe.parameters.FloatArrayParameter.get_default_unit>

        See also:
        * <phoebe.parameters.ParameterSet.get_quantity>
        * <phoebe.parameters.ParameterSet.set_quantity>
        * <phoebe.parameters.ParameterSet.get_value>
        * <phoebe.parameters.ParameterSet.set_value>
        * <phoebe.parameters.ParameterSet.set_value_all>
        * <phoebe.parameters.ParameterSet.set_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit_all>
        """
        return self.get_parameter(twig=twig, **kwargs).get_default_unit()

    def set_default_unit(self, twig=None, unit=None, **kwargs):
        """
        Set the default unit for a <phoebe.parameters.Parameter> in the
        <phoebe.parameters.ParameterSet>.

        Note: setting the default_unit of a Parameter in a ParameterSet WILL
        change that Parameter across any parent ParameterSets (including
        the <phoebe.frontend.bundle.Bundle>).

        Note: this only works for Parameter objects with a `set_default_unit` method.
        These include:
        * <phoebe.parameters.FloatParameter.set_default_unit>
        * <phoebe.parameters.FloatArrayParameter.set_default_unit>

        See also:
        * <phoebe.parameters.ParameterSet.get_quantity>
        * <phoebe.parameters.ParameterSet.set_quantity>
        * <phoebe.parameters.ParameterSet.get_value>
        * <phoebe.parameters.ParameterSet.set_value>
        * <phoebe.parameters.ParameterSet.set_value_all>
        * <phoebe.parameters.ParameterSet.get_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit_all>

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameter.  See <phoebe.parameters.ParameterSet.get_parameter>.
        * `unit` (unit, optional, default=None): valid unit to set for the
            matched Parameter.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter> and
            <phoebe.parameters.Parameter.set_value>.

        Raises
        --------
        * ValueError: if a unique match could not be found via
            <phoebe.parameters.ParameterSet.get_parameter>
        """
        if twig is not None and unit is None:
            # then try to support value as the first argument if no matches with twigs
            if isinstance(unit, u.Unit) or not isinstance(twig, str):
                unit = twig
                twig = None

            elif not len(self.filter(twig=twig, check_default=check_default, **kwargs)):
                unit = twig
                twig = None

        return self.get_parameter(twig=twig, **kwargs).set_default_unit(unit)

    def set_default_unit_all(self, twig=None, unit=None, **kwargs):
        """
        Set the default unit for all <phoebe.parameters.Parameter> objects in the
        <phoebe.parameters.ParameterSet>.

        Any Parameter that would be included in the resulting ParameterSet
        from a <phoebe.parameters.ParametSet.filter> call with the same arguments
        will have their default_unit set.

        Note: setting the default_unit of a Parameter in a ParameterSet WILL
        change that Parameter across any parent ParameterSets (including
        the <phoebe.frontend.bundle.Bundle>).

        Note: this only works for Parameter objects with a `set_default_unit` method.
        These include:
        * <phoebe.parameters.FloatParameter.set_default_unit>
        * <phoebe.parameters.FloatArrayParameter.set_default_unit>

        See also:
        * <phoebe.parameters.ParameterSet.get_quantity>
        * <phoebe.parameters.ParameterSet.set_quantity>
        * <phoebe.parameters.ParameterSet.get_value>
        * <phoebe.parameters.ParameterSet.set_value>
        * <phoebe.parameters.ParameterSet.set_value_all>
        * <phoebe.parameters.ParameterSet.get_default_unit>
        * <phoebe.parameters.ParameterSet.set_default_unit>


        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameters.  See <phoebe.parameters.ParameterSet.filter>.
        * `unit` (unit, optional, default=None): valid unit to set for each
            matched Parameter.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter> and
            `set_default_unit`.
        """
        # TODO: add support for ignore_none as per set_value_all
        if twig is not None and unit is None:
            # then try to support value as the first argument if no matches with twigs
            if isinstance(unit, u.Unit) or not isinstance(twig, str):
                unit = twig
                twig = None

            elif not len(self.filter(twig=twig, check_default=check_default, **kwargs)):
                unit = twig
                twig = None

        for param in self.filter(twig=twig, **kwargs).to_list():
            param.set_default_unit(unit)

    def get_adjust(self, twig=None, **kwargs):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def set_adjust(self):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def set_adjust_all(self):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def get_enabled(self, twig=None, **kwargs):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def set_enabled(self):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def get_description(self, twig=None, **kwargs):
        """
        Get the description of a <phoebe.parameters.Parameter> in the
        <phoebe.parameters.ParameterSet>.

        This is simply a shortcut to <phoebe.parameters.ParameterSet.get_parameter>
        and <phoebe.parameters.Parameter.get_description>.

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to be used to access
            the Parameter.  See <phoebe.parameters.ParameterSet.get_parameter>.
        * `**kwargs`: filter options to be passed along to
            <phoebe.parameters.ParameterSet.get_parameter>.

        Returns
        --------
        * (string) the description of the filtered
            <phoebe.parameters.Parameter>.
        """
        return self.get_parameter(twig=twig, **kwargs).get_description()

    def get_prior(self, twig=None, **kwargs):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def set_prior(self):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def remove_prior(self):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def get_posterior(self, twig=None, **kwargs):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError

    def remove_posterior(self):
        """
        [NOT IMPLEMENTED]

        raises NotImplementedError: because it isn't
        """
        raise NotImplementedError


    def compute_residuals(self, model=None, dataset=None, component=None, as_quantity=True):
        """
        Compute residuals between the observed values in a dataset and the
        corresponding model.

        Currently supports the following datasets:
        * <phoebe.parameters.dataset.lc>
        * <phoebe.parameters.dataset.rv>

        If necessary (due to the `compute_times`/`compute_phases` parameters
        or a change in the dataset `times` since the model was computed),
        interpolation will be handled, in time-space if possible, and in
        phase-space otherwise. See
        <phoebe.parameters.FloatArrayParameter.interp_value>.

        Arguments
        -----------
        * `model` (string, optional, default=None): model to compare against
            observations.  Required if more than one model exist.
        * `dataset` (string, optional, default=None): dataset for comparison.
            Required if more than one dataset exist.
        * `component` (string, optional, default=None): component for comparison.
            Required only if more than one component exist in the dataset (for
            RVs, for example)
        * `as_quantity` (bool, default=True): whether to return a quantity object.

        Returns
        -----------
        * (array) array of residuals with same length as the times array of the
            corresponding dataset.

        Raises
        ----------
        * ValueError: if the provided filter options (`model`, `dataset`,
            `component`) do not result in a single parameter for comparison.
        * NotImplementedError: if the dataset kind is not supported for residuals.
        """
        if not len(self.filter(context='dataset').datasets):
            dataset_ps = self._bundle.get_dataset(dataset=dataset)
        else:
            dataset_ps = self.filter(dataset=dataset, context='dataset')

        dataset_kind = dataset_ps.filter(kind='*dep').kind

        if not len(self.filter(context='model').models):
            model_ps = self._bundle.get_model(model=model).filter(dataset=dataset, component=component)
        else:
            model_ps = self.filter(model=model, context='model').filter(dataset=dataset, component=component)

        if dataset_kind == 'lc_dep':
            qualifier = 'fluxes'
        elif dataset_kind == 'rv_dep':
            qualifier = 'rvs'
        else:
            # TODO: lp compared for a given time interpolating in wavelength?
            # NOTE: add to documentation if adding support for other datasets
            raise NotImplementedError("compute_residuals not implemented for dataset with kind='{}' (model={}, dataset={}, component={})".format(dataset_kind, model, dataset, component))

        dataset_param = dataset_ps.get_parameter(qualifier, component=component)
        model_param = model_ps.get_parameter(qualifier)

        # TODO: do we need to worry about conflicting units?
        # NOTE: this should automatically handle interpolating in phases, if necessary
        times = dataset_ps.get_value('times', component=component)
        if not len(times):
            raise ValueError("no times in the dataset: {}@{}".format(dataset, component))
        if not len(dataset_param.get_value()) == len(times):
            if len(dataset_param.get_value())==0:
                # then the dataset was empty, so let's just return an empty array
                if as_quantity:
                    return np.asarray([]) * dataset_param.default_unit
                else:
                    return np.asarray([])
            else:
                raise ValueError("{}@{}@{} and {}@{}@{} do not have the same length, cannot compute residuals".format(qualifier, component, dataset, 'times', component, dataset))

        if dataset_param.default_unit != model_param.default_unit:
            raise ValueError("model and dataset do not have the same default_unit, cannot interpolate")

        residuals = np.asarray(dataset_param.interp_value(times=times) - model_param.interp_value(times=times))

        if as_quantity:
            return residuals * dataset_param.default_unit
        else:
            return residuals



    def _unpack_plotting_kwargs(self, **kwargs):



        # We now need to unpack if the contents within kwargs contain multiple
        # contexts/datasets/kinds/components/etc.
        # the dataset tag can appear in the compute context as well, so if the
        # context tag isn't in kwargs, let's default it to dataset or model
        kwargs.setdefault('context', ['dataset', 'model'])

        filter_kwargs = {}
        for k in list(self.meta.keys())+['twig']:
            if k in ['time']:
                # time handled later
                continue
            filter_kwargs[k] = kwargs.pop(k, None)

        ps = self.filter(check_visible=False, **filter_kwargs).exclude(qualifier=['compute_times', 'compute_phases'])

        if 'time' in kwargs.keys() and ps.kind in ['mesh', 'mesh_syn', 'lp', 'lp_syn']:
            ps = ps.filter(time=kwargs.get('time'))

        # If ps returns more than one dataset/model/component, then we need to
        # loop and plot all.  This will automatically rotate through colors
        # (unless the user provided color in a kwarg).  To choose individual
        # styling, the user must make individual calls and provide the styling
        # options as kwargs.

        # we'll return a list of dictionaries, with each dictionary prepared
        # to pass directly to autofig
        return_ = []

        if len(ps.contexts) > 1:
            for context in ps.contexts:
                this_return = ps.filter(check_visible=False, context=context)._unpack_plotting_kwargs(**kwargs)
                return_ += this_return
            return return_

        if len(ps.datasets)>1 and ps.kind not in ['mesh']:
            for dataset in ps.datasets:
                this_return = ps.filter(check_visible=False, dataset=dataset)._unpack_plotting_kwargs(**kwargs)
                return_ += this_return
            return return_

        # For kinds, we want to ignore the deps - those won't have arrays
        kinds = [m for m in ps.kinds if m[-3:] != 'dep']

        # If we are asking to plot a dataset that also shows up in columns in
        # the mesh, then remove the mesh kind.  In other words: mesh stuff
        # will only be plotted if mesh is the only kind in the filter.
        pskinds = ps.kinds
        if len(pskinds) > 1 and 'mesh' in pskinds:
            pskinds.remove('mesh')

        if len(kinds) == 1 and len(pskinds) > 1:
            # then we need to filter to exclude the dep
            ps = ps.filter(check_visible=False, kind=kinds[0])
            pskinds = [kinds[0]]

        if len(ps.kinds) > 1:
            for kind in [m for m in pskinds if m[-3:]!='dep']:
                this_return = ps.filter(check_visible=False, kind=kind)._unpack_plotting_kwargs(**kwargs)
                return_ += this_return
            return return_

        if len(ps.models) > 1:
            for model in ps.models:
                # TODO: change linestyle for models instead of color?
                this_return = ps.filter(check_visible=False, model=model)._unpack_plotting_kwargs(**kwargs)
                return_ += this_return
            return return_

        if len(ps.times) > 1 and kwargs.get('x', None) not in ['time', 'times'] and kwargs.get('y', None) not in ['time', 'times'] and kwargs.get('z', None) not in ['time', 'times']:
            # only meshes, lp, spectra, etc will be able to iterate over times
            for time in ps.times:
                this_return = ps.filter(check_visible=False, time=time)._unpack_plotting_kwargs(**kwargs)
                return_ += this_return
            return return_

        if len(ps.components) > 1:
            return_ = []
            for component in ps.components:
                this_return = ps.filter(check_visible=False, component=component)._unpack_plotting_kwargs(**kwargs)
                return_ += this_return
            return return_


        if ps.kind in ['mesh', 'mesh_syn', 'orb', 'orb_syn'] and \
                ps.context == 'dataset':
            # nothing to plot here... at least for now
            return []

        if not len(ps):
            return []

        # Now that we've looped over everything, we can assume that we are dealing
        # with a SINGLE call.  We need to prepare kwargs so that it can be passed
        # to autofig.plot or autofig.mesh


        #### SUPPORT DICTIONARIES IN KWARGS
        # like color={'primary': 'red', 'secondary': 'blue'} or
        # linestyle={'rv01': 'solid', 'rv02': 'dashed'}
        # here we need to filter any kwargs that are dictionaries if they match
        # the current ps
        for k,v in kwargs.items():
            if isinstance(v, dict) and 'kwargs' not in k:
                # overwrite kwargs[k] based on any match in v
                match = None
                for kk,vv in v.items():
                    if kk in ps.meta.values():
                        if match is not None:
                            raise ValueError("dictionary {}={} is not unique for {}".format(k,v, ps.meta))
                        match = vv

                if match is not None:
                    kwargs[k] = match
                else:
                    # remove from the dictionary and fallback on defaults
                    _dump = kwargs.pop(k)

        #### ALIASES
        if 'color' in kwargs.keys() and 'colors' not in kwargs.keys() and 'c' not in kwargs.keys():
            logger.warning("assuming you meant 'c' instead of 'color'")
            kwargs['c'] = kwargs.pop('color')
        elif 'colors' in kwargs.keys() and 'c' not in kwargs.keys():
            logger.warning("assuming you meant 'c' instead of 'colors'")
            kwargs['c'] = kwargs.pop('colors')
        if 'facecolor' in kwargs.keys() and 'facecolors' not in kwargs.keys() and 'fc' not in kwargs.keys():
            logger.warning("assuming you meant 'fc' instead of 'facecolor'")
            kwargs['fc'] = kwargs.pop('facecolor')
        elif 'facecolors' in kwargs.keys() and 'fc' not in kwargs.keys():
            logger.warning("assuming you meant 'fc' instead of 'facecolors'")
            kwargs['fc'] = kwargs.pop('facecolors')
        if 'edgecolor' in kwargs.keys() and 'edgecolors' not in kwargs.keys() and 'ec' not in kwargs.keys():
            logger.warning("assuming you meant 'ec' instead of 'edgecolor'")
            kwargs['ec'] = kwargs.pop('edgecolor')
        elif 'edgecolors' in kwargs.keys() and 'ec' not in kwargs.keys():
            logger.warning("assuming you meant 'ec' instead of 'edgecolors'")
            kwargs['ec'] = kwargs.pop('edgecolors')

        for d in ['x', 'y', 'z']:
            if '{}error'.format(d) not in kwargs.keys():
                if '{}errors'.format(d) in kwargs.keys():
                    logger.warning("assuming you meant '{}error' instead of '{}errors'".format(d,d))
                    kwargs['{}error'.format(d)] = kwargs.pop('{}errors'.format(d))

        def _kwargs_fill_dimension(kwargs, direction, ps):
            # kwargs[direction] is currently one of the following:
            # * twig/qualifier
            # * array/float
            # * string (applicable for color dimensions)
            #
            # if kwargs[direction] is a twig, then we need to change the
            # entry in the dictionary to be the data-array itself

            current_value = kwargs.get(direction, None)

            #### RETRIEVE DATA ARRAYS
            if isinstance(current_value, str):
                if ps.kind not in ['mesh'] and direction in ['fc', 'ec']:
                    logger.warning("fc and ec are not allowable for dataset={} with kind={}, ignoring {}={}".format(ps.dataset, ps.kind, direction, current_value))
                    _dump = kwargs.pop(direction)
                    return kwargs

                elif current_value in ['None', 'none']:
                    return kwargs

                elif '@' in current_value or current_value in ps.qualifiers or \
                        (current_value in ['xs', 'ys', 'zs'] and 'xyz_elements' in ps.qualifiers) or \
                        (current_value in ['us', 'vs', 'ws'] and 'uvw_elements' in ps.qualifiers):

                    if kwargs['autofig_method'] == 'mesh' and current_value in ['xs', 'ys', 'zs']:
                        # then we actually need to unpack from the xyz_elements
                        verts = ps.get_quantity(qualifier='xyz_elements')
                        array_value = verts.value[:, :, ['xs', 'ys', 'zs'].index(current_value)] * verts.unit
                    elif kwargs['autofig_method'] == 'mesh' and current_value in ['us', 'vs', 'ws']:
                        # then we actually need to unpack from the uvw_elements
                        verts = ps.get_quantity(qualifier='uvw_elements')
                        array_value = verts.value[:, :, ['us', 'vs', 'ws'].index(current_value)] * verts.unit
                    elif current_value in ['time', 'times'] and 'residuals' in kwargs.values():
                        # then we actually need to pull the times from the dataset instead of the model since the length may not match
                        array_value = ps._bundle.get_value('times', dataset=ps.dataset, component=ps.component, context='dataset')
                    else:
                        if len(ps.filter(current_value, check_visible=False))==1:
                            array_value = ps.get_quantity(current_value, check_visible=False)
                        elif len(ps.filter(current_value, check_visible=False).times) > 1 and ps.get_value(current_value, time=ps.filter(current_value, check_visible=False).times[0]):
                            # then we'll assume we have something like volume vs times.  If not, then there may be a length mismatch issue later
                            unit = ps.get_quantity(current_value, time=ps.filter(current_value).times[0]).unit
                            array_value = np.array([ps.get_quantity(current_value, time=time, check_visible=False).to(unit).value for time in ps.filter(current_value, check_visible=False).times])*unit
                        else:
                            raise ValueError("could not find Parameter for {} in {}".format(current_value, ps.meta))

                    kwargs[direction] = array_value

                    if ps.context == 'dataset' and current_value in sigmas_avail:
                        # then let's see if there are errors
                        errorkey = '{}error'.format(direction)
                        errors = kwargs.get(errorkey, None)
                        if isinstance(errors, np.ndarray) or isinstance(errors, float) or isinstance(errors, int):
                            kwargs[errorkey] = errors
                        elif isinstance(errors, str):
                            errors = ps.get_quantity(kwargs.get(errorkey))
                            kwargs[errorkey] = errors
                        else:
                            sigmas = ps.get_quantity('sigmas', check_visible=False)
                            if len(sigmas):
                                kwargs.setdefault(errorkey, sigmas)

                    # now let's set the label for the dimension from the qualifier/twig
                    kwargs.setdefault('{}label'.format(direction), _plural_to_singular.get(current_value, current_value))

                    # we'll also keep the qualifier around - autofig doesn't use this
                    # but we'll keep it so we can set some defaults
                    kwargs['{}qualifier'.format(direction)] = current_value

                    return kwargs

                elif current_value in ['time', 'times'] and len(ps.times):
                    kwargs[direction] = sorted([float(t) for t in ps.times])
                    kwargs['{}qualifier'] = None
                    return kwargs

                elif current_value in ['wavelengths'] and ps.time is not None:
                    # these are not tagged with the time, so we need to find them
                    full_dataset_meta = {k:v for k,v in ps.meta.items() if k not in ['qualifier', 'time']}
                    full_dataset_ps = ps._bundle.filter(**full_dataset_meta)
                    candidate_params = full_dataset_ps.filter(current_value)
                    if len(candidate_params) == 1:
                        kwargs[direction] = candidate_params.get_quantity()
                        kwargs.setdefault('{}label'.format(direction), _plural_to_singular.get(current_value, current_value))
                        kwargs['{}qualifier'.format(direction)] = current_value
                        return kwargs
                    elif len(candidate_params) > 1:
                        raise ValueError("could not find single match for {}={}, found: {}".format(direction, current_value, candidate_params.twigs))
                    else:
                        # then len(candidate_params) == 0
                        raise ValueError("could not find a match for {}={}".format(direction, current_value))

                elif current_value.split(':')[0] in ['phase', 'phases']:
                    component_phase = current_value.split(':')[1] \
                                        if len(current_value.split(':')) > 1 \
                                        else None


                    if 'residuals' in kwargs.values():
                        # then we actually need to pull the times from the dataset instead of the model since the length may not match
                        times = ps._bundle.get_value('times', dataset=ps.dataset, component=ps.component, context='dataset')
                    elif ps.kind in ['etvs']:
                        times = ps.get_value('time_ecls', unit=u.d)
                    else:
                        times = ps.get_value('times', unit=u.d)

                    kwargs[direction] = self._bundle.to_phase(times, component=component_phase, t0=kwargs.get('t0', 't0_supconj')) * u.dimensionless_unscaled

                    kwargs.setdefault('{}label'.format(direction), 'phase:{}'.format(component_phase) if component_phase is not None else 'phase')

                    kwargs['{}qualifier'.format(direction)] = current_value

                    # and we'll set the linebreak so that decreasing phase breaks any lines (allowing for phase wrapping)
                    kwargs.setdefault('linebreak', '{}-'.format(direction))

                    return kwargs

                elif current_value in ['residuals']:
                    if ps.model is None:
                        logger.info("skipping residuals for dataset")
                        return {}

                    # we're currently within the MODEL context
                    kwargs[direction] = ps.compute_residuals(model=ps.model, dataset=ps.dataset, component=ps.component, as_quantity=True)
                    kwargs.setdefault('{}label'.format(direction), '{} residuals'.format({'lc': 'flux', 'rv': 'rv'}.get(ps.kind, '')))
                    kwargs['{}qualifier'.format(direction)] = current_value
                    kwargs.setdefault('linestyle', 'none')
                    kwargs.setdefault('marker', '+')

                    return kwargs

                elif direction in ['c', 'fc', 'ec']:
                    # then there is the possibility of referring to a column
                    # that technnically is attached to a different dataset in
                    # the same mesh (e.g. rvs@rv01 inside kind=mesh).  Let's
                    # check for that first.

                    if ps.kind in ['mesh'] and ps._bundle is not None:
                        full_mesh_meta = {k:v for k,v in ps.meta.items() if k not in ['qualifier', 'dataset']}
                        full_mesh_ps = ps._bundle.filter(**full_mesh_meta)
                        candidate_params = full_mesh_ps.filter(current_value)
                        if len(candidate_params) == 1:
                            kwargs[direction] = candidate_params.get_quantity()
                            kwargs.setdefault('{}label'.format(direction), _plural_to_singular.get(current_value, current_value))
                            kwargs['{}qualifier'.format(direction)] = current_value
                            return kwargs
                        elif len(candidate_params) > 1:
                            raise ValueError("could not find single match for {}={}, found: {}".format(direction, current_value, candidate_params.twigs))
                        elif current_value in autofig.cyclers._mplcolors:
                            # no need to raise a warning, this is a valid color
                            pass
                        else:
                            # maybe a hex or anything not in the cycler? or should we raise an error instead?
                            logger.warning("could not find Parameter match for {}={} at time={}, assuming named color".format(direction, current_value, full_mesh_meta['time']))

                    # Nothing has been found, so we'll assume the string is
                    # the name of a color.  If the color isn't accepted by
                    # autofig then autofig will raise an error listing the
                    # list of allowed colors.
                    return kwargs

                else:
                    raise ValueError("could not recognize {} for {} direction in dataset='{}', ps.meta={}".format(current_value, direction, ps.dataset, ps.meta))

            elif _instance_in(current_value, np.ndarray, list, tuple, float, int):
                # then leave it as-is
                return kwargs
            elif current_value is None:
                return kwargs
            else:
                raise NotImplementedError


        #### DIRECTION DEFAULTS
        # define defaults for directions based on ps.kind
        if ps.kind in ['mesh', 'mesh_syn']:
            # first determine from any passed values if we're in xyz or uvw
            # (do not allow mixing between roche and POS)
            detected_qualifiers = [kwargs[af_direction] for af_direction in ['x', 'y', 'z'] if af_direction in kwargs.keys()]
            if len(detected_qualifiers):
                coordinate_systems = set(['uvw' if detected_qualifier in ['us', 'vs', 'ws'] else 'xyz' for detected_qualifier in detected_qualifiers if detected_qualifier in ['us', 'vs', 'ws', 'xs', 'ys', 'zs']])


                if len(coordinate_systems) == 1:
                    coordinates = ['xs', 'ys', 'zs'] if list(coordinate_systems)[0] == 'xyz' else ['us', 'vs', 'ws']
                elif len(coordinate_systems) > 1:
                    # then we're mixing roche and POS
                    raise ValueError("cannot mix xyz (roche) and uvw (pos) coordinates while plotting")
                else:
                    # then len(coordinate_system) == 0
                    coordinates = ['us', 'vs', 'ws']

            else:
                coordinates = ['us', 'vs', 'ws']


            defaults = {}
            # first we need to know if any of the af_directions are set to
            # something other than cartesian by the user (in which case we need
            # to check for the parameter's existence before defaulting and use
            # scatter instead of mesh plot)
            mesh_all_cartesian = True
            for af_direction in ['x', 'y', 'z']:
                if kwargs.get(af_direction, None) not in [None] + coordinates:
                    mesh_all_cartesian = False

            # now we need to loop again and set any missing defaults
            for af_direction in ['x', 'y', 'z']:
                if af_direction in kwargs.keys():
                    # then default doesn't matter, but we'll set it at what it is
                    defaults[af_direction] = kwargs[af_direction]

                    if kwargs[af_direction] in coordinates:
                        # the provided qualifier could be something else (ie teffs)
                        # in which case we'll end up doing a scatter instead of
                        # a mesh plot

                        # now we'll remove from coordinates still available
                        coordinates.remove(kwargs[af_direction])
                else:
                    # we'll take the first entry remaining in coordinates
                    coordinate = coordinates.pop(0)

                    # if mesh_all_cartesian then we're doing a mesh plot
                    # and know that we have xyz/uvw_elements available.
                    # Otherwise, we need to check and only apply the default
                    # if that parameter (xs, ys, zs, us, vs, ws) is available.
                    # Either way, we've removed this from the coordinates
                    # list so the next direction will fill from the next available
                    if mesh_all_cartesian or coordinate in ps.qualifiers:
                        defaults[af_direction] = coordinate


            # since we'll be selecting from the time tag, we need a non-zero tolerance
            kwargs.setdefault('itol', 1e-6)

            if mesh_all_cartesian:
                # then we'll be doing a mesh plot, so set some reasonable defaults

                # units will have handled this in POS (uvw) coordinates, but not
                # Roche (xyz) as those are unitless
                kwargs.setdefault('equal_aspect', True)

                # we want the wireframe by default
                kwargs.setdefault('ec', 'black')
                kwargs.setdefault('fc', 'white')
            else:
                # then even though the scatter may be rs vs cartesian with same
                # units, let's default to disabling equal aspect ratio
                kwargs.setdefault('equal_aspect', False)

            sigmas_avail = []

        elif ps.kind in ['orb', 'orb_syn']:
            # similar logic to meshes above, except we only have uvw
            coordinates = ['us', 'vs', 'ws']

            defaults = {}
            for af_direction in ['x', 'y', 'z']:
                if af_direction in kwargs.keys():
                    # then default doesn't matter, but we'll set it at what it is
                    defaults[af_direction] = kwargs[af_direction]

                    if kwargs[af_direction] in coordinates:
                        # the provided qualifier could be something else (ie teffs)
                        # in which case we'll end up doing a scatter instead of
                        # a mesh plot

                        # now we'll remove from coordinates still available
                        coordinates.remove(kwargs[af_direction])
                else:
                    # we'll take the first entry remaining in coordinates
                    defaults[af_direction] = coordinates.pop(0)

            if kwargs.get('projection', None) != '3d':
                defaults['z'] = 0

            sigmas_avail = []
        elif ps.kind in ['lc', 'lc_syn']:
            defaults = {'x': 'times',
                        'y': 'fluxes',
                        'z': 0}
            sigmas_avail = ['fluxes']
        elif ps.kind in ['rv', 'rv_syn']:
            defaults = {'x': 'times',
                        'y': 'rvs',
                        'z': 0}
            sigmas_avail = ['rvs']
        elif ps.kind in ['lp', 'lp_syn']:
            defaults = {'x': 'wavelengths',
                        'y': 'flux_densities',
                        'z': 0}
            sigmas_avail = ['flux_densities']

            # since we'll be selecting from the time tag, we need a non-zero tolerance
            kwargs.setdefault('itol', 1e-6)

            # if animating or drawing at a single time, we want to show only
            # the selected item, not all and then highlight the selected item
            kwargs.setdefault('highlight_linestyle', kwargs.get('linestyle', 'solid'))
            kwargs.setdefault('highlight_marker', 'None')
            kwargs.setdefault('highlight_size', kwargs.get('size', 0.02))  # this matches the default in autofig for call._sizes
            kwargs.setdefault('uncover', True)
            kwargs.setdefault('trail', 0)

        elif ps.kind in ['etv', 'etv_syn']:
            defaults = {'x': 'time_ecls',
                        'y': 'etvs',
                        'z': 0}
            sigmas_avail = ['etvs']
        else:
            logger.debug("could not find plotting defaults for ps.meta: {}, ps.twigs: {}".format(ps.meta, ps.twigs))
            raise NotImplementedError("defaults for kind {} (dataset: {}) not yet implemented".format(ps.kind, ps.dataset))

        #### DETERMINE AUTOFIG PLOT TYPE
        # NOTE: this must be done before calling _kwargs_fill_dimension below
        cartesian = ['xs', 'ys', 'zs', 'us', 'vs', 'ws']
        if ps.kind in ['mesh']:
            if mesh_all_cartesian:
                kwargs['autofig_method'] = 'mesh'
            else:
                kwargs['autofig_method'] = 'plot'

            if self.time is not None:
                kwargs['i'] = float(self.time)
        else:
            kwargs['autofig_method'] = 'plot'

        #### GET DATA ARRAY FOR EACH AUTOFIG "DIRECTION"
        for af_direction in ['x', 'y', 'z', 'c', 's', 'fc', 'ec']:
            # set the array and dimension label
            # logger.debug("af_direction={}, kwargs={}, defaults={}".format(af_direction, kwargs, defaults))
            if af_direction not in kwargs.keys() and af_direction in defaults.keys():
                # don't want to use setdefault here because we don't want an
                # entry if the af_direction is not in either dict
                kwargs[af_direction] = defaults[af_direction]

            # logger.debug("_kwargs_fill_dimension {} {} {}".format(kwargs, af_direction, ps.twigs))
            kwargs = _kwargs_fill_dimension(kwargs, af_direction, ps)

        #### HANDLE AUTOFIG'S INDENPENDENT VARIABLE DIRECTION (i)
        # try to find 'times' in the cartesian dimensions:
        iqualifier = kwargs.pop('i', 'times')
        for af_direction in ['x', 'y', 'z']:
            if kwargs['autofig_method'] != 'mesh' and (kwargs.get('{}label'.format(af_direction), None) in ['times', 'time_ecls'] if iqualifier=='times' else [iqualifier]):
                kwargs['i'] = af_direction
                kwargs['iqualifier'] = None
                break
        else:
            # then we didn't find a match, so we'll either pass the time
            # (for a mesh) or times array (otherwise)
            if ps.time is not None:
                # a single mesh will pass just that single time on as the
                # independent variable/direction
                if iqualifier=='times':
                    kwargs['i'] = float(ps.time)
                    kwargs['iqualifier'] = 'ps.times'
                elif isinstance(iqualifier, float):
                    kwargs['i'] = iqualifier
                    kwargs['iqualifier'] = iqualifier
                elif iqualifier.split(':')[0] == 'phases':
                    # TODO: need to test this
                    component = iqualifier.split(':')[1] if len(iqualifier.split(':')) > 1 else None
                    kwargs['i'] = self._bundle.to_phase(float(ps.time), component=component)
                    kwargs['iqualifier'] = iqualifier
                else:
                    raise NotImplementedError
            elif ps.kind in ['etv']:
                if iqualfier=='times':
                    kwargs['i'] = ps.get_quantity(qualifier='time_ecls')
                    kwargs['iqualifier'] = 'time_ecls'
                elif iqualifier.split(':')[0] == 'phases':
                    # TODO: need to test this
                    icomponent = iqualifier.split(':')[1] if len(iqualifier.split(':')) > 1 else None
                    kwargs['i'] = self._bundle.to_phase(ps.get_quantity(qualifier='time_ecls'), component=icomponent)
                    kwargs['iqualifier'] = iqualifier
                else:
                    raise NotImplementedError
            else:
                if iqualifier=='times':
                    kwargs['i'] = ps.get_quantity(qualifier='times')
                    kwargs['iqualifier'] = 'times'
                elif iqualifier.split(':')[0] == 'phases':
                    # TODO: need to test this
                    icomponent = iqualifier.split(':')[1] if len(iqualifier.split(':')) > 1 else None
                    kwargs['i'] = self._bundle.to_phase(ps.get_quantity(qualifier='times'), component=icomponent)
                    kwargs['iqualifier'] = iqualifier
                else:
                    raise NotImplementedError

        #### STYLE DEFAULTS
        # set defaults for marker/linestyle depending on whether this is
        # observational or synthetic data
        if ps.context == 'dataset':
            kwargs.setdefault('linestyle', 'none')
        elif ps.context == 'model':
            if ps.kind in ['mesh', 'mesh_syn'] and kwargs['autofig_method'] == 'plot':
                kwargs.setdefault('marker', '^')
                kwargs.setdefault('linestyle', 'none')
            else:
                kwargs.setdefault('marker', 'none')

        # set defaults for colormap and symmetric limits
        for af_direction in ['c', 'fc', 'ec']:
            qualifier = kwargs.get('{}qualifier'.format(af_direction), '').split('@')[0]
            if qualifier in ['rvs']:
                kwargs.setdefault('{}map'.format(af_direction), 'RdBu_r')
                if kwargs['{}map'.format(af_direction)] == 'RdBu_r':
                    # only apply symmetric default if taking the colormap default
                    kwargs.setdefault('{}lim'.format(af_direction), 'symmetric')
            elif qualifier in ['vxs', 'vys', 'vzs', 'vus', 'vvs', 'vws']:
                kwargs.setdefault('{}map'.format(af_direction), 'RdBu')
                if kwargs['{}map'.format(af_direction)] == 'RdBu':
                    # only apply symmetric default if taking the colormap default
                    kwargs.setdefault('{}lim'.format(af_direction), 'symmetric')
                kwargs.setdefault('{}lim'.format(af_direction), 'symmetric')
            elif qualifier in ['teffs']:
                kwargs.setdefault('{}map'.format(af_direction), 'afmhot')
            elif qualifier in ['loggs']:
                kwargs.setdefault('{}map'.format(af_direction), 'gnuplot')
            elif qualifier in ['visibilities']:
                kwargs.setdefault('{}map'.format(af_direction), 'RdYlGn')
                kwargs.setdefault('{}lim'.format(af_direction), (0,1))

        #### LABEL FOR LEGENDS
        attrs = ['component', 'dataset']
        if ps._bundle is not None and len(ps._bundle.models) > 1:
            attrs += ['model']
        default_label = '@'.join([getattr(ps, attr) for attr in attrs if getattr(ps, attr) is not None])
        kwargs.setdefault('label', default_label)

        return (kwargs,)

    def gcf(self):
        """
        Get the active current figure.

        See also:
        * <phoebe.parameters.ParameterSet.plot>
        * <phoebe.parameters.ParameterSet.show>
        * <phoebe.parameters.ParameterSet.savefig>
        * <phoebe.parameters.ParameterSet.clf>
        """
        if self._bundle is None:
            return autofig.gcf()

        if self._bundle._figure is None:
            self._bundle._figure = autofig.Figure()

        return self._bundle._figure

    def clf(self):
        """
        Clear/reset the active current figure.

        See also:
        * <phoebe.parameters.ParameterSet.plot>
        * <phoebe.parameters.ParameterSet.show>
        * <phoebe.parameters.ParameterSet.savefig>
        * <phoebe.parameters.ParameterSet.gcf>
        """
        if self._bundle is None:
            raise ValueError("could not find parent Bundle object")

        self._bundle._figure = None

    def plot(self, twig=None, **kwargs):
        """
        High-level wrapper around matplotlib that uses
        [autofig 1.0.0](https://github.com/kecnry/autofig/tree/1.0.0)
        under-the-hood for automated figure and animation production.

        See also:
        * <phoebe.parameters.ParameterSet.show>
        * <phoebe.parameters.ParameterSet.savefig>
        * <phoebe.parameters.ParameterSet.gcf>
        * <phoebe.parameters.ParameterSet.clf>

        Note: not all options are listed below.  See the
        [autofig](https://github.com/kecnry/autofig/tree/1.0.0)
        tutorials and documentation for more options which are passed along
        via `**kwargs`.

        Arguments
        ----------
        * `twig` (string, optional, default=None): twig to use for filtering
            prior to plotting.  See <phoebe.parameters.ParameterSet.filter>
        * `time` (float, optional): time to use for plotting/animating.
        * `times` (list/array, optional): times to use for animating (will
            override any value sent to `time`).
        * `t0` (string/float, optional): qualifier/twig or float of the t0 that
            should be used for phasing, if applicable.  If provided as a string,
            `b.get_value(t0)` needs to provide a valid float.

        * `x` (string/float/array, optional): qualifier/twig of the array to plot on the
            x-axis (will default based on the dataset-kind if not provided).
            With the exception of phase, `b.get_value(x)` needs to provide a
            valid float or array.  To plot phase along the x-axis, pass
            `x='phases'` or `x=phases:[component]`.  This will use the ephemeris
            from <phoebe.frontend.bundle.Bundle.get_ephemeris>(component) if
            possible to phase the applicable times array.
        * `y` (string/float/array, optional): qualifier/twig of the array to plot on the
            y-axis (will default based on the dataset-kind if not provided).  To
            plot residuals along the y-axis, pass `y='residuals'`.  This will
            call <phoebe.frontend.bundle.Bundle.compute_residuals> for the given
            dataset/model.
        * `z` (string/float/array, optional): qualifier/twig of the array to plot on the
            z-axis.  By default, this will just order the points on a 2D plot.
            To plot in 3D, also pass `projection='3d'`.
        * `s` (strong/float/array, optional): qualifier/twig of the array to use
            for size.  See the [autofig tutorial on size](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/size_modes.ipynb)
            for more information.
        * `c` (string/float/array, optional): qualifier/twig of the array to use
            for color.
        * `fc` (string/float/array, optional): qualifier/twig of the array to use
            for facecolor (only applicable for mesh plots).
        * `ec` (string/float/array, optional): qualifier/twig of the array to use
            for edgecolor (only applicable for mesh plots).

        * `i` (string, optional, default='time'): qualifier/twig to use for the
            independent variable.  In the vast majority of cases, using the default
            is sufficient.  If `x` is phase, then setting `i` to phase as well
            will sort and connect the points in phase-order instead of the default
            behavior or time-order.

        * `xerror` (string/float/array, optional): qualifier/twig of the array to plot as
            x-errors (will default based on `x` if not provided).
        * `yerror` (string/float/array, optional): qualifier/twig of the array to plot as
            y-errors (will default based on `y` if not provided).
        * `zerror` (string/float/array, optional): qualifier/twig of the array to plot as
            z-errors (will default based on `z` if not provided).

        * `xunit` (string/unit, optional): unit to plot on the x-axis (will
            default on `x` if not provided).
        * `yunit` (string/unit, optional): unit to plot on the y-axis (will
            default on `y` if not provided).
        * `zunit` (string/unit, optional): unit to plot on the z-axis (will
            default on `z` if not provided).
        * `cunit` (string/unit, optional): unit to plot on the color-axis (will
            default on `c` if not provided).
        * `fcunit` (string/unit, optional): unit to plot on the facecolor-axis (will
            default on `fc` if not provided, only applicable for mesh plots).
        * `ecunit` (string/unit, optional): unit to plot on the edgecolor-axis (will
            default on `ec` if not provided, only applicable for mesh plots).

        * `xlabel` (string, optional): label for the x-axis (will default on `x`
            if not provided, but will not set if the axes already has an xlabel).
        * `ylabel` (string, optional): label for the y-axis (will default on `y`
            if not provided, but will not set if the axes already has an ylabel).
        * `zlabel` (string, optional): label for the z-axis (will default on `z`
            if not provided, but will not set if the axes already has an zlabel).
        * `slabel` (string, optional): label for the size-axis (will default on `s`
            if not provided, but will not set if the axes already has an slabel).
        * `clabel` (string, optional): label for the color-axis (will default on `c`
            if not provided, but will not set if the axes already has an clabel).
        * `fclabel` (string, optional): label for the facecolor-axis (will default on `fc`
            if not provided, but will not set if the axes already has an fclabel,
            only applicable for mesh plots).
        * `eclabel` (string, optional): label for the edgecolor-axis (will default on `ec`
            if not provided, but will not set if the axes already has an eclabel,
            only applicable for mesh plots).

        * `xlim` (tuple/string, optional): limits for the x-axis (will default on
            data if not provided).  See [autofig tutorial on limits](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/limits.ipynb)
            for more information/choices.
        * `ylim` (tuple/string, optional): limits for the y-axis (will default on
            data if not provided).  See [autofig tutorial on limits](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/limits.ipynb)
            for more information/choices.
        * `zlim` (tuple/string, optional): limits for the z-axis (will default on
            data if not provided).  See [autofig tutorial on limits](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/limits.ipynb)
            for more information/choices.
        * `slim` (tuple/string, optional): limits for the size-axis (will default on
            data if not provided).  See [autofig tutorial on limits](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/limits.ipynb)
            for more information/choices.
        * `clim` (tuple/string, optional): limits for the color-axis (will default on
            data if not provided).  See [autofig tutorial on limits](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/limits.ipynb)
            for more information/choices.
        * `fclim` (tuple/string, optional): limits for the facecolor-axis (will default on
            data if not provided).  See [autofig tutorial on limits](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/limits.ipynb)
            for more information/choices.
        * `eclim` (tuple/string, optional): limits for the edgecolor-axis (will default on
            data if not provided).  See [autofig tutorial on limits](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/limits.ipynb)
            for more information/choices.

        * `smode` (string, optional): size mode.  See the [autofig tutorial on sizes](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/size_modes.ipynb)
            for more information.

        * `highlight` (bool, optional, default=True): whether to highlight at the
            current time.  Only applicable if `time` or `times` provided.
        * `highlight_marker` (string, optional): marker to use for highlighting.
            Only applicable if `highlight=True` and `time` or `times` provided.
        * `highlight_color` (string, optional): color to use for highlighting.
            Only applicable if `highlight=True` and `time` or `times` provided.

        * `uncover` (bool, optional): whether to uncover data based on the current
            time.  Only applicable if `time` or `times` provided.

        * `legend` (bool, optional, default=False): whether to draw a legend for
            this axes.
        * `legend_kwargs` (dict, optional):  keyword arguments (position,
            formatting, etc) to be passed on to [plt.legend](https://matplotlib.org/api/_as_gen/matplotlib.pyplot.legend.html)

        * `fig` (matplotlib figure, optional): figure to use for plotting.  If
            not provided, will use plt.gcf().  Ignored unless `save`, `show`,
            or `animate`.

        * `save` (string, optional, default=False): filename to save the
            figure (or False to not save).
        * `show` (bool, optional, default=False): whether to show the plot
        * `animate` (bool, optional, default=False): whether to animate the figure.
        * `draw_sidebars` (bool, optional, default=False): whether to include
            any applicable sidebars (colorbar, sizebar, etc).
        * `draw_title` (bool, optional, default=False): whether to draw axes
            titles.
        * `subplot_grid` (tuple, optional, default=None): override the subplot
            grid used (see [autofig tutorial on subplots](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/subplot_positioning.ipynb)
            for more details).

        * `save_kwargs` (dict, optional): any kwargs necessary to pass on to
            save (only applicable if `animate=True`).

        * `**kwargs`: additional keyword arguments are sent along to [autofig](https://github.com/kecnry/autofig/tree/1.0.0).

        Returns
        --------
        * (autofig figure, matplotlib figure)
        """
        if not _use_autofig:
            if os.getenv('PHOEBE_ENABLE_PLOTTING', 'TRUE').upper() != 'TRUE':
                raise ImportError("cannot plot because PHOEBE_ENABLE_PLOTTING environment variable is disasbled")
            else:
                raise ImportError("autofig not imported, cannot plot")

        # since we used the args trick above, all other options have to be in kwargs
        save = kwargs.pop('save', False)
        show = kwargs.pop('show', False)
        tight_layout = kwargs.pop('tight_layout', False)
        draw_sidebars = kwargs.pop('draw_sidebars', False)
        draw_title = kwargs.pop('draw_title', False)
        subplot_grid = kwargs.pop('subplot_grid', None)
        animate = kwargs.pop('animate', False)
        time = kwargs.get('time', None)  # don't pop since time may be used for filtering

        if twig is not None:
            kwargs['twig'] = twig

        plot_kwargss = self._unpack_plotting_kwargs(**kwargs)

        # this loop handles any of the automatically-generated
        # multiple plotting calls, passing each on to autofig
        for plot_kwargs in plot_kwargss:
            y = plot_kwargs.get('y', [])
            if (isinstance(y, u.Quantity) and isinstance(y.value, float)) or (hasattr(y, 'value') and isinstance(y.value, float)):
                pass
            elif not len(y):
                # a dataset without observational data, for example
                continue

            autofig_method = plot_kwargs.pop('autofig_method', 'plot')
            # we kept the qualifiers around so we could do some default-logic,
            # but it isn't necessary to pass them on to autofig.
            plot_kwargs = {k:v for k,v in plot_kwargs.items() if 'qualifier' not in k}
            logger.info("calling autofig.{}({})".format(autofig_method, ", ".join(["{}={}".format(k,v if not isinstance(v, np.ndarray) else "<data ({})>".format(v.shape)) for k,v in plot_kwargs.items()])))
            func = getattr(self.gcf(), autofig_method)

            func(**plot_kwargs)


        if save or show or animate:
            # NOTE: time, times, will all be included in kwargs
            try:
                return self._show_or_save(save, show, animate,
                                          draw_sidebars=draw_sidebars,
                                          draw_title=draw_title,
                                          tight_layout=tight_layout,
                                          subplot_grid=subplot_grid,
                                          **kwargs)
            except Exception as err:
                self.clf()
                raise
        else:
            afig = self.gcf()
            fig = None

            return afig, fig

    def _show_or_save(self, save, show, animate,
                      draw_sidebars=True,
                      draw_title=True,
                      tight_layout=False,
                      subplot_grid=None,
                      **kwargs):
        """
        Draw/animate and show and/or save a autofig plot
        """
        if animate and not show and not save:
            logger.warning("setting show to True since animate=True and save not provided")
            show = True

        if animate:
            # prefer times over time
            times = kwargs.get('times', kwargs.get('time', None))
            save_kwargs = kwargs.get('save_kwargs', {})

            if times is None:
                # then let's try to get all SYNTHETIC times
                # it would be nice to only do ENABLED, but then we have to worry about compute
                # it would also be nice to worry about models... but then you should filter first
                logger.info("no times were providing, so defaulting to animate over all dataset times")
                times = []
                for dataset in self.datasets:
                    ps = self.filter(dataset=dataset, context='model')
                    if len(ps.times):
                        # for the case of meshes/spectra
                        times += [float(t) for t in ps.times]
                    else:
                        for param in ps.filter(qualifier='times').to_list():
                            times += list(param.get_value())

                times = sorted(list(set(times)))

            logger.info("calling autofig.animate(i={}, draw_sidebars={}, draw_title={}, tight_layout={}, save={}, show={}, save_kwargs={})".format(times, draw_sidebars, draw_title, tight_layout, save, show, save_kwargs))

            mplanim = self.gcf().animate(i=times,
                                         draw_sidebars=draw_sidebars,
                                         draw_title=draw_title,
                                         tight_layout=tight_layout,
                                         subplot_grid=subplot_grid,
                                         save=save,
                                         show=show,
                                         save_kwargs=save_kwargs)

            afig = self.gcf()

            # clear the autofig figure
            self.clf()

            return afig, mplanim

        else:
            time = kwargs.get('time', None)

            if isinstance(time, str):
                time = self.get_value(time, context=['component', 'system'])

            logger.info("calling autofig.draw(i={}, draw_sidebars={}, draw_title={}, tight_layout={}, save={}, show={})".format(time, draw_sidebars, draw_title, tight_layout, save, show))
            fig = self.gcf().draw(i=time,
                                  draw_sidebars=draw_sidebars,
                                  draw_title=draw_title,
                                  tight_layout=tight_layout,
                                  subplot_grid=subplot_grid,
                                  save=save, show=show)
            # clear the figure so next call will start over and future shows will work
            afig = self.gcf()
            self.clf()

            return afig, fig


    def show(self, **kwargs):
        """
        Draw and show the plot.

        See also:
        * <phoebe.parameters.ParameterSet.plot>
        * <phoebe.parameters.ParameterSet.savefig>
        * <phoebe.parameters.ParameterSet.gcf>
        * <phoebe.parameters.ParameterSet.clf>

        Arguments
        ----------
        * `show` (bool, optional, default=True): whether to show the plot
        * `save` (False/string, optional, default=False): filename to save the
            figure (or False to not save).
        * `animate` (bool, optional, default=False): whether to animate the figure.
        * `fig` (matplotlib figure, optional): figure to use for plotting.  If
            not provided, will use plt.gcf().  Ignored unless `save`, `show`,
            or `animate`.
        * `draw_sidebars` (bool, optional, default=True): whether to include
            any applicable sidebars (colorbar, sizebar, etc).
        * `draw_title` (bool, optional, default=True): whether to draw axes
            titles.
        * `subplot_grid` (tuple, optional, default=None): override the subplot
            grid used (see [autofig tutorial on subplots](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/subplot_positioning.ipynb)
            for more details).
        * `time` (float, optional): time to use for plotting/animating.
        * `times` (list/array, optional): times to use for animating (will
            override any value sent to `time`).
        * `save_kwargs` (dict, optional): any kwargs necessary to pass on to
            save (only applicable if `animate=True`).

        Returns
        --------
        * (autofig figure, matplotlib figure)
        """
        kwargs.setdefault('show', True)
        kwargs.setdefault('save', False)
        kwargs.setdefault('animate', False)
        return self._show_or_save(**kwargs)

    def savefig(self, filename, **kwargs):
        """
        Draw and save the plot.

        See also:
        * <phoebe.parameters.ParameterSet.plot>
        * <phoebe.parameters.ParameterSet.show>
        * <phoebe.parameters.ParameterSet.gcf>
        * <phoebe.parameters.ParameterSet.clf>

        Arguments
        ----------
        * `save` (string): filename to save the figure (or False to not save).
        * `show` (bool, optional, default=False): whether to show the plot
        * `animate` (bool, optional, default=False): whether to animate the figure.
        * `fig` (matplotlib figure, optional): figure to use for plotting.  If
            not provided, will use plt.gcf().  Ignored unless `save`, `show`,
            or `animate`.
        * `draw_sidebars` (bool, optional, default=True): whether to include
            any applicable sidebars (colorbar, sizebar, etc).
        * `draw_title` (bool, optional, default=True): whether to draw axes
            titles.
        * `subplot_grid` (tuple, optional, default=None): override the subplot
            grid used (see [autofig tutorial on subplots](https://github.com/kecnry/autofig/blob/1.0.0/tutorials/subplot_positioning.ipynb)
            for more details).
        * `time` (float, optional): time to use for plotting/animating.
        * `times` (list/array, optional): times to use for animating (will
            override any value sent to `time`).
        * `save_kwargs` (dict, optional): any kwargs necessary to pass on to
            save (only applicable if `animate=True`).

        Returns
        --------
        * (autofig figure, matplotlib figure)
        """
        filename = os.path.expanduser(filename)
        kwargs.setdefault('show', False)
        kwargs.setdefault('save', filename)
        kwargs.setdefault('animate', False)
        return self._show_or_save(**kwargs)

class Parameter(object):
    def __init__(self, qualifier, value=None, description='', **kwargs):
        """
        This is a generic class for a Parameter.  Any Parameter that
        will actually be usable will be a subclass of this class.

        Parameters are the base of PHOEBE and hold, at the minimum,
        the value of the parameter, a description, and meta-tags
        which are used to collect and filter a list of Parameters
        inside a ParameterSet.

        Some subclasses of Parameter can add additional methods
        or attributes.  For example :class:`FloatParameter` handles
        converting units and storing a default_unit.


        Any subclass of Parameter must (at the minimum):
        - method for get_value
        - method for set_value,
        - call to set_value in the overload of __init__
        - self._dict_fields_other defined in __init__
        - self._dict_fields = _meta_fields_all + self._dict_fields_other in __init__

        Arguments
        ------------
        * `value`: value to initialize the parameter
        * `description` (string, optional): description of the parameter
        * `bundle` (<phoebe.frontend.bundle.Bundle>, optional): parent bundle
            object.
        * `uniqueid` (string, optional): uniqueid for the parameter (suggested to leave blank
            and a random string will be generated)
        * `time` (string/float, optional): value for the time tag
        * `history` (string, optional): label for the history tag
        * `feature` (string, optional): label for the feature tag
        * `component` (string, optional): label for the component tag
        * `dataset` (string, optional): label for the dataset tag
        * `constraint` (string, optional): label for the constraint tag
        * `compute` (string, optional): label for the compute tag
        * `model` (string, optional): label for the model tag
        * `fitting` (string, optional): label for the fitting tag
        * `feedback` (string, optional): label for the feedback tag
        * `plugin` (string, optional): label for the plugin tag
        * `kind` (string, optional): label for the kind tag
        * `context` (string, optional): label for the context tag
        * `copy_for` (dictionary/False, optional, default=False): dictionary of
            filter arguments for which this parameter must be copied (use with caution)
        * `visible_if` (string, optional): string to check the value of another
            parameter holding the same meta-tags (except qualifier) to determine
            whether this parameter is visible and therefore shown in filters
            (example: `visible_if='otherqualifier:True'`).  See also
            <phoebe.parameters.Parameter.is_visible>
        """

        uniqueid = kwargs.get('uniqueid', _uniqueid())
        bundle = kwargs.get('bundle', None)

        self._description = description
        self._bundle = bundle
        self._value = None

        # Meta-data
        self.set_uniqueid(uniqueid)
        self._qualifier = qualifier
        self._time = kwargs.get('time', None)
        self._history = kwargs.get('history', None)
        self._feature = kwargs.get('feature', None)
        self._component = kwargs.get('component', None)
        self._dataset = kwargs.get('dataset', None)
        self._constraint = kwargs.get('constraint', None)
        self._compute = kwargs.get('compute', None)
        self._model = kwargs.get('model', None)
        self._fitting = kwargs.get('fitting', None)
        self._feedback = kwargs.get('feedback', None)
        self._plugin = kwargs.get('plugin', None)
        self._kind = kwargs.get('kind', None)
        self._context = kwargs.get('context', None)

        # set whether new 'copies' of this parameter need to be created when
        # new objects (body components, not orbits) or datasets are added to
        # the bundle.
        self._copy_for = kwargs.get('copy_for', False)

        self._visible_if = kwargs.get('visible_if', None)

        self._dict_fields_other = ['description', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

        # loading from json can result in unicodes instead of strings - this then
        # causes problems with a lot of isinstances and string-matching.
        for attr in _meta_fields_twig + self._dict_fields_other:
            attr = '_{}'.format(attr)
            val = getattr(self, attr)

            if isinstance(val, unicode) and attr not in ['_copy_for']:
              setattr(self, attr, str(val))


            #if attr == '_copy_for' and isinstance(self._copy_for, str):
            #    print "***", self._copy_for
            #    self._copy_for = json.loads(self._copy_for)

    @classmethod
    def _from_json(cls, bundle=None, **kwargs):
        """
        """
        # this is a class method to initialize any subclassed Parameter by classname
        # will almost always call through parameter_from_json

        # TODO: is this even necessary?  for most cases we can probably just call __init__
        # TODO: this will surely break for those that require bundle as the first arg
        if bundle is not None:
            return cls(bundle, **kwargs)
        else:
            return cls(**kwargs)

    def __repr__(self):
        """
        """
        if isinstance(self._value, nparray.ndarray):
            quantity = self._value
        elif hasattr(self, 'quantity'):
            quantity = self.get_quantity()
        else:
            quantity = self.get_value()

        if hasattr(self, 'constraint') and self.constraint is not None:
            return "<Parameter: {}={} (constrained) | keys: {}>".format(self.qualifier, quantity, ', '.join(self._dict_fields_other))
        else:
            return "<Parameter: {}={} | keys: {}>".format(self.qualifier, quantity, ', '.join(self._dict_fields_other))

    def __str__(self):
        """
        """
        if isinstance(self._value, nparray.ndarray):
            quantity = self._value
        elif hasattr(self, 'quantity'):
            quantity = self.get_quantity()
        else:
            quantity = self.get_value()

        str_ = "{}: {}\n".format("Parameter", self.uniquetwig)
        str_ += "{:>32}: {}\n".format("Qualifier", self.qualifier)
        str_ += "{:>32}: {}\n".format("Description", self.description)
        str_ += "{:>32}: {}\n".format("Value", quantity)

        if hasattr(self, 'choices'):
            str_ += "{:>32}: {}\n".format("Choices", ", ".join(self.choices))
        if hasattr(self, 'constrained_by'):
            str_ += "{:>32}: {}\n".format("Constrained by", ", ".join([p.uniquetwig for p in self.constrained_by]) if self.constrained_by is not None else 'None')
        if hasattr(self, 'constrains'):
            str_ += "{:>32}: {}\n".format("Constrains", ", ".join([p.uniquetwig for p in self.constrains]) if len(self.constrains) else 'None')
        if hasattr(self, 'related_to'):
            str_ += "{:>32}: {}\n".format("Related to", ", ".join([p.uniquetwig for p in self.related_to]) if len(self.related_to) else 'None')
        if self.visible_if is not None:
            str_ += "{:>32}: {}\n".format("Only visible if", self.visible_if)

        return str_

    def __len__(self):
        """
        since this may be returned from a filter, fake to say there is only 1 result
        """
        return 1

    def __eq__(self, other):
        """
        """
        # TODO: check value as well
        if not isinstance(other, Parameter):
            return False
        return self.uniqueid == other.uniqueid

    def copy(self):
        """
        Deepcopy the <phoebe.parameters.Parameter> (with a new uniqueid).
        All other tags will remain the same... so some other tag should be
        changed before attaching back to a <phoebe.parameters.ParameterSet> or
        <phoebe.frontend.bundle.Bundle>.

        See also:
        * <phoebe.parameters.Parameter.uniqueid>

        Returns
        ---------
        * (<phoebe.parameters.Parameter>): the copied Parameter object
        """
        s = self.to_json()
        cpy = parameter_from_json(s)
        # TODO: may need to subclass for Parameters that require bundle by using this line instead:
        # cpy = parameter_from_json(s, bundle=self._bundle)
        cpy.set_uniqueid(_uniqueid())
        return cpy

    def to_string(self):
        """
        Return the string representation of the <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.Parameter.to_string_short>

        Returns
        -------
        * (str): the string representation
        """
        return self.__str__()

    def to_string_short(self):
        """
        Return a short/abreviated string representation of the
        <phoebe.parmaeters.Parameter>.

        See also:
        * <phoebe.parameters.Parameter.to_string>

        Returns
        --------
        * (str): the string representation
        """
        if hasattr(self, 'constrained_by') and len(self.constrained_by) > 0:
            return "* {:>30}: {}".format(self.uniquetwig_trunc, self.get_quantity() if hasattr(self, 'quantity') else self.get_value())
        else:
            return "{:>32}: {}".format(self.uniquetwig_trunc, self.get_quantity() if hasattr(self, 'quantity') else self.get_value())

    def __dict__(self):
        """
        """
        # including uniquetwig for everything can be VERY SLOW, so let's not
        # include that in the dictionary
        d =  {k: getattr(self,k) for k in self._dict_fields if k not in ['uniquetwig']}
        d['Class'] = self.__class__.__name__
        return d

    def to_dict(self):
        """
        Return the dictionary representation of the <phoebe.parameters.Parameter>.

        Returns
        -------
        * (dict): the dictionary representation of the Parameter.
        """
        return self.__dict__()

    def __getitem__(self, key):
        """
        """
        return self.__dict__()[key]

    def __setitem__(self, key, value):
        """
        """
        # TODO: don't allow changing things like visible_if or description here?
        raise NotImplementedError

    @classmethod
    def open(cls, filename):
        """
        Open a Parameter from a JSON-formatted file.
        This is a constructor so should be called as:

        ```py
        param = Parameter.open('test.json')
        ```

        See also:
        * <phoebe.parameters.ParameterSet.open>
        * <phoebe.frontend.bundle.Bundle.open>

        Arguments
        ---------
        * `filename` (string): relative or full path to the file

        Returns
        -------
        * (<phoebe.parameters.Parameter): the inistantiated Parameter object.
        """
        filename = os.path.expanduser(filename)
        f = open(filename, 'r')
        data = json.load(f, object_pairs_hook=parse_json)
        f.close()
        return cls(data)

    def save(self, filename, incl_uniqueid=False):
        """
        Save the Parameter to a JSON-formatted ASCII file

        See also:
        * <phoebe.parameters.ParameterSet.save>
        * <phoebe.frontend.bundle.Bundle.save>

        Arguments
        ----------
        * `filename` (string): relative or full path to the file
        * `incl_uniqueid` (bool, optional, default=False): whether to include
            uniqueids in the file (only needed if its necessary to maintain the
            uniqueids when reloading)

        Returns
        --------
        * (string) filename
        """
        filename = os.path.expanduser(filename)
        f = open(filename, 'w')
        json.dump(self.to_json(incl_uniqueid=incl_uniqueid), f,
                   sort_keys=True, indent=0, separators=(',', ': '))
        f.close()

        return filename

    def to_json(self, incl_uniqueid=False):
        """
        Convert the <phoebe.parameters.Parameter> to a json-compatible
        object.

        See also:
        * <phoebe.parameters.ParameterSet.to_json>
        * <phoebe.parameters.Parameter.to_dict>
        * <phoebe.parameters.Parameter.save>

        Arguments
        --------
        * `incl_uniqueid` (bool, optional, default=False): whether to include
            uniqueids in the file (only needed if its necessary to maintain the
            uniqueids when reloading)

        Returns
        -----------
        * (dict)
        """
        def _parse(k, v):
            """
            """
            if k=='value':
                if isinstance(self._value, nparray.ndarray):
                    if self._value.unit is not None and hasattr(self, 'default_unit'):
                        v = self._value.to(self.default_unit).to_dict()
                    else:
                        v = self._value.to_dict()
                if isinstance(v, u.Quantity):
                    v = self.get_value() # force to be in default units
                if isinstance(v, np.ndarray):
                    v = v.tolist()
                return v
            elif k=='limits':
                return [vi.value if hasattr(vi, 'value') else vi for vi in v]
            elif v is None:
                return v
            elif isinstance(v, str):
                return v
            elif isinstance(v, dict):
                return v
            elif isinstance(v, float) or isinstance(v, int) or isinstance(v, list):
                return v
            elif _is_unit(v):
                return str(v.to_string())
            else:
                try:
                    return str(v)
                except:
                    raise NotImplementedError("could not parse {} of '{}' to json".format(k, self.uniquetwig))

        return {k: _parse(k, v) for k,v in self.to_dict().items() if (v is not None and k not in ['twig', 'uniquetwig', 'quantity'] and (k!='uniqueid' or incl_uniqueid or self.qualifier=='detached_job'))}

    @property
    def attributes(self):
        """
        Return a list of the attributes of this <phoebe.parameters.Parameter>.

        Returns
        -------
        * (list)
        """
        return self._dict_fields_other

    def get_attributes(self):
        """
        Return a list of the attributes of this <phoebe.parameters.Parameter>.
        This is simply a shortcut to <phoebe.parameters.Parameter.attributes>.

        Returns
        --------
        * (list)
        """
        return self.attributes

    @property
    def meta(self):
        """
        See all the meta-tag properties for this <phoebe.parameters.Parameter>.

        See <phoebe.parameters.Parameter.get_meta> for the ability to ignore
        certain keys.

        Returns
        -------
        * (dict) an ordered dictionary of all tag properties.
        """
        return self.get_meta()

    def get_meta(self, ignore=['uniqueid']):
        """
        See all the meta-tag properties for this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.Parameter.meta>
        * <phoebe.parameters.ParameterSet.get_meta>

        Arguments
        ---------
        * `ignore` (list, optional, default=['uniqueid']): list of keys to
            exclude from the returned dictionary

        Returns
        ----------
        * (dict) an ordered dictionary of tag properties
        """
        return OrderedDict([(k, getattr(self, k)) for k in _meta_fields_all if k not in ignore])

    @property
    def tags(self):
        """
        Returns a dictionary that lists all available tags.

        See also:
        * <phoebe.parameters.ParameterSet.tags>
        * <phoebe.parameters.Parameter.meta>

        Will include entries from the singular attributes:
        * <phoebe.parameters.Parameter.context>
        * <phoebe.parameters.Parameter.kind>
        * <phoebe.parameters.Parameter.model>
        * <phoebe.parameters.Parameter.compute>
        * <phoebe.parameters.Parameter.constraint>
        * <phoebe.parameters.Parameter.dataset>
        * <phoebe.parameters.Parameter.component>
        * <phoebe.parameters.Parameter.feature>
        * <phoebe.parameters.Parameter.time>
        * <phoebe.parameters.Parameter.qualifier>

        Returns
        ----------
        * (dict) a dictionary of all singular tag attributes.
        """
        return self.get_meta(ignore=['uniqueid', 'plugin', 'feedback', 'fitting', 'history', 'twig', 'uniquetwig'])

    @property
    def qualifier(self):
        """
        Return the qualifier of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.qualifier>
        * <phoebe.parameters.ParameterSet.qualifiers>

        Returns
        -------
        * (str) the qualifier tag of this Parameter.
        """
        return self._qualifier

    @property
    def time(self):
        """
        Return the time of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.time>
        * <phoebe.parameters.ParameterSet.times>

        Returns
        -------
        * (str) the time tag of this Parameter.
        """
        # need to force formatting because of the different way numpy.float64 is
        # handled before numpy 1.14.  See https://github.com/phoebe-project/phoebe2/issues/247
        return '{:09f}'.format(float(self._time)) if self._time is not None else None

    @property
    def history(self):
        """
        Return the history of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.history>
        * <phoebe.parameters.ParameterSet.historys>

        Returns
        -------
        * (str) the history tag of this Parameter.
        """
        return self._history

    @property
    def feature(self):
        """
        Return the feature of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.feature>
        * <phoebe.parameters.ParameterSet.features>

        Returns
        -------
        * (str) the feature tag of this Parameter.
        """
        return self._feature

    @property
    def component(self):
        """
        Return the component of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.component>
        * <phoebe.parameters.ParameterSet.components>

        Returns
        -------
        * (str) the component tag of this Parameter.
        """
        return self._component

    @property
    def dataset(self):
        """
        Return the dataset of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.dataset>
        * <phoebe.parameters.ParameterSet.datasets>

        Returns
        -------
        * (str) the dataset tag of this Parameter.
        """
        return self._dataset

    @property
    def constraint(self):
        """
        Return the constraint of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.constraint>
        * <phoebe.parameters.ParameterSet.constraints>

        Returns
        -------
        * (str) the constraint tag of this Parameter.
        """
        return self._constraint

    @property
    def compute(self):
        """
        Return the compute of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.compute>
        * <phoebe.parameters.ParameterSet.computes>

        Returns
        -------
        * (str) the compute tag of this Parameter.
        """
        return self._compute

    @property
    def model(self):
        """
        Return the model of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.model>
        * <phoebe.parameters.ParameterSet.models>

        Returns
        -------
        * (str) the model tag of this Parameter.
        """
        return self._model

    @property
    def fitting(self):
        """
        Return the fitting of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.fitting>
        * <phoebe.parameters.ParameterSet.fittings>

        Returns
        -------
        * (str) the fitting tag of this Parameter.
        """
        return self._fitting

    @property
    def feedback(self):
        """
        Return the feedback of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.feedback>
        * <phoebe.parameters.ParameterSet.feedbacks>

        Returns
        -------
        * (str) the feedback tag of this Parameter.
        """
        return self._feedback

    @property
    def plugin(self):
        """
        Return the plugin of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.plugin>
        * <phoebe.parameters.ParameterSet.plugins>

        Returns
        -------
        * (str) the plugin tag of this Parameter.
        """
        return self._plugin

    @property
    def kind(self):
        """
        Return the kind of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.kind>
        * <phoebe.parameters.ParameterSet.kinds>

        Returns
        -------
        * (str) the kind tag of this Parameter.
        """
        return self._kind

    @property
    def context(self):
        """
        Return the context of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.context>
        * <phoebe.parameters.ParameterSet.contexts>

        Returns
        -------
        * (str) the context tag of this Parameter.
        """
        return self._context

    @property
    def uniqueid(self):
        """
        Return the uniqueid of this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.ParameterSet.uniequids>

        Returns
        -------
        * (str) the uniqueid of this Parameter.
        """
        return self._uniqueid

    @property
    def uniquetwig_trunc(self):
        """
        Return the uniquetwig but truncated if necessary to be <=12 characters.

        See also:
        * <phoebe.parameters.Parameter.uniquetwig>
        * <phoebe.parameters.Parameter.twig>

        Returns
        --------
        * (str) the uniquetwig, truncated to 12 characters
        """
        uniquetwig = self.uniquetwig
        if len(uniquetwig) > 30:
            return uniquetwig[:27]+'...'
        else:
            return uniquetwig


    @property
    def uniquetwig(self):
        """
        Determine the shortest (more-or-less) twig which will point
        to this single <phoebe.parameters.Parameter> in the parent
        <phoebe.frontend.bundle.Bundle>.

        See <phoebe.parameters.Parameter.get_uniquetwig> (introduced in 2.1.1)
        for the ability to pass a <phoebe.parameters.ParameterSet>.

        See also:
        * <phoebe.parameters.Parameter.twig>
        * <phoebe.parameters.Parameter.uniquetwig_trunc>

        Returns
        --------
        * (str) uniquetwig
        """
        return self.get_uniquetwig()


    def get_uniquetwig(self, ps=None):
        """
        Determine the shortest (more-or-less) twig which will point
        to this single <phoebe.parameters.Parameter> in a given parent
        <phoebe.parameters.ParameterSet>.

        See also:
        * <phoebe.parameters.Parameter.twig>
        * <phoebe.parameters.Parameter.uniquetwig_trunc>

        Arguments
        ----------
        * `ps` (<phoebe.parameters.ParameterSet>, optional): ParameterSet
            in which the returned uniquetwig will point to this Parameter.
            If not provided or None this will default to the parent
            <phoebe.frontend.bundle.Bundle>, if available.

        Returns
        --------
        * (str) uniquetwig
        """

        if ps is None:
            ps = self._bundle

        if ps is None:
            return self.twig
        return ps._uniquetwig(self.twig)

    @property
    def twig(self):
        """
        The twig of a <phoebe.parameters.Parameter> is a single string with the
        individual <phoebe.parameters.Parameter.meta> tags separated by '@' symbols.
        This twig gives a single string which can point back to this Parameter.

        See also:
        * <phoebe.parameters.Parameter.uniquetwig>
        * <phoebe.parameters.ParameterSet.twigs>

        Returns
        --------
        * (str): the full twig of this Parameter.
        """
        return "@".join([getattr(self, k) for k in _meta_fields_twig if getattr(self, k) is not None])

    @property
    def visible_if(self):
        """
        Return the `visible_if` expression for this <phoebe.parameters.Parameter>.

        See also:
        * <phoebe.parameters.Parameter.is_visible>

        Returns
        --------
        * (str): the `visible_if` expression for this Parameter
        """
        return self._visible_if

    @property
    def is_visible(self):
        """
        Execute the `visible_if` expression for this <phoebe.parameters.Parameter>
        and determine whether it is currently visible in the parent
        <phoebe.parameters.ParameterSet>.

        If `False`, <phoebe.parameters.ParameterSet.filter> calls must have
        `check_visible=False` or else this Parameter will be excluded.

        See also:
        * <phoebe.parameters.Parameter.visible_if>

        Returns
        --------
        * (bool):  whether this parameter is currently visible
        """
        def is_visible_single(visible_if):
            # visible_if syntax: [ignore,these]qualifier:value

            if visible_if.lower() == 'false':
                return False

            # otherwise we need to find the parameter we're referencing and check its value
            if visible_if[0]=='[':
                remove_metawargs, visible_if = visible_if[1:].split(']')
                remove_metawargs = remove_metawargs.split(',')
            else:
                remove_metawargs = []

            qualifier, value = visible_if.split(':')

            if 'hierarchy.' in qualifier:
                # TODO: set specific syntax (hierarchy.get_meshables:2)
                # then this needs to do some logic on the hierarchy
                hier = self._bundle.hierarchy
                if not len(hier.get_value()):
                    # then hierarchy hasn't been set yet, so we can't do any
                    # of these tests
                    return True

                method = qualifier.split('.')[1]

                if value in ['true', 'True']:
                    value = True
                elif value in ['false', 'False']:
                    value = False

                return getattr(hier, method)(self.component) == value

            else:

                # the parameter needs to have all the same meta data except qualifier
                # TODO: switch this to use self.get_parent_ps ?
                metawargs = {k:v for k,v in self.get_meta(ignore=['twig', 'uniquetwig', 'uniqueid']+remove_metawargs).items() if v is not None}
                metawargs['qualifier'] = qualifier
                # metawargs['twig'] = None
                # metawargs['uniquetwig'] = None
                # metawargs['uniqueid'] = None
                # if metawargs.get('component', None) == '_default':
                    # metawargs['component'] = None

                try:
                    # this call is quite expensive and bloats every get_parameter(check_visible=True)
                    param = self._bundle.get_parameter(check_visible=False, check_default=False, **metawargs)
                except ValueError:
                    # let's not let this hold us up - sometimes this can happen when copying
                    # parameters (from copy_for) in order that the visible_if parameter
                    # happens later
                    logger.debug("parameter not found when trying to determine if visible, {}".format(metawargs))
                    return True

                #~ print "***", qualifier, param.qualifier, param.get_value(), value

                if isinstance(param, BoolParameter):
                    if value in ['true', 'True']:
                        value = True
                    elif value in ['false', 'False']:
                        value = False


                if isinstance(value, str) and value[0] in ['!', '~']:
                    return param.get_value() != value[1:]
                elif value=='<notempty>':
                    return len(param.get_value()) > 0
                else:
                    return param.get_value() == value


        if self.visible_if is None:
            return True

        if not self._bundle:
            # then we may not be able to do the check, for now let's just return True
            return True

        return np.all([is_visible_single(visible_if_i) for visible_if_i in self.visible_if.split(',')])



    @property
    def copy_for(self):
        """
        Return the `copy_for` expression for this <phoebe.parameters.Parameter>.

        This expression determines which new components and datasets should
        receive a copy of this Parameter.

        Returns:
        * (dict) the `copy_for` expression for this Parameter
        """
        return self._copy_for


    @property
    def description(self):
        """
        Return the `description` of the <phoebe.parameters.Parameter>.  The
        description is a slightly longer explanation of the Parameter qualifier.

        See also:
        * <phoebe.parameters.Parameter.get_description>
        * <phoebe.parameters.ParameterSet.get_description>
        * <phoebe.parameters.Parameter.qualifier>

        Returns
        --------
        * (str) the description
        """
        return self._description

    def get_description(self):
        """
        Return the `description` of the <phoebe.parameters.Parameter>.  The
        description is a slightly longer explanation of the Parameter qualifier.

        See also:
        * <phoebe.parameters.Parameter.description>
        * <phoebe.parameters.ParameterSet.get_description>
        * <phoebe.parameters.Parameter.qualifier>

        Returns
        --------
        * (str) the description
        """
        return self._description

    @property
    def value(self):
        """
        Return the value of the <phoebe.parameters.Parameter>.  For more options,
        including units when applicable, use the appropriate `get_value`
        method instead:

        * <phoebe.parameters.FloatParameter.get_value>
        * <phoebe.parameters.FloatArrayParameter.get_value>
        * <phoebe.parameters.HierarchyParameter.get_value>
        * <phoebe.parameters.IntParameter.get_value>
        * <phoebe.parameters.BoolParameter.get_value>
        * <phoebe.parameters.ChoiceParameter.get_value>
        * <phoebe.parameters.SelectParameter.get_value>
        * <phoebe.parameters.ConstraintParameter.get_value>
        * <phoebe.parameters.HistoryParameter.get_value>

        Returns
        ---------
        * (float/int/string/bool): the current value of the Parameter.
        """

        return self.get_value()


    def _add_history(self, redo_func, redo_kwargs, undo_func, undo_kwargs):
        """
        """
        if self._bundle is None or not self._bundle.history_enabled:
            return
        if 'value' in undo_kwargs.keys() and undo_kwargs['value'] is None:
            return

            logger.debug("creating history entry for {}".format(redo_func))
        #~ print "*** param._add_history", redo_func, redo_kwargs, undo_func, undo_kwargs
        self._bundle._add_history(redo_func, redo_kwargs, undo_func, undo_kwargs)

    # TODO (done?): access to value, adjust, unit, prior, posterior, etc in dictionary (when applicable)
    # TODO (done?): ability to set value, adjust, unit, prior, posterior through dictionary access (but not meta-fields)

    def get_parent_ps(self):
        """
        Return a <phoebe.parameters.ParameterSet> of all Parameters in the same
        <phoebe.frontend.bundle.Bundle> which share the same
        meta-tags (except qualifier, twig, uniquetwig).

        See also:
        * <phoebe.parameters.Parameter.meta>

        Returns
        ----------
        * (<phoebe.parameters.ParameterSet>): the parent ParameterSet.
        """
        if self._bundle is None:
            return None

        metawargs = {k:v for k,v in self.meta.items() if k not in ['qualifier', 'twig', 'uniquetwig']}

        return self._bundle.filter(**metawargs)

    def to_constraint(self):
        """
        Convert this <phoebe.parameters.Parameter> to a
        <phoebe.parameters.ConstraintParameter>.

        **NOTE**: this is an advanced functionality: use with caution.

        Returns
        --------
        * (<phoebe.parameters.ConstraintParameter): the ConstraintParameter
        """
        return ConstraintParameter(self._bundle, "{%s}" % self.uniquetwig)

    def __math__(self, other, symbol, mathfunc):
        """
        """


        try:
            # print "***", type(other), mathfunc
            if isinstance(other, ConstraintParameter):
                # print "*** __math__", self.quantity, mathfunc, other.result, other.expr
                return ConstraintParameter(self._bundle, "{%s} %s (%s)" % (self.uniquetwig, symbol, other.expr), default_unit=(getattr(self.quantity, mathfunc)(other.result).unit))
            elif isinstance(other, Parameter):

                # we need to do some tricks here since the math could fail if doing
                # math on  arrays of different lengths (ie if one is empty)
                # So instead, we'll just multiply with 1.0 floats if we can get the
                # unit from the quantity.

                self_quantity = self.quantity
                other_quantity = other.quantity

                if hasattr(self_quantity, 'unit'):
                    self_quantity = 1.0 * self_quantity.unit
                if hasattr(other_quantity, 'unit'):
                    other_quantity = 1.0 * other_quantity.unit

                default_unit = getattr(self_quantity, mathfunc)(other_quantity).unit
                return ConstraintParameter(self._bundle, "{%s} %s {%s}" % (self.uniquetwig, symbol, other.uniquetwig), default_unit=default_unit)
            elif isinstance(other, u.Quantity):
                return ConstraintParameter(self._bundle, "{%s} %s %0.30f" % (self.uniquetwig, symbol, _value_for_constraint(other)), default_unit=(getattr(self.quantity, mathfunc)(other).unit))
            elif isinstance(other, float) or isinstance(other, int):
                if symbol in ['+', '-'] and hasattr(self, 'default_unit'):
                    # assume same units as self (NOTE: NOT NECESSARILY SI) if addition or subtraction
                    other = float(other)*self.default_unit
                else:
                    # assume dimensionless
                    other = float(other)*u.dimensionless_unscaled
                return ConstraintParameter(self._bundle, "{%s} %s %f" % (self.uniquetwig, symbol, _value_for_constraint(other)), default_unit=(getattr(self.quantity, mathfunc)(other).unit))
            elif isinstance(other, u.Unit) and mathfunc=='__mul__':
                return self.quantity*other
            else:
                raise NotImplementedError("math with type {} not supported".format(type(other)))
        except ValueError:
            raise ValueError("constraint math failed: make sure you're using astropy 1.0+")

    def __rmath__(self, other, symbol, mathfunc):
        """
        """
        try:
            if isinstance(other, ConstraintParameter):
                return ConstraintParameter(self._bundle, "(%s) %s {%s}" % (other.expr, symbol, self.uniquetwig), default_unit=(getattr(self.quantity, mathfunc)(other.result).unit))
            elif isinstance(other, Parameter):
                return ConstraintParameter(self._bundle, "{%s} %s {%s}" % (other.uniquetwig, symbol, self.uniquetwig), default_unit=(getattr(self.quantity, mathfunc)(other.quantity).unit))
            elif isinstance(other, u.Quantity):
                return ConstraintParameter(self._bundle, "%0.30f %s {%s}" % (_value_for_constraint(other), symbol, self.uniquetwig), default_unit=(getattr(self.quantity, mathfunc)(other).unit))
            elif isinstance(other, float) or isinstance(other, int):
                if symbol in ['+', '-'] and hasattr(self, 'default_unit'):
                    # assume same units as self if addition or subtraction
                    other = float(other)*self.default_unit
                else:
                    # assume dimensionless
                    other = float(other)*u.dimensionless_unscaled
                return ConstraintParameter(self._bundle, "%f %s {%s}" % (_value_for_constraint(other), symbol, self.uniquetwig), default_unit=(getattr(self.quantity, mathfunc)(other).unit))
            elif isinstance(other, u.Unit) and mathfunc=='__mul__':
                return self.quantity*other
            else:
                raise NotImplementedError("math with type {} not supported".format(type(other)))
        except ValueError:
            raise ValueError("constraint math failed: make sure you're using astropy 1.0+")

    def __add__(self, other):
        """
        """
        return self.__math__(other, '+', '__add__')

    def __radd__(self, other):
        """
        """
        return self.__rmath__(other, '+', '__radd__')

    def __sub__(self, other):
        """
        """
        return self.__math__(other, '-', '__sub__')

    def __rsub__(self, other):
        """
        """
        return self.__rmath__(other, '-', '__rsub__')

    def __mul__(self, other):
        """
        """
        return self.__math__(other, '*', '__mul__')

    def __rmul__(self, other):
        """
        """
        return self.__rmath__(other, '*', '__rmul__')

    def __div__(self, other):
        """
        """
        return self.__math__(other, '/', '__div__')

    def __rdiv__(self, other):
        """
        """
        return self.__rmath__(other, '/', '__rdiv__')

    def __truediv__(self, other):
        """
        """
        # NOTE: only used in python3
        return self.__math__(other, '/', '__truediv__')

    def __rtruediv__(self, other):
        """
        """
        # note only used in python3
        return self.__rmath__(other, '/', '__rtruediv__')

    def __pow__(self, other):
        """
        """
        return self.__math__(other, '**', '__pow__')

    def __rpow__(self, other):
        """
        """
        return self.__rmath__(other, '**', '__rpow__')

    def __mod__(self, other):
        """
        """
        return self.__math__(other, '%', '__mod__')

    def __rmod__(self, other):
        """
        """
        return self.__rmath__(other, '%', '__rmod__')

    def set_uniqueid(self, uniqueid):
        """
        Set the `uniqueid` of this <phoebe.parameters.Parameter>.
        There is no real need for a user to call this unless there is some
        conflict or they manually want to set the uniqueids.

        NOTE: this does not check for conflicts, and having two parameters
        without the same uniqueid (not really unique anymore is it) will
        surely cause unexpected results.  Use with caution.

        See also:
        * <phoebe.parameters.Parameter.uniqueid>

        Arguments
        ---------
        * `uniqueid` (string): the new uniqueid
        """
        # TODO: check to make sure uniqueid is valid (is actually unique within self._bundle and won't cause problems with constraints, etc)
        self._uniqueid = uniqueid

    def get_value(self, *args, **kwargs):
        """
        This method should be overriden by any subclass of
        <phoebe.parameters.Parameter>, and should be decorated with the
        @update_if_client decorator.
        Please see the individual classes documentation:

        * <phoebe.parameters.FloatParameter.get_value>
        * <phoebe.parameters.FloatArrayParameter.get_value>
        * <phoebe.parameters.HierarchyParameter.get_value>
        * <phoebe.parameters.IntParameter.get_value>
        * <phoebe.parameters.BoolParameter.get_value>
        * <phoebe.parameters.ChoiceParameter.get_value>
        * <phoebe.parameters.SelectParameter.get_value>
        * <phoebe.parameters.ConstraintParameter.get_value>
        * <phoebe.parameters.HistoryParameter.get_value>

        If subclassing, this method needs to:
        * cast to the correct type/units, handling defaults

        Raises
        -------
        * NoteImplemmentedError: because this must be subclassed
        """
        if self.qualifier in kwargs.keys():
            # then we have an "override" value that was passed, and we should
            # just return that.
            # Example teff_param.get_value('teff', teff=6000) returns 6000
            return kwargs.get(self.qualifier)
        return None

    def set_value(self, *args, **kwargs):
        """
        This method should be overriden by any subclass of Parameter, and should
        be decorated with the @send_if_client decorator
        Please see the individual classes for documentation:

        * <phoebe.parameters.FloatParameter.set_value>
        * <phoebe.parameters.FloatArrayParameter.set_value>
        * <phoebe.parameters.HierarchyParameter.set_value>
        * <phoebe.parameters.IntParameter.set_value>
        * <phoebe.parameters.BoolParameter.set_value>
        * <phoebe.parameters.ChoiceParameter.set_value>
        * <phoebe.parameters.SelectParameter.set_value>
        * <phoebe.parameters.ConstraintParameter.set_value>
        * <phoebe.parameters.HistoryParameter.set_value>

        If subclassing, this method needs to:
        * check the inputs for the correct format/agreement/cast_type
        * make sure that converting back to default_unit will work (if applicable)
        * make sure that in choices (if a choose)
        * make sure that not out of limits
        * make sure that not out of prior ??

        Raises
        -------
        * NotImplementedError: because this must be subclassed
        """
        raise NotImplementedError # <--- leave this in place, should be subclassed


class StringParameter(Parameter):
    """
    Parameter that accepts any string for the value
    """
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(StringParameter, self).__init__(*args, **kwargs)

        self.set_value(kwargs.get('value', ''))

        self._dict_fields_other = ['description', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @update_if_client
    def get_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.StringParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (string) the current or overridden value of the Parameter
        """
        default = super(StringParameter, self).get_value(**kwargs)
        if default is not None: return default
        return str(self._value)

    @send_if_client
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.StringParameter>.

        Arguments
        ----------
        * `value` (string): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to the correct type
            or is not a valid value for the Parameter.
        """
        _orig_value = deepcopy(value)

        try:
            value = str(value)
        except:
            raise ValueError("could not cast value to string")
        else:
            self._value = value

            self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})

class TwigParameter(Parameter):
    # TODO: change to RefParameter?
    """
    Parameter that handles referencing any other *parameter* by twig (must exist)
    This stores the uniqueid but will display as the current uniquetwig for that item
    """
    def __init__(self, bundle, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(TwigParameter, self).__init__(*args, **kwargs)

        # usually its the bundle's job to attach param._bundle after the
        # creation of a parameter.  But in this case, having access to the
        # bundle is necessary in order to intialize and set the value
        self._bundle = bundle

        self.set_value(kwargs.get('value', ''))

        self._dict_fields_other = ['description', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    def get_parameter(self):
        """
        Return the parameter that the `value` is referencing

        Returns
        --------
        * (<phoebe.parameters.Parameter>)
        """
        return self._bundle.get_parameter(uniqueid=self._value)

    @update_if_client
    def get_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.TwigParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (string) the current or overridden value of the Parameter
        """
        # self._value is the uniqueid of the parameter.  So we need to
        # retrieve that parameter, but display the current uniquetwig
        # to the user
        # print "*** TwigParameter.get_value self._value: {}".format(self._value)
        default = super(TwigParameter, self).get_value(**kwargs)
        if default is not None: return default
        if self._value is None:
            return None
        return _uniqueid_to_uniquetwig(self._bundle, self._value)


    @send_if_client
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.StringParameter>.

        Arguments
        ----------
        * `value` (string): the new value of the Parameter.
        * `**kwargs`: passed on to filter to find the Parameter

        Raises
        ---------
        * ValueError: if `value` could not be converted to the correct type
            or is not a valid value for the Parameter.
        """
        _orig_value = deepcopy(self.get_value())

        # first make sure only returns one results
        if self._bundle is None:
            raise ValueError("TwigParameters must be attached from the bundle, and cannot be standalone")

        value = str(value)  # <-- in case unicode

        # NOTE: this means that in all saving of bundles, we MUST keep the uniqueid and retain them when re-opening
        value = _twig_to_uniqueid(self._bundle, value, **kwargs)
        self._value = value

        self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})


class ChoiceParameter(Parameter):
    """
    Parameter in which the value has to match one of the pre-defined choices
    """
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(ChoiceParameter, self).__init__(*args, **kwargs)

        self._choices = kwargs.get('choices', [])

        self.set_value(kwargs.get('value', ''))

        self._dict_fields_other = ['description', 'choices', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @property
    def choices(self):
        """
        Return the valid list of choices.

        This is identical to: <phoebe.parameters.ChoiceParameter.get_choices>

        Returns
        ---------
        * (list) list of valid choices
        """
        return self._choices

    def get_choices(self):
        """
        Return the valid list of choices.

        This is identical to: <phoebe.parameters.ChoiceParameter.choices>

        Returns
        ---------
        * (list) list of valid choices
        """
        return self._choices

    @update_if_client
    def get_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.ChoiceParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.
            Note: the provided value is not checked against the valid set
            of choices (<phoebe.parameters.ChoiceParameter.choices>).

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (string) the current or overridden value of the Parameter
        """
        default = super(ChoiceParameter, self).get_value(**kwargs)
        if default is not None: return default
        return str(self._value)

    @send_if_client
    def set_value(self, value, run_checks=None, **kwargs):
        """
        Set the current value of the <phoebe.parameters.ChoiceParameter>.

        Arguments
        ----------
        * `value` (string): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to a string.
        * ValueError: if `value` is not one of
            <phoebe.parameters.ChoiceParameter.choices>
        """
        _orig_value = deepcopy(self.get_value())

        try:
            value = str(value)
        except:
            raise ValueError("could not cast value to string")

        if self.qualifier=='passband':
            if value not in self.choices:
                self._choices = list_passbands(refresh=True)

        if value not in self.choices:
            raise ValueError("value must be one of {}".format(self.choices))

        if self.qualifier=='passband' and value not in list_installed_passbands():
            # then we need to download and install before setting
            logger.info("downloading passband: {}".format(value))
            download_passband(value)

        self._value = value

        # run_checks if requested (default)
        if run_checks is None:
            run_checks = conf.interactive_checks
        if run_checks and self._bundle:
            passed, msg = self._bundle.run_checks()
            if not passed:
                # passed is either False (failed) or None (raise Warning)
                msg += "  If not addressed, this warning will continue to be raised and will throw an error at run_compute."
                logger.warning(msg)

        self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})

class SelectParameter(Parameter):
    """
    Parameter in which the value is a list of pre-defined choices
    """
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(SelectParameter, self).__init__(*args, **kwargs)

        self._choices = kwargs.get('choices', [])

        self.set_value(kwargs.get('value', []))

        self._dict_fields_other = ['description', 'choices', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @property
    def choices(self):
        """
        Return the valid list of choices.

        This is identical to: <phoebe.parameters.SelectParameter.get_choices>

        Returns
        ---------
        * (list) list of valid choices
        """
        return self._choices

    def get_choices(self):
        """
        Return the valid list of choices.

        This is identical to: <phoebe.parameters.SelectParameter.choices>

        Returns
        ---------
        * (list) list of valid choices
        """
        return self._choices

    def valid_selection(self, value):
        """
        Determine if `value` is valid given the current value of
        <phoebe.parameters.SelectParameter.choices>.

        In order to be valid, each item in the list `value` can be one of the
        items in the list of or match with at least one item by allowing for
        '*' and '?' wildcards.  Wildcard matching is done via the fnmatch
        python package.

        See also:
        * <phoebe.parameters.SelectParameter.remove_not_valid_selections>
        * <phoebe.parameters.SelectParameter.expand_value>

        Arguments
        ----------
        * `value` (string or list): the value to test against the list of choices

        Returns
        --------
        * (bool): whether `value` is valid given the choices.
        """
        if isinstance(value, list):
            return np.all([self.valid_selection(v) for v in value])

        if value in self.choices:
            return True

        # allow for wildcards
        for choice in self.choices:
            if fnmatch(choice, value):
                return True

        return False

    @update_if_client
    def get_value(self, expand=False, **kwargs):
        """
        Get the current value of the <phoebe.parameters.SelectParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        See also:
        * <phoebe.parameters.SelectParameter.expand_value>

        Arguments
        ----------
        * `expand` (bool, optional, default=False): whether to expand any
            wildcards in the stored value against the valid choices (see
            <phoebe.parameters.SelectParameter.choices>)
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (list) the current or overridden value of the Parameter
        """
        if expand:
            return self.expand_value(**kwargs)

        default = super(SelectParameter, self).get_value(**kwargs)
        if default is not None: return default
        return self._value

    def expand_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.SelectParameter>.

        This is simply a shortcut to <phoebe.parameters.SelectParameter.get_value>
        but passing `expand=True`.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        See also:
        * <phoebe.parameters.SelectParameter.valid_selection>
        * <phoebe.parameters.SelectParameter.remove_not_valid_selections>

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (list) the current or overridden value of the Parameter
        """
        selection = []
        for v in self.get_value(**kwargs):
            for choice in self.choices:
                if v==choice and choice not in selection:
                    selection.append(choice)
                elif fnmatch(choice, v) and choice not in selection:
                    selection.append(choice)

        return selection

    @send_if_client
    def set_value(self, value, run_checks=None, **kwargs):
        """
        Set the current value of the <phoebe.parameters.SelectParameter>.

        `value` must be valid according to
        <phoebe.parmaeters.SelectParameter.valid_selection>, otherwise a
        ValueError will be raised.

        Arguments
        ----------
        * `value` (string): the new value of the Parameter.
        * `run_checks` (bool, optional): whether to call
            <phoebe.frontend.bundle.Bundle.run_checks> after setting the value.
            If `None`, the value in `phoebe.conf.interactive_checks` will be used.
            This will not raise an error, but will cause a warning in the logger
            if the new value will cause the system to fail checks.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to the correct type
        * ValueError: if `value` is not valid for the current choices in
            <phoebe.parameters.SelectParameter.choices>.
            See also <phoebe.parameters.SelectParameter.valid_selection>
        """
        _orig_value = deepcopy(self.get_value())

        if isinstance(value, str):
            value = [value]

        if not isinstance(value, list):
            raise TypeError("value must be a list of strings, received {}".format(type(value)))

        try:
            value = [str(v) for v in value]
        except:
            raise ValueError("could not cast to list of strings")

        invalid_selections = []
        for v in value:
            if not self.valid_selection(v):
                invalid_selections.append(v)

        if len(invalid_selections):
            raise ValueError("{} are not valid selections.  Choices: {}".format(invalid_selections, self.choices))

        self._value = value

        # run_checks if requested (default)
        if run_checks is None:
            run_checks = conf.interactive_checks
        if run_checks and self._bundle:
            passed, msg = self._bundle.run_checks()
            if not passed:
                # passed is either False (failed) or None (raise Warning)
                logger.warning(msg)

        self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})

    def remove_not_valid_selections(self):
        """
        Update the value to remove any that are (no longer) valid.  This
        should not need to be called manually, but is often called internally
        when components or datasets are removed from the
        <phoebe.frontend.bundle.Bundle>.

        See also:
        * <phoebe.parameters.SelectParameter.valid_selection>
        * <phoebe.parameters.SelectParameter.expand_value>
        * <phoebe.parameters.SelectParameter.set_value>
        """
        value = [v for v in self.get_value() if self.valid_selection(v)]
        self.set_value(value)

    def __add__(self, other):
        if isinstance(other, str):
            other = [other]

        if not isinstance(other, list):
            return super(SelectParameter, self).__add__(self, other)

        # then we have a list, so we want to append to the existing value
        return list(set(self.get_value()+other))

    def __sub__(self, other):
        if isinstance(other, str):
            other = [other]

        if not isinstance(other, list):
            return super(SelectParameter, self).__sub__(self, other)

        return [v for v in self.get_value() if v not in other]

class BoolParameter(Parameter):
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(BoolParameter, self).__init__(*args, **kwargs)

        self.set_value(kwargs.get('value', True))

        self._dict_fields_other = ['description', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @update_if_client
    def get_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.BoolParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (bool) the current or overridden value of the Parameter
        """
        default = super(BoolParameter, self).get_value(**kwargs)
        if default is not None: return default
        return self._value

    @send_if_client
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.BoolParameter>.

        If not a boolean, `value` is casted as follows:
        * 'false', 'False', '0' -> `False`
        * default python casting (0->`False`, other numbers->`True`, strings with length->`True`)

        Arguments
        ----------
        * `value` (bool): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to a boolean
        """
        _orig_value = deepcopy(self.get_value())

        if value in ['false', 'False', '0']:
            value = False

        try:
            value = bool(value)
        except:
            raise ValueError("could not cast value to boolean")
        else:
            self._value = value

            if self.context not in ['setting', 'history']:
                self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})


class DictParameter(Parameter):
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(DictParameter, self).__init__(*args, **kwargs)

        self.set_value(kwargs.get('value', {}))

        self._dict_fields_other = ['description', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @update_if_client
    def get_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.DictParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (dict) the current or overridden value of the Parameter
        """
        default = super(DictParameter, self).get_value(**kwargs)
        if default is not None: return default
        return self._value

    @send_if_client
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.DictParameter>.

        Arguments
        ----------
        * `value` (dict): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to the correct type
            or is not a valid value for the Parameter.
        """
        _orig_value = deepcopy(self.get_value())

        try:
            value = dict(value)
        except:
            raise ValueError("could not cast value to dictionary")
        else:
            self._value = value

            self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})


class IntParameter(Parameter):
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(IntParameter, self).__init__(*args, **kwargs)

        limits = kwargs.get('limits', (None, None))
        self.set_limits(limits)

        self.set_value(kwargs.get('value', 1))

        self._dict_fields_other = ['description', 'value', 'limits', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @property
    def limits(self):
        """
        Return the current valid limits for the <phoebe.parameters.IntParameter>.

        This is identical to <phoebe.parameters.IntParameter.get_limits>.

        See also:
        * <phoebe.parameters.IntParameter.set_limits>
        * <phoebe.parameters.IntParameter.within_limits>

        Returns
        --------
        * (tuple): the current limits, where `None` means no lower/upper limits.
        """
        return self._limits

    def get_limits(self):
        """
        Return the current valid limits for the <phoebe.parameters.IntParameter>.

        This is identical to <phoebe.parameters.IntParameter.limits>.

        See also:
        * <phoebe.parameters.IntParameter.set_limits>
        * <phoebe.parameters.IntParameter.within_limits>

        Returns
        --------
        * (tuple): the current limits, where `None` means no lower/upper limits.
        """
        return self.limits

    def set_limits(self, limits=(None, None)):
        """
        Set the limits for the <phoebe.parameters.IntParameter>.

        See also:
        * <phoebe.parameters.IntParameter.get_limits>
        * <phoebe.parameters.IntParameter.within_limits>

        Arguments
        ----------
        * `limits` (tuple, optional, default=(None, None)): new limits
            formatted as (`lower`, `upper`) where either value can be `None`
            (interpretted as no lower/upper limits).
        """
        if not len(limits)==2:
            raise ValueError("limits must be in the format: (min, max)")

        if None not in limits and limits[1] < limits[0]:
            raise ValueError("lower limits must be less than upper limit")

        limits = list(limits)

        self._limits = limits

    def within_limits(self, value):
        """
        Check whether a value falls within the set limits.

        See also:
        * <phoebe.parameters.IntParameter.get_limits>
        * <phoebe.parameters.IntParameter.set_limits>

        Arguments
        --------
        * `value` (int): the value to check against the current limits.

        Returns
        --------
        * (bool): whether `value` is valid according to the limits.
        """

        return (self.limits[0] is None or value >= self.limits[0]) and (self.limits[1] is None or value <= self.limits[1])

    def _check_value(self, value):
        if isinstance(value, str):
            value = float(value)

        try:
            value = int(value)
        except:
            raise ValueError("could not cast value to integer")
        else:

            # make sure the value is within the limits
            if not self.within_limits(value):
                raise ValueError("value of {} must be within limits of {}".format(self.qualifier, self.limits))

        return value

    @update_if_client
    def get_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.IntParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (int) the current or overridden value of the Parameter
        """
        default = super(IntParameter, self).get_value(**kwargs)
        if default is not None: return default
        return self._value

    @send_if_client
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.IntParameter>.

        See also:
        * <phoebe.parameters.IntParameter.get_limits>
        * <phoebe.parameters.IntParameter.set_limits>
        * <phoebe.parameters.IntParameter.within_limits>

        Arguments
        ----------
        * `value` (int): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to an integer
        * ValueError: if `value` is outside the limits.  See:
            <phoebe.parameters.IntParameter.get_limits> and
            <phoebe.parameters.IntParameter.within_limits>
        """
        _orig_value = deepcopy(self.get_value())

        value = self._check_value(value)

        self._value = value

        self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})


class FloatParameter(Parameter):
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>

        additional options:
        * `default_unit`
        """
        super(FloatParameter, self).__init__(*args, **kwargs)

        self._in_constraints = []                        # labels of constraints that have this parameter in the expression (not implemented yet)
        self._is_constraint = None                          # label of the constraint that defines the value of this parameter (not implemented yet)

        default_unit = kwargs.get('default_unit', None)
        self.set_default_unit(default_unit)

        limits = kwargs.get('limits', (None, None))
        self.set_limits(limits)

        unit = kwargs.get('unit', None)  # will default to default_unit in set_value

        if isinstance(unit, unicode):
          unit = u.Unit(str(unit))


        timederiv = kwargs.get('timederiv', None)
        self.set_timederiv(timederiv)

        self.set_value(kwargs.get('value', ''), unit)

        self._dict_fields_other = ['description', 'value', 'quantity', 'default_unit', 'limits', 'visible_if', 'copy_for'] # TODO: add adjust?  or is that a different subclass?
        if conf.devel:
            # NOTE: this check will take place when CREATING the parameter,
            # so toggling devel after won't affect whether timederiv is included
            # in string representations.
            self._dict_fields_other += ['timederiv']

        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @property
    def default_unit(self):
        """
        Return the default unit for the <phoebe.parameters.FloatParameter>.

        This is identical to <phoebe.parameters.FloatParameter.get_default_unit>.

        See also:
        * <phoebe.parameters.FloatParameter.set_default_unit>

        Returns
        --------
        * (unit): the current default units.
        """
        return self._default_unit

    def get_default_unit(self):
        """
        Return the default unit for the <phoebe.parameters.FloatParameter>.

        This is identical to <phoebe.parameters.FloatParameter.default_unit>.

        See also:
        * <phoebe.parameters.FloatParameter.set_default_unit>

        Returns
        --------
        * (unit): the current default units.
        """
        return self.default_unit

    def set_default_unit(self, unit):
        """
        Set the default unit for the <phoebe.parameters.FloatParameter>.

        See also:
        * <phoebe.parameters.FloatParameter.get_default_unit>

        Arguments
        --------
        * `unit` (unit or valid string): the desired new units.  If the Parameter
            currently has default units, then the new units must be compatible
            with the current units

        Raises
        -------
        * Error: if the new and current units are incompatible.
        """
        # TODO: add to docstring documentation about what happens (does the value convert, etc)
        # TODO: check to make sure isinstance(unit, astropy.u.Unit)
        # TODO: check to make sure can convert from current default unit (if exists)
        if isinstance(unit, unicode) or isinstance(unit, str):
          unit = u.Unit(str(unit))
        elif unit is None:
            unit = u.dimensionless_unscaled

        if not _is_unit(unit):
            raise TypeError("unit must be a Unit")

        if hasattr(self, '_default_unit') and self._default_unit is not None:
            # we won't use a try except here so that the error comes from astropy
            check_convert = self._default_unit.to(unit)

        self._default_unit = unit

    @property
    def limits(self):
        """
        Return the current valid limits for the <phoebe.parameters.FloatParameter>.

        This is identical to <phoebe.parameters.FloatParameter.get_limits>.

        See also:
        * <phoebe.parameters.FloatParameter.set_limits>
        * <phoebe.parameters.FloatParameter.within_limits>

        Returns
        --------
        * (tuple): the current limits, where `None` means no lower/upper limits.
        """
        return self._limits

    def get_limits(self):
        """
        Return the current valid limits for the <phoebe.parameters.FloatParameter>.

        This is identical to <phoebe.parameters.FloatParameter.get_limits>.

        See also:
        * <phoebe.parameters.FloatParameter.set_limits>
        * <phoebe.parameters.FloatParameter.within_limits>

        Returns
        --------
        * (tuple): the current limits, where `None` means no lower/upper limits.
        """
        return self.limits

    def set_limits(self, limits=(None, None)):
        """
        Set the limits for the <phoebe.parameters.FloatParameter>.

        See also:
        * <phoebe.parameters.FloatParameter.get_limits>
        * <phoebe.parameters.FloatParameter.within_limits>

        Arguments
        ----------
        * `limits` (tuple, optional, default=(None, None)): new limits
            formatted as (`lower`, `upper`) where either value can be `None`
            (interpretted as no lower/upper limits).  If the individual values
            are floats (not quantities), they'll be assumed to be in the default
            units of the Parameter (see
            <phoebe.parameters.FloatParameter.get_default_unit> and
            <phoebe.parameters.FloatParameter.set_default_unit>)
        """
        if not len(limits)==2:
            raise ValueError("limits must be in the format: (min, max)")

        limits = list(limits)
        for i in range(2):
            # first convert to float if integer
            if isinstance(limits[i], int):
                limits[i] = float(limits[i])

            # now convert to quantity using default unit if value was float or int
            if isinstance(limits[i], float):
                limits[i] = limits[i] * self.default_unit

        if None not in limits and limits[1] < limits[0]:
            raise ValueError("lower limits must be less than upper limit")

        self._limits = limits

    def within_limits(self, value):
        """
        Check whether a value falls within the set limits.

        See also:
        * <phoebe.parameters.FloatParameter.get_limits>
        * <phoebe.parameters.FloatParameter.set_limits>

        Arguments
        --------
        * `value` (float/quantity): the value to check against the current
            limits.  If `value` is a float, it is assume to have the same
            units as the default units (see
            <phoebe.parameters.FloatParameter.get_default_unit> and
            <phoebe.parameters.FloatParameter.set_default_unit>).

        Returns
        --------
        * (bool): whether `value` is valid according to the limits.
        """

        if isinstance(value, int) or isinstance(value, float):
            value = value * self.default_unit

        return (self.limits[0] is None or value >= self.limits[0]) and (self.limits[1] is None or value <= self.limits[1])

    @property
    def timederiv(self):
        return self._timederiv

    @property
    def quantity(self):
        """
        Shortcut to <phoebe.parameters.FloatParameter.get_quantity>
        """
        return self.get_quantity()

    def get_timederiv(self):
        """
        """
        return self._timederiv

    def set_timederiv(self, timederiv):
        """
        """
        self._timederiv = timederiv

    #@update_if_client is on the called get_quantity
    def get_value(self, unit=None, t=None, **kwargs):
        """
        Get the current value of the <phoebe.parameters.FloatParameter> or
        <phoebe.parameters.FloatArrayParameter>.

        This is identical to <phoebe.parameters.FloatParameter.get_quantity>
        and is just included to match the method names of most other Parameter
        types.  See the documentation of <phoebe.parameters.FloatParameter.get_quantity>
        for full details.
        """
        default = super(FloatParameter, self).get_value(**kwargs)
        if default is not None: return default
        quantity = self.get_quantity(unit=unit, t=t, **kwargs)
        if hasattr(quantity, 'value'):
            return quantity.value
        else:
            return quantity

    @update_if_client
    def get_quantity(self, unit=None, t=None, **kwargs):
        """
        Get the current quantity of the <phoebe.parameters.FloatParameter> or
        <phoebe.parameters.FloatArrayParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        See also:
        * <phoebe.parameters.FloatParameter.get_quantity>

        Arguments
        ----------
        * `unit` (unit or string, optional, default=None): unit to convert the
            value.  If not provided, will use the default unit (see
            <phoebe.parameters.FloatParameter.default_unit>)
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (float/array) the current or overridden value of the Parameter
        """
        default = super(FloatParameter, self).get_value(**kwargs) # <- note this is calling get_value on the Parameter object
        if default is not None:
            value = default
            if isinstance(default, u.Quantity):
                return value
        else:
            value = self._value

        if isinstance(value, nparray.ndarray):
            if value.unit is not None:
                value = value.quantity
            else:
                value = value.array

        if t is not None:
            raise NotImplementedError("timederiv is currently disabled until it can be tested thoroughly")

        if t is not None and self.is_constraint is not None:
            # TODO: is this a risk for an infinite loop?
            value = self.is_constraint.get_result(t=t)

        if t is not None and self.timederiv is not None:
            # check to see if value came from a constraint - and if so, we will
            # need to re-evaluate that constraint at t=t.


            parent_ps = self.get_parent_ps()
            deriv = parent_ps.get_value(self.timederiv, unit=self.default_unit/u.d)
            # t0 = parent_ps.get_value('t0_values', unit=u.d)
            t0 = self._bundle.get_value('t0', context='system', unit=u.d)

            # if time has been provided without units, we assume the same units as t0
            if not hasattr(time, 'value'):
                # time = time * parent_ps.get_parameter('t0_values').default_unit
                time = time * self._bundle.get_value('t0', context='system').default_unit

            # print "***", value, deriv, time, t0
            value = value + deriv*(time-t0)

        if unit is None:
            unit = self.default_unit

        # TODO: check to see if this is still necessary
        if isinstance(unit, str):
            # we need to do this to make sure we get PHOEBE's version of
            # the unit instead of astropy's
            unit = u.Unit(unit)

        # TODO: catch astropy units and convert to PHOEBE's?

        if unit is None or value is None:
            return value
        else:
            # NOTE: astropy will raise an error if units not compatible
            return value.to(unit)

    def _check_value(self, value, unit=None):
        if isinstance(value, tuple) and (len(value) !=2 or isinstance(value[1], float) or isinstance(value[1], int)):
            # allow passing tuples (this could be a FloatArrayParameter - if it isn't
            # then this array will fail _check_type below)
            value = np.asarray(value)
        # accept tuples (ie 1.2, 'rad') from dictionary access
        if isinstance(value, tuple) and unit is None:
            value, unit = value
        if isinstance(value, str):
            value = float(value)
        if isinstance(value, dict) and 'nparray' in value.keys():
            # then we're loading the JSON version of an nparray object
            value = nparray.from_dict(value)

        return self._check_type(value), unit

    def _check_type(self, value):
        # we do this separately so that FloatArrayParameter can keep this set_value
        # and just subclass _check_type
        if isinstance(value, u.Quantity):
            if not (isinstance(value.value, float) or isinstance(value.value, int)):
                raise ValueError("value could not be cast to float")

        elif not (isinstance(value, float) or isinstance(value, int)):
            # TODO: probably need to change this to be flexible with all the cast_types
            raise ValueError("value could not be cast to float")

        return value

    #@send_if_client is on the called set_quantity
    def set_value(self, value, unit=None, force=False, run_checks=None, **kwargs):
        """
        Set the current value/quantity of the <phoebe.parameters.FloatParameter>.

        This is identical to <phoebe.parameters.FloatParameter.set_quantity>
        and is just included to match the method names of most other Parameter
        types.  See the documentation of <phoebe.parameters.FloatParameter.set_quantity>
        for full details.

        See also:
        * <phoebe.parameters.FloatParameter.set_quantity>
        * <phoebe.parameters.FloatParameter.get_limits>
        * <phoebe.parameters.FloatParameter.set_limits>
        * <phoebe.parameters.FloatParameter.within_limits>
        """
        return self.set_quantity(value=value, unit=unit, force=force, run_checks=run_checks, **kwargs)

    @send_if_client
    def set_quantity(self, value, unit=None, force=False, run_checks=None, run_constraints=None, **kwargs):
        """
        Set the current value/quantity of the <phoebe.parameters.FloatParameter>
        or <phoebe.parameters.FloatArrayParameter>.

        Units can either be passed by providing a Quantity object to `value`
        OR by passing a unit object (or valid string representation) to `unit`.
        If units are provided with both but do not agree, an error will be raised.

        See also:
        * <phoebe.parameters.FloatParameter.set_value>
        * <phoebe.parameters.FloatParameter.get_limits>
        * <phoebe.parameters.FloatParameter.set_limits>
        * <phoebe.parameters.FloatParameter.within_limits>

        Arguments
        ----------
        * `value` (float/quantity): the new value of the Parameter.
        * `unit` (unit or valid string, optional, default=None): the unit in
            which `value` is provided.  If not provided or None, it is assumed
            that `value` is in the default units (see <phoebe.parameters.FloatParameter.default_unit>
            and <phoebe.parameters.FloatParameter.set_default_unit>).
        * `force` (bool, optional, default=False, EXPERIMENTAL): override
            and set the value of a constrained Parameter.
        * `run_checks` (bool, optional): whether to call
            <phoebe.frontend.bundle.Bundle.run_checks> after setting the value.
            If `None`, the value in `phoebe.conf.interactive_checks` will be used.
            This will not raise an error, but will cause a warning in the logger
            if the new value will cause the system to fail checks.
        * `run_constraints` whether to run any necessary constraints after setting
            the value.  If `None`, the value in `phoebe.conf.interactive_constraints`
            will be used.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to a float/quantity.
        * ValueError: if the units of `value` and `unit` are in disagreement
        * ValueError: if the provided units are not compatible with the
            default units.
        * ValueError: if `value` is outside the limits.  See:
            <phoebe.parameters.FloatParameter.get_limits> and
            <phoebe.parameters.FloatParameter.within_limits>
        """
        _orig_value = deepcopy(self.get_value())

        if len(self.constrained_by) and not force:
            raise ValueError("cannot change the value of a constrained parameter.  This parameter is constrained by '{}'".format(', '.join([p.uniquetwig for p in self.constrained_by])))

        # if 'time' in kwargs.keys() and isinstance(self, FloatArrayParameter):
        #     # then find the correct index and set by index instead
        #     time_param = self._bundle

        value, unit = self._check_value(value, unit)

        if isinstance(unit, str):
            # print "*** converting string to unit"
            unit = u.Unit(unit)  # should raise error if not a recognized unit
        elif unit is not None and not _is_unit(unit):
            raise TypeError("unit must be an phoebe.u.Unit or None, got {}".format(unit))

        # check to make sure value and unit don't clash
        if isinstance(value, u.Quantity) or (isinstance(value, nparray.ndarray) and value.unit is not None):
            if unit is not None:
                # check to make sure they're the same
                if value.unit != unit:
                    raise ValueError("value and unit do not agree")

        elif value is None:
            # allowed for FloatArrayParameter if self.allow_none.  This should
            # already have been checked by self._check_type
            value = value

        elif unit is not None:
            # print "*** converting value to quantity"
            value = value * unit

        elif self.default_unit is not None:
            value = value * self.default_unit

        # handle wrapping for angle measurements
        if value is not None and value.unit.physical_type == 'angle':
            # NOTE: this may fail for nparray types
            if value > (360*u.deg) or value < (0*u.deg):
                value = value % (360*u.deg)
                logger.warning("wrapping value of {} to {}".format(self.qualifier, value))

        # make sure the value is within the limits, if this isn't an array or nan
        if isinstance(value, float) and not self.within_limits(value):
            raise ValueError("value of {} must be within limits of {}".format(self.qualifier, self.limits))

        # make sure we can convert back to the default_unit
        try:
            if self.default_unit is not None and value is not None:
                test = value.to(self.default_unit)
        except u.core.UnitsError:
            raise ValueError("cannot convert provided unit ({}) to default unit ({})".format(value.unit, self.default_unit))
        except:
            self._value = value
        else:
            self._value = value

        if run_constraints is None:
            run_constraints = conf.interactive_constraints
        if run_constraints:
            for constraint_id in self._in_constraints:
                #~ print "*** parameter.set_value run_constraint uniqueid=", constraint_id
                self._bundle.run_constraint(uniqueid=constraint_id, skip_kwargs_checks=True)
        else:
            # then we want to delay running constraints... so we need to track
            # which ones need to be run once requested
            for constraint_id in self._in_constraints:
                if constraint_id not in self._bundle._delayed_constraints:
                    self._bundle._delayed_constraints.append(constraint_id)

        # run_checks if requested (default)
        if run_checks is None:
            run_checks = conf.interactive_checks
        if run_checks and self._bundle:
            passed, msg = self._bundle.run_checks()
            if not passed:
                # passed is either False (failed) or None (raise Warning)
                msg += "  If not addressed, this warning will continue to be raised and will throw an error at run_compute."
                logger.warning(msg)

        self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})


    #~ @property
    #~ def constraint(self):
        #~ """
        #~ returns the label of the constraint that constrains this parameter
        #~
        #~ you can then access all of the parameters of the constraint via bundle.get_constraint(label)
        #~ """
        #~ return self.constraint_expression.uniquetwig

    @property
    def is_constraint(self):
        """
        Returns the <phoebe.parameters.ConstraintParameter> that constrains
        this parameter.  If this <phoebe.parameters.FloatParameter> is not
        constrained, this will return None.

        See also:
        * <phoebe.parameters.FloatParameter.constrained_by>
        * <phoebe.parameters.FloatParameter.in_constraints>
        * <phoebe.parameters.FloatParameter.constrains>
        * <phoebe.parameters.FloatParameter.related_to>

        Returns
        -------
        * (None or <phoebe.parameters.ConstraintParameter)
        """
        if self._is_constraint is None:
            return None
        return self._bundle.get_parameter(context='constraint', uniqueid=self._is_constraint)

    @property
    def constrained_by(self):
        """
        Returns a list of <phoebe.parameters.Parameter> objects that constrain
        this <phoebe.parameters.FloatParameter>.

        See also:
        * <phoebe.parameters.FloatParameter.is_constraint>
        * <phoebe.parameters.FloatParameter.in_constraints>
        * <phoebe.parameters.FloatParameter.constrains>
        * <phoebe.parameters.FloatParameter.related_to>

        Returns
        -------
        * (list of <phoebe.parameters.Parameter>)
        """
        if self._is_constraint is None:
            return []
        params = []
        for var in self.is_constraint._vars:
            param = var.get_parameter()
            if param.uniqueid != self.uniqueid:
                params.append(param)
        return params

    #~ @property
    #~ def in_constraints(self):
        #~ """
        #~ returns a list the labels of the constraints in which this parameter constrains another
        #~
        #~ you can then access all of the parameters of a given constraint via bundle.get_constraint(constraint)
        #~ """
        #~ return [param.uniquetwig for param in self.in_constraints_expressions]

    @property
    def in_constraints(self):
        """
        Returns a list of the expressions in which this
        <phoebe.parameters.FloatParameter> constrains other Parameters.

        See also:
        * <phoebe.parameters.FloatParameter.is_constraint>
        * <phoebe.parameters.FloatParameter.constrained_by>
        * <phoebe.parameters.FloatParameter.constrains>
        * <phoebe.parameters.FloatParameter.related_to>

        Returns
        -------
        * (list of expressions)
        """
        expressions = []
        for uniqueid in self._in_constraints:
            expressions.append(self._bundle.get_parameter(context='constraint', uniqueid=uniqueid))
        return expressions

    @property
    def constrains(self):
        """
        Returns a list of Parameters that are constrained by this
         <phoebe.parameters.FloatParameter>.

        See also:
        * <phoebe.parameters.FloatParameter.is_constraint>
        * <phoebe.parameters.FloatParameter.constrained_by>
        * <phoebe.parameters.FloatParameter.in_constraints>
        * <phoebe.parameters.FloatParameter.related_to>

         Returns
         -------
         * (list of Parameters)
        """
        params = []
        for constraint in self.in_constraints:
            for var in constraint._vars:
                param = var.get_parameter()
                if param.component == constraint.component and param.qualifier == constraint.qualifier:
                    if param not in params and param.uniqueid != self.uniqueid:
                        params.append(param)
        return params

    @property
    def related_to(self):
        """
        Returns a list of all parameters that are either constrained by or
        constrain this parameter.

        See also:
        * <phoebe.parameters.FloatParameter.is_constraint>
        * <phoebe.parameters.FloatParameter.constrained_by>
        * <phoebe.parameters.FloatParameter.in_constraints>
        * <phoebe.parameters.FloatParameter.constrains>

         Returns
         -------
         * (list of Parameters)
        """
        params = []
        constraints = self.in_constraints
        if self.is_constraint is not None:
            constraints.append(self.is_constraint)

        for constraint in constraints:
            for var in constraint._vars:
                param = var.get_parameter()
                if param not in params and param.uniqueid != self.uniqueid:
                    params.append(param)

        return params


class FloatArrayParameter(FloatParameter):
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>

        Additional arguments
        ---------------------
        * `allow_none` (bool, optional, default=False)
        """
        self._allow_none = kwargs.get('allow_none', False)
        super(FloatArrayParameter, self).__init__(*args, **kwargs)

        # NOTE: default_unit and value handled in FloatParameter.__init__()

        self._dict_fields_other = ['description', 'value', 'default_unit', 'visible_if', 'copy_for', 'allow_none']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    def __repr__(self):
        """
        FloatArrayParameter needs to "truncate" the array by temporarily
        overriding np.set_printoptions
        """
        opt = np.get_printoptions()
        # <Parameter:_qualifier= takes 13+len(qualifier) characters
        np.set_printoptions(threshold=8, edgeitems=3, linewidth=opt['linewidth']-(13+len(self.qualifier)))
        repr_ = super(FloatArrayParameter, self).__repr__()
        np.set_printoptions(**opt)
        return repr_

    def __str__(self):
        """
        FloatArrayParameter needs to "truncate" the array by temporarily
        overriding np.set_printoptions
        """
        opt = np.get_printoptions()
        # Value:_ takes 7 characters
        np.set_printoptions(threshold=8, edgeitems=3, linewidth=opt['linewidth']-7)
        str_ = super(FloatArrayParameter, self).__str__()
        np.set_printoptions(**opt)
        return str_

    @property
    def allow_none(self):
        """
        Return whether None is an acceptable value in addition to an array

        Returns
        --------
        * (bool)
        """
        return self._allow_none

    def to_string_short(self):
        """
        Short abbreviated string representation of the
        <phoebe.parameters.FloatArrayParameter>.

        See also:
        * <phoebe.parameters.Parameter.to_string>

        Returns
        --------
        * (str)
        """
        opt = np.get_printoptions()
        np.set_printoptions(threshold=8, edgeitems=3, linewidth=opt['linewidth']-len(self.uniquetwig)-2)
        str_ = super(FloatArrayParameter, self).to_string_short()
        np.set_printoptions(**opt)
        return str_

    def interp_value(self, **kwargs):
        """
        Interpolate to find the value in THIS array given a value from
        ANOTHER array in the SAME parent <phoebe.parameters.ParameterSet>
        (see <phoebe.parameters.Parameter.get_parent_ps>).

        This currently only supports simple 1D linear interpolation (via
        `numpy.interp`) and does no checks to make sure you're interpolating
        with respect to an independent parameter - so use with caution.

        ```py
        print this_param.get_parent_ps().qualifiers
        'other_qualifier' in this_param.get_parent_ps().qualifiers
        True
        this_param.interp_value(other_qualifier=5)
        ```

        where other_qualifier must be in ParentPS.qualifiers
        AND must point to another <phoebe.parameters.FloatArrayParameter>.

        Example:

        ```py
        b['fluxes@lc01@model'].interp_value(times=10.2)
        ```

        The only exception is when interpolating in phase-space, in which
        case the 'times' qualifier must be found in the ParentPS.  Interpolating
        in phase-space is only allowed if there are no time derivatives present
        in the system.  This can be checked with
        <phoebe.parameters.HierarchyParameter.is_time_dependent>.  To interpolate
        in phases:

        ```
        b['fluxes@lc01@model'].interp_value(phases=0.5)
        ```

        Additionally, when interpolating in time but the time is outside the
        available range, phase-interpolation will automatically be attempted,
        with a warning raised via the <phoebe.logger>.

        NOTE: this method does not currently support units.  You must provide
        the interpolating value in its default units and are returned the
        value in the default units (no support for quantities).

        Arguments
        ----------
        * `component` (string, optional): if interpolating in phases, `component`
            will be passed along to <phoebe.frontend.bundle.Bundle.to_phase>.
        * `t0` (string/float, optional): if interpolating in phases, `t0` will
            be passed along to <phoebe.frontend.bundle.Bundle.to_phase>.
        * `**kwargs`: see examples above, must provide a single
            qualifier-value pair to use for interpolation.  In most cases
            this will probably be time=value or wavelength=value.

        Returns
        --------
        * (float) the interpolated value.

        Raises
        --------
        * KeyError: if more than one qualifier is passed
        * KeyError: if no qualifier is passed that belongs to the
            parent :class:`ParameterSet`
        * KeyError: if the qualifier does not point to another
            <phoebe.parameters.FloatArrayParameter>
        """
        # TODO: add support for units
        # TODO: add support for non-linear interpolation (probably would need to use scipy)?
        # TODO: add support for interpolating in phase_space

        if len(kwargs.keys()) > 1:
            raise KeyError("interp_value only takes a single qualifier-value pair")

        qualifier, qualifier_interp_value = kwargs.items()[0]

        if isinstance(qualifier_interp_value, str):
            # then assume its a twig and try to resolve
            # for example: time='t0_supconj'
            qualifier_interp_value = self._bundle.get_value(qualifier_interp_value, context=['system', 'component'])

        parent_ps = self.get_parent_ps()

        if qualifier not in parent_ps.qualifiers and not (qualifier=='phases' and 'times' in parent_ps.qualifiers):
            # TODO: handle plural to singular (having to say
            # interp_value(times=5) is awkward)
            raise KeyError("'{}' not valid qualifier (must be one of {})".format(qualifier, parent_ps.qualifiers))

        if qualifier=='times':
            times = parent_ps.get_value(qualifier='times')
            if np.any(qualifier_interp_value < times.min()) or np.any(qualifier_interp_value > times.max()):
                qualifier_interp_value_time = qualifier_interp_value
                qualifier = 'phases'
                qualifier_interp_value = self._bundle.to_phase(qualifier_interp_value_time, **{k:v for k,v in kwargs.items() if k in ['component', 't0']})
                logger.warning("times={} outside of interpolation limits ({} -> {})... attempting to interpolate at phases={}".format(qualifier_interp_value_time, times.min(), times.max(), qualifier_interp_value))


        if qualifier=='phases':
            if self._bundle.hierarchy.is_time_dependent():
                raise ValueError("cannot interpolate in phase for time-dependent systems")

            times = parent_ps.get_value(qualifier='times')
            phases = self._bundle.to_phase(times, **{k:v for k,v in kwargs.items() if k in ['component', 't0']})

            sort = phases.argsort()

            return np.interp(qualifier_interp_value, phases[sort], self.get_value()[sort])

        else:

            qualifier_parameter = parent_ps.get(qualifier=qualifier)

            if not isinstance(qualifier_parameter, FloatArrayParameter):
                raise KeyError("'{}' does not point to a FloatArrayParameter".format(qualifier))

            return np.interp(qualifier_interp_value, qualifier_parameter.get_value(), self.get_value())


    def append(self, value):
        """
        Append a value to the end of the array.

        Arguments
        ---------
        * `value` (float): the float to append to the end of the current array
        """
        # check units
        if isinstance(value, u.Quantity):
            value = value.to(self.default_unit).value

        if isinstance(value, nparray.ndarray):
            value = value.to_array()

        new_value = np.append(self.get_value(), value) * self.default_unit
        self.set_value(new_value)

    def set_index_value(self, index, value, **kwargs):
        """
        Set the value of the array at a given index.

        Arguments
        -----------
        * `index` (int): the index of the value to be replaced
        * `value` (float): the value to be replaced
        * `**kwargs`: IGNORED
        """
        if isinstance(value, u.Quantity):
            value = value.to(self.default_unit).value
        elif isinstance(value, str):
            value = float(value)
        #else:
            #value = value*self.default_unit
        lst =self.get_value()#.value
        lst[index] = value
        self.set_value(lst)

    def __add__(self, other):
        if not (isinstance(other, list) or isinstance(other, np.ndarray)):
            return super(FloatArrayParameter, self).__add__(self, other)

        # then we have a list, so we want to append to the existing value
        return np.append(self.get_value(), np.asarray(other))

    def __sub__(self, other):
        if not (isinstance(other, list) or isinstance(other, np.ndarray)):
            return super(FloatArrayParameter, self).__add__(self, other)

        # then we have a list, so we want to append to the existing value
        return np.array([v for v in self.get_value() if v not in other])

    # def set_value_at_time(self, time, value, **kwargs):
    #     """
    #     """
    #     parent_ps = self.get_parent_ps()
    #     times_param = parent_ps.get_parameter(qualifier='times')
    #     index = np.where(times_param.get_value()==time)[0][0]
    #
    #     self.set_index_value(index, value, **kwargs)


    #~ def at_time(self, time):
        #~ """
        #~ looks for a parameter with qualifier time that shares all the same meta data and
        #~ """
        #~ raise NotImplementedError

    def _check_type(self, value):
        """
        """
        if self.allow_none and value is None:
            value = None

        elif isinstance(value, u.Quantity):
            if isinstance(value.value, float) or isinstance(value.value, int):
                value = np.array([value])

        # if isinstance(value, str):
            # value = np.fromstring(value)

        elif isinstance(value, float) or isinstance(value, int):
            value = np.array([value])

        elif isinstance(value, dict) and 'nparray' in value.keys():
            value = nparray.from_dict(value)

        elif not (isinstance(value, list) or isinstance(value, tuple) or isinstance(value, np.ndarray) or isinstance(value, nparray.ndarray)):
            # TODO: probably need to change this to be flexible with all the cast_types
            raise TypeError("value '{}' ({}) could not be cast to array".format(value, type(value)))

        return value

    def set_property(self, **kwargs):
        """
        Set any property of the underlying [nparray](https://github.com/kecnry/nparray/tree/1.0.0)
        object.

        Example:
        ```py
        param.set_value(start=10, stop=20)
        ```

        Arguments
        ----------
        * `**kwargs`: properties to be set on the underlying nparray object.

        Raises
        -------
        * ValueError: if the value is not an nparray object.
        """
        if not isinstance(self._value, nparray.ndarray):
            raise ValueError("value is not a nparray object")

        for property, value in kwargs.items():
            setattr(self._value, property, value)

class ArrayParameter(Parameter):
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(ArrayParameter, self).__init__(*args, **kwargs)

        self.set_value(kwargs.get('value', []))

        self._dict_fields_other = ['description', 'value', 'visible_if', 'copy_for']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    def append(self, value):
        """
        Append a value to the end of the array.

        Arguments
        ---------
        * `value`: the float to append to the end of the current array
        """
        if isinstance(value, nparray.ndarray):
            value = value.to_array()

        new_value = np.append(self.get_value(), value)
        self.set_value(new_value)

    #~ def at_time(self, time):
        #~ """
        #~ looks for a parameter with qualifier time that shares all the same meta data and
        #~ """
        #~ raise NotImplementedError

    @update_if_client
    def get_value(self, **kwargs):
        """
        Get the current value of the <phoebe.parameters.ArrayParameter>.

        **default/override values**: if passing a keyword argument with the same
            name as the Parameter qualifier (see
            <phoebe.parameters.Parameter.qualifier>), then the value passed
            to that keyword argument will be returned **instead of** the current
            value of the Parameter.  This is mostly used internally when
            wishing to override values sent to
            <phoebe.frontend.bundle.Bundle.run_compute>, for example.

        Arguments
        ----------
        * `**kwargs`: passing a keyword argument that matches the qualifier
            of the Parameter, will return that value instead of the stored value.
            See above for how default values are treated.

        Returns
        --------
        * (np array) the current or overridden value of the Parameter
        """
        default = super(ArrayParameter, self).get_value(**kwargs)
        if default is not None: return default

        if isinstance(self._value, nparray.ndarray):
            return self._value.to_array()
        else:
            return self._value

    @send_if_client
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.ArrayParameter>.

        Arguments
        ----------
        * `value` (Array): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to the correct type
            or is not a valid value for the Parameter.
        """
        _orig_value = deepcopy(self._value)
        self._value = np.array(value)

        if self.context not in ['setting', 'history']:
            self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})

class IntArrayParameter(FloatArrayParameter):
    def __init__(self, *args, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        kwargs.setdefault('default_unit', u.dimensionless_unscaled)
        super(IntArrayParameter, self).__init__(*args, **kwargs)


    def __repr__(self):
        """
        IntArrayParameter needs to "truncate" the array by temporarily
        overriding np.set_printoptions
        """
        opt = np.get_printoptions()
        # <Parameter:_qualifier= takes 13+len(qualifier) characters
        np.set_printoptions(threshold=8, edgeitems=3, linewidth=opt['linewidth']-(13+len(self.qualifier)))
        repr_ = super(IntArrayParameter, self).__repr__()
        np.set_printoptions(**opt)
        return repr_

    def __str__(self):
        """
        IntArrayParameter needs to "truncate" the array by temporarily
        overriding np.set_printoptions
        """
        opt = np.get_printoptions()
        # Value:_ takes 7 characters
        np.set_printoptions(threshold=8, edgeitems=3, linewidth=opt['linewidth']-7)
        str_ = super(IntArrayParameter, self).__str__()
        np.set_printoptions(**opt)
        return str_

    @property
    def quantity(self):
        """
        Shortcut to <phoebe.parameters.IntArrayParameter.get_quantity>.
        """
        return self.get_quantity()

    @update_if_client
    def get_quantity(self, **kwargs):
        """
        Return a quantity object, even though <phoebe.parameters.IntArrayParameter>
        do not have units.

        Arguments
        ---------
        * `**kwargs`: ignored

        Returns
        ---------
        * (quantity)
        """
        return self.get_value() * u.dimensionless_unscaled

    @send_if_client
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.IntArrayParameter>.

        Arguments
        ----------
        * `value` (array of ints): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to the correct type
            or is not a valid value for the Parameter.
        """
        _orig_value = deepcopy(self._value)
        self._value = np.array(value, dtype=np.int)

        self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})



class HierarchyParameter(StringParameter):
    def __init__(self, value, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        dump = kwargs.pop('qualifier', None)
        super(HierarchyParameter, self).__init__(qualifier='hierarchy', value=value, **kwargs)

    def __repr__(self):
        return "<HierarchyParameter: {}>".format(self.get_value())

    def __str__(self):
        #~ return self.get_value().replace('(', '\n\t').replace(')', '\n')
        #~ def _print_item(item, tab, str_):
            #~ if isinstance(item, list):
                #~ tab += 1
                #~ for child in item:
                    #~ str_ += _print_item(child, tab, str_)
            #~ else:
                #~ return str_ + '\n' + '\t'*tab + item
        #~
        #~ str_ = ''
        #~ for item in self._parse_repr():
            #~ tab = 0
            #~ str_ += _print_item(str(item), tab, '')
#~
        #~ return str_
        if not len(self.get_value()):
            return 'NO HIERARCHY'
        else:
            return json.dumps(self._parse_repr(), indent=4).replace(',','').replace('[','').replace(']','').replace('"', '').replace('\n\n','\n')

    @send_if_client
    def set_value(self, value, update_cache=True, **kwargs):
        """
        Set the current value of the <phoebe.parameters.HierarchyParameter>.

        Arguments
        ----------
        * `value` (string): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to a string.
        """

        # TODO: check to make sure valid

        _orig_value = deepcopy(self.get_value())

        try:
            value = str(value)
        except:
            raise ValueError("cannot cast to string")
        else:
            self._value = value

            self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})

        if update_cache:
            self._update_cache()

    def _clear_cache(self):
        """
        """
        self._is_binary = {}
        self._is_contact_binary = {}

    def _update_cache(self):
        """
        """
        # update cache for is_binary and is_contact_binary
        self._clear_cache()
        if self._bundle is not None:
            # for comp in self.get_components():
            for comp in self._bundle.components:
                if comp == '_default':
                    continue
                self._is_binary[comp] = self._compute_is_binary(comp)
                self._is_contact_binary[comp] = self._compute_is_contact_binary(comp)


    def _parse_repr(self):
         """
         turn something like "orbit:outer(orbit:inner(star:starA, star:starB), star:starC)"
         into ['orbit:outer', ['orbit:inner', ['star:starA', 'star:starB'], 'star:starC']]
         """

         repr_ = self.get_value()
         repr_str = '["{}"]'.format(repr_.replace(', ', '", "').replace('(', '", ["').replace(')', '"]')).replace(']"', '"]').replace('""', '"').replace(']"', ']')
         return json.loads(repr_str)

    def _recurse_find_trace(self, structure, item, trace=[]):
        """
        given a nested structure from _parse_repr and find the trace route to get to item
        """

        try:
            i = structure.index(item)
        except ValueError:
            for j,substructure in enumerate(structure):
                if isinstance(substructure, list):
                    trace_return = self._recurse_find_trace(substructure, item, trace+[j])
                    if trace_return is not None: return trace_return

            return None
        else:
            return trace+[i]

    def _get_by_trace(self, structure, trace):
        """
        retrieve an item from the nested structure from _parse_repr given a trace (probably modified from _recurse_find_trace)
        """
        for i in trace:
            structure = structure[i]

        return structure

    def _get_structure_and_trace(self, component):
        """
        """
        obj = self._bundle.filter(component=component, context='component', check_visible=False)
        our_item = '{}:{}'.format(obj.kind, component)


        repr_ = self.get_value()
        structure = self._parse_repr()

        trace = self._recurse_find_trace(structure, our_item)

        if trace is None:
            raise ValueError("could not find hierarchy trace of {} in structure {}".format(our_item, structure))

        return structure, trace, our_item

    def rename_component(self, old_component, new_component):
        """
        Swap a component in the <phoebe.parameters.HierarchyParameter>.

        Note that this does NOT update component tags within the
        <phoebe.parametes.ParameterSet> or <phoebe.frontend.bundle.Bundle>.
        To change the name of a component, use
        <phoebe.frontend.bundle.Bundle.rename_component> instead.

        Arguments
        ----------
        * `old_component` (string): the current name of the component in the
            hierarchy
        * `new_component` (string): the replaced component
        """
        kind = self.get_kind_of(old_component)
        value = self.get_value()
        # TODO: this could still cause issues if the names of components are
        # contained in other components (ie starA, starAB)
        value = value.replace("{}:{}".format(kind, old_component), "{}:{}".format(kind, new_component))
        # delay updating cache until after the bundle
        # has had a chance to also change its component tags
        self.set_value(value, update_cache=False)

    def get_components(self):
        """
        Return a list of all components in the <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_top>
        * <phoebe.parameters.HierarchyParameter.get_stars>
        * <phoebe.parameters.HierarchyParameter.get_envelopes>
        * <phoebe.parameters.HierarchyParameter.get_orbits>
        * <phoebe.parameters.HierarchyParameter.get_meshables>

        Returns
        -------
        * (list of strings)
        """
        l = re.findall(r"[\w']+", self.get_value())
        return l[1::2]

    def get_top(self):
        """
        Return the top-level component in the <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_components>
        * <phoebe.parameters.HierarchyParameter.get_stars>
        * <phoebe.parameters.HierarchyParameter.get_envelopes>
        * <phoebe.parameters.HierarchyParameter.get_orbits>
        * <phoebe.parameters.HierarchyParameter.get_meshables>

        Returns
        -------
        * (string)
        """
        return str(self._parse_repr()[0].split(':')[1])

    def get_stars(self):
        """
        Return a list of all components with kind='star' in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_components>
        * <phoebe.parameters.HierarchyParameter.get_top>
        * <phoebe.parameters.HierarchyParameter.get_envelopes>
        * <phoebe.parameters.HierarchyParameter.get_orbits>
        * <phoebe.parameters.HierarchyParameter.get_meshables>

        Returns
        -------
        * (list of strings)
        """
        l = re.findall(r"[\w']+", self.get_value())
        # now search for indices of star and take the next entry from this flat list
        return [l[i+1] for i,s in enumerate(l) if s=='star']

    def get_envelopes(self):
        """
        Return a list of all components with kind='envelope' in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_components>
        * <phoebe.parameters.HierarchyParameter.get_top>
        * <phoebe.parameters.HierarchyParameter.get_stars>
        * <phoebe.parameters.HierarchyParameter.get_orbits>
        * <phoebe.parameters.HierarchyParameter.get_meshables>

        Returns
        -------
        * (list of strings)
        """
        l = re.findall(r"[\w']+", self.get_value())
        # now search for indices of star and take the next entry from this flat list
        return [l[i+1] for i,s in enumerate(l) if s=='envelope']

    def get_orbits(self):
        """
        Return a list of all components with kind='orbit' in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_components>
        * <phoebe.parameters.HierarchyParameter.get_top>
        * <phoebe.parameters.HierarchyParameter.get_stars>
        * <phoebe.parameters.HierarchyParameter.get_envelopes>
        * <phoebe.parameters.HierarchyParameter.get_meshables>

        Returns
        -------
        * (list of strings)
        """
        #~ l = re.findall(r"[\w']+", self.get_value())
        # now search for indices of orbit and take the next entry from this flat list
        #~ return [l[i+1] for i,s in enumerate(l) if s=='orbit']
        orbits = []
        for star in self.get_stars():
            parent = self.get_parent_of(star)
            if parent not in orbits and parent!='component' and parent is not None:
                orbits.append(parent)
        return orbits

    def get_meshables(self):
        """
        Return a list of all components that are meshable (generally stars,
        but also handles the envelope for a contact binary)
        in the <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_components>
        * <phoebe.parameters.HierarchyParameter.get_top>
        * <phoebe.parameters.HierarchyParameter.get_stars>
        * <phoebe.parameters.HierarchyParameter.get_envelopes>
        * <phoebe.parameters.HierarchyParameter.get_orbits>

        Returns
        -------
        * (list of strings)
        """
        l = re.findall(r"[\w']+", self.get_value())
        # now search for indices of star and take the next entry from this flat list
        meshables = [l[i+1] for i,s in enumerate(l) if s in ['star', 'envelope']]

        # now we want to remove any star which has a sibling envelope
        has_sibling_envelope = []
        for item in meshables:
            if self.get_sibling_of(item, kind='envelope'):
                has_sibling_envelope.append(item)

        return [m for m in meshables if m not in has_sibling_envelope]

    def get_parent_of(self, component):
        """
        Get the parent of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_envelope_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_children_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>
        * <phoebe.parameters.HierarchyParameter.get_child_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.

        Returns
        ---------
        * (string)
        """
        # example:
        # - self.get_value(): "orbit:outer(orbit:inner(star:starA, star:starB), star:starC)"
        # - component: "starA"
        # - needs to return "inner"

        if component is None:
            return self.get_top()


        structure, trace, item = self._get_structure_and_trace(component)
        # trace points us to our_item at self._get_by_trace(structure, trace)
        # so to get the parent, if our trace is [1,1,0] we want to use [1, 0] which is trace[:-2]+[trace[-2]-1]


        #~ print "***", trace
        if len(trace)<=1:
            return None

        return str(self._get_by_trace(structure, trace[:-2]+[trace[-2]-1]).split(':')[-1])

    def get_sibling_of(self, component, kind=None):
        """
        Get the sibling of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        If there is more than one sibling, the first result will be returned.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_parent_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_envelope_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_children_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>
        * <phoebe.parameters.HierarchyParameter.get_child_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.
        * `kind` (string, optional): filter to match the kind of the component.

        Returns
        ---------
        * (string)
        """
        siblings = self.get_siblings_of(component, kind=kind)
        if not len(siblings):
            return None
        else:
            return siblings[0]


    def get_siblings_of(self, component, kind=None):
        """
        Get the siblings of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_parent_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_envelope_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_children_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>
        * <phoebe.parameters.HierarchyParameter.get_child_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.
        * `kind` (string, optional): filter to match the kind of the component.

        Returns
        ---------
        * (list of strings)
        """

        structure, trace, item = self._get_structure_and_trace(component)
        #item_kind, item_label = item.split(':')

        parent_label = self.get_parent_of(component)
        siblings = self.get_children_of(parent_label, kind=kind)

        #self_ind = siblings.index(component)
        if component in siblings:
            siblings.remove(component)

        if not len(siblings):
            return []
        else:
            return siblings

    def get_envelope_of(self, component):
        """
        Get the parent-envelope of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_parent_of>
        * <phoebe.parameters.HierarchyParameter.get_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_children_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>
        * <phoebe.parameters.HierarchyParameter.get_child_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.

        Returns
        ---------
        * (string)
        """
        envelopes = self.get_siblings_of(component, 'envelope')
        if not len(envelopes):
            return []
        else:
            return envelopes[0]

    def get_stars_of_sibling_of(self, component):
        """
        Get the stars under the sibling of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        This is the same as <phoebe.parameters.Hierarchy.get_sibling_of> except
        if a sibling is in an orbit, this will recursively follow the tree to
        return a list of all stars under that orbit.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_parent_of>
        * <phoebe.parameters.HierarchyParameter.get_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_envelope_of>
        * <phoebe.parameters.HierarchyParameter.get_children_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>
        * <phoebe.parameters.HierarchyParameter.get_child_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.

        Returns
        ---------
        * (string)
        """
        sibling = self.get_sibling_of(component)

        if sibling in self.get_stars():
            return [sibling]

        stars = [child for child in self.get_stars_of_children_of(sibling)]

        # TODO: do we need to make sure there aren't duplicates?
        # return list(set(stars))

        return stars


    def get_children_of(self, component, kind=None):
        """
        Get the children of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_parent_of>
        * <phoebe.parameters.HierarchyParameter.get_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_envelope_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>
        * <phoebe.parameters.HierarchyParameter.get_child_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.
        * `kind` (string, optional): filter to match the kind of the component.

        Returns
        ---------
        * (list of strings)
        """

        structure, trace, item = self._get_structure_and_trace(component)
        item_kind, item_label = item.split(':')

        if isinstance(kind, str):
            kind = [kind]

        if item_kind not in ['orbit']:
            # return None
            return []
        else:
            items = self._get_by_trace(structure, trace[:-1]+[trace[-1]+1])
            # we want to ignore suborbits
            #return [str(ch.split(':')[-1]) for ch in items if isinstance(ch, unicode)]
            return [str(ch.split(':')[-1]) for ch in items if isinstance(ch, unicode) and (kind is None or ch.split(':')[0] in kind)]

    def get_stars_of_children_of(self, component):
        """
        Get the stars under the children of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        This is the same as <phoebe.parameters.Hierarchy.get_children_of> except
        if any of the children is in an orbit, this will recursively follow the tree to
        return a list of all stars under that orbit.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_parent_of>
        * <phoebe.parameters.HierarchyParameter.get_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_envelope_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_children_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>
        * <phoebe.parameters.HierarchyParameter.get_child_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.

        Returns
        ---------
        * (string)
        """

        stars = self.get_stars()
        orbits = self.get_orbits()
        stars_children = []

        for child in self.get_children_of(component):
            if child in stars:
                stars_children.append(child)
            elif child in orbits:
                stars_children += self.get_stars_of_children_of(child)
            else:
                # maybe an envelope or eventually spot, ring, etc
                pass

        return stars_children



    def get_child_of(self, component, ind, kind=None):
        """
        Get the child (by index) of a component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        See also:
        * <phoebe.parameters.HierarchyParameter.get_parent_of>
        * <phoebe.parameters.HierarchyParameter.get_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_siblings_of>
        * <phoebe.parameters.HierarchyParameter.get_envelope_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_sibling_of>
        * <phoebe.parameters.HierarchyParameter.get_children_of>
        * <phoebe.parameters.HierarchyParameter.get_stars_of_children_of>

        Arguments
        ----------
        * `component` (string): the name of the component under which to search.
        * `ind` (int): the index of the child to return (starting at 0)
        * `kind` (string, optional): filter to match the kind of the component.

        Returns
        ---------
        * (string)
        """
        children = self.get_children_of(component, kind=kind)
        if children is None:
            return None
        else:
            return children[ind]


    def get_primary_or_secondary(self, component, return_ind=False):
        """
        Return whether a given component is the 'primary' or 'secondary'
        component in its parent orbit, according to the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
        <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        Arguments
        ----------
        * `component` (string): the name of the component.
        * `return_ind` (bool, optional, default=False): if `True`, this
            will return `0` instead of `'primary'` and `1` instead of
            `'secondary'`.

        Returns
        --------
        * (string or int): either 'primary'/'secondary' or 0/1 depending on the
            value of `return_ind`.
        """
        parent = self.get_parent_of(component)
        if parent is None:
            # then this is a single component, not in a binary
            return 'primary'

        children_of_parent = self.get_children_of(parent)

        ind = children_of_parent.index(component)

        if ind > 1:
            return None

        if return_ind:
            return ind + 1

        return ['primary', 'secondary'][ind]

    def get_kind_of(self, component):
        """
        Return the kind of a given component in the
        <phoebe.parameters.HierarchyParameter>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        Arguments
        ----------
        * `component` (string): the name of the component.

        Returns
        --------
        * (string): the kind (star, orbit, envelope, etc) of the component
        """
        structure, trace, item = self._get_structure_and_trace(component)
        item_kind, item_label = item.split(':')

        return item_kind


    def _compute_is_contact_binary(self, component):
        """
        """
        if 'envelope' not in self.get_value():
            return False

        if component not in self.get_components():
            # TODO: this can probably at least check to see if is itself
            # an envelope?
            return False

        kind = self.get_kind_of(component)

        if kind == 'envelope':
            return True
        elif kind=='orbit':
            return False
        else:
            return self.get_sibling_of(component, kind='envelope') is not None

    def is_contact_binary(self, component):
        """
        Return whether a given component is part of a contact binary,
        according to the <phoebe.parameters.HierarchyPararameter>.
        This is especially useful for <phoebe.parameters.ConstraintParameter>.

        This is done by checking whether any of the component's siblings is
        an envelope.  See <phoebe.parameters.HierarchyParameter.get_siblings_of>
        and <phoebe.parameters.HierarchyParameter.get_kind_of>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        Arguments
        ----------
        * `component` (string): the name of the component.

        Returns
        --------
        * (bool): whether the given component is part of a contact binary.
        """
        if component not in self._is_contact_binary.keys():
            self._update_cache()

        return self._is_contact_binary.get(component)

    def _compute_is_binary(self, component):
        """
        """
        if component not in self.get_components():
            # TODO: is this the best fallback?
            return True

        if len(self.get_stars())==1:
            return False

        parent = self.get_parent_of(component)
        if parent is None:
            return True
        else:
            return self.get_kind_of(self.get_parent_of(component))=='orbit'

    def is_binary(self, component):
        """
        Return whether a given component is part of a contact binary,
        according to the <phoebe.parameters.HierarchyPararameter>.
        This is especially useful for <phoebe.parameters.ConstraintParameter>.

        This is done by checking whether the component's parent is an orbit.
        See <phoebe.parameters.HierarchyParameter.get_parent_of> and
        <phoebe.parameters.HierarchyParameter.get_kind_of>.

        To access the HierarchyParameter from the Bundle, see
         <phoebe.frontend.bundle.Bundle.get_hierarchy>.

        Arguments
        ----------
        * `component` (string): the name of the component.

        Returns
        --------
        * (bool): whether the given component is part of a contact binary.
        """
        if component not in self._is_binary.keys():
            self._update_cache()

        return self._is_binary.get(component)

    def is_misaligned(self):
        """
        Return whether the system is misaligned.

        Returns
        ---------
        * (bool): whether the system is misaligned.
        """
        for component in self.get_stars():
            if self._bundle.get_value('pitch', component=component, context='component') != 0:
                return True
            if self._bundle.get_value('yaw', component=component, context='component') != 0:
                return True

        return False

    def is_time_dependent(self):
        """
        Return whether the system has any time-dependent parameters (other than
        phase-dependent).

        Returns
        ---------
        * (bool): whether the system is time-dependent
        """
        for orbit in self.get_orbits():
            if self._bundle.get_value('dpdt', component=orbit, context='component') != 0:
                return True
            if self._bundle.get_value('dperdt', component=orbit, context='component') != 0:
                return True
            if conf.devel and self._bundle.get_value('deccdt', component=orbit, context='component') != 0:
                return True

        return False


class ConstraintParameter(Parameter):
    """
    One side of a constraint (not an equality)

    qualifier: constrained parameter
    value: expression
    """
    def __init__(self, bundle, value, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        super(ConstraintParameter, self).__init__(qualifier=kwargs.pop('qualifier', None), value=value, description=kwargs.pop('description', 'constraint'), **kwargs)

        # usually its the bundle's job to attach param._bundle after the
        # creation of a parameter.  But in this case, having access to the
        # bundle is necessary in order to intialize and set the value
        self._bundle = bundle
        if isinstance(value, ConstraintParameter):
            default_unit = kwargs.get('default_unit', value.result.unit)
            value = value.get_value()

        else:
            default_unit = kwargs.get('default_unit', u.dimensionless_unscaled)

        self._vars = []
        self._var_params = None
        self._constraint_func = kwargs.get('constraint_func', None)
        self._constraint_kwargs = kwargs.get('constraint_kwargs', {})
        self._in_solar_units = kwargs.get('in_solar_units', False)
        self.set_value(value)
        self.set_default_unit(default_unit)
        self._dict_fields_other = ['description', 'value', 'default_unit', 'constraint_func', 'constraint_kwargs', 'in_solar_units']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    @property
    def is_visible(self):
        """
        Return whether the <phoebe.parameters.ConstraintParameter> is visible
        by checking on the visibility of the constrained parameter.

        See:
        * <phoebe.parameters.ConstraintParameter.constrained_parameter>
        * <phoebe.parameters.Parameter.is_visible>
        * <phoebe.parameters.Parameter.visible_if>

        Returns
        -------
        * (bool)
        """
        return self.constrained_parameter.is_visible

    @property
    def constraint_func(self):
        """
        Access the constraint_func tag of this
        <phoebe.parameters.ConstraintParameter>.

        Returns
        -------
        * (str) the constraint_func tag of this Parameter.
        """
        return self._constraint_func

    @property
    def constraint_kwargs(self):
        """
        Access the keyword arguments sent to the constraint.

        Returns
        ------
        * (dict)
        """
        return self._constraint_kwargs

    @property
    def in_solar_units(self):
        """
        """
        return self._in_solar_units

    @property
    def vars(self):
        """
        Return all the variables in this <phoebe.parameters.ConstraintParameter>
        as a <phoebe.parameters.ParameterSet>.

        Return
        ------
        * (<phoebe.parameters.ParameterSet>): ParameterSet of all variables in
            the expression for this constraint.
        """
        # cache _var_params
        if self._var_params is None:
            self._var_params = ParameterSet([var.get_parameter() for var in self._vars])
        return self._var_params

    def _get_var(self, param=None, **kwargs):
        if not isinstance(param, Parameter):
            if isinstance(param, str) and 'twig' not in kwargs.keys():
                kwargs['twig'] = param

            param = self.get_parameter(**kwargs)

        varids = [var.unique_label for var in self._vars]
        if param.uniqueid not in varids:
            raise KeyError("{} was not found in expression".format(param.uniquetwig))
        return self._vars[varids.index(param.uniqueid)]



    def _parse_expr(self, expr):

        # the expression currently has twigs between curly braces,
        # we need to extract these and turn each into a ConstraintVar
        # so that we actually store the uniqueid of the parameter,
        # but always display the /current/ uniquetwig in the expression

        vars_ = []
        lbls = re.findall(r'\{.[^{}]*\}', expr)

        for lbl in lbls:
            twig = lbl.replace('{', '').replace('}', '')
            #~ print "ConstraintParameter._parse_expr lbl: {}, twig: {}".format(lbl, twig)
            var = ConstraintVar(self._bundle, twig)

            # TODO: if var.is_param, we need to make it read-only and required by this constraint, etc

            vars_.append(var)
            expr = expr.replace(lbl, var.safe_label)

        if self.qualifier:
            #~ print "***", self._bundle.__repr__(), self.qualifier, self.component
            ps = self._bundle.filter(qualifier=self.qualifier, component=self.component, dataset=self.dataset, feature=self.feature, kind=self.kind, model=self.model, check_visible=False) - self._bundle.filter(context='constraint', check_visible=False)
            if len(ps) == 1:
                constrained_parameter = ps.get_parameter(check_visible=False, check_default=False)
            else:
                raise KeyError("could not find single match for {}".format({'qualifier': self.qualifier, 'component': self.component, 'dataset': self.dataset, 'feature': self.feature, 'model': self.model}))


            var = ConstraintVar(self._bundle, constrained_parameter.twig)

            vars_.append(var)

        return expr, vars_

    @property
    def constrained_parameter(self):
        """
        Access the <phoebe.parameters.Parameter> that is constrained (i.e.
        solved for) by this <phoebe.parameters.ConstraintParameter>.

        This is identical to
        <phoebe.parameters.ConstraintParameter.get_constrained_parameter>.

        See also:
        * <phoebe.parameters.ConstraintParameter.flip_for>
        * <phoebe.frontend.bundle.Bundle.flip_constraint>

        Returns
        -------
        * (<phoebe.parameters>parameter>)
        """
        # try:
        if True:
            return self.get_constrained_parameter()
        # except: # TODO exception type
            # return None

    def get_constrained_parameter(self):
        """
        Access the <phoebe.parameters.Parameter> that is constrained (i.e.
        solved for) by this <phoebe.parameters.ConstraintParameter>.

        This is identical to
        <phoebe.parameters.ConstraintParameter.constrained_parameter>.

        See also:
        * <phoebe.parameters.ConstraintParameter.flip_for>
        * <phoebe.frontend.bundle.Bundle.flip_constraint>

        Returns
        -------
        * (<phoebe.parameters>parameter>)
        """
        return self.get_parameter(qualifier=self.qualifier, component=self.component, dataset=self.dataset, check_visible=False)

    def get_parameter(self, twig=None, **kwargs):
        """
        Access one of the <phoebe.parameters.Parameter> object that is a variable
        in the <phoebe.parameters.ConstraintParameter>.

        **NOTE**: if the filtering results in more than one result, the first
        will be taken instead of raising an error.

        Arguments
        ----------
        * `twig` (string, optional): twig to use for filtering.  See
            <phoebe.parameters.ParameterSet.get_parameter>
        * `**kwargs`: other tags used for filtering.  See
            <phoebe.parameters.ParameterSet.get_parameter>

        Returns
        --------
        * (<phoebe.parameters.Parameter>)

        Raises
        -------
            * KeyError: if the filtering results in 0 matches
        """
        kwargs['twig'] = twig
        kwargs['check_default'] = False
        kwargs['check_visible'] = False
        ps = self.vars.filter(**kwargs)
        if len(ps)==1:
            return ps.get(check_visible=False, check_default=False)
        elif len(ps) > 1:
            # TODO: is this safe?  Some constraints may have a parameter listed
            # twice, so we can do this then, but maybe should check to make sure
            # all items have the same uniqueid?  Maybe check len(ps.uniqueids)?
            return ps.to_list()[0]
        else:
            raise KeyError("no result found")

    @property
    def default_unit(self):
        """
        Return the default unit for the <phoebe.parameters.ConstraintParameter>.

        This is identical to <phoebe.parameters.ConstraintParameter.get_default_unit>.

        See also:
        * <phoebe.parameters.ConstraintParameter.set_default_unit>

        Returns
        --------
        * (unit): the current default units.
        """
        return self._default_unit

    def get_default_unit(self):
        """
        Return the default unit for the <phoebe.parameters.ConstraintParameter>.

        This is identical to <phoebe.parameters.ConstraintParameter.default_unit>.

        See also:
        * <phoebe.parameters.ConstraintParameter.set_default_unit>

        Returns
        --------
        * (unit): the current default units.
        """
        return self.default_unit

    def set_default_unit(self, unit):
        """
        Set the default unit for the <phoebe.parameters.ConstraintParameter>.

        See also:
        * <phoebe.parameters.ConstraintParameter.get_default_unit>

        Arguments
        --------
        * `unit` (unit or valid string): the desired new units.  If the Parameter
            currently has default units, then the new units must be compatible
            with the current units

        Raises
        -------
        * Error: if the new and current units are incompatible.
        """
        # TODO: check to make sure can convert from current default unit (if exists)
        if isinstance(unit, unicode) or isinstance(unit, str):
            unit = u.Unit(str(unit))

        if not _is_unit(unit):
            raise TypeError("unit must be a Unit")

        if hasattr(self, '_default_unit') and self._default_unit is not None:
            # we won't use a try except here so that the error comes from astropy
            check_convert = self._default_unit.to(unit)


        self._default_unit = unit

    #@send_if_client   # TODO: this breaks
    def set_value(self, value, **kwargs):
        """
        Set the current value of the <phoebe.parameters.ConstraintParameter>.

        Arguments
        ----------
        * `value` (string): the new value of the Parameter.
        * `**kwargs`: IGNORED

        Raises
        ---------
        * ValueError: if `value` could not be converted to a string.
        * Error: if `value` could not be parsed into a valid constraint expression.
        """
        _orig_value = deepcopy(self.get_value())

        if self._bundle is None:
            raise ValueError("ConstraintParameters must be attached from the bundle, and cannot be standalone")
        value = str(value) # <-- in case unicode
        # if the user wants to see the expression, we'll replace all
        # var.safe_label with var.curly_label
        self._value, self._vars = self._parse_expr(value)
        # reset the cached version of the PS - will be recomputed on next request
        self._var_params = None
        #~ print "***", self.uniquetwig, self.uniqueid
        self._add_history(redo_func='set_value', redo_kwargs={'value': value, 'uniqueid': self.uniqueid}, undo_func='set_value', undo_kwargs={'value': _orig_value, 'uniqueid': self.uniqueid})

    def _update_bookkeeping(self):
        # do bookkeeping on parameters
        self._remove_bookkeeping()
        for var in self._vars:
            param = var.get_parameter()
            if param.qualifier == self.qualifier and param.component == self.component:
                # then this is the currently constrained parameter
                param._is_constraint = self.uniqueid
                if param.uniqueid in param._in_constraints:
                    param._in_constraints.remove(self.uniqueid)
            else:
                # then this is a constraining parameter
                if self.uniqueid not in param._in_constraints:
                    param._in_constraints.append(self.uniqueid)

    def _remove_bookkeeping(self):
        for var in self._vars:
            param = var.get_parameter()
            if param._is_constraint == self.uniqueid:
                param._is_constraint = None
            if self.uniqueid in param._in_constraints:
                param._in_constraints.remove(self.uniqueid)

    @property
    def expr(self):
        """
        Return the expression of the <phoebe.parameters.ConstraintParameter>.
        This is just a shortcut to
        <phoebe.parameters.ConstraintParameter.get_value>.

        Returns
        -------
        * (float)
        """
        return self.get_value()

    #@update_if_client  # TODO: this breaks
    def get_value(self):
        """
        Return the expression/value of the
        <phoebe.parameters.ConstraintParameter>.

        Returns
        -------
        * (float)
        """
        # for access to the sympy-safe expr, just use self._expr
        expr = self._value
        for var in self._vars:
            # update to current unique twig
            var.update_user_label()  # update curly label
            #~ print "***", expr, var.safe_label, var.curly_label
            expr = expr.replace(str(var.safe_label), str(var.curly_label))

        return expr

    def __repr__(self):
        expr = "{} ({})".format(self.expr, "solar units" if self.in_solar_units else "SI")
        if self.qualifier is not None:
            lhs = '{'+self.get_constrained_parameter().uniquetwig+'}'
            return "<ConstraintParameter: {} = {} => {}>".format(lhs, expr, self.result)
        else:
            return "<ConstraintParameter: {} => {}>".format(expr, self.result)

    def __str__(self):
        return "Constrains (qualifier): {}\nExpression in {} (value): {}\nCurrent Result (result): {}".format(self.qualifier, 'solar units' if self.in_solar_units else 'SI', self.expr, self.result)

    def __math__(self, other, symbol, mathfunc):
        #~ print "*** ConstraintParameter.__math__ other.type", type(other)
        if isinstance(other, ConstraintParameter):
            #~ print "*** ConstraintParameter.__math__", symbol, self.result, other.result
            return ConstraintParameter(self._bundle, "(%s) %s (%s)" % (self.expr, symbol, other.expr), default_unit=(getattr(self.result, mathfunc)(other.result).unit))
        elif isinstance(other, Parameter):
            return ConstraintParameter(self._bundle, "(%s) %s {%s}" % (self.expr, symbol, other.uniquetwig), default_unit=(getattr(self.result, mathfunc)(other.quantity).unit))
        elif isinstance(other, u.Quantity):
            #print "***", other, type(other), isinstance(other, ConstraintParameter)
            return ConstraintParameter(self._bundle, "(%s) %s %0.30f" % (self.expr, symbol, _value_for_constraint(other, self)), default_unit=(getattr(self.result, mathfunc)(other).unit))
        elif isinstance(other, float) or isinstance(other, int):
            if symbol in ['+', '-']:
                # assume same units as self (NOTE: NOT NECESSARILY SI) if addition or subtraction
                other = float(other)*self.default_unit
            else:
                # assume dimensionless
                other = float(other)*u.dimensionless_unscaled
            return ConstraintParameter(self._bundle, "(%s) %s %f" % (self.expr, symbol, _value_for_constraint(other, self)), default_unit=(getattr(self.result, mathfunc)(other).unit))
        elif isinstance(other, str):
            return ConstraintParameter(self._bundle, "(%s) %s %s" % (self.expr, symbol, other), default_unit=(getattr(self.result, mathfunc)(eval(other)).unit))
        elif _is_unit(other) and mathfunc=='__mul__':
            # here we'll fake the unit to become a quantity so that we still return a ConstraintParameter
            return self*(1*other)
        else:
            raise NotImplementedError("math using {} with type {} not supported".format(mathfunc, type(other)))

    def __rmath__(self, other, symbol, mathfunc):
        #~ print "*** ConstraintParameter.__rmath__ other.type", type(other)
        if isinstance(other, ConstraintParameter):
            #~ print "*** ConstraintParameter.__math__", symbol, self.result, other.result
            return ConstraintParameter(self._bundle, "(%s) %s (%s)" % (other.expr, symbol, self.expr), default_unit=(getattr(self.result, mathfunc)(other.result).unit))
        elif isinstance(other, Parameter):
            return ConstraintParameter(self._bundle, "{%s} %s (%s)" % (other.uniquetwig, symbol, self.expr), default_unit=(getattr(self.result, mathfunc)(other.quantity).unit))
        elif isinstance(other, u.Quantity):
            #~ print "*** rmath", other, type(other)
            return ConstraintParameter(self._bundle, "%0.30f %s (%s)" % (_value_for_constraint(other, self), symbol, self.expr), default_unit=(getattr(self.result, mathfunc)(other).unit))
        elif isinstance(other, float) or isinstance(other, int):
            if symbol in ['+', '-']:
                # assume same units as self if addition or subtraction
                other = float(other)*self.default_unit
            else:
                # assume dimensionless
                other = float(other)*u.dimensionless_unscaled
            return ConstraintParameter(self._bundle, "%f %s (%s)" % (_value_for_constraint(other, self), symbol, self.expr), default_unit=(getattr(self.result, mathfunc)(other).unit))
        elif isinstance(other, str):
            return ConstraintParameter(self._bundle, "%s %s (%s)" % (other, symbol, self.expr), default_unit=(getattr(self.result, mathfunc)(eval(other)).unit))
        elif _is_unit(other) and mathfunc=='__mul__':
            # here we'll fake the unit to become a quantity so that we still return a ConstraintParameter
            return self*(1*other)
        else:
            raise NotImplementedError("math using {} with type {} not supported".format(mathfunc, type(other)))

    def __add__(self, other):
        return self.__math__(other, '+', '__add__')

    def __radd__(self, other):
        return self.__rmath__(other, '+', '__radd__')

    def __sub__(self, other):
        return self.__math__(other, '-', '__sub__')

    def __rsub__(self, other):
        return self.__math__(other, '-', '__rsub__')

    def __mul__(self, other):
        return self.__math__(other, '*', '__mul__')

    def __rmul__(self, other):
        return self.__rmath__(other, '*', '__rmul__')

    def __div__(self, other):
        return self.__math__(other, '/', '__div__')

    def __rdiv__(self, other):
        return self.__rmath__(other, '/', '__rdiv__')

    def __pow__(self, other):
        return self.__math__(other, '**', '__pow__')

    @property
    def result(self):
        """
        Get the current value (as a quantity) of the result of the expression
        of this <phoebe.parameters.ConstraintParameter>.

        This is identical to <phoebe.parameters.ConstraintParameter.get_result>.

        Returns
        --------
        * (quantity): the current result of evaluating the constraint expression.
        """
        return self.get_result()

    def get_result(self, t=None):
        """
        Get the current value (as a quantity) of the result of the expression
        of this <phoebe.parameters.ConstraintParameter>.

        This is identical to <phoebe.parameters.ConstraintParameter.result>.

        Returns
        --------
        * (quantity): the current result of evaluating the constraint expression.
        """
        # TODO: optimize this:
        # almost half the time is being spent on self.get_value() of which most is spent on var.update_user_label
        # second culprit is converting everything to si
        # third culprit is the dictionary comprehensions

        # in theory, it would be nice to prepare this list at the module import
        # level, but that causes an infinite loop in the imports, so we'll
        # do a re-import here.  If this causes significant lag, it may be worth
        # trying to resolve the infinite loop.
        from phoebe.constraints import builtin
        _constraint_builtin_funcs = [f for f in dir(builtin) if isinstance(getattr(builtin, f), types.FunctionType)]
        _constraint_builtin_funcs += ['sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan', 'sqrt', 'log10']

        def eq_needs_builtin(eq):
            for func in _constraint_builtin_funcs:
                if "{}(".format(func) in eq:
                    #print "*** eq_needs_builtin", func
                    return True
            return False

        def get_values(vars, safe_label=True):
            # use np.float64 so that dividing by zero will result in a
            # np.inf
            def _single_value(quantity):
                if self.in_solar_units:
                    return np.float64(u.to_solar(quantity).value)
                else:
                    return np.float64(quantity.si.value)

            return {var.safe_label if safe_label else var.user_label: _single_value(var.get_quantity(t=t)) if var.get_parameter()!=self.constrained_parameter else _single_value(var.get_quantity()) for var in vars}

        eq = self.get_value()

        values = get_values(self._vars, safe_label=_use_sympy or not eq_needs_builtin(eq))

        if _use_sympy and not eq_needs_builtin(eq):
            values['I'] = 1 # CHEATING MAGIC
            # just to be safe, let's reinitialize the sympy vars
            for v in self._vars:
                #~ print "creating sympy var: ", v.safe_label
                sympy.var(str(v.safe_label), positive=True)

            # print "***", self._value, values
            eq = sympy.N(self._value, 30)
            # print "***", self._value, values, eq.subs(values), eq.subs(values).evalf(15)
            value = float(eq.subs(values).evalf(15))
        else:
            # order here matters - self.get_value() will update the user_labels
            # to be the current unique twigs
            #print "***", eq, values


            if eq_needs_builtin(eq):
                # the else (which works for np arrays) does not work for the built-in funcs
                # this means that we can't currently support the built-in funcs WITH arrays

                # cannot do from builtin import *
                for func in _constraint_builtin_funcs:
                    # I should be shot for doing this...
                    # in order for eval to work, the builtin functions need
                    # to be imported at the top-level, but I don't really want
                    # to do from builtin import * (and even if I did, python
                    # yells at me for doing that), so instead we'll add them
                    # to the locals dictionary.
                    locals()[func] = getattr(builtin, func)

                try:
                    value = float(eval(eq.format(**values)))
                except:
                    value = np.nan


            else:
                # the following works for np arrays

                # if any of the arrays are empty (except the one we're filling)
                # then we want to return an empty array as well (the math would fail)
                arrays_filled = True
                for var in self._vars:
                    var_value = var.get_value()
                    #print "***", self.twig, self.constrained_parameter.twig, var.user_label, var_value, isinstance(var_value, np.ndarray), var.unique_label != self.constrained_parameter.uniqueid
                    # if self.qualifier is None then this isn't attached to solve anything yet, so we don't need to worry about checking to see if the var is the constrained parameter
                    if isinstance(var_value, np.ndarray) and len(var_value)==0 and (var.unique_label != self.constrained_parameter.uniqueid or self.qualifier is None):
                        #print "*** found empty array", self.constrainted_parameter.twig, var.safe_label, var_value
                        arrays_filled = False
                        #break  # out of the for loop

                if arrays_filled:
                    #print "*** else else", self._value, values
                    #print "***", _use_sympy, self._value, value
                    value = eval(self._value, values)
                else:
                    #print "*** EMPTY ARRAY FROM CONSTRAINT"
                    value = np.array([])

        #~ return value

        # let's assume the math was correct to give SI and we want units stored in self.default_units

        if self.default_unit is not None:
            if self.in_solar_units:
                convert_scale = u.to_solar(self.default_unit)
            else:
                convert_scale = self.default_unit.to_system(u.si)[0].scale
            #value = float(value/convert_scale) * self.default_unit
            value = value/convert_scale * self.default_unit


        return value

    def flip_for(self, twig=None, expression=None, **kwargs):
        """
        Flip the constraint expression to solve for for any of the parameters
        in the expression.

        The filtering (with `twig` and `**kwargs`) must find a single match
        among the Parameters in the expression.  See
        <phoebe.parameters.ConstraintParameter.vars> and
        <phoebe.parameters.ConstraintParameter.get_parameter>.

        See also:
        * <phoebe.frontend.bundle.Bundle.flip_constraint>

        Arguments
        ----------
        * `twig` (string, optional): the twig of the Parameter to constraint (solve_for).
        * `expression` (string, optional): provide the new expression.  If not
            provided, the expression will be pulled from the constraint func
            if possible, or solved for analytically if sympy is installed.
        * `**kwargs`: tags to be used for filtering for the newly constrained
            Parameter.
        """

        _orig_expression = self.get_value()

        # try to get the parameter from the bundle
        kwargs['twig'] = twig
        newly_constrained_var = self._get_var(**kwargs)
        newly_constrained_param = self.get_parameter(**kwargs)

        check_kwargs = {k:v for k,v in newly_constrained_param.meta.items() if k not in ['context', 'twig', 'uniquetwig']}
        check_kwargs['context'] = 'constraint'
        if len(self._bundle.filter(**check_kwargs)):
            raise ValueError("'{}' is already constrained".format(newly_constrained_param.twig))

        currently_constrained_var = self._get_var(qualifier=self.qualifier, component=self.component)
        currently_constrained_param = currently_constrained_var.get_parameter() # or self.constrained_parameter

        # cannot be at the top, or will cause circular import
        from . import constraint
        if self.constraint_func is not None and hasattr(constraint, self.constraint_func):
            # then let's see if the method is capable of resolving for use
            # try:
            if True:
                # TODO: this is not nearly general enough, each method takes different arguments
                # and getting solve_for as newly_constrained_param.qualifier

                lhs, rhs, constraint_kwargs = getattr(constraint, self.constraint_func)(self._bundle, solve_for=newly_constrained_param, **self.constraint_kwargs)
            # except NotImplementedError:
            #     pass
            # else:
                # TODO: this needs to be smarter and match to self._get_var().user_label instead of the current uniquetwig

                expression = rhs._value # safe expression
                #~ print "*** flip by recalling method success!", expression

        # print "***", lhs._value, rhs._value

        if expression is not None:
            expression = expression

        elif _use_sympy:


            eq_safe = "({}) - {}".format(self._value, currently_constrained_var.safe_label)

            #~ print "*** solving {} for {}".format(eq_safe, newly_constrained_var.safe_label)

            expression = sympy.solve(eq_safe, newly_constrained_var.safe_label)[0]

            #~ print "*** solution: {}".format(expression)

        else:
            # TODO: ability for built-in constraints to flip themselves
            # we could access self.kind and re-call that with a new solve_for option?
            raise ValueError("must either have sympy installed or provide a new expression")

        self._qualifier = newly_constrained_param.qualifier
        self._component = newly_constrained_param.component
        self._kind = newly_constrained_param.kind

        self._value = str(expression)
        # reset the default_unit so that set_default_unit doesn't complain
        # about incompatible units
        self._default_unit = None
        self.set_default_unit(newly_constrained_param.default_unit)

        self._update_bookkeeping()

        self._add_history(redo_func='flip_constraint', redo_kwargs={'expression': expression, 'uniqueid': newly_constrained_param.uniqueid}, undo_func='flip_constraint', undo_kwargs={'expression': _orig_expression, 'uniqueid': currently_constrained_param.uniqueid})


class HistoryParameter(Parameter):
    def __init__(self, bundle, redo_func, redo_kwargs, undo_func, undo_kwargs, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>

        This Parameter should never be created manually, but instead handled
        by the <phoebe.frontend.bundle.Bundle>.

        Arguments
        -----------
        * `bundle`
        * `redo_func`
        * `redo_kwargs`
        * `undo_func`
        * `undo_kwargs`
        """
        dump = kwargs.pop('qualifier', None)
        kwargs['context'] = 'history'
        super(HistoryParameter, self).__init__(qualifier='history', **kwargs)

        # usually its the bundle's job to attach param._bundle after the
        # creation of a parameter.  But in this case, having access to the
        # bundle is necessary in order to check if function names are valid
        # methods of the bundle
        self._bundle = bundle

        # if a function itself is passed instead of the string name, convert
        if hasattr(redo_func, '__call__'):
            redo_func = redo_func.__name__
        if hasattr(undo_func, '__call__'):
            undo_func = undo_func.__name__

        # check to make sure the funcs are valid methods of the bundle
        if not hasattr(self._bundle, redo_func):
            raise ValueError("bundle does not have '{}' method".format(redo_func))
        if not hasattr(self._bundle, undo_func):
            raise ValueError("bundle does not have '{}' method".format(undo_func))

        self._redo_func = redo_func
        self._redo_kwargs = redo_kwargs
        self._undo_func = undo_func
        self._undo_kwargs = undo_kwargs

        self._affected_params = []


        # TODO: how can we hold other parameters affect (ie. if the user calls set_value('incl', 80) and there is a constraint on asini that changes a... how do we log that here)

        self._dict_fields_other = ['redo_func', 'redo_kwargs', 'undo_func', 'undo_kwargs']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    def __repr__(self):
        """
        """
        return "<HistoryParameter: {} | keys: {}>".format(self.history, ', '.join(self._dict_fields_other))

    def __str__(self):
        """
        """
        # TODO: fill in str representation
        return "{}\nredo: {}\nundo: {}".format(self.history, self.redo_str, self.undo_str)

    def to_string_short(self):
        """
        An abbreviated string representation of the <phoebe.parameters.HistoryParameter>.

        See also:
        * <phoebe.parameters.Parameter.to_string>

        Returns
        ----------
        * (string)
        """
        # this is what will be printed when in a PS (ie bundle.get_history())
        return "redo: {}, undo: {}".format(self.redo_str, self.undo_str)

    @property
    def undo_str(self):
        """
        """
        undo_kwargs = self.undo_kwargs
        if undo_kwargs is not None:
            return "{}({})".format(self.undo_func, ", ".join("{}={}".format(k,v) for k,v in undo_kwargs.items()))
        else:
            return "no longer undoable"

    @property
    def redo_str(self):
        """
        """
        redo_kwargs = self.redo_kwargs
        if redo_kwargs is not None:
            return "{}({})".format(self.redo_func, ", ".join("{}={}".format(k,v) for k,v in redo_kwargs.items()))
        else:
            return "no longer redoable"

    @property
    def redo_func(self):
        """
        """
        return self._redo_func

    @property
    def redo_kwargs(self):
        """
        """
        _redo_kwargs = deepcopy(self._redo_kwargs)
        if 'uniqueid' in _redo_kwargs.keys():
            uniqueid = _redo_kwargs.pop('uniqueid')
            try:
                _redo_kwargs['twig'] = self._bundle.get_parameter(uniqueid=uniqueid).uniquetwig
            except ValueError:
                # then the uniqueid is no longer available and we can no longer undo this item
                return None
        return _redo_kwargs

    @property
    def undo_func(self):
        """
        """
        return self._undo_func

    @property
    def undo_kwargs(self):
        """
        """
        _undo_kwargs = deepcopy(self._undo_kwargs)
        if 'uniqueid' in _undo_kwargs.keys():
            uniqueid = _undo_kwargs.pop('uniqueid')
            try:
                _undo_kwargs['twig'] = self._bundle.get_parameter(uniqueid=uniqueid).uniquetwig
            except ValueError:
                # then the uniqeuid is no longer available and we can no longer undo this item
                return None
        return _undo_kwargs

    @property
    def affected_params(self):
        """
        """
        return self.get_affected_params

    def get_affected_params(self, return_twigs=False):
        """
        """
        raise NotImplementedError
        if return_twigs:
            return [self._bundle.get_parameter(uniqueid=uniqueid).uniquetwig]
        else:
            return [self._bundle.get_parameter(uniqueid=uniqueid)]

    def redo(self):
        """
        """
        if self.redo_kwargs is None:
            # TODO: logger message explaining no longer redoable
            return
        # TODO: logger message
        return getattr(self._bundle, self._redo_func)(**self._redo_kwargs)

    def undo(self):
        """
        """
        if self.undo_kwargs is None:
            # TODO: logger message explaining no longer undoable
            return
        # TODO: logger message
        return getattr(self._bundle, self._undo_func)(**self._undo_kwargs)


class JobParameter(Parameter):
    """
    Parameter that tracks a submitted job (detached run_compute or run_fitting)
    """
    def __init__(self, b, location, status_method, retrieve_method, server_status=None, **kwargs):
        """
        see <phoebe.parameters.Parameter.__init__>
        """
        _qualifier = kwargs.pop('qualifier', None)
        super(JobParameter, self).__init__(qualifier='detached_job', **kwargs)

        self._bundle = b
        self._server_status = server_status
        self._location = location
        self._status_method = status_method
        self._retrieve_method = retrieve_method
        self._value = 'unknown'
        #self._randstr = randstr

        # TODO: may need to be more clever once remote servers are supported
        self._script_fname = os.path.join(location, '_{}.py'.format(self.uniqueid))
        self._results_fname = os.path.join(location, '_{}.out'.format(self.uniqueid))

        # TODO: add a description?

        self._dict_fields_other = ['description', 'value', 'server_status', 'location', 'status_method', 'retrieve_method', 'uniqueid']
        self._dict_fields = _meta_fields_all + self._dict_fields_other

    def __str__(self):
        """
        """
        # TODO: implement a nice(r) string representation
        return "qualifier: {}\nstatus: {}".format(self.qualifier, self.status)

    #@update_if_client # get_status will make API call if JobParam points to a server
    def get_value(self):
        """
        JobParameter doesn't really have a value, but for the sake of Parameter
        representations, we'll provide the current status.

        Also see:
            * :meth:`location`
            * :meth:`status_method`
            * :meth:`retrieve_method`
            * :meth:`status`
            * :meth:`attach`
        """
        return self.status

    def set_value(self, *args, **kwargs):
        """
        <phoebe.parameters.JobParameter> is read-only.  Calling set_value
        will raise an Error.

        Raises
        --------
        * NotImplementedError: because this never will be
        """

        raise NotImplementedError("JobParameter is a read-only parameter.  Call status or attach()")

    @property
    def server_status(self):
        """
        """
        return self._server_status

    @property
    def location(self):
        """
        """
        return self._location

    @property
    def status_method(self):
        """
        """
        return self._status_method

    @property
    def retrieve_method(self):
        """
        """
        return self._retrieve_method

    @property
    def status(self):
        """
        :raises NotImplementedError: if status isn't implemented for the given :meth:`status_method
        """
        return self.get_status()

    def get_status(self):
        """
        [NOT IMPLEMENTED]
        """
        if self._value == 'loaded':
            status = 'loaded'

        elif not _is_server and self._bundle is not None and self._server_status is not None:
            if not _can_requests:
                raise ImportError("requests module required for external jobs")

            if self._value in ['complete']:
                # then we have no need to bother checking again
                status = self._value
            else:
                url = self._server_status
                logger.info("checking job status on server from {}".format(url))
                # "{}/{}/parameters/{}".format(server, bundleid, self.uniqueid)
                r = requests.get(url, timeout=5)
                try:
                    rjson = r.json()
                except ValueError:
                    # TODO: better exception here - perhaps look for the status code from the response?
                    status = self._value
                else:
                    status = rjson['data']['attributes']['value']

        else:

            if self.status_method == 'exists':
                output_exists = os.path.isfile("_{}.out".format(self.uniqueid))
                if output_exists:
                    status = 'complete'
                else:
                    status = 'unknown'
            else:
                raise NotImplementedError

        # here we'll set the value to be the latest CHECKED status for the sake
        # of exporting to JSON and updating the status for clients.  get_value
        # will still call status so that it will return the CURRENT value.
        self._value = status
        return status

    def _retrieve_results(self):
        """
        [NOT IMPLEMENTED]
        """
        # now the file with the model should be retrievable from self._result_fname
        result_ps = ParameterSet.open(self._results_fname)
        return result_ps

    def attach(self, sleep=5, cleanup=True):
        """

        :parameter int sleep: number of seconds to sleep between status checks
        :parameter bool cleanup: whether to delete this parameter and any temporary
            files once the results are loaded (default: True)
        :raises ValueError: if not attached to a bundle
        :raises NotImplementedError: because it isn't
        """
        if not self._bundle:
            raise ValueError("can only attach a job if attached to a bundle")

        #if self._value == 'loaded':
        #    raise ValueError("results have already been loaded")


        while self.get_status() not in ['complete', 'loaded']:
            # TODO: any way we can not make 2 calls to self.status here?
            logger.info("current status: {}".format(self.get_status()))
            time.sleep(sleep)

        if self._server_status is not None and not _is_server:
            if not _can_requests:
                raise ImportError("requests module required for external jobs")
            # then we are no longer attached as a client to this bundle on
            # the server, so we need to just pull the results manually
            url = self._server_status
            logger.info("pulling job results from server from {}".format(url))
            # "{}/{}/parameters/{}".format(server, bundleid, self.uniqueid)
            r = requests.get(url, timeout=5)
            rjson = r.json()

            # status should already be complete because of while loop above,
            # but could always check the following:
            # rjson['value']['attributes']['value'] == 'complete'

            # TODO: server needs to sideload results once complete
            newparams = rjson['included']
            self._bundle._attach_param_from_server(newparams)


        else:

            result_ps = self._retrieve_results()

            # now we need to attach result_ps to self._bundle
            # TODO: is creating metawargs here necessary?  Shouldn't the params already be tagged?
            metawargs = {'compute': result_ps.compute, 'model': result_ps.model, 'context': 'model'}
            self._bundle._attach_params(result_ps, **metawargs)

            if cleanup:
                os.remove(self._script_fname)
                os.remove(self._results_fname)

        self._value = 'loaded'

        # TODO: add history?

        return self._bundle.get_model(self.model)
