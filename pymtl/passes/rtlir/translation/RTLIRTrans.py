#=========================================================================
# RTLIRTrans.py
#=========================================================================
# A framework for translating a PyMTL RTLComponent into arbitrary backend
# by calling user-defined translation callbacks.
#
# Author : Peitian Pan
# Date   : March 15, 2019

import inspect

from pymtl.passes.utility import get_string

from behavioral import BehavioralTrans
from structural import StructuralTrans

def mk_RTLIRTrans( _StructuralTrans, _BehavioralTrans ):
  """
     Construct an RTLIRTranslator from the two given translators. This
     allows incremental development and testing.
  """

  class _RTLIRTrans( _StructuralTrans, _BehavioralTrans ):

    # Override
    def __init__( s, top ):

      super( _RTLIRTrans, s ).__init__( top )

    # Override
    def translate( s ):

      super( _RTLIRTrans, s ).translate()

      s.hierarchy.component_srcs = []

      s.translate_components( s.top )

      s.hierarchy.component_src = s.__class__.rtlir_tr_components(
        s.hierarchy.component_srcs
      )

      s.hierarchy.src = s.__class__.rtlir_tr_src_layout(
        s.hierarchy.value_types, s.hierarchy.component_src
      )

    #-----------------------------------------------------------------------
    # translate_components
    #-----------------------------------------------------------------------

    def translate_components( s, m ):

      for child in m.get_child_components():
        s.translate_components( child )

      s.component[m].component_name =\
          s.__class__.rtlir_tr_component_name(
            s.gen_component_name( m )
          )

      s.hierarchy.component_srcs.append(
        s.__class__.rtlir_tr_component( s.component[m] )
      )

    #-----------------------------------------------------------------------
    # get_model_parameters
    #-----------------------------------------------------------------------

    def get_component_parameters( s, m ):

      ret = {}

      kwargs = m._dsl.kwargs.copy()
      if "elaborate" in m._dsl.param_dict:
        kwargs.update(
          { x: y\
            for x, y in m._dsl.param_dict[ "elaborate" ].iteritems() if x 
        } )

      ret[ '' ] = m._dsl.args

      ret.update( kwargs )

      return ret

    #-----------------------------------------------------------------------
    # gen_module_name
    #-----------------------------------------------------------------------

    def gen_component_name( s, m ):

      ret = m.__class__.__name__

      param = s.get_component_parameters( m )

      argspec = inspect.getargspec( getattr( m, 'construct' ) )

      # Add const args to module name
      for idx, arg_name in enumerate( argspec.args[1:] ):
        arg_value = param[ '' ][idx]
        ret += '__' + arg_name + '_' + get_string(arg_value)

      # Add varargs to module name
      if len( param[''] ) > len( argspec.args[1:] ):
        ret += '__' + argspec.varargs
      
      for arg_value in param[''][ len(argspec.args[1:]): ]:
        ret += '___' + get_string(arg_value)

      # Add kwargs to module name
      for arg_name, arg_value in param.iteritems():
        if arg_name == '': continue
        ret += '__' + arg_name + '_' + get_string(arg_value)

      return ret

    #-----------------------------------------------------------------------
    # Methods to be implemented by the backend translator
    #-----------------------------------------------------------------------

    @staticmethod
    def rtlir_tr_src_layout( value_types, component_src ):
      raise NotImplementedError()

    @staticmethod
    def rtlir_tr_components( components ):
      raise NotImplementedError()

    @staticmethod
    def rtlir_tr_component( component_nspace ):
      raise NotImplementedError()

    @staticmethod
    def rtlir_tr_component_name( component_name ):
      raise NotImplementedError()

    @staticmethod
    def rtlir_tr_signal_name( signal_name ):
      raise NotImplementedError()

  return _RTLIRTrans

RTLIRTrans = mk_RTLIRTrans( StructuralTrans, BehavioralTrans )
