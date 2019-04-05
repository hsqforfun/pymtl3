#=========================================================================
# StructuralRTLIRGenL1Pass.py
#=========================================================================
# This pass generates the structural RTLIR of a given component.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019

import ast, pymtl
from collections import defaultdict, deque
from pymtl.passes import BasePass, PassMetadata
from ..RTLIRType import *

class StructuralRTLIRGenL1Pass( BasePass ):

  def __call__( s, top ):
    """ generate structural RTLIR for component `top` """

    if not hasattr( top, '_pass_structural_rtlir_gen' ):

      top._pass_structural_rtlir_gen = PassMetadata()

    s.top = top
    s.gen_rtlir_types( top )
    s.gen_constants( top )
    s.gen_connections( top )
    s.sort_connections( top )

  #-----------------------------------------------------------------------
  # gen_rtlir_types
  #-----------------------------------------------------------------------

  def gen_rtlir_types( s, top ):

    top._pass_structural_rtlir_gen.rtlir_type = get_rtlir_type( top )

  #-----------------------------------------------------------------------
  # gen_constants
  #-----------------------------------------------------------------------

  def gen_constants( s, m ):

    ns = m._pass_structural_rtlir_gen
    ns.consts = []
    rtype = ns.rtlir_type
    const_types = rtype.get_consts()

    for const_name, const_rtype in const_types:

      assert const_name in m.__dict__
      const_instance = m.__dict__[ const_name ]
      ns.consts.append( ( const_name, const_rtype, const_instance ) )

  #-----------------------------------------------------------------------
  # gen_connections
  #-----------------------------------------------------------------------

  def gen_connections( s, top ):

    ns = top._pass_structural_rtlir_gen
    ns.connections_self_self = defaultdict( set )

    # Generate the connections assuming no sub-components

    nets = top.get_all_value_nets()
    adjs = top.get_signal_adjacency_dict()

    for writer, net in nets:

      S = deque( [ writer ] )
      visited = set( [ writer ] )

      while S:

        u = S.pop()
        writer_host        = u.get_host_component()
        writer_host_parent = writer_host.get_parent_object()

        for v in adjs[u]:

          if v not in visited:

            visited.add( v )
            S.append( v )
            reader_host        = v.get_host_component()
            reader_host_parent = reader_host.get_parent_object()

            # Four possible cases for the reader and writer signals:
            # 1.   They have the same host component. Both need 
            #       to be added to the host component.
            # 2/3. One's host component is the parent of the other.
            #       Both need to be added to the parent component.
            # 4.   They have the same parent component.
            #       Both need to be added to the parent component.

            if writer_host is reader_host:

              assert writer_host is top
              ns.connections_self_self[ writer_host ].add( ( u, v ) )

            else: assert False, "No sub-components are allowed at L1!"

  #-----------------------------------------------------------------------
  # sort_connections
  #-----------------------------------------------------------------------
  # At L1 every signal in the net corresponds to one `s.connect` statement

  def sort_connections( s, m ):

    ns = s.top._pass_structural_rtlir_gen

    m_connections = map( lambda x: (x, False), ns.connections_self_self[m] )
    # m_connections = ns.connections_self_self[m]
    # m_connections |= getattr(ns, 'connections_self_self', { m : set() })[m]
    # m_connections |= getattr(ns, 'connections_self_child', { m : set() })[m]
    # m_connections |= getattr(ns, 'connections_child_child', { m : set() })[m]

    connections = []

    for u, v in m.get_connect_order():

      for idx, (( wr, rd ), visited) in enumerate(m_connections):

        if ( ( s.contains( u, wr ) and s.contains( v, rd ) ) or\
           ( s.contains( u, rd ) and s.contains( v, wr ) ) ) and not visited:

          connections.append( ( wr, rd ) )
          m_connections[idx] = ( m_connections[idx][0], True )

    connections.extend(
      map( lambda x: x[0], filter( lambda x: not x[1], m_connections ) ) )

    m._pass_structural_rtlir_gen.connections = connections

  #-----------------------------------------------------------------------
  # contains
  #-----------------------------------------------------------------------

  def contains( s, obj, signal ):

    return obj == signal
