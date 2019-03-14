//========================================================================
// V{top_name}_v.cpp
//========================================================================
// This file provides a template for the C wrapper used in the import
// pass. The wrapper exposes a C interface to CFFI so that a
// Verilator-generated C++ model can be driven from Python.
// This templated is based on PyMTL v2.

#include "obj_dir_{top_name}/V{top_name}.h"
#include "stdio.h"
#include "stdint.h"
#include "verilated.h"
#include "verilated_vcd_c.h"

//------------------------------------------------------------------------
// CFFI Interface
//------------------------------------------------------------------------
// simulation methods and model interface ports exposed to CFFI

extern "C" {{
  typedef struct {{

    // Exposed port interface
    {port_externs}

    // Verilator model
    void * model;

  }} V{top_name}_t;

  // Exposed methods
  V{top_name}_t * create_model();
  void destroy_model( V{top_name}_t *);
  void eval( V{top_name}_t * );

}}

//------------------------------------------------------------------------
// sc_time_stamp
//------------------------------------------------------------------------
// Must be defined so the simulator knows the current time. Called by
// $time in Verilog. See:
// http://www.veripool.org/projects/verilator/wiki/Faq

vluint64_t g_main_time = 0;

double sc_time_stamp()
{{
  return g_main_time;
}}

//------------------------------------------------------------------------
// create_model()
//------------------------------------------------------------------------
// Construct a new verilator simulation, initialize interface signals
// exposed via CFFI, and setup VCD tracing if enabled.

V{top_name}_t * create_model() {{

  V{top_name}_t * m;
  V{top_name}   * model;

  Verilated::randReset( 0 );

  m     = (V{top_name}_t *) malloc( sizeof(V{top_name}_t) );
  model = new V{top_name}();

  m->model = (void *) model;

  // initialize exposed model interface pointers
{port_inits}

  return m;
}}

//------------------------------------------------------------------------
// destroy_model()
//------------------------------------------------------------------------
// Finalize the Verilator simulation, close files, call destructors.

void destroy_model( V{top_name}_t * m ) {{

  V{top_name} * model = (V{top_name} *) m->model;

  // finalize verilator simulation
  model->final();

  // TODO: this is probably a memory leak!
  //       But pypy segfaults if uncommented...
  //delete model;

}}

//------------------------------------------------------------------------
// eval()
//------------------------------------------------------------------------
// Simulate one time-step in the Verilated model.

void eval( V{top_name}_t * m ) {{

  V{top_name} * model = (V{top_name} *) m->model;

  // evaluate one time step
  model->eval();

}}

