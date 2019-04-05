#=========================================================================
# StructuralRTLIRGenL4Pass.py
#=========================================================================
# This pass generates the structural RTLIR of a given component.
#
# Author : Shunning Jiang, Peitian Pan
# Date   : Apr 3, 2019

from StructuralRTLIRGenL3Pass import StructuralRTLIRGenL3Pass

class StructuralRTLIRGenL4Pass( StructuralRTLIRGenL3Pass ):

  # Override
  def __call__( s, top ):

    s.top = top
    s.gen_metadata( top )
    s.gen_rtlir_types( top )
    s.gen_constants( top )
    s.gen_connections( top )
    s.sort_connections( top )

  #-----------------------------------------------------------------------
  # gen_metadata
  #-----------------------------------------------------------------------

  def gen_metadata( s, m ):

    if not hasattr( m, '_pass_structural_rtlir_gen' ):

      m._pass_structural_rtlir_gen = PassMetadata()

    for child in m.get_child_components():

      s.gen_metadata( child )

  #-----------------------------------------------------------------------
  # gen_rtlir_types
  #-----------------------------------------------------------------------

  # Override
  def gen_rtlir_types( s, m ):

    m._pass_structural_rtlir_gen.rtlir_type = get_rtlir_type( m )

    for child in m.get_child_components():
      
      s.gen_rtlir_types( child )

  #-----------------------------------------------------------------------
  # gen_constants
  #-----------------------------------------------------------------------

  # Override
  def gen_constants( s, m ):

    ns = m._pass_structural_rtlir_gen
    ns.consts = []
    rtype = ns.rtlir_type
    const_types = rtype.get_consts()

    for const_name, const_rtype in const_types:

      assert const_name in m.__dict__
      const_instance = m.__dict__[ const_name ]
      ns.consts.append( ( const_name, const_rtype, const_instance ) )

    for child in m.get_child_components():

      s.gen_constants( child )

  #-----------------------------------------------------------------------
  # gen_connections
  #-----------------------------------------------------------------------
  # Generate connections based on the net structures. This function must
  # be called from the top component!

  # Override
  def gen_connections( s, top ):

    ns = top._pass_structural_rtlir_gen
    ns.connections_self_self = defaultdict( set )
    ns.connections_self_child = defaultdict( set )
    ns.connections_child_child = defaultdict( set )

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

              ns.connections_self_self[ writer_host ].add( ( u, v ) )

            elif writer_host_parent is reader_host:

              ns.connections_self_child[ reader_host ].add( ( u, v ) )

            elif writer_host is reader_host_parent:

              ns.connections_self_child[ writer_host ].add( ( u, v ) )

            elif writer_host_parent == reader_host_parent:

              ns.connections_child_child[ writer_host_parent ].add( ( u, v ) )

            else: assert False

  #-----------------------------------------------------------------------
  # sort_connections
  #-----------------------------------------------------------------------

  # Override
  def sort_connections( s, m ):

    ns = s.top._pass_structural_rtlir_gen

    m_conn = map( lambda x: (x, False), ns.connections_self_self[m] )
    m_conn.extend(map( lambda x: (x, False), ns.connections_self_child[m] ))
    m_conn.extend(map( lambda x: (x, False), ns.connections_child_child[m] ))

    connections = []

    for u, v in m.get_connect_order():

      for idx, ( ( wr, rd ), visited ) in enumerate( m_conn ):

        if ( ( s.contains( u, wr ) and s.contains( v, rd ) ) or\
           ( s.contains( u, rd ) and s.contains( v, wr ) ) ) and not visited:

          connections.append( ( wr, rd ) )
          m_conn[idx] = ( m_conn[idx][0], True )

    connections.extend(
      map( lambda x: x[0], filter( lambda x: not x[1], m_conn ) ) )

    m._pass_structural_rtlir_gen.connections = connections
