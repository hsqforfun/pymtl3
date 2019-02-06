#========================================================================
# SimpleImportPass.py
#========================================================================
# SimpleImportPass class imports a SystemVerilog source file back to a 
# PyMTL RTLComponent. It is meant to be used on files generated by 
# pymtl.passes.SystemVerilogTranslationPass. 
# 
# Author : Peitian Pan
# Date   : Oct 18, 2018

import os
import re
import sys
import shutil

from pymtl      import *
from BasePass   import BasePass
from subprocess import check_output, STDOUT, CalledProcessError
from errors     import VerilatorCompileError, PyMTLImportError

# Indention const strings

space2 = '\n  '
space4 = '\n    '
space6 = '\n      '
space8 = '\n        '

class SimpleImportPass( BasePass ):

  #---------------------------------------------------------------------
  # Exposed __call__ API
  #---------------------------------------------------------------------

  def __call__( s, model ):
    """ Import a Verilog/SystemVerilog file. model is the PyMTL source of
        the input verilog file. """

    # This pass includes the following steps:
    # 1. Use verilator to compile the given Verilog source into C++.
    # 2. Create a C++ wrapper that can call the Verilated model.
    # 3. Compile the C++ wrapper and the Verilated model into a shared lib.
    # 4. Create a Python wrapper that can call the compiled shared lib
    #    through CFFI. 

    # model should have been translated

    try:
      assert model._translated, "Component should be translated first!"

    except AttributeError:
      raise PyMTLImportError( model.__class__.__name__,
        'the target model instance should be translated first!' 
      )

    # Assume the input verilog file and the top module has the same name 
    # as the class name of model
    
    verilog_file = model.__class__.__name__
    ssg_name     = model.__class__.__name__ + '.ssg'
    top_module   = model.__class__.__name__

    # Try to load the sensitive group from ssg file

    try:
      with open( ssg_name, 'r' ) as ssg_file:
        sense_group = []
        for line in ssg_file:
          ssg_rule = line.strip().replace( '\n', '' )
          pos = line.find( '=>' )

          if pos == -1:
            raise Exception( '.ssg file does not have the correct format!' )

          in_ports  = ssg_rule[ : pos ].strip()
          out_ports = ssg_rule[ pos+2 : ].strip()

          sense_group.append( ( s.parse_css( out_ports ), s.parse_css( in_ports ) ) )

    except IOError:
      sense_group = None

    # Get all ports

    ports = model.get_input_value_ports() | model.get_output_value_ports()

    # Generate Verilog and verilator names for all ports

    for port in ports:
      port.verilog_name   = s.generate_verilog_name( port._dsl.my_name )
      port.verilator_name = s.generate_verilator_name( port.verilog_name )
      if '[' in port._dsl.my_name:
        port.verilog_name = get_array_name( port.verilog_name )
        port.verilator_name = get_array_name( port.verilator_name )
		
    # Compile verilog_file with verilator

    s.create_verilator_model( verilog_file, top_module )

    # Create a cpp wrapper for the verilated model

    model.array_dict, port_cdef, c_wrapper =\
      s.create_verilator_c_wrapper( model, top_module ) 

    # Compile the cpp wrapper and the verilated model into a shared lib

    lib_file = s.create_shared_lib( model, c_wrapper, top_module )

    # Create a python wrapper that can access the verilated model

    py_wrapper_file = s.create_verilator_py_wrapper(
      model, top_module, lib_file, port_cdef, model.array_dict, sense_group
    )

    py_wrapper = py_wrapper_file.split('.')[0]

    if py_wrapper in sys.modules:
      # We are (probably) in a test process that is repeatedly run
      # Reloading is needed since user may have updated the source file
      exec( "reload( sys.modules[ '{py_wrapper}' ] )".format( **locals() ) )
      exec( "ImportedModel = sys.modules[ '{py_wrapper}' ].{top_module}".\
        format( **locals() )
      )

    else:
      # First time execution
      import_cmd = \
        'from {py_wrapper} import {top_module} as ImportedModel'.\
        format( py_wrapper = py_wrapper, 
                top_module = top_module,
        )

      exec( import_cmd )

    model.imported_model = ImportedModel()

  #---------------------------------------------------------------------
  # Pass helper functions
  #---------------------------------------------------------------------

  def create_verilator_model( s, verilog_file, top_module ):
    """ Create a verilator file correspoding to the verilog_file model """
    # This function is based on PyMTL v2

    # Prepare the verilator commandline

    verilator_cmd = '''verilator -cc {verilog_file} -top-module '''\
                    '''{top_module} --Mdir {obj_dir} -O3 {flags}'''

    obj_dir = 'obj_dir_' + top_module
    flags   = ' '.join( [
      '--unroll-count 1000000',
     '--unroll-stmts 1000000',
     '--assert',
     '-Wno-UNOPTFLAT', 
     '-Wno-UNSIGNED',
    ] )

    verilator_cmd = verilator_cmd.format( **vars() )

    # Remove obj_dir if already exists
    # It is the place where the verilator output is stored

    if os.path.exists( obj_dir ):
      shutil.rmtree( obj_dir )

    # Try to call verilator

    s.try_cmd( 'Calling verilator', \
      verilator_cmd, VerilatorCompileError, shell = True 
    )

  def create_verilator_c_wrapper( s, model, top_module ):
    """ create wrapper for verilated model so that later we can
        access it through cffi """
    # This function is based on PyMTL v2

    # Peitian, Oct 22, 2018
    # I added support for port defined using list comprehension so that
    # definitions like
    #   s.in_ = [ InVPort( Bits32 ) for x in xrange( 10 ) ]
    # can be correctly recognized.

    # The template should be in the same directory as this file

    template_file = os.path.dirname( os.path.abspath( __file__ ) )\
      + os.path.sep + 'verilator_wrapper_template.c'

    verilator_c_wrapper_file = top_module + '_v.cpp'

    # Collect all array ports
    
    array_dict = {}

    ports = sorted(\
      model.get_input_value_ports() | model.get_output_value_ports(),\
      key = repr 
    )

    s.collect_array_ports( array_dict, ports )

    # Generate input and output ports for the verilated model

    port_externs = []
    port_cdef = []

    for port in ports:
      # Only generate an array port decl if index is zero
      if '[' in port._dsl.my_name and get_array_idx( port._dsl.my_name ) != 0:
        continue
      port_externs.append( s.port_to_decl( array_dict, port ) + space4 )
      port_cdef.append( s.port_to_decl( array_dict, port ) )

    port_externs = ''.join( port_externs )

    # Generate initialization stmts for in/out ports

    port_inits = []

    for port in ports:
      # Generate n array port assignment if index is zero
      if '[' in port._dsl.my_name and get_array_idx( port._dsl.my_name ) != 0:
        continue
      port_inits.extend(
        map( lambda x: x + space2, s.port_to_init( array_dict, port ) )
      )

    port_inits = ''.join( port_inits )

    with open( template_file, 'r' )            as template,\
         open( verilator_c_wrapper_file, 'w' ) as output:

      c_wrapper = template.read()
      c_wrapper = c_wrapper.format(\
        top_module    = top_module,
        port_externs  = port_externs,
        port_inits    = port_inits,
      )
      output.write( c_wrapper )

    return array_dict, port_cdef, verilator_c_wrapper_file

  def create_shared_lib( s, model, c_wrapper, top_module ):
    ''' compile the Cpp wrapper and verilated model into a shared lib '''
    # This function is based on PyMTL v2

    lib_file = 'lib{}_v.so'.format( top_module )

    # Assume $PYMTL_VERILATOR_INCLUDE_DIR is defined

    verilator_include_dir = os.environ.get( 'PYMTL_VERILATOR_INCLUDE_DIR' )

    include_dirs = [
      verilator_include_dir, 
      verilator_include_dir + '/vltstd',
    ]

    obj_dir_prefix = 'obj_dir_{}/V{}'.format( top_module, top_module )

    cpp_sources_list = []

    # Read through the makefile of the verilated model to find 
    # cpp files we need

    with open( obj_dir_prefix + "_classes.mk" ) as makefile:
      found = False
      for line in makefile:
        if line.startswith("VM_CLASSES_FAST += "):
          found = True
        elif found:
          if line.strip() == '':
            found = False
          else:
            filename = line.strip()[:-2]
            cpp_file = 'obj_dir_{}/{}.cpp'.format( top_module, filename )
            cpp_sources_list.append( cpp_file )

    # Complete the cpp sources file list

    cpp_sources_list += [
      obj_dir_prefix + '__Syms.cpp', 
      verilator_include_dir + '/verilated.cpp', 
      verilator_include_dir + '/verilated_dpi.cpp', 
      c_wrapper,
    ]

    # Call compiler with generated flags & dirs

    s.compile(
      flags        = '-O0 -fPIC -shared', 
      include_dirs = include_dirs, 
      output_file  = lib_file, 
      input_files  = cpp_sources_list,
    )
    
    return lib_file

  def create_verilator_py_wrapper(
      s, model, top_module, lib_file, port_cdef, array_dict, sense_group
  ):
    ''' create a python wrapper that can manipulate the verilated model
    through the interfaces exposed by the Cpp wrapper '''

    # This function is based on PyMTL v2
    
    template_file = \
      os.path.dirname( os.path.abspath( __file__ ) ) \
      + os.path.sep + 'verilator_wrapper_template.py'

    verilator_py_wrapper_file = top_module + '_v.py'

    # Port definitions for verilated model
    port_externs  = ''.join( x+space8 for x in port_cdef )

    # Port definition in PyMTL style
    port_defs     = []

    # Set verilated input ports to PyMTL input ports
    set_inputs    = []

    # Output of combinational update block
    set_comb      = []

    # Output of sequential update block
    set_next      = []

    # Line trace 
    line_trace = s.generate_py_line_trace( model )

    # Internal line trace 
    in_line_trace = s.generate_py_internal_line_trace( model )

    # Template for update blocks
    comb_upblk = \
