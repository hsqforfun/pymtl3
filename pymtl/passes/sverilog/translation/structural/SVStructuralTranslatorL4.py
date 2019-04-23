#=========================================================================
# SVStructuralTranslatorL4.py
#=========================================================================

from pymtl.passes.utility import make_indent
from pymtl.passes.rtlir.translation.structural.StructuralTranslatorL4\
    import StructuralTranslatorL4
from pymtl.passes.rtlir.RTLIRType import *

from SVStructuralTranslatorL3 import SVStructuralTranslatorL3

class SVStructuralTranslatorL4(
    SVStructuralTranslatorL3, StructuralTranslatorL4
  ):

  # Declarations

  def rtlir_tr_subcomp_port_decls( s, _port_decls ):
    port_decls = map( lambda x: x['decl'], _port_decls )
    port_defs = map( lambda x: x['def'], _port_decls )
    make_indent( port_decls, 2 )
    make_indent( port_defs, 1 )
    return {
      'def' : '\n'.join( port_defs ),
      'decl' : ',\n'.join( port_decls )
    }

  def rtlir_tr_subcomp_port_decl( s, c_id, c_rtype, port_id, port_rtype,
      array_type ):
    port_dtype = port_rtype.get_dtype()
    port_def_rtype = Wire( port_rtype.get_dtype() )
    port_array_type = array_type

    if isinstance( port_dtype, Vector ):
      dtype = s.rtlir_tr_vector_dtype( port_dtype )
    elif isinstance( port_dtype, Array ):
      dtype = s.rtlir_tr_array_dtype( port_dtype )
    elif isinstance( port_dtype, Struct ):
      dtype = s.rtlir_tr_struct_dtype( port_dtype )
    else: assert False

    return {
      'def' : s.rtlir_tr_wire_decl('{c_id}$'+port_id, port_def_rtype,
                port_array_type, dtype),
      'decl' : '.{port_id}({{c_id}}${port_id})'.format( **locals() )
    }

  def rtlir_tr_subcomp_ifc_port_decls( s, _ifc_decls ):
    _ifc_decls = reduce( lambda res,l: res+l, _ifc_decls, [] )
    ifc_defs = map( lambda x: x['def'], _ifc_decls )
    ifc_decls = map( lambda x: x['decl'], _ifc_decls )
    return {
      'def' : '\n'.join( ifc_defs ),
      'decl' : ',\n'.join( ifc_decls )
    }

  def rtlir_tr_subcomp_ifc_port_decl( s, c_id, c_rtype, ifc_port_id,
      ifc_port_rtype, ifc_port_array_type, ports ):

    def gen_subcomp_ifc_decl( c_id, c_rtype, ports, n_dim, ifc_n_dim ):
      if not n_dim:
        return [ {
          'def' : ports['def'].format( **locals() ),
          'decl' : ports['decl'].format( **locals() )
        } ]
      else:
        return reduce( lambda res, l: res + l, map(
          lambda idx: gen_subcomp_ifc_decl( c_id, c_rtype, ports, n_dim[1:],
            ifc_n_dim+'_$'+str( idx ) ), xrange( n_dim[0] )
        ), [] )

    n_dim = ifc_port_array_type[ 'n_dim' ]
    return\
      gen_subcomp_ifc_decl( c_id, c_rtype, ports, n_dim, '' )

  # def rtlir_tr_subcomp_ifc_port_decls( s, _ifc_decls ):
    # ifc_port_decls = map( lambda x: x['decl'], _ifc_decls )
    # ifc_port_defs = map( lambda x: x['def'], _ifc_decls )
    # make_indent( ifc_port_decls, 2 )
    # make_indent( ifc_port_defs, 1 )
    # return {
      # 'def' : '\n'.join( ifc_port_defs ),
      # 'decl' : ',\n'.join( ifc_port_decls )
    # }

  # def rtlir_tr_subcomp_ifc_port_decl( s, c_id, c_rtype, ifc_port_id,
      # ifc_port_rtype, ifc_port_array_type ):
    # assert len( ifc_port_array_type['n_dim'] ) <= 1,\
      # 'interface array {} cannot have more than 1 dimension!'.format(
          # ifc_port_id )
    # ifc_name = ifc_port_rtype.get_name()
    # dim_sizes = ifc_port_array_type['decl']
    # inst_tmplt = '{ifc_name} {c_id}{{c_n_dim}}${ifc_port_id} {dim_sizes} ();'
    # decl_tmplt =\
      # '.{ifc_port_id}({c_id}{{c_n_dim}}${ifc_port_id}.ModuleSide)'
    # helper_tmplt =\
# """\
# {ifc_port_wires}
  # _{ifc_name}_helper _{c_id}{{c_n_dim}}${ifc_port_id} {dim_sizes}(
    # ._ifc( {c_id}{{c_n_dim}}${ifc_port_id} ),
# {ifc_ports}
  # );
# """

    # return { 'def' : inst_tmplt.format( **locals() ),
      # 'decl' : decl_tmplt.format( **locals() ) }

  # def rtlir_tr_subcomp_decls( s, subcomps ):
    # return '\n\n'.join( subcomps )

  # def rtlir_tr_subcomp_decl( s, c_id, c_rtype, port_decls, ifc_port_decls,
      # c_array_type ):
    # subcomp_tmplt = \
# """\
# """

  def rtlir_tr_subcomp_decls( s, subcomps ):
    subcomp_decls = reduce( lambda res, l: res+l, subcomps, [] )
    return '\n\n'.join( subcomp_decls )

  def rtlir_tr_subcomp_decl( s, c_id, c_rtype, port_conns, ifc_conns,
      array_type ):

    def gen_subcomp_array_decl( c_id, c_rtype, port_conns, ifc_conns,
        n_dim, c_n_dim ):
      c_name = s.rtlir_tr_component_unique_name( c_rtype )
      tplt =\
"""\
  {port_wire_defs}
  {ifc_inst_defs}

  {c_name} {c_id} (
{port_conn_decls}
{ifc_conn_decls}
  );\
"""
      if not n_dim:
        # Add the component dimension to the defs/decls
        port_wire_defs = port_conns['def'].format( **locals() )
        ifc_inst_defs = ifc_conns['def'].format( **locals() )
        port_conn_decls = port_conns['decl'].format( **locals() )
        ifc_conn_decls = ifc_conns['decl'].format( **locals() )
        return [ tplt.format( **locals() ) ]

      else:
        return reduce( lambda res, l: res+l, map(
          lambda idx: gen_subcomp_array_decl( c_id+'_$'+str(idx), c_rtype,
            port_conns, ifc_conns, n_dim[1:], c_n_dim+'_$'+str(idx) ),
          xrange( n_dim[0] )
        ), [] )

    # If `array_type` is not None we need to impelement an array of
    # components, each with their own connections for the ports.
    # This means we will only support component indexing where the index
    # is a constant integer.
    n_dim = array_type['n_dim']
    if port_conns['decl'] and ifc_conns['decl']: port_conns['decl'] += ','
    return\
      gen_subcomp_array_decl( c_id, c_rtype, port_conns, ifc_conns, n_dim, '' )

  def rtlir_tr_component_array_index( s, base_signal, index ):
    return '{base_signal}_${index}'.format( **locals() )

  def rtlir_tr_subcomp_attr( s, base_signal, attr ):
    return '{base_signal}${attr}'.format( **locals() )
