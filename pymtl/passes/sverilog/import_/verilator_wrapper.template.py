#=========================================================================
# V{top_name}_v.py
#=========================================================================
# This wrapper makes a Verilator-generated C++ model appear as if it
# were a normal PyMTL model. This template is based on PyMTL v2.

import os

from cffi  import FFI

from pymtl import *

def get_bit_slice( num, start, stop ):

  return (num >> start) & (2**(stop-start)-1)

#-------------------------------------------------------------------------
# {top_name}
#-------------------------------------------------------------------------
class {top_name}( Component ):
  id_ = 0

  def __init__( s ):

    s._finalization_count = 0

    # initialize FFI, define the exposed interface
    s.ffi = FFI()
    s.ffi.cdef('''
      typedef struct {{

        // Exposed port interface
        {port_externs}

        // Verilator model
        void * model;

      }} V{top_name}_t;

      V{top_name}_t * create_model();
      void destroy_model( V{top_name}_t *);
      void eval( V{top_name}_t * );

    ''')

    # Import the shared library containing the model. We defer
    # construction to the elaborate_logic function to allow the user to
    # set the vcd_file.

    print 'Modification time of {{}}: {{}}'.format(
      '{lib_file}', os.path.getmtime( './{lib_file}' )
    )

    s._ffi_inst = s.ffi.dlopen('./{lib_file}')

    # dummy class to emulate PortBundles
    # class BundleProxy( PortBundle ):
      # flip = False

    # increment instance count
    {top_name}.id_ += 1

  def finalize( s ):
    assert s._finalization_count == 0,\
      'Imported component can only be finalized once!'
    s._finalization_count += 1
    s._ffi_inst.destroy_model( s._ffi_m )
    s.ffi.dlclose( s._ffi_inst )
    s.ffi = None
    s._ffi_inst = None

  def __del__( s ):
    if s._finalization_count == 0:
      s._finalization_count += 1
      s._ffi_inst.destroy_model( s._ffi_m )
      s.ffi.dlclose( s._ffi_inst )
      s.ffi = None
      s._ffi_inst = None

  def construct( s ):

    # Construct the model.

    s._ffi_m = s._ffi_inst.create_model()

    # define the port interface
{port_defs}

    {comb_upblks}
    
    {readout_upblks}

    {seq_upblk}

    {constraints}

  def line_trace( s ):
{line_trace}

  def internal_line_trace( s ):
{in_line_trace}
