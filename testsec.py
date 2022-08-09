#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022                 #
########################################################################

from dbg import PM, B
from func import enumerate
import db
import ecommerce
import entities
import orm
import party
import tester
import uuid

import apriori; apriori.model()

class problems(orm.entities):
    pass

class problem(orm.entity):
    def creatability(self):
        raise Exception('I made poopies')

    def retrievability(self):
        raise Exception('I made poopies')

    def updatability(self):
        raise Exception('I made poopies')

    def retrievability(self):
        raise Exception('I made poopies')

    name = str, 0

class uncreatables(orm.entities):
    pass

class uncreatable(orm.entity):
    pass

class unretrievables(orm.entities):
    pass

class unretrievable(orm.entity):
    @property
    def creatability(self):
        return orm.violations()

class unupdatables(orm.entities):
    pass

class unupdatable(orm.entity):
    name = str, 0
    @property
    def creatability(self):
        return orm.violations()

    @property
    def retrievability(self):
        return orm.violations()

class undeletables(orm.entities):
    pass

class undeletable(orm.entity):
    @property
    def creatability(self):
        return orm.violations()

    @property
    def retrievability(self):
        return orm.violations()

class projects(orm.entities):
    pass

class project(orm.entity):
    pass

class systems(orm.entities):
    pass

