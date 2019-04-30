#=========================================================================
# ExternalSimSetup.py
#=========================================================================
# Setup the external simulation. For verilator, this includes calling
# verilator to compile the model, generating the C wrapper that provides
# interfaces, and compiling them into a shared lib. The C wrapper template
# and most of the code here are based on PyMTL v2.
# 
# Author : Peitian Pan
# Date   : Feb 22, 2019

import os, shutil, subprocess, copy

from pymtl.passes.sverilog.utility import make_indent

from errors  import VerilatorCompilationError, PyMTLImportError
from helpers import *

#-----------------------------------------------------------------------
# setup_external_sim
#-----------------------------------------------------------------------
# The entrance function to setup external simulation. `sv_name` is the
# SystemVerilog file name; `top_name` is the name of the top module;
# `ports` is a structure that contains all information about the
# module's ports.

def setup_external_sim( sv_name, top_name, ports ):

  create_verilator_model( sv_name, top_name )

  wrapper_name, port_cdefs = create_verilator_c_wrapper( top_name,
      ports )

  lib_name = create_shared_lib( wrapper_name, top_name )

  return lib_name, port_cdefs

#-----------------------------------------------------------------------
# create_verilator_model
#-----------------------------------------------------------------------
# Verilate the module with `top_name` in file `sv_name`.

def create_verilator_model( sv_name, top_name ):

  cmd = """verilator -cc {sv_name} -top-module {top_name}"""\
        """ --Mdir {obj_dir} -O3 {flags}"""

  obj_dir = 'obj_dir_' + top_name
  flags   = ' '.join( [
    '--unroll-count 1000000', '--unroll-stmts 1000000', '--assert',
    '-Wno-UNOPTFLAT', '-Wno-UNSIGNED',
  ] )

  cmd = cmd.format( **vars() )

  # Remove obj_dir if already exists
  # It is the place where the verilator output is stored

  if os.path.exists( obj_dir ):
    shutil.rmtree( obj_dir )

  # Try to call verilator

  print 'Modification timestamp of {}.sv: {}'.format(
      sv_name, os.path.getmtime( sv_name + '.sv' )
  )

  try:
    subprocess.check_output( cmd, stderr = subprocess.STDOUT, shell = True )

  except subprocess.CalledProcessError as e:

    raise VerilatorCompilationError(
      top_name,
      '    verilator command:\n    ' + cmd + '\n\n    ' + e.output
    )

#-----------------------------------------------------------------------
# create_verilator_c_wrapper
#-----------------------------------------------------------------------
# Create a C wrapper that calls verilator C API and provides interfaces
# that can be later called through CFFI.

def create_verilator_c_wrapper( top_name, ports ):

  # The template should be in the same directory as this file

  template_name =\
    os.path.dirname( os.path.abspath( __file__ ) ) +\
    os.path.sep + 'verilator_wrapper.template.c'

  wrapper_name = top_name + '_v.cpp'

  # Generate port decls for the verilated model in C

  port_cdefs = []

  for name, port in ports:
    
    port_cdefs.append( generate_signal_decl_c( name, port ) )

  port_externs = copy.copy( port_cdefs )
  make_indent( port_externs, 2 )
  port_externs = '\n'.join( port_externs )

  # Generate initialization stmts for in/out ports

  port_inits = []

  for name, port in ports:
    port_inits.extend( generate_signal_init_c( name, port ) )

  make_indent( port_inits, 1 )

  port_inits = '\n'.join( port_inits )

  # Generate debug prints

  port_print = []

  for name, port in ports:
    port_print.append( generate_signal_print_c( name, port ) )

  make_indent( port_print, 1 )

  port_print = '\n'.join( port_print )

  # Fill in the C wrapper template

  with open( template_name, 'r' ) as template:
    with open( wrapper_name, 'w' ) as output:

      c_wrapper = template.read()
      c_wrapper = c_wrapper.format( **locals() )

      output.write( c_wrapper )

  return wrapper_name, port_cdefs

#-----------------------------------------------------------------------
# create_shared_lib
#-----------------------------------------------------------------------
# Compile the verilated model and `wrapper_name` with top module 
# `top_name` into a shared lib.

def create_shared_lib( wrapper_name, top_name ):
  ''' compile the Cpp wrapper and verilated model into a shared lib '''

  lib_name = 'lib{}_v.so'.format( top_name )

  # Assume $PYMTL_VERILATOR_INCLUDE_DIR is defined

  verilator_include_dir = os.environ.get( 'PYMTL_VERILATOR_INCLUDE_DIR' )
  
  if verilator_include_dir is None:
    cmd = ['pkg-config', '--variable=includedir', 'verilator']

    try:
      verilator_include_dir = \
        subprocess.check_output( cmd, stderr=subprocess.STDOUT ).strip()

    except OSError:
      raise PyMTLImportError(
        top_name,
        """Cannot locate the include directory of verilator. Please make """
        """sure either $PYMTL_VERILATOR_INCLUDE_DIR is set or pkg-config """
        """has been configured properly!"""
      )

  include_dirs = [
    verilator_include_dir, 
    verilator_include_dir + '/vltstd',
  ]

  obj_dir_prefix = 'obj_dir_{}/V{}'.format( top_name, top_name )

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
          cpp_file = 'obj_dir_{}/{}.cpp'.format( top_name, filename )
          cpp_sources_list.append( cpp_file )

  # Complete the cpp sources file list

  cpp_sources_list += [
    obj_dir_prefix + '__Syms.cpp', 
    verilator_include_dir + '/verilated.cpp', 
    verilator_include_dir + '/verilated_dpi.cpp', 
    wrapper_name,
  ]

  # Call compiler with generated flags & dirs

  cmd = 'g++ {flags} {idirs} -o {ofile} {ifiles}'.format(
    flags  = '-O0 -fPIC -shared',
    idirs  = ' '.join( [ '-I' + d for d in include_dirs ] ),
    ofile  = lib_name,
    ifiles = ' '.join( cpp_sources_list )
  )

  # Try to call the C compiler

  print 'Modification timestamp of {}: {}'.format(
      wrapper_name, os.path.getmtime( wrapper_name )
  )

  try:
    subprocess.check_output( cmd, stderr = subprocess.STDOUT, shell = True )

  except subprocess.CalledProcessError as e:

    raise PyMTLImportError(
      top_name,
      '    C compiler command:\n    ' + cmd + '\n\n    ' + e.output
    )
  
  return lib_name