"""
    @s.update
    def {upblk_name}():
      # set inputs
      {set_inputs}
      # call evaluate function
      s._ffi_inst.eval( s._ffi_m )

      # get outputs
      {set_comb}"""

    # Combinational update blocks
    comb_upblks = []

    # Create PyMTL port definitions, input setting, comb stmts
    for port in model.get_input_value_ports():
      name = port._dsl.my_name
      if '[' in name:
        if get_array_idx( name ) != 0:
          continue
        else:
          # Only create definition for list element of index 0
          nbits = port._dsl.Type.nbits
          array_range = array_dict[ get_array_name( name ) ]
          name = get_array_name( name )
          port_defs.append(\
            '''s.{name} = [ InVPort(Bits{nbits}) '''
            '''for _x in xrange({array_range}) ]'''.\
            format( **locals() ) 
          )
      else:
        # This port is not a list
        port_defs.append( '{name} = InVPort( Bits{nbits} )'.\
          format(
            name  = port._dsl.full_name, 
            nbits = port._dsl.Type.nbits,
          ) 
        )

    for port in model.get_output_value_ports():
      name = port._dsl.my_name
      if '[' in name:
        if get_array_idx( name ) != 0:
          continue
        else:
          # Only create definition for the list element of index 0
          nbits = port._dsl.Type.nbits
          array_range = array_dict[ get_array_name( name ) ]
          name = get_array_name( name )
          port_defs.append(\
            '''s.{name} = [ OutVPort(Bits{nbits})'''
            ''' for _x in xrange({array_range}) ]'''.\
            format( **locals() ) 
          )
      else:
        # This port is not a list
        port_defs.append( '{name} = OutVPort( Bits{nbits} )'.\
          format(
            name  = port._dsl.full_name, 
            nbits = port._dsl.Type.nbits,
          ) 
        )

    # Generate comb_upblks according to sense_group
    if sense_group is None:
      for port in model.get_input_value_ports():
        if port._dsl.my_name == 'clk':
          continue
        # Generate assignments to setup the inputs of verilated model 
        set_inputs.extend( s.set_input_stmt( port, array_dict ) )

      for port in model.get_output_value_ports():
        # Generate assignments to read output from the verilated model
        comb, next_ = s.set_output_stmt( port, array_dict )
        set_comb.extend( comb )
        set_next.extend( next_ )

      comb_upblks.append( comb_upblk.format(
        upblk_name = 'comb_eval',
        set_inputs = ''.join( [ x+space6 for x in set_inputs ] ),
        set_comb = ''.join( [ x+space6 for x in set_comb ] )
      ) )

    else:
      # Generate one upblk for each sensitive group
      for idx, ( out, in_ ) in enumerate( sense_group ):
        set_inputs = []
        set_comb = []
        
        for in_port in in_:
          set_inputs.extend( s.set_input_stmt( model.__dict__[ in_port ], array_dict ) )
        for out_port in out:
          comb, next_ = s.set_output_stmt( model.__dict__[ out_port ], array_dict )
          set_comb.extend( comb )
          set_next.extend( next_ )

        comb_upblks.append( comb_upblk.format(
          upblk_name = 'comb_eval_' + str( idx ),
          set_inputs = ''.join( [ x+space6 for x in set_inputs ] ),
          set_comb = ''.join( [ x+space6 for x in set_comb ] )
        ) )

    # Read from template and fill in contents 

    with open( template_file, 'r' )             as template, \
         open( verilator_py_wrapper_file, 'w' ) as output:

      py_wrapper = template.read()
      py_wrapper = py_wrapper.format(
        top_module    = top_module,
        lib_file      = lib_file,
        port_externs  = port_externs,
        port_defs     = ''.join( [ x+space4 for x in port_defs ] ),
        comb_upblks   = '\n'.join( [ x for x in comb_upblks ] ),
        # set_inputs    = ''.join( [ x+space6 for x in set_inputs ] ),
        # set_comb      = ''.join( [ x+space6 for x in set_comb ] ),
        set_next      = ''.join( [ x+space6 for x in set_next ] ),
        line_trace    = line_trace,
        in_line_trace = in_line_trace,
      )
      output.write( py_wrapper )

    return verilator_py_wrapper_file

  #----------------------------------------------------------------------
  # Helper functions for SimpleImportPass
  #----------------------------------------------------------------------

  def try_cmd( s, name, cmd, exception = Exception, shell = False ):
    """Try to run name action with cmd command. If the command fails, 
    CalledProcessError exception is raised"""

    try:
      if shell:
        # for verilator compiling command
        ret = check_output( cmd, stderr=STDOUT, shell = True )
      else:
        # for compiling
        ret = check_output( cmd.split(), stderr=STDOUT, shell = shell )
    except CalledProcessError as e:
      error_msg = """
                    {name} error! 

                    Cmd:
                    {cmd}

                    Error:
                    {error}
                  """
      raise exception( error_msg.format( 
        name    = name, 
        cmd     = e.cmd, 
        error   = e.output
      ) )

  def collect_array_ports( s, array_dict, ports ):
    """Fill array_dict with port names and index ranges."""

    for port in ports:
      if '[' in port._dsl.my_name:
        array_name    = get_array_name( port._dsl.my_name )
        array_idx     = get_array_idx( port._dsl.my_name )
        try: 
          array_range = array_dict[ array_name ]
        except KeyError:
          array_range = 1
        array_dict[ array_name ] = max( array_idx + 1, array_range )

  def port_to_decl( s, array_dict, port ):
    """Generate port declarations for port"""
    # This function is based on its counterpart from PyMTL v2

    if '[' in port._dsl.my_name:
      # port belongs to a list of ports
      ret         = '{data_type} * {name}[{array_range}];'
      name        = get_array_name( port._dsl.my_name )
      array_range = array_dict[ name ]
    else:
      # single port
      ret         = '{data_type} * {name};'
      name        = port._dsl.my_name

    bitwidth = port._dsl.Type.nbits

    if    bitwidth <= 8:   
      data_type = 'unsigned char'
    elif  bitwidth <= 16:  
      data_type = 'unsigned short'
    elif  bitwidth <= 32: 
      data_type = 'unsigned int'
    elif bitwidth <= 64:
      data_type = 'unsigned long'
    else:
      data_type = 'unsigned int'

    return ret.format( **locals() )

  def port_to_init( s, array_dict, port ):
    """Generate port initializations for port"""
    # This function is based on its counterpart from PyMTL v2

    ret = []
    
    bitwidth       = port._dsl.Type.nbits
    dereference    = '&' if bitwidth <= 64 else ''

    if '[' in port._dsl.my_name:
      # This is a list of ports
      name = get_array_name( port._dsl.my_name )
      ret.append( 'for( int i = 0; i < {array_range}; i++ )'.\
          format( array_range = array_dict[ name ] )
      )
      ret.append( '  m->{name}[i] = {dereference}model->{name}[i];'.\
          format( name = name, dereference = dereference ) 
      )
    else:
      name = port._dsl.my_name
      ret.append( 'm->{name} = {dereference}model->{name};'.\
          format( name = name, dereference = dereference ) 
      )

    return ret

  def generate_verilog_name( s, name ):
    """Generate a verilog-compliant name based on name"""
    return name.replace('.', '_')

  def generate_verilator_name( s, name ):
    """Generate a verilator-compliant name based on name"""
    return name.replace( '__', '___05F' ).replace( '$', '__024' )

  def compile( s, flags, include_dirs, output_file, input_files ):
    """Compile the Cpp wrapper and the verilated model into shared lib"""
    # This function is based on its counterpart from PyMTL v2

    compile_cmd = 'g++ {flags} {idirs} -o {ofile} {ifiles}'

    compile_cmd = compile_cmd.format(
      flags  = flags, 
      idirs  = ' '.join( [ '-I'+d for d in include_dirs ] ), 
      ofile  = output_file, 
      ifiles = ' '.join( input_files ), 
    )

    s.try_cmd( 'Compiling shared lib', compile_cmd )

  def generate_py_line_trace( s, m ):
    """Create a line trace string for all ports"""

    ret = "'"   # eg: 'clk:{}, reset:{}, \n'.format( s.clk, s.reset, )

    ports = sorted(
      m.get_input_value_ports() | m.get_output_value_ports(), 
      key = repr
    )

    for port in ports:
      ret += '{my_name}: {{}}, '.format( my_name = port._dsl.my_name )

    ret += "'.format("

    for port in ports:
      ret += '{}, '.format( port._dsl.full_name )

    ret += ")"

    return ret

  def generate_py_internal_line_trace( s, m ):
    """Create a line trace string for all ports inside the verilated
    model"""

    ret = "'"   # eg: 'clk:{}, reset:{}, \n'.format( s.clk, s.reset, )

    ports = sorted(
      m.get_input_value_ports() | m.get_output_value_ports(), 
      key = repr
    )

    for port in ports:
      ret += '{my_name}: {{}}, '.format( my_name = port._dsl.my_name )

    ret += "\\n'.format("

    for port in ports:
      ret += '{}, '.format( 's._ffi_m.'+port._dsl.my_name+'[0]' )

    ret += ")"

    return ret
  
  def set_input_stmt( s, port, array_dict ):
    """Generate initializations for interfaces"""
    # This function is based on its counterpart from PyMTL v2

    inputs = []
    name = port._dsl.my_name
    if '[' in name:
      # special treatment for list
      name = get_array_name( name )
      inputs.append( 'for _x in xrange({array_range}):'.\
        format( array_range = array_dict[ name ] ) 
      )
      for idx, offset in s.get_indices( port ):
        inputs.append('  s._ffi_m.{v_name}[_x][{idx}]=s.{py_name}[_x]{offset}'.\
          format(\
            v_name  = port.verilator_name, 
            py_name = name, 
            idx     = idx, 
            offset  = offset
          ) 
        )
    else:
      for idx, offset in s.get_indices( port ):
        inputs.append( 's._ffi_m.{v_name}[{idx}] = s.{py_name}{offset}'.\
          format(\
            v_name  = port.verilator_name,
            py_name = name, 
            idx     = idx, 
            offset  = offset
          ) 
        )
    return inputs

  def set_output_stmt( s, port, array_dict ):
    """Generate the list of vars that should be called in update blocks or
    update-on-edge blocks"""
    # This function is based on its counterpart from PyMTL v2

    comb, next_ = [], []
    outputs = []
    name = port._dsl.my_name
    if '[' in name:
      name = get_array_name( name )
      outputs.append( 'for _x in xrange({array_range}):'.\
          format( array_range = array_dict[ name ] ) 
      )
      for idx, offset in s.get_indices( port ):
        outputs.append(\
          '  s.{py_name}[_x]{offset} = s._ffi_m.{v_name}[_x][{idx}]'.\
          format(
            v_name  = port.verilator_name, 
            py_name = name, 
            idx     = idx, 
            offset  = offset
          ) 
        )
    else:
      for idx, offset in s.get_indices( port ):
        stmt = 's.{py_name}{offset} = s._ffi_m.{v_name}[{idx}]'.\
          format(
            v_name  = port.verilator_name, 
            py_name = port._dsl.my_name, 
            idx     = idx, 
            offset  = offset
          )
      outputs.append( stmt )
      # next_.append( stmt )

    comb = outputs
    # TODO: currently only work on combinational upblks
    # next_ = outputs
    return comb, next_

  def get_indices( s, port ):
    """Generate a list of idx-offset tuples to copy data from verilated
    model to PyMTL model"""
    # This function is based on its counterpart from PyMTL v2

    num_assigns = 1 if port._dsl.Type.nbits <= 64 else (port._dsl.Type.nbits-1)/32+1
    if num_assigns == 1:
      return [(0, '')]
    return [
      ( i, '[{}:{}]'.format( i*32, min( i*32+32, port._dsl.Type.nbits ) ) ) \
      for i in range(num_assigns)
    ]

  def parse_css( s, css ):
    """Parse a comma-separated string and return a set of all fields"""
    return map( lambda x: x.strip(), css.split( ',' ) )

#-------------------------------------------------------------------------------
# Global helper functions
#-------------------------------------------------------------------------------

def get_array_name( name ):
  return re.sub( r'\[(\d+)\]', '', name )

def get_array_idx( name ):
  m = re.search( r'\[(\d+)\]', name )
  return int( m.group( 1 ) )
