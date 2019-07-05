"""
MIT License

Copyright (c) 2019 Jesse Hogan

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from articles import *
from configfile import configfile
from datetime import timezone, datetime
from entities import BrokenRulesError, rgetattr
from MySQLdb.constants.ER import BAD_TABLE_ERROR, DUP_ENTRY
from parties import *
from pdb import Pdb
from tester import *
from uuid import uuid4
from func import enumerate
import argparse
import dateutil
import decimal; dec=decimal.Decimal
import functools
import io
import MySQLdb
import _mysql_exceptions
import orm
import pathlib
import primative
import random
import re

# Set conditional break points
def B(x=True):
    if x: 
        #Pdb().set_trace(sys._getframe().f_back)
        from IPython.core.debugger import Tracer; 
        Tracer().debugger.set_trace(sys._getframe().f_back)

# We will use basic and supplementary multilingual plane UTF-8 characters when
# testing str attributes to ensure unicode is being supported.

# A two byte character from the Basic Multilingual Plane
Delta = bytes("\N{GREEK CAPITAL LETTER DELTA}", 'utf-8').decode()

# A three byte character
V = bytes("\N{ROMAN NUMERAL FIVE}", 'utf-8').decode()

# A four byte character from the Supplementary Multilingual Plane
Cunei_a = bytes("\N{CUNEIFORM SIGN A}", 'utf-8').decode()

def getattr(obj, attr, *args):
    # Redefine getattr() to support deep attribututes 
    # 
    # For example:
    #    Instead of this:
    #        entity.constituents.first.id
    #    we can do this:
    #        getattr(entity, 'constituents.first.id')

    def rgetattr(obj, attr):
        if obj:
            return builtins.getattr(obj, attr, *args)

        return None
    return functools.reduce(rgetattr, [obj] + attr.split('.'))

class locations(orm.entities):
    pass

class presentations(orm.entities):
    pass

class concerts(presentations):
    pass

class components(orm.entities):
    pass

class artifacts(orm.entities):
    pass

class artists(orm.entities):
    pass

class location(orm.entity):
    address     = str
    description = str

    @staticmethod
    def getvalid():
        loc = location()
        loc.description = uuid4().hex
        loc.address     = uuid4().hex
        return loc

class presentation(orm.entity):
    date         =  datetime
    name         =  orm.fieldmapping(str)
    description  =  str
    locations    =  locations
    components   =  components
    title        =  str,        orm.fulltext('title_desc',0)
    description1 =  str,        orm.fulltext('title_desc',1)

    @staticmethod
    def getvalid():
        pres = presentation()
        pres.name          =  uuid4().hex
        pres.description   =  uuid4().hex
        pres.description1  =  uuid4().hex
        pres.title         =  uuid4().hex
        return pres

class concert(presentation):
    @staticmethod
    def getvalid():
        pres = presentation.getvalid()
        conc = concert()
        conc.record = uuid4().hex
        conc.name = uuid4().hex
        conc.title = pres.title
        conc.description = pres.description
        conc.description1 = pres.description1
        return conc
    
    record = orm.fieldmapping(str)

    # tinyint
    ticketprice  =  orm.fieldmapping(int,  min=-128,      max=127)

    # mediumint
    attendees    =  orm.fieldmapping(int,  min=-8388608,  max=8388607)

    # tinyint unsigned
    duration     =  orm.fieldmapping(int,  min=0,         max=255)

    # mediumint unsigned
    capacity     =  orm.fieldmapping(int,  min=0,         max=16777215)

    # int unsigned
    externalid   =  orm.fieldmapping(int,  min=0,         max=4294967295)

    # bigint unsigned
    externalid1  =  orm.fieldmapping(int,  min=0,         max=(2**64)-1)

class component(orm.entity):
    @staticmethod
    def getvalid():
        comp = component()
        comp.name = uuid4().hex
        comp.digest = bytes([random.randint(0, 255) for _ in range(32)])
        return comp

    name    =  str
    weight  =  float,  8,   7
    height  =  float
    digest  =  bytes,  16,  255

    @orm.attr(float, 5, 1)
    def width(self):
        return attr(abs(attr()))

class artifact(orm.entity):
    def getvalid():
        fact = artifact()
        fact.title = uuid4().hex
        fact.description = uuid4().hex
        return fact

    title        =  str,        orm.fulltext('title_desc',0)
    description  =  str,        orm.fulltext('title_desc',1)
    weight       =  int,        -2**63,                       2**63-1
    abstract     =  bool
    price        =  dec
    components   =  components

class artist(orm.entity):
    firstname      =  str, orm.index('fullname', 1)
    lastname       =  str, orm.index('fullname', 0)
    lifeform       =  str
    weight         =  int, 0, 1000
    networth       =  int
    style          =  str, 1, 50
    dob            =  datetime
    password       =  bytes, 32, 32
    ssn            =  str, 11, 11, orm.index #  char
    locations      =  locations
    presentations  =  presentations

    # title here to be ambigous with artifact.title. It's purpose is to ensure
    # against ambiguity problems that may arise
    title          =  str, 0, 1
    phone2         =  str, 0, 1
    email_1        =  str, 0, 1

    # Bio's will be longtext. Any str where max > 65,535 can no longer be a
    # varchar, so we make it a longtext.
    bio = str, 1, 65535 + 1, orm.fulltext

    @staticmethod
    def getvalid():
        art = artist()
        art.firstname = 'Gary'
        art.lastname  = 'Yourofsky'
        art.lifeform  = uuid4().hex
        art.password  = bytes([random.randint(0, 255) for _ in range(32)])
        art.ssn       = '1' * 11
        art.phone     = '1' * 7
        art.email     = 'username@domain.tld'
        return art

    @orm.attr(int, 1000000, 9999999)
    def phone(self):
        phone = attr()
        if phone is None:
            return None
        # Strip non-numerics ( "(555)-555-555" -> "555555555" )

        if type(phone) is str and not phone.isnumeric():
            phone = re.sub('\D*', '', phone)

            # Cache in map so we don't have to do this every time the phone
            # attribute is read. (Normally, caching in the map would be needed
            # if the operation actually took a really long time.  The output
            # for the re.sub wouldn't typically need to be cached. This is
            # simply to test the attr() function's ability to set map values.)
            attr(phone)

        return attr()

    @orm.attr(str, 3, 254)
    def email(self):
        return attr().lower()

    # Though it seems logical that there would be mutator analog to the
    # accessor logic (used above for the 'phone' attr), there doesn't seem to
    # be a need for this. Conversions should be done in the accessor (as in the
    # 'phone' accessor above).  If functionality needs to run when a mutator is
    # called, this can be handled in an onaftervaluechange handler (though this
    # seems rare).  Since at the moment, no use-case can be imagined for
    # mutator @attr's, we should leave this unimplemented. If a use-case
    # presents itself, the below, commented-out code approximates how it should
    # look.  The 'setter' method in the 'Property' class here
    # https://docs.python.org/3/howto/descriptor.html#properties hints at how
    # this may be implemented in orm.attr.
    """
    @phone.setter(str)
    def phone(self,)
        self.orm.mappings('phone').value = v
    """

    def __init__(self, o=None):
        super().__init__(o)

        if self.orm.isnew:
            self.lifeform = 'organic'
            self.bio = None
            self.style = 'classicism'
            self._processing = False

    def clear(self):
        self.locations.clear()
        self.presentations.clear()

    @property
    def processing(self):
        return self._processing

    @processing.setter
    def processing(self, v):
        self._processing = v

    @property
    def fullname(self):
        return self.firstname + ' ' + self.lastname

    def __str__(self):
        return self.fullname
        
class artist_artifacts(orm.associations):
    pass

class artist_artifact(orm.association):
    artist    =  artist
    artifact  =  artifact
    role      =  str
    planet    =  str

    def __init__(self, o=None):
        self['planet'] = 'Earth'
        self._processing = False
        super().__init__(o)

    @staticmethod
    def getvalid():
        aa = artist_artifact()
        aa.role = uuid4().hex
        aa.timespan = uuid4().hex
        return aa

    # The duration an artist worked on an artifact
    @orm.attr(str)
    def timespan(self):
        return attr().replace(' ', '-')

    @property
    def processing(self):
        return self._processing

    @processing.setter
    def processing(self, v):
        self._processing = v

class singers(artists):
    pass

class singer(artist):
    voice    = str
    concerts = concerts

    @staticmethod
    def getvalid():
        super = singer.orm.super.getvalid()

        sng = singer()
        keymaps = (orm.primarykeyfieldmapping, orm.foreignkeyfieldmapping)
        for map in super.orm.mappings:
            if isinstance(map, orm.fieldmapping) and type(map) not in keymaps:
                setattr(sng, map.name, getattr(super, map.name))

        sng.voice     = uuid4().hex
        sng.register  = 'laryngealization'
        return sng

    @orm.attr(str)
    def register(self):
        v = self.orm.mappings['register'].value.lower()

        if v in ('laryngealization', 'pulse phonation', 'creak'):
            return 'vocal fry'
        if v in ('flute', 'whistle tone'):
            return 'whistle'
        return v

    def __init__(self, o=None):
        self._transmitting = False
        super().__init__(o)

    def clear(self):
        super().clear()
        self.concerts.clear()

    @property
    def transmitting(self):
        return self._transmitting

    @transmitting.setter
    def transmitting(self, v):
        self._transmitting = v

class issues(orm.entities):
    pass

class issue(orm.entity):
    @orm.attr(str)
    def raiseAttributeError(self):
        raise AttributeError()


class test_orm(tester):
    def __init__(self):
        super().__init__()
        self.chronicles = db.chronicles()
        db.chronicler.getinstance().chronicles.onadd += self._chronicler_onadd

        artist.reCREATE(recursive=True)
    
    def _chrons(self, e, op):
        chrons = self.chronicles.where('entity',  e)
        if not (chrons.hasone and chrons.first.op == op):
            self._failures += failure()

    def _chronicler_onadd(self, src, eargs):
        self.chronicles += eargs.entity
        #print(eargs.entity)

    def it_computes_abbreviation(self):
        es = orm.orm.getentitys() + orm.orm.getassociations()

        abbrs = [e.orm.abbreviation for e in es]
        abbrs1 = [e().orm.abbreviation for e in es]
        self.unique(abbrs)
        self.eq(abbrs, abbrs1)

        for i in range(10):
            self.eq(abbrs, [e.orm.abbreviation for e in es])
            self.eq(abbrs, [e().orm.abbreviation for e in es])

    def it_calls_count_on_class(self):
        cnt = 10
        for i in range(cnt):
            artist.getvalid().save()

        self.ge(artists.count, cnt)

        arts = artists()
        arts += artist.getvalid()
        arts.count

    def it_calls__str__on_entities(self):
        arts = artists()
        arts += artist.getvalid()
        arts += artist.getvalid()

        r = '%s object at %s count: %s\n' % (type(arts), 
                                             hex(id(arts)), 
                                             arts.count)
        for art in arts:
            r += '    ' + str(art) + '\n'
            
        self.eq(r, str(arts))

    def it_has_index(self):
        # TODO When DDL reading facilities are made available through the DDL
        # migration code, use them to ensure that artists.ssn and other indexed
        # columns are sucessfully being index in MySQL.
        ...

    def it_has_composite_index(self):
        # TODO When DDL reading facilities are made available through the DDL
        # migration code, use them to ensure that artist.firstname and 
        # artist.lastname share a composite index.
        ...

    def it_calls_createdat(self):
        art = artist.getvalid()
        self.none(art.createdat)
        
        # Ensure the createdat gets the current datetime

        # Strip seconds and microsecond for comparison
        expect = primative.datetime.utcnow().replace(microsecond=0, second=0)
        art.save()
        actual = art.createdat.replace(microsecond=0, second=0)

        art = artist(art.id)
        self.eq(expect, actual)

        # Ensure the createdat isn't change on subsequest saves
        art.firstname == uuid4().hex
        art.save()
        art1 = artist(art.id)
        self.eq(art.createdat, art1.createdat)

    def it_calls_updatedate(self):
        art = artist.getvalid()
        self.none(art.updatedat)
        
        # Ensure the updatedat gets the current datetime on creation

        # Strip seconds and microsecond for comparison
        expect = primative.datetime.utcnow().replace(microsecond=0, second=0)
        art.save()
        actual = art.updatedat.replace(microsecond=0, second=0)

        art = artist(art.id)
        self.eq(expect, actual)

        # Ensure the updatedat is change on subsequest saves
        art.firstname = uuid4().hex
        expected = art.updatedat
        art.save()
        art1 = artist(art.id)
        self.gt(art.updatedat, expected)

    def it_cant_instantiate_entities(self):
        ''' Since orm.entities() wouldn't have an orm property (since a
        subclass hasn't invoked the metaclass code that would assign it the orm
        property), generic entities collections shouldn't be allowed. They
        should basically be considered abstract. '''
        self.expect(NotImplementedError, lambda: orm.entities())

    def it_calls__str__on_entity(self):
        art = artist.getvalid()
        self.eq(art.fullname, str(art))
        
    def it_has_static_composites_reference(self):
        comps = location.orm.composites
        es = [x.entity for x in comps]
        self.two(comps)
        self.true(presentation in es)
        self.true(artist in es)

        comps = presentation.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artist)

        comps = artifact.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artist)

        comps = artist.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artifact)

        comps = singer.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artifact)

        comps = concert.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, singer)

    def it_has_static_constituents_reference(self):
        consts = [x.entity for x in artist.orm.constituents]
        self.three(consts)
        self.true(presentation in consts)
        self.true(artifact     in consts)
        self.true(location     in consts)

        consts = artist.orm.constituents['presentation'].orm.constituents
        self.two(consts)
        consts.sort('name')
        self.is_(consts.first.entity, component)
        self.is_(consts.second.entity, location)

        consts = artifact.orm.constituents
        self.two(consts)

        consts.sort('name')
        self.is_(consts.first.entity, artist)
        self.is_(consts.second.entity, component)

    def it_has_static_super_references(self):
        self.is_(artist, singer.orm.super)

    def it_loads_and_saves_multicomposite_entity(self):
        chrons = self.chronicles

        # Create artist with presentation with empty locations and
        # presentations, reload and test
        art = artist.getvalid()
        pres = presentation.getvalid()

        self.zero(art.locations)
        self.zero(pres.locations)
        self.isnot(art.locations, pres.locations)

        art.presentations += pres

        chrons.clear()
        art.save()
        self.two(chrons)
        self._chrons(art, 'create')
        self._chrons(pres, 'create')

        art = artist(art.id)
        
        self.zero(art.presentations.first.locations)
        self.zero(art.locations)

        # Add locations, save, test, reload, test
        art.locations += location.getvalid()
        art.presentations.first.locations += location.getvalid()

        chrons.clear()
        art.save()
        self.two(chrons)
        self._chrons(art.locations.first,                     'create')
        self._chrons(art.presentations.first.locations.first, 'create')

        art1 = artist(art.id)

        chrons.clear()
        self.eq(art.locations.first.id, art1.locations.first.id)
        self.eq(art.presentations.first.locations.first.id, 
                art1.presentations.first.locations.first.id)

        self.three(chrons)
        self._chrons(art1.presentations,                  'retrieve')
        self._chrons(art1.presentations.first.locations,  'retrieve')
        self._chrons(art1.locations,                      'retrieve')

    def it_loads_and_saves_multicomposite_subentity(self):
        chrons = self.chronicles

        # Create singer with concert with empty locations and
        # concerts, reload and test
        sng = singer.getvalid()
        conc = concert.getvalid()

        self.zero(sng.locations)
        self.zero(conc.locations)
        self.isnot(sng.locations, conc.locations)

        sng.concerts += conc

        chrons.clear()
        sng.save()
        self.four(chrons)
        self._chrons(sng, 'create')
        self._chrons(conc, 'create')
        self._chrons(sng.orm.super, 'create')
        self._chrons(conc.orm.super, 'create')

        sng = singer(sng.id)
        
        self.zero(sng.concerts.first.locations)
        self.zero(sng.locations)

        # Add locations, save, test, reload, test
        sng.locations += location.getvalid()
        sng.concerts.first.locations += location.getvalid()

        chrons.clear()
        sng.save()
        self.two(chrons)
        self._chrons(sng.locations.first, 'create')
        self._chrons(sng.concerts.first.locations.first, 'create')

        sng1 = singer(sng.id)

        chrons.clear()

        self.eq(sng.locations.first.id, sng1.locations.first.id)
        self.eq(sng.concerts.first.locations.first.id, 
                sng1.concerts.first.locations.first.id)

        self.five(chrons)
        self._chrons(sng1.concerts,                  'retrieve')
        self._chrons(sng1.concerts.first.orm.super,  'retrieve')
        self._chrons(sng1.concerts.first.locations,  'retrieve')
        self._chrons(sng1.locations,                 'retrieve')

        # NOTE Loading locations requires that we load singer's superentity
        # (artist) first because `locations` is a constituent of `artist`.
        # Though this may seem ineffecient, since the orm has what it needs to
        # load `locations` without loading `artist`, we would want the
        # following to work for the sake of predictability:
        #
        #     assert sng1.locations.artists is sng1.orm.super
        #
        self._chrons(sng1.locations.artist,          'retrieve')

        chrons.clear()
        self.is_(sng1.locations.artist, sng1.orm.super)
        self.zero(chrons)

    def it_receives_AttributeError_from_explicit_attributes(self):
        # An issue was discovered in the former entities.__getattr__. When an
        # explicit attribute raised an AttributeError, the __getttr__ was
        # invoked (this is the reason it gets invoke in the first place) and
        # returned the map.value of the attribute. The effect was that the
        # explict attribute never had a chance to run, so we got whatever
        # was in map.value.
        #
        # To correct this, the __getattr__ was converted to a __getattribute__,
        # and some adjustments were made (map.isexplicit was added). Now, an
        # explicit attribute can raise an AttributeError and it bubble up
        # correctly (as confirmed by this test). The problem isn't likely to
        # resurface. However, this test was written just as a way to ensure the
        # issue never comes up again. The `issue` entity class was created for
        # this test because adding the `raiseAttributeError` explicit attribute
        # to other classes cause an AttributeError to be raise when the the
        # brokenrules logic was invoked, which broke a lot of tests.
        iss = issue()
        self.expect(AttributeError, lambda: iss.raiseAttributeError)

    def it_loads_and_saves_associations(self):
        # TODO Test loading and saving deeply nested associations
        chrons = self.chronicles
        
        chrons.clear()
        art = artist.getvalid()

        self.zero(chrons)

        aa = art.artist_artifacts
        self.zero(aa)

        # Ensure property caches
        self.is_(aa, art.artist_artifacts)

        # Test loading associated collection
        facts = art.artifacts
        self.zero(facts)

        # Ensure property caches
        self.is_(facts, art.artifacts)

        # Ensure the association's associated collections is the same as the
        # associated collection of the entity.
        self.is_(art.artifacts, art.artist_artifacts.artifacts)

        self.is_(art, art.artist_artifacts.artist)

        # Save and load an association
        art                   =   artist.getvalid()
        fact                  =   artifact.getvalid()
        aa                    =   artist_artifact.getvalid()
        aa.role               =   uuid4().hex
        aa.artifact           =   fact
        art.artist_artifacts  +=  aa

        self.is_(fact,    art.artist_artifacts.first.artifact)
        self.is_(art,     art.artist_artifacts.first.artist)
        self.eq(aa.role,  art.artist_artifacts.first.role)
        self.one(art.artist_artifacts)
        self.one(art.artifacts)

        chrons.clear()
        art.save()

        self.three(chrons)
        self.three(chrons.where('create'))
        self.one(chrons.where('entity', art))
        self.one(chrons.where('entity', aa))
        self.one(chrons.where('entity', fact))

        chrons.clear()
        art1 = artist(art.id)

        self.one(chrons)
        self.one(chrons.where('retrieve'))
        self.one(chrons.where('entity', art1))

        self.one(art1.artist_artifacts)
        self.one(art1.artifacts)

        aa1 = art1.artist_artifacts.first

        self.eq(art.id,          art1.id)
        self.eq(aa.id,           aa1.id)
        self.eq(aa.role,         aa1.role)

        self.eq(aa.artist.id,    aa1.artist.id)
        self.eq(aa.artistid,     aa1.artistid)

        self.eq(aa.artifact.id,  aa1.artifact.id)
        self.eq(aa.artifactid,   aa1.artifactid)

        # Add as second artist_artifact, save, reload and test
        aa2 = artist_artifact.getvalid()
        aa2.artifact = artifact.getvalid()

        art1.artist_artifacts += aa2

        chrons.clear()
        art1.save()

        self.two(chrons)
        self.two(chrons.where('create'))
        self.one(chrons.where('entity', aa2))
        self.one(chrons.where('entity', aa2.artifact))

        art2 = artist(art1.id)
        self.eq(art1.id,         art2.id)

        aas1=art1.artist_artifacts.sorted('role')
        aas2=art2.artist_artifacts.sorted('role')

        for aa1, aa2 in zip(aas1, aas2):

            self.eq(aa1.id,           aa2.id)
            self.eq(aa1.role,         aa2.role)

            self.eq(aa1.artist.id,    aa2.artist.id)
            self.eq(aa1.artistid,     aa2.artistid)

            self.eq(aa1.artifact.id,  aa2.artifact.id)
            self.eq(aa1.artifactid,   aa2.artifactid)

        # Add a third artifact to artist's pseudo-collection.
        # Save, reload and test.
        art2.artifacts += artifact.getvalid()
        art2.artist_artifacts.last.role = uuid4().hex
        art2.artist_artifacts.last.planet = uuid4().hex
        art2.artist_artifacts.last.timespan = uuid4().hex
        self.three(art2.artifacts)
        self.three(art2.artist_artifacts)

        chrons.clear()
        art2.save()
        self.two(chrons)
        self.two(chrons.where('create'))
        self.one(chrons.where('entity', art2.artist_artifacts.third))
        self.one(chrons.where('entity', art2.artist_artifacts.third.artifact))

        art3 = artist(art2.id)

        self.three(art3.artifacts)
        self.three(art3.artist_artifacts)

        aas2 = art2.artist_artifacts.sorted('role')
        aas3 = art3.artist_artifacts.sorted('role')

        for aa2, aa3 in zip(aas2, aas3):
            self.eq(aa2.id,           aa3.id)
            self.eq(aa2.role,         aa3.role)

            self.eq(aa2.artist.id,    aa3.artist.id)
            self.eq(aa2.artistid,     aa3.artistid)

            self.eq(aa2.artifact.id,  aa3.artifact.id)
            self.eq(aa2.artifactid,   aa3.artifactid)

        # Add two components to the artifact's components collection
        comps3 = components()
        for _ in range(2):
            comps3 += component.getvalid()

        comps3.sort()
        art3.artist_artifacts.first.artifact.components += comps3.first
        art3.artifacts.first.components += comps3.second

        self.two(art3.artist_artifacts.first.artifact.components)
        self.two(art3.artifacts.first.components)

        self.is_(comps3[0], art3.artist_artifacts.first.artifact.components[0])
        self.is_(comps3[1], art3.artist_artifacts.first.artifact.components[1])
        self.is_(comps3[0], art3.artifacts.first.components[0])
        self.is_(comps3[1], art3.artifacts.first.components[1])

        chrons.clear()
        art3.save()

        self.two(chrons)
        self.two(chrons.where('create'))
        self.one(chrons.where('entity', comps3.first))
        self.one(chrons.where('entity', comps3.second))

        art4 = artist(art3.id)
        comps4 = art4.artist_artifacts.first.artifact.components.sorted('id')

        self.two(comps4)
        self.eq(comps4.first.id, comps3.first.id)
        self.eq(comps4.second.id, comps3.second.id)

    def it_updates_associations_constituent_entity(self):
        art = artist.getvalid()
        chrons = self.chronicles

        for i in range(2):
            aa = artist_artifact.getvalid()
            aa.artifact = artifact.getvalid()
            art.artist_artifacts += aa

        art.save()

        art1 = artist(art.id)

        for fact in art1.artifacts:
            fact.title = uuid4().hex

        # Save and reload
        self.chronicles.clear()
        art1.save()

        # Ensure the four entities where updated
        self.two(chrons)
        self.two(chrons.where('update'))
        self.one(chrons.where('entity', art1.artifacts.first))
        self.one(chrons.where('entity', art1.artifacts.second))
        
        art2 = artist(art1.id)

        self.two(art1.artifacts)
        self.two(art2.artifacts)

        facts  = art. artifacts.sorted('title')
        facts1 = art1.artifacts.sorted('title')
        facts2 = art2.artifacts.sorted('title')

        for f, f2 in zip(facts, facts2):
            self.ne(f.title, f2.title)

        for f1, f2 in zip(facts1, facts2):
            self.eq(f1.title, f2.title)

        attrs = 'artifacts.first.components', \
               'artist_artifacts.first.artifact.components'

        for attr in attrs:
            comps = getattr(art2, attr)
            comps += component.getvalid()

        art2.save()

        art3 = artist(art2.id)

        for attr in attrs:
            comps = getattr(art3, attr)
            for comp in comps:
                comp.name = uuid4().hex

        chrons.clear()
        art3.save()

        self.two(chrons)
        self.two(chrons.where('update'))
        self.one(chrons.where('entity', art3.artifacts.first.components.first))
        self.one(chrons.where('entity', art3.artifacts.first.components.second))

        art4 = artist(art3.id)

        for attr in attrs:
            comps2 = getattr(art2, attr)
            comps3 = getattr(art3, attr)
            comps4 = getattr(art4, attr)

            self.two(comps2)
            self.two(comps3)
            self.two(comps4)

            for comp4 in comps4:
                for comp2 in comps2:
                    self.ne(comp2.name, comp4.name)

            for comp4 in comps4:
                for comp3 in comps3:
                    if comp4.name == comp3.name:
                        break
                else:
                    self.fail('No match within comps4 and comps3')

        # TODO Test deeply nested associations

    def it_updates_association(self):
        chrons = self.chronicles

        art = artist.getvalid()

        for i in range(2):
            aa = artist_artifact.getvalid()
            aa.artifact = artifact.getvalid()
            art.artist_artifacts += aa

        art.save()

        art1 = artist(art.id)

        for aa in art1.artist_artifacts:
            aa.role = uuid4().hex

        # Save and reload
        chrons.clear()
        art1.save()

        self.two(chrons)
        self.two(chrons.where('update'))
        self.one(chrons.where('entity', art1.artist_artifacts.first))
        self.one(chrons.where('entity', art1.artist_artifacts.first))

        art2 = artist(art1.id)

        aas  = art. artist_artifacts.sorted('role')
        aas1 = art1.artist_artifacts.sorted('role')
        aas2 = art2.artist_artifacts.sorted('role')

        for aa, aa2 in zip(aas, aas2):
            self.ne(aa.role, aa2.role)

        for aa1, aa2 in zip(aas1, aas2):
            self.eq(aa1.role, aa2.role)

        # TODO Test deeply nested associations

    def it_removes_associations(self):
        chrons = self.chronicles

        for removeby in 'pseudo-collection', 'association':
            art = artist.getvalid()

            for i in range(2):
                aa = artist_artifact.getvalid()
                aa.artifact = artifact.getvalid()
                aa.artifact.components += component.getvalid()
                art.artist_artifacts += aa
                art.artist_artifacts.last.artifact.components += component.getvalid()

            art.save()

            art = artist(art.id)
            
            self.two(art.artist_artifacts)
            self.zero(art.artist_artifacts.orm.trash)
            self.two(art.artifacts)
            self.zero(art.artifacts.orm.trash)

            if removeby == 'pseudo-collection':
                rmfact = art.artifacts.shift()
            elif removeby == 'association':
                rmfact = art.artist_artifacts.shift().artifact

            rmcomps = rmfact.components

            rmaa = art.artist_artifacts.orm.trash.first

            self.one(art.artist_artifacts)
            self.one(art.artist_artifacts.orm.trash)
            self.one(art.artifacts)
            self.one(art.artifacts.orm.trash)

            for f1, f2 in zip(art.artifacts, art.artist_artifacts.artifacts):
                self.isnot(f1, rmfact)
                self.isnot(f2, rmfact)

            chrons.clear()
            art.save()

            self.four(chrons)
            self.four(chrons.where('delete'))
            self.one(chrons.where('entity', rmcomps.first))
            self.one(chrons.where('entity', rmcomps.second))
            self.one(chrons.where('entity', rmfact))
            self.one(chrons.where('entity', art.artist_artifacts.orm.trash.first))


            art1 = artist(art.id)

            self.one(art1.artist_artifacts)
            self.zero(art1.artist_artifacts.orm.trash)
            self.one(art1.artifacts)
            self.zero(art1.artifacts.orm.trash)
                
            aas = art.artist_artifacts.sorted('role')
            aas1 = art1.artist_artifacts.sorted('role')

            for aa, aa1 in zip(aas, aas1):
                self.eq(aa.id,           aa1.id)
                self.eq(aa.role,         aa1.role)

                self.eq(aa.artist.id,    aa1.artist.id)
                self.eq(aa.artistid,     aa1.artistid)

                self.eq(aa.artifact.id,  aa1.artifact.id)
                self.eq(aa.artifactid,   aa1.artifactid)

            for fact in art1.artifacts:
                self.ne(rmfact.id, fact.id)

            self.expect(db.RecordNotFoundError, lambda: artist_artifact(rmaa.id))
            self.expect(db.RecordNotFoundError, lambda: artifact(rmfact.id))

            for comp in rmcomps:
                self.expect(db.RecordNotFoundError, lambda: component(comp.id))

        # TODO Test deeply nested associations

    def it_rollsback_save_with_broken_trash(self):
        art = artist.getvalid()
        art.presentations += presentation.getvalid()
        art.save()

        art = artist(art.id)
        art.presentations.pop()

        self.zero(art.presentations)
        self.one(art.presentations.orm.trash)

        artst     =  art.orm.persistencestate
        presssts  =  art.presentations.orm.trash.orm.persistencestates

        # Break save method
        pres = art.presentations.orm.trash.first
        save, pres._save = pres._save, lambda cur: 0/0

        self.expect(ZeroDivisionError, lambda: art.save())

        self.eq(artst,     art.orm.persistencestate)
        self.eq(presssts,  art.presentations.orm.trash.orm.persistencestates)

        # Restore unbroken save method
        pres._save = save
        trashid = art.presentations.orm.trash.first.id

        art.save()

        self.zero(artist(art.id).presentations)

        self.expect(db.RecordNotFoundError, lambda: presentation(trashid))

        # Test associations
        art = artist.getvalid()
        art.artifacts += artifact.getvalid()
        factid = art.artifacts.first.id
        aa = art.artist_artifacts.first
        aaid = aa.id
        aa.role = uuid4().hex
        aa.timespan = uuid4().hex

        art.save()

        art = artist(art.id)
        art.artifacts.pop()

        aatrash = art.artist_artifacts.orm.trash
        artst    =  art.orm.persistencestate
        aasts    =  aatrash.orm.persistencestates
        aassts   =  aatrash.first.orm.trash.orm.persistencestates
        factssts =  art.artifacts.orm.trash.orm.persistencestates

        self.zero(art.artifacts)
        self.one(art.artist_artifacts.orm.trash)
        self.one(art.artifacts.orm.trash)

        # Break save method
        fn = lambda cur, follow: 0/0
        save = art.artist_artifacts.orm.trash.first._save
        art.artist_artifacts.orm.trash.first._save = fn

        self.expect(ZeroDivisionError, lambda: art.save())

        aatrash = art.artist_artifacts.orm.trash

        self.eq(artst,     art.orm.persistencestate)
        self.eq(aasts,     aatrash.orm.persistencestates)
        self.eq(aassts,    aatrash.first.orm.trash.orm.persistencestates)
        self.eq(factssts,  art.artifacts.orm.trash.orm.persistencestates)

        self.zero(art.artifacts)
        self.one(art.artist_artifacts.orm.trash)
        self.one(art.artifacts.orm.trash)
        self.one(artist(art.id).artifacts)
        self.one(artist(art.id).artist_artifacts)

        # Restore unbroken save method
        art.artist_artifacts.orm.trash.first._save = save

        art.save()
        self.zero(artist(art.id).artifacts)
        self.zero(artist(art.id).artist_artifacts)

        self.expect(db.RecordNotFoundError, lambda: artist_artifact(aa.id))
        self.expect(db.RecordNotFoundError, lambda: artifact(factid))

    def it_raises_error_on_invalid_attributes_of_associations(self):
        art = artist()
        self.expect(AttributeError, lambda: art.artist_artifacts.artifactsX)

    def it_has_broken_rules_of_constituents(self):
        art                =   artist.getvalid()
        pres               =   presentation.getvalid()
        loc                =   location.getvalid()
        pres.locations     +=  loc
        art.presentations  +=  pres

        # Break the max-size rule on presentation.name
        pres.name = 'x' * (presentation.orm.mappings['name'].max + 1)

        self.one(art.brokenrules)
        self.broken(art, 'name', 'fits')

        # Break deeply (>2) nested constituent
        # Break the max-size rule on location.description

        loc.description = 'x' * (location.orm.mappings['description'].max + 1)
        self.two(art.brokenrules)
        self.broken(art, 'description', 'fits')

        # unbreak
        loc.description = 'x' * location.orm.mappings['description'].min
        pres.name =       'x' * presentation.orm.mappings['name'].min
        self.zero(art.brokenrules)

        # The artist_artifact created when assigning a valid artifact will
        # itself have two broken rules by default. Make sure they bubble up to
        # art.
        art.artifacts += artifact.getvalid()
        self.two(art.brokenrules)
        self.broken(art, 'timespan', 'fits')
        self.broken(art, 'role',     'fits')

        # Fix the artist_artifact
        art.artist_artifacts.first.role     = uuid4().hex
        art.artist_artifacts.first.timespan = uuid4().hex
        self.true(art.isvalid) # Ensure fixed

        # Break an artifact and ensure the brokenrule bubbles up to art
        art.artifacts.first.weight = uuid4().hex # break
        self.one(art.brokenrules)
        self.broken(art, 'weight', 'valid')

    def it_moves_constituent_to_a_different_composite(self):
        chrons = self.chronicles

        # Persist an art with a pres
        art = artist.getvalid()
        art.presentations += presentation.getvalid()
        art.presentations.last.name = uuid4().hex
        art.save()

        # Give the pres to a new artist (art1)
        art1 = artist.getvalid()
        art.presentations.give(art1.presentations)

        # Ensure the move was made in memory
        self.zero(art.presentations)
        self.one(art1.presentations)
        
        # Save art1 and ensure the pres's artistid is art1.id
        chrons.clear()
        art1.save()

        self.two(chrons)
        self.one(chrons.where('entity', art1))
        self.one(chrons.where('entity', art1.presentations.first))

        self.zero(artist(art.id).presentations)
        self.one(artist(art1.id).presentations)

        # Move deeply nested entity

        # Create and save a new location
        art1.presentations.first.locations += location.getvalid()

        art1.save()

        # Create a new presentation and give the location in art1 to the
        # locations collection of art.
        art.presentations += presentation.getvalid()
        art1.presentations.first.locations.give(art.presentations.last.locations)

        chrons.clear()
        art.save()

        self.two(chrons)

        loc = art.presentations.last.locations.last
        pres = art.presentations.last

        self.eq(chrons.where('entity', pres).first.op, 'create')
        self.eq(chrons.where('entity', loc).first.op, 'update')

        self.zero(artist(art1.id).presentations.first.locations)
        self.one(artist(art.id).presentations.first.locations)

    def it_calls_count_on_streamed_entities(self):
        arts1 = artists()
        firstname = uuid4().hex
        for i in range(2):
            art = artist.getvalid()
            art.firstname = firstname
            arts1 += art
            art.save()

        arts = artists(orm.stream, firstname=firstname)
        self.true(arts.orm.isstreaming)
        self.eq(2, arts.count)

        # Ensure count works in nonstreaming mode
        self.false(arts1.orm.isstreaming)
        self.eq(2, arts1.count)

    def it_raises_exception_when_innerjoin_stream_entities(self):
        ''' Streaming and joins don't mix. An error should be thrown
        if an attempt to stream joins is detected. The proper way 
        to stream constituents would probably be with a getter, e.g.:

            for fact in art.get_artifacts(orm.stream):
                ...

        '''

        fns = (
            lambda:  artists(orm.stream).join(locations()),
            lambda:  artists()            &  locations(orm.stream),

            lambda:  artists(orm.stream)  &  artist_artifacts(),
            lambda:  artists()            &  artist_artifacts(orm.stream),

            lambda:  artists(orm.stream)  &  artifacts(),
            lambda:  artists()            &  artifacts(orm.stream),

            lambda:  artists() & artist_artifacts() & artifacts(orm.stream)

        )

        for fn in fns:
            self.expect(orm.invalidstream, fn)

    def it_calls__iter__on_streamed_entities(self):
        # Create a variant number of artists to test. This will help
        # discover one-off errors in the __iter__
        for i in range(4):
            # Create some artists in db with the same lastname 
            lastname = uuid4().hex
            arts = artists()
            for _ in range(i):
                arts += artist.getvalid()
                arts.last.lastname = lastname
                arts.last.save()

            # Create a streamed artists collection where lastname is the same as
            # the artists created above. Set chunksize to a very low value of 2 so
            # the test isn't too slow. Order by id so the iteration test
            # below can be preformed correctly.
            stm = orm.stream(chunksize=2)
            arts1 = artists(stm, lastname=lastname).sorted('id')

            # Ensure streamed collection count matches non-streamed count
            self.eq(arts1.count, arts.count)

            # Iterate over the streamed collection and compare it two the
            # non-streameed artists collections above. Do this twice so we know
            # __iter__ resets itself correctly.
            arts.sort()
            for _ in range(2):
                j = -1
                for j, art in enumerate(arts1):
                    self.eq(arts[j].id, art.id)
                    self.eq(lastname, art.lastname)

                self.eq(i, j + 1)

        # Ensure that interation works after fetching an element from a chunk
        # that comes after the first chunk.
        arts1[i - 1] # Don't remove
        self.eq(arts1.count, len(list(arts1)))

    def it_calls__getitem__on_entities(self):
        arts = artists()
        for _ in range(4):
            art = artist.getvalid()
            arts += art

        self.is_(art, arts[art.id])
        self.is_(art, arts[art])
        self.expect(IndexError, lambda: arts[uuid4()])

        arts.sort()
        arts1 = arts[:2].sorted()

        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

        art1 = arts[0]

        self.eq(arts.first.id, art1.id)

    def it_calls__getitem__on_streamed_entities(self):
        lastname = uuid4().hex
        arts = artists()
        cnt = 10
        for _ in range(cnt):
            arts += artist.getvalid()
            arts.last.lastname = lastname
            arts.last.save()

        # Test every chunk size
        for chunksize in range(1, 12):
            stm = orm.stream(chunksize=chunksize)
            arts1 = artists(stm, lastname=lastname).sorted('id')

            arts.sort()
            
            # Test indexing in asceding order
            for i in range(10):
                self.eq(arts[i].id, arts1[i].id)
                self.eq(arts[i].id, arts1(i).id)

            # Test indexing in descending order
            for i in range(9, 0, -1):
                self.eq(arts[i].id, arts1[i].id)

            # Test negative indexing in descending order
            for i in range(0, -10, -1):
                self.eq(arts[i].id, arts1[i].id)
                self.eq(arts[i].id, arts1(i).id)

            # Test getting chunks from different ends of the ultimate
            # result-set in an alternating fashion
            for i in range(0, -10, -1):
                self.eq(arts[i].id, arts1[i].id)
                self.eq(arts[abs(i)].id, arts1[abs(i)].id)

            # Test slices
            for i in range(10):
                for j in range(10):
                    self.eq(arts[i:j].pluck('id'), arts1[i:j].pluck('id'))

            # Negative slices (i.e., arts1[4:3]) should produce empty results
            for i in range(10):
                for j in range(i -1, 0, -1):
                    self.zero(arts1[i:j])
                for j in range(0, -10 -1):
                    # TODO Negative stops (arts1[4:-4]) are currently not
                    # implemented.
                    self.expect(NotImplementedError, lambda: arts1[i:j])

            # Ensure that __getitem__ raises IndexError if the index is out of
            # range
            self.expect(IndexError, lambda: arts1[cnt + 1])

            # Ensure that __call__ returns None if the index is out of range
            self.none(arts1(cnt + 1))

            # TODO Test indexing by UUID, i.e.,
            # arts[id]
            # NOTE that UUID indexing on streams has not been implemented yet.

    def it_calls_unavailable_attr_on_streamed_entities(self):
        arts = artists(orm.stream)
        nonos = (
            'getrandom',    'getrandomized',  'where',    'clear',
            'remove',       'shift',          'pop',      'reversed',
            'reverse',      'insert',         'push',     'has',
            'unshift',      'append',         '__sub__',  'getcount',
            '__setitem__',  'getindex',       'delete'
        )

        for nono in nonos:
            self.expect(AttributeError, lambda: getattr(arts, nono))
        
    def it_calls_head_and_tail_on_streamed_entities(self):
        lastname = uuid4().hex
        arts = artists()
        for i in range(10):
            art = artist.getvalid()
            art.lastname = lastname
            arts += art
            art.save()

        # TODO Remove all 'id' argument being passed to the `sorted()` methods
        # since it is the default.
        arts1 = artists(orm.stream, lastname=lastname).sorted('id')
        arts.sort()

        self.eq(arts.head(2).pluck('id'), arts1.head(2).pluck('id'))

        arts1.tail(2)
        self.eq(arts.tail(2).pluck('id'), arts1.tail(2).pluck('id'))

    def it_calls_ordinals_on_streamed_entities(self):
        ords = ('first',            'second',             'third',
                'fourth',           'fifth',              'sixth',
                'last',             'ultimate',           'penultimate',
                'antepenultimate',  'preantepenultimate')

        lastname = uuid4().hex
        arts = artists()
        for _ in range(6):
            arts += artist.getvalid()
            arts.last.lastname = lastname
            arts.last.save()

        arts1 = artists(orm.stream, lastname=lastname).sorted()
        arts.sort()
        for ord in ords:
            self.eq(getattr(arts, ord).id, getattr(arts1, ord).id)

    def it_calls_sort_and_sorted_on_streamed_entities(self):
        lastname = uuid4().hex
        arts = artists()
        for _ in range(10):
            arts += artist.getvalid()
            arts.last.firstname = uuid4().hex
            arts.last.lastname = lastname
            arts.last.save()

        # Test sorting on None - which means: 'sort on id', since id is the
        # default.  Then sort on firstname
        for sort in None, 'firstname':
            for reverse in None, False, True:
                arts.sort(sort, reverse)
                arts1 = artists(orm.stream, lastname=lastname)
                arts1.sort(sort, reverse)
                arts1.orm.sql

                # Test sort()
                for i, art1 in enumerate(arts1):
                    self.eq(arts[i].id, art1.id)

                # Test sorted()
                for i, art1 in enumerate(arts1.sorted(sort, reverse)):
                    self.eq(arts[i].id, art1.id)

    def it_calls_all(self):
        arts = artists()
        cnt = 10
        firstname = uuid4().hex
        for _ in range(cnt):
            arts += artist.getvalid()
            arts.last.firstname = firstname
            arts.last.save()

        arts1 = artists.all
        self.true(arts1.orm.isstreaming)
        self.ge(arts1.count, cnt)

        arts = [x for x in arts1 if x.firstname == firstname]
        self.count(cnt, arts)

    def it_saves_entities(self):
        chrons = self.chronicles

        arts = artists()

        for _ in range(2):
            arts += artist.getvalid()
            arts.last.firstname = uuid4().hex
            arts.last.lastname = uuid4().hex

        chrons.clear()
        arts.save()

        self.two(chrons)
        self.eq(chrons.where('entity', arts.first).first.op, 'create')
        self.eq(chrons.where('entity', arts.second).first.op, 'create')

        for art in arts:
            art1 = artist(art.id)

            for map in art.orm.mappings:
                if not isinstance(map, orm.fieldmapping):
                    continue

                self.eq(getattr(art, map.name), getattr(art1, map.name))

    def it_searches_entities(self):
        arts = artists()
        uuid = uuid4().hex
        for i in range(4):
            art = artist.getvalid()
            arts += art
            art.firstname = uuid4().hex

            if i >= 2:
                art.lastname = uuid
            else:
                art.lastname = uuid4().hex

        arts.save()

        # For clarity, this is a recipe for doing `where x in ([...])` queries.
        # The where string has to be created manually.
        ids = sorted(arts[0:2].pluck('id'))
        where = 'id in (' + ','.join(['%s'] * len(ids)) + ')'

        self.chronicles.clear()

        arts1 = artists(where, ids)
        self.zero(self.chronicles) # defered

        self.two(arts1)
        self.one(self.chronicles)
        self._chrons(arts1, 'retrieve')

        arts1.sort() 
        self.eq(ids[0], arts1.first.id)
        self.eq(ids[1], arts1.second.id)

        # Test a plain where string with no args
        def fn():
            artists("firstname = '%s'" % arts.first.firstname)

        # This should throw an error because we want the user to specify an
        # empty tuple if they don't want to pass in args. This serves as a
        # reminder that they are not taking advantage of the
        # prepared/parameterized statements and may therefore be exposing
        # themselves to SQL injection attacks.
        self.expect(ValueError, fn)

        self.chronicles.clear()

        arts1 = artists("firstname = '%s'" % arts.first.firstname, ())
        self.zero(self.chronicles) # defered

        self.one(arts1)
        self.one(self.chronicles)
        self._chrons(arts1, 'retrieve')

        self.eq(arts.first.id, arts1.first.id)

        # Test a simple 2 arg equality test
        arts1 = artists("firstname", arts.first.firstname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        fname, lname = arts.first['firstname', 'lastname']

        # Test where literal has a UUID so introducers (_binary) are tested.
        arts1 = artists("id", arts.first.id)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with an args tuple
        arts1 = artists('firstname = %s', (arts.first.firstname,))
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with an args tuple and an args param
        where = 'firstname = %s and lastname = %s'
        arts1 = artists(where, (fname,), lname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with an args tuple and a *args element
        arts1 = artists('firstname = %s and lastname = %s', fname, lname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with one *args param
        arts1 = artists('firstname = %s', arts.first.firstname)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with a multi-args tuple
        args = arts.first['firstname', 'lastname']
        arts1 = artists('firstname = %s and lastname = %s', args)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a where string with a multi-args tuple and an *arg element
        args = arts.first['firstname', 'lastname']
        where = 'firstname = %s and lastname = %s and id = %s'
        arts1 = artists(where, args, arts.first.id)
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test a search that gets us two results
        arts1 = artists('lastname = %s', (uuid,))
        arts1 = arts1.sorted('id')
        self.two(arts1)
        arts2 = (arts.third + arts.fourth).sorted('id')
        self.eq(arts2.first.id, arts1.first.id)
        self.eq(arts2.second.id, arts1.second.id)

        arts1 = artists(firstname = arts.first.firstname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

        arts1 = artists(firstname = fname, lastname = lname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

        id = arts.first.id

        def fn():
            artists('id = id', firstname = fname, lastname = lname)

        # Force user to supply an empty args list
        self.expect(ValueError, fn)
        arts = artists('id = id', (), firstname = fname, lastname = lname)
        self.one(arts1)
        arts.first
        self.eq(arts1.first.id, arts.first.id)

        arts = artists('id = %s', (id,), firstname = fname, lastname = lname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

        arts = artists('id = %s', (id,), firstname = fname, lastname = lname)
        self.one(arts1)
        self.eq(arts1.first.id, arts.first.id)

    def it_searches_subentities(self):
        sngs = singers()
        uuid = uuid4().hex
        for i in range(4):
            sng = singer.getvalid()
            sngs += sng
            sng.voice = uuid4().hex
            sng.firstname = uuid4().hex

            if i >= 2:
                sng.register = uuid
            else:
                sng.register = uuid4().hex

            sng.save()

        # Test a plain where string with no args
        def fn():
            singers("firstname = '%s'" % sngs.first.firstname)

        # This should throw an error because we want the user to specify an
        # empty tuple if they don't want to pass in args. This serves as a
        # reminder that they are not taking advantage of the
        # prepared/parameterized statements and may therefore be exposing
        # themselves to SQL injection attacks.
        self.expect(ValueError, fn)

        '''
        Test searching on subenitiy's properties
        '''
        self.chronicles.clear()
        sngs1 = singers("voice = '%s'" % sngs.first.voice, ())
        self.zero(self.chronicles) # defered

        self.one(sngs1)

        self.eq(sngs.first.id, sngs1.first.id)

        # Only one query will have been executed
        self.one(self.chronicles)
        self._chrons(sngs1, 'retrieve')

        # Calling isvalid will load the the super class artist as well
        self.true(sngs1.isvalid)
        self.two(self.chronicles)
        self._chrons(sngs1.first.orm.super, 'retrieve')

        '''
        Test searching on a property of singer's superentity
        '''
        # Each firstname will be unique so we should should only get one result
        # from this query and it should be entity-equivalent sngs.first
        self.chronicles.clear()
        sngs1 = singers("firstname = '%s'" % sngs.first.firstname, ())
        self.zero(self.chronicles) # defered

        self.one(sngs1)
        self.one(self.chronicles) # defered
        self._chrons(sngs1, 'retrieve')

        # Calling isvalid will result in zero additional queries
        self.true(sngs1.isvalid)
        self.one(self.chronicles)

        self.eq(sngs.first.id, sngs1.first.id)

        '''
        Test searching on a property of singer and a property of singer's
        superentity (artist)
        '''
        sngs.sort()
        self.chronicles.clear()
        where = "voice = '%s' or firstname = '%s'" 
        where %= sngs.first.voice, sngs.second.firstname
        sngs1 = singers(where, ())
        self.zero(self.chronicles) # defered

        sngs1.sort()

        # Sorting will cause a load
        self.one(self.chronicles)
        self._chrons(sngs1, 'retrieve')

        # Make sure valid
        self.true(sngs1.isvalid)

        # isvalid should not cause any additional queries to be chronicled (if
        # we had not included the firstname in the above query, isvalid would
        # need to load singer's super
        self.one(self.chronicles)

        self.two(sngs1)
        self.eq(sngs.first.id, sngs1.first.id)
        self.eq(sngs.second.id, sngs1.second.id)

        # Still nothing new chronicled
        self.one(self.chronicles)

    def it_searches_entities_using_fulltext_index(self):
        for e in artists, artifacts:
            e.orm.truncate()

        arts, facts = artists(), artifacts()
        for i in range(2):
            art = artist.getvalid()
            fact = artifact.getvalid()
            if i:
                art.bio = fact.title = 'one two three %s four five six'
                fact.description = 'seven eight %s nine ten'
            else:
                art.bio = la2gr('one two three four five six')
                fact.title = art.bio
                fact.description = la2gr('seven eight nine ten')

            arts += art; facts += fact

        arts.save(facts)

        # Search string of 'zero' should produce zero results
        arts1 = artists('match(bio) against (%s)', 'zero')
        self.zero(arts1)

        # Search for the word "three"
        arts1 = artists('match(bio) against (%s)', 'three')
        self.one(arts1)
        self.eq(arts.second.id, arts1.first.id)

        # Search for the Greek transliteration of "three". We want to ensure
        # there is no issue with Unicode characters.
        arts1 = artists('match(bio) against (%s)', la2gr('three'))
        self.one(arts1)
        self.eq(arts.first.id, arts1.first.id)

        # Test "composite" full-text search

        # Search string of 'zero' should produce zero results
        arts1 = artifacts('match(title, description) against(%s)', 'zero')
        self.zero(arts1)

        # Search for the word "three". "three" is in 'title'.
        arts1 = artifacts('match(title, description) against(%s)', 'three')
        self.one(arts1)
        self.eq(facts.second.id, arts1.first.id)

        # Search for eight. "eight" is in 'description'.
        arts1 = artifacts('match(title, description) against(%s)', 'eight')
        self.one(arts1)
        self.eq(facts.second.id, arts1.first.id)

        # Search for the Greek transliteration of "three". It is in 'title';
        arts1 = artifacts('match(title, description) against(%s)', la2gr('three'))
        self.one(arts1)
        self.eq(facts.first.id, arts1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description'.
        arts1 = artifacts('match(title, description) against(%s)', la2gr('eight'))
        self.one(arts1)
        self.eq(facts.first.id, arts1.first.id)

        # Search for literal placeholders string (i.e., '%s')
        arts1 = artists("match(bio) against (%s)", 'three %s')
        self.one(arts1)
        self.eq(arts.second.id, arts1.first.id)

        # NOTE MySQL doesn't return a match here, even though there is a
        # literal '%s' in the artist.bio field
        arts1 = artists("match(bio) against ('%s')", ())
        self.zero(arts1)

        arts1 = artists("match(bio) against ('three %s')", ())
        self.one(arts1)
        self.eq(arts.second.id, arts1.first.id)

        arts1 = artists("match(bio) against ('%x')", ())
        self.zero(arts1)

    def it_searches_subentities_using_fulltext_index(self):
        sngs, concs = artists(), concerts()
        for i in range(2):
            sng = singer.getvalid()
            conc = concert.getvalid()
            if i:
                sng.bio = conc.title = 'one two three four five six'
                conc.description1 = 'seven eight nine ten'
            else:
                sng.bio = conc.title = la2gr('one two three four five six')
                conc.description1 = la2gr('seven eight nine ten')

            sngs += sng; concs += conc

        sngs.save(concs)

        # Search string of 'zero' should produce zero results
        sngs1 = singers("match(bio) against (%s)", 'zero')
        self.zero(sngs1)

        # Search string of 'zero' should produce zero results
        sngs1 = singers("match(bio) against ('zero')", ())
        self.zero(sngs1)

        # Search for the word "three"
        sngs1 = singers("match(bio) against (%s)", 'three')
        self.one(sngs1)
        self.eq(sngs.second.id, sngs1.first.id)

        # Search for the word "three"
        sngs1 = singers("match(bio) against ('three')", ())
        self.one(sngs1)
        self.eq(sngs.second.id, sngs1.first.id)

        # Search for the Greek transliteration of "three". We want to ensure
        # there is no issue with Unicode characters.
        sngs1 = singers("match(bio) against (%s)", la2gr('three'))
        self.one(sngs1)
        self.eq(sngs.first.id, sngs1.first.id)

        l = lambda: concerts("match(title, xxx) against(%s)", 'zero')
        self.expect(orm.invalidcolumn, l)

        # Test "composite" full-text search

        # Search string of 'zero' should produce zero results
        concs1 = concerts("match(title, description1) against(%s)", 'zero')
        self.zero(concs1)
        
        concs1 = concerts("match(title, description1) against('zero')", ())
        self.zero(concs1)

        # Search for the word "three". "three" is in 'title'.
        concs1 = concerts("match(title, description1) against(%s)", 'three')
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for the word "three". "three" is in 'title'.
        concs1 = concerts("match(title, description1) against('three')", ())
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for eight. "eight" is in 'description1'.
        concs1 = concerts("match(title, description1) against(%s)", 'eight')
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for eight. "eight" is in 'description1'.
        concs1 = concerts("match(title, description1) against('eight')", ())
        self.one(concs1)
        self.eq(concs.second.id, concs1.first.id)

        # Search for the Greek transliteration of "three". It is in 'title';
        wh = "match(title, description1) against('%s')" % la2gr('three')
        concs1 = concerts(wh, ())
        self.one(concs1)
        self.eq(concs.first.id, concs1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description1'
        concs1 = concerts("match(title, description1) against(%s)", la2gr('eight'))
        self.one(concs1)
        self.eq(concs.first.id, concs1.first.id)

        # Search for the Greek transliteration of "eight". It is in 'description1'
        wh = "match(title, description1) against('%s')" % la2gr('eight')
        concs1 = concerts(wh, ())
        self.one(concs1)
        self.eq(concs.first.id, concs1.first.id)
        
    def it_rollsback_save_of_entities(self):
        # Create two artists
        arts = artists()

        for _ in range(2):
            arts += artist()
            arts.last.firstname = uuid4().hex
            arts.last.lastname = uuid4().hex

        arts.save()

        # First, break the save method so a rollback occurs, and test the
        # rollback. Second, fix the save method and ensure success.
        for i in range(2):
            if i:
                # Restore original save method
                arts.second._save = save

                # Update property 
                arts.first.firstname = new = uuid4().hex
                arts.save()
                self.eq(new, artist(arts.first.id).firstname)
            else:
                # Update property
                old, arts.first.firstname = arts.first.firstname, uuid4().hex

                # Break save method
                save, arts.second._save = arts.second._save, lambda x: 0/0

                self.expect(ZeroDivisionError, lambda: arts.save())
                self.eq(old, artist(arts.first.id).firstname)

    def it_deletes_entities(self):
        # Create two artists
        arts = artists()

        for _ in range(2):
            arts += artist.getvalid()
        
        arts.save()

        art = arts.shift()
        self.one(arts)
        self.one(arts.orm.trash)

        self.chronicles.clear()
        arts.save()
        self.one(self.chronicles)
        self._chrons(art, 'delete')

        self.expect(db.RecordNotFoundError, lambda: artist(art.id))
        
        # Ensure the remaining artist still exists in database
        self.expect(None, lambda: artist(arts.first.id))

    def it_doesnt_needlessly_save_entitity(self):
        chrons = self.chronicles

        art = artist()

        art.firstname = uuid4().hex
        art.lastname = uuid4().hex
        art.ssn = '1' * 11
        art.phone = '1' * 7
        art.password  = bytes([random.randint(0, 255) for _ in range(32)])
        art.email = 'username@domain.tld'

        for i in range(2):
            chrons.clear()
            art.save()
            
            if i == 0:
                self.one(chrons)
                self.eq(chrons.where('entity', art).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

        # Dirty art and save. Ensure the object was actually saved if needed
        art.firstname = uuid4().hex
        for i in range(2):
            chrons.clear()
            art.save()

            if i == 0:
                self.one(chrons)
                self.eq(chrons.where('entity', art).first.op, 'update')
            elif i == 1:
                self.zero(chrons)

        # Test constituents
        art.presentations += presentation.getvalid()
        
        for i in range(2):
            chrons.clear()
            art.save()

            if i == 0:
                self.one(chrons)
                pres = art.presentations.last
                self.eq(chrons.where('entity', pres).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

        # Test deeply-nested (>2) constituents
        art.presentations.last.locations += location.getvalid()

        for i in range(2):

            chrons.clear()
            art.save()

            if i == 0:
                self.one(chrons)
                loc = art.presentations.last.locations.last
                self.eq(chrons.where('entity', loc).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

    def entity_contains_reference_to_composite(self):
        chrons = self.chronicles

        art = artist.getvalid()

        for _ in range(2):
            art.presentations += presentation.getvalid()

            for _ in range(2):
                art.presentations.last.locations += location.getvalid()

        art.save()

        for i, art in enumerate((art, artist(art.id))):
            for pres in art.presentations:
                chrons.clear()
                    
                self.is_(art, pres.artist)
                self.zero(chrons)

                for loc in pres.locations:
                    chrons.clear()
                    self.is_(pres, loc.presentation)
                    self.zero(chrons)

    def it_loads_and_saves_entities_constituents(self):
        chrons = self.chronicles

        # Ensure that a new composite has a constituent object with zero
        # elements
        art = artist.getvalid()
        self.zero(art.presentations)

        # Ensure a saved composite object with zero elements in a constiuent
        # collection loads with zero the constiuent collection containing zero
        # elements.
        art.firstname = uuid4().hex
        art.lastname = uuid4().hex

        self.is_(art.presentations.artist, art)
        self.zero(art.presentations)

        art.save()

        self.is_(art.presentations.artist, art)
        self.zero(art.presentations)

        art = artist(art.id)
        self.zero(art.presentations)
        self.is_(art.presentations.artist, art)

        # Create some presentations within artist, save artist, reload and test
        art = artist.getvalid()
        art.presentations += presentation.getvalid()
        art.presentations += presentation.getvalid()

        for pres in art.presentations:
            pres.name = uuid4().hex

        chrons.clear()
        art.save()

        self.three(chrons)
        press = art.presentations
        self.eq(chrons.where('entity', art).first.op, 'create')
        self.eq(chrons.where('entity', press.first).first.op, 'create')
        self.eq(chrons.where('entity', press.second).first.op, 'create')

        art1 = artist(art.id)

        chrons.clear()

        press = art1.presentations
        art.presentations.sort()

        self.one(chrons)

        self.eq(chrons.where('entity', press).first.op, 'retrieve')
        art1.presentations.sort()
        for pres, pres1 in zip(art.presentations, art1.presentations):
            self.eq((False, False, False), pres.orm.persistencestate)
            self.eq((False, False, False), pres1.orm.persistencestate)
            for map in pres.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(pres, map.name), getattr(pres1, map.name))
            
            self.is_(art1, pres1.artist)

        # Create some locations with the presentations, save artist, reload and
        # test
        for pres in art.presentations:
            for _ in range(2):
                pres.locations += location.getvalid()

        chrons.clear()
        art.save()

        self.four(chrons)

        locs = art.presentations.first.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        locs = art.presentations.second.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        art1 = artist(art.id)
        self.two(art1.presentations)

        art.presentations.sort()
        art1.presentations.sort()
        for pres, pres1 in zip(art.presentations, art1.presentations):

            pres.locations.sort()

            chrons.clear()
            pres1.locations.sort()

            self.one(chrons)
            locs = pres1.locations

            self.eq(chrons.where('entity', locs).first.op, 'retrieve')

            for loc, loc1 in zip(pres.locations, pres1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        v, v1 = getattr(loc, map.name), getattr(loc1, map.name)
                        self.eq(v, v1)
            
                self.is_(pres1, loc1.presentation)
        return

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        art = artist.getvalid()
        press = presentations()

        for _ in range(2):
            press += presentation.getvalid()

        art.presentations += press

        for i in range(2):
            if i:
                art.save()
                art = artist(art.id)

            self.eq(press.count, art.presentations.count)

            for pres in art.presentations:
                self.is_(art, pres.artist)

    def it_updates_entity_constituents_properties(self):
        chrons = self.chronicles
        art = artist.getvalid()

        for _ in range(2):
            art.presentations += presentation.getvalid()
            art.presentations.last.name = uuid4().hex

            for _ in range(2):
                art.presentations.last.locations += location.getvalid()
                art.presentations.last.locations.last.description = uuid4().hex

        art.save()

        art1 = artist(art.id)
        for pres in art1.presentations:
            pres.name = uuid4().hex
            
            for loc in pres.locations:
                loc.description = uuid4().hex

        chrons.clear()
        art1.save()
        self.six(chrons)
        for pres in art1.presentations:
            self.eq(chrons.where('entity', pres).first.op, 'update')
            for loc in pres.locations:
                self.eq(chrons.where('entity', loc).first.op, 'update')
            

        art2 = artist(art.id)
        press = (art.presentations, art1.presentations, art2.presentations)
        for pres, pres1, pres2 in zip(*press):
            # Make sure the properties were changed
            self.ne(getattr(pres2, 'name'), getattr(pres,  'name'))

            # Make user art1.presentations props match those of art2
            self.eq(getattr(pres2, 'name'), getattr(pres1, 'name'))

            locs = pres.locations, pres1.locations, pres2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(getattr(loc2, 'description'), getattr(loc,  'description'))

                # Make user art1 locations props match those of art2
                self.eq(getattr(loc2, 'description'), getattr(loc1, 'description'))

    def it_saves_and_loads_entity_constituent(self):
        chrons = self.chronicles

        # Make sure the constituent is None for new composites
        pres = presentation.getvalid()

        chrons.clear()
        self.none(pres.artist)
        self.zero(chrons)

        self.zero(pres.brokenrules)
        
        # Test setting an entity constituent then test saving and loading
        art = artist.getvalid()
        pres.artist = art
        self.is_(art, pres.artist)

        chrons.clear()
        pres.save()
        self.two(chrons)
        self.eq(chrons.where('entity', art).first.op,  'create')
        self.eq(chrons.where('entity', pres).first.op, 'create')

        # Load by artist then lazy-load presentations to test
        art1 = artist(pres.artist.id)
        self.one(art1.presentations)
        self.eq(art1.presentations.first.id, pres.id)

        # Load by presentation and lazy-load artist to test
        pres1 = presentation(pres.id)

        chrons.clear()
        self.eq(pres1.artist.id, pres.artist.id)
        self.one(chrons)
        self.eq(chrons.where('entity', pres1.artist).first.op,  'retrieve')

        art1 = artist.getvalid()
        pres1.artist = art1

        chrons.clear()
        pres1.save()

        self.two(chrons)
        self.eq(chrons.where('entity', art1).first.op,  'create')
        self.eq(chrons.where('entity', pres1).first.op, 'update')


        pres2 = presentation(pres1.id)
        self.eq(art1.id, pres2.artist.id)
        self.ne(art1.id, art.id)

        # Test deeply-nested (>2)
        # Set entity constuents, save, load, test
       
        loc = location.getvalid()
        self.none(loc.presentation)

        loc.presentation = pres = presentation.getvalid()
        self.is_(pres, loc.presentation)

        chrons.clear()
        self.none(loc.presentation.artist)
        self.zero(chrons)

        loc.presentation.artist = art = artist.getvalid()
        self.is_(art, loc.presentation.artist)

        loc.save()

        self.three(chrons)
        self.eq(chrons.where('entity',  loc).first.op,               'create')
        self.eq(chrons.where('entity',  loc.presentation).first.op,  'create')
        self.eq(chrons.where('entity',  art).first.op,               'create')

        chrons.clear()
        loc1 = location(loc.id)
        pres1 = loc1.presentation

        self.eq(loc.id, loc1.id)
        self.eq(loc.presentation.id, loc1.presentation.id)
        self.eq(loc.presentation.artist.id, loc1.presentation.artist.id)

        self.three(chrons)
        self.eq(chrons.where('entity',  loc1).first.op,          'retrieve')
        self.eq(chrons.where('entity',  pres1).first.op,         'retrieve')
        self.eq(chrons.where('entity',  pres1.artist).first.op,  'retrieve')

        # Change the artist
        loc1.presentation.artist = art1 = artist.getvalid()

        chrons.clear()
        loc1.save()

        self.two(chrons)
        pres1 = loc1.presentation

        self.eq(chrons.where('entity',  pres1).first.op,  'update')
        self.eq(chrons.where('entity',  art1).first.op,   'create')

        loc2 = location(loc1.id)
        self.eq(loc1.presentation.artist.id, loc2.presentation.artist.id)
        self.ne(art.id, loc2.presentation.artist.id)

        # Note: Going up the graph, mutating attributes and persisting lower in
        # the graph won't work because of the problem of infinite recursion.
        # The below tests demonstrate this.

        # Assign a new name
        name = uuid4().hex
        loc2.presentation.artist.presentations.first.name = name

        # The presentation objects here aren't the same reference so they will
        # have different states.
        self.ne(loc2.presentation.name, name)

        chrons.clear()
        loc2.save()

        self.zero(chrons)

        loc2 = location(loc2.id)

        self.one(chrons)
        self.eq(chrons.where('entity',  loc2).first.op,   'retrieve')

        # The above save() didn't save the new artist's presentation collection
        # so the new name will not be present in the reloaded presentation
        # object.
        self.ne(loc2.presentation.name, name)
        self.ne(loc2.presentation.artist.presentations.first.name, name)

    def entity_constituents_break_entity(self):
        pres = presentation.getvalid()
        pres.artist = artist.getvalid()

        # Break rule that art.networth should be an int
        pres.artist.networth = str() # Break

        self.one(pres.brokenrules)
        self.broken(pres, 'networth', 'valid')

        pres.artist.networth = int() # Unbreak
        self.zero(pres.brokenrules)

        loc = location.getvalid()
        loc.description = 'x' * 256 # break
        loc.presentation = presentation.getvalid()
        loc.presentation.name = 'x' * 256 # break
        loc.presentation.artist = artist.getvalid()
        loc.presentation.artist.firstname = 'x' * 256 # break

        self.three(loc.brokenrules)
        for prop in 'description', 'name', 'firstname':
            self.broken(loc, prop, 'fits')

    def it_rollsback_save_of_entity_with_broken_constituents(self):
        art = artist.getvalid()

        art.presentations += presentation.getvalid()
        art.presentations.last.name = uuid4().hex

        art.presentations += presentation.getvalid()
        art.presentations.last.name = uuid4().hex

        # Cause the last presentation's invocation of save() to raise an
        # Exception to cause a rollback
        art.presentations.last._save = lambda cur, followentitymapping: 1/0

        # Save expecting the ZeroDivisionError
        self.expect(ZeroDivisionError, lambda: art.save())

        # Ensure state of art was restored to original
        self.true(art.orm.isnew)
        self.false(art.orm.isdirty)
        self.false(art.orm.ismarkedfordeletion)

        # Ensure artist wasn't saved
        self.expect(db.RecordNotFoundError, lambda: artist(art.id))

        # For each presentations, ensure state was not modified and no presentation 
        # object was saved.
        for pres in art.presentations:
            self.true(pres.orm.isnew)
            self.false(pres.orm.isdirty)
            self.false(pres.orm.ismarkedfordeletion)
            self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))

    def it_calls_entities(self):
        
        # Creating a single orm.entity with no collection should produce an
        # AttributeError
        def fn():
            class single(orm.entity):
                firstname = orm.fieldmapping(str)

        self.expect(AttributeError, fn)

        # Test explicit detection of orm.entities 
        class bacteria(orm.entities):
            pass

        class bacterium(orm.entity):
            entities = bacteria
            name = orm.fieldmapping(str)

        b = bacterium()
        self.is_(b.orm.entities, bacteria)
        self.eq(b.orm.table, 'bacteria')

        # Test implicit entities detection based on naive pluralisation
        art = artist()
        self.is_(art.orm.entities, artists)
        self.eq(art.orm.table, 'artists')

        # Test implicit entities detection of entities subclass based on naive
        # pluralisation
        s = singer()
        self.is_(s.orm.entities, singers)
        self.eq(s.orm.table, 'singers')

    def it_calls_id_on_entity(self):
        art = artist.getvalid()

        self.true(hasattr(art, 'id'))
        self.type(uuid.UUID, art.id)
        self.zero(art.brokenrules)

    def it_calls_custom_methods_on_entity(self):
        art = artist()

        # Ensure artist.__init__ got called. It will default "lifeform" to
        # 'organic'
        self.eq('organic', art.lifeform)

        art.presentations += presentation()
        art.locations += location()

        self.one(art.presentations)
        self.one(art.locations)

        # Ensure the custom method clear() is called and successfully clears
        # the presentations and locations collections.
        art.clear()

        self.zero(art.presentations)
        self.zero(art.locations)

        # Test a custom @property
        self.false(art.processing)
        art.processing = True
        self.true(art.processing)

        # Test it calls fields
        uuid = uuid4().hex
        art.test = uuid
        self.eq(uuid, art.test)

    def it_calls_custom_methods_on_subentity(self):
        sng = singer()

        # Ensure artist.__init__ got called. It will default "lifeform" to
        # 'organic'
        self.eq('organic', sng.lifeform)

        sng.concerts += concert()
        sng.locations += location()

        self.one(sng.concerts)
        self.one(sng.locations)

        # Ensure the custom method clear() is called and successfully clears
        # the presentations and locations collections.
        sng.clear()

        self.zero(sng.concerts)
        self.zero(sng.locations)

        # Test a custom @property
        self.false(sng.transmitting)
        sng.transmitting = True
        self.true(sng.transmitting)

        # Test a custom @property in super class 
        self.false(sng.processing)
        sng.processing = True
        self.true(sng.processing)

        # Test it calls fields
        uuid = uuid4().hex
        sng.test = uuid
        self.eq(uuid, sng.test)


    def it_calls__getitem__on_entity(self):
        art = artist()
        art.firstname = uuid4().hex
        art.lastname = uuid4().hex
        art.phone = '1' * 7

        self.eq(art['firstname'], art.firstname)

        expected = art.firstname, art.lastname
        actual = art['firstname', 'lastname']

        self.eq(expected, actual)
        self.expect(IndexError, lambda: art['idontexist'])

        actual = art['presentations', 'locations']
        expected = art.presentations, art.locations

        actual = art['phone']
        expected = art.phone

        self.eq(actual, expected)

    def it_calls__getitem__on_subentity(self):
        sng = singer()
        sng.firstname = uuid4().hex
        sng.lastname = uuid4().hex
        sng.voice = uuid4().hex
        sng.register = 'laryngealization'

        self.eq(sng['firstname'], sng.firstname)

        names = sng.firstname, sng.lastname
        self.eq(names, sng['firstname', 'lastname'])
        self.expect(IndexError, lambda: sng['idontexist'])

        actual = sng['presentations', 'locations']
        expected = sng.presentations, sng.locations

        self.eq(actual, expected)

        actual = sng['voice', 'concerts']
        expected = sng.voice, sng.concerts

        self.eq(actual, expected)

        actual = sng['phone']
        expected = sng.phone

        self.eq(actual, expected)

        actual = sng.register
        expected = sng.register

        self.eq(actual, expected)

    def it_calls__getitem__on_association(self):
        art = artist()
        art.artist_artifacts += artist_artifact()
        aa = art.artist_artifacts.first

        self.eq(aa['role'], aa.role)

        expected = aa.role, aa.planet
        actual = aa['role', 'planet']

        self.eq(expected, actual)
        self.expect(IndexError, lambda: aa['idontexist'])

        actual = aa['artist', 'artifact']
        expected = aa.artist, aa.artifact

        self.eq(actual, expected)

        aa.timespan = '1/1/2001 3/3/2001'
        actual = aa['timespan', 'processing']
        expected = aa.timespan, aa.processing

        self.eq(actual, expected)

    def it_doesnt_raise_exception_on_invalid_attr_values(self):
        # For each type of attribute, ensure that any invalid value can be
        # given. The invalid value should cause a brokenrule but should never
        # result in a type coercion exception on assignment or retrieval

        # datetime
        art = artist.getvalid()
        art.dob = uuid4().hex       
        self.expect(None, lambda: art.dob) 
        self.one(art.brokenrules)
        self.broken(art, 'dob', 'valid')

        # int
        art = artist.getvalid()
        art.weight = uuid4().hex       
        self.expect(None, lambda: art.weight) 
        self.one(art.brokenrules)
        self.broken(art, 'weight', 'valid')

        # float
        comp = component.getvalid()
        comp.height = uuid4().bytes       
        self.expect(None, lambda: comp.height) 
        self.one(comp.brokenrules)
        self.broken(comp, 'height', 'valid')

        # decimal
        fact = artifact.getvalid()
        fact.price = uuid4().bytes       
        self.expect(None, lambda: fact.price) 
        self.one(fact.brokenrules)
        self.broken(fact, 'price', 'valid')

        # bytes
        comp = component.getvalid()
        comp.digest = uuid4().hex       
        self.expect(None, lambda: comp.digest) 
        self.one(comp.brokenrules)
        self.broken(comp, 'digest', 'valid')

        # constituent entity
        art = artist.getvalid()
        art.presentations += location.getvalid() # break
        self.expect(None, lambda: art.presentations) 
        self.one(art.brokenrules)
        self.broken(art, 'presentations', 'valid')

        # constituent
        art = artist.getvalid()
        art.presentations = locations() # break
        self.expect(None, lambda: art.presentations) 
        self.one(art.brokenrules)
        self.broken(art, 'presentations', 'valid')

        # composite
        pres = presentation.getvalid()
        pres.artist = location.getvalid()

        self.one(pres.brokenrules)
        self.broken(pres, 'artist', 'valid')

        loc = location.getvalid()
        loc.presentation = pres

        self.broken(loc, 'artist', 'valid')

        # associations

        # Add wrong type to association
        art = artist.getvalid()
        art.artist_artifacts += location()
        self.three(art.brokenrules)
        self.broken(art, 'artist_artifacts', 'valid')

        # Add wrong type to the pseudo-collection
        art = artist.getvalid()
        facts = art.artifacts 
        loc = location.getvalid()
        facts += loc

        self.three(art.brokenrules)
        self.broken(art, 'artifact', 'valid')
        
    def it_calls_explicit_attr_on_subentity(self):
        # Test inherited attr (phone)
        sng = singer()
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex
        sng.lifeform  = uuid4().hex
        sng.password  = bytes([random.randint(0, 255) for _ in range(32)])
        sng.ssn       = '1' * 11
        sng.register  = 'laryngealization'
        sng.email     = 'username@domain.tld'
        self.eq(int(), sng.phone)

        sng.phone = '1' * 7
        self.type(int, sng.phone)

        sng.save()

        art1 = singer(sng.id)
        self.eq(sng.phone, art1.phone)

        art1.phone = '1' * 7
        self.type(int, art1.phone)

        art1.save()

        art2 = singer(art1.id)
        self.eq(art1.phone, art2.phone)

        # Test non-inherited attr (register)
        sng = singer()
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex
        sng.lifeform  = uuid4().hex
        sng.password  = bytes([random.randint(0, 255) for _ in range(32)])
        sng.ssn       = '1' * 11
        sng.phone     = '1' * 7
        sng.email     = 'username@domain.tld'
        self.is_(str(), sng.register)

        sng.register = 'Vocal Fry'
        self.eq('vocal fry', sng.register)

        sng.save()

        art1 = singer(sng.id)
        self.eq(sng.register, art1.register)

        art1.register = 'flute'
        self.eq('whistle', art1.register)

        art1.save()

        art2 = singer(art1.id)
        self.eq(art1.register, art2.register)

    def it_calls_explicit_attr_on_association(self):
        art = artist.getvalid()

        art.artist_artifacts += artist_artifact.getvalid()
        aa = art.artist_artifacts.first

        # Ensure the overridden __init__ was called. It defaults planet to
        # "Earth".
        self.eq('Earth', aa.planet)

        # Test the explicit attribute timespan. It removes spaces from the
        # value and replaces them with dashes.
        art.artist_artifacts.first.timespan = '1/10/2018 2/10/2018'
        self.eq('1/10/2018-2/10/2018', aa.timespan)

        art.save()
        art1 = artist(art.id)
        self.eq('1/10/2018-2/10/2018', aa.timespan)

        # Test non-mapped property
        self.false(aa.processing)
        aa.processing = True
        self.true(aa.processing)

        # Test field
        uuid = str(uuid4())
        self.test = uuid
        self.eq(uuid, self.test)

    def it_calls_bytes_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)

            return getattr(e, attr) == getattr(e1, attr)

        def rand(size):
            return bytes([random.randint(0, 255) for _ in range(size)])

        # Test bytes attribute as a varbinary (min != max)
        comp = component()
        comp.name = uuid4().hex
        map = comp.orm.mappings['digest']

        # Make sure the password field hasn't been tampered with
        self.ne(map.min, map.max) 
        self.eq('varbinary(%s)' % map.max, map.dbtype)
        self.true(hasattr(comp, 'digest'))
        self.type(bytes, comp.digest)
        self.one(comp.brokenrules)
        self.broken(comp, 'digest', 'fits')

        # Test max
        self.ne(map.min, map.max) 
        comp.digest = rand(map.max)
        self.true(saveok(comp, 'digest'))

        comp.digest = rand(map.max + 1)
        self.broken(comp, 'digest', 'fits')

        # Test min
        comp.digest = rand(map.max)
        self.true(saveok(comp, 'digest'))
        
        comp.digest = rand(map.min - 1)
        self.broken(comp, 'digest', 'fits')

        # Ensure non-Bytes are coerced in accordance with bytes()'s rules.
        arrint = [random.randint(0, 255) for _ in range(32)]
        for v in arrint, bytearray(arrint):
            comp.digest = v
            self.eq(bytes(arrint), comp.digest)
            self.type(bytes, comp.digest)
            self.true(saveok(comp, 'digest'))

        # Test bytes attribute as a binary (min != max)
        art = artist()
        art.firstname = uuid4().hex
        art.lastname = uuid4().hex
        art.ssn = '1' * 11
        art.phone = '1' * 7
        art.email = 'username@domain.tld'
        map = art.orm.mappings['password']

        # Make sure the password field hasn't been tampered with
        self.eq(map.min, map.max) 
        self.eq('binary(%s)' % map.max, map.dbtype)
        self.true(hasattr(art, 'password'))
        self.type(bytes, art.password)
        self.one(art.brokenrules)
        self.broken(art, 'password', 'fits')

        # Test default
        self.eq(b'', art.password)

        # Test max
        art.password = rand(map.max)
        self.true(saveok(art, 'password'))

        art.password = rand(map.max + 1)
        self.broken(art, 'password', 'fits')

        # Test min
        art.password = rand(map.max)
        self.true(saveok(art, 'password'))
        
        art.password = rand(map.min - 1)
        self.broken(art, 'password', 'fits')

        # Ensure non-Bytes are coerced in accordance with bytes()'s rules.
        arrint = [random.randint(0, 255) for _ in range(32)]
        for v in arrint, bytearray(arrint):
            art.password = v
            self.eq(bytes(arrint), art.password)
            self.type(bytes, art.password)
            self.true(saveok(art, 'password'))

    def it_calls_bool_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        fact = artifact.getvalid()
        self.eq('bit', fact.orm.mappings['abstract'].dbtype)
        self.type(bool, fact.abstract)
        self.true(hasattr(fact, 'abstract'))
        self.zero(fact.brokenrules)

        # Test default
        self.false(fact.abstract)
        self.true(saveok(fact, 'abstract'))

        # Test save
        for b in True, False:
            fact.abstract = b
            self.type(bool, fact.abstract)
            self.eq(b, fact.abstract)
            self.true(saveok(fact, 'abstract'))

        # Falsys and Truthys not allowed
        for v in int(), float(), str():
            fact.abstract = v
            self.one(fact.brokenrules)
            self.broken(fact, 'abstract', 'valid')

        # None, of course, is allowed despite being Falsy
        fact.abstract = None
        self.zero(fact.brokenrules)

    def it_calls_explicit_str_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        # Ensure that a non-str gets converted to a str
        for o in int(1), float(3.14), dec(1.99), datetime.now(), True:
            art = artist()
            art.email = o
            self.type(str, art.email)
            self.eq(str(o).lower(), art.email)


        Delta = la2gr('d')
        for art in (artist(), singer()):
            map = art.orm.mappings('email')
            if not map:
                map = art.orm.super.orm.mappings['email']
            self.true(hasattr(art, 'email'))
            self.eq(str(), art.email)
            self.eq((3, 254), (map.min, map.max))

            art.email = email = 'USERNAME@DOMAIN.TDL'
            self.eq(email.lower(), art.email)

            art.email = '\n\t ' + email + '\n\t '
            self.eq(email.lower(), art.email)

            art = artist.getvalid()
            min, max = map.min, map.max

            art.email = Delta * map.max
            self.true(saveok(art, 'email'))

            art.email += Delta
            self.one(art.brokenrules)
            self.broken(art, 'email', 'fits')

            art.email = Delta * min
            self.true(saveok(art, 'email'))

            art.email = (Delta * (min - 1))
            self.one(art.brokenrules)
            self.broken(art, 'email', 'fits')

    def it_calls_str_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        # Ensure that a non-str gets converted to a str
        for o in int(1), float(3.14), dec(1.99), datetime.now(), True:
            art = artist()
            art.firstname = o
            self.type(str, art.firstname)
            self.eq(str(o), art.firstname)

        for art in (artist(), singer()):
            art.lastname  = uuid4().hex
            art.lifeform  = uuid4().hex
            art.password  = bytes([random.randint(0, 255) for _ in range(32)])
            art.ssn       = '1' * 11
            art.phone     = '1' * 7
            art.email     = 'username@domain.tld'
            if type(art) is singer:
                art.voice     = uuid4().hex
                art.register  = 'laryngealization'
            
            map = art.orm.mappings('firstname')
            if not map:
                map = art.orm.super.orm.mappings['firstname']

            self.false(map.isfixed)
            self.eq('varchar(%s)' % (str(map.max),), map.dbtype)

            min, max = map.min, map.max

            art.firstname = firstname = '\n\t ' + (Delta * 10) + '\n\t '
            self.eq(firstname.strip(), art.firstname)

            art.firstname = Delta * max
            self.true(saveok(art, 'firstname'))

            art.firstname += Delta
            self.one(art.brokenrules)
            self.broken(art, 'firstname', 'fits')

            art.firstname = Delta * min
            self.true(saveok(art, 'firstname'))

            art.firstname = (Delta * (min - 1))
            self.one(art.brokenrules)
            self.broken(art, 'firstname', 'fits')

            art.firstname = Cunei_a * 255
            self.true(saveok(art, 'firstname'))

            art.firstname += Cunei_a
            self.one(art.brokenrules)
            self.broken(art, 'firstname', 'fits')

            art.firstname = Cunei_a * 255 # Unbreak

            art.firstname = None
            self.true(saveok(art, 'firstname'))

            # Test fixed-length ssn property
            art = artist()
            art.firstname = uuid4().hex
            art.lastname  = uuid4().hex
            art.lifeform  = uuid4().hex
            art.password  = bytes([random.randint(0, 255) for _ in range(32)])
            art.phone     = '1' * 7
            art.email     = 'username@domain.tld'
            if type(art) is singer:
                art.voice     = uuid4().hex
                art.register  = 'laryngealization'

            map = art.orm.mappings['ssn']
            self.true(map.isfixed)
            self.eq('char(%s)' % (map.max,), map.dbtype)
            self.empty(art.ssn)

            # We are treating ssn as a fixed-length string that can hold any
            # unicode character - not just numeric characters. So lets user a roman
            # numeral V.
            art.ssn = V * map.max
            self.true(saveok(art, 'ssn'))

            art.ssn = V * (map.max + 1)
            self.one(art.brokenrules)
            self.broken(art, 'ssn', 'fits')

            art.ssn = V * (map.min - 1)
            self.one(art.brokenrules)
            self.broken(art, 'ssn', 'fits')

            art.ssn = None
            self.true(saveok(art, 'ssn'))

            # Test longtext
            art = artist()
            art.firstname = uuid4().hex
            art.lastname  = uuid4().hex
            art.lifeform  = uuid4().hex
            art.password  = bytes([random.randint(0, 255) for _ in range(32)])
            art.phone     = '1' * 7
            art.email     = 'username@domain.tld'
            art.ssn       = V * 11
            if type(art) is singer:
                art.voice     = uuid4().hex
                art.register  = 'laryngealization'

            map = art.orm.mappings['bio']
            self.false(map.isfixed)
            self.eq('longtext', map.dbtype)
            self.none(art.bio)

            art.bio = V * map.max
            self.true(saveok(art, 'bio'))

            art.bio = V * (map.max + 1)
            self.one(art.brokenrules)
            self.broken(art, 'bio', 'fits')

            art.bio = V * (map.min - 1)
            self.one(art.brokenrules)
            self.broken(art, 'bio', 'fits')

            art.bio = None
            self.true(saveok(art, 'bio'))

    def it_calls_explicit_float_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = builtins.type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        comp = component.getvalid()

        map = comp.orm.mappings['width']
        self.type(float, comp.width)
        self.eq(-9999.9, map.min)
        self.eq(9999.9, map.max)

        comp.width = -100
        self.eq(100, comp.width)

        saveok(comp, 'width')

    def it_calls_explicit_int_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = builtins.type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        art = artist.getvalid()

        map = art.orm.mappings['phone']
        self.type(int, art.phone)
        self.eq(1000000, map.min)
        self.eq(9999999, map.max)

        art.phone = '555-5555'
        self.eq(5555555, art.phone)

        saveok(art, 'phone')

    def it_calls_num_attr_on_entity(self):
        def saveok(e, attr):
            getattr(e, 'save')()
            e1 = builtins.type(e)(e.id)
            return getattr(e, attr) == getattr(e1, attr)

        constraints = (
            {
                'cls': artifact,
                'attr': 'price',
                'type': 'decimal(12, 2)',
                'signed': True,
            },
            {
                'cls': component,
                'attr': 'height',
                'type': 'double(12, 2)',
                'signed': True,
            },
            {
                'cls': component,
                'attr': 'weight',
                'type': 'double(8, 7)',
                'signed': True,
            },
            {
                'cls': concert,
                'attr': 'ticketprice',
                'type': 'tinyint',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'tinyint unsigned',
                'attr': 'duration',
                'signed': False,
            },
            {
                'cls': concert,
                'type': 'mediumint',
                'attr': 'attendees',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'mediumint unsigned',
                'attr': 'capacity',
                'signed': False,
            },
            {
                'cls': artist,
                'type': 'smallint unsigned',
                'attr': 'weight',
                'signed': False,
            },
            {
                'cls': artist,
                'type': 'int',
                'attr': 'networth',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'int unsigned',
                'attr': 'externalid',
                'signed': False,
            },
            {
                'cls': artifact,
                'type': 'bigint',
                'attr': 'weight',
                'signed': True,
            },
            {
                'cls': concert,
                'type': 'bigint unsigned',
                'attr': 'externalid1',
                'signed': False,
            },
        )
        for const in constraints:
            type    =  const['type']
            attr    =  const['attr']
            cls     =  const['cls']
            signed  =  const['signed']

            if 'double' in type:
                pytype =  float
            elif 'decimal' in type:
                pytype = dec
            elif 'int' in type:
                pytype = int

            dectype = pytype in (float, dec)

            obj = cls.getvalid()
            map = obj.orm.mappings[attr]

            min, max = map.min, map.max

            self.eq(type, map.dbtype, str(const))
            self.eq(signed, map.signed, str(const))
            self.true(hasattr(obj, attr))
            self.zero(obj.brokenrules)
            self.type(pytype, getattr(obj, attr))

            # Test default
            self.eq(pytype(), getattr(obj, attr))
            self.true(saveok(obj, attr))

            # Test min
            setattr(obj, attr, min)
            self.zero(obj.brokenrules)
            self.true(saveok(obj, attr))

            setattr(obj, attr, getattr(obj, attr) - 1)
            self.one(obj.brokenrules)
            self.broken(obj, attr, 'fits')

            # Test max
            setattr(obj, attr, max)
            self.zero(obj.brokenrules)
            self.true(saveok(obj, attr))

            setattr(obj, attr, getattr(obj, attr) + 1)
            self.one(obj.brokenrules)
            self.broken(obj, attr, 'fits')

            # Test given an int as a str
            v = random.randint(int(min), int(max))
            setattr(obj, attr, str(v))
            self.eq(pytype(v), getattr(obj, attr))

            # Test given a float/decimal as a str. This also ensures that floats and
            # Decimals round to their scales.
            if pytype is not int:
                v = round(random.uniform(float(min), float(max)), map.scale)
                setattr(obj, attr, str(v))

                self.eq(round(pytype(v), map.scale), 
                        getattr(obj, attr), str(const))

                self.type(pytype, getattr(obj, attr))
                self.true(saveok(obj, attr))

            # Nullable
            setattr(obj, attr, None)
            self.zero(obj.brokenrules)
            self.true(saveok(obj, attr))

    def it_calls_datetime_attr_on_entity(self):
        utc = timezone.utc

        # It converts naive datetime to UTC
        art = artist.getvalid()
        self.none(art.dob)
        art.dob = '2004-01-10'
        self.type(primative.datetime, art.dob)
        self.type(primative.datetime, art.dob)
        expect = datetime(2004, 1, 10, tzinfo=utc)
        self.eq(expect, art.dob)
       
        # Save, reload, test
        art.save()
        self.eq(expect, artist(art.id).dob)
        self.type(primative.datetime, artist(art.id).dob)

        # It converts aware datetime to UTC
        aztz = dateutil.tz.gettz('US/Arizona')
        azdt = datetime(2003, 10, 11, 10, 13, 46, tzinfo=aztz)
        art.dob = azdt
        expect = azdt.astimezone(utc)

        self.eq(expect, art.dob)

        # Save, reload, test
        art.save()
        self.eq(expect, artist(art.id).dob)
        self.type(primative.datetime, artist(art.id).dob)

        # It converts backt to AZ time using string tz
        self.eq(azdt, art.dob.astimezone('US/Arizona'))

        # Test invalid date times
        art = art.getvalid()
        
        # Python can do a 1 CE, but MySQL can't so this should break validation.
        art.dob = datetime(1, 1, 1)
        self.one(art.brokenrules)
        self.broken(art, 'dob', 'fits')

        # Ensure microseconds are persisted
        ms = random.randint(100000, 999999)
        art.dob = primative.datetime('9999-12-31 23:59:59.%s' % ms)
        art.save()
        self.eq(ms, artist(art.id).dob.microsecond)

        # The max is 9999-12-31 23:59:59.999999
        art.dob = primative.datetime('9999-12-31 23:59:59.999999')
        art.save()
        self.eq(art.dob, artist(art.id).dob)
        
    def it_calls_str_propertys_setter_on_entity(self):
        class persons(orm.entities):
            pass

        class person(orm.entity):
            firstname = orm.fieldmapping(str)

        p = person()

        uuid = uuid4().hex
        p.firstname = uuid

        self.eq(uuid, p.firstname)
        self.zero(p.brokenrules)

        # Ensure whitespace in strip()ed from str values.
        p.firstname = ' \n\t' + uuid + ' \n\t'
        self.eq(uuid, p.firstname)
        self.zero(p.brokenrules)

    def it_calls_save_on_entity(self):
        art = artist.getvalid()

        # Test creating and retrieving an entity
        art.firstname = uuid4().hex
        art.lastname  = uuid4().hex
        art.lifeform  = uuid4().hex

        self.true(art.orm.isnew)
        self.false(art.orm.isdirty)

        self.chronicles.clear()
        art.save()
        self.one(self.chronicles)
        self._chrons(art, 'create')

        self.false(art.orm.isnew)
        self.false(art.orm.isdirty)

        art1 = artist(art.id)

        self.false(art1.orm.isnew)
        self.false(art1.orm.isdirty)

        for map in art1.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                expect = getattr(art, map.name)
                actual = getattr(art1, map.name)
                self.eq(expect, actual, map.name)

        # Test changing, saving and retrieving an entity
        art1.firstname  =  uuid4().hex
        art1.lastname   =  uuid4().hex
        art1.phone      =  '2' * 7
        art1.lifeform   =  uuid4().hex
        art1.style      =  uuid4().hex
        art1.weight     += 1
        art1.networth   =  1
        art1.dob        =  primative.datetime.now().replace(tzinfo=timezone.utc)
        art1.password   = bytes([random.randint(0, 255) for _ in range(32)])
        art1.ssn        = '2' * 11
        art1.bio        = uuid4().hex
        art1.email      = 'username1@domain.tld'
        art1.title      = uuid4().hex[0]
        art1.phone2     = uuid4().hex[0]
        art1.email_1    = uuid4().hex[0]

        self.false(art1.orm.isnew)
        self.true(art1.orm.isdirty)

        # Ensure that changing art1's properties don't change art's. This
        # problem is likely to not reoccure, but did come up in early
        # development.
        for prop in art.orm.properties:
            if prop == 'id':
                self.eq(getattr(art1, prop), getattr(art, prop), prop)
            else:
                if prop in ('createdat', 'updatedat'):
                    continue
                self.ne(getattr(art1, prop), getattr(art, prop), prop)

        self.chronicles.clear()
        art1.save()
        self._chrons(art1, 'update')

        self.false(art1.orm.isnew)
        self.false(art1.orm.isdirty)

        art2 = artist(art.id)

        for map in art2.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                if map.isdatetime:
                    name = map.name
                    dt1 = getattr(art1, name)
                    dt2 = getattr(art2, name)
                    setattr(art1, name, dt1.replace(second=0, microsecond=0))
                    setattr(art2, name, dt2.replace(second=0, microsecond=0))
                self.eq(getattr(art1, map.name), getattr(art2, map.name))

    def it_fails_to_save_broken_entity(self):
        art = artist()

        art.firstname = 'x' * 256
        self.broken(art, 'firstname', 'fits')

        try:
            art.save()
        except Exception as ex:
            self.type(BrokenRulesError, ex)
        else:
            self.fail('Exception not thrown')

    def it_hard_deletes_entity(self):
        for i in range(2):
            art = artist.getvalid()

            art.save()

            self.expect(None, lambda: artist(art.id))

            if i:
                art.lastname  = uuid4().hex
                self.zero(art.brokenrules)
            else:
                art.lastname  = 'X' * 265 # break rule
                self.one(art.brokenrules)

            self.chronicles.clear()
            art.delete()
            self.one(self.chronicles)
            self._chrons(art, 'delete')

            self.eq((True, False, False), art.orm.persistencestate)

            self.expect(db.RecordNotFoundError, lambda: artist(art.id))

    def it_deletes_from_entitys_collections(self):
        # Create artist with a presentation and save
        art = artist.getvalid()
        pres = presentation.getvalid()
        art.presentations += pres
        loc = location.getvalid()
        art.presentations.last.locations += loc
        art.save()

        # Reload
        art = artist(art.id)

        # Test presentations and its trash collection
        self.one(art.presentations)
        self.zero(art.presentations.orm.trash)

        self.one(art.presentations.first.locations)
        self.zero(art.presentations.first.locations.orm.trash)

        # Remove the presentation
        pres = art.presentations.pop()

        # Test presentations and its trash collection
        self.zero(art.presentations)
        self.one(art.presentations.orm.trash)

        self.one(art.presentations.orm.trash.first.locations)
        self.zero(art.presentations.orm.trash.first.locations.orm.trash)

        self.chronicles.clear()
        art.save()
        self.two(self.chronicles)
        self._chrons(pres, 'delete')
        self._chrons(pres.locations.first, 'delete')

        art = artist(art.id)
        self.zero(art.presentations)
        self.zero(art.presentations.orm.trash)

        self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))


    def it_raises_exception_on_unknown_id(self):
        for cls in singer, artist:
            try:
                cls(uuid4())
            except Exception as ex:
                self.type(db.RecordNotFoundError, ex)
            else:
                self.fail('Exception not thrown')

    def it_calls_dir_on_entity(self):
        # Make sure mapped properties are returned when dir() is called.
        # Also ensure there is only one of each property in the directory. If
        # there are more, entitymeta may not be deleting the original property
        # from the class body.
        art = artist()
        dir = builtins.dir(art)
        for p in art.orm.properties:
            self.eq(1, dir.count(p))

    def it_calls_dir_on_subentity(self):
        # Make sure mapped properties are returned when dir() is called.  Also
        # ensure there is only one of each property in the directory. If there
        # are more, entitymeta may not be deleting the original property from
        # the class body.

        art = artist()
        sng = singer()
        dir = builtins.dir(sng)

        # Non-inherited
        for p in art.orm.properties:
            self.eq(1, dir.count(p))

        # Non-inherited
        for p in sng.orm.properties:
            self.eq(1, dir.count(p))

    def it_calls_dir_on_association(self):
        art = artist()
        art.artifacts += artifact()
        aa = art.artist_artifacts.first

        d = dir(aa)

        for prop in aa.orm.properties:
            self.eq(1, d.count(prop))

    def it_reconnects_closed_database_connections(self):
        def art_onafterreconnect(src, eargs):
            drown()

        def drown():
            pool = db.pool.getdefault()
            for conn in pool._in + pool._out:
                conn.kill()

        # Kill all connections in and out of the pool
        drown()

        art = artist.getvalid()

        # Subscribe to the onafterreconnect event so the connections can
        # be re-drowned. This will ensure that the connections never get
        # sucessfully reconnected which will cause an OperationalError.
        art.onafterreconnect += art_onafterreconnect

        self.expect(MySQLdb.OperationalError, lambda: art.save())

        # Make sure the connections have been killed.
        drown()

        # Unsubscribe so .save() is allowed to reconnect. This will cause
        # save() to be successful.
        art.onafterreconnect -= art_onafterreconnect

        self.expect(None, lambda: art.save())

        # Ensure e._load recovers correctly from a disconnect like we did with
        # e.save() above.  (Normally, __init__(id) for an entity calls
        # self._load(id) internally.  Here we call art._load directly so we
        # have time to subscribe to art's onafterreconnect event.)
        drown()
        id, art = art.id, artist.getvalid()
        art.onafterreconnect += art_onafterreconnect

        self.expect(MySQLdb.OperationalError, lambda: art._load(id))

        art.onafterreconnect -= art_onafterreconnect

        self.expect(None, lambda: art._load(id))

        # Ensure that es.load() recovers correctly from a reconnect
        arts = artists(id=id)

        # Subscribe to event to ensure loads fail. This will load arts first
        # then subscribe so we have to clear arts next.
        arts.onafterreconnect += art_onafterreconnect

        # Subscribing to the event above loads arts so call the clear() method.
        arts.clear()

        # In addition to clear()ing the collection, flag the collection as
        # unloaded to ensure an attempt is made to reload the collection when
        # `arts.count` is called below.
        arts.orm.isloaded = False

        # Make sure connections are drowned.
        drown()

        # Calling count (or any attr) forces a load. Enuser the load causing an
        # exception due to the previous drown()ing of connections.
        self.expect(MySQLdb.OperationalError, lambda: arts.count)

        # Remove the drowning event. 
        arts.onafterreconnect -= art_onafterreconnect

        # Drown again. We want to ensure that the next load will cause a
        # recovery form the dead connection.
        drown()

        # Clear to force a reload
        arts.clear()

        # Calling the count property (like any attr) will load arts. No
        # exception will be thrown because the drowning event handler was
        # unsubscribed from.
        self.expect(None, lambda: arts.count)

    def it_mysql_warnings_are_exceptions(self):
        def warn(cur):
            cur.execute('select 0/0')

        exec = db.executioner(warn)

        self.expect(_mysql_exceptions.Warning, lambda: exec.execute())

    def it_saves_multiple_graphs(self):
        art1 = artist.getvalid()
        art2 = artist.getvalid()
        sng = singer.getvalid()

        pres     =  presentation.getvalid()
        sngpres  =  presentation.getvalid()
        loc      =  location.getvalid()

        art1.presentations += pres
        sng.presentations += sngpres
        art1.presentations.first.locations += loc

        arts = artists()
        for _ in range(2):
            arts += artist.getvalid()

        art1.save(art2, arts, sng)

        for e in art1 + art2 + arts + sng:
            self.expect(None, lambda: artist(e.id))

        self.expect(None, lambda: presentation(pres.id))
        self.expect(None, lambda: presentation(sngpres.id))
        self.expect(None, lambda: location(loc.id))
        self.expect(None, lambda: singer(sng.id))

        art1.presentations.pop()

        art2.save(art1, arts)

        for e in art1 + art2 + arts + sng:
            self.expect(None, lambda: artist(e.id))

        self.expect(None, lambda: singer(sng.id))

        self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

        for e in art1 + art2 + arts + sng:
            e.delete()
            self.expect(db.RecordNotFoundError, lambda: artist(pres.id))

        arts.save(art1, art2, sng)

        for e in art1 + art2 + arts + sng:
            self.expect(None, lambda: artist(e.id))

    def it_rollsback_save_of_entities(self):
        # Create two artists
        pres = presentation.getvalid()
        art = artist.getvalid()
        art.presentations += pres

        arts = artists()

        for _ in range(2):
            arts += artist.getvalid()
            arts.last.firstname = uuid4().hex

        def saveall():
            pres.save(arts.first, arts.second)

        saveall()

        # First, break the save method so a rollback occurs, and test the
        # rollback. Second, fix the save method and ensure success.
        for i in range(2):
            if i:
                # Restore original save method
                arts.second._save = save

                # Update property 
                arts.first.firstname = new = uuid4().hex
                saveall()
                self.eq(new, artist(arts.first.id).firstname)
            else:
                # Update property
                old, arts.first.firstname = arts.first.firstname, uuid4().hex

                # Break save method
                save, arts.second._save = arts.second._save, lambda x: 0/0

                self.expect(ZeroDivisionError, saveall)

                self.eq(old, artist(arts.first.id).firstname)

    def it_calls_inherited_property(self):
        s = singer()
        uuid = uuid4().hex
        s.firstname = uuid 
        self.eq(uuid, s.firstname)

    def it_inherited_class_has_same_id_as_super(self):
        s = singer()
        self.eq(s.orm.super.id, s.id)

    def it_saves_and_loads_inherited_entity(self):
        sng = singer.getvalid()
        sng.firstname  =  fname  =  uuid4().hex
        sng.voice      =  voc    =  uuid4().hex
        sng.save()

        art = sng1 = None
        def load():
            nonlocal art, sng1
            art   = artist(sng.id)
            sng1 = singer(sng.id)

        self.expect(None, load)

        self.eq(fname,  art.firstname)
        self.eq(fname,  sng1.firstname)
        self.eq(voc,    sng1.voice)

    def it_saves_subentities(self):
        chrons = self.chronicles

        sngs = singers()

        for _ in range(2):
            sngs += singer.getvalid()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex

        chrons.clear()
        sngs.save()

        self.four(chrons)
        self.eq(chrons.where('entity', sngs.first).first.op, 'create')
        self.eq(chrons.where('entity', sngs.second).first.op, 'create')
        self.eq(chrons.where('entity', sngs.first.orm.super).first.op, 'create')
        self.eq(chrons.where('entity', sngs.second.orm.super).first.op, 'create')

        for sng in sngs:
            sng1 = singer(sng.id)

            for map in sng.orm.mappings:
                if not isinstance(map, orm.fieldmapping):
                    continue

                self.eq(getattr(sng, map.name), getattr(sng1, map.name))

    def it_rollsback_save_of_subentities(self):
        # Create two singers
        sngs = singers()

        for _ in range(2):
            sngs += singer.getvalid()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex

        sngs.save()

        # First, break the save method so a rollback occurs, and test the
        # rollback. Second, fix the save method and ensure success.
        for i in range(2):
            if i:
                # Restore original save method
                sngs.second._save = save

                # Update property 
                sngs.first.firstname = new = uuid4().hex
                sngs.save()
                self.eq(new, singer(sngs.first.id).firstname)
            else:
                # Update property
                old, sngs.first.firstname = sngs.first.firstname, uuid4().hex

                # Break save method
                save, sngs.second._save = sngs.second._save, lambda x: 0/0

                self.expect(ZeroDivisionError, lambda: sngs.save())
                self.eq(old, singer(sngs.first.id).firstname)

    def subentity_contains_reference_to_composite(self):
        chrons = self.chronicles

        sng = singer.getvalid()
        for _ in range(2):
            pres = presentation.getvalid()
            sng.presentations += pres

            pres.locations += location.getvalid()

        sng.save()

        for i, sng1 in enumerate((sng, singer(sng.id))):
            for pres in sng1.presentations:
                self.is_(sng1,            pres.singer)
                self.is_(sng1.orm.super,  pres.artist)
                self.eq(pres.singer.id,   pres.artist.id)
                self.type(artist,         sng1.orm.super)
                self.type(artist,         pres.singer.orm.super)

                chrons.clear()
                locs = sng.presentations[pres].locations.sorted('id')
                locs1 = pres.locations.sorted('id')

                loc, loc1 = locs.first, locs1.first

                if i:
                    self.one(chrons)
                    self.eq(chrons.where('entity', pres.locations).first.op, 'retrieve')
                else:
                    self.zero(chrons)

                self.one(locs)
                self.one(locs1)
                self.eq(loc.id, loc1.id)

        sng = singer.getvalid()

        for _ in range(2):
            sng.concerts += concert.getvalid()
            sng.concerts.last.locations += location.getvalid()

        sng.save()

        for i, sng in enumerate((sng, singer(sng.id))):
            for conc in sng.concerts:
                chrons.clear()
                self.is_(sng,            conc.singer)
                self.is_(sng.orm.super,  conc.singer.orm.super)
                self.type(artist,        sng.orm.super)
                self.type(artist,        conc.singer.orm.super)

                self.zero(chrons)

                chrons.clear()
                locs = sng.concerts[conc].locations.sorted('id')
                locs1 = conc.locations.sorted('id')

                loc, loc1 = locs.first, locs1.first

                if i:
                    self.eq(chrons.where('entity', conc.locations).first.op, 'retrieve')
                    self.eq(chrons.where('entity', conc.orm.super).first.op, 'retrieve')
                    self.two(chrons)
                else:
                    self.zero(chrons)

                self.one(locs)
                self.one(locs1)
                self.eq(loc.id, loc1.id)

    def it_loads_and_saves_subentitys_constituents(self):
        chrons = self.chronicles

        # Ensure that a new composite has a constituent object with zero
        # elements
        sng = singer.getvalid()
        self.zero(sng.presentations)

        # Ensure a saved composite object with zero elements in a constiuent
        # collection loads with zero the constiuent collection containing zero
        # elements.
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex

        self.zero(sng.presentations)

        sng.save()

        self.zero(sng.presentations)

        sng = singer(sng.id)
        self.zero(sng.presentations)
        self.is_(sng,            sng.presentations.singer)
        self.is_(sng.orm.super,  sng.presentations.artist)

        sng = singer.getvalid()

        sng.presentations += presentation.getvalid()
        sng.presentations += presentation.getvalid()

        for pres in sng.presentations:
            pres.name = uuid4().hex

        chrons.clear()
        sng.save()

        self.four(chrons)
        press = sng.presentations
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'create')
        self.eq(chrons.where('entity', sng).first.op, 'create')
        self.eq(chrons.where('entity', press.first).first.op, 'create')
        self.eq(chrons.where('entity', press.second).first.op, 'create')

        sng1 = singer(sng.id)

        chrons.clear()
        press = sng1.presentations

        self.two(chrons)

        self.eq(chrons.where('entity', press).first.op, 'retrieve')

        sng.presentations.sort()
        sng1.presentations.sort()
        for pres, pres1 in zip(sng.presentations, sng1.presentations):
            for map in pres.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(pres, map.name), getattr(pres1, map.name))
            
            self.is_(pres1.singer, sng1)
            self.is_(pres1.artist, sng1.orm.super)

        # Create some locations with the presentations, save singer, reload and
        # test
        for pres in sng.presentations:
            for _ in range(2):
                pres.locations += location.getvalid()

        chrons.clear()
        sng.save()

        self.four(chrons)

        locs = sng.presentations.first.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        locs = sng.presentations.second.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        sng1 = singer(sng.id)
        self.two(sng1.presentations)

        sng.presentations.sort()
        sng1.presentations.sort()
        for pres, pres1 in zip(sng.presentations, sng1.presentations):

            pres.locations.sort()

            chrons.clear()
            pres1.locations.sort()

            self.one(chrons)
            locs = pres1.locations
            self.eq(chrons.where('entity', locs).first.op, 'retrieve')

            for loc, loc1 in zip(pres.locations, pres1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(getattr(loc, map.name), getattr(loc1, map.name))
            
                self.is_(pres1, loc1.presentation)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        sng = singer.getvalid()
        press = presentations()

        for _ in range(2):
            press += presentation.getvalid()

        sng.presentations += press

        for i in range(2):
            if i:
                sng.save()
                sng = singer(sng.id)

            self.eq(press.count, sng.presentations.count)

            for pres in sng.presentations:
                self.is_(sng, pres.singer)
                self.is_(sng.orm.super, pres.artist)

    def it_loads_and_saves_subentitys_subentity_constituents(self):
        chrons = self.chronicles

        # Ensure that a new composite has a constituent subentities with zero
        # elements
        sng = singer.getvalid()
        self.zero(sng.concerts)

        # Ensure a saved composite object with zero elements in a subentities
        # constiuent collection loads with zero the constiuent collection
        # containing zero elements.
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice     = uuid4().hex

        self.zero(sng.concerts)

        sng.save()

        self.zero(sng.concerts)

        sng = singer(sng.id)
        self.zero(sng.concerts)
        self.is_(sng,            sng.concerts.singer)
        self.is_(sng.orm.super,  sng.concerts.artist)

        sng = singer.getvalid()

        sng.concerts += concert.getvalid()
        sng.concerts += concert.getvalid()

        for conc in sng.concerts:
            conc.name = uuid4().hex

        chrons.clear()
        sng.save()

        self.six(chrons)
        concs = sng.concerts
        self.eq(chrons.where('entity',  sng.orm.super).first.op,    'create')
        self.eq(chrons.where('entity',  sng).first.op,              'create')
        self.eq(chrons.where('entity',  concs.first).first.op,      'create')
        self.eq(chrons.where('entity',  concs.second).first.op,     'create')
        self.eq(chrons.where('entity',  concs[0].orm.super)[0].op,  'create')
        self.eq(chrons.where('entity',  concs[1].orm.super)[0].op,  'create')

        sng1 = singer(sng.id)

        chrons.clear()
        concs = sng1.concerts

        self.two(chrons)

        self.eq(chrons.where('entity', concs).first.op, 'retrieve')
        self.eq(chrons.where('entity', concs[0].orm.super).first.op, 'retrieve')
        self.eq(chrons.where('entity', concs[1].orm.super).first.op, 'retrieve')

        sng.concerts.sort()
        sng1.concerts.sort()
        for conc, conc1 in zip(sng.concerts, sng1.concerts):
            for map in conc.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(conc, map.name), getattr(conc1, map.name))
            
            self.is_(conc1.singer, sng1)

        # Create some locations with the concerts, save singer, reload and
        # test
        for conc in sng.concerts:
            for _ in range(2):
                conc.locations += location.getvalid()

        chrons.clear()
        sng.save()

        self.four(chrons)

        locs = sng.concerts.first.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        locs = sng.concerts.second.locations
        self.eq(chrons.where('entity', locs.first).first.op, 'create')
        self.eq(chrons.where('entity', locs.second).first.op, 'create')

        sng1 = singer(sng.id)
        self.two(sng1.concerts)

        sng.concerts.sort()
        sng1.concerts.sort()
        for conc, conc1 in zip(sng.concerts, sng1.concerts):

            conc.locations.sort()

            chrons.clear()
            conc1.locations.sort()

            locs = conc1.locations

            self.eq(chrons.where('entity', locs).first.op, 'retrieve')
            self.eq(chrons.where('entity', conc1.orm.super).first.op, 'retrieve')
            self.two(chrons)

            for loc, loc1 in zip(conc.locations, conc1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(getattr(loc, map.name), getattr(loc1, map.name))
            
                self.is_(conc1, loc1.concert)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        sng = singer.getvalid()
        concs = concerts()

        for _ in range(2):
            concs += concert.getvalid()

        sng.concerts += concs

        for i in range(2):
            if i:
                sng.save()
                sng = singer(sng.id)

            self.eq(concs.count, sng.concerts.count)

            for conc in sng.concerts:
                self.is_(sng, conc.singer)
                self.type(artist, sng.orm.super)

    def it_updates_subentities_constituents_properties(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        for _ in range(2):
            sng.presentations += presentation.getvalid()
            sng.presentations.last.name = uuid4().hex

            for _ in range(2):
                sng.presentations.last.locations += location.getvalid()
                sng.presentations.last.locations.last.description = uuid4().hex

        sng.save()

        sng1 = singer(sng.id)
        for pres in sng1.presentations:
            pres.name = uuid4().hex
            
            for loc in pres.locations:
                loc.description = uuid4().hex

        chrons.clear()
        sng1.save()
        self.six(chrons)
        for pres in sng1.presentations:
            self.eq(chrons.where('entity', pres).first.op, 'update')
            for loc in pres.locations:
                self.eq(chrons.where('entity', loc).first.op, 'update')
            

        sng2 = singer(sng.id)
        press = sng.presentations, sng1.presentations, sng2.presentations
        for pres, pres1, pres2 in zip(*press):

            # Make sure the properties were changed
            self.ne(getattr(pres2, 'name'), getattr(pres,  'name'))

            # Make user sng1.presentations props match those of sng2
            self.eq(getattr(pres2, 'name'), getattr(pres1, 'name'))

            locs = pres.locations, pres1.locations, pres2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(getattr(loc2, 'description'), getattr(loc,  'description'))

                # Make user sng1 locations props match those of sng2
                self.eq(getattr(loc2, 'description'), getattr(loc1, 'description'))

    def it_updates_subentitys_subentities_constituents_properties(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        for _ in range(2):
            sng.concerts += concert.getvalid()
            sng.concerts.last.record = uuid4().hex

            for _ in range(2):
                sng.concerts.last.locations += location.getvalid()
                sng.concerts.last.locations.last.description = uuid4().hex

        sng.save()

        sng1 = singer(sng.id)
        for conc in sng1.concerts:
            conc.record = uuid4().hex
            conc.name   = uuid4().hex
            
            for loc in conc.locations:
                loc.description = uuid4().hex

        chrons.clear()
        sng1.save()
        self.eight(chrons)
        for conc in sng1.concerts:
            self.eq(chrons.where('entity', conc).first.op, 'update')
            self.eq(chrons.where('entity', conc.orm.super).first.op, 'update')
            for loc in conc.locations:
                self.eq(chrons.where('entity', loc).first.op, 'update')
            

        sng2 = singer(sng.id)
        concs = (sng.concerts, sng1.concerts, sng2.concerts)
        for conc, conc1, conc2 in zip(*concs):
            # Make sure the properties were changed
            self.ne(getattr(conc2, 'record'), getattr(conc,  'record'))
            self.ne(getattr(conc2, 'name'),   getattr(conc,  'name'))

            # Make user sng1.concerts props match those of sng2
            self.eq(getattr(conc2, 'record'), getattr(conc1, 'record'))
            self.eq(getattr(conc2, 'name'),   getattr(conc1, 'name'))

            locs = conc.locations, conc1.locations, conc2.locations
            for loc, loc1, loc2 in zip(*locs):
                # Make sure the properties were changed
                self.ne(getattr(loc2, 'description'), getattr(loc,  'description'))

                # Make user sng1 locations props match those of sng2
                self.eq(getattr(loc2, 'description'), getattr(loc1, 'description'))

    def it_saves_and_loads_subentity_constituent(self):
        chrons = self.chronicles

        # Make sure the constituent is None for new composites
        pres = presentation.getvalid()

        chrons.clear()
        self.none(pres.artist)
        self.zero(chrons)

        self.zero(pres.brokenrules)

        # Test setting an entity constituent then test saving and loading
        sng = singer.getvalid()
        pres.artist = sng
        self.is_(sng, pres.artist)

        chrons.clear()
        pres.save()
        self.three(chrons)
        self.eq(chrons.where('entity',  sng).first.op,            'create')
        self.eq(chrons.where('entity',  sng.orm.super).first.op,  'create')
        self.eq(chrons.where('entity',  pres).first.op,           'create')

        # Load by artist then lazy-load presentations to test
        art1 = artist(pres.artist.id)
        self.one(art1.presentations)
        self.eq(art1.presentations.first.id, pres.id)

        # Load by presentation and lazy-load artist to test
        pres1 = presentation(pres.id)

        chrons.clear()
        self.eq(pres1.artist.id, pres.artist.id)
        self.one(chrons)
        self.eq(chrons.where('entity', pres1.artist).first.op,  'retrieve')

        sng1 = singer.getvalid()
        pres1.artist = sng1

        chrons.clear()
        pres1.save()

        self.three(chrons)
        self.eq(chrons.where('entity', sng1).first.op,  'create')
        self.eq(chrons.where('entity', sng1.orm.super).first.op, 'create')
        self.eq(chrons.where('entity', pres1).first.op, 'update')

        pres2 = presentation(pres1.id)
        self.eq(sng1.id, pres2.artist.id)
        self.ne(sng1.id, sng.id)

        # Test deeply-nested (>2)
        # Set entity constuents, save, load, test
       
        loc = location.getvalid()
        self.none(loc.presentation)

        loc.presentation = pres = presentation.getvalid()
        self.is_(pres, loc.presentation)

        chrons.clear()
        self.none(loc.presentation.artist)
        self.zero(chrons)

        loc.presentation.artist = sng = singer.getvalid()
        self.is_(sng, loc.presentation.artist)

        loc.save()

        self.four(chrons)
        self.eq(chrons.where('entity',  loc).first.op,               'create')
        self.eq(chrons.where('entity',  loc.presentation).first.op,  'create')
        self.eq(chrons.where('entity',  sng).first.op,               'create')
        self.eq(chrons.where('entity',  sng.orm.super).first.op,     'create')

        chrons.clear()
        loc1 = location(loc.id)
        pres1 = loc1.presentation

        self.eq(loc.id, loc1.id)
        self.eq(loc.presentation.id, loc1.presentation.id)
        self.eq(loc.presentation.artist.id, loc1.presentation.artist.id)

        self.three(chrons)
        self.eq(chrons.where('entity',  loc1).first.op,          'retrieve')
        self.eq(chrons.where('entity',  pres1).first.op,         'retrieve')
        self.eq(chrons.where('entity',  pres1.artist).first.op,  'retrieve')

        # Change the artist
        loc1.presentation.artist = sng1 = singer.getvalid()

        chrons.clear()
        loc1.save()

        self.three(chrons)
        pres1 = loc1.presentation

        self.eq(chrons.where('entity',  pres1).first.op,           'update')
        self.eq(chrons.where('entity',  sng1).first.op,            'create')
        self.eq(chrons.where('entity',  sng1.orm.super).first.op,  'create')

        loc2 = location(loc1.id)
        self.eq(loc1.presentation.artist.id, loc2.presentation.artist.id)
        self.ne(sng.id, loc2.presentation.artist.id)

        # Note: Going up the graph, mutating attributes and persisting lower in
        # the graph won't work because of the problem of infinite recursion.
        # The below tests demonstrate this.

        # Assign a new name
        name = uuid4().hex
        loc2.presentation.artist.presentations.first.name = name

        # The presentation objects here aren't the same reference so they will
        # have different states.
        self.ne(loc2.presentation.name, name)

        chrons.clear()
        loc2.save()

        self.zero(chrons)

        loc2 = location(loc2.id)

        self.one(chrons)
        self.eq(chrons.where('entity',  loc2).first.op,   'retrieve')

        # The above save() didn't save the new artist's presentation collection
        # so the new name will not be present in the reloaded presentation
        # object.
        self.ne(loc2.presentation.name, name)
        self.ne(loc2.presentation.artist.presentations.first.name, name)

    def it_saves_and_loads_subentities_subentity_constituent(self):
        chrons = self.chronicles

        # Make sure the constituent is None for new composites
        conc = concert.getvalid()

        chrons.clear()
        self.none(conc.singer)
        self.expect(AttributeError, lambda: conc.artist)
        self.zero(chrons)

        self.zero(conc.brokenrules)

        # Test setting an entity constituent then test saving and loading
        sng = singer.getvalid()
        conc.singer = sng
        self.is_(sng, conc.singer)

        chrons.clear()
        conc.save()
        self.four(chrons)
        self.eq(chrons.where('entity',  sng).first.op,             'create')
        self.eq(chrons.where('entity',  sng.orm.super).first.op,   'create')
        self.eq(chrons.where('entity',  conc).first.op,            'create')
        self.eq(chrons.where('entity',  conc.orm.super).first.op,  'create')

        # Load by singer then lazy-load concerts to test
        sng1 = singer(conc.singer.id)
        self.one(sng1.concerts)
        self.eq(sng1.concerts.first.id, conc.id)

        # Load by concert and lazy-load singer to test
        conc1 = concert(conc.id)

        chrons.clear()
        self.eq(conc1.singer.id, conc.singer.id)

        self._chrons(conc1.singer,            'retrieve')
        self.one(chrons)

        sng1 = singer.getvalid()
        conc1.singer = sng1

        chrons.clear()
        conc1.save()

        self.four(chrons)
        self._chrons(sng1,             'create')
        self._chrons(sng1.orm.super,   'create')
        self._chrons(conc1,            'update')
        self._chrons(conc1.orm.super,  'update')

        conc2 = concert(conc1.id)
        self.eq(sng1.id, conc2.singer.id)
        self.ne(sng1.id, sng.id)

        # TODO Test deeply-nested (>2)
        # Set entity constuents, save, load, test

        # TODO We need to answer the question should loc.concert exist.
        # concert().locations exists, so it would seem that the answer would be
        # "yes". However, the logic for this would be strange since we would
        # need to query the mappings collection of each subentities of the
        # presentation collection to find a match. Plus, this seems like
        # a very unlikely way for someone to want to use the ORM. I would like 
        # to wait to see if this comes up in a real life situation before writing 
        # the logic and tests for this. 
        """
        self.expect(AttributeError, lambda: loc.concert)
       
        loc = location.getvalid()
        self.none(loc.concert)

        loc.concert = conc = concert.getvalid()
        self.is_(conc, loc.concert)

        chrons.clear()
        self.none(loc.concert.singer)
        self.zero(chrons)

        loc.concert.singer = sng = singer.getvalid()
        self.is_(sng, loc.concert.singer)

        loc.save()

        self.four(chrons)
        self.eq(chrons.where('entity',  loc).first.op,               'create')
        self.eq(chrons.where('entity',  loc.concert).first.op,  'create')
        self.eq(chrons.where('entity',  sng).first.op,               'create')
        self.eq(chrons.where('entity',  sng.orm.super).first.op,     'create')

        chrons.clear()
        loc1 = location(loc.id)
        conc1 = loc1.concert

        self.eq(loc.id, loc1.id)
        self.eq(loc.concert.id, loc1.concert.id)
        self.eq(loc.concert.singer.id, loc1.concert.singer.id)

        self.three(chrons)
        self.eq(chrons.where('entity',  loc1).first.op,          'retrieve')
        self.eq(chrons.where('entity',  conc1).first.op,         'retrieve')
        self.eq(chrons.where('entity',  conc1.singer).first.op,  'retrieve')

        # Change the singer
        loc1.concert.singer = sng1 = singer.getvalid()

        chrons.clear()
        loc1.save()

        self.three(chrons)
        conc1 = loc1.concert

        self.eq(chrons.where('entity',  conc1).first.op,           'update')
        self.eq(chrons.where('entity',  sng1).first.op,            'create')
        self.eq(chrons.where('entity',  sng1.orm.super).first.op,  'create')

        loc2 = location(loc1.id)
        self.eq(loc1.concert.singer.id, loc2.concert.singer.id)
        self.ne(sng.id, loc2.concert.singer.id)

        # Note: Going up the graph, mutating attributes and persisting lower in
        # the graph won't work because of the problem of infinite recursion.
        # The below tests demonstrate this.

        # Assign a new name
        name = uuid4().hex
        loc2.concert.singer.concerts.first.name = name

        # The concert objects here aren't the same reference so they will
        # have different states.
        self.ne(loc2.concert.name, name)

        chrons.clear()
        loc2.save()

        self.zero(chrons)

        loc2 = location(loc2.id)

        self.one(chrons)
        self.eq(chrons.where('entity',  loc2).first.op,   'retrieve')

        # The above save() didn't save the new singer's concert collection
        # so the new name will not be present in the reloaded concert
        # object.
        self.ne(loc2.concert.name, name)
        self.ne(loc2.concert.singer.concerts.first.name, name)
        """

    def subentity_constituents_break_entity(self):
        pres = presentation.getvalid()
        pres.artist = singer.getvalid()

        # Get max lengths for various properties
        presmax  =  presentation.  orm.  mappings['name'].         max
        locmax   =  location.      orm.  mappings['description'].  max
        artmax   =  artist.        orm.  mappings['firstname'].    max
        x = 'x'

        pres.artist.firstname = x * (artmax + 1)
        self.one(pres.brokenrules)
        self.broken(pres, 'firstname', 'fits')

        pres.artist.firstname = uuid4().hex # Unbreak
        self.zero(pres.brokenrules)

        loc = location.getvalid()
        loc.description = x * (locmax + 1) # break

        loc.presentation = presentation.getvalid()
        loc.presentation.name = x * (presmax + 1) # break

        loc.presentation.artist = singer.getvalid()
        loc.presentation.artist.firstname = x * (artmax + 1) # break

        self.three(loc.brokenrules)
        for prop in 'description', 'name', 'firstname':
            self.broken(loc, prop, 'fits')

    def subentity_constituents_break_subentity(self):
        conc = concert.getvalid()
        conc.singer = singer.getvalid()

        # Break rule that art.firstname should be a str
        conc.singer.firstname = 'x' * 256 # Break

        self.one(conc.brokenrules)
        self.broken(conc, 'firstname', 'fits')

        conc.singer.firstname = uuid4().hex # Unbreak
        self.zero(conc.brokenrules)

    def it_rollsback_save_of_subentity_with_broken_constituents(self):
        sng = singer.getvalid()

        sng.presentations += presentation.getvalid()
        sng.presentations.last.name = uuid4().hex

        sng.presentations += presentation.getvalid()
        sng.presentations.last.name = uuid4().hex

        sng.concerts += concert.getvalid()
        sng.concerts.last.name = uuid4().hex

        # Cause the last presentation's invocation of save() to raise an
        # Exception to cause a rollback
        sng.presentations.last._save = lambda cur, followentitymapping: 1/0

        # Save expecting the ZeroDivisionError
        self.expect(ZeroDivisionError, lambda: sng.save())

        # Ensure state of sng was restored to original
        self.eq((True, False, False), sng.orm.persistencestate)

        # Ensure singer wasn't saved
        self.expect(db.RecordNotFoundError, lambda: singer(sng.id))

        # For each presentations and concerts, ensure state was not modified
        # and no presentation object was saved.
        for pres in sng.presentations:
            self.eq((True, False, False), pres.orm.persistencestate)
            self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))

        for conc in sng.concerts:
            self.eq((True, False, False), conc.orm.persistencestate)
            self.expect(db.RecordNotFoundError, lambda: concert(conc.id))

    def it_deletes_subentities(self):
        # Create two artists
        sngs = singers()

        for _ in range(2):
            sngs += singer.getvalid()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex
        
        self.chronicles.clear()
        sngs.save()
        self.four(self.chronicles)

        sng = sngs.shift()
        self.one(sngs)
        self.one(sngs.orm.trash)

        self.chronicles.clear()
        sngs.save()
        self.two(self.chronicles)
        self._chrons(sng, 'delete')
        self._chrons(sng.orm.super, 'delete')

        for sng in sng, sng.orm.super:
            self.expect(db.RecordNotFoundError, lambda: singer(sng.id))
            
        # Ensure the remaining singer and artist still exists in database
        for sng in sngs.first, sngs.first.orm.super:
            self.expect(None, lambda: singer(sng.id))

    def it_doesnt_needlessly_save_subentity(self):
        chrons = self.chronicles

        sng = singer.getvalid()
        sng.firstname  =  uuid4().hex
        sng.lastname   =  uuid4().hex
        sng.voice      =  uuid4().hex

        for i in range(2):
            chrons.clear()
            sng.save()
            
            if i == 0:
                self.two(chrons)
                self.eq(chrons.where('entity', sng).first.op,           'create')
                self.eq(chrons.where('entity', sng.orm.super).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

        # Dirty sng and save. Ensure the object was actually saved
        sng.firstname = uuid4().hex
        sng.voice     = uuid4().hex

        for i in range(2):
            chrons.clear()
            sng.save()
            if i == 0:
                self.two(chrons)
                self.eq(chrons.where('entity', sng).first.op,           'update')
                self.eq(chrons.where('entity', sng.orm.super).first.op, 'update')
            elif i == 1:
                self.zero(chrons)

        # Test constituents
        sng.presentations += presentation.getvalid()
        sng.concerts      += concert.getvalid()
        
        for i in range(2):
            chrons.clear()
            sng.save()

            if i == 0:
                self.three(chrons)
                self._chrons(sng.presentations.last,       'create')
                self._chrons(sng.concerts.last,            'create')
                self._chrons(sng.concerts.last.orm.super,  'create')
            elif i == 1:
                self.zero(chrons)

        # Test deeply-nested (>2) constituents
        sng.presentations.last.locations += location.getvalid()
        sng.concerts.last.locations      += location.getvalid()

        for i in range(2):
            chrons.clear()
            sng.save()

            if i == 0:
                self.two(chrons)
                self._chrons(sng.presentations.last.locations.last, 'create')
                self._chrons(sng.concerts.last.locations.last,      'create')
            elif i == 1:
                self.zero(chrons)

    def it_calls_id_on_subentity(self):
        sng = singer.getvalid()

        self.true(hasattr(sng, 'id'))
        self.type(uuid.UUID, sng.id)
        self.zero(sng.brokenrules)

    def it_calls_save_on_subentity(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        # Test creating and retrieving an entity
        self.eq((True, False, False), sng.orm.persistencestate)

        chrons.clear()
        sng.save()
        self.eq(chrons.where('entity', sng).first.op,           'create')
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'create')

        self.eq((False, False, False), sng.orm.persistencestate)

        sng1 = singer(sng.id)

        self.eq((False, False, False), sng1.orm.persistencestate)

        for map in sng1.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(sng, map.name), getattr(sng1, map.name))

        # Test changing, saving and retrieving an entity
        sng1.firstname = uuid4().hex
        sng1.lastname  = uuid4().hex
        sng1.voice     = uuid4().hex
        sng1.lifeform  = uuid4().hex
        sng1.phone     = '2' * 7
        sng1.register  = uuid4().hex
        sng1.style     = uuid4().hex
        sng1.weight    = 1
        sng1.networth  =- 1
        sng1.dob       = datetime.now()
        sng1.password  = bytes([random.randint(0, 255) for _ in range(32)])
        sng1.ssn       = '2' * 11
        sng1.bio       = uuid4().hex
        sng1.email     = 'username1@domain.tld'
        sng1.title     = uuid4().hex[0]
        sng1.phone2    = uuid4().hex[0]
        sng1.email_1   = uuid4().hex[0]

        self.eq((False, True, False), sng1.orm.persistencestate)

        # Ensure that changing sng1's properties don't change sng's. This
        # problem is likely to not reoccur, but did come up in early
        # development.

        for prop in sng.orm.properties:

            if prop == 'artifacts':
                # The subentity-to-associations relationship has not implemented
                # been implemented, so skip the call to sng.artifacts
                continue

            if prop == 'id':
                self.eq(getattr(sng1, prop), getattr(sng, prop), prop)
            else:
                if prop in ('createdat', 'updatedat'):
                    continue
                self.ne(getattr(sng1, prop), getattr(sng, prop), prop)

        sng1.save()

        self.eq((False, False, False), sng1.orm.persistencestate)

        sng2 = singer(sng.id)

        for map in sng2.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(sng1, map.name), getattr(sng2, map.name))

        # Ensure that the entity is persisted correctly when inherited and
        # non-inherited properties change.
        for prop in 'firstname', 'voice':
            sng = singer(sng.id)
            
            self.eq((False, False, False), sng.orm.persistencestate, prop)

            setattr(sng, prop, uuid4().hex)

            self.eq((False, True, False), sng.orm.persistencestate, prop)

            chrons.clear()
            sng.save()

            self.one(chrons)
            e = sng.orm.super if prop == 'firstname' else sng
            self.eq(chrons.where('entity', e).first.op, 'update')

            self.eq((False, False, False), sng.orm.persistencestate, prop)

    def it_fails_to_save_broken_subentity(self):
        sng = singer()

        for prop in 'firstname', 'voice':
            setattr(sng, prop, 'x' * 256)

            self.broken(sng, prop, 'fits')

            try:
                sng.save()
            except Exception as ex:
                self.type(BrokenRulesError, ex)
            else:
                self.fail('Exception not thrown')

    def it_hard_deletes_subentity(self):
        chrons = self.chronicles
        sng = singer.getvalid()

        sng.save()

        chrons.clear()
        sng.delete()
        self.two(chrons)
        self.eq(chrons.where('entity', sng).first.op,           'delete')
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'delete')

        self.eq((True, False, False), sng.orm.persistencestate)

        self.expect(db.RecordNotFoundError, lambda: artist(sng.id))
        self.expect(db.RecordNotFoundError, lambda: singer(sng.id))

        # Ensure that an invalid sng can be deleted
        sng = singer.getvalid()

        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.save()

        sng.lastname  = 'X' * 256 # Invalidate

        sng.delete()
        self.expect(db.RecordNotFoundError, lambda: artist(sng.id))
        self.expect(db.RecordNotFoundError, lambda: singer(sng.id))

    def it_deletes_from_subentitys_entities_collections(self):
        chrons = self.chronicles

        # Create singer with a presentation and save
        sng = singer.getvalid()
        pres = presentation.getvalid()
        sng.presentations += pres
        loc = location.getvalid()
        locs = sng.presentations.last.locations 
        locs += loc
        sng.save()

        # Reload
        sng = singer(sng.id)

        # Test presentations and its trash collection
        self.one(sng.presentations)
        self.zero(sng.presentations.orm.trash)
        
        self.one(sng.presentations.first.locations)
        self.zero(sng.presentations.first.locations.orm.trash)

        # Remove the presentation
        rmsng = sng.presentations.pop()

        # Test presentations and its trash collection
        self.zero(sng.presentations)
        self.one(sng.presentations.orm.trash)

        self.one(sng.presentations.orm.trash.first.locations)
        self.zero(sng.presentations.orm.trash.first.locations.orm.trash)

        chrons.clear()
        sng.save()
        self.two(chrons)
        self._chrons(rmsng, 'delete')
        self._chrons(rmsng.locations.first, 'delete')
        
        sng = singer(sng.id)
        self.zero(sng.presentations)
        self.zero(sng.presentations.orm.trash)

        self.expect(db.RecordNotFoundError, lambda: presentation(pres.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

    def it_deletes_from_subentitys_subentities_collections(self):
        chrons = self.chronicles

        # Create singer with a concert and save
        sng = singer.getvalid()
        conc = concert.getvalid()
        sng.concerts += conc
        loc = location.getvalid()
        sng.concerts.last.locations += loc
        sng.save()

        # Reload
        sng = singer(sng.id)

        # Test concerts and its trash collection
        self.one(sng.concerts)
        self.zero(sng.concerts.orm.trash)

        self.one(sng.concerts.first.locations)
        self.zero(sng.concerts.first.locations.orm.trash)

        # Remove the concert
        rmconc = sng.concerts.pop()

        # Test concerts and its trash collection
        self.zero(sng.concerts)
        self.one(sng.concerts.orm.trash)

        self.one(sng.concerts.orm.trash.first.locations)
        self.zero(sng.concerts.orm.trash.first.locations.orm.trash)

        chrons.clear()
        sng.save()
        self.three(chrons)
        self._chrons(rmconc, 'delete')
        self._chrons(rmconc.orm.super, 'delete')
        self._chrons(rmconc.locations.first, 'delete')
        
        sng = singer(sng.id)
        self.zero(sng.concerts)
        self.zero(sng.concerts.orm.trash)

        self.expect(db.RecordNotFoundError, lambda: concert(conc.id))
        self.expect(db.RecordNotFoundError, lambda: location(loc.id))

    def _create_join_test_data(self):
        ''' Create test data to be used by the outer/inner join tests. '''

        for c in (artist, presentation, location, artist_artifact, artifact):
            c.orm.truncate()

        # The artist entities and constituents will have sequential indexes to
        # query against.
        arts = artists()
        for i in range(4):
            art = artist.getvalid()
            art.firstname = 'fn-' + str(i)
            art.lastname = 'ln-'  + str(i + 1)
            arts += art

            for j in range(4):
                art.locations += location.getvalid()
                art.locations.last.address = 'art-loc-addr-' + str(j)
                art.locations.last.description = 'art-loc-desc-' + str(j + 1)
                
            for k in range(4):
                art.presentations += presentation.getvalid()
                pres = art.presentations.last
                pres.name = 'pres-name-' + str(k)
                pres.description = 'pres-desc-' + str(k + 1) + '-' + str(i)

                for l in range(4):
                    pres.locations += location.getvalid()
                    pres.locations.last.address = 'pres-loc-addr-' + str(l)
                    pres.locations.last.description ='pres-loc-desc-' +  str(l + 1)

            for k in range(4):
                aa = artist_artifact.getvalid()
                aa.role = 'art-art_fact-role-' + str(k)
                aa.planet = 'art-art_fact-planet-' + str(k + 1)
                fact = artifact.getvalid()

                aa.artifact = fact
                fact.title = 'art-art_fact-fact-title-' + str(k)
                fact.description = 'art-art_fact-fact-desc-' + str(k + 1)
                art.artist_artifacts += aa

                for l in range(4):
                    comp = component.getvalid()
                    comp.name = 'art-art_fact-role-fact-comp-name' + str(l)
                    fact.components += comp

        arts.save()

        return arts

    def it_calls_innerjoin_on_entities_with_BETWEEN_clauses(self):
        arts = artists()
        for i in range(8):
            art = artist.getvalid()
            art.weight = i

            aa = artist_artifact.getvalid()
            art.artist_artifacts += aa
            aa.artifact = artifact.getvalid()
            aa.artifact.weight = i + 10

            arts += art

        arts.save()

        for op in '', 'NOT':
            # Load an innerjoin where both tables have [NOT] IN where clause
            # 	SELECT *
            # 	FROM artists
            # 	INNER JOIN artist_artifacts AS `artists.artist_artifacts`
            # 		ON `artists`.id = `artists.artist_artifacts`.artistid
            # 	INNER JOIN artifacts AS `artists.artist_artifacts.artifacts`
            # 		ON `artists.artist_artifacts`.artifactid = `artists.artist_artifacts.artifacts`.id
            # 	WHERE (`artists`.firstname [NOT] IN (%s, %s))
            # 	AND (`artists.artist_artifacts.artifacts`.title[NOT]  IN (%s, %s))

            arts1 = artists('weight %s BETWEEN 0 AND 1' % op, ()).join(
                        artifacts('weight %s BETWEEN 10 AND 11' %op, ())
                    )

            if op == 'NOT':
                self.six(arts1)
            else:
                self.two(arts1)

            for art1 in arts1:
                if op == 'NOT':
                    self.gt(art1.weight, 1)
                else:
                    self.le(art1.weight, 1)

                self.one(art1.artifacts)

                fact1 = art1.artifacts.first
                
                if op == 'NOT':
                    self.gt(fact1.weight, 11)
                else:
                    self.le(fact1.weight, 11)

        artwhere = 'weight BETWEEN 0 AND 1 OR weight BETWEEN 3 AND 4'
        factwhere = 'weight BETWEEN 10 AND 11 OR weight BETWEEN 13 AND 14'
        arts1 = artists(artwhere, ()).join(
                    artifacts(factwhere, ())
                )

        self.four(arts1)

        for art1 in arts1:
            self.true(art1.weight in (0, 1, 3, 4))

            self.one(art1.artifacts)

            fact1 = art1.artifacts.first
            
            self.true(fact1.weight in (10, 11, 13, 14))

    def it_calls_innerjoin_on_entities_with_IN_clauses(self):
        for e in artists, artifacts:
            e.orm.truncate()
        arts = artists()
        for i in range(8):
            art = artist.getvalid()
            art.firstname = uuid4().hex

            aa = artist_artifact.getvalid()
            art.artist_artifacts += aa
            aa.artifact = artifact.getvalid()
            aa.artifact.title = uuid4().hex

            arts += art

        arts.save()

        for op in '', 'NOT':
            # Load an innerjoin where both tables have [NOT] IN where clause
            # 	SELECT *
            # 	FROM artists
            # 	INNER JOIN artist_artifacts AS `artists.artist_artifacts`
            # 		ON `artists`.id = `artists.artist_artifacts`.artistid
            # 	INNER JOIN artifacts AS `artists.artist_artifacts.artifacts`
            # 		ON `artists.artist_artifacts`.artifactid = `artists.artist_artifacts.artifacts`.id
            # 	WHERE (`artists`.firstname [NOT] IN (%s, %s))
            # 	AND (`artists.artist_artifacts.artifacts`.title[NOT]  IN (%s, %s))

            firstnames = ['\'%s\'' % x for x in arts.pluck('firstname')]
            artwhere = 'firstname %s IN (%s)' % (op, ', '.join(firstnames[:4]))

            titles = ['\'%s\'' % x.first.title for x in arts.pluck('artifacts')]
            factwhere = 'title %s IN (%s)' % (op, ', '.join(titles[:4]))

            arts1 = artists(artwhere, ()) & artifacts(factwhere, ())

            self.four(arts1)
            titles = [x[1:-1] for x in titles]

            for art1 in arts1:
                if op == 'NOT':
                    self.true(art1.firstname not in arts.pluck('firstname')[:4])
                else:
                    self.true(art1.firstname in arts.pluck('firstname')[:4])

                self.one(art1.artifacts)

                fact1 = art1.artifacts.first
                
                if op == 'NOT':
                    self.true(fact1.title not in titles[:4])
                else:
                    self.true(fact1.title in titles[:4])

        # Test using conjoined IN clauses in artists and artifacts.
        # artwhere
        artwhere1 = 'firstname IN (%s)' % (', '.join(firstnames[:2]))
        artwhere2 = 'firstname IN (%s)' % (', '.join(firstnames[2:4]))

        artwhere = '%s OR %s' % (artwhere1, artwhere2)

        # factwhere
        titles = ['\'%s\'' % x.first.title for x in arts.pluck('artifacts')]
        factwhere1 = 'title IN (%s)' % (', '.join(titles[:2]))
        factwhere2 = 'title IN (%s)' % (', '.join(titles[2:4]))

        factwhere = '%s OR %s' % (factwhere1, factwhere2)

        arts1 = artists(artwhere, ()).join(
            artifacts(factwhere, ())
        )

        self.four(arts1)

        titles = [x[1:-1] for x in titles]

        for art1 in arts1:
            self.true(art1.firstname in arts.pluck('firstname')[:4])
            self.one(art1.artifacts)
            fact1 = art1.artifacts.first
            self.true(fact1.title in titles[:4])

    def it_calls_innerjoin_on_entities_with_MATCH_clauses(self):
        artkeywords, factkeywords = [], []

        arts = artists()
        for i in range(2):
            art = artist.getvalid()
            artkeyword, factkeyword = uuid4().hex, uuid4().hex
            artkeywords.append(artkeyword)
            factkeywords.append(factkeyword)
            art.bio = 'one two three %s five six' % artkeyword
            aa = artist_artifact.getvalid()

            art.artist_artifacts += aa

            aa.artifact = artifact.getvalid()

            aa.artifact.title = 'one two three %s five six' % factkeyword

            arts += art

        arts.save()

        # Query where composite and constituent have one MATCH clase each
        arts1 = artists("match(bio) against ('%s')" % artkeywords[0], ()).join(
            artifacts(
                "match(title, description) against ('%s')" %  factkeywords[0], ()
            )
        )


        # Query where composite and constituent have two MATCH clase each
        artmatch = (
            "MATCH(bio) AGAINST ('%s') OR "
            "MATCH(bio) AGAINST ('%s')"
        )

        factmatch = (
            "MATCH(title, description) AGAINST ('%s') OR "
            "MATCH(title, description) AGAINST ('%s')"
        )

        artmatch  %= tuple(artkeywords)
        factmatch %= tuple(factkeywords)

        arts1 = artists(artmatch, ()) & artifacts(factmatch, ())

        self.two(arts1)

        arts.sort()
        arts1.sort()

        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)
            self.eq(art.artifacts.first.id, art1.artifacts.first.id)

    def it_calls_innerjoin_on_associations(self):
        arts = self._create_join_test_data()
        arts.sort()

        fff = False, False, False

        # Test artists joined with artist_artifacts with no condititons
        arts1 = artists()
        arts1 &= artist_artifacts()

        self.one(arts1.orm.joins)

        self.four(arts1)

        arts1.sort()
        
        self.chronicles.clear()

        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            self.four(art1.artist_artifacts)

            art.artist_artifacts.sort()
            art1.artist_artifacts.sort()

            for aa, aa1 in zip(art.artist_artifacts, art1.artist_artifacts):
                self.eq(aa.id, aa.id)

                self.eq(fff, aa1.orm.persistencestate)

                aa1.artifact

                self.eq(aa.artifact.id, aa1.artifact.id)
                
                self.is_(aa1.artifact, self.chronicles.last.entity)
                self.eq('retrieve', self.chronicles.last.op)

                self.eq(aa1.artist.id, art1.id)


        # NOTE The above will lazy-load aa1.artifact 16 times
        self.count(16, self.chronicles)

        # Test artists joined with artist_artifacts where the association has a
        # conditional
        arts1 = artists()
        arts1 &= artist_artifacts('role = %s', ('art-art_fact-role-0',))

        self.one(arts1.orm.joins)

        self.four(arts1)

        self.chronicles.clear()

        arts1.sort()
        for art, art1 in zip(arts, arts1):
            self.eq(art.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            self.one(art1.artist_artifacts)

            aa1 = art1.artist_artifacts.first
            self.eq(aa1.role, 'art-art_fact-role-0')
            self.eq(aa1.artifactid, aa1.artifact.id)

            self.eq(fff, aa1.orm.persistencestate)

            # The call to aa1.artifact wil lazy-load artifact which will add to
            # self.chronicles
            self.eq('retrieve', self.chronicles.last.op)

            self.is_(aa1.artifact, self.chronicles.last.entity)

            self.eq(fff, aa1.artifact.orm.persistencestate)

        # NOTE This wil lazy-load aa1.artifact 4 times
        self.four(self.chronicles)

        # Test unconditionally joining the associated entities collecties
        # (artist_artifacts) with its composite (artifacts)
        for b in False, True:
            if b:
                # Implicitly join artist_artifact
                arts1 = artists() & artifacts()
            else:
                # Explicitly join artist_artifact
                arts1 = artists() 
                arts1 &= artist_artifacts() & artifacts()

            self.one(arts1.orm.joins)
            self.type(artist_artifacts, arts1.orm.joins.first.entities)
            self.one(arts1.orm.joins.first.entities.orm.joins)
            facts = arts1.orm.joins.first.entities.orm.joins.first.entities
            self.type(artifacts, facts)

            arts1.sort()

            self.chronicles.clear()

            self.four(arts1)

            for art, art1 in zip(arts, arts1):
                self.eq(art.id, art1.id)

                self.eq(fff, art1.orm.persistencestate)

                self.four(art1.artist_artifacts)

                art.artist_artifacts.sort()
                art1.artist_artifacts.sort()

                for aa, aa1 in zip(art.artist_artifacts, art1.artist_artifacts):
                    self.eq(fff, aa1.orm.persistencestate)
                    self.eq(aa.id, aa.id)
                    self.eq(aa.artifact.id, aa1.artifact.id)

            self.zero(self.chronicles)


        # Test joining the associated entities collecties (artist_artifacts)
        # with its composite (artifacts) where the composite's join is
        # conditional.
        for b in True, False:
            if b:
                # Explicitly join artist_artifacts
                arts1 = artists() 
                arts1 &= artist_artifacts() & artifacts('description = %s', ('art-art_fact-fact-desc-1',))
            else:
                # Implicitly join artist_artifacts
                arts1 = artists() & artifacts('description = %s', ('art-art_fact-fact-desc-1',))

            self.one(arts1.orm.joins)
            self.type(artist_artifacts, arts1.orm.joins.first.entities)
            self.one(arts1.orm.joins.first.entities.orm.joins)
            facts = arts1.orm.joins.first.entities.orm.joins.first.entities
            self.type(artifacts, facts)

            arts1.sort()

            self.four(arts1)

            self.chronicles.clear()
            for art, art1 in zip(arts, arts1):
                self.eq(fff, art1.orm.persistencestate)
                self.eq(art.id, art1.id)

                aas = art1.artist_artifacts
                self.one(aas)
                self.eq('art-art_fact-fact-desc-1', aas.first.artifact.description)
                self.eq(fff, aas.first.orm.persistencestate)

            self.zero(self.chronicles)

        # Test joining the associated entities collecties (artist_artifacts)
        # with its composite (artifacts) where the composite's join is
        # conditional along with the other two.
        arts1 =  artists('firstname = %s', ('fn-1')) 
        arts1 &= artist_artifacts('role = %s', ('art-art_fact-role-0',)) & \
                 artifacts('description = %s', ('art-art_fact-fact-desc-1',))

        self.one(arts1)

        self.chronicles.clear()
        self.eq('fn-1', arts1.first.firstname)

        aas1 = arts1.first.artist_artifacts
        self.one(aas1)
        self.eq(fff, aas1.first.orm.persistencestate)
        self.eq('art-art_fact-role-0', aas1.first.role)
        self.eq('art-art_fact-fact-desc-1', aas1.first.artifact.description)

        self.zero(self.chronicles)

        # Test joining a constituent (component) of the composite (artifacts)
        # of the association (artist_artifacts) without conditions.
        for b in True, False:
            if b:
                # Explicitly join the associations (artist_artifacts())
                arts1 =  artists().join(
                            artist_artifacts().join(
                                artifacts() & components()
                            )
                         )
            else:
                # Implicitly join the associations (artist_artifacts())
                arts1 =  artists().join(
                            artifacts() & components()
                         )


            self.four(arts1)

            arts1.sort()

            self.chronicles.clear()

            for art, art1 in zip(arts, arts1):
                self.eq(fff, art1.orm.persistencestate)
                self.eq(art.id, art1.id)
                aas = art.artist_artifacts.sorted()
                aas1 = art1.artist_artifacts.sorted()
                self.four(aas1)

                for aa, aa1 in zip(aas, aas1):
                    self.eq(fff, aa1.orm.persistencestate)
                    self.eq(aa.id, aa1.id)
                    fact = aa.artifact
                    fact1 = aa1.artifact
                    self.eq(fff, fact1.orm.persistencestate)

                    self.eq(fact.id, fact1.id)

                    comps = fact.components.sorted()
                    comps1 = fact1.components.sorted()

                    self.four(comps1)

                    for comp, comp1 in zip(comps, comps1):
                        self.eq(fff, comp1.orm.persistencestate)
                        self.eq(comp.id, comp1.id)

            self.zero(self.chronicles)

        # Test joining a constituent (component) of the composite (artifacts)
        # of the association (artist_artifacts) with conditions.
        aarole = 'art-art_fact-role-1'
        facttitle = 'art-art_fact-fact-title-1'
        compname = 'art-art_fact-role-fact-comp-name1'
        arts1 =  artists() & (
                    artist_artifacts(role = aarole) & (
                        artifacts(title = facttitle) & components(name = compname)
                    )
                 )

        self.four(arts1)

        arts1.sort()

        self.chronicles.clear()

        for art, art1 in zip(arts, arts1):
            self.eq(fff, art1.orm.persistencestate)

            self.eq(art.id, art1.id)
            aas1 = art1.artist_artifacts
            self.one(aas1)

            self.eq(aarole, aas1.first.role)
            self.eq(fff, aas1.first.orm.persistencestate)

            self.eq(facttitle, aas1.first.artifact.title)
            self.eq(fff, aas1.first.artifact.orm.persistencestate)

            self.one(aas1.first.artifact.components)

            self.eq(compname, aas1.first.artifact.components.first.name)
            self.eq(fff, aas1.first.artifact.components.first.orm.persistencestate)

        self.zero(self.chronicles)

    def it_calls_outerjoin(self):
        # Outer join artists with presentations; no predicates
        arts1 = artists()
        press1 = presentations()

        # I don't currently see the point in OUTER LEFT JOINs in ORMs, so,
        # until a use case is presented, we will raise a NotImplementedError
        self.expect(NotImplementedError, lambda: arts1.outerjoin(press1))
        
    def it_ensures_that_the_match_columns_have_full_text_indexes(self):
        exprs = (
            "match (firstname) against ('keyword') and firstname = 1",
            "firstname = 1 and match (lastname) against ('keyword')",
        )

        for expr in exprs:
            self.expect(orm.invalidcolumn, lambda: artists(expr, ()))

        exprs = (
            "match (bio) against ('keyword') and firstname = 1",
            "firstname = 1 and match (bio) against ('keyword')",
        )

        for expr in exprs:
            self.expect(None, lambda: artists(expr, ()))

    def it_demand_that_the_column_exists(self):
        exprs = (
            "notacolumn = 'value'",
            "firstname = 'value' or notacolumn = 'value'",
            "notacolumn between 'value' and 'othervalue'",
            "match (notacolumn) against ('keyword') and firstname = 1",
            "firstname = 1 and match (notacolumn) against ('keyword')",
            "match (bio) against ('keyword') and notacolumn = 1",
            "notacolumn = 1 and match (bio) against ('keyword')",
        )

        for expr in exprs:
            self.expect(orm.invalidcolumn, lambda: artists(expr, ()))

    def it_parameterizes_predicate(self):
        ''' Ensure that the literals in predicates get replaced with
        placeholders and that the literals are moved to the correct 
        positions in the where.args list. '''

        # TODO With the addition of this feature, we can remove the requirement
        # that a empty tuple be given as the second argument here. It also
        # seems possible that we remove the args tuple altogether since it no
        # longer seems necessary. NOTE, on the other hand, we may want to keep
        # the argument parameter for binary queries, e.g.,:
        #
        #     artist('id = %s', (uuid.bytes,))
        #
        # Writing the above using string concatenation is difficult.
        #
        # HOWEVER: Given that the predicate parser (`predicate._parse()`) has
        # not been thoroughly review by security specialists, it is considered
        # unsafe to rely on it to correctly identify literals and columns in
        # WHERE predicates.  Because of this, until we have a proof that the
        # predicate parser is invincible to malicious attacts, we should
        # continue to insist that the user use the `args` tuple to pass in
        # varient values when querying entities collections so the underlying
        # MySQL library can safely deal with these arguments seperately.

        arts = artists("firstname = '1234'", ())
        self.eq("1234", arts.orm.where.args[0])
        self.eq("%s", arts.orm.where.predicate.operands[1])

        arts = artists("firstname = '1234' or lastname = '5678'", ())
        self.eq("1234", arts.orm.where.args[0])
        self.eq("5678", arts.orm.where.args[1])
        for i, pred in enumerate(arts.orm.where.predicate):
            self.eq("%s", pred.operands[1])
            self.lt(i, 2)

        expr = (
            "firstname between '1234' and '5678' or "
            "lastname  between '2345' and '6789'"
        )

        arts = artists(expr, ())
        self.eq("1234", arts.orm.where.args[0])
        self.eq("5678", arts.orm.where.args[1])
        self.eq("2345", arts.orm.where.args[2])
        self.eq("6789", arts.orm.where.args[3])
        for i, pred in enumerate(arts.orm.where.predicate):
            self.eq("%s", pred.operands[1])
            self.lt(i, 2)

    def _it_saves_association_FIXME(self):
        art = artist.getvalid()
        art.artist_artifacts += artist_artifact.getvalid()

        # FIXME This raises an exception. To work around it,
        # you have do this:
        #     art.artist_artifacts.last.artifact = artifact.getvalid()
        #
        # This test should be integrated into a more general
        # it_save_associations test
        art.artifacts += artifact.getvalid()

        art.save()

    def it_raises_exception_whene_non_existing_column_is_referenced(self):
        self.expect(orm.invalidcolumn, lambda: artists(notacolumn = 1234))

    def it_raises_exception_when_bytes_type_is_compared_to_nonbinary(self):
        # TODO This should raise an exception
        arts1 = artists('id = 123', ())
        return
        arts1 &= artifacts()

        arts1.load()

    def it_calls_innerjoin_on_entities_and_writes_new_records(self):
        arts = self._create_join_test_data()
        arts.sort()

        arts1 = artists() & (artifacts() & components())

        # Explicitly load artists->artifacts->components. Add an entry to
        # `arts1` and make sure that the new record persists.
        arts1.load()

        art1 = artist.getvalid()
        arts1 += art1
        aas1 = art1.artist_artifacts
        aas1 += artist_artifact.getvalid()
        aas1.last.artifact = artifact.getvalid()
        aas1.last.artifact.components += component.getvalid()
        arts1.save()

        art2 = None
        def instantiate():
            nonlocal art2
            art2 = artist(art1.id)

        self.expect(None, instantiate)

        self.eq(art1.id, art2.id)

        aas2 = art2.artist_artifacts
        facts2 = art2.artifacts
        self.one(aas2)
        self.one(facts2)

        self.eq(art1.artist_artifacts.last.id, aas2.last.id)
        self.eq(art1.artifacts.last.id, facts2.last.id)

        comps2 = facts2.first.components
        self.one(comps2)
        
        self.eq(art1.artifacts.last.components.last.id,
                comps2.last.id)

        # Reload using the explicit loading, join method and update the record
        # added above. Ensure that the new data presists.
        arts3 = artists() & (artifacts() & components())
        arts3.load()
        art3 = arts3[art2.id]
        newval = uuid4().hex

        art3.firstname = newval
        art3.artist_artifacts.first.role = newval
        art3.artifacts.first.title = newval
        art3.artifacts.first.components.first.name = newval

        arts3.save()

        art4 = artist(art3.id)

        self.eq(newval, art4.firstname)
        self.eq(newval, art4.artist_artifacts.first.role)
        self.eq(newval, art4.artifacts.first.title)
        self.eq(newval, art4.artifacts.first.components.first.name)

    # TODO Allow the .join, .innerjoin, et. al. to accept an entities class in
    # addition to of an entities object
    def it_calls_innerjoin_on_entities(self):
        fff = False, False, False

        def join(joiner, joinee, type):
            if type in ('innerjoin', 'join'):
                getattr(joiner, type)(joinee)
            elif type  == 'standard':
                joiner = joiner & joinee
            elif type  == 'inplace':
                joiner &= joinee

            # Incorrect implementation of & and &= can nullify `joiner`, even
            # though the actual join was successful, so ensure `joiner` is
            # notnone
            self.notnone(joiner)

        arts = self._create_join_test_data()

        jointypes = 'innerjoin', 'join', 'standard', 'inplace'

        # Inner join where only artist has a where clause
        for t in jointypes:
            arts1 = artists(firstname = 'fn-0')
            press = presentations()
            locs = locations()
            artlocs = locations()

            join(press, locs, t)
            join(arts1, press, t)
            join(arts1, artlocs, t)

            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            # Test
            self.one(arts1)

            self.chronicles.clear()

            art1 = arts1.first
            self.eq(arts.first.id, art1.id)

            self.eq(fff, art1.orm.persistencestate)

            press = arts.first.presentations.sorted()
            press1 = art1.presentations.sorted()

            self.four(press1)

            locs = arts.first.locations.sorted()
            locs1 = art1.locations.sorted() 
            self.four(locs1)

            for loc, loc1 in zip(locs, locs1):
                self.eq(fff, loc.orm.persistencestate)
                self.eq(loc.id, loc1.id)

            for pres, pres1 in zip(press, press1):
                self.eq(fff, pres.orm.persistencestate)
                self.eq(pres.id, pres1.id)

                locs = pres.locations.sorted()
                locs1 = pres1.locations.sorted() 
                self.four(pres1.locations)

                for loc, loc1 in zip(locs, locs1):
                    self.eq(fff, loc.orm.persistencestate)
                    self.eq(loc.id, loc1.id)

            self.zero(self.chronicles)

        # Inner join query: All four have where clauses with simple predicate,
        # i.e., (x=1)
        for t in jointypes:
            arts1    =  artists        (firstname    =  'fn-0')
            press    =  presentations  (name         =  'pres-name-0')
            locs     =  locations      (description  =  'pres-loc-desc-1')
            artlocs  =  locations      (address      =  'art-loc-addr-0')

            join(press,  locs,     t)
            join(arts1,  press,    t)
            join(arts1,  artlocs,  t)

            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            self.one(arts1)

            self.chronicles.clear()

            art1 = arts1.first
            self.eq(fff, art1.orm.persistencestate)
            self.eq('fn-0', art1.firstname)

            locs1 = art1.locations
            self.one(locs1)
            loc1 = locs1.first
            self.eq(fff, loc1.orm.persistencestate)
            self.eq('art-loc-addr-0', loc1.address)

            press1 = art1.presentations
            self.one(press1)
            pres = press1.first
            self.eq(fff, pres.orm.persistencestate)
            self.eq('pres-name-0', pres.name)

            locs1 = pres.locations
            self.one(locs1)
            loc = locs1.first
            self.eq(fff, loc.orm.persistencestate)
            self.eq('pres-loc-desc-1', loc.description)

            self.zero(self.chronicles)

        # Inner join query: Artist has a conjoined predicate
        # i.e, (x=1 and y=1)
        # firstname=firstname will match the last artist while lifeform=organic
        # will match the first artist.
        for t in jointypes:
            arts1    =  artists('firstname = %s or '
                                'lastname = %s' , ('fn-0', 'ln-2'))
            press    =  presentations()
            locs     =  locations()
            artlocs  =  locations()

            join(press,  locs,     t)
            join(arts1,  press,    t)
            join(arts1,  artlocs,  t)

            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)
            
            self.two(arts1)

            self.chronicles.clear()

            # Test that the correct graph was loaded
            for art1 in arts1:
                self.eq(fff, art1.orm.persistencestate)
                self.true(art1.firstname == 'fn-0' or
                          art1.lastname  == 'ln-2')

                arts.first.presentations.sort('name')
                press1 = art1.presentations.sorted('name')
                self.four(press1)

                for i, pres1 in press1.enumerate():
                    self.eq(fff, pres1.orm.persistencestate)
                    pres = arts.first.presentations[i]
                    self.eq(pres.name, pres1.name)

                    locs  = pres.locations.sorted('description')
                    locs1 = pres1.locations.sorted('description')
                    self.four(locs1)

                    for i, loc1 in locs1.enumerate():
                        self.eq(fff, loc1.orm.persistencestate)
                        self.eq(locs[i].address, loc1.address)
                        self.eq(locs[i].description, loc1.description)
            
            self.zero(self.chronicles)

        for t in jointypes:
            arts1 = artists('firstname = %s and lastname = %s', 
                            ('fn-0', 'ln-1'))
            press = presentations()
            locs  = locations('address = %s or description = %s', 
                             ('pres-loc-addr-0', 'pres-loc-desc-2'))

            artlocs  =  locations('address = %s or description = %s', 
                                 ('art-loc-addr-0', 'art-loc-desc-2'))

            join(arts1,  artlocs,  t)
            join(arts1,  press,    t)
            join(press,  locs,     t)

            # Test join counts
            self.two(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            # Only one artist will have been retrieved by the query
            self.one(arts1)

            self.chronicles.clear()

            self.eq(fff, arts1.first.orm.persistencestate)

            # Test artist's locations
            locs = arts1.first.locations
            self.two(locs)
            for loc in locs:
                self.eq(fff, loc.orm.persistencestate)
                self.true(loc.address     == 'art-loc-addr-0' or 
                          loc.description == 'art-loc-desc-2')

            # Test arts1.first.presentations' locations
            press = arts1.first.presentations

            # All four presentations were match by the location predicate
            self.four(press) 
            for pres in press:
                self.eq(fff, pres.orm.persistencestate)
                self.two(pres.locations)
                for loc in pres.locations:
                    self.eq(fff, loc.orm.persistencestate)
                    self.true(loc.address     == 'pres-loc-addr-0' or 
                              loc.description == 'pres-loc-desc-2')

            self.zero(self.chronicles)

        for t in jointypes:
            # Query where the only filter is down the graph three levels
            # artist->presentation->locations. The algorithm that generates the
            # where predicate has unusual recursion logic that is sensitive to
            # top-level joins not having `where` objects so we need to make
            # sure this doesn't get broken.
            arts1 = artists()
            press = presentations()
            locs  = locations('address = %s or description = %s', 
                             ('pres-loc-addr-0', 'pres-loc-desc-2'))

            join(arts1, press, t)
            join(press, locs, t)


            # Test join counts
            self.one(arts1.orm.joins)
            self.one(press.orm.joins)
            self.zero(locs.orm.joins)

            self.four(arts1)

            self.chronicles.clear()

            for art in arts1:
                self.eq(fff, art.orm.persistencestate)
                self.four(art.presentations)
                for pres in art.presentations:
                    self.eq(fff, pres.orm.persistencestate)
                    self.two(pres.locations)
                    for loc in pres.locations:
                        self.eq(fff, loc.orm.persistencestate)
                        self.true(loc.address     == 'pres-loc-addr-0' or
                                  loc.description == 'pres-loc-desc-2')

            self.zero(self.chronicles)
            
        # Test joining using the three our more & operators.
        # NOTE Sadely, parenthesis must be used to correct precedence. This
        # will likely lead to confusion if the & techinique is promoted. I'm
        # thinking &= should be recommended instead.
        arts1 = artists() & (presentations() & locations())

        self.four(arts1)

        self.chronicles.clear()

        for art in arts1:
            self.eq(fff, art.orm.persistencestate)
            self.four(art.presentations)
            for pres in art.presentations:
                self.eq(fff, pres.orm.persistencestate)
                self.four(pres.locations)

        self.zero(self.chronicles)
                    
    def it_eager_loads_constituents(self):
        arts = artists()
        for _ in range(4):
            arts += artist.getvalid()
            arts.last.artist_artifacts += artist_artifact.getvalid()
            arts.last.artist_artifacts.last.artifact = artifact.getvalid()
            arts.last.locations += location.getvalid()

            arts.last.presentations += presentation.getvalid()
            arts.last.presentations.last.locations  += location.getvalid()
            arts.last.presentations.last.components += component.getvalid()
        arts.save()

        # Eager-load one constituent
        arts1 = artists(orm.eager('presentations'))
        self.one(arts1.orm.joins)
        self.type(presentations, arts1.orm.joins.first.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

        # Eager-load two constituents
        arts1 = artists(orm.eager('presentations', 'locations'))
        self.two(arts1.orm.joins)
        self.type(presentations, arts1.orm.joins.first.entities)
        self.type(locations, arts1.orm.joins.second.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

            for loc in art.locations:
                loc1 = art1.locations(loc.id)
                self.notnone(loc1)

        # Eager-load two constituents
        arts1 = artists(orm.eager('presentations', 'locations'))
        self.two(arts1.orm.joins)
        self.type(presentations, arts1.orm.joins.first.entities)
        self.type(locations, arts1.orm.joins.second.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

            for loc in art.locations:
                loc1 = art1.locations(loc.id)
                self.notnone(loc1)
            
        # Eager-load two constituents
        arts1 = artists(orm.eager('presentations.locations', 'presentations.components'))
        self.one(arts1.orm.joins)
        self.two(arts1.orm.joins.first.entities.orm.joins)
        presjoins = arts1.orm.joins.first.entities.orm.joins
        self.type(locations, presjoins.first.entities)
        self.type(components, presjoins.second.entities)

        self.le(arts.count, arts1.count)

        for art in arts:
            art1 = arts1(art.id)
            self.notnone(art1)

            for pres in art.presentations:
                pres1 = art1.presentations(pres.id)
                self.notnone(pres1)

                for loc in pres.locations:
                    loc1 = pres1.locations(loc.id)
                    self.notnone(loc1)

                for comp in pres.components:
                    comp1 = pres1.components(comp.id)
                    self.notnone(comp1)

    def it_creates_iter_from_predicate(self):
        ''' Test the predicates __iter__() '''

        # Iterate over one predicate
        pred = orm.predicate('col = 1')
        pred1 = None
        for i, pred1 in enumerate(pred):
            self.eq(str(pred1), str(pred))

        self.notnone(pred1)
        self.eq(0, i)

        # Iterate over two predicates
        pred = orm.predicate('col = 1 and col1 = 2')

        pred1 = None
        for i, pred1 in enumerate(pred):
            if i == 0:
                self.eq('col = 1 AND col1 = 2', str(pred1))
            elif i == 1:
                self.eq(' AND col1 = 2', str(pred1))
            else:
                self.fail('Predicate count exceeds 2')

        # Iterate over match predicate and standard
        pred = orm.predicate("match(col) against ('keyword') and col = 1")

        pred1 = None
        for i, pred1 in enumerate(pred):
            if i == 0:
                self.eq("MATCH (col) AGAINST ('keyword' IN NATURAL LANGUAGE MODE) AND col = 1", str(pred1))
            elif i == 1:
                self.eq(' AND col = 1', str(pred1))
            else:
                self.fail('Predicate count exceeds 2')

        # Iterate over match predicate and standard or standard
        pred = orm.predicate("match(col) against ('keyword') and col = 1 or col1 = 2")

        pred1 = None
        for i, pred1 in enumerate(pred):
            if i == 0:
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) AND col = 1 OR col1 = 2"
                )
                self.eq(expr, str(pred1))
            elif i == 1:
                self.eq(' AND col = 1 OR col1 = 2', str(pred1))
            elif i == 2:
                self.eq(' OR col1 = 2', str(pred1))
            else:
                self.fail('Predicate count exceeds 2')
        
    def it_failes_parsing_malformed_predicates(self):
        p = orm.predicate("match ((col) against ('search str')")
        parens = '''
            (col = 1
            (col = 1) or (( col = 2)
            (col = 1) and ( col = 2 or (col = 3)
            (col = 1) and col = 2 or (col = 3))
            (col = 1 and col = 2 or (col = 3)
            (col = 1))
            ((col = 1)
            x = 1 and (x = 1 and x = 1
            match (col) against ('search str') and col = 1)
            (match (col) against ('search str') and col = 1
            match (col) against ('search str') and (col = 1
            match (col) against ('search str')) and col = 1
            match (col) against ('search str') and )col = 1
        '''

        syntax = '''
            match (col) against (unquoted)
        '''

        unexpected = '''
            col = 1 and
            col = 1 =
            = col = 1
            = 1
            1 =
            or col = 1
            match against ('search str')
            match (col) ('search str')
            match () against ('search str')
            match () ('search str')
            match (col) ('search str')
            match (col) against ()
            match (col) against ('search str') in UNnatural language mode
            match (col) against ('search str') mode language natural in
            match (col,) against ('search str') mode language natural in
            col = %S
            col in ()
            col in (1) or col in ()
            col in (
            col in (1) or col in (
        '''

        invalidop = '''
            col != 1
            col === 1
            col <<< 1
            () against ('search str')
        '''

        pairs = (
            (orm.predicate.ParentheticalImbalance,  parens),
            (orm.predicate.SyntaxError,             syntax),
            (orm.predicate.UnexpectedToken,         unexpected),
            (orm.predicate.InvalidOperator,         invalidop),
        )

        for ex, exprs in pairs:
            for expr in exprs.splitlines():
                expr = expr.strip()
                if not expr:
                    continue
 
                try:
                    pred = orm.predicate(expr)
                except Exception as ex1:
                    if type(ex1) is not ex:
                        msg = (
                            'Incorrect exception type; '
                            'expected: %s; actual: %s'
                        ) % (ex, type(ex1))

                        self.fail(msg)
                else:
                    self.fail('No exception parsing: ' + expr)

    def it_parses_where_predicate(self):
        def test(expr, pred, first, op, second, third=''):
            msg = expr
            self.eq(first,   pred.operands[0],  msg)
            self.eq(op,      pred.operator,     msg)
            if second:
                self.eq(second,  pred.operands[1],  msg)

            if third:
                self.eq(third,  pred.operands[2],  msg)
                
            self.eq(expr,    str(pred),         msg)

        # Simple col = literal
        for expr in 'col = 11', 'col=11':
            pred = orm.predicate(expr)
            test('col = 11', pred, 'col', '=', '11')

        # Joined simple col > literal (or|and) col < literal
        for op in 'and', 'or':
            for expr in 'col > 0 %s col < 11' % op, 'col>0 %s col<11' % op:
                pred = orm.predicate(expr)
                test('col > 0 %s col < 11' % op.upper(), pred, 'col', '>', '0')

        # Simple literal = column
        for expr in '11 = col', '11=col':
            pred = orm.predicate(expr)
            test('11 = col', pred, '11', '=', 'col')

        # Joined simple literal > col (or|and) literal < col
        for op in 'and', 'or':
            for expr in '0 > col %s 11 < col' % op, '0>col %s 11<col' % op:
                pred = orm.predicate(expr)
                test('0 > col %s 11 < col' % op.upper(), pred, '0', '>', 'col')
                test(' %s 11 < col' % op.upper(), pred.junction, '11', '<', 'col')

        # Simple c = l
        for expr in 'c = 1', 'c=1':
            pred = orm.predicate(expr)
            test('c = 1', pred, 'c', '=', '1')

        # Joined simple c > 1 (or|and) 1 < c
        for op in 'and', 'or':
            for expr in '0 > c %s 1 < c' % op, '0>c %s 1<c' % op:
                pred = orm.predicate(expr)
                test('0 > c %s 1 < c' % op.upper(), pred, '0', '>', 'c')
                test(' %s 1 < c' % op.upper(), pred.junction, '1', '<', 'c')

        # Simple l = c
        for expr in '1 = c', '1=c':
            pred = orm.predicate(expr)
            test('1 = c', pred, '1', '=', 'c')

        # Simple col = 'literal'
        for expr in "col = '11'", "col='11'":
            pred = orm.predicate(expr)
            test("col = '11'", pred, 'col', '=', "'11'")

        # Joined simple col > 'literal' (or|and) col = 'literal'
        for op in 'and', 'or':
            exprs = (
                "col = '11' %s col1 = '111'" % op, 
                "col='11' %s col1='111'" % op.upper()
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                test( "col = '11' %s col1 = '111'" % op.upper(), pred, 'col', '=', "'11'")
                test( " %s col1 = '111'" % op.upper(), pred.junction, 'col1', '=', "'111'")

        # Simple 'literal' = column
        for expr in "'11' = col", "'11'=col":
            pred = orm.predicate(expr)

            test("'11' = col", pred, "'11'", '=', 'col')

        # Simple col = "literal"
        for expr in 'col = "11"', 'col="11"':
            pred = orm.predicate(expr)
            test('col = "11"', pred, 'col', '=', '"11"')

        # Simple "literal" <= column ; Test multicharacter special ops)
        for expr in 'col <= 11', 'col<=11':
            pred = orm.predicate(expr)
            test('col <= 11', pred, 'col', '<=', '11')

        # Simple column = 'lit=eral' (literal has operator in it)
        for expr in  "col = '1 = 1'", "col='1 = 1'":
            test("col = '1 = 1'", orm.predicate(expr), 'col', '=', "'1 = 1'")

        # Simple 'lit=eral' = column (literal has operator in it)
        for expr in "'1 = 1' = col", "'1 = 1'=col":
            test("'1 = 1' = col", orm.predicate(expr), "'1 = 1'", '=', 'col')

        # column is literal
        for expr in 'col is null', 'col  IS  NULL':
            test('col IS NULL', orm.predicate(expr), 'col', 'IS', 'NULL')

        # literal is column
        for expr in 'null is col', 'NULL  IS  col':
            test('NULL IS col', orm.predicate(expr), 'NULL', 'IS', 'col')

        # column is not literal
        for expr in 'col is not null', 'col  IS  NOT   NULL':
            pred = orm.predicate(expr)
            test('col IS NOT NULL', pred, 'col', 'IS NOT', 'NULL')

        # literal is not column
        for expr in 'null is not col', 'NULL  IS   NOT col':
            pred = orm.predicate(expr)
            test('NULL IS NOT col', pred, 'NULL', 'IS NOT', 'col')

        # column like literal
        for expr in "col like '%lit%'", "col   LIKE '%lit%'":
            pred = orm.predicate(expr)
            test("col LIKE '%lit%'", pred, 'col', 'LIKE', "'%lit%'")

        # column not like literal
        for expr in "col not like '%lit%'", "col   NOT  LIKE '%lit%'":
            pred = orm.predicate(expr)
            test("col NOT LIKE '%lit%'", pred, 'col', 'NOT LIKE', "'%lit%'")

        # column is literal
        for expr in "col is true", "col   IS   TRUE":
            pred = orm.predicate(expr)
            test('col IS TRUE', pred, 'col', 'IS', "TRUE")

        # column is not literal
        for expr in "col is not true", "col   IS   NOT TRUE":
            pred = orm.predicate(expr)
            test('col IS NOT TRUE', pred, 'col', 'IS NOT', "TRUE")

        # column is literal
        for expr in "col is false", "col   IS   FALSE":
            pred = orm.predicate(expr)
            test('col IS FALSE', pred, 'col', 'IS', "FALSE")

        # column is not literal
        for expr in "col is not false", "col   IS   NOT FALSE":
            pred = orm.predicate(expr)
            test('col IS NOT FALSE', pred, 'col', 'IS NOT', "FALSE")

        # column between 1 and 10
        for expr in 'col between 1 and 10', 'col   BETWEEN  1  AND  10':
            pred = orm.predicate(expr)
            test('col BETWEEN 1 AND 10', pred, 'col', 'BETWEEN', '1', '10')

        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                'col between 1 and 10 %s col1 = 1'% op, 
                'col   BETWEEN  1  AND  10  %s  col1  =  1' % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                test(
                    'col BETWEEN 1 AND 10 %s col1 = 1' % OP, pred,
                    'col', 'BETWEEN', '1', '10' 
                )
                test(
                    ' %s col1 = 1' % OP, pred.junction, 
                    'col1', '=', '1'
                )

        # column not between 1 and 10
        for expr in 'col not between 1 and 10', 'col   NOT BETWEEN  1  AND  10':
            pred = orm.predicate(expr)
            test('col NOT BETWEEN 1 AND 10', pred, 'col', 'NOT BETWEEN', '1', '10')

        def testmatch(pred, cols, expr, mode='natural'):
            self.none(pred.operands)
            self.notnone(pred.match)
            self.eq(cols, pred.match.columns)
            B(expr != str(pred.match))
            self.eq(expr, str(pred.match))

            if pred.junctionop:
                self.eq(' %s %s' % (pred.junctionop, expr), str(pred))

            self.eq(mode, pred.match.mode)

        # match(col) against ('keyword')
        exprs =  "match(col) against ('keyword')",  "MATCH ( col )  AGAINST  ( 'keyword' )"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col) AGAINST ('keyword' "
                "IN NATURAL LANGUAGE MODE)"
            )
            testmatch(pred, ['col'], expr)

        # match (col) against ('''keyword has ''single-quoted'' strings''')
        expr =  "MATCH (col) AGAINST ('''keyword has ''single-quoted'' strings''')"
        pred = orm.predicate(expr)
        self.eq("''keyword has ''single-quoted'' strings''", pred.match.searchstring)
        expr =  (
            "MATCH (col) AGAINST ('''keyword has ''single-quoted'' strings''' "
            "IN NATURAL LANGUAGE MODE)"
        )
        testmatch(pred, ['col'], expr)

        # match (col) against ('"keyword has "double-quoted"' strings"')
        expr =  "MATCH (col) AGAINST ('\"keyword has \"double-quoted\" strings\"')"
        pred = orm.predicate(expr)
        self.eq("\"keyword has \"double-quoted\" strings\"", pred.match.searchstring)

        expr = (
            "MATCH (col) AGAINST ('\"keyword has \"double-quoted\" strings\"' "
            "IN NATURAL LANGUAGE MODE)"
        )

        testmatch(pred, ['col'], expr)

        # match(col) against ('keyword') and col = 1
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "match(col) against ('keyword') %s col = 1" % op, 
                "match(col)  against  ('keyword')  %s col=1" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) %s col = 1" % OP
                )

                testmatch(pred, ['col'], expr)

                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) %s col = 1" % OP
                )

                self.eq(expr, str(pred))

                test(
                    ' %s col = 1' % OP, pred.match.junction, 
                    'col', '=', '1'
                )

        # (match(col) against ('keyword')) and (col = 1)
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "(match(col) against ('keyword')) %s (col = 1)" % op, 
                "(match(col)  against  ('keyword'))  %s (col=1)" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)"
                )

                testmatch(pred, ['col'], expr)

                expr = (
                    "(MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)) %s (col = 1)" % OP
                )

                self.eq(expr, str(pred))

                test(
                    ' %s (col = 1)' % OP, pred.junction, 
                    'col', '=', '1'
                )

        # (match(col) against ('keyword') and col = 1) and (col1 = 2)
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "(match(col) against ('keyword') and col = 1) %s (col1 = 2)" % op, 
                "(match(col)  against  ( 'keyword' ) and col=1)  %s (col1=2)" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "(MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE) "
                    "AND col = 1) %s (col1 = 2)" % OP
                )

                self.eq(expr, str(pred))

        # col = 1 and match(col) against ('keyword')
        for op in 'and', 'or':
            OP = op.upper()
            exprs = (
                "col = 1 %s match(col) against ('keyword')" % op, 
                "col  =  1  %s  match(col)  against  ('keyword')" % OP
            )
            for expr in exprs:
                pred = orm.predicate(expr)
                expr = (
                    "col = 1 " + OP + " MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)"
                )
                test(expr, pred, 'col', '=', '1')
                expr = (
                    "MATCH (col) AGAINST ('keyword' "
                    "IN NATURAL LANGUAGE MODE)"
                )
                testmatch(pred.junction, ['col'], expr)

        # match(col1, col2) against ('keyword')
        exprs =  "match(col1, col2) against ('keyword')", \
                 "MATCH ( col1, col2 )  AGAINST  ( 'keyword' )"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col1, col2) AGAINST ('keyword' "
                "IN NATURAL LANGUAGE MODE)"
            )
            testmatch(pred, ['col1', 'col2'], expr)

        # match(col1, col2) against ('keyword') in natural language mode
        exprs =  "match(col1, col2) against ('keyword') in natural language mode", \
                 "MATCH ( col1, col2 )  AGAINST  ( 'keyword' )  IN  NATURAL     LANGUAGE    MODE"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col1, col2) AGAINST ('keyword' "
                "IN NATURAL LANGUAGE MODE)"
            )
            testmatch(pred, ['col1', 'col2'], expr)

        # match(col1, col2) against ('keyword') in boolean mode
        exprs =  "match(col1, col2) against ('keyword') in boolean mode", \
                 "MATCH ( col1, col2 )  AGAINST  ( 'keyword' )  IN      BOOLEAN    MODE"
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = (
                "MATCH (col1, col2) AGAINST ('keyword' "
                "IN BOOLEAN MODE)"
            )
            testmatch(pred, ['col1', 'col2'], expr, 'boolean')

        # (col = 1)
        for expr in '(col = 1)', '( col=1 )':
            pred = orm.predicate(expr)
            expr = '(col = 1)'
            test(expr, pred, 'col', '=', '1')

        # (col = 1) and (col1 = 2)
        for expr in '(col = 1) and (col1 = 2)', '(col=1)AND(col1=2)':
            pred = orm.predicate(expr)
            expr = '(col = 1) AND (col1 = 2)'
            test(expr, pred, 'col', '=', '1')

            expr = ' AND (col1 = 2)'
            test(expr, pred.junction, 'col1', '=', '2')

        # (col = 1 and col1 = 2)
        for expr in '(col = 1 and col1 = 2)', '(col=1 AND col1=2)':
            pred = orm.predicate(expr)
            expr = '(col = 1 AND col1 = 2)'
            test(expr, pred, 'col', '=', '1')

            expr = ' AND col1 = 2)'
            test(expr, pred.junction, 'col1', '=', '2')

        # (col = 1 and (col1 = 2 and col2 = 3))
        exprs = (
           '(col = 1 and (col1 = 2 and col2 = 3))',
           '(col  =  1  AND ( col1=2 AND col2 = 3 ) )',
        )
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = '(col = 1 AND (col1 = 2 AND col2 = 3))'
            test(expr, pred, 'col', '=', '1')

            expr = ' AND (col1 = 2 AND col2 = 3))'
            test(expr, pred.junction, 'col1', '=', '2')

        # ((col = 1 and col1 = 2) and col2 = 3)
        exprs = (
           '((col = 1 and col1 = 2) and col2 = 3)',
           '((col=1 AND col1=2) AND col2=3)',
        )
        for expr in exprs:
            pred = orm.predicate(expr)
            expr = '((col = 1 AND col1 = 2) AND col2 = 3)'
            test(expr, pred, 'col', '=', '1')

        # col = 'can''t won''t shan''t'
        expr = "col = 'can''t won''t shan''t'"
        pred = orm.predicate(expr)
        expr = "col = 'can''t won''t shan''t'"
        test(expr, pred, 'col', '=', "'can''t won''t shan''t'")

        for op in orm.predicate.Specialops:
            expr = 'col %s 123' % op
            pred = orm.predicate(expr)
            test(expr, pred, 'col', op, '123')

        # col_1 = 1 and col_2 = 2
        expr = "col_0 = 0 AND col_1 = 1"
        for i, pred in enumerate(orm.predicate(expr)):
            col = 'col_' + str(i)
            if i.first:
                expr = 'col_0 = 0 AND col_1 = 1' 
            elif i.second:
                expr = ' AND col_1 = 1'
            test(expr, pred, col, '=', str(i))
        
        ## Placeholders ##
        expr = 'col = %s'
        pred = orm.predicate(expr)
        test(expr, pred, 'col', '=', '%s')

        ## Parse introducers#
        expr = 'id = _binary %s'
        pred = orm.predicate(expr)
        self.eq('id = _binary %s', str(pred))

        # _binary id = %s
        expr = '_binary id = %s'
        pred = orm.predicate(expr)
        self.eq('_binary id = %s', str(pred))

        # _binary id = _binary %s
        expr = '_binary id = _binary %s'
        pred = orm.predicate(expr)
        self.eq('_binary id = _binary %s', str(pred))

        # col in (123) 
        exprs = (
            'col in (123)',
            'col IN(123)',
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq('col IN (123)', str(pred))

        # col in (123, 'test') 
        exprs = (
            "col in (123, 'test')",
            "col IN(123, 'test')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (123, 'test')", str(pred))

        # col in (123, '''test ''single-quoted'' strings''')
        exprs = (
            "col in (123, '''test ''single-quoted'' strings''')",
            "col IN(123,'''test ''single-quoted'' strings''')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (123, '''test ''single-quoted'' strings''')", str(pred))

        # col in (1 2 3 'test', 'test1')
        exprs = (
            "col in (1, 2, 3, 'test', 'test1')",
            "col IN(1, 2, 3, 'test', 'test1')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (1, 2, 3, 'test', 'test1')", str(pred))

        # col not in (1 2 3 'test', 'test1')
        exprs = (
            "col not in (1, 2, 3, 'test', 'test1')",
            "col NOT IN(1, 2, 3, 'test', 'test1')",
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col NOT IN (1, 2, 3, 'test', 'test1')", str(pred))

        exprs = (
            'col in (_binary %s)',
            'col IN(_binary %s)',
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (_binary %s)", str(pred))

        exprs = (
            'col in (_binary %s, _binary %s)',
            'col IN(_binary %s,_binary %s)',
        )

        for expr in exprs:
            pred = orm.predicate(expr)
            self.eq("col IN (_binary %s, _binary %s)", str(pred))

class test_blog(tester):
    def __init__(self):
        super().__init__()
        blogs().              RECREATE()
        tags().               RECREATE()
        tags_mm_articles().   RECREATE()
        articlerevisions().   RECREATE()
        blogpostrevisions().  RECREATE()
        users().              RECREATE()

    def it_calls_ALL(self):
        # TODO
        return

        blogs().RECREATE()
        slugdescs =  (('the-abolitionist-approach', 'The abolitionist approach'),
                      ('a-second-blog',             'The second blog'))

        for slug, desc in slugdescs:
            bl = blog()
            bl.slug = slug
            bl.description = desc
            bl.save()
        
        bs = blogs().ALL()

    def it_calls_import(self):
        onimportstatuschangecalled = False
        ps = persons()
        imparts = articles()
        errarts = []
        onimportstatuschange = False

        def local_onimportstatuschange(src, eargs):
            nonlocal onimportstatuschange
            onimportstatuschange = True

        def local_onrequestauthormap(src, eargs):
            nonlocal ps
            importpersons = eargs.importpersons
            creators      = eargs.creators
            ps += importpersons
            
            for p in importpersons:
                u = user.load(p.users.first.name, 'carapacian')
                if not u:
                    u = user()
                    u.name = p.users.first.name
                    u.service = 'carapacian'
                    u.password = uuid4().hex
                    u.save()
                    creators += u

        def local_onitemimport(src, eargs):
            nonlocal imparts
            imparts += eargs.item

        def local_onitemimporterror(src, eargs):
            errarts.append((eargs.item, eargs.exception))

        bl = blog()
        bl.onimportstatuschange += local_onimportstatuschange
        bl.onrequestauthormap += local_onrequestauthormap
        bl.onitemimport += local_onitemimport
        bl.onitemimporterror += local_onitemimporterror
        bl.slug = 'imported-blog'
        bl.description = 'This blog contains blogposts and articles imported from a WXR file'
        bl.save()

        bl.import_(io.StringIO(wxr))

        # Assert local_onimportstatuschange was called at least once
        self.assertTrue(onimportstatuschange)

        # Assert that local_onrequestauthormap was called with two persons in
        # eargs.importpersons
        ps.sort('email')
        self.assertTwo(ps)
        self.assertEq('dhogan@fakemail.com', ps.first.email)
        self.assertEq('jhogan@fakemail.com', ps.second.email)
	
        # Assert that 3 art were imported
        imparts.sort('title')
        self.assertThree(imparts)
        self.assertEq('Get Query Duration with dbext with MySQL',   imparts.first.title)
        self.assertEq('My Story', imparts.second.title)
        self.assertEq('Resume',   imparts.third.title)

        # Assert that one invalid article was captured in local_onitemimporterror
        self.assertOne(errarts)
        self.assertTwo(errarts[0])
        self.assertFalse(errarts[0][0].isvalid)

    def it_creates(self):
        bl = blog()
        bl.slug = 'carapacian-tech'
        bl.description = "The technical blog for Carapacian, LLC"
        self.assertTrue(bl._isnew)
        self.assertFalse(bl._isdirty)
        self.assertNone(bl.id)
        bl.save()
        self.assertTrue(type(bl.id) == uuid.UUID)
        self.assertFalse(bl._isnew)
        self.assertFalse(bl._isdirty)

        bl1 = blog(bl.id)

        self.assertFalse(bl1._isnew)
        self.assertFalse(bl1._isdirty)
        self.assertEq(bl.id, bl1.id)
        self.assertEq(bl.slug, bl1.slug)
        self.assertEq(bl.description, bl1.description)

    def it_sets_properties(self):
        slug = 'carapacian-tech'
        description = "The technical blog for Carapacian, LLC"
        bl = blog()
        bl.slug = slug
        bl.description = description
        self.assertEq(slug, bl.slug)
        self.assertEq(description, bl.description)

    def it_breaks_rules(self):
        slug = 'carapacian-tech'
        description = "The technical blog for Carapacian, LLC"
        bl = blog()
        self.assertCount(2, bl.brokenrules)
        self.assertTrue(bl.brokenrules.contains('slug', 'full'))
        self.assertTrue(bl.brokenrules.contains('description', 'full'))
        bl.slug = slug
        self.assertCount(1, bl.brokenrules)
        self.assertTrue(bl.brokenrules.contains('description', 'full'))
        bl.description = description
        self.assertCount(0, bl.brokenrules)

    def it_updates(self):
        slug = str(uuid4())
        description = "The technical blog for Carapacian, LLC"
        bl = blog()
        bl.slug = slug
        bl.description = description
        bl.save()

        bl = blog(bl.id)
        bl.description = 'new'
        bl.save()

        bl = blog(bl.id)
        self.assertEq('new', bl.description)
        self.assertEq(slug, bl.slug)

        slug = str(uuid4())
        bl.slug = slug
        bl.save()

        bl = blog(bl.id)
        self.assertEq('new', bl.description)
        self.assertEq(slug, bl.slug)

    def it_loads_as_valid(self):
        bl = blog()
        bl.slug = str(uuid4())
        bl.description = "The technical blog for Carapacian, LLC"
        bl.save()
        self.assertValid(blog(bl.id))

    def it_loads_by_id(self):
        bl = blog()
        bl.slug = uuid4().hex
        bl.description = "The technical blog for Carapacian, LLC"
        bl.save()

        bl1 = blog(bl.id)

        self.eq(bl1.slug, bl.slug)
        self.eq(bl1.description, bl.description)

    def it_loads_by_slug(self):
        bl = blog()
        bl.slug = uuid4().hex
        bl.description = "The technical blog for Carapacian, LLC"
        bl.save()

        bl1 = blog(bl.slug)

        self.eq(bl1.slug, bl.slug)
        self.eq(bl1.description, bl.description)

    def it_calls__str__(self):
        bl = blog()
        bl.slug = uuid4().hex
        bl.description = uuid4().hex
        bl.save()

        bl1 = blog(bl.id)

        expect = """Id:          {}
Slug:        {}
Description: {}
"""
        expect = expect.format(str(bl.id), bl.slug, bl.description)

        self.eq(expect, str(bl1))


    def it_violates_unique_constraint_on_slug(self):
        bl = blog()
        bl.slug = 'non-unique'
        bl.description = "The technical blog for Carapacian, LLC"
        bl.save()

        bl = blog()
        bl.slug = 'non-unique'
        bl.description = "The technical blog for Carapacian, LLC"
        try:
            bl.save()
        except MySQLdb.IntegrityError as ex:
            self.assertTrue(ex.args[0] == DUP_ENTRY)
        except Exception:
            self.assertFail('Wrong exception')
        else:
            self.assertFail("Didn't raise IntegrityError")

class test_blogpostrevision(tester):
    def __init__(self):
        super().__init__()
        articlerevisions().RECREATE()
        blogpostrevisions().RECREATE()
        blogs().RECREATE()

        # Create a blog
        bl = blog()
        bl.slug = 'carapacian-tech-blog'
        bl.description = 'Carapacian Tech Blog'
        bl.save()

        self.blog = bl

    def it_creates(self):
        bl = self.blog

        # Create blogpostrevision
        body = test_blogpost.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        rev = blogpostrevision()
        rev.title = title
        rev.body = body
        rev.blog = bl
        rev.slug = slug
        rev.excerpt = test_article.Smallpostexcerpt
        rev.status = article.Pending
        rev.iscommentable = False
        rev.slugcache = slug
        rev.save()

        # Reload blogpostrevision and test
        rev1 = blogpostrevision(rev.id)
        self.assertEq(rev.title, rev1.title)
        self.assertEq(rev.slug, rev1.slug)
        self.assertEq(rev.body, rev1.body)
        self.assertEq(rev.excerpt, rev1.excerpt)
        self.assertEq(rev.status, rev1.status)
        self.assertEq(rev.iscommentable, rev1.iscommentable)
        self.assertEq(rev.slugcache, rev1.slugcache)
        self.assertEq(bl.id, rev1.blog.id)

    def it_instantiates(self):
        rev = blogpostrevision()
        self.assertNone(rev.id)
        self.assertNone(rev.author)
        self.assertNone(rev.createdat)
        self.assertNone(rev.title)
        self.assertNone(rev.body)
        self.assertNone(rev.excerpt)
        self.assertEq(article.Draft, rev.status)
        self.assertFalse(rev.iscommentable)
        self.assertNone(rev.slug)
        self.assertNone(rev.blog)

    def it_fails_on_save_when_invalid(self):
        rev = blogpostrevision()
        try:
            rev.save()
        except BrokenRulesError as ex:
            self.assertIs(rev, ex.object)
        except Exception as ex:
            msg = ('BrokenRulesError expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_fails_to_load_given_nonexistent_id(self):
        try:
            rev = blogpostrevision(uuid4())
        except Exception as ex:
            self.assertTrue(True)
        else:
            self.assertFail('Exception was not thrown')

    def it_loads_as_valid(self):
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.blog = self.blog
        rev.save()

        rev = blogpostrevision(rev.id)
        self.assertValid(rev)

    def it_breaks_diff_rules(self):
        # Diff must be empty for root revisions
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle
        rev.diff = diff.diff('herp', 'derp')
        rev.blog = self.blog
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'empty'))

        # Fix
        rev.diff = None
        self.assertValid(rev)

        # Break the rule that says a diff must be of type diff.diff
        rent = blogpostrevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_article.Smallposttitle
        rev.blog = self.blog
        rent.diff = diff.diff('herp', 'derp')

        rev._parent = rent
        rev.body = None
        rev.diff = 'wrong type'
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

    def it_breaks_title_rules(self):
        # Root revisions must have non null titles
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.blog = self.blog
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Non-root revisions can have null titles
        rev._parent = blogpostrevision()
        self.assertCount(0, rev.brokenrules)

        # Root revisions can have empty strings as titles
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.blog = self.blog
        rev.title = ''
        self.assertCount(0, rev.brokenrules)

        # Revisions titles must be strings
        rev.title = 123
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))
        rev._parent = blogpostrevision() # Make non-root
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))

        # Title must be less than 500 characters
        rev = blogpostrevision()
        rev.blog = self.blog
        rev.body = test_blogpost.Smallpostbody
        rev.title = 'X' * 500
        self.assertCount(0, rev.brokenrules)
        rev.title = 'X' * 501
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'fits'))

    def it_breaks_status_rules(self):
        rev = blogpostrevision()
        rev.blog = self.blog
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle
        for st in article.Statuses:
            rev.status = st
            self.assertCount(0, rev.brokenrules)

        for st in ('wrong-type', 9999, object()):
            rev.status = st
            self.assertCount(1, rev.brokenrules)
            self.assertTrue(rev.brokenrules.contains('status', 'valid'))

    def it_breaks_body_rules_of_child(self):
        rent = blogpostrevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_article.Smallposttitle + str(uuid4())
        rent.blog = self.blog
        self.assertValid(rent)

        rev = blogpostrevision()
        rev._parent = rent
        rev.body = None
        rev.diff = diff.diff(rent.body, rent.body + '\n<b>This is strong</strong>')
        self.assertTrue(rev.brokenrules.contains('derivedbody', 'valid'))

    def it_breaks_body_rules(self):
        # Body must be full for root revisions
        rev = blogpostrevision()
        rev.blog = self.blog
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('body', 'full'))
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Invalid HTML in body
        rev.title = test_article.Smallposttitle
        rev.body = '<em>This is special</i>'
        self.assertOne(rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('body', 'valid'))
        self.assertEq(rev.brokenrules.first.message, "Can't close <em> with </i> at 1,19")

        # Ensure valid html with nested tags don't break rules
        rev.body = '<p>This is a <a href="link">link</a> and this is an <abbr>abbreviation</abbr>.</p>'
        self.assertZero(rev.brokenrules)

        # Ensure invalidly nested tags are invalid
        rev.body = """<p>
This is a 
<a href="link">
    link
    <p>
</a>
and this is an 
<abbr>
    </p>
    abbreviation
</abbr>.
</p>"""
        self.assertOne(rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('body', 'valid'))
        self.assertEq(rev.brokenrules.first.message, "Can't close <p> with </a> at 6,0")

        # Create a parent then test the child
        rent = blogpostrevision()
        rent.body = test_blogpost.Smallpostbody
        rent.title = test_article.Smallposttitle
        rent.diff = diff.diff('herp', 'derp')

        # A body and a diff shouldn't exist in the same record
        rev._parent = rent
        rev.diff = diff.diff('herp', 'derp')
        rev.body = test_blogpost.Smallpostbody
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

        # A non-root revision should can have a body but no diff. This
        # may be useful for caching or other isssues such as a failure to
        # create a diff.
        rev.body = test_blogpost.Smallpostbody
        rev.diff = None
        self.assertValid(rev)
    
    def it_breaks_blog_rules(self):
        # Body must be full for root revisions
        rev = blogpostrevision()
        rev.body = test_blogpost.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.blog
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('blog', 'full'))
        
    def it_retrieves(self):
        rev = blogpostrevision()
        rev.blog = self.blog
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.save()
        rev = blogpostrevision(rev.id)
        self.assertEq(rev.id, rev.id)

class test_blogpost(tester):
    Smallpostbody = """
    <p>
        But men labor under a mistake. The better part of the man is soon plowed
        into the soil for compost. By a seeming fate, commonly called necessity,
        they are employed, as it says in an old book, laying up treasures which
        moth and rust will corrupt and thieves break through and steal. It is a
        fool's life, as they will find when they get to the end of it, if not
        before. It is said that Deucalion and Pyrrha created men by throwing
        stones over their heads behind them:-
        &nbsp;
    </p>
    <pre xml:space="preserve">           
        Inde genus durum sumus, experiensque laborum,
        Et documenta damus qua simus origine nati.
    </pre>
    <p class="nind">
        Or, as Raleigh rhymes it in his sonorous way,-
    </p>
    <pre xml:space="preserve">  
        "From thence our kind hard-hearted is, enduring pain and care,
        Approving that our bodies of a stony nature are."
    </pre>
    <p class="nind">
        So much for a blind obedience to a blundering oracle, throwing the stones
        over their heads behind them, and not seeing where they fell.
    </p>
    """
    def __init__(self):
        super().__init__()
        articlerevisions().RECREATE()
        blogpostrevisions().RECREATE()
        blogs().RECREATE()
        users().RECREATE()
        tags()              .RECREATE()
        tags_mm_articles()  .RECREATE()

        # Create some tags
        for name in 'ethics', 'environment', 'health':
            t = tag()
            t.name = name
            t.save()

        # Create a blog
        bl = blog()
        bl.slug = 'carapacian-tech-blog'
        bl.description = 'Carapacian Tech Blog'
        bl.save()

        self.blog = bl
    
    def it_calls_search(self):
        # Create an article. We will want to ensure that it doesn't get
        # returned as part of the search; only blogposts should be returned
        art = article()
        art.title = uuid4().hex
        art.body = uuid4().hex
        art.save()

        # Init some vars
        strs = []
        cnt = 3
        commonbody = uuid4().hex
        commontitle = uuid4().hex

        # Create {cnt} blogposts
        for i in range(cnt):
            body = uuid4().hex
            title = uuid4().hex
            strs.append( (body, title) )
            bp = blogpost()
            bp.blog = self.blog
            bp.body = '<p>{} {}</p>'.format(body, commonbody)
            bp.title = '{}-{}'.format(title, commontitle)
            bp.save()

        # Search for strings in the body and post of each of the blogposts from
        # above. Since these strings are unique, ensure that exactly one
        # blogpost is in the returned collection.
        for tup in strs:
            body, title = tup
            bps = blogposts.search(title)
            self.assertOne(bps)
            self.assertType(blogposts, bps)
            for bp in bps:
                self.assertType(blogpost, bp)

            bps = blogposts.search(body)
            self.assertOne(bps)
            self.assertType(blogposts, bps)
            for bp in bps:
                self.assertType(blogpost, bp)

        # commonbody and commonbody are in all blogposts saved above. Ensure
        # that searching for them returns all of these blogposts.
        for str in commonbody, commontitle:
            bps = blogposts.search(commonbody)
            self.assertCount(cnt, bps)
            self.assertType(blogposts, bps)
            for bp in bps:
                self.assertType(blogpost, bp)
        
        # Search for the articles saved above. The search should only return
        # blogposts, so ensure that the collection contains zero entities.
        bps = blogposts.search(art.title)
        bps += blogposts.search(art.body)

        self.assertZero(bps)

    def it_loads_as_valid(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title  = title
        slug = re.sub(r'\W+', '-', bp.title).strip('-').lower()
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = article.Pending
        bp.iscommentable = True
        bp.blog = self.blog
        bp.save()

    def it_saves_x_revisions_with_null_properties(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title  = title
        slug = re.sub(r'\W+', '-', bp.title).strip('-').lower()
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True
        bp.blog = self.blog

        bp.save()

        x = 4
        for i in range(x):
            if i < x / 2:
                bp.title = None
                bp.excerpt = None
                bp.slug = None
            else:
                bp.body = test_article.Smallpostbody  + ' Rev: ' + str(i)
                revisedtitle = title + ' Rev: ' + str(i)
                bp.title = revisedtitle
                bp.excerpt = test_article.Smallpostexcerpt  + ' Rev: ' + str(i)
                
            bp.save()

            bp = blogpost(bp.id)

            if i < x / 2:
                self.assertEq(test_article.Smallpostbody, bp.body)
                self.assertEq(title, bp.title)
                self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
            else:
                self.assertEq(test_article.Smallpostbody + ' Rev: ' + str(i), bp.body)
                self.assertEq(revisedtitle, bp.title)
                self.assertEq(test_article.Smallpostexcerpt + ' Rev: ' + str(i), bp.excerpt)
            self.assertEq(blogpost.Pending, bp.status)
            self.assertTrue(bp.iscommentable)
            self.assertEq(slug, bp.slug)

    def it_calls_blog(self):
        bp = blogpost()
        self.assertTrue(bp.brokenrules.contains('blog', 'full'))

        self.assertNone(bp.blog)
        bp.blog = self.blog
        self.assertIs(self.blog, bp.blog)

        bp.save()

        bp = blogpost(bp.id)
        bp.blog
        self.assertEq(self.blog.id, bp.blog.id)

    def it_breaks_slugcache_uniqueness_rule(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.slug = 'my-slug'
        bp.save()

        bp = blogpost()
        bp.blog = self.blog
        bp.slug = 'my-slug'
        self.assertTrue(bp.brokenrules.contains('slugcache', 'unique'))

        # Create a new blog
        bl = blog()
        bl.slug = 'some-other-tech-blog'
        bl.description = 'Some other blog'
        bl.save()

        bp.blog = bl
        self.assertZero(bp.brokenrules);

    def it_calls_revisions(self):
        # TODO Copy this to test_article
        bp = blogpost()
        bp.blog = self.blog

        self.assertCount(0, bp.revisions)

        # First save
        bp.save()
        self.assertCount(1, bp.revisions)
        self.assertType(blogpostrevisions, bp.revisions)
        for rev in bp.revisions:
            self.assertType(blogpostrevision, rev)

        self.assertEq(bp.blog.id, bp.revisions.first.blog.id)

        # ... then load
        
        bp1 = blogpost(bp.id)
        self.assertCount(1, bp1.revisions)
        self.assertEq(bp1.blog.id, bp1.revisions.first.blog.id)
        self.assertType(blogpostrevisions, bp1.revisions)
        for rev in bp1.revisions:
            self.assertType(blogpostrevision, rev)

        # Second save
        bp.save()
        self.assertCount(2, bp.revisions)
        self.assertEq(bp.blog.id, bp.revisions.first.blog.id)
        self.assertType(blogpostrevisions, bp1.revisions)
        for rev in bp1.revisions:
            self.assertType(blogpostrevision, rev)

        # ... then load
        
        # TODO: The second save should insert a revision record with a blog
        # value of None
        return
        self.assertEq(None, bp.revisions.second.blog)
        bp1 = blogpost(bp.id)
        self.assertCount(2, bp1.revisions)
        self.assertEq(bp1.blog.id, bp1.revisions.first.blog.id)
        self.assertEq(None, bp1.revisions.second.blog)

    def it_calls_body(self): 
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.body)
        bp.save()
        self.assertEmpty(bp.body)

        bp.body = test_article.Smallpostbody
        self.assertEq(test_article.Smallpostbody, bp.body)

        bp.save()
        self.assertEq(test_article.Smallpostbody, bp.body)

        bp = blogpost(bp.id)
        self.assertEq(test_article.Smallpostbody, bp.body)

    def it_breaks_body_rules(self):
        # Previously, saving an invalid blogpost would result in the body
        # property being set to None. This tests ensure that bug does't creap
        # back in.
        bp = blogpost()
        bp.blog = self.blog
        bp.body = '<p>first</p>'
        bp.save()
        bp.body = "<em>I'm special</i>"
        try:
            bp.save()
        except:
            pass

        self.assertOne(bp.brokenrules)
        self.assertBroken(bp, 'derivedbody', 'valid')

    def it_calls_createdat(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.createdat)
        before = datetime.now().replace(microsecond=0)

        bp.blog = self.blog
        bp.save()

        after = datetime.now().replace(microsecond=0)

        self.assertLe(before, bp.createdat)
        self.assertGe(after, bp.createdat)

        createdat = bp.createdat

        bp = blogpost(bp.id)
        self.assertEq(createdat, bp.createdat)

    def it_calls_title(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.title)

        bp.save()

        self.assertEmpty(bp.title)

        bp.title = test_article.Smallposttitle
        self.assertEq(test_article.Smallposttitle, bp.title)

        bp.save()
        self.assertEq(test_article.Smallposttitle, bp.title)

        bp = blogpost(bp.id)
        self.assertEq(test_article.Smallposttitle, bp.title)

    def it_calls_slug(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.slug)

        bp.save()

        self.assertEmpty(bp.slug)

        slug = str(uuid4())
        bp.slug = slug
        self.assertEq(slug, bp.slug)

        bp.save()
        self.assertEq(slug, bp.slug)

        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)

    def it_calls_title_and_slug(self):
        bp = blogpost()
        bp.blog = self.blog
        title = 'Herp derp'
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        bp.title = title

        self.assertEq(slug, bp.slug)

        bp.save()
        self.assertEq(slug, bp.slug)

        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)

    def it_calls_excerpt(self):
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.excerpt)
        bp.save()
        self.assertEmpty(bp.excerpt)

        bp = blogpost(bp.id)
        self.assertEmpty(bp.excerpt)

        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.excerpt)
        bp.save()
        self.assertEmpty(bp.excerpt)
        bp = blogpost(bp.id)
        self.assertEmpty(bp.excerpt)

        bp = blogpost()
        bp.blog = self.blog
        bp.excerpt = test_article.Smallpostexcerpt
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
        bp.save()
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
        bp = blogpost(bp.id)
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)

    def it_calls_status(self): 
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.status)
        bp.save()
        self.assertEq(blogpost.Draft, bp.status)
        bp = blogpost(bp.id)
        self.assertEq(blogpost.Draft, bp.status)

        bp = blogpost()
        bp.blog = self.blog
        bp.status = blogpost.Pending
        self.assertEq(blogpost.Pending, bp.status)
        bp.save()
        self.assertEq(blogpost.Pending, bp.status)
        bp = blogpost(bp.id)
        self.assertEq(blogpost.Pending, bp.status)

        for i in range(7):
            bp.status = i
            self.true(bp.isvalid)

        for i in range(7, 20):
            bp.status = i
            self.false(bp.isvalid)
            self.broken(bp, 'status', 'valid')

    def it_calls_iscommentable(self): 
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.iscommentable)
        bp.save()
        self.assertFalse(bp.iscommentable)
        bp = blogpost(bp.id)
        self.assertFalse(bp.iscommentable)

        bp = blogpost()
        bp.blog = self.blog
        bp.iscommentable = True
        self.assertTrue(bp.iscommentable)
        bp.save()
        self.assertTrue(bp.iscommentable)
        bp = blogpost(bp.id)
        self.assertTrue(bp.iscommentable)

        bp = blogpost()
        bp.blog = self.blog
        bp.iscommentable = False
        self.assertFalse(bp.iscommentable)
        bp.save()
        self.assertFalse(bp.iscommentable)
        bp = blogpost(bp.id)
        self.assertFalse(bp.iscommentable)

    def it_calls_author(self):
        u = user()
        u.name      =  'mcyrus'
        u.service   =  'carapacian'
        u.password  =  'secret'

        u1 = user()
        u1.name      =  'lhemsworth'
        u1.service   =  'carapacian'
        u1.password  =  'secret'

        # Create blogpost, test its author is None, save and re-test
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.author)
        bp.save()
        self.assertNone(bp.author)
        bp = blogpost(bp.id)
        self.assertNone(bp.author)

        # Associate author, test, reload and test
        bp.author = u
        self.assertEq(u.name, bp.author.name)
        bp.save()
        self.assertEq(u.name, bp.author.name)
        bp = blogpost(bp.id)
        self.assertEq(u.name, bp.author.name)

        # Change author, test, reload and test
        bp.author = u1
        self.assertEq(u1.name, bp.author.name)
        bp.save()
        self.assertEq(u1.name, bp.author.name)
        bp = blogpost(bp.id)
        self.assertEq(u1.name, bp.author.name)
        
        # Ensure each revision of the blogpost has the correct author
        self.assertNone(bp.revisions.first.author)
        self.assertEq(u.name,    bp.revisions.second.author.name)
        self.assertEq(u1.name,   bp.revisions.third.author.name)

    def it_loads_by_id(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.save()
        id = bp.id

        bp = blogpost(id)
        self.assertEq(id,   bp.id)

    def it_loads_by_slug(self):
        bp = blogpost()
        bp.blog = self.blog
        slug = str(uuid4())
        bp.slug = slug
        bp.save()
        id = bp.id

        bp = blogpost(slug, self.blog)
        self.assertEq(slug, bp.slug)
        self.assertEq(id,   bp.id)

        try:
            blogpost(uuid4().hex)
        except Exception as ex:
            self.type(TypeError, ex)
        else:
            self.fail('Exception not thrown')

        try:
            blogpost(uuid4().hex, self.blog)
        except Exception as ex:
            self.type(db.RecordNotFoundError, ex)
        else:
            self.fail('Exception not thrown')

        bl = blog()
        bl.slug = uuid4().hex
        bl.description = 'This is not the correct blog'
        bl.save()
        try:
            blogpost(slug, bl)
        except Exception as ex:
            self.type(db.RecordNotFoundError, ex)
        else:
            self.fail('Exception not thrown')

    def it_calls_slug_and_title(self):
        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        bp = blogpost()
        bp.blog = self.blog
        bp.title = title
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)
        bp.save()
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)
        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)
        bp = blogpost(bp.id)
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)

        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        bp = blogpost()
        bp.blog = self.blog
        self.assertNone(bp.slug)
        self.assertEq(None, bp.title) 
        bp.title = title
        self.assertEq(slug, bp.slug)
        self.assertEq(title, bp.title)

        bp.save()
        self.assertEq(title, bp.title)
        self.assertEq(slug, bp.slug)
        bp = blogpost(bp.id)
        self.assertEq(title, bp.title)
        self.assertEq(slug, bp.slug)

        bp = blogpost()
        bp.blog = self.blog
        self.assertEq(None, bp.title)
        bp.save()
        self.assertEq('', bp.title)
        self.assertEmpty(bp.slug)
        bp = blogpost(bp.id)
        self.assertEmpty(bp.slug)
        self.assertEq('', bp.title)

        bp = blogpost()
        bp.blog = self.blog
        bp.slug = 'Herp Derp'
        self.assertEq('Herp Derp', bp.slug)
        self.assertEq(None, bp.title)
        bp.title = title
        self.assertEq('Herp Derp', bp.slug)
        bp.save()
        self.assertEq(title, bp.title)
        self.assertEq('Herp Derp', bp.slug)
        bp = blogpost(bp.id)
        self.assertEq(title, bp.title)
        self.assertEq('Herp Derp', bp.slug)

    def it_saves_x_revisions_with_empty_properties(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title = title
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True

        bp.save()

        for i in range(2):
            bp.title = ''
            bp.excerpt = ''
            bp.slug = ''
            bp.save()

            bp = blogpost(bp.id)
            bp.blog = self.blog
            self.assertEmpty(bp.title)
            self.assertEmpty(bp.excerpt)
            self.assertEq(blogpost.Pending, bp.status)
            self.assertTrue(bp.iscommentable)
            self.assertEmpty(bp.slug)
            
    def it_has_valid_revisions(self):
        # TODO Ensure that each of the revisions is the revision property are
        # the correct type, etc. Ensure this is true when a blogpost is reloaded.
        # Copy this to test_article as well.
        pass

    def it_saves_x_revisions(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        bp.title = title
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True

        bp.save()

        createdat = bp.createdat
        
        self.assertNotNone(bp.id)
        self.assertEq(test_article.Smallpostbody, bp.body)
        self.assertEq(title, bp.title)
        self.assertEq(test_article.Smallpostexcerpt, bp.excerpt)
        self.assertEq(blogpost.Pending, bp.status)
        self.assertEq(True, bp.iscommentable)
        slug = re.sub(r'\W+', '-', bp.title).strip('-').lower()
        self.assertEq(slug, bp.slug)

        x = 20

        for i in range(x):
            id = bp.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = bp.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(bp.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                bp.slug = 'walden-or-life-in-the-woods-hard-set'
                newbody = 'X' + bp.body
                
            bp.body = newbody

            bp.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            bp.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            bp.status = blogpost.Publish
            bp.iscommentable = i % 2 == 0
            
            bp.save()

            self.assertNotNone(bp.id)
            self.assertEq(id, bp.id)
            self.assertEq(newbody, bp.body)
            self.assertEq(createdat, bp.createdat)
            self.assertEq(newtitle, bp.title)
            self.assertEq(newexcerpt, bp.excerpt)
            self.assertEq(blogpost.Publish, bp.status)
            self.assertEq(i % 2 == 0, bp.iscommentable)
            if i > 10:
                self.assertEq('walden-or-life-in-the-woods-hard-set', bp.slug)
            else:
                self.assertEq(slug, bp.slug)

    def _createblogpost(self):
        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        bp.title = test_article.Smallposttitle 
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Pending
        bp.iscommentable = True

        bp.save()

        x = 20

        for i in range(x):
            id = bp.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = bp.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(bp.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                newbody = 'X' + bp.body
                
            bp.body = newbody

            bp.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            bp.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            bp.status = blogpost.Publish
            bp.iscommentable = i % 2 == 0
            
            bp.save()
        return bp

    def it_retrives_blogpost(self):
        bp1 = self._createblogpost()
        bp2 = blogpost(bp1.id)

        self.assertTrue(type(bp2.id) == uuid.UUID)
        self.assertEq(bp1.id,                bp2.id)

        self.assertEq(type(bp2.createdat),  datetime)
        self.assertEq(bp1.createdat,        bp2.createdat)

        self.assertEq(bp1.body,              bp2.body)
        self.assertEq(bp1.title,             bp2.title)
        self.assertEq(bp1.excerpt,           bp2.excerpt)
        self.assertEq(bp1.status,            bp2.status)
        self.assertEq(bp1.iscommentable,     bp2.iscommentable)
    
    def it_calls__str__(self):
        p = person()
        p.firstname   =  'Emily'
        p.lastname    =  'Deschanel'
        p.email       =  'edeschanel@fakemail.com'
        p.phone       =  '555 555 5555'

        u = user()
        u.name = 'edeschanel'
        u.service = 'carapacian'
        u.password = 'bones'
        u.person = p

        bp = blogpost()
        bp.blog = self.blog
        bp.body = test_article.Smallpostbody
        bp.title = test_article.Smallposttitle + str(uuid4())
        bp.excerpt = test_article.Smallpostexcerpt 
        bp.status = blogpost.Publish
        bp.iscommentable = True
        bp.author = u

        ts = tags().ALL()
        bp.tags += ts['health']
        bp.tags += ts['environment']

        for _ in range(2):
            bp.save()
            bp.body += 'small change'
        
        expect = """
Id:           {}
Author:       Emily Deschanel <edeschanel>
Created:      {}
Commentable:  True
Blog:         carapacian-tech-blog
Status:       Publish
Title:        {}
Excerpt:      Walden is a book by noted transcendentalist Henry David...
Body:         When I wrote the following pages, or rather the bulk of them,...
Tags:         #health #environment

Revisions
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ix | id      | createdat           | parentid | rootid  | title                      | excerpt                      | status  | iscommentable | slug                      | body | author                       |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0  | {} | {} |          | {} | Walden; or, Life in the... | Walden is a book by noted... | Publish | True          | walden-or-life-in-the-... | 354  | Emily Deschanel <edeschanel> |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | {} | {} | {}  | {} | Walden; or, Life in the... | Walden is a book by noted... | Publish | True          | walden-or-life-in-the-... | null | Emily Deschanel <edeschanel> |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
""".format( bp.id, 
			bp.createdat, 
            bp.title, 
            str(bp.revisions.first.id)[:7],
            bp.revisions.first.createdat, 
            str(bp.root.id)[:7],
            str(bp.revisions.second.id)[:7],
            bp.revisions.second.createdat, 
            str(bp.revisions.second.parent.id)[:7],
            str(bp.root.id)[:7])
        
        self.assertEq(expect, str(bp))
    
class test_articles(tester):
    def __init__(self):
        super().__init__()
        articlerevisions()   .RECREATE()
        blogpostrevisions()  .RECREATE()
        users()              .RECREATE()
        persons()            .RECREATE()
        tags()               .RECREATE()
        tags_mm_articles()   .RECREATE()

        ts = tags()
        for n in 'monsters', 'animals', 'orwell':
            ts += tag()
            ts.last.name = n
        ts.save()

        p = person()
        p.firstname   =  'George'
        p.lastname    =  'Orwell'
        p.email       =  'gorwell@fakemail.com'
        p.phone       =  '555 555 5555'

        u = user()
        u.name = 'gorwell'
        u.service = 'secker-and-warburg'
        u.password = 'doubleplusungood'
        u.person = p

        art = article()
        art.title = 'Animal Farm'
        art.excerpt = 'Animal Farm is an allegorical novella by George Orwell, first published in England on 17 August 1945.'
        art.body = """Mr. Jones, of the Manor Farm, had locked the hen-houses for
the night, but was too drunk to remember to shut the pop-holes. With the ring
of light from his lantern dancing from side to side, he lurched across the
yard, kicked off his boots at the back door, drew himself a last glass of beer
from the barrel in the scullery, and made his way up to bed, where Mrs. Jones
was already snoring."""
        art.author = u
        art.tags += ts['animals'] + ts['orwell']
        art.save()

        u = user()
        u.name = 'mshelley'
        u.service = 'lackington-hughes-harding-mavor-jones'
        u.password = 'fire'

        art = article()
        art.title = 'Frankenstein'
        art.excerpt = 'Frankenstein; or, The Modern Prometheus is a novel written by English author Mary Shelley (1797-1851) that tells the story of Victor Frankenstein, a young scientist who creates a grotesque but sapient creature in an unorthodox scientific experiment.'
        art.body = """I am by birth a Genevese, and my family is one of the
most distinguished of that republic. My ancestors had been for many years
counsellors and syndics, and my father had filled several public situations
with honour and reputation."""
        art.author = u
        art.tags += ts['monsters']
        art.save()
        art.body += """ He was respected by all who knew him for his
integrity and indefatigable attention to public business.  He passed his
younger days perpetually occupied by the affairs of his country; a variety of
circumstances had prevented his marrying early, nor was it until the decline of
life that he became a husband and the father of a family."""
        art.save()

        art = article()
        art.title = 'Summaries & Interpretations : Animal Farm'
        art.excerpt = 'The story takes place on a farm somewhere in England.The story is told by an all-knowing narrator in the third person.  T'
        art.body = """The story takes place on a farm somewhere in England.
The story is told by an all-knowing narrator in the third person.  The action
of this novel starts when the oldest pig on the farm, Old Major, calls all
animals to a secret meeting. He tells them about his dream of a revolution
against the cruel Mr Jones. Three days later Major dies, but the speech gives
the more intelligent animals a new outlook on life. The pigs, who are
considered the most intelligent animals, instruct the other ones. During the
period of preparation two pigs distinguish themselves, Napoleon and Snowball.
Napoleon is big, and although he isn't a good speaker, he can assert himself.
Snowball is a better speaker, he has a lot of ideas and he is very vivid.
Together with another pig called Squealer, who is a very good speaker, they
work out the theory of "Animalism". The rebellion starts some months later,
when Mr Jones comes home drunk one night and forgets to feed the animals. They
break out of the barns and run to the house, where the food is stored. When Mr
Jones sees this he takes out his shotgun, but it is too late for him; all the
animals fall over him and drive him off the farm. The animals destroy all
whips, nose rings, reins, and all other instruments that have been used to
suppress them. The same day the animals celebrate their victory with an extra
ration of food. The pigs make up the seven commandments, and they write them
above the door of the big barn."""
        art.tags += ts['animals'] + ts['orwell']
        art.save()

    def it_searches_body(self):
        arts = articles.search('Genevese')
        self.assertOne(arts)
        self.assertEq('Frankenstein', arts.first.title)
        self.assertTwo(arts.first.revisions)

        arts = articles.search('Mr Jones')
        self.assertTwo(arts)

        arts.sort('title')

        self.assertEq('Animal Farm', arts.first.title)
        self.assertEq('Summaries & Interpretations : Animal Farm', 
                      arts.second.title)

    def it_searches_title(self):
        arts = articles.search('animal farm')
        self.assertTwo(arts)

        arts.sort('title')

        self.assertEq('Animal Farm', arts.first.title)
        self.assertEq('Summaries & Interpretations : Animal Farm', arts.second.title)

        arts = articles.search('Frankenstein')
        self.assertOne(arts)
        self.assertEq('Frankenstein', arts.first.title)

    def it_searches_author(self):
        for str in 'gorwell', 'George', 'gorwell@fakemail.com':
            arts = articles.search(str)
            self.assertOne(arts)
            self.assertEq('Animal Farm', arts.first.title)

    def it_calls__str__(self):
        arts = articles().ALL()
        arts.sort('title')
        
        for art in arts: 
            art.tags.sort('name')

        expect = """+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| ix | id      | createdat  | title                                   | excerpt                                  | status | iscommentable | slug                                  | body | author                  | tags           |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0  | {0} | {3} | Animal Farm                             | Animal Farm is an allegorical novella... | Draft  | False         | animal-farm                           | 390  | George Orwell <gorwell> | animals orwell |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 1  | {1} | {4} | Frankenstein                            | Frankenstein; or, The Modern...          | Draft  | False         | frankenstein                          | 565  | mshelley                | monsters       |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 2  | {2} | {5} | Summaries & Interpretations : Animal... | The story takes place on a farm...       | Draft  | False         | summaries-interpretations-animal-farm | 1460 |                         | animals orwell |
+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
""".format(*[x.id.hex[:7] for x in arts] + [x.createdat.date() for x in arts])
        self.assertEq(expect, str(arts))

class test_article(tester):
    
    Smallposttitle = 'Walden; or, Life in the Woods'

    Smallpostbody = """When I wrote the following pages, or rather the bulk of them, I lived alone, in the woods, a mile from any neighbor, in a house which I had built myself, on the shore of Walden Pond, in Concord, Massachusetts, and earned my living by the labor of my hands only. I lived there two years and two months. At present I am a sojourner in civilized life again.""" 
    Smallpostexcerpt = """Walden is a book by noted transcendentalist Henry David Thoreau. The text is a reflection upon simple living in natural surroundings. The work is part personal declaration of independence, social experiment, voyage of spiritual discovery, satire, and-to some degree-a manual for self-reliance.""" 
    def __init__(self):
        super().__init__()
        articlerevisions()  .RECREATE()
        persons()           .RECREATE()
        tags_mm_articles()  .RECREATE()
        tags()              .RECREATE()
        users()             .RECREATE()

        for name in 'ethics', 'environment', 'health':
            t = tag()
            t.name = name
            t.save()

    def it_calls_tags(self):
        ts = tags().ALL()
        art = article()
        art.body   =  test_article.Smallpostbody
        art.title  =  test_article.Smallposttitle  +  str(uuid4())

        # Ensure we start out with zero
        self.assertZero(art.tags)

        # Add and remove a tag without saving. Test the count
        art.tags += ts['health']
        self.assertOne(art.tags)

        art.tags -= ts['health']
        self.assertZero(art.tags)

        art.tags += ts['health']
        self.assertOne(art.tags)

        # Save, test, reload, test
        art.save()
        self.assertOne(art.tags)
        self.assertEq('health', art.tags.first.name)

        art = article(art.id)
        self.assertOne(art.tags)
        self.assertEq('health', art.tags.first.name)

        # Add second tab, test, save, reload, test
        art.tags += ts['environment']
        self.assertTwo(art.tags)
        self.assertEq('health',       art.tags.first.name)
        self.assertEq('environment',  art.tags.second.name)

        art.save()
        art.tags.sort('name')

        self.assertTwo(art.tags)
        self.assertEq('environment',  art.tags.first.name)
        self.assertEq('health',       art.tags.second.name)

        art = article(art.id)
        art.tags.sort('name')

        self.assertTwo(art.tags)
        self.assertEq('environment',  art.tags.first.name)
        self.assertEq('health',       art.tags.second.name)

        # Add third tag, remove first test, save, reload, test
        art.tags += ts['ethics']
        art.tags.shift()
        self.assertTwo(art.tags)
        self.assertEq('health', art.tags.first.name)
        self.assertEq('ethics', art.tags.second.name)

        art.save()
        self.assertTwo(art.tags)
        self.assertEq('health', art.tags.first.name)
        self.assertEq('ethics', art.tags.second.name)

        art = article(art.id)

        art.tags.sort('name')
        self.assertTwo(art.tags)
        self.assertEq('ethics', art.tags.first.name)
        self.assertEq('health', art.tags.second.name)

        # Remove the rest of the tags until there are zero
        art.tags.shift()
        art.save()
        art = article(art.id)
        self.assertOne(art.tags)
        self.assertEq('health', art.tags.first.name)

        art.tags.shift()
        art.save()
        art = article(art.id)
        self.assertZero(art.tags)

    def it_call_isdirty(self):
        u = user()
        u.name      =  'byoung'
        u.password  =  'secret'
        u.service   =  'carapacian'

        u1 = user()
        u1.name      =  'caffleck'
        u1.password  =  'secret'
        u1.service   =  'carapacian'

        art0 = article()
        art0.body                       =  test_article.Smallpostbody
        art0.title                      =  test_article.Smallposttitle + str(uuid4())
        art0.excerpt                    =  test_article.Smallpostexcerpt
        art0.status                     =  article.Future
        art0.iscommentable              =  True
        art0.author                     =  u
        self.assertFalse(art0.isdirty)

        art0.save()
        art = article(art0.id)

        self.assertFalse(art.isdirty)

        props = 'title', 'body', 'excerpt', 'status', 'iscommentable'

        for prop in props:
            if    prop  ==  'status':         newval  =  article.Draft
            elif  prop  ==  'iscommentable':  newval  =  False
            elif  prop  ==  'author':         newval  =  u1
            else:                             newval  = uuid4().hex

            setattr(art, prop, newval)
            self.assertTrue(art.isdirty, prop + ' did not dirty article')

            setattr(art, prop, getattr(art0, prop))
            self.assertFalse(art.isdirty, 'Could not clean article')

    def it_loads_as_valid(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title  = title
        slug = re.sub(r'\W+', '-', art.title).strip('-').lower()
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True
        art.save()
        art = article(art.id)
        self.assertValid(art)

    def it_saves_x_revisions_with_null_properties(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title  = title
        slug = re.sub(r'\W+', '-', art.title).strip('-').lower()
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        x = 4
        for i in range(x):
            if i < x / 2:
                art.title = None
                art.excerpt = None
                art.slug = None
            else:
                art.body = test_article.Smallpostbody  + ' Rev: ' + str(i)
                revisedtitle = title + ' Rev: ' + str(i)
                art.title = revisedtitle
                art.excerpt = test_article.Smallpostexcerpt  + ' Rev: ' + str(i)
                
            art.save()

            art = article(art.id)

            if i < x / 2:
                self.assertEq(test_article.Smallpostbody, art.body)
                self.assertEq(title, art.title)
                self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
            else:
                self.assertEq(test_article.Smallpostbody + ' Rev: ' + str(i), art.body)
                self.assertEq(revisedtitle, art.title)
                self.assertEq(test_article.Smallpostexcerpt + ' Rev: ' + str(i), art.excerpt)
            self.assertEq(article.Pending, art.status)
            self.assertTrue(art.iscommentable)
            self.assertEq(slug, art.slug)

    def it_calls_body(self): 
        art = article()
        self.assertNone(art.body)
        art.save()
        self.assertEmpty(art.body)

        art.body = test_article.Smallpostbody
        self.assertEq(test_article.Smallpostbody, art.body)

        art.save()
        self.assertEq(test_article.Smallpostbody, art.body)

        art = article(art.id)
        self.assertEq(test_article.Smallpostbody, art.body)

    def it_calls_bodycache(self):
        art = article()
        body = str(uuid4())
        art.body = body
        art.save()
        art = article(art.id)

        self.assertEq(body, art.revisions.root.bodycache)

        body = str(uuid4())
        art.body = body
        art.save()
        art = article(art.id)

        self.assertEq(body, art.revisions.root.bodycache)
        self.assertNone(art.revisions.second.bodycache)

        body = str(uuid4())
        art.body = body
        art.save()
        art = article(art.id)

        self.assertEq(body, art.revisions.root.bodycache)
        self.assertNone(art.revisions.second.bodycache)
        self.assertNone(art.revisions.third.bodycache)

        art.status = 9999 # Invalidate
        art.body = str(uuid4())
        try:
            art.save()
        except BrokenRulesError:
            pass
        except:
            self.assertFail('Wrong exception thrown')
        else:
            self.assertFail('Exception was not raised')

        self.assertEq(body, art.revisions.root.bodycache)


    def it_calls_createdat(self):
        art = article()
        self.assertNone(art.createdat)
        before = datetime.now().replace(microsecond=0)

        art.save()

        after = datetime.now().replace(microsecond=0)

        self.assertLe(before, art.createdat)
        self.assertGe(after, art.createdat)

        createdat = art.createdat

        art = article(art.id)
        self.assertEq(createdat, art.createdat)

    def it_calls_publishedat(self):
        art = article()
        self.none(art.publishedat)
        art.save()
        self.none(art.publishedat)
        art = article(art.id)
        self.none(art.publishedat)

        art.status = article.Publish
        self.none(art.publishedat)
        for i in range(2):
            art.save()
            self.type(datetime, art.publishedat)

        art = article(art.id)
        self.type(datetime, art.publishedat)

        # Revert back to draft
        art.status = article.Draft
        self.type(datetime, art.publishedat)
        art.save()
        self.none(art.publishedat)
        art = article(art.id)
        self.none(art.publishedat)

        # Advance back to Publish
        art.status = article.Publish
        self.none(art.publishedat)
        for i in range(2):
            art.save()
            self.type(datetime, art.publishedat)

        art = article(art.id)
        self.type(datetime, art.publishedat)

    def it_calls_title(self):
        art = article()
        self.assertNone(art.title)

        art.save()

        self.assertEmpty(art.title)

        art.title = test_article.Smallposttitle
        self.assertEq(test_article.Smallposttitle, art.title)

        art.save()
        self.assertEq(test_article.Smallposttitle, art.title)

        art = article(art.id)
        self.assertEq(test_article.Smallposttitle, art.title)

    def it_calls_titlecache(self):
        art = article()
        art.save()
        art = article(art.id)

        self.assertEmpty(art.revisions.root.titlecache)

        title = str(uuid4())
        art.title = title
        art.save()
        art = article(art.id)

        self.assertEq(title, art.revisions.root.titlecache)
        self.assertNone(art.revisions.second.titlecache)

        title = str(uuid4())
        art.title = title
        art.save()
        art = article(art.id)

        self.assertEq(title, art.revisions.root.titlecache)
        self.assertNone(art.revisions.second.titlecache)
        self.assertNone(art.revisions.third.titlecache)

        art.status = 9999 # Invalidate
        art.title = str(uuid4())
        try:
            art.save()
        except BrokenRulesError:
            pass
        except:
            self.assertFail('Wrong exception thrown')
        else:
            self.assertFail('Exception was not raised')

        self.assertEq(title, art.revisions.root.titlecache)

    def it_calls_slug(self):
        art = article()
        self.assertNone(art.slug)

        art.save()

        self.assertEmpty(art.slug)

        slug = str(uuid4())
        art.slug = slug
        self.assertEq(slug, art.slug)

        art.save()
        self.assertEq(slug, art.slug)

        art = article(art.id)
        self.assertEq(slug, art.slug)

    def it_calls_title_and_slug(self):
        art = article()
        title = 'Herp derp'
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        art.title = title

        self.assertEq(slug, art.slug)

        art.save()
        self.assertEq(slug, art.slug)

        art = article(art.id)
        self.assertEq(slug, art.slug)

    def it_calls_excerpt(self):
        art = article()
        self.assertNone(art.excerpt)
        art.save()
        self.assertEmpty(art.excerpt)

        art = article(art.id)
        self.assertEmpty(art.excerpt)

        art = article()
        self.assertNone(art.excerpt)
        art.save()
        self.assertEmpty(art.excerpt)
        art = article(art.id)
        self.assertEmpty(art.excerpt)

        art = article()
        art.excerpt = test_article.Smallpostexcerpt
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
        art.save()
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
        art = article(art.id)
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)

    def it_calls_status(self): 
        art = article()
        self.assertNone(art.status)
        art.save()
        self.assertEq(article.Draft, art.status)
        art = article(art.id)
        self.assertEq(article.Draft, art.status)

        art = article()
        art.status = article.Pending
        self.assertEq(article.Pending, art.status)
        art.save()
        self.assertEq(article.Pending, art.status)
        art = article(art.id)
        self.assertEq(article.Pending, art.status)

    def it_calls_statusproperties(self): 
        # This is a work in progress
        art = article()
        self.false(art.ispublished)
        art.status = article.Publish
        self.true(art.ispublished)

    def it_calls_iscommentable(self): 
        art = article()
        self.assertNone(art.iscommentable)
        art.save()
        self.assertFalse(art.iscommentable)
        art = article(art.id)
        self.assertFalse(art.iscommentable)

        art = article()
        art.iscommentable = True
        self.assertTrue(art.iscommentable)
        art.save()
        self.assertTrue(art.iscommentable)
        art = article(art.id)
        self.assertTrue(art.iscommentable)

        art = article()
        art.iscommentable = False
        self.assertFalse(art.iscommentable)
        art.save()
        self.assertFalse(art.iscommentable)
        art = article(art.id)
        self.assertFalse(art.iscommentable)

    def it_calls_author(self):
        u = user()
        u.name      =  'asilverston'
        u.service   =  'carapacian'
        u.password  =  'secret'

        u1 = user()
        u1.name      =  'agrande'
        u1.service   =  'carapacian'
        u1.password  =  'secret'

        # Create article, test its author is None, save and re-test
        art = article()
        self.assertNone(art.author)
        art.save()
        self.assertNone(art.author)
        art = article(art.id)
        self.assertNone(art.author)

        # Associate author, test, reload and test
        art.author = u
        self.assertEq(u.name, art.author.name)
        art.save()
        self.assertEq(u.name, art.author.name)
        art = article(art.id)
        self.assertEq(u.name, art.author.name)

        # Change author, test, reload and test
        art.author = u1
        self.assertEq(u1.name, art.author.name)
        art.save()
        self.assertEq(u1.name, art.author.name)
        art = article(art.id)
        self.assertEq(u1.name, art.author.name)
        
        # Ensure each revision of the article has the correct author
        self.assertNone(art.revisions.first.author)
        self.assertEq(u.name,    art.revisions.second.author.name)
        self.assertEq(u1.name,   art.revisions.third.author.name)

    def it_calls_authorcache(self):
        u = user()
        u.name      =  'wharrelson'
        u.service   =  'carapacian'
        u.password  =  'secret'

        u1 = user()
        u1.name      =  'mbialik'
        u1.service   =  'carapacian'
        u1.password  =  'secret'

        art = article()
        art.save()
        art = article(art.id)

        self.assertNone(art.revisions.root.authorcache)

        art.author = u
        art.save()
        art = article(art.id)

        self.assertEq(u.name, art.revisions.root.authorcache)
        self.assertNone(art.revisions.second.authorcache)

        art.author = u1
        art.save()
        art = article(art.id)

        self.assertEq(u1.name, art.revisions.root.authorcache)
        self.assertNone(art.revisions.second.authorcache)
        self.assertNone(art.revisions.third.authorcache)

        art.status = 9999 # Invalid
        art.author = u

        try:
            art.save()
        except BrokenRulesError:
            pass
        except:
            self.assertFail('Wrong exception thrown')
        else:
            self.assertFail('Exception was not raised')

        self.assertEq(u1.name, art.revisions.root.authorcache)

        p = person()
        p.firstname   =  'Woody'
        p.lastname    =  'Harrelson'
        p.email       =  'wharrelson@fakemail.com'
        p.phone       =  '555 555 5555'
        u.person = p

        art.author = u
        art.status = article.Pending
        art.save()
        art = article(art.id)

        expect = '{} {} {}'.format(u.name, p.fullname, p.email)
        self.assertEq(expect, art.revisions.root.authorcache)

    def it_searches_by_id(self):
        art = article()
        art.save()
        id = art.id

        art = article(id)
        self.assertEq(id,   art.id)

    def it_searches_by_slug(self):
        art = article()
        slug = str(uuid4())
        art.slug = slug
        art.save()
        id = art.id

        art = article(slug)
        self.assertEq(slug, art.slug)
        self.assertEq(id,   art.id)

    def it_calls_wont_save_if_there_are_brokenrules(self): 
        # TODO
        return
        art = article()
        try:
            art.save()
        except BrokenRulesError as ex:
            self.assertIs(art, ex.object)
        except:
            msg = ('BrokenRulesError expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_calls_slug_and_title(self):
        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        art = article()
        art.title = title
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)
        art.save()
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)
        art = article(art.id)
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)
        art = article(art.id)
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)

        title = test_article.Smallposttitle + str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()
        art = article()
        self.assertNone(art.slug)
        self.assertEq(None, art.title) 
        art.title = title
        self.assertEq(slug, art.slug)
        self.assertEq(title, art.title)

        art.save()
        self.assertEq(title, art.title)
        self.assertEq(slug, art.slug)
        art = article(art.id)
        self.assertEq(title, art.title)
        self.assertEq(slug, art.slug)

        art = article()
        self.assertEq(None, art.title)
        art.save()
        self.assertEq('', art.title)
        self.assertEmpty(art.slug)
        art = article(art.id)
        self.assertEmpty(art.slug)
        self.assertEq('', art.title)

        art = article()
        art.slug = 'Herp Derp'
        self.assertEq('Herp Derp', art.slug)
        self.assertEq(None, art.title)
        art.title = title
        self.assertEq('Herp Derp', art.slug)
        art.save()
        self.assertEq(title, art.title)
        self.assertEq('Herp Derp', art.slug)
        art = article(art.id)
        self.assertEq(title, art.title)
        self.assertEq('Herp Derp', art.slug)

    def it_saves_x_revisions_with_empty_properties(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title = title
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        for i in range(2):
            art.title = ''
            art.excerpt = ''
            art.slug = ''
            art.save()

            art = article(art.id)
            self.assertEmpty(art.title)
            self.assertEmpty(art.excerpt)
            self.assertEq(article.Pending, art.status)
            self.assertTrue(art.iscommentable)
            self.assertEmpty(art.slug)

    def it_saves_x_revisions(self):
        art = article()
        art.body = test_article.Smallpostbody
        title = test_article.Smallposttitle + ' - ' + str(uuid4())
        art.title = title
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        createdat = art.createdat
        
        self.assertNotNone(art.id)
        self.assertEq(test_article.Smallpostbody, art.body)
        self.assertEq(title, art.title)
        self.assertEq(test_article.Smallpostexcerpt, art.excerpt)
        self.assertEq(article.Pending, art.status)
        self.assertEq(True, art.iscommentable)
        slug = re.sub(r'\W+', '-', art.title).strip('-').lower()
        self.assertEq(slug, art.slug)

        x = 20

        for i in range(x):
            id = art.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = art.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(art.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                art.slug = 'walden-or-life-in-the-woods-hard-set'
                newbody = 'X' + art.body
                
            art.body = newbody

            art.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            art.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            art.status = article.Publish
            art.iscommentable = i % 2 == 0
            
            art.save()

            self.assertNotNone(art.id)
            self.assertEq(id, art.id)
            self.assertEq(newbody, art.body)
            self.assertEq(createdat, art.createdat)
            self.assertEq(newtitle, art.title)
            self.assertEq(newexcerpt, art.excerpt)
            self.assertEq(article.Publish, art.status)
            self.assertEq(i % 2 == 0, art.iscommentable)
            if i > 10:
                self.assertEq('walden-or-life-in-the-woods-hard-set', art.slug)
            else:
                self.assertEq(slug, art.slug)

    def _createblogpost(self):
        art = article()
        art.body = test_article.Smallpostbody
        art.title = test_article.Smallposttitle 
        art.excerpt = test_article.Smallpostexcerpt 
        art.status = article.Pending
        art.iscommentable = True

        art.save()

        x = 20

        for i in range(x):
            id = art.id

            # Mutate the body to ensure revision patching works
            if i < 5:
                newbody = art.body + 'X'
            elif i >= 5 and i <= 10:
                newbody = ''
                for j, c in enumerate(art.body):
                    if j == i:
                        c = 'x'
                    newbody += c
            elif i > 10:
                newbody = 'X' + art.body
                
            art.body = newbody

            art.title = newtitle = test_article.Smallposttitle + ' Rev ' + str(i)
            art.excerpt = newexcerpt = test_article.Smallpostexcerpt + ' Rev ' + str(i)
            art.status = article.Publish
            art.iscommentable = i % 2 == 0
            
            art.save()
        return art

    def it_retrives_blogpost(self):
        bp1 = self._createblogpost()
        bp2 = article(bp1.id)

        self.assertTrue(type(bp2.id) == uuid.UUID)
        self.assertEq(bp1.id,                bp2.id)

        self.assertEq(type(bp2.createdat),  datetime)
        self.assertEq(bp1.createdat,        bp2.createdat)

        self.assertEq(bp1.body,              bp2.body)
        self.assertEq(bp1.title,             bp2.title)
        self.assertEq(bp1.excerpt,           bp2.excerpt)
        self.assertEq(bp1.status,            bp2.status)
        self.assertEq(bp1.iscommentable,     bp2.iscommentable)

class test_articlerevisions(tester):
    def __init__(self):
        super().__init__()
        articlerevisions().RECREATE()

class test_articlerevision(tester):
    def __init__(self):
        super().__init__()
        articlerevisions().RECREATE()
        users().RECREATE()

    def it_instantiates(self):
        rev = articlerevision()
        self.assertNone(rev.id)
        self.assertNone(rev.author)
        self.assertNone(rev.createdat)
        self.assertNone(rev.title)
        self.assertNone(rev.body)
        self.assertNone(rev.excerpt)
        self.assertEq(article.Draft, rev.status)
        self.assertFalse(rev.iscommentable)
        self.assertNone(rev.slug)

    def it_calls_str(self):
        u = user()
        u.name      =  'jphoenix'
        u.service   =  'carapacian'
        u.password  =  'secret'

        rev = articlerevision()

        title    =  test_article.Smallposttitle    +  str(uuid4())
        slug = re.sub(r'\W+', '-', title).strip('-').lower()

        rev.title = title
        rev.slug = slug
        rev.slugcache = slug
        rev.excerpt  =  test_article.Smallpostexcerpt
        rev.body     =  test_article.Smallpostbody

        expect = """Title:          {}
Excerpt:        {}
Status:         {}
Body:           {}
Slug:           {}
SlugCache:      {}
""".format( rev.title, 
                    rev.excerpt, 
                    str(rev.status), 
                    str(len(rev.body)),
                    rev.slug,
                    rev.slugcache)

        self.assertEq(expect, str(rev))

        rev.save()

        expect = """Created:        {}
Title:          {}
Excerpt:        {}
Status:         {}
Body:           {}
Slug:           {}
SlugCache:      {}
""".format(
        str(rev.createdat),
        rev.title, 
        rev.excerpt, 
        str(rev.status), 
        str(len(rev.body)),
        rev.slug,
        rev.slugcache)

        self.assertEq(expect, str(rev))

        rev.author = u

        expect = """Created:        {}
Title:          {}
Excerpt:        {}
Status:         {}
Body:           {}
Slug:           {}
SlugCache:      {}
Author:         {}
""".format(
        str(rev.createdat),
        rev.title, 
        rev.excerpt, 
        str(rev.status), 
        str(len(rev.body)),
        rev.slug,
        rev.slugcache,
        str(rev.author.name))

        self.assertEq(expect, str(rev))


        child = articlerevision()
        child._parent = rev
        child.save()
        expected = """Parent:         {}
Created:        {}
Status:         {}
""".format(str(child.parent.id),
           str(child.createdat),
           str(child.status))

        self.assertEq(expect, str(rev))

    def it_calls_author(self):

        # Create new revision and user, associate the two, save and test
        u = user()
        u.name      =  'jphoenix'
        u.service   =  'carapacian'
        u.password  =  'secret'

        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())

        rev.author = u

        rev.save()

        rev = articlerevision(rev.id)
        self.assertEq(u.name, rev.author.name)

        # Create new revision, associate an existing author
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.author = u
        u.save()

        self.assertEq(u.name, rev.author.name)

    def it_fails_on_save_when_invalid(self):
        rev = articlerevision()
        try:
            rev.save()
        except BrokenRulesError as ex:
            self.assertIs(rev, ex.object)
        except Exception as ex:
            msg = ('BrokenRulesError expected however a different exception '
                  ' was thrown: ' + str(type(ex)))
            self.assertFail(msg)
        else:
            self.assertFail('No exception thrown on save of invalid object.')

    def it_fails_to_load_given_nonexistent_id(self):
        try:
            rev = articlerevision(uuid4())
        except Exception as ex:
            self.assertTrue(True)
        else:
            self.assertFail('Exception was not thrown')

    def it_loads_as_valid(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.save()

        rev = articlerevision(rev.id)
        self.assertValid(rev)

    def it_breaks_diff_rules(self):
        # Diff must be empty for root revisions
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        rev.diff = diff.diff('herp', 'derp')
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'empty'))

        # Fix
        rev.diff = None
        self.assertValid(rev)

        # Break the rule that says a diff must be of type diff.diff
        rent = articlerevision()
        rent.body = test_article.Smallpostbody
        rent.title = test_article.Smallposttitle
        rent.diff = diff.diff('herp', 'derp')

        rev._parent = rent
        rev.body = None
        rev.diff = 'wrong type'
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

    def it_breaks_title_rules(self):
        # Root revisions must have non null titles
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Non-root revisions can have null titles
        rev._parent = articlerevision()
        self.assertCount(0, rev.brokenrules)

        # Root revisions can have empty strings as titles
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = ''
        self.assertCount(0, rev.brokenrules)

        # Revisions titles must be strings
        rev.title = 123
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))
        rev._parent = articlerevision() # Make non-root
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'valid'))

        # Title must be less than 500 characters
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = 'X' * 500
        self.assertCount(0, rev.brokenrules)
        rev.title = 'X' * 501
        self.assertCount(1, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('title', 'fits'))

    def it_breaks_status_rules(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle
        for st in article.Statuses:
            rev.status = st
            self.assertCount(0, rev.brokenrules)

        for st in ('wrong-type', 9999, object()):
            rev.status = st
            self.assertCount(1, rev.brokenrules)
            self.assertTrue(rev.brokenrules.contains('status', 'valid'))

    def it_breaks_body_rules(self):
        # Body must be full for root revisions
        rev = articlerevision()
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('body', 'full'))
        self.assertTrue(rev.brokenrules.contains('title', 'full'))

        # Create a parent then test the child
        rent = articlerevision()
        rent.body = test_article.Smallpostbody
        rent.title = test_article.Smallposttitle
        rent.diff = diff.diff('herp', 'derp')

        # A body and a diff shouldn't exist in the same record
        rev._parent = rent
        rev.diff = diff.diff('herp', 'derp')
        rev.body = test_article.Smallpostbody
        self.assertCount(2, rev.brokenrules)
        self.assertTrue(rev.brokenrules.contains('diff', 'valid'))

        # A non-root revision should can have a body but no diff. This
        # may be useful for caching or other isssues such as a failure to
        # create a diff.
        rev.body = test_article.Smallpostbody
        rev.diff = None
        self.assertValid(rev)

    def it_retrieves(self):
        rev = articlerevision()
        rev.body = test_article.Smallpostbody
        rev.title = test_article.Smallposttitle + str(uuid4())
        rev.save()

        rev = articlerevision(rev.id)
        self.assertEq(rev.id, rev.id)


class test_persons(tester):
    def __init__(self):
        super().__init__()
        persons()           .RECREATE()

    def it_calls__str__(self):
        ps = persons()

        p = person()
        p.firstname   =  'Ellan'
        p.lastname    =  'Page'
        p.email       =  'epage@fakemail.com'
        p.phone       =  '555 555 5555'
        ps += p

        p = person()
        p.firstname   =  'Jessica'
        p.lastname    =  'Chastain'
        p.email       =  'jchastain@fakemail.com'
        p.phone       =  '555 555 5555'
        ps += p

        p = person()
        p.firstname   =  'James'
        p.lastname    =  'Cromwell'
        p.email       =  'jcromwell@fakemail.com'
        p.phone       =  '555 555 5555'
        ps += p

        expect = """+-------------------------------------------------------------------------------------+
| ix | id | firstname | middlename | lastname | email                  | phone        |
|-------------------------------------------------------------------------------------|
| 0  |    | Ellan     |            | Page     | epage@fakemail.com     | 555 555 5555 |
|-------------------------------------------------------------------------------------|
| 1  |    | Jessica   |            | Chastain | jchastain@fakemail.com | 555 555 5555 |
|-------------------------------------------------------------------------------------|
| 2  |    | James     |            | Cromwell | jcromwell@fakemail.com | 555 555 5555 |
+-------------------------------------------------------------------------------------+
"""
        self.assertEq(expect, str(ps))

    def it_calls_search(self):
        ps = persons()
        p = person()
        p.firstname   =  'Ellan'
        p.lastname    =  'Page'
        p.email       =  'epage@fakemail.com'
        p.phone       =  '555 555 1111'
        ps += p

        p = person()
        p.firstname   =  'Jessica'
        p.lastname    =  'Chastain'
        p.email       =  'jchastain@fakemail.com'
        p.phone       =  '555 555 2222'
        ps += p

        p = person()
        p.firstname   =  'James'
        p.lastname    =  'Cromwell'
        p.email       =  'jcromwell@fakemail.com'
        p.phone       =  '555 555 3333'
        ps += p

        ps.save()

        for s in 'james', 'Cromwell', 'jcromwell', 3333:
            ps = persons.search(s)

            self.assertOne(ps)
            self.assertEq('James',     ps.first.firstname)
            self.assertEq('Cromwell',  ps.first.lastname)

        ps = persons.search(555)
        self.assertThree(ps)

    def it_calls_sorted(self):
        # dbentities.sorted usually depends on the correct implementation of
        # __init__ and __iter__. These implementations are fragile and prone to
        # change so it's important to test them.
        ps = persons()
        p = person()
        p.firstname   =  'Ellan'
        p.lastname    =  'Page'
        p.email       =  'epage@fakemail.com'
        p.phone       =  '555 555 1111'
        ps += p

        p = person()
        p.firstname   =  'Jessica'
        p.lastname    =  'Chastain'
        p.email       =  'jchastain@fakemail.com'
        p.phone       =  '555 555 2222'
        ps += p

        p = person()
        p.firstname   =  'James'
        p.lastname    =  'Cromwell'
        p.email       =  'jcromwell@fakemail.com'
        p.phone       =  '555 555 3333'
        ps += p

        # Sort by firstname
        ps1 = ps.sorted('firstname')
        self.assertEq('Ellan', ps1.first.firstname)
        self.assertEq('James', ps1.second.firstname)
        self.assertEq('Jessica', ps1.third.firstname)

        # Sort by firstname in reverse order
        ps1 = ps.sorted('firstname', True)
        self.assertEq('Jessica', ps1.first.firstname)
        self.assertEq('James', ps1.second.firstname)
        self.assertEq('Ellan', ps1.third.firstname)
    
class test_person(tester):
    def __init__(self):
        super().__init__()
        persons().RECREATE()

    def it_calls__str__(self):
        p = person()
        p.firstname   =  'Tom'
        p.lastname    =  'Regan'
        p.email       =  'tregan@fakemail.com'
        p.phone       =  '555 555 5555'

        expect = """First name: Tom
Last name: Regan
Email: tregan@fakemail.com
Phone: 555 555 5555
"""
        self.assertEq(expect, str(p)) 

    def it_calls_save(self):
        p = person()
        p.firstname   =  'Gary'
        p.middlename  =  'Lawrence'
        p.lastname    =  'Francione'
        p.email       =  'glawrence@fakemail.com'
        p.phone       =  '480 555 5555'
        p.save()

    def it_loads(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.lastname = 'Francione'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'
        p.save()

        p1 = person(p.id)

        for prop in ('firstname', 'middlename', 'lastname', 'id', 'email', 'phone'):
            self.assertEq(getattr(p, prop), getattr(p1, prop))

    def it_deletes(self):
        p = person()
        p.firstname   =  'Peter'
        p.middlename  =  'Albert David'
        p.lastname    =  'Singer'
        p.email       =  'psinger@fakemail.com'
        p.phone       =  '555 555 5555'

        p.save()
        p = person(p.id)
        cnt = p.delete()

        self.assertEq(1, cnt)
        self.assertTrue(p.isnew)

        cnt = p.delete()
        self.assertEq(0, cnt)

        try:
            p = person(p.id)
        except Exception:
            pass
        else:
            self.assertFail('No exception thrown')

    def it_calls_fullname(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.lastname = 'Francione'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'

        self.assertEq(p.firstname + ' ' + p.lastname, p.fullname)

    def it_calls_name(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.lastname = 'Francione'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'

        self.assertEq(p.fullname, p.name)

    def it_breaks_firstname_rule(self):
        p = person()
        p.firstname = 'X' * 255
        p.middlename = 'Lawrence'
        p.lastname = 'Francione'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'

        self.assertZero(p.brokenrules)

        p.firstname = 'X' * 256
        self.assertCount(1, p.brokenrules)
        self.assertTrue(p.brokenrules.contains('firstname', 'fits'))

    def it_breaks_middlename_rule(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'X' * 255
        p.lastname = 'Francione'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'

        self.assertZero(p.brokenrules)

        p.middlename = 'X' * 256
        self.assertCount(1, p.brokenrules)
        self.assertTrue(p.brokenrules.contains('middlename', 'fits'))

    def it_breaks_lastname_rule(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.lastname = ''
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'

        self.assertCount(1, p.brokenrules)
        self.assertTrue(p.brokenrules.contains('lastname', 'full'))

        p.lastname = 'X' * 255
        self.assertZero(p.brokenrules)

        p.lastname = 'X' * 256
        self.assertCount(1, p.brokenrules)
        self.assertTrue(p.brokenrules.contains('lastname', 'fits'))

    def it_breaks_email_rule(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.lastname = 'Francione'
        p.email = 'not-an-email-address'
        p.phone = '555 555 5555'

        self.assertCount(1, p.brokenrules)
        self.assertTrue(p.brokenrules.contains('email', 'valid'))

        p.email = ('X' * 246) + '@mail.com'
        self.assertZero(p.brokenrules)

        p.email = ('X' * 247) + '@mail.com'
        self.assertCount(1, p.brokenrules)
        self.assertTrue(p.brokenrules.contains('email', 'fits'))

    def it_breaks_phone_rule(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.lastname = 'Francione'
        p.email = 'glawrence@fakemail.com'
        p.phone = 'X' * 255

        self.assertZero(p.brokenrules)

        p.phone = 'X' * 256
        self.assertCount(1, p.brokenrules)
        self.assertTrue(p.brokenrules.contains('phone', 'fits'))

    def it_wont_save_invaild(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'
        p.lastname = ''

        try:
            p.save()
        except BrokenRulesError:
            pass # This should happen
        except Exception as ex:
            self.assertFail('Incorrect exception type: ' + str(type(ex)))
        else:
            self.assertFail("Invalid person object didn't throw error on save")

    def it_updates(self):
        p = person()
        p.firstname = 'Gary'
        p.middlename = 'Lawrence'
        p.lastname = 'Francione'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'
        p.save() # insert

        p = person(p.id)
        p.firstname = 'Gary - update'
        p.middlename = 'Lawrence - update'
        p.lastname = 'Francione - update'
        p.email = 'glawrence@fakemail.com'
        p.phone = '555 555 5555'
        p.save() # update

        p1 = person(p.id)
        for prop in ('firstname', 'middlename', 'lastname', 'id', 'email', 'phone'):
            self.assertEq(getattr(p, prop), getattr(p1, prop))

    def it_adds_users(self):
        # Create new person
        p = person()
        p.firstname  =  'Joseph'
        p.lastname   =  'Armstrong'
        p.email      =  'jarmstrong@fakemail.com'
        p.phone      =  '555 555 5555'

        # Create new user
        u = user()
        u.service   =  str(uuid4())
        u.name      =  str(uuid4())
        u.password  =  str(uuid4())

        us = users()
        us += u

        # Add user to person and save
        p.users += u

        # Test p.users
        self.assertEq(u.service,    p.users.first.service)
        self.assertEq(u.name,       p.users.first.name)

        p.save()

        # Reload person; test p.users
        p = person(p.id)

        self.assertEq(u.service,    p.users.first.service)
        self.assertEq(u.name,       p.users.first.name)
        self.assertEq(u.person.id,  p.id)

        # Change property of user, test, save person, reload, test
        name = str(uuid4())
        p.users.first.name = name

        self.assertOne(p.users)
        self.assertTrue(p.isdirty)
        self.assertEq(u.service,    p.users.first.service)
        self.assertEq(name,         p.users.first.name)
        self.assertEq(u.person.id,  p.id)

        p.save()

        p = person(p.id)

        self.assertOne(p.users)
        self.assertEq(u.service,    p.users.first.service)
        self.assertEq(name,         p.users.first.name)
        self.assertEq(u.person.id,  p.id)

        # Create new user, add user, test, save person, test
        u = user()
        u.service   =  str(uuid4())
        u.name      =  str(uuid4())
        u.password  =  str(uuid4())

        us += u

        p.users += u

        ## Correct for the name change above so we can test by iteration
        us.first.name = name

        self.assertTwo(p.users)
        for u, pu in zip(us, p.users):
            self.assertEq(u.service,    pu.service)
            self.assertEq(u.name,       pu.name)

        p.save()

        p = person(p.id)

        self.assertTwo(p.users)

        us.sort(); p.users.sort()
        for u, pu in zip(us, p.users):
            self.assertEq(u.service,    pu.service)
            self.assertEq(u.name,       pu.name)
            self.assertEq(u.person.id,  p.id)

        # Create new user, add user, remove another user, test, save person, test
        u = user()
        u.service   =  str(uuid4())
        u.name      =  str(uuid4())
        u.password  =  str(uuid4())

        ## Add user to us collection, sort, and shift. This is to test against p.users.

        # TODO FIXME Appending a new user, sorting by id, then shift()ing results
        # in the new user being immediately removed - so basically nothing is
        # happening here. The same thing happens below with p.users. This bug
        # makes the test work.  It conceals the fact that shift()ing doesn't
        # mark the user entity for deletion.
        us += u
        us.sort()
        us.shift()

        ## Add to p.users, sort and shift. We we are adding one and removing another.
        p.users += u
        p.users.sort()
        p.users.shift()

        self.assertTwo(p.users)
        for u, pu in zip(us, p.users):
            self.assertEq(u.service,    pu.service)
            self.assertEq(u.name,       pu.name)

        p.save()

        p = person(p.id)

        self.assertTwo(p.users)

        us.sort(); p.users.sort()
        for u, pu in zip(us, p.users):
            self.assertEq(u.service,    pu.service)
            self.assertEq(u.name,       pu.name)
            self.assertEq(u.person.id,  p.id)

class test_users(tester):
    def __init__(self):
        super().__init__()
        users().RECREATE()
        roles().RECREATE()
        roles_mm_objects().RECREATE()

    def it_calls_search(self):
        us = users()
        u = user()
        u.service   =  'carapacian'
        u.name      =  'glawrence'
        u.password  =  'secret'

        us += u

        u = user()
        u.service   =  'carapacian'
        u.name      =  'epage'
        u.password  =  'secret'

        us += u

        us.save()

        us = users.search('page')
        self.assertOne(us)
        self.assertEq('epage', us.first.name)

        us = users.search('lawrence')
        self.assertOne(us)
        self.assertEq('glawrence', us.first.name)

        us = users.search('arapacia')
        self.assertTwo(us)
        us.sort('name')
        self.assertEq('epage',     us.first.name)
        self.assertEq('glawrence', us.second.name)

    def it_calls__str__(self):
        us = users()

        p = person()
        p.firstname   =  'Gary'
        p.lastname    =  'Francione'
        p.email       =  'glawrence@fakemail.com'
        p.phone       =  '555 555 5555'

        u = user()
        u.service   =  'carapacian'
        u.name      =  'glawrence'
        u.password  =  'secret'
        u.person    =  p

        us += u

        u = user()
        u.service   =  'carapacian'
        u.name      =  'epage'
        u.password  =  'secret'

        us += u

        expect = """+------------------------------------------------------------------+
| ix | id | service    | name      | person.name    | person.phone |
|------------------------------------------------------------------|
| 0  |    | carapacian | glawrence | Gary Francione | 555 555 5555 |
|------------------------------------------------------------------|
| 1  |    | carapacian | epage     |                |              |
+------------------------------------------------------------------+
"""

        self.assertEq(expect, str(us))

    def it_calls_sorted(self):
        us = users()

        p = person()
        p.firstname   =  'Gary'
        p.lastname    =  'Francione'
        p.email       =  'glawrence@fakemail.com'
        p.phone       =  '555 555 5555'

        u = user()
        u.service   =  'carapacian'
        u.name      =  'glawrence'
        u.password  =  'secret'
        u.person    =  p

        us += u

        u = user()
        u.service   =  'carapacian'
        u.name      =  'epage'
        u.password  =  'secret'

        us += u

        us1 = us.sorted('name')
        self.assertEq('epage', us1.first.name)
        self.assertEq('glawrence', us1.second.name)


class test_user(tester):
    def __init__(self):
        super().__init__()
        articlerevisions()   .RECREATE()
        blogpostrevisions()  .RECREATE()
        blogs()              .RECREATE()
        persons()            .RECREATE()
        roles_mm_objects()   .RECREATE()
        roles()              .RECREATE()
        users()              .RECREATE()

        # Create a blog
        bl = blog()
        bl.slug = 'carapacian-tech-blog'
        bl.description = 'Carapacian Tech Blog'
        bl.save()
        self.blog = bl

        rs = roles()
        for name in (
                        'carapacian-blog-editor', 
                        'carapacian-techblog-editor', 
                        'vegout-blog-editor',
                    ):
            rs += role()
            rs.last.name = name

        rs.save()

    def it_calls_articles(self):
        # Create user
        u = user()
        u.name      =  'jjett'
        u.service   =  'carapacian'
        u.password  =  'secret'

        # Should have zero articles
        self.assertZero(u.articles)

        # Create an article and a blogpost
        art = article()
        art.body   =  test_article.Smallpostbody
        art.title  =  'a' + test_article.Smallposttitle  +  str(uuid4())

        bp = blogpost()
        bp.blog    =  self.blog
        bp.body    =  test_article.Smallpostbody
        bp.title   =  'b' + test_article.Smallposttitle  +  str(uuid4())

        # Add the article and blogpost to the user's collection of articles.
        u.articles += art
        u.articles += bp

        # Test that the two articles are there before saving
        self.assertTwo(u.articles)
        self.assertEq(art.title, u.articles.first.title)
        self.assertEq(bp.title,  u.articles.second.title)

        # Save, reload and test
        u.save()
        u = user(u.id)
        u.articles.sort('title')

        self.assertTwo(u.articles)
        self.assertEq(art.title, u.articles.first.title)
        self.assertEq(bp.title,  u.articles.second.title)

        # Change the articles
        arttitle = str(uuid4())
        bptitle  = str(uuid4())
        u.articles.first.title = arttitle
        u.articles.second.title = bptitle

        # Test, save user, reload and test again
        self.assertTwo(u.articles)
        self.assertEq(arttitle, u.articles.first.title)
        self.assertEq(bptitle,  u.articles.second.title)

        arts = u.articles 
        u.save()
        u = user(u.id)

        u.articles.sort('title')
        arts.sort('title')

        self.assertTwo(u.articles)
        self.assertEq(arts.first.title,   u.articles.first.title)
        self.assertEq(arts.second.title,  u.articles.second.title)

        # Add article, test, save, reload, test
        art1 = article()
        art1.body   =  test_article.Smallpostbody
        art1.title  =  'c' + test_article.Smallposttitle  +  uuid4().hex
        arts += art1

        u.articles += art1

        self.assertThree(u.articles)
        self.assertEq(arts.first.title,   u.articles.first.title)
        self.assertEq(arts.second.title,  u.articles.second.title)
        self.assertEq(arts.third.title,   u.articles.third.title)

        u.save()
        u = user(u.id)

        u.articles.sort('title')
        arts.sort('title')
        self.assertThree(u.articles)
        self.assertEq(arts.first.title,   u.articles.first.title)
        self.assertEq(arts.second.title,  u.articles.second.title)
        self.assertEq(arts.third.title,   u.articles.third.title)

        # Remove article
        # TODO
        return
        u.articles.shift()
        self.assertTwo(u.articles)
        self.assertEq(arts.second.title,  u.articles.first.title)
        self.assertEq(arts.third.title,   u.articles.second.title)

        u.save()
        u = user(u.id)
        u.articles.sort('title')

        self.assertTwo(u.articles)
        self.assertEq(arts.second.title,  u.articles.first.title)
        self.assertEq(arts.third.title,   u.articles.second.title)
        

    def it_gets_articles_brokenrules(self):
        # TODO
        pass


    def it_calls__str__(self):
        p = person()
        p.firstname   =  'Gary'
        p.middlename  =  'Lawrence'
        p.lastname    =  'Francione'
        p.email       =  'gfrancione@mail.com'
        p.phone       =  '5' *  10

        u = user()
        u.service   =  'carapacian'
        u.name      =  'glawrence'

        # Test without person
        expect = """Name:     glawrence
Service:  carapacian
"""
        self.assertEq(expect, str(u))

        # Test with person
        u.person = p # Add person

        expect = """Name:     glawrence
Service:  carapacian
Person:   Gary Francione
"""

        self.assertEq(expect, str(u))


    def it_calls_save(self):
        u = user()
        u.service   =  str(uuid4())
        u.name      =  'glawrence'
        u.password  =  'secret'
        u.save()

    def it_calls_delete(self):
        u = user()
        u.service   =  str(uuid4())
        u.name      =  str(uuid4())
        u.password  =  str(uuid4())
        u.save()

        u = user(u.id)

        cnt = u.delete()
        self.assertEq(1, cnt)

        cnt = u.delete()
        self.assertEq(0, cnt)

        try:
            u = user(u.id)
        except Exception:
            pass
        else:
            self.assertFail('No exception thrown')

    def it_loads(self):
        u = user()
        u.service = str(uuid4())
        u.name = 'glawrence'
        u.password = 'secret'
        u.save()

        u1 = user(u.id)

        for prop in ('service', 'name', 'hash', 'salt'):
            self.assertEq(getattr(u, prop), getattr(u1, prop))

        self.assertNone(u1.password)

    def it_breaks_service_rule(self):
        u = user()
        u.service = str(uuid4())
        u.name = 'glawrence'
        u.password = 'secret'
        self.assertZero(u.brokenrules)

        for v in (None, '', ' ' * 100):
            u.service = v
            self.assertCount(1, u.brokenrules)
            self.assertTrue(u.brokenrules.contains('service', 'full'))

        u.service = 'X' * 255
        self.assertZero(u.brokenrules)

        u.service = 'X' * 256
        self.assertCount(1, u.brokenrules)
        self.assertTrue(u.brokenrules.contains('service', 'fits'))

    def it_breaks_name_rule(self):
        u = user()
        u.service = str(uuid4())
        u.name = 'glawrence'
        u.password = 'secret'
        self.assertZero(u.brokenrules)

        for v in (None, '', ' ' * 100):
            u.name = v
            self.assertCount(1, u.brokenrules)
            self.assertTrue(u.brokenrules.contains('name', 'full'))

        u.name = 'X' * 255
        self.assertZero(u.brokenrules)

        u.name = 'X' * 256
        self.assertCount(1, u.brokenrules)
        self.assertTrue(u.brokenrules.contains('name', 'fits'))

    def it_breaks_name_and_service_uniqueness_rule(self):
        u = user()
        u.service = str(uuid4())
        u.name = str(uuid4())
        u.password = str(uuid4())
        u.save()

        u1 = user()
        u1.service = u.service
        u1.name = u.name
        u1.password = str(uuid4())
        self.assertTrue(u1.brokenrules.contains('name', 'unique'))

        # Fix
        u1.service = str(uuid4())
        self.assertZero(u1.brokenrules)

        # Break again
        u1.service = u.service
        self.assertTrue(u1.brokenrules.contains('name', 'unique'))

        # Fix another way
        u1.name = str(uuid4())
        self.assertZero(u1.brokenrules)

    def it_validates_password(self):
        pwd = str(uuid4())

        u = user()
        u.service = str(uuid4())
        u.name = 'glawrence'
        u.password = pwd

        self.assertTrue(u.ispassword(pwd))
        self.assertFalse(u.ispassword(str(uuid4())))

        u.save()

        self.assertTrue(u.ispassword(pwd))
        self.assertFalse(u.ispassword(str(uuid4())))

    def it_call_load(self):
        u = user()
        u.service = str(uuid4())
        u.name = str(uuid4())
        u.password = str(uuid4())
        u.save()

        u1 = user.load(u.name, u.service)
        for prop in ('service', 'name', 'hash', 'salt'):
            self.assertEq(getattr(u, prop), getattr(u1, prop))

        u = user.load(str(uuid4()), str(uuid4()))
        self.assertNone(u)

    def it_calls_name(self):
        u = user()
        name = str(uuid4())
        u.name = name
        u.service = str(uuid4())
        u.password = str(uuid4())
        self.assertEq(name, u.name)
        u.save()

        u = user(u.id)
        self.assertEq(name, u.name)

        # Change name
        name = str(uuid4())
        u.name = name

        u.save()

        u = user(u.id)
        self.assertEq(name, u.name)

    def it_calls_service(self):
        u = user()
        name = str(uuid4())
        u.name = name
        service = str(uuid4())
        u.service = service
        u.password = str(uuid4())
        self.assertEq(name, u.name)
        u.save()

        u = user(u.id)
        self.assertEq(service, u.service)

        # Change service
        service = str(uuid4())
        u.service = service

        u.save()

        u = user(u.id)
        self.assertEq(service, u.service)

    def it_calls_password(self):
        u = user()
        name = str(uuid4())
        u.name = name
        service = str(uuid4())
        u.service = service
        pwd = 'password'
        u.password = pwd
        self.assertEq(name, u.name)
        u.save()

        u = user(u.id)
        self.assertTrue(u.ispassword(pwd))

        # Change password
        pwd = 'password0'
        u.password = pwd

        u.save()

        u = user(u.id)
        self.assertTrue(u.ispassword(pwd))

    def it_calls_person(self):
        # Create a person
        p = person()
        p.firstname   =  'Gary'
        p.middlename  =  'Lawrence'
        p.lastname    =  'Francione'
        p.email       =  'gfrancione@mail.com'
        p.phone       =  '5' *  10

        # Create a new user
        u = user()
        u.name      =  str(uuid4())
        u.service   =  str(uuid4())
        u.password  =  str(uuid4())

        # Associate the user with the person
        u.person = p

        # Save user, reload and test association
        u.save()
        u = user(u.id)
        self.assertEq(p.id,          u.person.id)
        self.assertEq(p.firstname,   u.person.firstname)
        self.assertEq(p.middlename,  u.person.middlename)
        self.assertEq(p.lastname,    u.person.lastname)
        self.assertEq(p.email,       u.person.email)
        self.assertEq(p.phone,       u.person.phone)

        # Alter person, save user, reload, test
        phone = '6' * 10
        u.person.phone = phone
        u.save()
        u = user(u.id)
        self.assertEq(p.id,          u.person.id)
        self.assertEq(p.firstname,   u.person.firstname)
        self.assertEq(p.middlename,  u.person.middlename)
        self.assertEq(p.lastname,    u.person.lastname)
        self.assertEq(p.email,       u.person.email)
        self.assertEq(phone,         u.person.phone)

        # Create a second person
        p = person()
        p.firstname   =  'James'
        p.middlename  =  '<none>'
        p.lastname    =  'Aspey'
        p.email       =  'jaspey@mail.com'
        p.phone       =  '5' *  10

        # Associate the second person with the user
        u.person = p

        # Save user, reload, test that new person was associated
        u.save()
        u = user(u.id)

        self.assertEq(p.id,          u.person.id)
        self.assertEq(p.firstname,   u.person.firstname)
        self.assertEq(p.middlename,  u.person.middlename)
        self.assertEq(p.lastname,    u.person.lastname)
        self.assertEq(p.email,       u.person.email)
        self.assertEq(p.phone,       u.person.phone)

    def it_captures_persons_brokenrules(self):
        p = person()
        p.firstname   =  'Emily'
        p.middlename  =  'Moran'
        p.lastname    =  'Barwick'
        p.email       =  'ebarwick@mail.com'
        p.phone       =  '5' * 256 # broken rule

        u = user()
        u.name      =  str(uuid4())
        u.service   =  str(uuid4())
        u.password  =  str(uuid4())
        u.person = p

        self.assertOne(u.brokenrules)
        self.assertBroken(u, 'phone', 'fits')

    def it_captures_role_mm_object_brokenrules(self):
        u = user()
        u.name      =  str(uuid4())
        u.service   =  str(uuid4())
        u.password  =  str(uuid4())

        rs = roles().ALL()

        u.roles += rs.first

        u.roles.first._id = None # break rule

        try:
            u.save()
        except BrokenRulesError as ex:
            self.assertOne(ex.object.brokenrules)
            self.assertBroken(ex.object, 'roleid', 'full')
        except:
            self.assertFail('The wrong exception type was raised')
        else:
            self.assertFail('No exception was raised')

    def it_persists_roles(self):
        rs = roles().ALL()
        rs.sort(key=lambda x: x.name)

        # Create user 
        u = user()
        u.service = str(uuid4())
        u.name = str(uuid4())
        u.password = str(uuid4())

        # Add roles
        for r in 'carapacian-blog-editor', 'carapacian-techblog-editor':
            u.roles += rs[r]

        # Save user
        u.save()

        # Reload user and assert roles were saved and reloaded
        u = user(u.id)
        u.roles.sort(key=lambda x: x.name)

        self.assertTwo(u.roles)
        for i, r in enumerate(u.roles):
            self.assertEq(rs[i].name, r.name)

        # Add an additional roles, save, load and test
        u.roles += rs['vegout-blog-editor']

        u.save()

        u = user(u.id)
        u.roles.sort(key=lambda x: x.name)
        self.assertThree(u.roles)
        for i, r in enumerate(u.roles):
            self.assertEq(rs[i].name, r.name)

        # Remove a roles, one-by-one, reload and test
        for i in range(u.roles.count, 0, -1):
            # Remove
            u.roles.pop()

            # Test
            for j, r in enumerate(u.roles):
                self.assertEq(rs[j].name, r.name)
            self.assertCount(i - 1, u.roles)

            # Save and reload
            u.save()
            u = user(u.id)

            # Test
            u.roles.sort('name')
            self.assertCount(i - 1, u.roles)
            for j, r in enumerate(u.roles):
                self.assertEq(rs[j].name, r.name)

    def it_calls_isassigned(self):
        r = role()
        r.name = 'good-eats-blog-editor'

        u = user()
        u.service   =  str(uuid4())
        u.name      =  str(uuid4())
        u.password  =  str(uuid4())

        u.roles += r

        self.assertTrue(u.isassigned(r))
        self.assertFalse(u.isassigned(role('not-assigned')))

        for t in '', None, 1, True:
            try:
                u.isassigned(t)
            except TypeError:
                pass
            except Exception:
                self.assertFail('Wrong exception type')
            else:
                self.assertFail('No exception thrown')

    def it_prevents_modifications_of_roles(self):
        u = user()
        rs = roles().ALL()
        u.roles += rs['vegout-blog-editor']

        try:
            u.roles.first.name = 'shouldnt-be-doing-this'
        except NotImplementedError:
            pass
        except Exception:
            self.assertFail('Wrong exception type')
        else:
            self.assertFail('No exception was thrown')

        # TODO Capabilities shouldn't be modifiable either. Implement the below.
        if False:
            try:
                u.roles.first.capabilities += 'can-derp'
            except NotImplementedError:
                pass
            except Exception as ex:
                self.assertFail('Wrong exception type')
            else:
                self.assertFail('No exception was thrown')

    def it_creates_an_article(self):
        # TODO
        return
        u = user()
        u.name      =  'edegeneres'
        u.service   =  'carapacian'
        u.password  =  'secret'

        art = article()
        
        u.articles += art

        self.assertEq(art.author.name, u.name)
        self.assertOne(u.articles)

class test_role(tester):
    def __init__(self):
        super().__init__()
        users().RECREATE()
        roles().RECREATE()

    def it_creates_valid(self):
        r = role()
        r.name = uuid4()

        self.assertZero(r.brokenrules)

    def it_creates(self):
        r = role()
        r.name          =   str(uuid4())
        r.capabilities  +=  str(uuid4())
        r.capabilities  +=  str(uuid4())
        r.save()

    def it_deletes(self):
        r = role()
        r.name          =   str(uuid4())
        r.capabilities  +=  str(uuid4())
        r.capabilities  +=  str(uuid4())
        r.save()

        cnt = r.delete()

        self.assertEq(1, cnt)

        cnt = r.delete()
        self.assertEq(0, cnt)

        try:
            r = person(r.id)
        except Exception:
            pass
        else:
            self.assertFail('No exception thrown')

    def it_loads(self):
        r = role()
        r.name = str(uuid4())
        r.save()

        r1 = role(r.id)
        for p in 'id', 'name':
            self.assertEq(getattr(r, p), getattr(r1, p), 'Property: ' + p)

        self.assertZero(r.capabilities)

        r = role()
        r.name = str(uuid4())
        r.capabilities += str(uuid4())
        r.capabilities += str(uuid4())
        r.save()

        r1 = role(r.id)

        self.assertCount(2, r1.capabilities)

        for cap in r.capabilities:
            found = False
            for cap1 in r1.capabilities:
                if cap.name == cap1.name:
                    found = True
            self.assertTrue(found)

    def it_enforces_uniqueness_constraint_on_name(self):
        r = role()
        name = str(uuid4())
        r.name = name
        r.save()

        r = role()
        r.name = name
        self.assertBroken(r, 'name', 'unique')

        try:
            r._insert()
        except MySQLdb.IntegrityError as ex:
            self.assertTrue(ex.args[0] == DUP_ENTRY)
        except Exception:
            self.assertFail('Wrong exception')
        else:
            self.assertFail("Didn't raise an exception")

    def it_calls_name(self):
        r = role()
        name = str(uuid4())
        r.name = name

        self.assertEq(name, r.name)
        r.save()
        self.assertEq(name, r.name)

        name = str(uuid4())
        r.name = name
        self.assertEq(name, r.name)
        r.save()

        r = role(r.id)
        self.assertEq(name, r.name)

    def it_calls_capabilities(self):
        r = role()
        self.assertZero(r.capabilities)
        self.assertType(capabilities, r.capabilities)
        r.save()

        r = role(r.id)
        self.assertZero(r.capabilities)
        self.assertType(capabilities, r.capabilities)

        r.capabilities += str(uuid4())
        r.capabilities += str(uuid4())
        self.assertCount(2, r.capabilities)
        r.save()
        self.assertCount(2, r.capabilities)

        r1 = role(r.id)
        self.assertCount(2, r1.capabilities)
        self.assertType(capabilities, r1.capabilities)
        for cap in r.capabilities:
            found = False
            for cap1 in r1.capabilities:
                if cap.name == cap1.name:
                    found = True
            self.assertTrue(found)

        r = r1

        r.capabilities += str(uuid4())
        self.assertCount(3, r.capabilities)
        r.save()
        self.assertCount(3, r.capabilities)

        r1 = role(r.id)
        self.assertCount(3, r1.capabilities)
        for cap in r.capabilities:
            found = False
            for cap1 in r1.capabilities:
                if cap.name == cap1.name:
                    found = True
            self.assertTrue(found)

        r = r1
        r.capabilities -= r.capabilities.first
        r.save()

        r1 = role(r.id)

        self.assertCount(2, r1.capabilities)
        for cap in r.capabilities:
            found = False
            for cap1 in r1.capabilities:
                if cap.name == cap1.name:
                    found = True
            self.assertTrue(found)

class test_capabilities(tester):
    
    def it_adds(self):
        # Add zero
        caps = capabilities()

        self.assertZero(caps)
        
        # Add one
        caps += 'edit_posts'

        self.assertOne(caps)
        self.assertEq(caps.first.name, 'edit_posts')

        # Add the same one
        caps += 'edit_posts'

        self.assertOne(caps)
        self.assertEq(caps.first.name, 'edit_posts')

        # Add a second one
        caps += 'add_posts'

        self.assertTwo(caps)
        self.assertEq(caps.first.name, 'edit_posts')
        self.assertEq(caps.second.name, 'add_posts')

    def it_removes(self):
        caps = capabilities()

        # Remove non existing capability
        caps -= 'edit_posts'

        self.assertZero(caps)
        
        # Add one
        caps += 'edit_posts'

        # Remove existing capability
        caps -= 'edit_posts'

        self.assertZero(caps)

        caps += 'edit_posts'
        caps += 'add_posts'

        # Remove one of two
        caps -= 'edit_posts'

        self.assertOne(caps)
        self.assertEq(caps.first.name, 'add_posts')

    def it_call__str__(self):
        caps = capabilities()
        self.assertEmpty(str(caps))

        caps += 'edit_posts'
        self.assertEq('edit_posts', str(caps))

        caps += 'add_posts'
        self.assertEq('edit_posts add_posts', str(caps))

class test_capability(tester):
    
    def it_breaks_name_rule(self):
        cap = capability('')
        self.assertOne(cap.brokenrules)
        self.assertBroken(cap, 'name', 'full')

        cap = capability(None)
        self.assertCount(1, cap.brokenrules)
        self.assertBroken(cap, 'name', 'full')

        cap = capability(1)
        self.assertOne(cap.brokenrules)
        self.assertBroken(cap, 'name', 'valid')

        cap = capability('can edit')
        self.assertOne(cap.brokenrules)
        self.assertBroken(cap, 'name', 'valid')

        cap = capability(' can-edit ')
        self.assertZero(cap.brokenrules)

class test_tags(tester):

    def it_calls_sorted(self):
        ts = tags()
        for s in 'alpha', 'beta', 'gamma':
            ts += tag()
            ts.last.name = s

        ts = ts.sorted('name', True)
        self.assertEq('gamma',  ts.first.name)
        self.assertEq('beta',   ts.second.name)
        self.assertEq('alpha',  ts.third.name)

        ts = ts.sorted('name')
        self.assertEq('alpha',  ts.first.name)
        self.assertEq('beta',   ts.second.name)
        self.assertEq('gamma',  ts.third.name)

    def it_calls_sort(self):
        ts = tags()
        for s in 'alpha', 'beta', 'gamma':
            ts += tag()
            ts.last.name = s

        ts.sort('name', True)
        self.assertEq('gamma',  ts.first.name)
        self.assertEq('beta',   ts.second.name)
        self.assertEq('alpha',  ts.third.name)

        ts.sort('name')
        self.assertEq('alpha',  ts.first.name)
        self.assertEq('beta',   ts.second.name)
        self.assertEq('gamma',  ts.third.name)

    def it_calls__str__(self):
        ts = tags()
        for s in 'alpha', 'beta', 'gamma':
            ts += tag()
            ts.last.name = s

        expect = """+-----------------+
| ix | id | name  |
|-----------------|
| 0  |    | alpha |
|-----------------|
| 1  |    | beta  |
|-----------------|
| 2  |    | gamma |
+-----------------+
"""
        self.assertEq(expect, str(ts))

class test_tag(tester):
    def __init__(self):
        super().__init__()
        tags().RECREATE()
    
    def it_saves(self):
        t = tag()
        t.name = 'food'
        t.save()
        t = tag(t.id)

        self.assertEq('food', t.name)

    def it_calls_name(self):
        t = tag()
        t.name = 'vegetarian'

        self.assertEq('vegetarian', t.name)

        t.save()
        t = tag(t.id)

        self.assertEq('vegetarian', t.name)

        t.name = 'vegan'
        t.save()

        t = tag(t.id)

        self.assertEq('vegan', t.name)

    def it_breaks_name_uniqueness_null(self):
        t = tag()
        t.name = 'snowflake'
        t.save()

        # Test unique brokenrule
        t = tag()
        t.name = 'snowflake'
        self.assertOne(t.brokenrules)
        self.assertBroken(t, 'name', 'unique')

        # Test MySQL UNIQUE contraint
        try:
            t._insert()
        except MySQLdb.IntegrityError as ex:
            self.assertTrue(ex.args[0] == DUP_ENTRY)
        except Exception:
            self.assertFail('Wrong exception')
        else:
            self.assertFail("Didn't raise IntegrityError")

        t.name = 'snow flake'
        self.assertOne(t.brokenrules)
        self.assertBroken(t, 'name', 'valid')

    def it_breaks_name_rule(self):
        t = tag()
        self.assertOne(t.brokenrules)
        self.assertBroken(t, 'name', 'full')

    def it_calls__str__(self):
        t = tag()
        self.assertEq('', str(t))

        t.name = 'vegan'
        self.assertEq('#vegan', str(t))

    def it_calls_delete(self):
        t = tag()
        t.name = 'technology'
        t.save()
        t.delete()

        try:
            t = tag(t.id)
        except:
            pass
        else:
            self.assertFail('No exception')

    def it_aggregates_brokenrules_from_articles(self):
        # TODO
        pass

    def it_calls_articles(self):
        t = tag()
        t.name = 'recipe'

        # Ensure we start out with zero
        self.assertZero(t.articles)
        
        art = article()
        art.body  =  test_article.Smallpostbody
        title     =  test_article.Smallposttitle  +  uuid4().hex
        art.title =  title

        # Add and remove an article without saving. Test the count
        t.articles += art
        self.assertOne(t.articles)

        t.articles -= art
        self.assertZero(t.articles)

        t.articles += art
        self.assertOne(t.articles)

        # Save tag, test, reload and test
        t.save()
        self.assertOne(t.articles)
        self.assertEq(title, t.articles.first.title)

        t = tag(t.id)
        self.assertOne(t.articles)
        self.assertEq(title, t.articles.first.title)

        # Update an article, test, save, test, reload and test
        title = uuid4().hex
        t.articles.first.title = title
        self.assertOne(t.articles)
        self.assertEq(title, t.articles.first.title)

        t.save()
        self.assertOne(t.articles)
        self.assertEq(title, t.articles.first.title)

        t = tag(t.id)
        self.assertOne(t.articles)
        self.assertEq(title, t.articles.first.title)

        arts = articles()
        arts += t.articles.first

        arts += article()
        arts.last.body   =  test_article.Smallpostbody
        arts.last.title  =  test_article.Smallposttitle  +  uuid4().hex

        t.articles += arts.last
        t.articles.sort('title')
        arts.sort('title')

        self.assertTwo(t.articles)
        self.assertEq(arts.first.title, t.articles.first.title)
        self.assertEq(arts.second.title, t.articles.second.title)

        t.save()
        self.assertTwo(t.articles)
        self.assertEq(arts.first.title, t.articles.first.title)
        self.assertEq(arts.second.title, t.articles.second.title)

        t = tag(t.id)
        t.articles.sort('title')
        self.assertTwo(t.articles)
        self.assertEq(arts.first.title, t.articles.first.title)
        self.assertEq(arts.second.title, t.articles.second.title)

def la2gr(chars):
    map = {
        'a': b'\u03b1', 'b': b'\u03b2', 'c': b'\u03ba', 'd': b'\u03b4', 'e': b'\u03b5',
        'f': b'\u03c6', 'g': b'\u03b3', 'h': b'\u03b7', 'i': b'\u03b9', 'j': b'\u03c3',
        'k': b'\u03ba', 'l': b'\u03bb', 'm': b'\u03b1', 'n': b'\u03bc', 'o': b'\u03c0',
        'p': b'\u03b1', 'q': b'\u03b8', 'r': b'\u03c1', 's': b'\u03c3', 't': b'\u03c4',
        'u': b'\u03c5', 'v': b'\u03b2', 'w': b'\u03c9', 'x': b'\u03be', 'y': b'\u03c5',
        'z': b'\u03b6',
    }

    r = ''
    for c in chars.lower():
        try:
            r += map[c].decode('unicode_escape')
        except:
            r += ' '
    return r
        
"""
Test end here. Below are here documents used for testing.
"""

wxr = """<?xml version="1.0" encoding="UTF-8"?>
<!-- This is a WordPress eXtended RSS file generated by WordPress as an export of your site. -->
<!-- It contains information about your site's posts, pages, comments, categories, and other content. -->
<!-- You may use this file to transfer that content from one site to another. -->
<!-- This file is not intended to serve as a complete backup of your site. -->
<!-- To import this information into a WordPress site follow these steps: -->
<!-- 1. Log in to that site as an administrator. -->
<!-- 2. Go to Tools: Import in the WordPress admin panel. -->
<!-- 3. Install the "WordPress" importer from the list. -->
<!-- 4. Activate & Run Importer. -->
<!-- 5. Upload this file using the form provided on that page. -->
<!-- 6. You will first be asked to map the authors in this export file to users -->
<!--    on the site. For each author, you may choose to map to an -->
<!--    existing user on the site or to create a new user. -->
<!-- 7. WordPress will then import each of the posts, pages, comments, categories, etc. -->
<!--    contained in this file into your site. -->
<!-- generator="WordPress/4.6.1" created="2018-07-15 13:33" -->
<rss xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:wfw="http://wellformedweb.org/CommentAPI/" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:wp="http://wordpress.org/export/1.2/" version="2.0">
  <channel>
    <title>Jesse Hogan</title>
    <link>http://jesse-hogan.com</link>
    <description>Programmer</description>
    <pubDate>Sun, 15 Jul 2018 13:33:02 +0000</pubDate>
    <language>en-US</language>
    <wp:wxr_version>1.2</wp:wxr_version>
    <wp:base_site_url>http://jesse-hogan.com</wp:base_site_url>
    <wp:base_blog_url>http://jesse-hogan.com</wp:base_blog_url>
    <wp:author>
      <wp:author_id>1</wp:author_id>
      <wp:author_login><![CDATA[jhogan]]></wp:author_login>
      <wp:author_email><![CDATA[jhogan@fakemail.com]]></wp:author_email>
      <wp:author_display_name><![CDATA[Jesse Hogan]]></wp:author_display_name>
      <wp:author_first_name><![CDATA[Jesse]]></wp:author_first_name>
      <wp:author_last_name><![CDATA[Hogan]]></wp:author_last_name>
    </wp:author>
    <wp:author>
      <wp:author_id>2</wp:author_id>
      <wp:author_login><![CDATA[dhogan]]></wp:author_login>
      <wp:author_email><![CDATA[dhogan@fakemail.com]]></wp:author_email>
      <wp:author_display_name><![CDATA[Delia Hogan]]></wp:author_display_name>
      <wp:author_first_name><![CDATA[Delia]]></wp:author_first_name>
      <wp:author_last_name><![CDATA[Hogan]]></wp:author_last_name>
    </wp:author>
    <wp:category>
      <wp:term_id>1</wp:term_id>
      <wp:category_nicename><![CDATA[uncategorized]]></wp:category_nicename>
      <wp:category_parent><![CDATA[]]></wp:category_parent>
      <wp:cat_name><![CDATA[Uncategorized]]></wp:cat_name>
    </wp:category>
    <wp:tag>
      <wp:term_id>33</wp:term_id>
      <wp:tag_slug><![CDATA[ajax]]></wp:tag_slug>
      <wp:tag_name><![CDATA[ajax]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>15</wp:term_id>
      <wp:tag_slug><![CDATA[angular]]></wp:tag_slug>
      <wp:tag_name><![CDATA[angular]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>25</wp:term_id>
      <wp:tag_slug><![CDATA[apt]]></wp:tag_slug>
      <wp:tag_name><![CDATA[apt]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>19</wp:term_id>
      <wp:tag_slug><![CDATA[azure]]></wp:tag_slug>
      <wp:tag_name><![CDATA[azure]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>43</wp:term_id>
      <wp:tag_slug><![CDATA[brokenrules]]></wp:tag_slug>
      <wp:tag_name><![CDATA[brokenrules]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>46</wp:term_id>
      <wp:tag_slug><![CDATA[chromebook]]></wp:tag_slug>
      <wp:tag_name><![CDATA[chromebook]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>9</wp:term_id>
      <wp:tag_slug><![CDATA[coffee]]></wp:tag_slug>
      <wp:tag_name><![CDATA[coffee]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>11</wp:term_id>
      <wp:tag_slug><![CDATA[collection-class]]></wp:tag_slug>
      <wp:tag_name><![CDATA[collection class]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>4</wp:term_id>
      <wp:tag_slug><![CDATA[commonpy]]></wp:tag_slug>
      <wp:tag_name><![CDATA[commonpy]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>5</wp:term_id>
      <wp:tag_slug><![CDATA[debugging]]></wp:tag_slug>
      <wp:tag_name><![CDATA[debugging]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>44</wp:term_id>
      <wp:tag_slug><![CDATA[design-patterns]]></wp:tag_slug>
      <wp:tag_name><![CDATA[design patterns]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>14</wp:term_id>
      <wp:tag_slug><![CDATA[dingo]]></wp:tag_slug>
      <wp:tag_name><![CDATA[dingo]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>26</wp:term_id>
      <wp:tag_slug><![CDATA[dns]]></wp:tag_slug>
      <wp:tag_name><![CDATA[dns]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>22</wp:term_id>
      <wp:tag_slug><![CDATA[dpkg]]></wp:tag_slug>
      <wp:tag_name><![CDATA[dpkg]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>10</wp:term_id>
      <wp:tag_slug><![CDATA[entities]]></wp:tag_slug>
      <wp:tag_name><![CDATA[entities]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>29</wp:term_id>
      <wp:tag_slug><![CDATA[epiphany]]></wp:tag_slug>
      <wp:tag_name><![CDATA[epiphany]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>30</wp:term_id>
      <wp:tag_slug><![CDATA[epiphany-py]]></wp:tag_slug>
      <wp:tag_name><![CDATA[epiphany-py]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>7</wp:term_id>
      <wp:tag_slug><![CDATA[git]]></wp:tag_slug>
      <wp:tag_name><![CDATA[git]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>8</wp:term_id>
      <wp:tag_slug><![CDATA[git-commit]]></wp:tag_slug>
      <wp:tag_name><![CDATA[git commit]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>48</wp:term_id>
      <wp:tag_slug><![CDATA[git-git-commit]]></wp:tag_slug>
      <wp:tag_name><![CDATA[git git-commit]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>6</wp:term_id>
      <wp:tag_slug><![CDATA[git-instrumentation]]></wp:tag_slug>
      <wp:tag_name><![CDATA[git instrumentation]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>40</wp:term_id>
      <wp:tag_slug><![CDATA[html]]></wp:tag_slug>
      <wp:tag_name><![CDATA[html]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>17</wp:term_id>
      <wp:tag_slug><![CDATA[http-304]]></wp:tag_slug>
      <wp:tag_name><![CDATA[http 304]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>16</wp:term_id>
      <wp:tag_slug><![CDATA[javascript]]></wp:tag_slug>
      <wp:tag_name><![CDATA[javascript]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>34</wp:term_id>
      <wp:tag_slug><![CDATA[jquery]]></wp:tag_slug>
      <wp:tag_name><![CDATA[jquery]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>31</wp:term_id>
      <wp:tag_slug><![CDATA[json]]></wp:tag_slug>
      <wp:tag_name><![CDATA[json]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>41</wp:term_id>
      <wp:tag_slug><![CDATA[lambda]]></wp:tag_slug>
      <wp:tag_name><![CDATA[lambda]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>47</wp:term_id>
      <wp:tag_slug><![CDATA[laptop]]></wp:tag_slug>
      <wp:tag_name><![CDATA[laptop]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>12</wp:term_id>
      <wp:tag_slug><![CDATA[laravel]]></wp:tag_slug>
      <wp:tag_name><![CDATA[laravel]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>20</wp:term_id>
      <wp:tag_slug><![CDATA[linux]]></wp:tag_slug>
      <wp:tag_name><![CDATA[linux]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>24</wp:term_id>
      <wp:tag_slug><![CDATA[livecd]]></wp:tag_slug>
      <wp:tag_name><![CDATA[livecd]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>37</wp:term_id>
      <wp:tag_slug><![CDATA[mount]]></wp:tag_slug>
      <wp:tag_name><![CDATA[mount]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>28</wp:term_id>
      <wp:tag_slug><![CDATA[pantheon]]></wp:tag_slug>
      <wp:tag_name><![CDATA[pantheon]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>13</wp:term_id>
      <wp:tag_slug><![CDATA[php]]></wp:tag_slug>
      <wp:tag_name><![CDATA[php]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>3</wp:term_id>
      <wp:tag_slug><![CDATA[python]]></wp:tag_slug>
      <wp:tag_name><![CDATA[python]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>18</wp:term_id>
      <wp:tag_slug><![CDATA[rdp]]></wp:tag_slug>
      <wp:tag_name><![CDATA[rdp]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>38</wp:term_id>
      <wp:tag_slug><![CDATA[sftp]]></wp:tag_slug>
      <wp:tag_name><![CDATA[sftp]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>39</wp:term_id>
      <wp:tag_slug><![CDATA[sshfs]]></wp:tag_slug>
      <wp:tag_name><![CDATA[sshfs]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>36</wp:term_id>
      <wp:tag_slug><![CDATA[terminal]]></wp:tag_slug>
      <wp:tag_name><![CDATA[terminal]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>21</wp:term_id>
      <wp:tag_slug><![CDATA[ubuntu]]></wp:tag_slug>
      <wp:tag_name><![CDATA[ubuntu]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>45</wp:term_id>
      <wp:tag_slug><![CDATA[validation]]></wp:tag_slug>
      <wp:tag_name><![CDATA[validation]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>32</wp:term_id>
      <wp:tag_slug><![CDATA[vim]]></wp:tag_slug>
      <wp:tag_name><![CDATA[vim]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>23</wp:term_id>
      <wp:tag_slug><![CDATA[wicd-curses]]></wp:tag_slug>
      <wp:tag_name><![CDATA[wicd-curses]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>27</wp:term_id>
      <wp:tag_slug><![CDATA[wordpress]]></wp:tag_slug>
      <wp:tag_name><![CDATA[wordpress]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>35</wp:term_id>
      <wp:tag_slug><![CDATA[xhr]]></wp:tag_slug>
      <wp:tag_name><![CDATA[xhr]]></wp:tag_name>
    </wp:tag>
    <wp:tag>
      <wp:term_id>42</wp:term_id>
      <wp:tag_slug><![CDATA[zachary]]></wp:tag_slug>
      <wp:tag_name><![CDATA[zachary]]></wp:tag_name>
    </wp:tag>
    <wp:term>
      <wp:term_id><![CDATA[33]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[ajax]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[ajax]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[15]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[angular]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[angular]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[25]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[apt]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[apt]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[19]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[azure]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[azure]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[43]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[brokenrules]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[brokenrules]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[46]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[chromebook]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[chromebook]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[9]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[coffee]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[coffee]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[11]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[collection-class]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[collection class]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[4]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[commonpy]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[commonpy]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[5]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[debugging]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[debugging]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[44]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[design-patterns]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[design patterns]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[14]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[dingo]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[dingo]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[26]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[dns]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[dns]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[22]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[dpkg]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[dpkg]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[10]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[entities]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[entities]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[29]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[epiphany]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[epiphany]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[30]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[epiphany-py]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[epiphany-py]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[7]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[git]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[git]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[8]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[git-commit]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[git commit]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[48]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[git-git-commit]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[git git-commit]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[6]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[git-instrumentation]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[git instrumentation]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[40]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[html]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[html]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[17]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[http-304]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[http 304]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[16]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[javascript]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[javascript]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[34]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[jquery]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[jquery]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[31]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[json]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[json]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[41]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[lambda]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[lambda]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[47]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[laptop]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[laptop]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[12]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[laravel]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[laravel]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[20]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[linux]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[linux]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[24]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[livecd]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[livecd]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[2]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[nav_menu]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[main]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[Main]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[37]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[mount]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[mount]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[28]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[pantheon]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[pantheon]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[13]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[php]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[php]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[3]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[python]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[python]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[18]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[rdp]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[rdp]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[38]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[sftp]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[sftp]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[39]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[sshfs]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[sshfs]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[36]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[terminal]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[terminal]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[21]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[ubuntu]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[ubuntu]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[1]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[category]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[uncategorized]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[Uncategorized]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[45]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[validation]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[validation]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[32]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[vim]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[vim]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[23]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[wicd-curses]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[wicd-curses]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[27]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[wordpress]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[wordpress]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[35]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[xhr]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[xhr]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id><![CDATA[42]]></wp:term_id>
      <wp:term_taxonomy><![CDATA[post_tag]]></wp:term_taxonomy>
      <wp:term_slug><![CDATA[zachary]]></wp:term_slug>
      <wp:term_parent><![CDATA[]]></wp:term_parent>
      <wp:term_name><![CDATA[zachary]]></wp:term_name>
    </wp:term>
    <wp:term>
      <wp:term_id>2</wp:term_id>
      <wp:term_taxonomy>nav_menu</wp:term_taxonomy>
      <wp:term_slug><![CDATA[main]]></wp:term_slug>
      <wp:term_name><![CDATA[Main]]></wp:term_name>
    </wp:term>
    <generator>https://wordpress.org/?v=4.6.1</generator>
    <item>
      <title>Resume</title>
      <link>http://jesse-hogan.com/resume/</link>
      <pubDate>Sun, 01 May 2016 02:02:22 +0000</pubDate>
      <dc:creator><![CDATA[jhogan]]></dc:creator>
      <guid isPermaLink="false">http://jesse-hogan.com/2016/05/01/resume/</guid>
      <description/>
      <content:encoded><![CDATA[]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>4</wp:post_id>
      <wp:post_date><![CDATA[2016-05-01 02:02:22]]></wp:post_date>
      <wp:post_date_gmt><![CDATA[2016-05-01 02:02:22]]></wp:post_date_gmt>
      <wp:comment_status><![CDATA[closed]]></wp:comment_status>
      <wp:ping_status><![CDATA[closed]]></wp:ping_status>
      <wp:post_name><![CDATA[resume]]></wp:post_name>
      <wp:status><![CDATA[publish]]></wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>2</wp:menu_order>
      <wp:post_type><![CDATA[nav_menu_item]]></wp:post_type>
      <wp:post_password><![CDATA[]]></wp:post_password>
      <wp:is_sticky>0</wp:is_sticky>
      <category domain="nav_menu" nicename="main"><![CDATA[Main]]></category>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_type]]></wp:meta_key>
        <wp:meta_value><![CDATA[custom]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_menu_item_parent]]></wp:meta_key>
        <wp:meta_value><![CDATA[0]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_object_id]]></wp:meta_key>
        <wp:meta_value><![CDATA[3]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_object]]></wp:meta_key>
        <wp:meta_value><![CDATA[custom]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_target]]></wp:meta_key>
        <wp:meta_value><![CDATA[]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_classes]]></wp:meta_key>
        <wp:meta_value><![CDATA[a:1:{i:0;s:0:"";}]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_xfn]]></wp:meta_key>
        <wp:meta_value><![CDATA[]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_menu_item_url]]></wp:meta_key>
        <wp:meta_value><![CDATA[/resume]]></wp:meta_value>
      </wp:postmeta>
    </item>
    <item>
      <title>Jesse Web Background</title>
      <link>http://jesse-hogan.com/jesse-web-background/</link>
      <pubDate>Mon, 02 May 2016 20:12:33 +0000</pubDate>
      <dc:creator><![CDATA[dhogan]]></dc:creator>
      <guid isPermaLink="false">http://jesse-hogan.com/wp-content/uploads/2016/05/Jesse-Web-Background.png</guid>
      <description/>
      <content:encoded><![CDATA[]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>61</wp:post_id>
      <wp:post_date><![CDATA[2016-05-02 20:12:33]]></wp:post_date>
      <wp:post_date_gmt><![CDATA[2016-05-02 20:12:33]]></wp:post_date_gmt>
      <wp:comment_status><![CDATA[open]]></wp:comment_status>
      <wp:ping_status><![CDATA[closed]]></wp:ping_status>
      <wp:post_name><![CDATA[jesse-web-background]]></wp:post_name>
      <wp:status><![CDATA[inherit]]></wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>0</wp:menu_order>
      <wp:post_type><![CDATA[attachment]]></wp:post_type>
      <wp:post_password><![CDATA[]]></wp:post_password>
      <wp:is_sticky>0</wp:is_sticky>
      <wp:attachment_url><![CDATA[http://jesse-hogan.com/wp-content/uploads/2016/05/Jesse-Web-Background.png]]></wp:attachment_url>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_attached_file]]></wp:meta_key>
        <wp:meta_value><![CDATA[2016/05/Jesse-Web-Background.png]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_attachment_metadata]]></wp:meta_key>
        <wp:meta_value><![CDATA[a:5:{s:5:"width";i:1440;s:6:"height";i:520;s:4:"file";s:32:"2016/05/Jesse-Web-Background.png";s:5:"sizes";a:7:{s:9:"thumbnail";a:4:{s:4:"file";s:32:"Jesse-Web-Background-150x150.png";s:5:"width";i:150;s:6:"height";i:150;s:9:"mime-type";s:9:"image/png";}s:6:"medium";a:4:{s:4:"file";s:32:"Jesse-Web-Background-300x108.png";s:5:"width";i:300;s:6:"height";i:108;s:9:"mime-type";s:9:"image/png";}s:12:"medium_large";a:4:{s:4:"file";s:32:"Jesse-Web-Background-768x277.png";s:5:"width";i:768;s:6:"height";i:277;s:9:"mime-type";s:9:"image/png";}s:5:"large";a:4:{s:4:"file";s:33:"Jesse-Web-Background-1024x370.png";s:5:"width";i:1024;s:6:"height";i:370;s:9:"mime-type";s:9:"image/png";}s:14:"post-thumbnail";a:4:{s:4:"file";s:32:"Jesse-Web-Background-720x260.png";s:5:"width";i:720;s:6:"height";i:260;s:9:"mime-type";s:9:"image/png";}s:13:"identity-logo";a:4:{s:4:"file";s:31:"Jesse-Web-Background-224x81.png";s:5:"width";i:224;s:6:"height";i:81;s:9:"mime-type";s:9:"image/png";}s:29:"identity-full-width-thumbnail";a:4:{s:4:"file";s:33:"Jesse-Web-Background-1140x412.png";s:5:"width";i:1140;s:6:"height";i:412;s:9:"mime-type";s:9:"image/png";}}s:10:"image_meta";a:12:{s:8:"aperture";s:1:"0";s:6:"credit";s:0:"";s:6:"camera";s:0:"";s:7:"caption";s:0:"";s:17:"created_timestamp";s:1:"0";s:9:"copyright";s:0:"";s:12:"focal_length";s:1:"0";s:3:"iso";s:1:"0";s:13:"shutter_speed";s:1:"0";s:5:"title";s:0:"";s:11:"orientation";s:1:"0";s:8:"keywords";a:0:{}}}]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_attachment_custom_header_last_used_identity]]></wp:meta_key>
        <wp:meta_value><![CDATA[1462220036]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_attachment_is_custom_header]]></wp:meta_key>
        <wp:meta_value><![CDATA[identity]]></wp:meta_value>
      </wp:postmeta>
    </item>
    <item>
      <title>My Story</title>
      <link>http://jesse-hogan.com/about/</link>
      <pubDate>Sun, 01 May 2016 02:12:54 +0000</pubDate>
      <dc:creator><![CDATA[jhogan]]></dc:creator>
      <guid isPermaLink="false">http://jesse-hogan.com/?page_id=7</guid>
      <description/>
      <content:encoded><![CDATA[When I was in > 3<sup>rd</sup> grade, my grandmother gave me a <a href="https://en.wikipedia.org/wiki/TRS-80">TRS-80</a> - a powerful machine even without the cassette recorder to which I could save my work. Even at that young age, I was fascinated by the notion that, in principle, computers could execute any set of logical operations, if properly programmed.

Later, with the advent of <a href="https://en.wikipedia.org/wiki/Windows_95">Windows 95</a> and its <a href="https://en.wikipedia.org/wiki/QBasic">QBasic</a> interpreter, I began to teach myself programming in earnest. My first programs were attempts to see how creative I could get a computer to be. I used QBasic's graphics facilities to create images of human faces relying on the random number generator. I was also interested creating programs that could create original prose. How I wish I still had the source code for those early attempts.

Later I got the latest version of <a href="https://en.wikipedia.org/wiki/Visual_Basic">Visual Basic interpreter (VB5)</a> and began my foray into the world of professional programming. I learned about databases, SQL, object-oriented programming and website programming with <a href="https://en.wikipedia.org/wiki/Active_Server_Pages">ASP</a>. I began writing inventory tracking software for my employer using Visual Basic for Applications, Microsoft Access and MySQL.

On the heels of the dot-com bubble, I began work as a software developer at <a href="http://www.revana.com/">Direct Alliance Corporation</a>. I was thrown right into a noodly pit of classic, 1970's style spaghetti code. Within a few months, I was able to work my way into a more respectable position of VB6/ASP developer. In the meantime, I taught myself Perl by writing an <a href="https://github.com/jhogan/antipasta">IMS/Basic parser</a> as an attempt at manage the legacy system's spaghetti code.

The VB6/ASP application was a full-featured CRM/ERP system written to replace the old IMS/Basic system. Though it was written in classic ASP/<a href="https://en.wikipedia.org/wiki/Component_Object_Model">COM</a>, we began adding .NET features to it such as C# and ASP.NET. As it became more mature, I began writing configuration management software such as issue tracking and software deployment programs in ASP.NET and C#. I was also writing file management software in Perl.

I eventually moved on to <a href="http://www.glynlyon.com/">Glynlyon Inc</a>. There I maintained <a href="https://en.wikipedia.org/wiki/Learning_management_system">learning management systems (LMS)</a> using .NET technologies as well as PHP and other open-source software.  ]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>7</wp:post_id>
      <wp:post_date><![CDATA[2016-05-01 02:12:54]]></wp:post_date>
      <wp:post_date_gmt><![CDATA[2016-05-01 02:12:54]]></wp:post_date_gmt>
      <wp:comment_status><![CDATA[closed]]></wp:comment_status>
      <wp:ping_status><![CDATA[closed]]></wp:ping_status>
      <wp:post_name><![CDATA[about]]></wp:post_name>
      <wp:status><![CDATA[publish]]></wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>0</wp:menu_order>
      <wp:post_type><![CDATA[page]]></wp:post_type>
      <wp:post_password><![CDATA[]]></wp:post_password>
      <wp:is_sticky>0</wp:is_sticky>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_edit_last]]></wp:meta_key>
        <wp:meta_value><![CDATA[1]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_page_template]]></wp:meta_key>
        <wp:meta_value><![CDATA[default]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_content_score]]></wp:meta_key>
        <wp:meta_value><![CDATA[30]]></wp:meta_value>
      </wp:postmeta>
    </item>
    <item>
      <title>Resume</title>
      <link>http://jesse-hogan.com/resume/</link>
      <pubDate>Sun, 01 May 2016 13:43:54 +0000</pubDate>
      <dc:creator><![CDATA[jhogan]]></dc:creator>
      <guid isPermaLink="false">http://jesse-hogan.com/?page_id=13</guid>
      <description/>
      <content:encoded><![CDATA[<div>
    <style>
      header.author-profile{text-align: center;}
      header#masthead{display: none;}
      header.entry-header{display: none;}
      div.org-meta{font-weight: bolder;}
      div.org-meta span {width: 33%; display: inline-table;}
      ul.summary li{margin-bottom: 1em;}
      section#experience h2 {margin-bottom: 0.5rem; margin-top: 2.5rem;}
      section#contact-details h1{margin-bottom: -1.5rem;}
      address{font-style: normal;}
    </style>
    <div id="wrapper">
      <div id="content">
        <header class="author-profile">
          <section id="contact-details">
            <div class="header_2">
              <h1>
                <span>Jesse Hogan</span><a id="doc" href="https://github.com/jhogan/resume/blob/master/hogan,jesse-software_developer.docx?raw=true" title="Download Resume in Word"><img src="data:image/svg+xml;utf8;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iaXNvLTg4NTktMSI/Pgo8IS0tIEdlbmVyYXRvcjogQWRvYmUgSWxsdXN0cmF0b3IgMTguMS4xLCBTVkcgRXhwb3J0IFBsdWctSW4gLiBTVkcgVmVyc2lvbjogNi4wMCBCdWlsZCAwKSAgLS0+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayIgdmVyc2lvbj0iMS4xIiBpZD0iQ2FwYV8xIiB4PSIwcHgiIHk9IjBweCIgdmlld0JveD0iMCAwIDMxLjAwNCAzMS4wMDQiIHN0eWxlPSJlbmFibGUtYmFja2dyb3VuZDpuZXcgMCAwIDMxLjAwNCAzMS4wMDQ7IiB4bWw6c3BhY2U9InByZXNlcnZlIiB3aWR0aD0iMzJweCIgaGVpZ2h0PSIzMnB4Ij4KPGc+Cgk8cGF0aCBkPSJNMjIuMzk5LDMxLjAwNFYyNi40OWMwLTAuOTM4LDAuNzU4LTEuNjk5LDEuNjk3LTEuNjk5bDMuNDk4LTAuMUwyMi4zOTksMzEuMDA0eiIgZmlsbD0iIzAwNkRGMCIvPgoJPHBhdGggZD0iTTI1Ljg5OCwwSDUuMTA5QzQuMTY4LDAsMy40MSwwLjc2LDMuNDEsMS42OTV2MjcuNjExYzAsMC45MzgsMC43NTksMS42OTcsMS42OTksMS42OTdoMTUuNjAydi02LjAyICAgYzAtMC45MzYsMC43NjItMS42OTcsMS42OTktMS42OTdoNS4xODVWMS42OTVDMjcuNTk0LDAuNzYsMjYuODM3LDAsMjUuODk4LDB6IE0yNC43NTcsMTQuNTFjMCwwLjI2Ni0wLjI5MywwLjQ4NC0wLjY1NiwwLjQ4NCAgIEg2LjU2NmMtMC4zNjMsMC0wLjY1OC0wLjIxOS0wLjY1OC0wLjQ4NHYtMC44MDdjMC0wLjI2OCwwLjI5NS0wLjQ4NCwwLjY1OC0wLjQ4NGgxNy41MzVjMC4zNjMsMCwwLjY1NiwwLjIxNywwLjY1NiwwLjQ4NCAgIEwyNC43NTcsMTQuNTFMMjQuNzU3LDE0LjUxeiBNMjQuNzU3LDE3Ljk4OGMwLDAuMjctMC4yOTMsMC40ODQtMC42NTYsMC40ODRINi41NjZjLTAuMzYzLDAtMC42NTgtMC4yMTUtMC42NTgtMC40ODR2LTAuODA1ICAgYzAtMC4yNjgsMC4yOTUtMC40ODYsMC42NTgtMC40ODZoMTcuNTM1YzAuMzYzLDAsMC42NTYsMC4yMTksMC42NTYsMC40ODZMMjQuNzU3LDE3Ljk4OEwyNC43NTcsMTcuOTg4eiBNMjQuNzU3LDIxLjUzOSAgIGMwLDAuMjY4LTAuMjkzLDAuNDg0LTAuNjU2LDAuNDg0SDYuNTY2Yy0wLjM2MywwLTAuNjU4LTAuMjE3LTAuNjU4LTAuNDg0di0wLjgwN2MwLTAuMjY4LDAuMjk1LTAuNDg2LDAuNjU4LTAuNDg2aDE3LjUzNSAgIGMwLjM2MywwLDAuNjU2LDAuMjE5LDAuNjU2LDAuNDg2TDI0Ljc1NywyMS41MzlMMjQuNzU3LDIxLjUzOXogTTE1Ljg0LDI1LjA1NWMwLDAuMjY2LTAuMTU1LDAuNDgtMC4zNDcsMC40OEg2LjI1NSAgIGMtMC4xOTIsMC0wLjM0OC0wLjIxNS0wLjM0OC0wLjQ4di0wLjgwOWMwLTAuMjY2LDAuMTU1LTAuNDg0LDAuMzQ4LTAuNDg0aDkuMjM4YzAuMTkxLDAsMC4zNDcsMC4yMTksMC4zNDcsMC40ODRWMjUuMDU1eiAgICBNMTIuMzY0LDExLjM5MUwxMC42OCw1LjQxNmwtMS45MDYsNS45NzVIOC4wODdjMCwwLTIuNTUxLTcuNjIxLTIuNzU5LTcuOTAyQzUuMTk0LDMuMjk1LDQuOTksMy4xNTgsNC43MTksMy4wNzZWMi43NDJoMy43ODMgICB2MC4zMzRjLTAuMjU3LDAtMC40MzQsMC4wNDEtMC41MjksMC4xMjVzLTAuMTQ0LDAuMTgtMC4xNDQsMC4yODdjMCwwLjEwMiwxLjM1NCw0LjE5MywxLjM1NCw0LjE5M2wxLjA1OC0zLjI3OSAgIGMwLDAtMC4zNzktMC45NDctMC40OTktMS4wNzJDOS42MjEsMy4yMDksOS40MzQsMy4xMjMsOS4xODIsMy4wNzZWMi43NDJoMy44NHYwLjMzNGMtMC4zMDEsMC4wMTgtMC40ODksMC4wNjUtMC41NjksMC4xMzcgICBjLTAuMDgsMC4wNzYtMC4xMiwwLjE4Mi0wLjEyLDAuMzJjMCwwLjEzMSwxLjI5MSw0LjE0OCwxLjI5MSw0LjE0OHMxLjE3MS0zLjc0LDEuMTcxLTMuODk2YzAtMC4yMzQtMC4wNTEtMC40MDQtMC4xNTMtMC41MTQgICBjLTAuMTAxLTAuMTA3LTAuMjk5LTAuMTcyLTAuNTkyLTAuMTk1VjIuNzQyaDIuMjJ2MC4zMzRjLTAuMjQ1LDAuMDM1LTAuNDQyLDAuMTMzLTAuNTg1LDAuMjkxICAgYy0wLjE0NiwwLjE1OC0yLjY2Miw4LjAyMy0yLjY2Miw4LjAyM2gtMC42NlYxMS4zOTF6IE0yNC45MzMsNC42N2MwLDAuMjY2LTAuMTMxLDAuNDgyLTAuMjkzLDAuNDgyaC03Ljc5ICAgYy0wLjE2MiwwLTAuMjkzLTAuMjE3LTAuMjkzLTAuNDgyVjMuODYxYzAtMC4yNjYsMC4xMzEtMC40ODIsMC4yOTMtMC40ODJoNy43OWMwLjE2MiwwLDAuMjkzLDAuMjE3LDAuMjkzLDAuNDgyVjQuNjd6ICAgIE0yNC45OTcsMTAuNjYyYzAsMC4yNjgtMC4xMzEsMC40OC0wLjI5MiwwLjQ4aC03Ljc5MWMtMC4xNjQsMC0wLjI5My0wLjIxMy0wLjI5My0wLjQ4VjkuODU0YzAtMC4yNjYsMC4xMjktMC40ODQsMC4yOTMtMC40ODQgICBoNy43OTFjMC4xNjEsMCwwLjI5MiwwLjIxOSwwLjI5MiwwLjQ4NFYxMC42NjJ6IE0yNC45NjUsNy42NzZjMCwwLjI2OC0wLjEyOSwwLjQ4Mi0wLjI5MywwLjQ4MmgtNy43OSAgIGMtMC4xNjIsMC0wLjI5My0wLjIxNS0wLjI5My0wLjQ4MlY2Ljg2OWMwLTAuMjY4LDAuMTMxLTAuNDg0LDAuMjkzLTAuNDg0aDcuNzljMC4xNjQsMCwwLjI5MywwLjIxNywwLjI5MywwLjQ4NFY3LjY3NnoiIGZpbGw9IiMwMDZERjAiLz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8Zz4KPC9nPgo8L3N2Zz4K" /></a><a id="pdf" href="https://github.com/jhogan/resume/blob/master/hogan,jesse-software_developer.pdf?raw=true" title="Download Resume in PDF"><img src="data:image/svg+xml;utf8;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iaXNvLTg4NTktMSI/Pgo8IS0tIEdlbmVyYXRvcjogQWRvYmUgSWxsdXN0cmF0b3IgMTYuMC4wLCBTVkcgRXhwb3J0IFBsdWctSW4gLiBTVkcgVmVyc2lvbjogNi4wMCBCdWlsZCAwKSAgLS0+CjwhRE9DVFlQRSBzdmcgUFVCTElDICItLy9XM0MvL0RURCBTVkcgMS4xLy9FTiIgImh0dHA6Ly93d3cudzMub3JnL0dyYXBoaWNzL1NWRy8xLjEvRFREL3N2ZzExLmR0ZCI+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94bGluayIgdmVyc2lvbj0iMS4xIiBpZD0iQ2FwYV8xIiB4PSIwcHgiIHk9IjBweCIgd2lkdGg9IjMycHgiIGhlaWdodD0iMzJweCIgdmlld0JveD0iMCAwIDU1MC44MDEgNTUwLjgwMSIgc3R5bGU9ImVuYWJsZS1iYWNrZ3JvdW5kOm5ldyAwIDAgNTUwLjgwMSA1NTAuODAxOyIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSI+CjxnPgoJPHBhdGggZD0iTTE2MC4zODEsMjgyLjIyNWMwLTE0LjgzMi0xMC4yOTktMjMuNjg0LTI4LjQ3NC0yMy42ODRjLTcuNDE0LDAtMTIuNDM3LDAuNzE1LTE1LjA3MSwxLjQzMlYzMDcuNiAgIGMzLjExNCwwLjcwNyw2Ljk0MiwwLjk0OSwxMi4xOTIsMC45NDlDMTQ4LjQxOSwzMDguNTQ5LDE2MC4zODEsMjk4Ljc0LDE2MC4zODEsMjgyLjIyNXoiIGZpbGw9IiNEODAwMjciLz4KCTxwYXRoIGQ9Ik0yNzIuODc1LDI1OS4wMTljLTguMTQ1LDAtMTMuMzk3LDAuNzE3LTE2LjUxOSwxLjQzNXYxMDUuNTIzYzMuMTE2LDAuNzI5LDguMTQyLDAuNzI5LDEyLjY5LDAuNzI5ICAgYzMzLjAxNywwLjIzMSw1NC41NTQtMTcuOTQ2LDU0LjU1NC01Ni40NzRDMzIzLjg0MiwyNzYuNzE5LDMwNC4yMTUsMjU5LjAxOSwyNzIuODc1LDI1OS4wMTl6IiBmaWxsPSIjRDgwMDI3Ii8+Cgk8cGF0aCBkPSJNNDg4LjQyNiwxOTcuMDE5SDQ3NS4ydi02My44MTZjMC0wLjM5OC0wLjA2My0wLjc5OS0wLjExNi0xLjIwMmMtMC4wMjEtMi41MzQtMC44MjctNS4wMjMtMi41NjItNi45OTVMMzY2LjMyNSwzLjY5NCAgIGMtMC4wMzItMC4wMzEtMC4wNjMtMC4wNDItMC4wODUtMC4wNzZjLTAuNjMzLTAuNzA3LTEuMzcxLTEuMjk1LTIuMTUxLTEuODA0Yy0wLjIzMS0wLjE1NS0wLjQ2NC0wLjI4NS0wLjcwNi0wLjQxOSAgIGMtMC42NzYtMC4zNjktMS4zOTMtMC42NzUtMi4xMzEtMC44OTZjLTAuMi0wLjA1Ni0wLjM4LTAuMTM4LTAuNTgtMC4xOUMzNTkuODcsMC4xMTksMzU5LjAzNywwLDM1OC4xOTMsMEg5Ny4yICAgYy0xMS45MTgsMC0yMS42LDkuNjkzLTIxLjYsMjEuNjAxdjE3NS40MTNINjIuMzc3Yy0xNy4wNDksMC0zMC44NzMsMTMuODE4LTMwLjg3MywzMC44NzN2MTYwLjU0NSAgIGMwLDE3LjA0MywxMy44MjQsMzAuODcsMzAuODczLDMwLjg3aDEzLjIyNFY1MjkuMmMwLDExLjkwNyw5LjY4MiwyMS42MDEsMjEuNiwyMS42MDFoMzU2LjRjMTEuOTA3LDAsMjEuNi05LjY5MywyMS42LTIxLjYwMSAgIFY0MTkuMzAyaDEzLjIyNmMxNy4wNDQsMCwzMC44NzEtMTMuODI3LDMwLjg3MS0zMC44N3YtMTYwLjU0QzUxOS4yOTcsMjEwLjgzOCw1MDUuNDcsMTk3LjAxOSw0ODguNDI2LDE5Ny4wMTl6IE05Ny4yLDIxLjYwNSAgIGgyNTAuMTkzdjExMC41MTNjMCw1Ljk2Nyw0Ljg0MSwxMC44LDEwLjgsMTAuOGg5NS40MDd2NTQuMTA4SDk3LjJWMjEuNjA1eiBNMzYyLjM1OSwzMDkuMDIzYzAsMzAuODc2LTExLjI0Myw1Mi4xNjUtMjYuODIsNjUuMzMzICAgYy0xNi45NzEsMTQuMTE3LTQyLjgyLDIwLjgxNC03NC4zOTYsMjAuODE0Yy0xOC45LDAtMzIuMjk3LTEuMTk3LTQxLjQwMS0yLjM4OVYyMzQuMzY1YzEzLjM5OS0yLjE0OSwzMC44NzgtMy4zNDYsNDkuMzA0LTMuMzQ2ICAgYzMwLjYxMiwwLDUwLjQ3OCw1LjUwOCw2Ni4wMzksMTcuMjI2QzM1MS44MjgsMjYwLjY5LDM2Mi4zNTksMjgwLjU0NywzNjIuMzU5LDMwOS4wMjN6IE04MC43LDM5My40OTlWMjM0LjM2NSAgIGMxMS4yNDEtMS45MDQsMjcuMDQyLTMuMzQ2LDQ5LjI5Ni0zLjM0NmMyMi40OTEsMCwzOC41MjcsNC4zMDgsNDkuMjkxLDEyLjkyOGMxMC4yOTIsOC4xMzEsMTcuMjE1LDIxLjUzNCwxNy4yMTUsMzcuMzI4ICAgYzAsMTUuNzk5LTUuMjUsMjkuMTk4LTE0LjgyOSwzOC4yODVjLTEyLjQ0MiwxMS43MjgtMzAuODY1LDE2Ljk5Ni01Mi40MDcsMTYuOTk2Yy00Ljc3OCwwLTkuMS0wLjI0My0xMi40MzUtMC43MjN2NTcuNjdIODAuNyAgIFYzOTMuNDk5eiBNNDUzLjYwMSw1MjMuMzUzSDk3LjJWNDE5LjMwMmgzNTYuNFY1MjMuMzUzeiBNNDg0Ljg5OCwyNjIuMTI3aC02MS45ODl2MzYuODUxaDU3LjkxM3YyOS42NzRoLTU3LjkxM3Y2NC44NDhoLTM2LjU5MyAgIFYyMzIuMjE2aDk4LjU4MlYyNjIuMTI3eiIgZmlsbD0iI0Q4MDAyNyIvPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+CjxnPgo8L2c+Cjwvc3ZnPgo=" /></a>
              </h1>
              <h3>Software Developer</h3>
              <address>
                17212 N Scottsdale Rd. <br/>
                Apt: 2245
                Scottsdale, AZ
                (480) 745-6116 <br/>
                <a href="mailto:jessehogan0@gmail.com">jessehogan0@gmail.com</a> <br/>
              </address>
            </div>
          </section>
        </header>
        <div class="clear"> </div>
        <dl>
          <dt><h2>Overview</h2></dt>
          <dd>
            <ul class="summary">
              <li>
                16 years of solid software development experience.
              </li>
              <li>
                A broad skill-set which allows me to choose the correct solutions and
                technologies to solve problems.
              </li>
              <li>
                Language Expertise: C#, PHP, C, Perl, VB.NET, ASP.NET, Python,
                Bash Shell, AWK, Sed, SQL, JavaScript/HTML/CSS and more.
              </li>
              <li>
                Frameworks: ASP.NET MVC, Doctrine ORM, CSLA, .NET, Hibernate
              </li>
              <li>
                Server Expertise: Linux, Microsoft Windows, Apache, MySQL, Microsoft SQL
                Server, IIS, Subversion, etc...
              </li>
              <li>
                I've programmed in many problem domains: ERP, CRM, 
                learning management systems (LMS), front-end, back-end
                (multi-tiered, transactional), automated code deployments, B2B
                communication (XML/XSLT/EDI), ActiveRecord ORM development, RDBMS data
                archiving, automated file exchange (FTP/SFTP), shell scripting and
                automated system monitoring
              </li>
              <li>
                I have strong Linux/Unix and Microsoft Windows administration skills as
                well as strong networking skills.
              </li>
              <li>
                I have configuration management experience (source control
                management/administration (Git/Github, Subversion), build management,
                deployment automation (Jenkins), Automated Testing (NUnit, Sikuli ,
                etc...)
              </li>
              <li>
                I'm an object-oriented programmer with a strong emphasis on writing
                highly reusable and highly maintainable code.
              </li>
              <li>
                I work very well independently and on single-person projects. I also
                work well in a team environment. I communicate well, am helpful, and
                keep interested parties informed on the status of my efforts.
              </li>
              <li>
                I am highly self-trainable.
              </li>
              <li>
                I have experience working with overseas clients and developers.
              </li>
              <li>
                I have significant training in AngularJS, Drupal, and Java development.
              </li>
            </ul>
          </dd>
        </dl>
        <!-- End Profile Section -->

        <div class="clear"> </div>
        <!-- Begin Experience Section -->
        <dl>
          <dt><h2>Experience</h2></dt>
          <dd>
            <section id="experience">

              <!-- Position #1 -->
              <h2 class="top">Software Developer</h2>
              <div class="org-meta">
                 <span class="bus1">Glynlyon Inc.</span> <span class="time">2008 to 2016</span><span class="location">Chandler, Az</span>
              </div>
              <p>
                  As a WordPress/PHP developer, I built and maintained several public
                  facing sites. The software was developed using PHP, JavaScript, jQuery,
                  HTML and CSS. The e-commerce sites used Magento. Other sites used
                  WordPress in a Pantheon environment. Source code was maintained in
                  Subversion and Git repositories. I built and maintained a custom
                  WebService proxy in PHP so the WordPress sites could generate leads in
                  the Microsoft CRM server.
              </p>
              <p>
                  I was a member of a software development team that develops and
                  maintains an learning management system (LMS) (grades 3 through 12). The
                  user interface is written in HTML, CSS, JavaScript and jQuery. The
                  business tier is written in PHP with a custom-built MVC framework. It
                  uses Doctrine as an object-relational mapper to interface with a MySQL
                  back-end. 
              </p>
              <p>
                  I also supported and developed a similar software product that uses
                  Microsoft and open source technologies. For back-end operations, we use
                  SQL Server 2005/2008 accessed through direct ODBC calls and through a
                  Web Services interface. The business tier is developed in C# and VB.NET.
                  The front end is chiefly comprised of HTML/CSS, jQuery and WinForms.
                  Multimedia offerings, such as videos and games, are implemented in Flash
                  and HTML5. Reports are implemented in Crystal Reports. We use Subversion
                  and Git for source control.
              </p>
              <p>
                  Working with the Curriculum Development department, I wrote scripts to
                  automate the file management, validation, correction, reporting, source
                  control management (Subversion), and deployment (server and CD) of a
                  vast number of XML files. This is done using Bash, Python, Visual Basic
                  and C#.
              </p>
              <p>
                  My database administrative activities include creating and maintaining
                  scripts written in Bash and Python to automate the code-generation of
                  SQL scripts which perform the task of database schema migrations. I also
                  maintain a GUI utility which allows tech-support and customers to easily
                  perform database administrative tasks against production databases.
              </p>

              <!-- Position #2 -->
              <h2>Software Developer</h2>
              <div class="org-meta">
                <span class="bus1">Direct Alliance Corporation</span> <span class="time">2001 to 2008</span> <span class="location">Tempe, Az</span>
              </div>
              <p>
                I was team-lead of a department which develops, maintains and optimizes
                a 3-tiered, internationalized, web-based, telesales ERP system for a
                large overseas client. It is a large system with multiple functional
                areas including order entry, fulfillment, accounting, account management
                and human resources. The system uses HTML, CSS, JavaScript, ASP and
                ASP.NET for its UI tier. Visual Basic COM  DLL's and C# managed DLL's in
                a COM+ application are used as the business tier. Stored procedures
                running on a MS SQL Server database provided the data layer. Microsoft
                SQL Server replication is used to maintain a separate database used for
                reports implemented with ActiveReports. The system also has a B2B
                ordering interface which accepts XML data (through HTTP POST's) for
                order placement. Fulfillment is accomplished by an EDI interface with
                suppliers. It fulfills 300-600 orders a day.
              </p>
              <p>
                I wrote a desktop application to automate the source control management
                (CVS and Subversion) and source code deployment of several web and
                text-based applications for several different clients. The software also
                maintains time metrics on SCM and QA personnel, maintains data related
                to the software changes being deployed, and reported on its data in text
                or Excel formats. The software was implemented in C# (WinForms). I wrote
                an ORM based on CSLA (Business Objects) to automated common CRUD tasks.
                I used a MySQL database for data persistence. 
              </p>
              <p>
                I maintained a Perl middleware program in a Linux environment
                responsible for file transfers (usually over FTP or SFTP) from servers
                in external networks to local servers and visa-versa. The files contain
                different type of high priority business data such as database extracts,
                TSR call data, EDI data and so on.
              </p>
              <p>
                I wrote a Perl program to replicate Subversion commit deltas from one
                Subversion data store to another to provide a redundant repository in
                the case of a failure. 
              </p>
              <p>
                I wrote software to archive sales order records (along with child
                records from hundreds of child tables) to an archive database server.
                The software is composed of two programs: A C# WinForm application to
                configure the archiving process and a daemon program to archive the
                data.
              </p>
              <p>
                I maintained an internal website responsible for managing the
                communication between different departments and clients during major
                system failures such as a website outage. The system was written in
                ASP.NET and used Microsoft SQL Server as a back-ends. 
              </p>
              <p>
                I maintained a Forte3 (ERP) system written in IMS/BASIC in Linux and SCO
                UNIX environment for several different clients. The system provide many
                business functions such as: accounts receivable/payable, order entry,
                fulfillment and so on. The code is managed using a CVS repository.
              </p>

              <!-- Position #3 -->
              <h2>Database Developer</h2>
              <div class="org-meta">
                <span class="bus1">ITMETRIXX</span> <span class="time">2000 to 2001</span> <span class="location">Phoenix, Az</span>
              </div>
              <p>
                I developed a ticketing system to be utilized from various locations for
                Sun Health, Inc., a major corporation with multiple client sites. This
                project included use of Microsoft Access interfacing with a MySQL
                back-end running on a Linux platform. The system effectively managed
                entry of hardware hot swap orders and technical support issues.
              </p>
              <p>
                I trained end-users and peers in various technical procedures.
              </p>

              <!-- Position #4 -->
              <h2>Database Application Developer</h2>
              <div class="org-meta">
                <span class="bus1">Inacom</span> <span class="time">1998 to 2000</span> <span class="location">Phoenix, Az</span>
              </div>
              <p>
                Wrote software to manage warehouse inventory and track technical issues.
                System was implemented in Microsoft Access.
              </p>
              <p>
                I wrote a system for Human Resources operations. System was written in
                Microsoft Access and used Excel Automation for reporting.
              </p>

              <!-- Position #5 -->
              <h2>Technical Consultant</h2>
              <div class="org-meta">
                <span class="bus1">Microage</span> <span class="time">1998</span> <span class="location">Tempe, Az</span>
              </div>
              <p>
                I diagnosed connectivity problems for US West ADSL routers in the
                technical support department. Performed advanced troubleshooting daily. 
              </p>
              <p>
                I interacted extensively with US West customers to identify issues.
              </p>
              <p>
                I performed sales activities to secure new business for DSL routers.
              </p>
            </section>
          </dd>
        </dl>

        <!-- End Experience Section -->
        <div class="clear"> </div>

        <footer id="footer">
          <div>
            <ul class="icons_2">
              
            </ul>
            <!-- End Schema Person -->
          </div>
          <div class="credits">
            <small>
              Icon made by <a href="mailto:jessehogan0@gmail.com">jessehogan0@gmail.com</a>              from <a title="Flaticon" href="http://www.flaticon.com">www.flaticon.com</a></small>
          </div>

          <!-- End Footer Content -->
        </footer>
        <!-- End Footer -->
      </div>
      <!-- End Content -->
    </div>
    <!-- End Wrapper -->
</div>
]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>13</wp:post_id>
      <wp:post_date><![CDATA[2016-05-01 13:43:54]]></wp:post_date>
      <wp:post_date_gmt><![CDATA[2016-05-01 13:43:54]]></wp:post_date_gmt>
      <wp:comment_status><![CDATA[closed]]></wp:comment_status>
      <wp:ping_status><![CDATA[closed]]></wp:ping_status>
      <wp:post_name><![CDATA[resume]]></wp:post_name>
      <wp:status><![CDATA[publish]]></wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>0</wp:menu_order>
      <wp:post_type><![CDATA[page]]></wp:post_type>
      <wp:post_password><![CDATA[]]></wp:post_password>
      <wp:is_sticky>0</wp:is_sticky>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_edit_last]]></wp:meta_key>
        <wp:meta_value><![CDATA[1]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_wp_page_template]]></wp:meta_key>
        <wp:meta_value><![CDATA[default]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_content_score]]></wp:meta_key>
        <wp:meta_value><![CDATA[30]]></wp:meta_value>
      </wp:postmeta>
    </item>
    <item>
      <title>Epiphany Py released</title>
      <link>http://jesse-hogan.com/commonpy-released-2/</link>
      <pubDate>Sun, 18 Sep 2016 20:06:26 +0000</pubDate>
      <dc:creator><![CDATA[jhogan]]></dc:creator>
      <guid isPermaLink="false">http://jesse-hogan.com/?p=109</guid>
      <description/>
      <content:encoded><![CDATA[I've released <a href="https://github.com/jhogan/epiphany-py/tree/1.0">version 1.0</derp> of <a href="https://github.com/jhogan/epiphany-py">Epiphany Py</a> today. Epiphany Py is a collection of libraries that would prove useful in any Python project. Currently it contains a base-class similar to the .NET <a href="https://msdn.microsoft.com/en-us/library/system.collections.collectionbase(v=vs.110).aspx">CollectionBase</a> class. You can use it to make your Python objects behave like super powerful arrays. It also comes with a useful unit testing framework called Tester.

I've enjoyed using these base classes in my other projects and have achieved a high degree of reusability and terseness from them. In future posts, I will provide demonstrations on how to use them. ]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>188</wp:post_id>
      <wp:post_date><![CDATA[2016-09-18 20:06:26]]></wp:post_date>
      <wp:post_date_gmt><![CDATA[2016-09-18 20:06:26]]></wp:post_date_gmt>
      <wp:comment_status><![CDATA[open]]></wp:comment_status>
      <wp:ping_status><![CDATA[open]]></wp:ping_status>
      <wp:post_name><![CDATA[commonpy-released-2]]></wp:post_name>
      <wp:status><![CDATA[publish]]></wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>0</wp:menu_order>
      <wp:post_type><![CDATA[post]]></wp:post_type>
      <wp:post_password><![CDATA[]]></wp:post_password>
      <wp:is_sticky>0</wp:is_sticky>
      <category domain="post_tag" nicename="epiphany"><![CDATA[epiphany]]></category>
      <category domain="post_tag" nicename="epiphany-py"><![CDATA[epiphany-py]]></category>
      <category domain="post_tag" nicename="python"><![CDATA[python]]></category>
      <category domain="category" nicename="uncategorized"><![CDATA[Uncategorized]]></category>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_edit_last]]></wp:meta_key>
        <wp:meta_value><![CDATA[1]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_primary_category]]></wp:meta_key>
        <wp:meta_value><![CDATA[]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_focuskw_text_input]]></wp:meta_key>
        <wp:meta_value><![CDATA[commonpy]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_focuskw]]></wp:meta_key>
        <wp:meta_value><![CDATA[commonpy]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_metadesc]]></wp:meta_key>
        <wp:meta_value><![CDATA[I've released version 1.0 of commonpy today. It contains a collection base class similar to the.NET CollectionBase class, as well as a useful unit testing]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_linkdex]]></wp:meta_key>
        <wp:meta_value><![CDATA[52]]></wp:meta_value>
      </wp:postmeta>
    </item>
    <item>
      <title>Get Query Duration with dbext with MySQL</title>
      <link>http://jesse-hogan.com/?p=371</link>
      <pubDate>Mon, 30 Nov -0001 00:00:00 +0000</pubDate>
      <dc:creator><![CDATA[jhogan]]></dc:creator>
      <guid isPermaLink="false">http://jesse-hogan.com/?p=371</guid>
      <description/>
      <content:encoded><![CDATA[
dbext uses the MySQL command line to work its magic behind the scenes.
However, there appears to be no way to get <code>mysql</code> to show the query
duration. Luckily, MySQL has a profiling feature that allows you to capture the
duration of a given query.]]></content:encoded>
      <excerpt:encoded><![CDATA[]]></excerpt:encoded>
      <wp:post_id>371</wp:post_id>
      <wp:post_date><![CDATA[2017-03-10 17:15:39]]></wp:post_date>
      <wp:post_date_gmt><![CDATA[0000-00-00 00:00:00]]></wp:post_date_gmt>
      <wp:comment_status><![CDATA[open]]></wp:comment_status>
      <wp:ping_status><![CDATA[open]]></wp:ping_status>
      <wp:post_name><![CDATA[]]></wp:post_name>
      <wp:status><![CDATA[draft]]></wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>0</wp:menu_order>
      <wp:post_type><![CDATA[post]]></wp:post_type>
      <wp:post_password><![CDATA[]]></wp:post_password>
      <wp:is_sticky>0</wp:is_sticky>
      <category domain="category" nicename="uncategorized"><![CDATA[Uncategorized]]></category>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_edit_last]]></wp:meta_key>
        <wp:meta_value><![CDATA[1]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_content_score]]></wp:meta_key>
        <wp:meta_value><![CDATA[60]]></wp:meta_value>
      </wp:postmeta>
      <wp:postmeta>
        <wp:meta_key><![CDATA[_yoast_wpseo_primary_category]]></wp:meta_key>
        <wp:meta_value><![CDATA[]]></wp:meta_value>
      </wp:postmeta>
    </item>
  </channel>
</rss>
"""

cli.run()
