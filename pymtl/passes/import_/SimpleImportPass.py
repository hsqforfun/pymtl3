#=========================================================================
# SimpleImportPass.py
#=========================================================================
# SimpleImportPass class imports a SystemVerilog source file back to a 
# PyMTL RTLComponent. It is meant to be used on files generated by 
# pymtl.passes.SystemVerilogTranslationPass. 
# 
# Author : Peitian Pan
# Date   : Oct 18, 2018

import os, re, sys, shutil 

from pymtl                    import *
from pymtl.passes             import BasePass, PassMetadata
from pymtl.passes.translation import collect_ports, generate_module_name

from ExternalSimSetup         import setup_external_sim
from PyMTLWrapperGen          import generate_py_wrapper

class SimpleImportPass( BasePass ):

  def __call__( s, model ):
    """Import a Verilog/SystemVerilog file. `model` is the PyMTL object
    to be imported."""

    try:
      model._pass_systemverilog_translation.translated

    except AttributeError:
      raise PyMTLImportError( model.__class__.__name__,
        'the target model instance should be translated first!' 
      )

    model._pass_simple_import = PassMetadata()

    # Assume the input verilog file and the top module has the same name 
    # as the class name of model
    
    sv_name  = model.__class__.__name__
    ssg_name = model.__class__.__name__ + '.ssg'
    # top_name = model.__class__.__name__
    top_name = generate_module_name( model )

    # Generate the interface structure

    interface =\
      collect_ports( model, InVPort ) + collect_ports( model, OutVPort )

    ports = sorted(
      model.get_input_value_ports() | model.get_output_value_ports(),
      key = repr
    )

    # Setup verilator

    lib_name, port_cdefs = setup_external_sim( sv_name, top_name, interface )

    # Create a python wrapper that can access the verilated model

    py_wrapper_name = generate_py_wrapper(
      interface, ports, top_name, lib_name, port_cdefs, ssg_name
    )

    py_wrapper = py_wrapper_name.split('.')[0]

    if py_wrapper in sys.modules:
      # We are (probably) in a test process that is repeatedly run
      # Reloading is needed since the user may have updated the source file

      exec( "reload( sys.modules['{py_wrapper}'] )".format( **locals() ) )
      exec(
        "ImportedModel=sys.modules['{py_wrapper}'].{top_name}".format(**locals())
      )

    else:
      # First time execution
      import_cmd = \
        'from {py_wrapper} import {top_name} as ImportedModel'.format(
          py_wrapper = py_wrapper, top_name   = top_name,
        )
      exec( import_cmd )

    model._pass_simple_import.imported_model = ImportedModel()
