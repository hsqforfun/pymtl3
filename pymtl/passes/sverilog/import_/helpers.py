#=========================================================================
# helpers.py
#=========================================================================
# This file includes the functions that might be useful to some import
# passes. Some of the functions are based on PyMTL v2.
# 
# Author : Peitian Pan
# Date   : Feb 22, 2019

import pymtl, __builtin__

from pymtl.dsl.Connectable import Signal as pymtl_Signal
from pymtl.passes.utility.pass_utility import make_indent
from pymtl.passes.rtlir.RTLIRType      import *
from pymtl.passes.rtlir.structural.StructuralRTLIRSignalExpr import *

#-------------------------------------------------------------------------
# verilog_name
#-------------------------------------------------------------------------

def verilog_name( name ):

  return name.replace('[', '_$').replace(']', '')

#-------------------------------------------------------------------------
# verilator_name
#-------------------------------------------------------------------------

def verilator_name( name ):

  return verilog_name(name).replace('_$', '___024')

#-------------------------------------------------------------------------
# pymtl_name
#-------------------------------------------------------------------------

def pymtl_name( name ):

  return name

#-------------------------------------------------------------------------
# get_nbits
#-------------------------------------------------------------------------

def get_nbits( port ):

  if isinstance( port, Array ): rtype = port.get_sub_type()
  else: rtype = port

  return rtype.get_dtype().get_length()

#-------------------------------------------------------------------------
# get_n_dim_size
#-------------------------------------------------------------------------

def get_n_dim_size( port ):

  if isinstance( port, Array ): return port.get_dim_sizes()
  else: return []

#-------------------------------------------------------------------------
# get_c_dim_size
#-------------------------------------------------------------------------

def get_c_dim_size( port ):

  return reduce( lambda s,i: s+'[{}]'.format(i), get_n_dim_size( port ), '' )

#-------------------------------------------------------------------------
# generate_signal_print_c
#-------------------------------------------------------------------------

def generate_signal_print_c( name, port ):

  nbits = get_nbits( port )

  if    nbits <= 8:  fspec = 'x'
  elif  nbits <= 16: fspec = 'x'
  elif  nbits <= 32: fspec = 'x'
  elif  nbits <= 64: fspec = 'x'
  else:              fspec = 'x'

  name = verilator_name( name )

  return\
    'printf( "{name} = %{fspec}\\n", model->{name} );'.format( **locals() )

#-------------------------------------------------------------------------
# generate_signal_decl_c
#-------------------------------------------------------------------------

def generate_signal_decl_c( name, port ):

  nbits = get_nbits( port )
  c_dim_size = get_c_dim_size( port )

  if    nbits <= 8:  data_type = 'unsigned char'
  elif  nbits <= 16: data_type = 'unsigned short'
  elif  nbits <= 32: data_type = 'unsigned int'
  elif  nbits <= 64: data_type = 'unsigned long'
  else:              data_type = 'unsigned int'

  name = verilator_name( name )

  return '{data_type} * {name}{c_dim_size};'.format( **locals() )

#-------------------------------------------------------------------------
# generate_signal_init_c
#-------------------------------------------------------------------------

def generate_signal_init_c( name, port ):

  ret        = []
  nbits      = get_nbits( port )
  deference  = '&' if nbits <= 64 else ''
  c_dim_size = get_c_dim_size( port )
  name       = verilator_name( name )

  if c_dim_size:

    # This is a potentially recursive array structure

    n_dim_size = get_n_dim_size( port )
    sub = ''

    for idx, dim_size in enumerate( n_dim_size ):
      ret.append(
        'for ( int i_{idx} = 0; i_{idx} < {dim_size}; i_{idx}++ )'.format(
          **locals()
      ) )
      sub += '[i_{idx}]'.format( **locals() )

    ret.append( 'm->{name}{sub} = {deference}model->{name}{sub};'.format(
      **locals()
    ) )

    # Indent the whole for loop appropriately

    for start, dim_size in enumerate( n_dim_size ):
      for idx in xrange( start+1, len( n_dim_size )+1 ):
        ret[ idx ] = '  ' + ret[ idx ]

  else:

    ret.append( 'm->{name} = {deference}model->{name};'.format( **locals() ) )

  return ret

#-------------------------------------------------------------------------
# load_ssg
#-------------------------------------------------------------------------
# Return the sensitivity group from the given .ssg file. None is returned
# if the given ssg file does not exist.

