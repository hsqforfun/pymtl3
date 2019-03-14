#=========================================================================
# translate.py
#=========================================================================
# A framework for translating a PyMTL RTLComponent into arbitrary backend
# by calling user-defined translation callbacks.
#
# Author : Peitian Pan
# Date   : March 11, 2019

from pymtl import *
from pymtl.passes.rtlir import RTLIRMetadataGenPass
from pymtl.passes.utility import collect_objs

from ..RTLIRType import *
from ..RTLIRMetadataGenPass import RTLIRMetadataGenPass
from utility     import *
from ConstraintGenPass import ConstraintGenPass

class RTLIRTranslator( object ):

  def __init__( s, callbacks ):
    s.callbacks  = callbacks
    s.translated = []
    s.src = ""

  def translate( s, m ):
    """Translate PyMTL RTLComponent `m` into a specific backend
    representation by calling the translation callbacks."""

    m.apply( RTLIRMetadataGenPass() )
    s.upblks   = m._pass_rtlir_metadata_gen.rtlir_upblks
    s.type_env = m._pass_rtlir_metadata_gen.rtlir_type_env
    s.freevars = m._pass_rtlir_metadata_gen.rtlir_freevars
    s.tmpvars  = m._pass_rtlir_metadata_gen.rtlir_tmpvars

    s.connections = generate_connections( m )

    s.translate_custom_types( m )

    s.translate_hierarchy( m )

    m.apply( ConstraintGenPass() )
    s.constraint_src = m._pass_constraint_gen.constraint_src

#-------------------------------------------------------------------------
# translate_custom_types
#-------------------------------------------------------------------------

  def translate_custom_types( s, m ):

    s.translate_struct_def( m )

#-------------------------------------------------------------------------
# translate_struct_def
#-------------------------------------------------------------------------

  def translate_struct_def( s, m ):

    # Generate type environment of structs

    type_env = []

    for obj, Type in s.type_env.iteritems():
      if isinstance( Type, Struct ):
        type_env.append( (obj, Type) )

    # Deduplicate structs

    for idx, (obj, Type) in enumerate(type_env):
      for _idx, (_obj, _Type) in enumerate(type_env[idx+1:]):
        if is_obj_eq( obj, _obj ):
          del type_env[ _idx ]

    # Generate struct dependency DAG
    
    dag = {}
    in_degree = {}

    for obj, Type in type_env:
      if not (obj, Type) in dag:
        dag[ (obj, Type) ] = []
      if not (obj, Type) in in_degree:
        in_degree[ (obj, Type) ] = 0

      _env = Type.type_env
      for _obj, _Type in _env.iteritems():
        if isinstance( _Type, Struct ):
          if not (_obj, _Type) in dag:
            dag[ (_obj, _Type) ] = []
          if not (obj, Type) in in_degree:
            in_degree[ (obj, Type) ] = 0

          dag[ (_obj, _Type) ].append( (obj, Type) )
          in_degree[ (obj, Type) ] += 1

    # Topo sort on dag

    q = []
    visited = {}
    ordered_structs = []

    for vertex, ind in in_degree.iteritems():
      if ind == 0:
        q.append( vertex )

    while q:
      vertex = q.pop()

      ordered_structs.append(
        ( vertex[0]._dsl.Type.__class__.__name__, vertex[1] )
      )

      visited[ vertex ] = True

      for _vertex in dag[ vertex ]:
        in_degree[ _vertex ] -= 1
        if in_degree[ _vertex ] == 0:
          q.append( _vertex )
    
    assert len( visited.keys() ) == len( dag.keys() ),\
      "Circular dependency detected in struct definition!"

    s.src += s.callbacks.rtlir_tr_struct_def( ordered_structs )

#-------------------------------------------------------------------------
# translate_hierarchy
#-------------------------------------------------------------------------

  def translate_hierarchy( s, m ):

    # De-duplicate modules by the RTLIR type of the components
    for component in s.translated:
      if s.type_env[m] == s.type_env[component]:
        return ''

    s.translated.append( m )

    for child in sorted( m.get_child_components(), key=repr ):
      s.translate_hierarchy( child )

    s.translate_component( m )

#-------------------------------------------------------------------------
# translate_component
#-------------------------------------------------------------------------

  def translate_component( s, m ):
    """Translate component `m` to some backend definition."""

    strs = {}

    strs['interface_src'] = s.translate_component_interface_decl( m )

    strs['wire_decl_src'] = s.translate_component_wire_decl( m )

    strs['subcomponent_inst_src'] = s.translate_component_inst( m )

    strs['upblk_decl_src'] = s.translate_upblk_decl( m )

    strs['connection_decl_src'] = s.translate_connection_decl( m )

    strs['freevar_decl_src'] = s.translate_freevar_decl( m )

    strs['tmpvar_decl_src'] = s.translate_tmpvar_decl( m )

    s.src += s.callbacks.rtlir_tr_component_decl( strs, s.type_env[m] )

#-------------------------------------------------------------------------
# translate_component_interface_decl
#-------------------------------------------------------------------------

  def translate_component_interface_decl( s, m ):

    interface = collect_objs( m, InVPort ) + collect_objs( m, OutVPort )

    return s.callbacks.rtlir_tr_component_interface_decl(
      map( lambda x: (x[0], s.type_env[freeze(x[1])]), interface )
    )

#-------------------------------------------------------------------------
# translate_component_wire_decl
#-------------------------------------------------------------------------

  def translate_component_wire_decl( s, m ):

    wires = collect_objs( m, Wire )

    return s.callbacks.rtlir_tr_component_wire_decl(
      map( lambda x: (x[0], s.type_env[freeze(x[1])]), wires )
    )

#-------------------------------------------------------------------------
# translate_component_inst
#-------------------------------------------------------------------------

  def translate_component_inst( s, m ):

    subcomponents = m.get_child_components()

    return s.callbacks.rtlir_tr_component_inst(
      map( lambda x: (x._dsl.my_name, s.type_env[x]), subcomponents )
    )

#-------------------------------------------------------------------------
# translate_upblk_decl
#-------------------------------------------------------------------------

  def translate_upblk_decl( s, m ):

    upblks = []

    for upblk in m.get_update_blocks():
      upblks.append( ( upblk, s.upblks[ upblk ] ) )

    return s.callbacks.rtlir_tr_upblk_decl( upblks )

#-------------------------------------------------------------------------
# translate_connection_decl
#-------------------------------------------------------------------------

  def translate_connection_decl( s, m ):

    _connections = { 'self_child' : set(), 'child_self' : set() }

    for prefix in [ 'self_self', 'child_child' ]:
      _connections[prefix] = s.connections[prefix][m]

    for writer, reader in s.connections['self_child'][m]:
      if writer.get_host_component() is m:
        _connections['child_self'].add( (writer, reader) )
      else:
        _connections['self_child'].add( (writer, reader) )

    return s.callbacks.rtlir_tr_connections( _connections )

#-------------------------------------------------------------------------
# translate_freevar_decl
#-------------------------------------------------------------------------

  def translate_freevar_decl( s, m ):

    freevars = s.freevars.iteritems()

    return s.callbacks.rtlir_tr_freevar_decl( freevars )

#-------------------------------------------------------------------------
# translate_tmpvar_decl
#-------------------------------------------------------------------------

  def translate_tmpvar_decl( s, m ):

    tmpvars = s.tmpvars.iteritems()

    return s.callbacks.rtlir_tr_tmpvar_decl( tmpvars )
