#=========================================================================
# StructuralDeclTransL1.py
#=========================================================================
# Translate all ports to their declaration.
#
# Author : Peitian Pan
# Date   : March 15, 2019

from pymtl                    import *
from pymtl.passes.utility     import collect_objs
from pymtl.passes.rtlir.RTLIRType import *

from ..utility                import *
from BaseStructuralTrans import BaseStructuralTrans

class StructuralDeclTransL1( BaseStructuralTrans ):

  # Override
  def __init__( s, top ):

    super( StructuralDeclTransL1, s ).__init__( top )

    s.structural.ports = {}
    s.gen_signal_decl_trans_l1_metadata( top )

  # Override
  def translate( s ):

    super( StructuralDeclTransL1, s ).translate()

    s.structural.port_decls = {}
    s.translate_port_decls( s.top )
 
  #-----------------------------------------------------------------------
  # gen_signal_decl_trans_l1_metadata
  #-----------------------------------------------------------------------

  def gen_signal_decl_trans_l1_metadata( s, m ):

    s.structural.ports[m] = collect_objs( m, InVPort ) + \
                            collect_objs( m, OutVPort )

    for child in m.get_child_components():
      s.gen_signal_decl_trans_l1_metadata( child )

  #-----------------------------------------------------------------------
  # translate_port_decls
  #-----------------------------------------------------------------------

  def translate_port_decls( s, m ):

    port_decls = []
    
    for name, port in s.structural.ports[m]:

      if   isinstance( port, InVPort ):  direction = 'input'
      elif isinstance( port, OutVPort ): direction = 'output'
      else:                              assert False

      port_decls.append( s.__class__.rtlir_tr_port_decl(
        direction, name, s.dtype_tr_get_member_type( port )
      ) )

    s.component[m].port_decls = s.__class__.rtlir_tr_port_decls( port_decls )

  #-----------------------------------------------------------------------
  # Methods to be implemented by the backend translator
  #-----------------------------------------------------------------------

  @staticmethod
  def rtlir_tr_port_decls( port_decls ):
    raise NotImplementedError()

  @staticmethod
  def rtlir_tr_port_decl( direction, name, Type ):
    raise NotImplementedError()