def load_ssg( ssg_name ):

  def parse_css( css ):
    """Parse a comma-separated string and return a list of all fields"""
    return map( lambda x: x.strip(), css.split( ',' ) )

  try:
    with open( ssg_name, 'r' ) as ssg_file:

      ssg = []
      for line in ssg_file:
        ssg_rule = line.strip().replace( '\n', '' )
        pos = line.find( '=>' )

        if pos == -1:
          raise Exception(
            '{} does not have the correct format!'.format( ssg_name ) )

        in_ports  = ssg_rule[ : pos ].strip()
        out_ports = ssg_rule[ pos+2 : ].strip()

        ssg.append( ( parse_css( out_ports ), parse_css( in_ports ) ) )

  except IOError:
    ssg = None

  return None if ssg == [] else ssg

#-------------------------------------------------------------------------
# generate_default_ssg
#-------------------------------------------------------------------------
# Generate the default ssg from the given module interface. Assume all
# outport ports depends on all input ports (both combinationally and
# sequentially).

def generate_default_ssg( unpacked_ports ):

  inports, outports = [], []

  for name, port in unpacked_ports:

    if   port.get_direction() == 'input':  inports.append( name )
    elif port.get_direction() == 'output': outports.append( name )
    else: assert False

    # if isinstance( port, pymtl.InVPort ):
      # inports.append( port._dsl.my_name )

    # elif isinstance( port, pymtl.OutVPort ):
      # outports.append( port._dsl.my_name )

  return [ ( outports, map( lambda x: 'B'+x, inports ) ) ]

#-------------------------------------------------------------------------
# get_struct_objects
#-------------------------------------------------------------------------

def get_struct_objects( port_objs ):

  def get_struct_class( port_obj ):

    assert isinstance( port_obj, pymtl_Signal )

    Type = port_obj._dsl.Type

    assert hasattr(Type, '__name__') and not Type.__name__ in dir(__builtin__)

    return Type

  ret = {}

  for port_obj in port_objs:

    rtype = get_rtlir_type( port_obj )
    assert isinstance( rtype, Port )
    dtype = rtype.get_dtype()

    if isinstance( dtype, Struct ):

      if dtype.get_name() in ret: continue
    
      # Try to get the class object of this struct
      # I think this should be enough even for structs with nested
      # structs ( i.e. you have that nested struct once you have the top
      # level struct )... Need to check this later!

      Type = get_struct_class( port_obj )

    else: continue

    assert Type.__name__ == dtype.get_name()

    ret[ Type.__name__ ] = Type

  return ret

#-------------------------------------------------------------------------
# generate_signal_decl_py
#-------------------------------------------------------------------------

def generate_signal_decl_py( name, port ):

  name = pymtl_name( name )

  nbits = get_nbits( port )

  if isinstance( port, Array ): rtype = port.get_sub_type()
  else: rtype = port
  dtype = rtype.get_dtype()
  assert isinstance( rtype, Port )

  if rtype.get_direction() == 'input': direction = 'InVPort'
  elif rtype.get_direction() == 'output': direction = 'OutVPort'
  else: assert False

  ret = '{}'
  n_dim_size = get_n_dim_size( port )

  # Array type

  if n_dim_size:

    for idx, dim_size in enumerate( n_dim_size ):
      ret = ret.format( '[{{}} for i_{idx} in xrange({dim_size})]'.format(
        **locals()
      ) )

  # Vector type

  if isinstance( dtype, Vector ):

    ret = ret.format( direction+'(Bits'+str(nbits)+')' )

  # Struct type

  elif isinstance( dtype, Struct ):

    ret = ret.format( direction+'('+dtype.get_name()+')' )

  else: assert False

  ret = 's.' + name + ' = ' + ret

  return ret

#-------------------------------------------------------------------------
# flatten_packed_dtype
#-------------------------------------------------------------------------

def flatten_packed_dtype( name, dtype ):

  if isinstance( dtype, Vector ):

    return [ ( 's.'+name, dtype.get_length() ) ]

  elif isinstance( dtype, Struct ):

    ret = []

    for field_name, field_dtype in dtype.get_all_properties():

      ret.extend( flatten_packed_dtype( name+'.'+field_name, field_dtype ) )

    return ret

  elif isinstance( dtype, PackedArray ):

    ret = []

    for idx in xrange( dtype.get_dim_sizes()[0] ):

      ret.extend(
        flatten_packed_dtype( name+'[{}]'.format(idx),
        dtype.get_next_dim_type() ) )

    return ret

  else: assert False

