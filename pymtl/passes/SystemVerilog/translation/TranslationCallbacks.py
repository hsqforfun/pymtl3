#=========================================================================
# TranslationCallbacks.py
#=========================================================================
# A class of callback functions that are used to generate the backend
# source code.
#
# Author : Peitian Pan
# Date   : March 12, 2019

from pymtl.passes.utility import collect_objs

from utility import *
from UpblkRTLIRToSV import rtlir_upblk_to_sv

class TranslationCallbacks( object ):
  def __init__( s ):
    pass

  @staticmethod
  def rtlir_tr_struct_def( Types ):

    ret = ""

    for name, Type in Types:
      ret += generate_struct_def( name, Type ) + '\n'

    return ret

  @staticmethod
  def rtlir_tr_component_decl( strs, Type ):

    sv_component_template =\
"""//------------------------------------------------------------------------
// PyMTL translation result for component {module_name}
//------------------------------------------------------------------------

module {module_name}
(
  {interface_decls}
);
  {local_params}
  {wire_decls}
  {child_decls}
  {assignments}
  {blk_srcs}
endmodule

"""
    module_name = generate_module_name( Type )

    if strs['interface_src'] is []:
      interface_decls = ''
    else:
      make_indent( strs['interface_src'], 1 )
      interface_decls = ',\n'.join( strs['interface_src'] )

    if strs['freevar_decl_src'] is []:
      local_params = ''
    else:
      make_indent( strs['freevar_decl_src'], 1 )
      local_params = '// PyMTL freevars\n' +\
        ';\n'.join(strs['freevar_decl_src']) + '\n\n'

    if strs['wire_decl_src'] is []:
      wire_decls = ''
    else:
      make_indent( strs['wire_decl_src'], 1 )
      wire_decls = '// PyMTL wires\n' +\
        ';\n'.join(strs['wire_decl_src']) + '\n\n'
    
    if strs['tmpvar_decl_src'] is []:
      make_indent( strs['tmpvar_decl_src'], 1 )
      wire_decls += '// PyMTL tmpvars\n' +\
        ';\n'.join(strs['tmpvar_decl_src']) + '\n\n'

    if strs['subcomponent_inst_src'] is []:
      child_decls = ''
    else:
      make_indent( strs['subcomponent_inst_src'], 1 )
      child_decls = '// PyMTL sub-components\n' +\
        '\n'.join(strs['subcomponent_inst_src']) + '\n\n'

    if strs['upblk_decl_src'] is []:
      blk_srcs = ''
    else:
      make_indent( strs['upblk_decl_src'], 1 )
      blk_srcs = '// PyMTL upblks\n' +\
        '\n'.join(strs['upblk_decl_src']) + '\n\n'

    if strs['connection_decl_src'] is []:
      assignments = ''
    else:
      make_indent( strs['connection_decl_src'], 1 )
      assignments = '// PyMTL connections\n' +\
        ';\n'.join(strs['connection_decl_src']) + '\n\n'

    return sv_component_template.format( **locals() )

  @staticmethod
  def rtlir_tr_component_interface_decl( Types ):

    interface = []

    for name, ifc_type in Types:
      interface.append( generate_interface_decl( name, ifc_type ) )

    return interface

  @staticmethod
  def rtlir_tr_component_wire_decl( Types ):

    wires = []

    for name, wire_type in Types:
      wires.append( generate_signal_decl_from_type( name, wire_type ) + ';' )

    return wires

  @staticmethod
  def rtlir_tr_component_inst( Types ):

    component_inst = []

    for name, Type in Types:
      child_name = name
      child_name = get_verilog_name( child_name )

      ifcs = {}
      ifcs_decl_str = { 'input':[], 'output':[] }
      connection_wire = { 'input':[], 'output':[] }
      
      # First collect all input/output ports
      ifcs['input'] = collect_objs( Type.obj, InVPort )
      ifcs['output'] = collect_objs( Type.obj, OutVPort )

      # For in/out ports, generate and append their declarations to the list
      for prefix in [ 'input', 'output' ]:
        for name, port in ifcs[ prefix ]:

          ifcs_decl_str[ prefix ].append(
            generate_signal_decl( child_name + '$' + name, port ) + ';'
          )

          connection_wire[ prefix ].append(
            '  .{0:6}( {1}${0} ),'.format( get_verilog_name(name), child_name )
          )

      component_inst.extend( ifcs_decl_str[ 'input' ] )
      component_inst.extend( ifcs_decl_str[ 'output' ] )
      component_inst.append( '' )
      component_inst.append( generate_module_name(Type.obj)+' '+child_name )
      component_inst.append( '(' )
      component_inst.append( "  // Child component's inputs" )
      component_inst.extend( connection_wire[ 'input' ] )
      component_inst.append( "  // Child component's outputs" )
      component_inst.extend( connection_wire[ 'output' ] )
      component_inst[-2 if not connection_wire['output'] else -1] = \
        component_inst[-2 if not connection_wire['output'] else -1].rstrip(',')
      component_inst.append( ');' )

    return component_inst

  @staticmethod
  def rtlir_tr_upblk_decl( upblks ):

    upblk_src = []

    for blk, rtlir_upblk in upblks:
      upblk_src += rtlir_upblk_to_sv( blk, rtlir_upblk )

    return upblk_src

  @staticmethod
  def rtlir_tr_connections( connections ):

    assign_strs = []

    for writer, reader in connections['self_self']:
      assign_strs.append( 'assign {} = {};'.format(
        reader.get_field_name(), writer.get_field_name() 
      ) )

    for writer, reader in connections['child_child']:
      assign_strs.append( 'assign {}${} = {}${};'.format(
        get_verilog_name(reader.get_host_component().get_field_name()),
        reader.get_field_name(), 
        get_verilog_name(writer.get_host_component().get_field_name()),
        writer.get_field_name() 
      ) )

    for writer, reader in connections['self_child']:
      assign_strs.append( 'assign {} = {}${};'.format(
        reader.get_field_name(), 
        get_verilog_name(writer.get_host_component().get_field_name()),
        writer.get_field_name() 
      ) )

    for writer, reader in connections['child_self']:
      assign_strs.append( 'assign {}${} = {};'.format(
        get_verilog_name(reader.get_host_component().get_field_name()),
        reader.get_field_name(), 
        writer.get_field_name() 
      ) )

    return assign_strs

  @staticmethod
  def rtlir_tr_freevar_decl( freevars ):
    
    freevar_src = []

    for name, freevar_obj in freevars:
      freevar_src.append( 'localparam {} = {};'.format(
        name, str( freevar_obj )
      ) )

    return freevar_src

  @staticmethod
  def rtlir_tr_tmpvar_decl( tmpvars ):

    tmpvar_src = []

    for name, tmpvar_type in tmpvars:
      tmpvar_src.append( generate_signal_decl_from_type(
        name, tmpvar_type
      ) )

    return tmpvar_src