class system(orm.entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('name', None)

    @property
    def creatability(self):
        vs = orm.violations()
        usrs = 'bgates', 'sballmer'
        if orm.security().owner.name not in usrs:
            vs += f'Only {usrs} can create systems'
        return vs

    @property
    def retrievability(self):
        vs = orm.violations(entity=self)

        usr = orm.security().owner

        managers = 'bgates', 'sballmer', 'snadella'

        if self.name.startswith('Even'):
            if usr.name not in managers[::2]:
                vs += (
                    'Systems that start with "Even" can only be '
                    'retrieved by bgates and snadella'
                )

        elif self.name.startswith('Odd'):
            if usr.name not in managers[1::2]:
                vs += (
                    'Systems that start with "Even" can only be '
                    'retrieved by sballmer'
                )
            
        return vs

    @property
    def updatability(self):
        vs = orm.violations()
        usrs = 'bgates', 'sballmer'
        if orm.security().owner.name not in usrs:
            vs += f'Only {usrs} can update systems'
        return vs

    @property
    def deletability(self):
        vs = orm.violations()
        if orm.security().owner.name != 'bgates':
            vs += f'Only bgates can delete systems'
        return vs

    name = str

class engineers(orm.entities):
    pass

class engineer(orm.entity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('name', None)
        self.orm.default('skills', None)
        self.orm.default('bio', None)

    name = str
    @classmethod
    def getvalid(cls):
        return cls()

    skills = str

    systems = systems
    
    bio = str, orm.fulltext

    @property
    def creatability(self):
        vs = orm.violations(entity=self)
        if orm.security().owner.name != 'bgates':
            vs += "User must be 'bgates'"

        return vs

    @property
    def retrievability(self):
        vs = orm.violations()
        usr = orm.security().owner

        managers = 'bgates', 'sballmer', 'snadella'

        if self.name.startswith('Even'):
            if usr.name not in managers[::2]:
                vs += 'system must be retrieved by bgates or snadella'
                
        elif self.name.startswith('Odd'):
            if usr.name not in managers[1::2]:
                vs += 'system must be retrieved by sballmer'
        else:
            if usr.name not in managers:
                vs += 'system must be retrieved by a manager'

        return vs

    @property
    def updatability(self):
        vs = orm.violations()
        if orm.security().owner.name != 'bgates':
            vs += 'Only bgates can update engineer'
        return vs

    @property
    def deletability(self):
        vs = orm.violations()
        if orm.security().owner.name != 'bgates':
            vs += 'Only bgates can delete engineer'
        return vs

class hackers(engineers):
    pass

class hacker(engineer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('handle', None)
    handle = str

class phreaks(hackers):
    pass

class phreak(hacker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('boxes', None)

    boxes = str

class engineer_projects(orm.associations):
    pass

class engineer_project(orm.association):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.orm.default('name', None)
    name = str
    engineer = engineer
    project = project

class authorization(tester.tester):
    """ Tests the accessibility properties of entities (creatability,
    retrievability, updatability and deletability).
    """ 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        mods = ('party', 'apriori', 'ecommerce', 'file')
        for e in orm.orm.getentityclasses(includeassociations=True):
            if e.__module__ in mods:
                e.orm.recreate()

        orm.orm.recreate(
            engineer,     hacker,         phreak,
            system,       project,        engineer_project,
            uncreatable,  unretrievable,  unupdatables,
            undeletable,  problem,
        )

        sec = orm.security()
        with orm.override():
            root = ecommerce.users.root
            sec.owner = root

            com = party.company(name='Microsoft')
            orm.security().proprietor = com
            com.save()

        with orm.sudo():
            self.bgates = ecommerce.user(name='bgates')
            self.bgates.save()

            self.sballmer = ecommerce.user(name='sballmer')
            self.sballmer.save()

            self.snadella = ecommerce.user(name='snadella')
            self.snadella.save()

        sec.owner = None

        orm.security().override = False

    ''' CREATABILITY '''
    def it_cant_create_entity(self):
        try:
            with orm.su(self.bgates):
                uncreatable().save()
        except orm.AuthorizationError as ex:
            self.eq('c', ex.crud)
            self.type(uncreatable, ex.entity)
        except Exception as ex:
            self.fail(f'Wrong exception type: {ex}')
        else:
            self.fail('No exception')
            
    def it_creates_entity(self):
        with orm.sudo():
            bgates = ecommerce.user(name='bgates')
            bgates.save()

            sballmer = ecommerce.user(name='sballmer')
            sballmer.save()

        with orm.su(bgates):
            eng = engineer(name='Steve')
            self.expect(None, eng.save)
            self.eq((False, False, False), eng.orm.persistencestate)

        with orm.sudo():
            eng1 = eng.orm.reloaded()
            self.eq(eng.id, eng1.id)
            self.eq(bgates.id, eng1.owner.id)

        with orm.su(sballmer):
            eng = engineer(name='Steve')
            try:
                eng.save()
            except orm.AuthorizationError as ex:
                self.eq(
                    "User must be 'bgates'",
                    ex.violations.first.message
                )
            except Exception:
                self.fail('AuthorizationError not raised')
                
            else:
                self.fail('No exception raised')

            self.eq((True, False, False), eng.orm.persistencestate)

        with orm.sudo():
            self.expect(db.RecordNotFoundError, eng.orm.reloaded)

    def it_creates_constituents(self):
        with orm.sudo():
            eng = engineer()
            eng.save()

        with orm.su(self.bgates):
            eng.systems += system(name='Even')
            eng.save()

        with orm.su(self.snadella):
            eng.systems += system(name='Even')
            try:
                eng.save()
            except orm.AuthorizationError as ex:
                self.eq('c', ex.crud)
                self.one(ex.violations)
                self.is_(eng.systems.last, ex.entity)
            except Exception as ex:
                self.fail(f'Wrong exception type {ex}')
            else:
                self.fail('No exception')

    def it_allows_root_to_create_all(self):
        clss = (
            engineer, hacker, phreak, system, uncreatable,
            uncreatable, unretrievable, unupdatable, undeletable
        )

        with orm.sudo():
            for cls in clss:
                e = cls()
                e.save()
                e1 = e.orm.reloaded()
                self.eq(e.id, e1.id)

    def it_disallows_proprietor_creating_other_proprietors_record(self):
        assert orm.security().proprietor.name == 'Microsoft'

        with orm.su(self.bgates):
            eng = engineer()

            assert eng.proprietor.name == 'Microsoft'

            with orm.proprietor(party.company.carapacian):
                self.expect(orm.ProprietorError, eng.save)
        

    ''' RETRIEVABILITY '''
    def it_cant_retrieve_entity(self):
        with orm.su(self.bgates):
            un = unretrievable()
            un.save()
            try:
                unretrievable(un.id)
            except orm.AuthorizationError as ex:
                self.eq('r', ex.crud)
                self.type(unretrievable, ex.entity)
            except Exception as ex:
                self.fail(f'Wrong exception type: {ex}')
            else:
                self.fail('No exception')
            
    def it_allows_root_to_retrieve_all(self):
        systems.orm.truncate()

        with orm.sudo():
            bgates = ecommerce.user(name='bgates')
            bgates.save()

        with orm.su(bgates):
            engs = engineers()

            for name in ('Even', 'Odd', 'Derp'):
                engs += engineer(name=name)

                for name in ('Even', 'Odd', 'Derp'):
                    engs.last.systems += system(name=name)

            engs.save()

            with orm.sudo():
                for eng in engs:
                    eng = self.expect(None, eng.orm.reloaded)

                    syss = eng.systems

                    self.three(syss)

                    self.eq(
                        ['Derp', 'Even', 'Odd'],
                        sorted(syss.pluck('name'))
                    )

    def it_retrieves_aggregate_values_on_classes(self):
        """ TODO """

    def it_retrieves_entity_by_id(self):
        bgates = ecommerce.user(name='bgates')
        fdrake = ecommerce.user(name='fdrake')

        with orm.sudo():
            eng = engineer.getvalid()
            eng.name = 'Steve'
            eng.save()

        with orm.su(bgates):
            try:
                eng1 = engineer(eng.id)
            except orm.AuthorizationError:
                self.fail(f'bgates should be able to access {eng.id}')
            else:
                self.eq(eng.id, eng1.id)

        with orm.su(fdrake):
            self.expect(
                orm.AuthorizationError, lambda: engineer(eng.id)
            )

    def it_cant_retrieve_entity_by_id(self):
        with orm.sudo():
            eng = engineer.getvalid()
            eng.name = 'Steve'
            eng.save()

        fdrake = ecommerce.user(name='fdrake')

        ''' Access by id '''
        with orm.su(fdrake):
            try:
                eng1 = engineer(eng.id)
            except orm.AuthorizationError as err:
                self.type(engineer, err.entity)

                msgs = err.message.split(':')
                self.eq(err.entity.id.hex, msgs.pop())
                self.eq('Cannot access engineer', msgs.pop())
                self.eq('r', err.crud)

    def it_retrieves_entities(self):
        engineers.orm.truncate()

        bgates = ecommerce.user(name='bgates')
        sballmer = ecommerce.user(name='sballmer')

        # Create 4 engineers. Two will have 'Even' in their name and two
        # will have 'Odd' in there name. Due to the contrived
        # authorization rules for `engineer` (engineer.isretrievable)
        # bgates will be authorized to retrieved the 'Even' ones and
        # sballmer will be able to retrieve the 'Odd' ones.
        with orm.sudo():
            for i, _ in enumerate(range(4)):
                if i.even:
                    engineer(name=f"Even {i}").save()
                else:
                    engineer(name=f"Odd {i}").save()

        for usr, parity in ( (bgates, 'Even'), (sballmer, 'Odd') ):
            with orm.su(usr):
                engs = engineers("skills is %s", (None,))

                self.two(engs)

                for eng in engs:
                    self.startswith(parity, eng.name)

    def it_retrieves_constituents(self):
        systems.orm.truncate()

        with orm.sudo():
            bgates = ecommerce.user(name='bgates')
            sballmer = ecommerce.user(name='sballmer')
            bgates.save()
            sballmer.save()

        with orm.su(bgates):
            eng = engineer(name='Even')
            eng.save()

            for i, _ in enumerate(range(4)):
                if i.even:
                    with orm.su(bgates):
                        eng.systems += system(name=f"Even {i}")
                        eng.save()
                else:
                    with orm.su(sballmer):
                        eng.systems += system(name=f"Odd {i}")
                        eng.save()

        for usr, parity in ((bgates, 'Even'), (sballmer, 'Odd')):

            with orm.sudo():
                eng = eng.orm.reloaded()

            with orm.su(usr):
                syss = eng.systems
                self.two(syss)

                for sys in syss:
                    self.startswith(parity, sys.name)

    ''' UPDATABILITY '''
    def it_allows_root_to_update_all(self):
        clss = (engineer, hacker, phreak, system)
        with orm.sudo():
            for cls in clss:
                e = cls()
                e.name = 'one'
                e.save()

                e1 = e.orm.reloaded()
                e1.name = 'two'
                e1.save()

                e1 = e1.orm.reloaded()

                self.eq(e.id, e1.id)
                self.eq('two', e1.name)

    def it_cant_update_entity(self):
        with orm.su(self.bgates):
            un = unupdatable()
            un.name = 'I will not be updated'
            un.save()

            un = unupdatable(un.id)
            un.name = 'Will I be updated?'
            try:
                un.save()
            except orm.AuthorizationError as ex:
                self.eq('u', ex.crud)
                self.type(unupdatable, ex.entity)
            except Exception as ex:
                self.fail(f'Wrong exception type: {ex}')
            else:
                self.fail('No exception')

    def it_can_update_entity(self):
        with orm.su(self.bgates):
            eng = engineer()
            eng.name = "I should be updatable"
            eng.save()

            eng = eng.orm.reloaded()
            eng.name = 'I am being updated'
            eng.save()

        eng.name = 'sballmer should not be able to update me'
        with orm.su(self.sballmer):
            try:
                eng.save()
            except orm.AuthorizationError as ex:
                self.eq('u', ex.crud)
                self.is_(eng, ex.entity)
                self.one(ex.violations)
            except Exception as ex:
                self.fail(f'Wrong exception type: {ex}')
            else:
                self.fail('No exception')

    def it_can_update_constituents(self):
        with orm.sudo():
            eng = engineer()
            for _ in range(2):
                eng.systems += system(name='one')
            eng.save()
            eng = eng.orm.reloaded()

        with orm.su(self.bgates):
            eng.systems.sort()
            eng.systems.first.name = 'two'
            eng.save()

        with orm.su(self.snadella):
            eng.systems.second.name = 'two'
            try:
                eng.save()
            except orm.AuthorizationError as ex:
                self.eq('u', ex.crud)
                self.is_(eng.systems.second, ex.entity)
                self.one(ex.violations)
            except Exception as ex:
                self.fail(f'Wrong exception type: {ex}')
            else:
                self.fail('No exception')

    ''' DELETABILITY '''
    def it_allows_root_to_delete_all(self):
        with orm.su(self.bgates):
            eng = engineer()
            eng.save()

        with orm.sudo():
            self.expect(None, eng.delete)
            self.expect(db.RecordNotFoundError, eng.orm.reloaded)

    def it_can_delete_entity(self):
        with orm.sudo():
            eng = engineer()
            eng.save()

        with orm.su(self.bgates):
            eng.delete()

        with orm.sudo():
            self.expect(db.RecordNotFoundError, eng.orm.reloaded)

            eng = engineer()
            eng.save()

        with orm.su(self.sballmer):
            try:
                eng.delete()
            except orm.AuthorizationError as ex:
                self.eq('d', ex.crud)
                self.is_(eng, ex.entity)
                self.one(ex.violations)
                self.eq(
                    'Only bgates can delete engineer',
                    ex.violations.first.message,
                )
            except Exception as ex:
                self.fail(f'Wrong exception type: {ex}')
            else:
                self.fail('No exception')

        with orm.sudo():
            self.expect(None, eng.orm.reloaded)

    def it_cant_delete_entity(self):
        with orm.su(self.bgates):
            un = undeletable()
            un.save()

            try:
                un.delete()
            except orm.AuthorizationError as ex:
                self.eq('d', ex.crud)
                self.type(undeletable, ex.entity)
            except Exception as ex:
                self.fail(f'Wrong exception type: {ex}')
            else:
                self.fail('No exception')

    def it_deletes_constituents(self):
        with orm.sudo():
            eng = engineer()
            eng.systems += system()
            eng.systems += system()
            eng.save()

        with orm.su(self.bgates):
            sys = eng.systems.pop()
            eng.save()

        with orm.sudo():
            self.expect(db.RecordNotFoundError, sys.orm.reloaded)

        with orm.su(self.sballmer):
            sys = eng.systems.pop()
            try:
                eng.save()
            except orm.AuthorizationError as ex:
                self.eq('d', ex.crud)
                self.is_(sys, ex.entity)
                self.eq(
                    'Only bgates can delete systems',
                    ex.violations.first.message,
                )
            except Exception as ex:
                self.fail(f'Wrong exception type: {ex}')
            else:
                self.fail('No exception')

        with orm.sudo():
            self.expect(None, sys.orm.reloaded)

    ''' orm.override '''
    def it_creates_and_retrieves_with_override(self):
        orm.security().owner = self.bgates

        with orm.override():
            pr = problem()
            self.expect(None, pr.save)
            pr1 = self.expect(None, pr.orm.reloaded)

    def it_retrieves_constituents_with_override(self):
        orm.security().owner = self.bgates

        with orm.su(self.bgates):
            eng = engineer(name='Even')
            eng.systems += system(name='Even')
            eng.save()

        with orm.su(self.sballmer):
            eng.systems += system(name='Even')
            eng.save()

        with orm.su(self.bgates):
            eng = eng.orm.reloaded()

        with orm.override():
            with orm.su(self.sballmer):
                self.two(eng.systems)

        with orm.su(self.bgates):
            eng = eng.orm.reloaded()

        with orm.override(False):
            with orm.su(self.sballmer):
                self.zero(eng.systems)

    def it_updates_with_override(self):
        with orm.sudo():
            pr = problem()
            pr.name = 'old'
            pr.save()
            pr = pr.orm.reloaded()

        with orm.override():
            pr.name = 'new'
            self.expect(None, pr.save)
            pr = pr.orm.reloaded()
            self.eq('new', pr.name)

    def it_deletes_with_override(self):
        with orm.sudo():
            pr = problem()
            pr.name = 'old'
            pr.save()
            pr = pr.orm.reloaded()

        with orm.override():
            self.expect(None, pr.delete)
            self.expect(db.RecordNotFoundError, pr.orm.reloaded)

class owner(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        orm.security().override = True

        orm.orm.recreate(
            engineer,  
        )

        for e in orm.orm.getentityclasses(includeassociations=True):
            if e.__module__ in ('party', 'apriori', 'ecommerce'):
                e.orm.recreate()

    def it_calls_owner(self):
        def create_owner(name):
            with orm.sudo():
                own = ecommerce.user(name=name)
                own.save()
                return own

        ''' New entity gets owner '''
        own = create_owner('owner')
        orm.security().owner = own
        eng = engineer()
        self.is_(orm.security().owner, eng.owner)
        eng.save()
        self.eq(orm.security().owner.id, eng.owner.id)

        ''' Change orm owner: existing entity preserves owner '''
        own1 = create_owner('owner1')
        orm.security().owner = own1

        eng = eng.orm.reloaded()
        self.eq(own.id, eng.owner.id)
        self.ne(own1.id, eng.owner.id)

        ''' 
        Change orm owner: existing entity preserves owner after
        update
        '''
        own2 = ecommerce.user(name='owner1')
        orm.security().owner = own2

        eng.name = 'new name'
        eng.save()

        eng = eng.orm.reloaded()

        self.eq(own.id, eng.owner.id)
        self.eq('new name', eng.name)
        self.ne(own2.id, eng.owner.id)

    def it_cant_save_with_no_owner(self):
        # Ensure owner is None
        orm.security().owner = None

        # We should get a validation error when saving
        eng = engineer()
        self.expect(entities.BrokenRulesError, eng.save)
        self.one(eng.brokenrules)
        self.eq('valid', eng.brokenrules.first.type)
        self.is_(eng, eng.brokenrules.first.entity)

class root(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orm.security().override = True
        if self.rebuildtables:
            orm.orm.recreate(
                ecommerce.user,
            )

    def it_cannot_create_multiple_root_users(self):
        # TODO:887c6605 Lift restriction on multiple users being named
        # root. Now that we have root's id hardcoded, we can rely on
        # that as the identifier of the system's root.
        ecommerce.user.orm.truncate()
        root = ecommerce.user(name='root')
        self.expect(None, root.save)

        root1 = ecommerce.user(name='root')
        self.expect(entities.BrokenRulesError, root1.save)
        self.one(root1.brokenrules)
        br = root1.brokenrules.first
        self.eq('valid', br.type)
        self.is_(root1, br.entity)

    def it_assigns_root_a_consistent_id(self):
        Id = uuid.UUID(hex='93a7930b-2ae4-402a-8c77-011f0ffca9ce')

        for _ in range(2):
            ecommerce.user.orm.truncate()
            ecommerce.users._root = None

            self.eq(Id, ecommerce.users.root.id)

            ecommerce.user.orm.truncate()

            self.eq(Id, ecommerce.users.root.id)

class proprietor(tester.tester):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        orm.orm.recreate(
            engineer,  hacker,   phreak,
            system,    project,  engineer_project
        )

        for e in orm.orm.getentityclasses(includeassociations=True):
            if e.__module__ in ('party', 'apriori'):
                e.orm.recreate()

        orm.security().owner = ecommerce.users.root

        with orm.sudo():
            self.bgates = ecommerce.user(name='bgates')
            self.emusk = ecommerce.user(name='emusk')
            self.bgates.save(self.emusk)

    def it_creates_associations(self):
        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        orm.security().proprietor = tsla
        eng = engineer()
        proj = project()
        e_p = engineer_project(
            project = proj
        )

        eng.engineer_projects += e_p

        self.is_(tsla, e_p.proprietor)

        eng.save()

        eng = eng.orm.reloaded()
        self.is_(tsla, eng.engineer_projects.last.proprietor)

        proj = proj.orm.reloaded()
        self.is_(tsla, proj.engineer_projects.last.proprietor)

        self.expect(None, e_p.orm.reloaded)

        orm.security().proprietor = ms
        self.expect(db.RecordNotFoundError, e_p.orm.reloaded)

        e_p.name = 'x'

        with orm.su(self.bgates):
            self.expect(orm.ProprietorError, e_p.save)
            self.expect(orm.ProprietorError, e_p.delete)

    def it_cant_load_composite(self):
        engineers.orm.truncate()
        systems.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Assign the system to a Telsa engineer
        orm.security().proprietor = tsla
        sys = system()
        sys.engineer = engineer(name='x')
        sys.save()

        # Reload the system as Tesla
        sys = sys.orm.reloaded()

        # Try to load the Tesla `engineer` composite as Microsoft. 
        orm.security().proprietor = ms
        self.expect(db.RecordNotFoundError, lambda: sys.engineer)

        # Try again to load the Tesla `engineer` composite as Tesla. 
        orm.security().proprietor = tsla
        self.notnone(sys.engineer)

    def it_deletes_entity(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create a Tesla engineers
        orm.security().proprietor = tsla
        eng = engineer(name='Tesla engineer')
        eng.save()

        # Delete it. We shouldn't get errors.
        self.expect(None, eng.delete)

        # Ensure the record has been deleted
        self.expect(db.RecordNotFoundError, eng.orm.reloaded)

        # Create another Tesla engineers
        eng = engineer(name='Tesla engineer')
        eng.save()

        # Switch proprietor to Microsoft
        orm.security().proprietor = ms

        # Delete it. Microsoft shouldn't be able to delete Tesla's
        # records so we should get errors.
        with self.bgates.su():
            self.expect(orm.ProprietorError, eng.delete)

        # Switch proprietor back to Telsa
        orm.security().proprietor = tsla

        # Ensure the record was not deleted
        self.expect(None, eng.orm.reloaded)

    def it_deletes_constituents(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create a Tesla engineers
        orm.security().proprietor = tsla
        eng = engineer(name='Tesla engineer')
        eng = engineer()
        for i in range(3):
            eng.systems += system(
                name = f'Tesla system {i}',
            )

        eng.save()

        # Create a Microsoft engineers
        orm.security().proprietor = ms
        eng = engineer(name='Microsoft engineer')
        eng = engineer()
        for i in range(3):
            eng.systems += system(
                name = f'Microsoft system {i}',
            )

        eng.save()

        # Mark the Microsoft's engineer's last system for deletion.
        eng.systems.pop()

        # In midstream, set the proprietor to Tesla. This would be a
        # mistake if a web developer were to do this, but just in case,
        # make sure that Tesla can't delete a Microsoft system.
        orm.security().proprietor = tsla

        with self.emusk.su():
            self.expect(orm.ProprietorError, eng.save)

        # Set the proprietor back to Microsoft, reload and ensure the
        # system wasn't deleted.
        orm.security().proprietor = ms
        eng = eng.orm.reloaded()
        self.three(eng.systems)

    def it_adds_proprietor_to_entity(self):
        ''' Test class (static attribute)'''
        orm.security().proprietor = None

        # Test the map
        map = engineer.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in engineer.orm.mappings 
            if x.name == 'proprietor'
        ])

        # proprietor should be a `party`
        self.is_(party.party, map.entity)

        ''' Test object '''
        eng = engineer.getvalid()

        map = eng.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.isnot(
            engineer.orm.mappings['proprietor'],
            map
        )
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in eng.orm.mappings 
            if x.name == 'proprietor'
        ])

        self.none(eng.proprietor)

        with orm.sudo():
            proprietor = party.person(name='Malcolm McLaren')

        eng.proprietor = proprietor

        eng.save()

        eng1 = eng.orm.reloaded()

        self.eq(eng.id, eng1.id)
        self.eq(eng.proprietor.id, eng1.proprietor.id)

    def it_adds_proprietor_to_subentity(self):
        ''' Test class (static attribute)'''
        orm.security().proprietor = None

        # Test the map
        map = hacker.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in hacker.orm.mappings 
            if x.name == 'proprietor'
        ])

        # proprietor should be a `party`
        self.is_(party.party, map.entity)

        ''' Test object '''
        hckr = hacker.getvalid()

        map = hckr.orm.mappings['proprietor']
        self.eq('proprietor', map.name)

        # Make sure the proprietor mapping was cloned, i.e., the
        # object's proprietor mapping is not identical to the class's
        # proprietor mapping.
        self.isnot(
            hacker.orm.mappings['proprietor'],
            map
        )
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in hckr.orm.mappings 
            if x.name == 'proprietor'
        ])

        self.none(hckr.proprietor)

        proprietor = party.person(name='Malcolm McLaren')

        hckr.proprietor = proprietor

        self.notnone(hckr.orm.super.proprietor)

        hckr.save()

        hckr1 = hckr.orm.reloaded()

        self.eq(hckr.id, hckr1.id)
        self.eq(hckr.proprietor.id, hckr1.proprietor.id)

        self.notnone(hckr.orm.super.proprietor)

    def it_adds_proprietor_to_subsubentity(self):
        ''' Test class (static attribute)'''
        orm.security().proprietor = None

        # Test the map
        map = phreak.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in phreak.orm.mappings 
            if x.name == 'proprietor'
        ])

        # proprietor should be a `party`
        self.is_(party.party, map.entity)

        ''' Test object '''
        phr = phreak.getvalid()

        map = phr.orm.mappings['proprietor']
        self.eq('proprietor', map.name)
        self.isnot(
            phreak.orm.mappings['proprietor'],
            map
        )
        self.type(orm.entitymapping, map)

        # Ensure only one
        self.one([
            x for x in phr.orm.mappings 
            if x.name == 'proprietor'
        ])

        self.none(phr.proprietor)

        proprietor = party.person(name='Malcolm McLaren')

        phr.proprietor = proprietor

        phr.save()

        phr1 = phr.orm.reloaded()

        self.eq(phr.id, phr1.id)
        self.eq(phr.proprietor.id, phr1.proprietor.id)

        self.notnone(phr.orm.super.proprietor)
        self.notnone(phr.orm.super.orm.super.proprietor)

    def it_sets_proprietor(self):
        tsla = party.company(name='Tesla')
        orm.security().proprietor = tsla

        ''' Test object '''
        eng = engineer.getvalid()

        self.is_(tsla, eng.proprietor)

        eng.save()

        # Ensure it can be changed after a save()
        eng = eng.orm.reloaded()

        self.eq(tsla.id, eng.proprietor.id)

        malcolm = party.person(name='Malcolm McLaren')
        orm.security().proprietor = malcolm
        eng.proprietor = malcolm

        self.is_(malcolm, eng.proprietor)
        eng.save()

        eng = eng.orm.reloaded()
        self.eq(malcolm.id, eng.proprietor.id)

    def it_propagates_proprietor_to_supers(self):
        """ When an subentity is newly created, it's supers should have
        the same proprietor.
        """
        tsla = party.company(name='Tesla')
        orm.security().proprietor = tsla

        # Test without saving.
        phr = phreak()
        self.eq(tsla.id, phr.orm.super.orm.super.proprietor.id)
        self.eq(tsla.id, phr.orm.super.proprietor.id)

        # Save immediatly then test
        phr = phreak()
        phr.save()

        eng = engineer(phr)
        self.eq(tsla.id, eng.proprietor.id)

        hckr = hacker(phr)
        self.eq(tsla.id, hckr.proprietor.id)

        # TODO If eng's or hckr's proprietor were changed at this point,
        # it's supers and subs should be updated with the new
        # proprietor. Let's wait to see if this is an actual need. The
        # ui developer could do this manually if it ever comes
        # up; though I'm not really sure what's best at this point.

    def it_filters_entity(self):
        """ By default, queries should only be able to return records 
        belonging to the proprietor as defined by orm.security().proprietor.
        """

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # If orm.security().proprietor is None, no filtering should take place.
        # This shouldn't be allowed except for system administration
        # tasks.
        orm.security().proprietor = tsla

        # Save an engineer record whose proprietor is Tesla
        eng = engineer()
        eng.save()

        # Set orm.security().proprietor is None. We should be able to query this
        # engineer without RecordNotFoundError being thrown. We sort of
        # have "root" access because orm.security().proprietor is None.
        orm.security().proprietor = None
        self.expect(None, lambda: engineer(eng.id))

        # Set the orm.security().proprietor to tsla. Still no problems getting
        # the Tesla engineer because the orm.security().proprietor is Tesla.
        orm.security().proprietor = tsla
        engineer(eng.id)
        self.expect(None, lambda: engineer(eng.id))

        # Now that the orm.security().proprietor is Microsoft, we should not be
        # able to access the engineer record owned by Tesla.
        orm.security().proprietor = ms
        self.expect(db.RecordNotFoundError, lambda: engineer(eng.id))

    def it_updates_entity(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla engineers
        orm.security().proprietor = tsla
        engs = engineers()
        for i in range(3):
            engs += engineer(
                name   = f'Tesla engineer {i}',
                skills = 'c++'
            )

        engs.save()

        # Create some Microsoft engineers
        orm.security().proprietor = ms
        for i in range(3):
            engs += engineer(
                name   = f'Microsoft engineer {i}',
                skills = 'c++'
            )

        engs.save()

        orm.security().proprietor = tsla

        # Load the thre Tesla engineers
        engs = engineers("name LIKE %s", '%engineer%')

        # Double check that we only have Tesla's engineers
        self.three(engs)
        for eng in engs:
            self.true(eng.name.startswith(f'Tesla engineer'))

        for eng in engs:
            # Swith proprietors to Microsoft and try updating Tesla's
            # engineers. 
            orm.security().proprietor = ms

            eng.skills = 'VB.NET'
            # We would expect Microsoft to get an error if they changed
            # Tesla's engineer records.
            with self.emusk.su():
                self.expect(orm.ProprietorError, eng.save)

            # Reload the engineer to make sure it wasn't saved despite
            # the exception.
            orm.security().proprietor = tsla
            self.eq('c++', eng.orm.reloaded().skills)

        # Switching the proprietor to Tesla should fix the problem.
        orm.security().proprietor = tsla
        for eng in engs:
            eng.skills = 'VB.NET'
            # We would expect Microsoft to get an error if they changed
            # Tesla's engineer records.
            self.expect(None, eng.save)

            self.eq('VB.NET', eng.orm.reloaded().skills)

        orm.security().proprietor = ms

        # Load the thre Microsoft engineers
        engs = engineers("name LIKE %s", '%engineer%')

        # Ensure they haven't been changed
        self.three(engs)
        for eng in engs:
            self.true(eng.name.startswith(f'Microsoft engineer'))
            self.eq('c++', eng.skills)
            eng.skills = 'python' # Make a change

        # Change proprietor
        orm.security().proprietor = tsla

        # This time, save the collection
        with self.bgates.su():
            self.expect(orm.ProprietorError, engs.save)

        # Correct proprietor
        orm.security().proprietor = ms

        # Ensure no changes were made
        engs = engineers("name LIKE %s", '%engineer%')
        for eng in engs:
            self.true(eng.name.startswith(f'Microsoft engineer'))
            self.eq('c++', eng.skills)
            eng.skills = 'python' # Make a change

        # This time, save the collection
        self.expect(None, engs.save)

        # Ensure no changes were made
        engs = engineers("name LIKE %s", '%engineer%')
        for eng in engs:
            self.true(eng.name.startswith(f'Microsoft engineer'))
            self.eq('python', eng.skills)

    def it_searches_entities(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla engineers
        orm.security().proprietor = tsla
        engs = engineers()
        for i in range(3):
            engs += engineer(
                name   = f'Tesla engineer {i}',
                skills = 'c++'
            )

        engs.save()

        # Create some Microsoft engineers
        orm.security().proprietor = ms
        for i in range(3):
            engs += engineer(
                name   = f'Microsoft engineer {i}',
                skills = 'c++'
            )

        engs.save()

        ids = engs.pluck('id')
        self.six(ids)

        # Set proprietor and run the same query. Make sure only the the
        # entities that the proprietor ows are returned
        for com in (tsla, ms):
            orm.security().proprietor = com

            # Test IN operator
            engs = engineers(
                f"id in ({','.join(['%s'] * len(ids))})", ids
            )
            self.three(engs)
            for eng in engs:
                self.true(
                    eng.name.startswith(f'{com.name} engineer')
                )

            # Proprietor is currently set to {com.name}. We should be
            # able to query for all the {com.name} engineers
            engs = engineers("name LIKE %s", '%engineer%')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Use a non-parameterized query. Note that this results in a
            # mixed query; i.e., partially parameterized and partially
            # not::
            #
            #   engs = engineers(
            #     "skills = 'c++', proprietor__partyid = %s", ['c70...']
            #  )
            engs = engineers("skills = 'c++'", ())
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Test two-value query (equality)
            engs = engineers('skills', 'c++')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Test with *args
            wh = "name LIKE %s AND skills = %s"
            engs = engineers(wh, ('%engineer%',), 'c++')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Test conjunctive
            wh = "name LIKE %s AND skills = %s"
            engs = engineers(wh, ('%engineer%', 'c++'))
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # kwargs query
            engs = engineers(skills = 'c++')
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

            # Literal with kwargs
            engs = engineers(
                "name LIKE '%engineer%'", (), skills = 'c++'
            )
            self.three(engs)
            for eng in engs:
                self.true(eng.name.startswith(f'{com.name} engineer'))

    def it_loads_constituents(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')
        ms.save()

        # Create Tesla engineer and the `systems` s/he administors
        orm.security().proprietor = tsla
        eng = engineer()
        for i in range(3):
            eng.systems += system(
                name = f'Tesla system {i}',
            )

        eng.save()

        # Create Microsoft engineer
        orm.security().proprietor = ms
        eng = engineer()
        for i in range(3):
            eng.systems += system(
                name = f'Microsoft system {i}',
            )

        eng.save()

        eng1 = eng.orm.reloaded()

        syss = eng1.systems.sorted()

        self.three(syss)

        for sys in syss:
            self.startswith(f'{ms.name} system', sys.name)

        # Reload engineer as Microsoft
        eng1 = eng.orm.reloaded()

        # Set proprietor to Tesla
        orm.security().proprietor = tsla

        # Even though we have Microsoft's engineer (this situation
        # should never happen unless there was a mistake by a web
        # developer), we can't load its systems because the proprietor
        # was set to Tesla.
        self.zero(eng1.systems)

        # Load engineer as Microsoft, change the name of a system and
        # save as Tesla. We would expect "Tesla" to receive a
        # ProprietorError.
        orm.security().proprietor = ms
        eng1 = eng.orm.reloaded()
        eng1.systems.first.name = 'Tesla system'

        orm.security().proprietor = tsla

        with self.bgates.su():
            self.expect(orm.ProprietorError, eng1.save)

    def it_eager_loads_constituents(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create a Tesla engineers and the `system` s/he administors
        orm.security().proprietor = tsla
        eng = engineer(name='Tesla engineer')
        for i in range(3):
            eng.systems += system(
                name = f'Tesla system {i}',
            )

        eng.save()

        # Create a Microsoft engineers and the `system` s/he administors
        orm.security().proprietor = ms
        eng = engineer(name='Microsoft engineer')
        for i in range(3):
            eng.systems += system(
                name = f'Microsoft system {i}',
            )

        eng.save()

        for com in (ms, tsla):
            orm.security().proprietor = com
            engs = engineers(
                'name LIKE %s', '%engineer%', orm.eager('systems')
            )

            self.one(engs)

            eng = engs.first

            for sys in eng.systems:
                self.startswith(f'{com.name} system', sys.name)


    def it_searches_subentities(self):
        engineers.orm.truncate()
        hackers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla hackers
        orm.security().proprietor = tsla
        hckrs = hackers()
        for i in range(3):
            hckrs += hacker(
                name   = f'Tesla hacker {i}',
                skills = 'c++',
                handle = 'Neo',
            )

        hckrs.save()

        # Create some Microsoft engineers
        orm.security().proprietor = ms
        for i in range(3):
            hckrs += hacker(
                name   = f'Microsoft hacker {i}',
                skills = 'c++',
                handle = 'Neo',
            )

        hckrs.save()

        ids = hckrs.pluck('id')
        self.six(ids)

        for com in (tsla, ms):
            orm.security().proprietor = com

            # Test IN operator
            hckrs = hackers(
                f"id in ({','.join(['%s'] * len(ids))})", ids
            )
            self.three(hckrs)
            for hckr in hckrs:
                self.true(
                    hckr.name.startswith(f'{com.name} hacker')
                )

            
            # Proprietor is currently set to {com.name}. We should be
            # able to query for all the {com.name} hackers
            hckrs = hackers("name LIKE %s", '%hacker%')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Use a non-parameterized query. Note that this results in a
            # mixed query; i.e., partially parameterized and partially
            # not::
            #
            #   hckrs = hackers(
            #     "skills = 'c++', proprietor__partyid = %s", ['c70...']
            #  )
            hckrs = hackers("skills = 'c++'", ())
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test two-value query (equality)
            hckrs = hackers('skills', 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test with *args
            wh = "name LIKE %s AND skills = %s"
            hckrs = hackers(wh, ('%hacker%',), 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test conjunctive
            wh = "name LIKE %s AND skills = %s"
            hckrs = hackers(wh, ('%hacker%', 'c++'))
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # kwargs query
            hckrs = hackers(skills = 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Literal with kwargs
            hckrs = hackers(
                "name LIKE '%hacker%'", (), skills = 'c++'
            )
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test query with subentity column
            hckrs = hackers(handle = 'Neo')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

            # Test query with subentity column and superentity column
            hckrs = hackers(handle = 'Neo', skills = 'c++')
            self.three(hckrs)
            for hckr in hckrs:
                self.true(hckr.name.startswith(f'{com.name} hacker'))

    def it_searches_subsubentities(self):
        engineers.orm.truncate()
        hackers.orm.truncate()
        phreaks.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla phreaks
        orm.security().proprietor = tsla
        phrs = phreaks()
        for i in range(3):
            phrs += phreak(
                name   = f'Tesla phreak {i}',
                skills = 'DTMF',
                handle = 'Captain Crunch',
                boxes = 'blue',
            )

        phrs.save()

        # Create some Microsoft engineers
        orm.security().proprietor = ms
        for i in range(3):
            phrs += phreak(
                name   = f'Microsoft phreak {i}',
                skills = 'DTMF',
                handle = 'Captain Crunch',
                boxes = 'blue',
            )

        phrs.save()

        ids = phrs.pluck('id')
        self.six(ids)

        for com in (tsla, ms):
            orm.security().proprietor = com

            # Test IN operator
            phrs = phreaks(
                f"id in ({','.join(['%s'] * len(ids))})", ids
            )
            self.three(phrs)
            for phr in phrs:
                self.true(
                    phr.name.startswith(f'{com.name} phreak')
                )

            # Proprietor is currently set to {com.name}. We should be
            # able to query for all the {com.name} phreaks
            phrs = phreaks("name LIKE %s", '%phreak%')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Use a non-parameterized query. Note that this results in a
            # mixed query; i.e., partially parameterized and partially
            # not::
            #
            #   phrs = phreaks(
            #     "skills = 'c++', proprietor__partyid = %s", ['c70...']
            #  )
            phrs = phreaks("skills = 'DTMF'", ())
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test two-value query (equality)
            phrs = phreaks('skills', 'DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test with *args
            wh = "name LIKE %s AND skills = %s"
            phrs = phreaks(wh, ('%phreak%',), 'DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test conjunctive
            wh = "name LIKE %s AND skills = %s"
            phrs = phreaks(wh, ('%phreak%', 'DTMF'))
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # kwargs query
            phrs = phreaks(skills = 'DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Literal with kwargs
            phrs = phreaks(
                "name LIKE '%phreak%'", (), skills = 'DTMF'
            )
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test query with subsubentity column
            phrs = phreaks(boxes = 'blue')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))


            # Test query with subentity column
            phrs = phreaks(handle = 'Captain Crunch')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

            # Test query with entity column.
            phrs = phreaks(skills='DTMF')
            self.three(phrs)
            for phr in phrs:
                self.true(phr.name.startswith(f'{com.name} phreak'))

    def it_makes_proprietors_self_owning(self):
        orm.security().proprietor = None

        tsla = party.company(name='Tesla')

        # At this point, tsla will not have a record proprietor
        self.none(tsla.proprietor)

        orm.security().proprietor = tsla

        # After setting tsla as the proprietor, tlsa, and its supers,
        # will have tsla as their proprietors.
        sup = tsla
        while sup:
            self.is_(tsla, sup.proprietor)
            sup = sup.orm.super

        tsla.save()

        sup = tsla.orm.reloaded()

        while sup:
            self.eq(tsla.id, sup.proprietor.id)
            sup = sup.orm.super

    def it_streams_entities(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla engineers
        orm.security().proprietor = tsla
        engs = engineers()
        for i in range(2):
            engs += engineer(
                name   = f'Tesla engineer {i}',
                skills = 'c++'
            )

        engs.save()

        # Create some Microsoft engineers
        orm.security().proprietor = ms
        for i in range(3):
            engs += engineer(
                name   = f'Microsoft engineer {i}',
                skills = 'c++'
            )

        engs.save()

        # Stream all engineers (normally we would just use
        # `engineer.orm.all`)
        engs = engineers(orm.allstream)

        # NOTE It's important to test the count here because orm.count
        # works different in streaming mode. It creates its own SELECT
        # statement.
        self.three(engs)

        for eng in engs:
            self.startswith(f'Microsoft engineer', eng.name)


        orm.security().proprietor = tsla

        engs = engineers(orm.allstream)
        self.two(engs)
        for eng in engs:
            self.startswith(f'Tesla engineer', eng.name)

    def it_searches_entities_using_fulltext_index(self):
        engineers.orm.truncate()

        # Create some proprietors
        tsla = party.company(name='Tesla')
        ms = party.company(name='Microsoft')

        # Create some Tesla engineers
        orm.security().proprietor = tsla
        engs = engineers()
        for i in range(3):
            engs += engineer(
                name   = f'Tesla engineer {i}',
                skills = 'c++',
                bio = self.dedent('''
                I enjoy  designing digital communication busses
                (CAN, Ethernet, RS-485, USB, SPI, I2C, etc
                ''')
            )

        engs.save()

        # Create some Microsoft engineers
        orm.security().proprietor = ms
        for i in range(3):
            engs += engineer(
                name   = f'Microsoft engineer {i}',
                skills = 'c++',
                bio = self.dedent('''
                Ability to use machine learning algorithms for
                classification, regression, forecasting, reinforcement
                learning, anomaly detection for a user facing
                product, etc
                ''')
            )

        engs.save()

        for com in tsla, ms:
            orm.security().proprietor = com
            search = 'machine learning' if com is ms else 'USB'
            
            engs = engineers('match(bio) against (%s)', search)
            self.three(engs)

            # Test conjuction (both bio's have 'etc')
            engs = engineers(
                'match(bio) against (%s) and match(bio) against(%s)', 
                search, 'etc'
            )
            self.three(engs)

            engs = engineers(
                'match(bio) against (%s) and skills = %s',
                search, 'c++'
            )
            self.three(engs)

            search = 'USB' if com is ms else 'machine learning'
            engs = engineers('match(bio) against (%s)', search)
            self.zero(engs)

if __name__ == '__main__':
    tester.cli().run()
