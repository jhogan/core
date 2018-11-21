# vim: set et ts=4 sw=4 fdm=marker
"""
MIT License

Copyright (c) 2018 Jesse Hogan

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
from entities import brokenruleserror, rgetattr
from MySQLdb.constants.ER import BAD_TABLE_ERROR, DUP_ENTRY
import _mysql_exceptions
from parties import *
from pdb import set_trace; B=set_trace
from tester import *
from uuid import uuid4
import argparse
import MySQLdb
import pathlib
import re
import io
import orm
import functools

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
    description = orm.fieldmapping(str)

class presentation(orm.entity):
    name = orm.fieldmapping(str)
    locations = locations

class concert(presentation):
    record = orm.fieldmapping(str)

class component(orm.entity):
    name = orm.fieldmapping(str)

class artifact(orm.entity):
    title = orm.fieldmapping(str)
    components = components

class artist(orm.entity):
    firstname = orm.fieldmapping(str)
    lastname = orm.fieldmapping(str)
    presentations = presentations

class artist_artifacts(orm.associations):
    pass

class artist_artifact(orm.association):
    artist = artist
    artifact = artifact
    role = orm.fieldmapping(str)

class singers(artists):
    pass

class singer(artist):
    # TODO This breaks things
    #locations = locations
    voice = orm.fieldmapping(str)
    concerts = concerts

class test_orm(tester):

    def __init__(self):
        super().__init__()
        self.chronicles = db.chronicles()
        db.chronicler.getinstance().chronicles.onadd += self._chronicler_onadd

        artist.reCREATE(recursive=True)

    def _chronicler_onadd(self, src, eargs):
        self.chronicles += eargs.entity

    def it_has_static_composites_reference(self):
        comps = location.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, presentation)

        comps = comps.first.entity.orm.composites
        self.one(comps)
        self.is_(comps.first.entity, artist)

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
        self.two(consts)
        self.true(presentation in consts)
        self.true(artifact     in consts)

        consts = artist.orm.constituents['presentation'].orm.constituents
        self.one(consts)
        self.is_(consts.first.entity, location)

        consts = artifact.orm.constituents
        self.two(consts)

        consts.sort('name')
        self.is_(consts.first.entity, artist)
        self.is_(consts.second.entity, component)

    def it_has_static_super_references(self):
        self.is_(artist, singer.orm.super)

    def it_loads_and_saves_associations(self):
        # TODO Test loading and saving deeply nested associations
        chrons = self.chronicles
        
        chrons.clear()
        art = artist()

        self.zero(chrons)

        B()
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
        art                   =   artist()
        fact                  =   artifact()
        aa                    =   artist_artifact()
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
        aa2 = artist_artifact()
        aa2.role = uuid4().hex
        aa2.artifact = artifact()

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
        art2.artifacts += artifact()
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
            comps3 += component()

        comps3.sort('id')
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
        art = artist()
        chrons = self.chronicles

        for i in range(2):
            aa = artist_artifact()
            aa.artifact = artifact()
            aa.artifact.title = uuid4().hex
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
            comps += component()
            comps.last.name = uuid4().hex

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

        art = artist()

        for i in range(2):
            aa = artist_artifact()
            aa.artifact = artifact()
            aa.role = uuid4().hex
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
            art = artist()

            for i in range(2):
                aa = artist_artifact()
                aa.artifact = artifact()
                aa.artifact.components += component()
                art.artist_artifacts += aa
                art.artist_artifacts.last.artifact.components += component()

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

            self.expect(db.recordnotfounderror, lambda: artist_artifact(rmaa.id))
            self.expect(db.recordnotfounderror, lambda: artifact(rmfact.id))

            for comp in rmcomps:
                self.expect(db.recordnotfounderror, lambda: component(comp.id))

        # TODO Test deeply nested associations

    def it_rollsback_save_with_broken_trash(self):
        # Test entities collection

        art = artist()
        art.presentations += presentation()
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
        art.save()

        self.zero(artist(art.id).presentations)

        trashid = art.presentations.orm.trash.first.id
        self.expect(db.recordnotfounderror, lambda: presentation(trashid))

        # Test associations
        art = artist()
        art.artifacts += artifact()
        factid = art.artifacts.first.id
        aaid = art.artist_artifacts.first.id

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

        self.expect(db.recordnotfounderror, lambda: artist_artifact(aaid))
        self.expect(db.recordnotfounderror, lambda: artifact(factid))

    def it_raises_error_on_invalid_attributes_of_associations(self):
        art = artist()
        self.expect(AttributeError, lambda: art.artist_artifacts.artifactsX)

    def it_calls_str_on_entity(self):
        # TODO Test str on entity, entities, association and associations.
        pass

    def it_has_broken_rules_of_constituents(self):
        art                =   artist()
        pres               =   presentation()
        loc                =   location()
        pres.locations     +=  loc
        art.presentations  +=  pres

        # Break the rule that presentation.name should be a str
        pres.name = 1

        self.one(art.brokenrules)
        self.broken(art, 'name', 'valid')

        # Break deeply (>2) nested constituent
        # Break the rule that location.description should be a str
        loc.description = 1
        self.two(art.brokenrules)
        self.broken(art, 'description', 'valid')

    def it_moves_constituent_to_a_different_composite(self):
        chrons = self.chronicles

        art = artist()
        art.presentations += presentation()
        art.presentations.last.name = uuid4().hex
        art.save()

        art1 = artist()
        art.presentations.give(art1.presentations)

        self.zero(art.presentations)
        self.one(art1.presentations)
        
        chrons.clear()
        art1.save()

        self.two(chrons)
        self.one(chrons.where('entity', art1))
        self.one(chrons.where('entity', art1.presentations.first))

        self.zero(artist(art.id).presentations)
        self.one(artist(art1.id).presentations)

        # Move deeply nested entity
        art1.presentations.first.locations += location()

        art1.save()

        art.presentations += presentation()
        art1.presentations.first.locations.give(art.presentations.last.locations)

        chrons.clear()
        art.save()

        loc = art.presentations.last.locations.last
        pres = art.presentations.last

        self.two(chrons)
        self.eq(chrons.where('entity', pres).first.op, 'create')
        self.eq(chrons.where('entity', loc).first.op, 'update')

        self.zero(artist(art1.id).presentations.first.locations)
        self.one(artist(art.id).presentations.first.locations)

    def it_saves_entities(self):
        chrons = self.chronicles

        arts = artists()

        for _ in range(2):
            arts += artist()
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
            arts += artist()
            arts.last.firstname = uuid4().hex
            arts.last.lastname = uuid4().hex
        
        # TODO Test chrons
        arts.save()

        art = arts.shift()
        self.one(arts)
        self.one(arts.orm.trash)

        arts.save()

        self.expect(db.recordnotfounderror, lambda: artist(art.id))
        
        # Ensure the remaining artist still exists in database
        self.expect(None, lambda: artist(arts.first.id))

    def it_doesnt_needlessly_save_entitity(self):
        chrons = self.chronicles

        art = artist()
        art.firstname = uuid4().hex
        art.lastname = uuid4().hex

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
        art.presentations += presentation()
        
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
        art.presentations.last.locations += location()

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

        art = artist()

        for _ in range(2):
            art.presentations += presentation()

            for _ in range(2):
                art.presentations.last.locations += location()

        art.save()

        for art in (art, artist(art.id)):
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
        art = artist()
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
        art = artist()
        art.presentations += presentation()
        art.presentations += presentation()

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

        self.two(chrons)

        self.eq(chrons.where('entity', press.first).first.op, 'retrieve')
        self.eq(chrons.where('entity', press.second).first.op, 'retrieve')

        art.presentations.sort('id')
        art1.presentations.sort('id')
        for pres, pres1 in zip(art.presentations, art1.presentations):
            for map in pres.orm.mappings:
                if isinstance(map, orm.fieldmapping):
                    self.eq(getattr(pres, map.name), getattr(pres1, map.name))
            
            self.is_(art1, pres1.artist)

        # Create some locations with the presentations, save artist, reload and
        # test
        for pres in art.presentations:
            for _ in range(2):
                pres.locations += location()

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

        art.presentations.sort('id')
        art1.presentations.sort('id')
        for pres, pres1 in zip(art.presentations, art1.presentations):

            pres.locations.sort('id')

            chrons.clear()
            pres1.locations.sort('id')

            self.two(chrons)
            locs = pres1.locations
            self.eq(chrons.where('entity', locs.first).first.op, 'retrieve')
            self.eq(chrons.where('entity', locs.second).first.op, 'retrieve')

            for loc, loc1 in zip(pres.locations, pres1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(getattr(loc, map.name), getattr(loc1, map.name))
            
                self.is_(pres1, loc1.presentation)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        art = artist()
        press = presentations()

        for _ in range(2):
            press += presentation()

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
        art = artist()

        for _ in range(2):
            art.presentations += presentation()
            art.presentations.last.name = uuid4().hex

            for _ in range(2):
                art.presentations.last.locations += location()
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
        pres = presentation()

        chrons.clear()
        self.none(pres.artist)
        self.zero(chrons)

        self.broken(pres, 'artistid', 'full')

        # Test setting an entity constituent then test saving and loading
        art = artist()
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

        art1 = artist()
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
       
        loc = location()
        self.none(loc.presentation)

        loc.presentation = pres = presentation()
        self.is_(pres, loc.presentation)

        chrons.clear()
        self.none(loc.presentation.artist)
        self.zero(chrons)

        loc.presentation.artist = art = artist()
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
        loc1.presentation.artist = art1 = artist()

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
        pres = presentation()
        pres.artist = artist()

        # Break rule that art.firstname should be a str
        pres.artist.firstname = int() # Break

        self.one(pres.brokenrules)
        self.broken(pres, 'firstname', 'valid')

        pres.artist.firstname = str() # Unbreak
        self.zero(pres.brokenrules)

        loc = location()
        loc.description = int() # break
        loc.presentation = presentation()
        loc.presentation.name = int() # break
        loc.presentation.artist = artist()
        loc.presentation.artist.firstname = int() # break

        self.three(loc.brokenrules)
        for prop in 'description', 'name', 'firstname':
            self.broken(loc, prop, 'valid')


    def it_rollsback_save_of_entity_with_broken_constituents(self):
        art = artist()

        art.presentations += presentation()
        art.presentations.last.name = uuid4().hex

        art.presentations += presentation()
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
        self.expect(db.recordnotfounderror, lambda: artist(art.id))

        # For each presentations, ensure state was not modified and no presentation 
        # object was saved.
        for pres in art.presentations:
            self.true(pres.orm.isnew)
            self.false(pres.orm.isdirty)
            self.false(pres.orm.ismarkedfordeletion)
            self.expect(db.recordnotfounderror, lambda: presentation(pres.id))

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

    def it_calls_RECREATE(self):
        # TODO
        pass

    def it_calls_CREATE(self):
        # TODO
        pass

    def it_calls_DROP(self):
        # TODO
        pass

    def it_calls_id_on_entity(self):
        art = artist()

        self.true(hasattr(art, 'id'))
        self.type(uuid.UUID, art.id)
        self.zero(art.brokenrules)

    # Test str properties #
    def it_calls_str_property_on_entity(self):
        art = artist()

        self.true(hasattr(art, 'firstname'))
        self.none(art.firstname)
        self.zero(art.brokenrules)

    def it_calls_str_property_with_default_on_entity(self):
        # Test where the default is None
        class persons(orm.entities):
            pass

        class person(orm.entity):
            firstname = orm.fieldmapping(str)

        p = person()

        self.true(hasattr(p, 'firstname'))
        self.none(p.firstname)
        self.zero(p.brokenrules)

        # Test where the default is a random string
        guid = uuid4().hex
        class person(orm.entity):
            firstname = orm.fieldmapping(str, default=guid)

        p = person()

        self.true(hasattr(p, 'firstname'))
        self.type(str, p.firstname)
        self.eq(guid, p.firstname)
        self.zero(p.brokenrules)

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

    def it_breaks_fits_rule_of_str_property_on_entity(self):

        # Without specifying a default, the string should be no longer than
        # 255 in len().
        class persons(orm.entities):
            pass

        class person(orm.entity):
            firstname = orm.fieldmapping(str)

        p = person()

        p.firstname = 'x' * 256
        self.one(p.brokenrules)
        self.broken(p, 'firstname', 'fits')

        p.firstname = 'x' * 255
        self.zero(p.brokenrules)

        # Specify a max
        max = 123
        class person(orm.entity):
            firstname = orm.fieldmapping(str, max=max)

        p = person()

        p.firstname = 'x' * (max + 1)
        self.one(p.brokenrules)
        self.broken(p, 'firstname', 'fits')

        p.firstname = 'x' * max
        self.zero(p.brokenrules)

    def it_breaks_full_rule_of_str_property_on_entity(self):

        # Without specifying a default, the string should be no longer than
        # 255 in len().
        class persons(orm.entities):
            pass

        class person(orm.entity):
            firstname = orm.fieldmapping(str)

        # By default, str properties should except None and whitespace
        p = person()
        for v in [None, '', ' \t\n']:
            p.firstname = v
            self.zero(p.brokenrules)

    def it_calls_save_on_entity(self):
        art = artist()

        # Test creating and retrieving an entity
        # TODO Test more property types when they become available.
        art.firstname = uuid4().hex
        art.lastname  = uuid4().hex

        self.true(art.orm.isnew)
        self.false(art.orm.isdirty)

        # TODO Test chrons
        art.save()

        self.false(art.orm.isnew)
        self.false(art.orm.isdirty)

        art1 = artist(art.id)

        self.false(art1.orm.isnew)
        self.false(art1.orm.isdirty)

        for map in art1.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(art, map.name), getattr(art1, map.name))

        # Test changing, saving and retrieving an entity
        art1.firstname = uuid4().hex
        art1.lastname  = uuid4().hex

        self.false(art1.orm.isnew)
        self.true(art1.orm.isdirty)

        # Ensure that changing art1's properties don't change art's. This
        # problem is likely to not reoccure, but did come up in early
        # development.
        for prop in art.orm.properties:
            if prop == 'id':
                self.eq(getattr(art1, prop), getattr(art, prop))
            else:
                self.ne(getattr(art1, prop), getattr(art, prop))

        art1.save()

        self.false(art1.orm.isnew)
        self.false(art1.orm.isdirty)

        art2 = artist(art.id)

        for map in art2.orm.mappings:
            if isinstance(map, orm.fieldmapping):
                self.eq(getattr(art1, map.name), getattr(art2, map.name))

    def it_fails_to_save_broken_entity(self):
        art = artist()

        art.firstname = 'x' * 256
        self.broken(art, 'firstname', 'fits')

        try:
            art.save()
        except Exception as ex:
            self.type(brokenruleserror, ex)
        else:
            self.fail('Exception not thrown')

    def it_hard_deletes_entity(self):
        # TODO Invalidate art. You should be able to delete an object whether
        # or not it is valid.
        art = artist()

        art.firstname = uuid4().hex
        art.lastname  = uuid4().hex

        # TODO Test chrons
        art.save()

        art.delete()

        self.true(art.orm.isnew)
        self.false(art.orm.isdirty)
        self.false(art.orm.ismarkedfordeletion)

        self.expect(db.recordnotfounderror, lambda: artist(art.id))

    def it_deletes_from_entitys_collections(self):
        # TODO Test chron
        # Create artist with a presentation and save
        art = artist()
        pres = presentation()
        art.presentations += pres
        loc = location()
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
        art.presentations.pop()

        # Test presentations and its trash collection
        self.zero(art.presentations)
        self.one(art.presentations.orm.trash)

        self.one(art.presentations.orm.trash.first.locations)
        self.zero(art.presentations.orm.trash.first.locations.orm.trash)

        art.save()

        art = artist(art.id)
        self.zero(art.presentations)
        self.zero(art.presentations.orm.trash)

        self.expect(db.recordnotfounderror, lambda: presentation(pres.id))
        self.expect(db.recordnotfounderror, lambda: location(loc.id))

    def it_assigns_and_retrives_unicode_values_from_str_properties(self):
        # TODO
        return
        art = artist()

        art.firstname = bytes("\N{GREEK CAPITAL LETTER DELTA}", 'utf-8').decode()
        art.lastname  = bytes("\N{GREEK CAPITAL LETTER DELTA}", 'utf-8').decode()
        art.save()

        art1 = artist(art.id)

    def it_raises_exception_on_unknown_id(self):
        for cls in singer, artist:
            try:
                cls(uuid4())
            except Exception as ex:
                self.type(db.recordnotfounderror, ex)
            else:
                self.fail('Exception not thrown')

    def it_calls_dir_on_entity(self):
        # TODO Add more properties to test

        # Make sure mapped properties are returned when dir() is called.
        # Also ensure there is only one of eoach property in the directory. If
        # there are more, entitymeta may not be deleting the original property
        # from the class body.
        d = dir(artist())
        self.eq(1, d.count('firstname'))
        self.eq(1, d.count('presentations'))
        self.eq(1, d.count('artist_artifacts'))

        # TODO Make the below work
        # self.true('artifacts' in d)

    def it_calls_dir_on_entities(self):
        # TODO
        ...

    def it_calls_dir_on_association(self):
        # TODO
        # TODO Test for pseudo-collection property from associations
        ...

    def it_calls_dir_on_associations(self):
        # TODO
        ...

    # TODO
    # Test int properties #

    def it_reconnects_closed_database_connections(self):
        def art_onafterreconnect(src, eargs):
            drown()

        def drown():
            pool = db.pool.getdefault()
            for conn in pool._in + pool._out:
                conn.kill()

        # Kill all connections in and out of the pool
        drown()

        art = artist()

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
        id, art = art.id, artist()
        art.onafterreconnect += art_onafterreconnect

        self.expect(MySQLdb.OperationalError, lambda: art._load(id))

        art.onafterreconnect -= art_onafterreconnect

        self.expect(None, lambda: art._load(id))

        # Ensure that es.load() recovers correctly from a reconnect
        drown()
        arts = artists()

        arts.onafterreconnect += art_onafterreconnect
        self.expect(MySQLdb.OperationalError, lambda: arts.load('id', id))

        arts.onafterreconnect -= art_onafterreconnect
        self.expect(None, lambda: arts.load('id', id))

    def it_mysql_warnings_are_exceptions(self):
        def warn(cur):
            cur.execute('select 0/0')

        exec = db.executioner(warn)

        self.expect(_mysql_exceptions.Warning, lambda: exec.execute())

    def it_saves_multiple_graphs(self):
        art1 = artist()
        art2 = artist()
        sng = singer()

        pres     =  presentation()
        sngpres  =  presentation()
        loc      =  location()

        art1.presentations += pres
        sng.presentations += sngpres
        art1.presentations.first.locations += loc

        arts = artists()
        for _ in range(2):
            arts += artist()

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

        self.expect(db.recordnotfounderror, lambda: presentation(pres.id))
        self.expect(db.recordnotfounderror, lambda: location(loc.id))

        for e in art1 + art2 + arts + sng:
            e.delete()
            self.expect(db.recordnotfounderror, lambda: artist(pres.id))

        arts.save(art1, art2, sng)

        for e in art1 + art2 + arts + sng:
            self.expect(None, lambda: artist(e.id))

    def it_rollsback_save_of_entities(self):
        # Create two artists
        pres = presentation()
        art = artist()
        art.presentations += pres

        arts = artists()

        for _ in range(2):
            arts += artist()
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
        sng = singer()
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
            sngs += singer()
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
            sngs += singer()
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

    def it_deletes_subentities(self):
        chrons = self.chronicles

        # Create two singers
        sngs = singers()

        for _ in range(2):
            sngs += singer()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex
        
        sngs.save()

        sng = sngs.shift()

        self.one(sngs)
        self.one(sngs.orm.trash)

        chrons.clear()
        sngs.save()

        self.two(chrons)
        self.eq(chrons.where('entity', sng).first.op, 'delete')
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'delete')

        self.expect(db.recordnotfounderror, lambda: singer(sng.id))
        self.expect(db.recordnotfounderror, lambda: artist(sng.orm.super.id))
        
        # Ensure the remaining singer still exists in database
        self.expect(None, lambda: singer(sngs.first.id))
        self.expect(None, lambda: artist(sngs.first.orm.super.id))


    def subentity_contains_reference_to_composite(self):
        chrons = self.chronicles

        sng = singer()

        for _ in range(2):
            sng.presentations += presentation()

            for _ in range(2):
                sng.presentations.last.locations += location()

        sng.save()

        for sng in (sng, singer(sng.id)):
            for pres in sng.presentations:
                chrons.clear()
                self.is_(sng, pres.singer)
                self.zero(chrons)

                for loc in pres.locations:
                    chrons.clear()
                    self.is_(pres, loc.presentation)
                    self.zero(chrons)

        sng = singer()
        for _ in range(2):
            sng.concerts += concert()

            # TODO Add deeply-nested collection, i.e.,
            # sng.concerts.first.locations += location()

        ##
        orm = concert().orm
        B()
        print(orm.mappings)
        conc = sng.concerts.first
        conc.brokenrules
        ##

        sng.save()

        for sng in (sng, singer(sng.id)):
            for conc in sng.concerts:
                chrons.clear()
                self.is_(sng, conc.singer)
                self.zero(chrons)


    def it_loads_and_saves_subentities_constituents(self):
        chrons = self.chronicles

        # Ensure that a new composite has a constituent object with zero
        # elements
        sng = singer()
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

        sng = singer()

        sng.presentations += presentation()
        sng.presentations += presentation()

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

        self.eq(chrons.where('entity', press.first).first.op, 'retrieve')
        self.eq(chrons.where('entity', press.second).first.op, 'retrieve')

        sng.presentations.sort('id')
        sng1.presentations.sort('id')
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
                pres.locations += location()

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

        sng.presentations.sort('id')
        sng1.presentations.sort('id')
        for pres, pres1 in zip(sng.presentations, sng1.presentations):

            pres.locations.sort('id')

            chrons.clear()
            pres1.locations.sort('id')

            self.two(chrons)
            locs = pres1.locations
            self.eq(chrons.where('entity', locs.first).first.op, 'retrieve')
            self.eq(chrons.where('entity', locs.second).first.op, 'retrieve')

            for loc, loc1 in zip(pres.locations, pres1.locations):
                for map in loc.orm.mappings:
                    if isinstance(map, orm.fieldmapping):
                        self.eq(getattr(loc, map.name), getattr(loc1, map.name))
            
                self.is_(pres1, loc1.presentation)

        # Test appending a collection of constituents to a constituents
        # collection. Save, reload and test.
        sng = singer()
        press = presentations()

        for _ in range(2):
            press += presentation()

        sng.presentations += press

        for i in range(2):
            if i:
                sng.save()
                sng = singer(sng.id)

            self.eq(press.count, sng.presentations.count)

            for pres in sng.presentations:
                self.is_(sng, pres.singer)
                self.is_(sng.orm.super, pres.artist)

    def it_updates_subentities_constituents_properties(self):
        chrons = self.chronicles
        sng = singer()

        for _ in range(2):
            sng.presentations += presentation()
            sng.presentations.last.name = uuid4().hex

            for _ in range(2):
                sng.presentations.last.locations += location()
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
        press = (sng.presentations, sng1.presentations, sng2.presentations)
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

    def it_saves_and_loads_subentity_constituent(self):
        chrons = self.chronicles

        # Make sure the constituent is None for new composites
        pres = presentation()

        chrons.clear()
        self.none(pres.artist)
        self.zero(chrons)

        self.broken(pres, 'artistid', 'full')

        # Test setting an entity constituent then test saving and loading
        sng = singer()
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

        sng1 = singer()
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
       
        loc = location()
        self.none(loc.presentation)

        loc.presentation = pres = presentation()
        self.is_(pres, loc.presentation)

        chrons.clear()
        self.none(loc.presentation.artist)
        self.zero(chrons)

        loc.presentation.artist = sng = singer()
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
        loc1.presentation.artist = sng1 = singer()

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

    def subentity_constituents_break_entity(self):
        pres = presentation()
        pres.artist = singer()

        # Break rule that art.firstname should be a str
        pres.artist.firstname = int() # Break

        self.one(pres.brokenrules)
        self.broken(pres, 'firstname', 'valid')

        pres.artist.firstname = str() # Unbreak
        self.zero(pres.brokenrules)

        loc = location()
        loc.description = int() # break
        loc.presentation = presentation()
        loc.presentation.name = int() # break
        loc.presentation.artist = singer()
        loc.presentation.artist.firstname = int() # break

        self.three(loc.brokenrules)
        for prop in 'description', 'name', 'firstname':
            self.broken(loc, prop, 'valid')

    def it_rollsback_save_of_subentity_with_broken_constituents(self):
        sng = singer()

        sng.presentations += presentation()
        sng.presentations.last.name = uuid4().hex

        sng.presentations += presentation()
        sng.presentations.last.name = uuid4().hex

        # Cause the last presentation's invocation of save() to raise an
        # Exception to cause a rollback
        sng.presentations.last._save = lambda cur, followentitymapping: 1/0

        # Save expecting the ZeroDivisionError
        self.expect(ZeroDivisionError, lambda: sng.save())

        # Ensure state of sng was restored to original
        self.true(sng.orm.isnew)
        self.false(sng.orm.isdirty)
        self.false(sng.orm.ismarkedfordeletion)

        # Ensure singer wasn't saved
        self.expect(db.recordnotfounderror, lambda: singer(sng.id))

        # For each presentations, ensure state was not modified and no presentation 
        # object was saved.
        for pres in sng.presentations:
            self.true(pres.orm.isnew)
            self.false(pres.orm.isdirty)
            self.false(pres.orm.ismarkedfordeletion)
            self.expect(db.recordnotfounderror, lambda: presentation(pres.id))

    def it_deletes_subentities(self):
        # Create two artists
        sngs = singers()

        for _ in range(2):
            sngs += singer()
            sngs.last.firstname = uuid4().hex
            sngs.last.lastname = uuid4().hex
        
        # TODO Test chrons
        sngs.save()

        art = sngs.shift()
        self.one(sngs)
        self.one(sngs.orm.trash)

        sngs.save()

        self.expect(db.recordnotfounderror, lambda: singer(art.id))
        
        # Ensure the remaining singer still exists in database
        self.expect(None, lambda: singer(sngs.first.id))

    def it_doesnt_needlessly_save_subentity(self):
        chrons = self.chronicles

        sng = singer()
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
        sng.presentations += presentation()
        
        for i in range(2):
            chrons.clear()
            sng.save()

            if i == 0:
                self.one(chrons)
                pres = sng.presentations.last
                self.eq(chrons.where('entity', pres).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

        # Test deeply-nested (>2) constituents
        sng.presentations.last.locations += location()

        for i in range(2):
            chrons.clear()
            sng.save()

            if i == 0:
                self.one(chrons)
                loc = sng.presentations.last.locations.last
                self.eq(chrons.where('entity', loc).first.op, 'create')
            elif i == 1:
                self.zero(chrons)

    def it_calls_id_on_subentity(self):
        sng = singer()

        self.true(hasattr(sng, 'id'))
        self.type(uuid.UUID, sng.id)
        self.zero(sng.brokenrules)

    def it_calls_str_property_on_subentity(self):
        sng = singer()

        self.true(hasattr(sng, 'firstname'))
        self.none(sng.firstname)
        self.zero(sng.brokenrules)

    def it_calls_str_property_with_default_on_subentity(self):
        # Test where the default is None
        class persons(orm.entities):
            pass

        class person(orm.entity):
            firstname = orm.fieldmapping(str)

        class subpersons(orm.entities):
            pass

        class subperson(person):
            pass

        p = subperson()

        self.true(hasattr(p, 'firstname'))
        self.none(p.firstname)
        self.zero(p.brokenrules)

        # Test where the default is a random string
        guid = uuid4().hex
        class person(orm.entity):
            firstname = orm.fieldmapping(str, default=guid)

        class subperson(person):
            pass

        p = subperson()

        self.true(hasattr(p, 'firstname'))
        self.type(str, p.firstname)
        self.eq(guid, p.firstname)
        self.zero(p.brokenrules)

    def it_calls_str_propertys_setter_on_subentity(self):
        class persons(orm.entities):
            pass

        class subpersons(orm.entities):
            pass

        class person(orm.entity):
            firstname = orm.fieldmapping(str)

        class subperson(person):
            pass

        p = subperson()

        uuid = uuid4().hex
        p.firstname = uuid

        self.eq(uuid, p.firstname)
        self.zero(p.brokenrules)

        # Ensure whitespace in strip()ed from str values.
        p.firstname = ' \n\t' + uuid + ' \n\t'
        self.eq(uuid, p.firstname)
        self.zero(p.brokenrules)

    
    def it_calls_save_on_subentity(self):
        chrons = self.chronicles
        sng = singer()

        # Test creating and retrieving an entity
        # TODO Test more property types when they become available.
        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.voice  = uuid4().hex

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

        self.eq((False, True, False), sng1.orm.persistencestate)

        # Ensure that changing sng1's properties don't change sng's. This
        # problem is likely to not reoccur, but did come up in early
        # development.

        for prop in sng.orm.properties:
            if prop == 'id':
                self.eq(getattr(sng1, prop), getattr(sng, prop))
            else:
                self.ne(getattr(sng1, prop), getattr(sng, prop))

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
                self.type(brokenruleserror, ex)
            else:
                self.fail('Exception not thrown')

    def it_hard_deletes_subentity(self):
        chrons = self.chronicles
        sng = singer()

        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex

        sng.save()

        chrons.clear()
        sng.delete()
        self.two(chrons)
        self.eq(chrons.where('entity', sng).first.op,           'delete')
        self.eq(chrons.where('entity', sng.orm.super).first.op, 'delete')

        self.eq((True, False, False), sng.orm.persistencestate)

        self.expect(db.recordnotfounderror, lambda: artist(sng.id))
        self.expect(db.recordnotfounderror, lambda: singer(sng.id))

        # Ensure that an invalid sng can be deleted
        sng = singer()

        sng.firstname = uuid4().hex
        sng.lastname  = uuid4().hex
        sng.save()

        sng.lastname  = 'X' * 256 # Invalidate

        sng.delete()
        self.expect(db.recordnotfounderror, lambda: artist(sng.id))
        self.expect(db.recordnotfounderror, lambda: singer(sng.id))

    def it_deletes_from_subentitys_collections(self):
        chrons = self.chronicles

        # Create singer with a presentation and save
        sng = singer()
        pres = presentation()
        sng.presentations += pres
        loc = location()
        sng.presentations.last.locations += loc
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
        self.eq(chrons.where('entity', rmsng).first.op, 'delete')
        self.eq(chrons.where('entity', rmsng.locations.first).first.op, 'delete')
        
        sng = singer(sng.id)
        self.zero(sng.presentations)
        self.zero(sng.presentations.orm.trash)

        self.expect(db.recordnotfounderror, lambda: presentation(pres.id))
        self.expect(db.recordnotfounderror, lambda: location(loc.id))

    def it_calls_dir_on_subentity(self):
        # TODO Add more properties to test
        # Make sure mapped properties show are returned when dir() is called 

        # Also ensure there is only one of eoach property in the directory. If
        # there are more, entitymeta may not be deleting the original property
        # from the class body.
        d = dir(singer())
        self.eq(1, d.count('firstname'))
        self.eq(1, d.count('voice'))
        self.eq(1, d.count('presentations'))
        self.eq(1, d.count('artist_artifacts'))
        # TODO Make the below work
        # self.eq(1, d.count('artifacts'))

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
        except brokenruleserror as ex:
            self.assertIs(rev, ex.object)
        except Exception as ex:
            msg = ('brokenruleserror expected however a different exception '
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
            self.type(db.recordnotfounderror, ex)
        else:
            self.fail('Exception not thrown')

        bl = blog()
        bl.slug = uuid4().hex
        bl.description = 'This is not the correct blog'
        bl.save()
        try:
            blogpost(slug, bl)
        except Exception as ex:
            self.type(db.recordnotfounderror, ex)
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
        except brokenruleserror:
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
        except brokenruleserror:
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
        except brokenruleserror:
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
        except brokenruleserror as ex:
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
        except brokenruleserror as ex:
            self.assertIs(rev, ex.object)
        except Exception as ex:
            msg = ('brokenruleserror expected however a different exception '
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
        except brokenruleserror:
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

        us.sort('id'); p.users.sort('id')
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

        # TODO BUG Appending a new user, sorting by id, then shift()ing results
        # in the new user being immediately removed - so basically nothing is
        # happening here. The same thing happens below with p.users. This bug
        # makes the test work.  It conceals the fact that shift()ing doesn't
        # mark the user entity for deletion.
        us += u
        us.sort('id')
        us.shift()

        ## Add to p.users, sort and shift. We we are adding one and removing another.
        p.users += u
        p.users.sort('id')
        p.users.shift()

        self.assertTwo(p.users)
        for u, pu in zip(us, p.users):
            self.assertEq(u.service,    pu.service)
            self.assertEq(u.name,       pu.name)

        p.save()

        p = person(p.id)

        self.assertTwo(p.users)

        us.sort('id'); p.users.sort('id')
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
        except brokenruleserror as ex:
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

def main():
    p = argparse.ArgumentParser()
    p.add_argument('testunit',  help='The test class or method to run',  nargs='?')
    p.add_argument('-b', '--break-on-exception', action='store_true', dest='breakonexception')
    args = p.parse_args()

    t = testers()
    t.breakonexception = args.breakonexception
    t.oninvoketest += lambda src, eargs: print('# ', end='', flush=True)
    t.oninvoketest += lambda src, eargs: print(eargs.method[0], flush=True)
    t.run(args.testunit)
    print(t)

main()