#-------------------------------------------------------------------------
# read_ffi_model_py
#-------------------------------------------------------------------------

def read_ffi_model_py( lhs, rhs, name, dtype ):

  dtype_length = dtype.get_length()

  if   dtype_length <= 8  : VL_BITWIDTH = 8
  elif dtype_length <= 16 : VL_BITWIDTH = 16
  elif dtype_length <= 32 : VL_BITWIDTH = 32
  elif dtype_length <= 64 : VL_BITWIDTH = 64
  else:                     VL_BITWIDTH = 32

  tplt = '{dtype_name}[{lhs_start}:{lhs_stop}] = ' +\
         'get_bit_slice( {rhs_signal}, {rhs_start}, {rhs_stop} )'

  ret = []

  rname = pymtl_name( name )
  vec_list = flatten_packed_dtype( name, dtype )
  vec_list.reverse()

  cur_vec_list = []
  rhs_pos, rhs_cur_bit, lhs_cur_bit, signal_idx = 0, 0, 0, 0

  while signal_idx < len( vec_list ):

    rhs_rest_bit = VL_BITWIDTH-rhs_cur_bit
    dtype_name = vec_list[ signal_idx ][0]
    nbits = vec_list[ signal_idx ][1] - lhs_cur_bit

    if rhs_rest_bit > nbits:

      lhs_start = lhs_cur_bit
      lhs_stop = lhs_cur_bit+nbits
      rhs_signal = (rhs+'[{rhs_pos}]').format( **locals() )
      rhs_start = rhs_cur_bit
      rhs_stop = rhs_cur_bit+nbits

      rhs_cur_bit += nbits
      lhs_cur_bit = 0
      signal_idx += 1

    else:

      if rhs_rest_bit == nbits:

        lhs_start = lhs_cur_bit
        lhs_stop = lhs_cur_bit+nbits
        rhs_signal = (rhs+'[{rhs_pos}]').format( **locals() )
        rhs_start = rhs_cur_bit
        rhs_stop = rhs_cur_bit+nbits

        rhs_cur_bit = 0
        lhs_cur_bit = 0
        signal_idx += 1

      else:

        lhs_start = lhs_cur_bit
        lhs_stop = lhs_cur_bit+rhs_rest_bit
        rhs_signal = (rhs+'[{rhs_pos}]').format( **locals() )
        rhs_start = rhs_cur_bit
        rhs_stop = rhs_cur_bit+rhs_rest_bit

        rhs_cur_bit = 0
        lhs_cur_bit += rhs_rest_bit

      rhs_pos += 1

    ret.append( tplt.format( **locals() ) )

  return ret

#-------------------------------------------------------------------------
# write_ffi_model_py
#-------------------------------------------------------------------------

