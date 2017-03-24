#=========================================================================
# UpdatesExpl.py
#=========================================================================
# At the bottom level, we only have update blocks and explicit constraints
# between two update blocks/one update block. Basically this layer defines
# the scheduling policy/elaboration process.
# Each update block is called exactly once every cycle. PyMTL will
# schedule all update blocks based on the constraints. A total constraint
# between two update blocks specifies the order of the two blocks, i.e.
# call A before B.
# We collect one type of explicit constraints at this level:
# * Block constraint: s.add_constraints( U(upA) < U(upB) )

verbose = False
# verbose = True

import random, py.code
from PyMTLObject     import PyMTLObject
from collections     import defaultdict, deque
from ConstraintTypes import U

class UpdatesExpl( PyMTLObject ):

  def __new__( cls, *args, **kwargs ):
    inst = PyMTLObject.__new__( cls, *args, **kwargs )
    # These will be collected recursively
    inst._name_upblk       = {}
    inst._blkid_upblk      = {}
    inst._expl_constraints = set() # contains ( id(func), id(func) )s
    return inst

  def update( s, blk ):
    assert blk.__name__ not in s._name_upblk, ("Cannot declare two update blocks using the same name!")
    s._name_upblk[ blk.__name__ ] = s._blkid_upblk[ id(blk) ] = blk
    return blk

  def get_update_block( s, name ):
    return s._name_upblk[ name ]

  def add_constraints( s, *args ):
    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ):
        s._expl_constraints.add( (id(x0.func), id(x1.func)) )

  def _synthesize_constraints( s ):
    s._total_constraints = s._expl_constraints.copy()

  # Override
  def _collect_child_vars( s, child ):
    if isinstance( child, UpdatesExpl ):
      s._name_upblk.update( child._name_upblk )
      s._blkid_upblk.update( child._blkid_upblk )
      s._expl_constraints.update( child._expl_constraints )

  def _schedule( s ):

    if verbose:
      from graphviz import Digraph
      dot = Digraph(comment = s.__class__)
      dot.graph_attr["rank"] = "source"
      dot.graph_attr["ratio"] = "fill"
      dot.graph_attr["margin"] = "0.1"
      for (x, y) in s._total_constraints:
        dot.edge( s._blkid_upblk[x].__name__+"@"+hex(x), s._blkid_upblk[y].__name__+"@"+hex(y) )
      dot.render("/tmp/pymtl.gv", view=True)

    N = len( s._blkid_upblk )
    edges  = [ [] for _ in xrange(N) ]
    upblks = s._blkid_upblk.keys()
    InDeg  = [0] * N
    OutDeg = [0] * N

    # Discretize in O(NlogN), to avoid later O(logN) lookup

    id_vtx = dict()
    for i in xrange(N):
      id_vtx[ upblks[i] ] = i

    # Prepare the graph

    for (x, y) in list(s._total_constraints):
      vtx_x = id_vtx[ x ]
      vtx_y = id_vtx[ y ]
      edges [ vtx_x ].append( vtx_y )
      InDeg [ vtx_y ] += 1
      OutDeg[ vtx_x ] += 1

    # Perform topological sort in O(N+M). Note that this gives us a linear
    # schedule.

    Q = deque()
    for i in xrange(N):
      if InDeg[i] == 0:
        Q.append( i )
      assert InDeg[i]>0 or OutDeg[i]>0, "Update block \"%s\" has no constraint" % s._blkid_upblk[ upblks[i] ].__name__

    _schedule_list = []
    while Q:
      # random.shuffle(Q) # to catch corner cases; will be removed later

      u = Q.popleft() # bfs order is faster than dfs order
      _schedule_list.append( s._blkid_upblk[ upblks[u] ] )
      for v in edges[u]:
        InDeg[v] -= 1
        if InDeg[v] == 0:
          Q.append( v )

    s._schedule_list = _schedule_list

    assert len(s._schedule_list) == N, "Update blocks have cyclic dependencies."

    # + Berkin's recipe
    strs = map( "  update_blk{}()".format, xrange( len( _schedule_list ) ) )
    gen_schedule_src = py.code.Source("""
      {}
      def cycle():
        # The code below does the actual calling of update blocks.
        {}

      """.format( "; ".join( map(
                  "update_blk{0} = _schedule_list[{0}]".format,
                      xrange( len( _schedule_list ) ) ) ),
                  "\n        ".join( strs ) ) )

    if verbose: print "Generate schedule source: ", gen_schedule_src
    exec gen_schedule_src.compile() in locals()

    s.cycle = cycle

    if True:

      all_src = ""
      func_globals = dict()
      for x in _schedule_list:
        # Get the func source and object closure
        obj = x.func_closure[0].cell_contents if x.func_closure else s
        func_globals.update( x.func_globals )
        src = type(obj)._blkid_ast[ x.__name__ ][1]

        all_src += src[src.find(":")+1:].replace("\n    ","\n").replace("s.", obj.full_name()+".")

      gen_schedule_src = py.code.Source("""
      def cycle():
        # The code below does the actual calling of update blocks.
        {}

      """.format( all_src ) )
      exec gen_schedule_src.compile() in locals()

      cycle.func_globals.update( func_globals )
      print gen_schedule_src

      s.cycle = cycle

    # Maybe we can find some lightweight multi-threading library
    # Perform work partitioning to basically extract batches of frontiers
    # for parallelism

    InDeg = [0] * N
    for x in edges:
      for y in x:
        InDeg[y] += 1

    Q = deque()
    for i in xrange(N):
      if InDeg[i] == 0:
        Q.append( i )

    s._batch_schedule = []

    while Q:
      Q2 = deque()
      s._batch_schedule.append( [ s._blkid_upblk[ upblks[y] ] for y in Q ] )
      for u in Q:
        for v in edges[u]:
          InDeg[v] -= 1
          if InDeg[v] == 0:
            Q2.append( v )
      Q = Q2

  def elaborate( s ):
    s._elaborate()
    s._synthesize_constraints()
    s._schedule()

  def cycle( s ):
    print "Please elaborate before the simulation!"

  def print_schedule( s ):
    assert hasattr( s, "_schedule_list"), "Please elaborate before you print schedule!"
    print
    for (i, blk) in enumerate( s._schedule_list ):
      print i, blk.__name__
    for x in s._batch_schedule:
      print [ y.__name__ for y in x ]
