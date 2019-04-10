#=========================================================================
# StructuralRTLIRGenL3Pass.py
#=========================================================================
# This pass generates the structural RTLIR of a given component.
#
# Author : Peitian Pan
# Date   : Apr 3, 2019

from StructuralRTLIRGenL2Pass import StructuralRTLIRGenL2Pass
from ..RTLIRType import *
from StructuralRTLIRSignalExpr import CurComp

class StructuralRTLIRGenL3Pass( StructuralRTLIRGenL2Pass ):

  def __call__( s, top ):

    super( StructuralRTLIRGenL3Pass, s ).__call__( top )

    s.gen_interfaces( top )

  #-----------------------------------------------------------------------
  # collect_all_interfaces
  #-----------------------------------------------------------------------

  def collect_ifcs( s, m_rtype ):

    return m_rtype.get_ifc_views_packed()

  #-----------------------------------------------------------------------
  # gen_interfaces
  #-----------------------------------------------------------------------
  # Figure out the interfaces that each interface view belongs to.

  def gen_interfaces( s, top ):

    ifcs = []
    view2ifc = {}
    top_views = s.collect_ifcs( top._pass_structural_rtlir_gen.rtlir_type )

    for idx, ( view_name, rtype ) in enumerate( top_views ):

      view_rtype = rtype.get_sub_type() if isinstance(rtype, Array)\
              else rtype

      view2ifc[ view_name ] =\
          ( Interface( '_TmpIfc'+str(idx), [ view_rtype ] ), view_rtype )

    # Group all the views that do not conflict with each other into the
    # same interface

    for idx, ( view_name, rtype ) in enumerate( top_views[:-1] ):

      view_rtype = rtype.get_sub_type() if isinstance(rtype, Array)\
              else rtype

      for _view_name, _rtype in top_views[ idx+1: ]:

        _view_rtype = _rtype.get_sub_type() if isinstance(_rtype, Array)\
                 else _rtype

        if view2ifc[ view_name ][0].can_add_view( _view_rtype ):

          view2ifc[ _view_name ] =\
            ( view2ifc[ view_name ][0], _view_rtype )

          view2ifc[ view_name ][0].add_view( _view_rtype )

    for view_name, ( ifc_rtype, view_rtype ) in view2ifc.iteritems():

      view_rtype._set_interface( ifc_rtype )

      if not ifc_rtype in ifcs:

        ifc_rtype._set_name( 'Interface'+str(len( ifcs )) )
        ifcs.append( ifc_rtype )

    top._pass_structural_rtlir_gen.ifcs = ifcs

  #-----------------------------------------------------------------------
  # contains
  #-----------------------------------------------------------------------
  # At L3 not all signals have direct correspondance to `s.connect`
  # statements because of interfaces. Therefore we need to check if `obj`
  # is some parent of `signal`.

  # Override
  def contains( s, obj, signal ):

    if super(StructuralRTLIRGenL3Pass, s).contains(obj, signal): return True

    if not isinstance( signal, CurComp ):

      return s.contains( obj, signal.get_base() )

    return False
