#=========================================================================
# UpdatesConnection.py
#=========================================================================
# UpdatesConnection class supports connections of variables and explicit
# constraints between update blocks and the read and write of Connectable
# variables

import py.code
from collections     import defaultdict, deque
from PyMTLObject     import PyMTLObject
from UpdatesExpl     import UpdatesExpl, verbose
from ConstraintTypes import U, RD, WR, ValueConstraint
from Connectable     import Connectable, Wire
from ASTHelper       import get_ast, get_read_write, DetectReadsAndWrites

class UpdatesConnection( UpdatesExpl ):

  def __new__( cls, *args, **kwargs ):
    inst = super( UpdatesConnection, cls ).__new__( cls, *args, **kwargs )

    # These will be collected recursively
    inst._read_blks   = defaultdict(list)
    inst._read_expls  = defaultdict(list)
    inst._write_blks  = defaultdict(list)
    inst._write_expls = defaultdict(list)
    inst._id_obj      = dict()
    inst._varid_net   = dict()

    # These are only processed at the current level
    inst._blkid_reads  = defaultdict(list)
    inst._blkid_writes = defaultdict(list)
    return inst

  # Override
  def update( s, blk ):
    super( UpdatesConnection, s ).update( blk )

    # I parse the asts of upblks. To also cache them across different
    # instances of the same class, I attach them to the class object.
    if not "_blkid_ast" in type(s).__dict__:
      type(s)._blkid_ast = dict()
    if blk.__name__ not in type(s)._blkid_ast:
      type(s)._blkid_ast[ blk.__name__ ] = get_ast( blk )

    get_read_write( type(s)._blkid_ast[ blk.__name__ ], blk, \
                    s._blkid_reads[ id(blk) ], s._blkid_writes[ id(blk) ] )
    return blk

  # Override
  def add_constraints( s, *args ):
    for (x0, x1) in args:
      if   isinstance( x0, U ) and isinstance( x1, U ): # U & U
        s._expl_constraints.add( (id(x0.func), id(x1.func)) )
      elif isinstance( x0, ValueConstraint ) and isinstance( x1, ValueConstraint ):
        assert False, "Constraints between two variables are not allowed!"
      elif isinstance( x0, ValueConstraint ) or isinstance( x1, ValueConstraint ):
        sign = 1 # RD(x) < U(x) is 1, RD(x) > U(x) is -1
        if isinstance( x1, ValueConstraint ):
          sign = -1
          x0, x1 = x1, x0

        if isinstance( x0, RD ):
          s._read_expls[ id(x0.var) ].append( (sign, id(x1.func) ) )
        else:
          s._write_expls[ id(x0.var) ].append( ( sign, id(x1.func) ) )

  # This elaboration process goes back and forth between two nested dfs
  # functions. One dfs only traverse s.x.y, i.e. single field. The other
  # dfs is in charge of expanding the indices of array element.

  def _elaborate_vars( s ):

    # Find s.x[0][*][2]
    def expand_array_index( print_typ, obj, name_depth, name, idx_depth, idx, id_blks, id_obj, blk_id ):
      if idx_depth >= len(idx):
        lookup_var( print_typ, obj, name_depth+1, name, id_blks, id_obj, blk_id )
        return

      if isinstance( idx[idx_depth], int ): # handle x[2]'s case
        # if it's wire, we don't check len
        assert isinstance(obj, Wire) or idx[idx_depth] < len(obj), "Index out of bound. Check the declaration of %s" % (".".join([ x[0]+"".join(["[%s]"%str(y) for y in x[1]]) for x in name]))
        expand_array_index( print_typ, obj[ idx[idx_depth] ], name_depth, name, idx_depth+1, idx, id_blks, id_obj, blk_id )
      elif idx[idx_depth] == "*":
        for i in xrange(len(obj)):
          expand_array_index( print_typ, obj[i], name_depth, name, idx_depth+1, idx, id_blks, id_obj, blk_id )
      else:
        assert isinstance( idx[idx_depth], slice )
        expand_array_index( print_typ, obj[ idx[idx_depth] ], name_depth, name, idx_depth+1, idx, id_blks, id_obj, blk_id )

    # Add an array of objects, s.x = [ [ A() for _ in xrange(2) ] for _ in xrange(3) ]
    def add_all( obj, id_blks, id_obj, blk_id ):
      if isinstance( obj, Connectable ):
        id_blks[ id(obj) ].add( blk_id )
        id_obj [ id(obj) ] = obj
        return
      if isinstance( obj, list ) or isinstance( obj, deque ):
        for i in xrange(len(obj)):
          add_all( obj[i], id_blks, id_obj, blk_id )

    # Find the object s.a.b.c, if c is c[] then jump to expand_array_index
    def lookup_var( print_typ, obj, depth, name, id_blks, id_obj, blk_id ):
      if depth >= len(name):
        if not callable(obj): # exclude function calls
          if verbose: print " -", print_typ, name, type(obj), hex(id(obj)), "in blk:", hex(blk_id), s._blkid_upblk[blk_id].__name__
          add_all( obj, id_blks, id_obj, blk_id ) # if this object is a list/array again...
        return

      (field, idx) = name[ depth ]
      obj = getattr( obj, field )

      if not idx: # just a variable
        lookup_var( print_typ, obj, depth+1, name, id_blks, id_obj, blk_id )
      else: # let another function handle   s.x[4].y[*]
        # As long as the thing implements __getitem__, we don't check it.
        # assert isinstance( obj, list ) or isinstance( obj, deque ), "%s is %s, not a list" % (field, type(obj))
        expand_array_index( print_typ, obj, depth, name, 0, idx, id_blks, id_obj, blk_id )

    # First check if each read/write variable exists, then bind the actual
    # variable id (not name anymore) to upblks that reads/writes it.

    read_blks  = defaultdict(set)
    write_blks = defaultdict(set)
    id_obj     = dict()

    for blk_id, reads in s._blkid_reads.iteritems():
      for read_name in reads:
        lookup_var( "read", s, 0, read_name, read_blks, id_obj, blk_id )
    for i in read_blks:
      s._read_blks[i].extend( list( read_blks[i] ) )

    for blk_id, writes in s._blkid_writes.iteritems():
      for write_name in writes:
        lookup_var( "write", s, 0, write_name, write_blks, id_obj, blk_id )
    for i in write_blks:
      s._write_blks[i].extend( list( write_blks[i] ) )

    s._id_obj.update( id_obj )

  # Override
  def _synthesize_constraints( s ): # FIXME
    read_blks   = s._read_blks
    write_blks  = s._write_blks
    read_expls  = s._read_expls
    write_expls = s._write_expls

    for read, rd_expls in read_expls.iteritems():
      rd_blks = read_blks[ read ]

      for (sign, blk) in rd_expls:
        for rd_blk in rd_blks:
          if blk != rd_blk:
            if sign == 1: # sign=1 --> rd_blk<blk
              s._expl_constraints.add( (rd_blk, blk) )
            else: # sign=-1 --> blk<rd_blk
              s._expl_constraints.add( (blk, rd_blk) )

    for write, wr_expls in write_expls.iteritems():
      wr_blks = write_blks[ write ]

      for (sign, blk) in wr_expls:
        for wr_blk in wr_blks:
          if blk != wr_blk:
            if sign == 1: # sign=1 --> wr_blk<blk
              s._expl_constraints.add( (wr_blk, blk) )
            else: # sign=-1 --> blk<wr_blk
              s._expl_constraints.add( (blk, wr_blk) )

    s._total_constraints = s._expl_constraints.copy()

  # Override
  def _collect_child_vars( s, child ):
    super( UpdatesConnection, s )._collect_child_vars( child )

    if isinstance( child, UpdatesConnection ):
      for k in child._read_blks:
        s._read_blks[k].extend( child._read_blks[k] )
      for k in child._write_blks:
        s._write_blks[k].extend( child._write_blks[k] )

      for k in child._read_expls:
        s._read_expls[k].extend( child._read_expls[k] )
      for k in child._write_expls:
        s._write_expls[k].extend( child._write_expls[k] )

      s._id_obj.update( child._id_obj )
      s._varid_net.update( child._varid_net )

    if isinstance( child, Connectable ):
      child.collect_nets( s._varid_net )

  # Override
  def _elaborate( s ):

    def cleanup_connectables( parent ):
      if   isinstance( parent, list ): # check if iteratable
        for i in xrange(len(parent)):
          if isinstance( parent[i], Wire ):
            parent[i] = parent[i].default_value()
          else:
            cleanup_connectables( parent[i] )

      elif isinstance( parent, PyMTLObject ):
        for name, obj in parent.__dict__.iteritems():
          if not name.startswith("_"): # filter private variables
            if isinstance( obj, Wire ):
              setattr( parent, name, obj.default_value() )
            else:
              cleanup_connectables( obj )

    super( UpdatesConnection, s )._elaborate()
    s._resolve_var_connections()
    cleanup_connectables( s )

  def _resolve_var_connections( s ):

    # A writer of a net is one of the three: some signal itself, ancestor
    # of some signal, or descendant of some signal.
    #
    # We need to use an iterative algorithm to figure out the writer of
    # each net. The example is the following. Net 1's writer is s.x
    # and one of the reader is s.y. Net 2's writer is s.y.a but we know it
    # only after we figure out Net 1's writer, and one of the reader is
    # s.z. Net 3's writer is s.z.a but we only know it after we figure out
    # Net 2's writer, and so forth.

    # s.x will be propagated by WR s.x.a or WR s.x.b, but the propagated
    # s.x cannot propagate back to s.x.a or s.x.b
    # The original state is all the writers from all update blocks.

    obj_writer  = dict()
    propagatable = dict()

    for wid in s._write_blks:
      obj = s._id_obj[ wid ]
      obj_writer  [ id(obj) ] = obj
      propagatable[ id(obj) ] = True

      assert len( s._write_blks[ wid ] ) == 1, "%s is written in multiple update blocks.\n - %s" % \
            ( obj.full_name(), "\n - ".join([ s._blkid_upblk[x].__name__ for x in s._write_blks[ wid ] ]) )

      obj = obj._parent
      while obj:
        obj_writer  [ id(obj) ] = obj
        propagatable[ id(obj) ] = False
        obj = obj._parent

    headless = s._varid_net.values()
    frozen   = set()

    while headless:
      new_headless = []
      fcount = len(frozen)

      # For each net, figure out the writer among all vars and their
      # ancestors. Moreover, if x's ancestor has a writer in another net,
      # x should be the writer of this net.
      #
      # If there is a writer, propagate writer information to all readers
      # and readers' unfrozen ancestors. The propagation is tricky.
      # Assume s.x.a is in net, and s.x.b is written in upblk, s.x.b will
      # mark s.x as an unpropagatable writer, 

      for net in headless:
        has_writer, writer = False, None

        for v in net:
          obj = v
          while obj:
            oid = id(obj)
            if oid in obj_writer:
              owriter = obj_writer[ oid ]
              if obj == v or propagatable[ oid ]:
                assert not has_writer or id(v) == id(writer), \
                      "Two-writer conflict [%s] [%s] in the following net:\n - %s" % \
                      (v.full_name(), writer.full_name(), "\n - ".join([ x.full_name() for x in net ]))
                has_writer, writer = True, v
                break
            obj = obj._parent

        if has_writer:
          if id(writer) not in obj_writer: # child of some propagatable s.x
            wid = id(writer)
            obj_writer  [ wid ] = writer
            propagatable[ wid ] = True
            frozen.add  ( wid )

          for v in net:
            if v != writer:
              vid = id(v)
              obj_writer  [ vid ] = writer # My writer is the writer in the net
              propagatable[ vid ] = True
              frozen.add  ( vid )

              obj = v._parent
              while obj:
                oid = id(obj)
                if oid not in frozen:
                  obj_writer  [ oid ] = obj # Promote unfrozen ancestors to be a writer
                  propagatable[ oid ] = False # This writer information is not propagatable
                  frozen.add  ( oid )
                obj = obj._parent

        else:
          new_headless.append( net )

      assert fcount < len(frozen), "The following nets need drivers.\nNet:\n - %s " % ("\nNet:\n - ".join([ "\n - ".join([ x.full_name() for x in y ]) for y in headless ]))
      headless = new_headless

    for net in s._varid_net.values():
      has_writer, writer = False, None
      readers = []

      for v in net:
        v_writer = obj_writer[ id(v) ]
        if v_writer is not None and id(v_writer) != id(writer):
          assert not has_writer, "Two-writer conflict.\n - %s\n - %s" %(writer.full_name(), v.full_name())
          has_writer, writer = True, v_writer

        if id(v_writer) != id(v):
          readers.append( v )

      assert has_writer, "The following net needs a driver.\n - %s" % "\n - ".join([ x.full_name() for x in net ])

      # Writer means it is written somewhere else, so it will feed all other readers.
      # In these connection blocks, the writer's value is read by someone, i.e. v = writer

      # Optimization to reduce trace size:
      #
      # - Common writer: "x = s.x.y; s.a.b = x; s.b.c = x;" instead of
      #   "s.a.b = s.x.y; s.b.c = s.x.y"
      #
      # - Common prefix: grep the longest common prefix for readers
      #   "s.a.b = x; s.a.c = x" --> "y = s.a; y.b = x; y.c = x"

      upblk_name_ = "%s_FANOUT_%d" % (writer.full_name(), len(readers))
      upblk_name  = upblk_name_.replace( ".", "_" ) \
                               .replace( "[", "_" ).replace( "]", "_" ) \

      if len(readers) == 1:

        rstr = readers[0].full_name()
        wstr = writer.full_name()
        minlen = min( len(rstr), len(wstr) )

        LCP = 0
        while LCP <= minlen:
          if rstr[LCP] != wstr[LCP]:
            break
          LCP += 1

        while rstr[LCP-1] != ".": # s.mux and s.mustang's LCP can't be s.mu ..
          LCP -= 1

        if rstr[:LCP] == "s.":
          # Vanilla
          gen_connection_src = py.code.Source("""
            @s.update
            def {}():
              # The code below does the actual copy of variables.
              {} = {}

            """.format( upblk_name, rstr, wstr ) )
        else:
          # Apply common prefix
          gen_connection_src = py.code.Source("""
            @s.update
            def {}():
              # The code below does the actual copy of variables.
              y = {}; y.{} = y.{}

          """.format( upblk_name, rstr[:LCP-1], rstr[LCP:], wstr[LCP:]))

      else:
        strs   = []
        minlen = 1 << 31
        for x in readers:
          st = x.full_name()
          minlen = min( minlen, len(st) )
          strs.append( st )

        LCP = 0
        while LCP <= minlen:
          ch = strs[0][LCP]
          flag = True
          for j in xrange( 1, len(strs) ):
            if strs[j][LCP] != ch:
              flag = False
              break
          if not flag: break
          LCP += 1

        while strs[0][LCP-1] != ".": # s.mux and s.mustang's LCP can't be s.mu ..
          LCP -= 1

        if strs[0][:LCP] == "s.":
          # Only able to apply common writer optimization
          gen_connection_src = py.code.Source("""
            @s.update
            def {}():
              # The code below does the actual copy of variables.
              x = {}
              {}

          """.format( upblk_name, writer.full_name(),
                        "; ".join([ "{} = x".format(st) for st in strs ] ) ) )
        else:
          # Apply both common writer and common prefix
          gen_connection_src = py.code.Source("""
            @s.update
            def {}():
              # The code below does the actual copy of variables.
              x = {}; y = {}
              {}

          """.format( upblk_name, writer.full_name(), strs[0][:LCP-1],
                        "; ".join([ "y.{} = x".format( st[LCP:]) for st in strs ] ) ) )

      exec gen_connection_src.compile() in locals()

      upblk  = s._name_upblk[ upblk_name ]
      blk_id = id(upblk)
      s._read_blks[ id(writer) ].append(blk_id)
      s._id_obj[ id(writer) ] = writer
      for v in readers:
        s._write_blks[ id(v) ].append(blk_id)
        s._id_obj[ id(v) ] = v

      if verbose:
        print "Generate connection source: ", gen_connection_src
        print "+ Net", ("[%s]" % writer.full_name()).center(12), " Readers", [ x.full_name() for x in readers ]