def write_ffi_model_py( lhs, rhs, name, dtype ):

  ret = []

  dtype_length = dtype.get_length()

  if   dtype_length <= 8  : VL_BITWIDTH = 8
  elif dtype_length <= 16 : VL_BITWIDTH = 16
  elif dtype_length <= 32 : VL_BITWIDTH = 32
  elif dtype_length <= 64 : VL_BITWIDTH = 64
  else:              VL_BITWIDTH = 32

  vec_list = flatten_packed_dtype( name, dtype )
  vec_list.reverse()

  cur_vec_list = []
  lhs_pos, lhs_cur_bit, rhs_cur_bit, signal_idx = 0, 0, 0, 0

  while signal_idx < len( vec_list ):

    lhs_rest_bit = VL_BITWIDTH-lhs_cur_bit
    nbits = vec_list[ signal_idx ][1] - rhs_cur_bit

    if lhs_rest_bit > nbits:

      cur_vec_list.append( (
        vec_list[signal_idx][0]+'[{}:{}]'.format(
          rhs_cur_bit, rhs_cur_bit+nbits ),
        0 if len(cur_vec_list) == 0\
          else cur_vec_list[-1][2]+cur_vec_list[-1][1],
        nbits
      ) )
      lhs_cur_bit += nbits
      rhs_cur_bit = 0
      signal_idx += 1

    else:

      if lhs_rest_bit == nbits:

        cur_vec_list.append( (
          vec_list[signal_idx][0]+'[{}:{}]'.format(
            rhs_cur_bit, rhs_cur_bit+nbits ),
          0 if len(cur_vec_list) == 0\
            else cur_vec_list[-1][2]+cur_vec_list[-1][1],
          nbits
        ) )
        lhs_cur_bit = 0
        rhs_cur_bit = 0
        signal_idx += 1

      else:

        cur_vec_list.append( (
          vec_list[signal_idx][0]+'[{}:{}]'.format(
            rhs_cur_bit, rhs_cur_bit+lhs_rest_bit ),
          0 if len(cur_vec_list) == 0\
            else cur_vec_list[-1][2]+cur_vec_list[-1][1],
          lhs_rest_bit
        ) )
        lhs_cur_bit = 0
        rhs_cur_bit += lhs_rest_bit

      rhs_str = reduce( lambda s, x: '({}<<{})|({})'.format(
        'int('+x[0]+')', x[1], s ), cur_vec_list[1:],
        'int('+cur_vec_list[0][0]+')' )

      ret.append(
        (lhs+'='+rhs_str).format( name = pymtl_name(name)+'[{}]'.format(lhs_pos) )
      )

      lhs_pos += 1

      cur_vec_list = []

  if cur_vec_list:

    rhs_str = reduce( lambda s, x: '({}<<{})|({})'.format(
      'int('+x[0]+')', x[1], s ), cur_vec_list[1:],
      'int('+cur_vec_list[0][0]+')' )

    ret.append(
      (lhs+'='+rhs_str).format(name = pymtl_name(name)+'[{}]'.format(lhs_pos))
    )

  return ret

#-------------------------------------------------------------------------
# generate_seq_upblk_py
#-------------------------------------------------------------------------

def generate_seq_upblk_py( ports, ssg ):

  seq_upblk_tplt = """@s.update_on_edge
    def tick_sequential():
{register_inputs}
      s._ffi_m.clk[0] = 0
      s._ffi_inst.eval( s._ffi_m )
      s._ffi_m.clk[0] = 1
      s._ffi_inst.eval( s._ffi_m )"""

  seq_in_ports = set()
  port_rtypes = {}
  port_rtypes.update( ports )
  seq_dep_outports = set()

  # for name, port in ports: port_rtypes[ name ] = port

  # C: there is only combinational path from the input to the output
  # S: there is only sequential path from the input to the output
  # B: there are both seq and comb path from the input to the output
  for idx, (out, in_) in enumerate( ssg ):
    for in_port in in_:
      if in_port.startswith( ('S', 'B') ):
        seq_in_ports.add( in_port[1:] )
        seq_dep_outports.add( idx )

  # Purely combinational models do not need sequential blocks
  if len( seq_in_ports ) == 0: return '', []

  set_inputs = []
  constraints = []

  # Generate input assignments and constraints

  for in_port in seq_in_ports:
    # name = pymtl_name( in_port )
    name = in_port

    dtype = port_rtypes[ in_port ].get_dtype()

    set_inputs.extend( write_ffi_model_py(
      's._ffi_m.{name}', 's.{name}', name, dtype
    ) )

    constraints.append( 'U(tick_sequential) < WR(s.{}),'.format( name ) )

  make_indent( set_inputs, 3 )

  for outport in seq_dep_outports:
    constraints.append( 'U(tick_sequential) < U(readout_{}),'.format( outport ) )

  # Fill in the seq upblk template

  seq_upblk = seq_upblk_tplt.format( register_inputs = '\n'.join( set_inputs ) )

  return seq_upblk, constraints

#-------------------------------------------------------------------------
# generate_comb_upblks_py
#-------------------------------------------------------------------------
# Return a list of comb upblks in string.

