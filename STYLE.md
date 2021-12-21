Create new objects within collections using methods with the name of the
object:

    rs = rows()
    assert rs.count == 0

    r1 = rows.row()
    assert rs.count == 1
    assert rs.first is r1

Blocks that overflow 72 characters:
    
    def f(self,
        ..., ...
    ):

    ls = [x 
        for x in ...
    ]

    f(
        a, b, ...
    }
     
Sort imports alphabetically
