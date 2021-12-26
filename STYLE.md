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

@property getters and setters should have no prefix:
    
    @property
    def children
        ...

getter and setter methods should be prefixed with get and set:

    def getchildren(self, recursive)
        ...

    def setchildren(self, v)
        ...

generators shoud be prefixed with 'gen'

    def genchildren(self, recursive):
        ...