def generate_comb_upblks_py( ports, ssg ):

  comb_upblk_tplt = """
    @s.update
    def comb_eval_{idx}():
      # set inputs
{set_inputs}
      # call evaluate function
      s._ffi_inst.eval( s._ffi_m )"""

  comb_ssg = []
  port_rtypes = {}
  port_rtypes.update( ports )

  # for name, port in ports: port_rtypes[ name ] = port

  # C: there is only combinational path from the input to the output
  # S: there is only sequential path from the input to the output
  # B: there are both seq and comb path from the input to the output
  for idx, (out, in_) in enumerate( ssg ):
    inports = []

    for in_port in in_:
      if in_port.startswith( ('C', 'B') ):
        inports.append( in_port[1:] )

    if len( inports ) != 0:
      comb_ssg.append( ( inports, out, idx ) )

  # Purely sequential models do not need combinational blocks
  if len( comb_ssg ) == 0: return '', []

  # Generate a list of comb upblks according to comb_ssg

  comb_upblks = []
  constraints = []

  for inports, outports, upblk_num in comb_ssg:
    set_inputs = []

    for in_port in inports:
      # name = pymtl_name(in_port)
      name = in_port

      dtype = port_rtypes[ in_port ].get_dtype()

      set_inputs.extend( write_ffi_model_py(
        's._ffi_m.{name}', 's.{name}', name, dtype
      ) )

      constraints.append( 'U(comb_eval_{upblk_num}) < WR(s.{name}),'.format(
        **locals()
      ) )

    make_indent( set_inputs, 3 )

    constraints.append(
      'U(comb_eval_{upblk_num}) < U(readout_{upblk_num}),'.format(**locals()) )

    # Fill in the comb upblk template

    comb_upblk = comb_upblk_tplt.format(
      idx = upblk_num, set_inputs = '\n'.join( set_inputs )
    )

    comb_upblks.append( comb_upblk )

  return comb_upblks, constraints

#-------------------------------------------------------------------------
# generate_readout_upblks_py
#-------------------------------------------------------------------------

def generate_readout_upblks_py( ports, ssg ):

  readout_upblks = []
  port_rtypes = {}
  port_rtypes.update( ports )
  constraints = []

  # for port in ports: port_rtypes[ port._dsl.my_name ] = port

  readout_tplt = """
    @s.update
    def readout_{idx}():
{read_outputs}"""

  for upblk_num, ( out, in_ ) in enumerate( ssg ):
    read_outputs = []

    for outport in out:
      # name = pymtl_name( outport )
      name = outport

      dtype = port_rtypes[ outport ].get_dtype()

      read_outputs.extend( read_ffi_model_py(
        's.{name}', 's._ffi_m.{rname}', name, dtype
      ) )
      # for idx, offset in get_indices( port_objs[ outport ] ):
        # read_outputs.append( 's.{name}{offset} = s._ffi_m.{name}[{idx}]'.format(
          # name = pymtl_name(outport), offset = offset, idx = idx
        # ) )

      constraints.append( 'U(readout_{upblk_num}) < RD(s.{name}),'.format(
        **locals()
      ) )

    make_indent( read_outputs, 3 )

    readout_upblk = readout_tplt.format(
      idx = upblk_num, read_outputs = '\n'.join( read_outputs )
    )

    readout_upblks.append( readout_upblk )

  return readout_upblks, constraints

#-------------------------------------------------------------------------
# generate_line_trace_py
#-------------------------------------------------------------------------
# A line trace that shows the value of all PyMTL wrapper ports

def generate_line_trace_py( ports ):

  ret = [ 'lt = ""' ]

  for name, port in ports:
    my_name = name
    full_name = 's.'+name
    # my_name = pymtl_name( port._dsl.my_name )
    # full_name = pymtl_name( port._dsl.full_name )
    ret.append(
      'lt += "{my_name} = {{}}, ".format({full_name})'.format(**locals())
    )

  ret.append( 'return lt' )

  make_indent( ret, 2 )

  return '\n'.join( ret )

#-------------------------------------------------------------------------
# generate_internal_line_trace_py
#-------------------------------------------------------------------------
# A line trace that shows the value of all cffi ports

def generate_internal_line_trace_py( ports ):

  ret = [ 'lt = ""' ]

  for name, port in ports:
    my_name = pymtl_name( name )
    # my_name = pymtl_name( port._dsl.my_name )
    ret.append(
      'lt += "{my_name} = {{}}, ".format(s._ffi_m.{my_name}[0])'.\
        format(**locals())
    )

  ret.append( 'return lt' )

  make_indent( ret, 2 )

  return '\n'.join( ret )

#-------------------------------------------------------------------------
# get_indices
#-------------------------------------------------------------------------
# Generate a list of idx-offset tuples to copy data from verilated
# model to PyMTL model.

def get_indices( port ):

  nbits = get_nbits( port )

  num_assigns = 1 if nbits <= 64 else (nbits-1)/32+1

  if num_assigns == 1:
    return [(0, '')]

  return [
    ( i, '[{}:{}]'.format( i*32, min( i*32+32, nbits ) ) ) \
    for i in range(num_assigns)
  ]
