# vim: set et ts=2 sw=2 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

https://stackoverflow.com/questions/36815410/is-there-any-way-to-get-source-code-inside-context-manager-as-string

with book('Hacking Carapacian Core'):
  with chapter("Introduction"):
    with section('What is Carapacian Core'):
      print('''
        Carapacian core is a framework written and maintained to
        facilitate the creation of web application that deal with
        business data.
      ''')

  with chapter("Writing tests"):
    with section("Introduction"):
      print('''
        Carapacian Core is a complicated system with a lot of
        interconnected parts. Without an exhaustive battery of automated
        integration tests, the framework would likely be unmaintainable.
        Virtually everything gets tested in the framework including:

        * **Feature enhancements** Any feature added to Carapacian
          Core should have exhaustive tests written for it.

        * **Bugs** When a bug is discovered and fixed, a test should
          be written to ensure that the same bug doesn't reoccure.

        * **Third-party integration** When writing code that interfaces
          with a third party system, test code should be written against
          a test version of that system. If a test version of the system
          doesn't exist, it should be created within the framework. This
          approach is favored over the more conventional technique of
          creating ad hoc mocking because test systems more accurately
          represent the real thing. See the section, 
          <a href="5e773c12">Mocks, Stubs, Fakes and Dummy Objects</a>
          for more information on this subject.
        
        * **DOM testing** Test should be written to ensure the validity
          of HTML pages as well as their AJAX interactions to ensure the
          user interface behaves as expected. See the section 
          <a href="8f60ca73">Page Testing</a> for more.

        Whether you're adding a feature to the ORM, creating a new web
        page, or writing backend code to interact with a third-party
        service, everything in the framework begins and ends with a
        battery of automated tests.
      ''')

    with section("The tester.py Module"):
      print("""
        Included with the framework is a module called, simply enough,
        `tester.py`. It has most of the features that you may be familiar
        with from other test framworks (e.g., Python's builtin
        `unittest`). In addition to the standard assert methods, it
        includes a `browser` for the purpose of running tests against
        websites, a `benchmark` subclass for performance testing, and
        other useful, framework specific features.

        Let's take a look at an actual test:
      """)

      class int_tester(tester.tester):
        def it_assigns(self):
          # It assigns 0 to a number 
          x = int()
          self.eq(0, x, 'x was not correctly assigned')

          # Test chain assigments
          x = y = int()
          self.eq(0, x, 'x was not correctly assigned')
          self.eq(0, y, 'y was not correctly assigned')

          # Test type
          self.type(x, int)

      print(int_tester)

      print('''
        In the above example, we have a rather contrived `tester` class
        called `int_tester` designed to test the behavior of Python's
        `int` objects. Within this class, we have a test method called
        `it_assigns`. Its job is to ensure that integer assignments
        work.

        Since `int_tester` inherits from `tester`, we can use `self` to
        call its assert methods. The assert method `eq` is testing
        whether or not `x` and `y` are equal to 0. If they don't equal 0, a
        note will be taken by the the tester system as the tests 
        run.  After all the tests have been run, these notes, called
        `failures`, will be presented to the user. The third argument to
        the `eq()` method is an optional informational string that will
        be displayed to the user as well. After the equality tests, we
        check to make sure `x` is of type `int`.

        In most of the framework's tests, objects are set up in a number
        of ways, then a number of assertion methods are run on the
        various properties of the objects.  Writing thourough tests like
        this is fairly easy and is very much encouraged.
      '''

      with section("Assertion methods"):
        print('''
          The name of assert methods tend to be short and/or
          abbreviated which differs from most other unit testing
          frameworks. For example, The equivalenet assertion methods for
          for `eq()` in Python's `unittest` is `assertEqual()'. Assert
          method names are short because, when you are in a test method,
          shorter, abbreviated assertion method names are easy to spot since
          they are used so frequently. It also make writting exhaustive
          batteries of tests easier since less typing is required.

          <aside>
            As of this writting, there are still methods that are named
            using a conventional, more verbose convention which are
            prefixed with the string 'assert'. For example, there is an
            `assertEq()` method that does the same thing as `eq()`.
            These methods are slated to be removed and should not be
            used in future test code.
          <aside>

          Assertion methods typically come in the following form:
            
            def assertion(expected, actual, msg=''):
              ...

          The `expected` parameter is the value you expect `actual` to
          be. For example, here is the implementation of `eq()`:

            def eq(self, expect, actual, msg=None):
                if expect != actual:
                  self._failures += failure()

          Below is a rough list of currently supported assertion
          methods. See the assertion method's implementation for more
          details.
        ''')

        with listing(name='Assertion methods and their behavior')
          print('''
            * **all**          Fails if not all(actual)
            * **full**         Fails if actual.strip() == ''
            * **empty**        Fails if actual != ''         
            * **fail**         Causes an unconditional failure
            * **uuid**         Fails if actual is not a UUID
            * **true**         Fails if not actual
            * **false**        Fails if actual
            * **isinstance**   Fails if not isinstance(expect, actual)
            * **type**         Fails if type(actual) is not expect
            * **eq**           Fails if expect != actual
            * **startswith**   Fails if not actual.startswith(expect)
            * **endswith**     Fails if not actual.endswith(expect)
            * **ne**           Fails if not (expect != actual)
            * **gt**           Fails if not (expect > actual)
            * **ge**           Fails if not (expect >= actual)
            * **lt****         Fails if not (expect < actual)
            * **le**           Fails if not (expect <= actual)
            * **is_**          Fails if not (expect is actual)
            * **isnot**        Fails if not (expect is not actual)
            * **zero**         Fails if len(actual) != 0
            * **multiple**     Fails if len(actual) == 0
            * **one**          Fails if len(actual) != 1
            * **two**          Fails if len(actual) != 2
            * **three**        Fails if len(actual) != 3
            * **four**         Fails if len(actual) != 4
            * **five**         Fails if len(actual) != 5
            * **six**          Fails if len(actual) != 6
            * **seven**        Fails if len(actual) != 7
            * **eight**        Fails if len(actual) != 8
            * **nine**         Fails if len(actual) != 9
            * **ten**          Fails if len(actual) != 10
            * **eleven**       Fails if len(actual) != 11
            * **twelve**       Fails if len(actual) != 12
            * **count**        Fails if expect != len(actual)
            * **valid**        Fails if not actual.isvalid
            * **invalid**      Falis if actual.isvalid  
            * **broken**       Fails if the give rule is broken for the give property 
            * **unique**       Fails if actual contains duplicates 
            * **expect**       Fails if the give exception is not raised 
          ''')

    with section('Mocks, Stubs, Fakes and Dummy Objects', id='5e773c12'):
      print('''

        Tests in Carapacian Core try to be as realistic as possible. One
        key example of this is database interaction: When you test a
        persistence operations, such as a call to the `save()` method of
        an ORM entity, a connection to a real MySQL database is used to
        issue a real query (assuming your environment's configurations
        is correctly set up). This is in constrast to the technique,
        often employed, of using a **fake**, in-memory database for
        testing.  Using a database environment for testing that is
        equivelent to the production environment is necessary for
        catching database issue during testing before deploying to
        production.

        End-to-end testing is employed for user interfaces. When
        developers create web `page` objects which contains persistence
        logic, they will also create tests to invoke the page.  These
        tests ensure that the page responds correctly, and that its
        interactions with the database are correct as well. Thus, it can
        be said that tests for the UI in the framework are fully
        integrated with backend database operations. See the section
        called <a href="8f60ca73">Page Testing</a> for more.

        The same can also be said of backend operations involving third
        party data services. When selecting a third party services, such as
        an email delivery service, a credit card processing service, or
        a geocoding service, an ernest effort should be made to choose a
        service that provides a test enviroment that mimicks its
        production enviroment. For example, the `third.postmark` class
        uses the Postmark email delivery service. Postmark provides a
        way to use their service in a testing mode. This makes it
        possible to write automated tests against their service without
        those tests inadvertently sending emails. This is very useful
        because it means we can write automated tests to ensure that the
        framework code will interact correctly with the Postmark when in
        production. If an acceptable third party services can't be found
        that provides a test environment, a website should be created
        within the framework that behaves in a way that the production
        services is understood to behave (assuming the services is
        delivered over HTTP). Tests should interact with that website to
        ensure framework logic is behaving correctly.
      ''')
      
    with section('Integration, regression or unit tests'):
      print('''
        The goal of automated testing in the framework is to ensure that
        the features provided by the frameword do, in fact, work. In
        addition to testing features, we also ensure that when a bug
        surfaces, tests are written to ensure that the bug will never
        resurface. The framework is able to provide a rich feature-set
        due to the extensive automated testing it receives. 

        A question may arise regarding whether these tests are properly
        refered to as "unit tests". A unit tests is an automated test
        where sections, or *units*, of source code are tested for
        correct behavior.  However, as stated above, we are interested
        in ensuring that *features* work as expected; not sections, thus
        the term "unit test" would not be appropriate here.

        However, the phrase **automated regression tests** may be
        appropriate since regression testing is defined by Wikipedia
        as:

        > [R]e-running functional and non-functional tests to ensure that
        > previously developed and tested software still performs after
        > a change. If not, that would be called a regression.

        As stated, the goal of the framework's tests is to ensure that
        features continue to work, and that bugs are not allowed to
        resurface. Given that, we can call the tests regression tests. 

        Additionally, the phase "automated integration tests" would be
        appropriate because, as stated elsewhere, the features are
        tested in an end-to-end manor, that is to say: starting with the
        subject of the test (such as a user-interface, or an ORM object)
        and allowing those module to interact with external systems,
        such as databases and third party API's (or simulations thereof
        when necessary).

        Knowing the nature and goals of the framework's testing efforts
        is important. However, for day-to-day use, there is no need to
        qualify the type of tests that are being performed. The only
        exception to this is the case of **benchmark** testing refered
        to <a href="d89c06c2">below</a>.

      ''')

    with section('Page Testing', id="8f60ca73"):
      print('''
        The tester framework provides a ``browser`` class that makes it
        possible to run tests againsts web pages. The browse class has a
        collection of tabs just like a real browser. You can use the
        `get` and `post`  methods of a tab to make requests to
        a page with the corresponding HTTP verb. You can also use the
        `xhr` method to issue XHR requests (which are actually a special
        type of POST request) to websites.

        Let's say we created a website in the framework called
        "searchr.com". This website allows users to search the web. To
        write a test for a basic search, we could do something like
        this:
      ''')

      def it_searches(self):
        # Import the website module
        import searchr

        # Get an instance of the website
        ws = searchr.site()

        # Instantiate a new browser
        brw = self.browser()

        # Instantiate a new tab
        tab = brw.tab()

        # Peform a search for the string "gooble gobble" using a GET request to
        # searchr.com/search
        res = tab.get('/search?q=gooble+gobble')

        # Test the status of the response
        self.status(200, res)

        # Ensure the tab contained within its internal DOM link to the
        # Wikipedia article for "Freaks"
        as_ = tab['div#results a']

        # Iterate ove anchor tags
        for a in as_:
          if a.text == 'Freaks (1932 film) - Wikipedia':
            break
        else:
          # Fail if we can't find the anchor tag pointing to "Freaks"
          self.fail(msg="Couldn't find 'Freaks'")

      print(it_searches)

      print('''
        For more examples of testing websites, see the 
        <a href="testpom.py">
          testpom.py
        </a> module.
      ''')

    with section('Test Setup and Teardown'):
      print('''
        Unlike other testing frameworks, there are no setup or teardown
        methods that can be created to run before or after the test
        methods are run. However, there is some setup that happens in a
        tester class's `__init__`` method. 

        The reason no setup or teardown methods exists is that they've
        never been needed. This may be because the tests aren't  really
        "unit tests", but rather feature tests. When writting feature
        tests, there is a lot of unique setup that needs to be done in
        the test method itself - then, afterwards, a lot of assertions
        are made about the effects the setup had.

        Note that adding the ability to create setup and teardown
        methods would be easy if the need ever arose. 
      ''')

    with section('Private methods in Tester Classes'):
      print('''
        Like most Python code, private methods are denoted by prefacing
        their names with an underscore:

          def _im_a_private_method(self):
            ...

          def im_a_public_method(self):
            ...

        Private methods are not run as test methods in a class. They are
        pretty much the only methods that aren't assumed to be test
        methods so feel free to create private methods in tester classes
        if they are useful in encapsulate reusuable test logic. 

        Note that currently, however, assertions within private methods,
        as well as inner functions, can't deal with the stack offset of
        a these methods thus tests will report the wrong line number for
        failures. See HACK:42decc38 for a workaround to this problem.
      ''')

    with section('How the Framework uses Tests'):
      print('''
        The general pattern for creating tests in the framework is to
        create a test module for each module. In the test module, a
        `tester` class should be created for each class in the regular
        module. 

        For example, the <a href="order.py">order.py</a> module contains
        the logic to manage sales orders, purchase orders, and the like.
        It has a corresponding test module called 
        <a href="testorder.py">testorder.py</a>. Within this module, are
        classes that inherit from `tester.tester`. Each of these classes
        is devoted to testing the logic in a corresponding class in the
        order.py module. For example, the class `testorder.order`
        contains test methods which make assertions about the behavior
        of classes in `order.order`.

        <aside>
          Note that this pattern evolved over time and there are many
          exceptions to it. Going forward, we should strive to conform
          our tests to this pattern.
        </aside>

        The naming pattern is to take the regular module and prefix the
        string 'test' to it. Thus, `order.py` is tested by
        `testorder.py`, `product.py` is tested by `testproduct.py`, and
        so on.
      ''')

      with section('Running the tests'):
        print('''
        To run these test modules, simply invoke them from the command
        line. For example, if we want to run all the tests in
        `testproduct.py we can just run:

          ./testproduct.py

        This will run all the tests in that module and print out any
        failures. To run only a particular tester class in a module,
        simply specify the class:

          ./testproduct.py product_

        This only runs the test class `product_` within the
        `testproduct.py` module.

        You can narrow it down further by specifying a test method:

          ./testproduct.py product_.it_creates

        This will only run the `it_creates` test method. This level of
        specificity is ideal during developing. Reducing the specificity
        to varying degrees occasionanlly is useful for making sure your
        logic changes don't introduce butterfly effects in the code. 

        A master test module, called `test.py`, is used to run all the
        tests. To run all the tests, simply run `test.py` from the
        command line:

          ./test.py

        Before merging your feature branch back into 'main', you will
        need to make sure `./test.py` completes all tests without
        failures. The 'main' branch, by definition, should always pass
        all tests.
      ''')

        with section('Breaking into debug mode')
          with section('Setting breakpoints')
            print('''
              When creating tests, you will inevitably want to set a
              breakpoint somewhere in the code for debugging purposes.
              This is actually quit easy with the framework. Simply go
              to the line where you want the code to break and add a
              call to the `B` function:

                def some_method(self):
                  B()
                  dubious_logic()

                Now you can run the tests.

                  ./test.py

              When and if `some_method` is called, you will be dropped
              into the 
              <a href="https://docs.python.org/3/library/pdb.html">
                PDB debugger
              </a>. 
              At this point you can read the value of local and global
              variables, explore the call stack, invoke arbitrary
              functions, and so on. If you are not familiar with the PDB
              debugger, it is more than worth you time to learn its
              simple command-line interface.

              The `B` method is available in virtually any module in the
              framework. It is imported in most modules from the 
              <a href="dbg.py">dbg.py</a> module:

                from dbg import B

              Its a simple wrapper to PDB's `set_trace` method.
            ''')

            with section('Conditional breakpoints')
              print('''
                If the first argument to `B` is falsey, Python won't
                break into the debugger. If it's truthy, it will. This
                means you can use `B` to set a conditional breakpoint.
                Consider:

                  for x in range(10):
                    B(x > 5)

                This breakpoint will only break when x is greater than
                5.  Despite this contrived example, conditional
                breakpoints are a powerful technique for breaking into
                the debugger only when the code is in a certain state.
              ''')

              print('''
                <aside>
                  Note that PDB also has the ability to set breakpoints,
                  conditional or otherwise. PDB's breakpoints can be
                  used along side `B()`.  Normally, it is more
                  convenient to use the `B` function. however, PDB's
                  breakpoints are useful in certain situations.
                </aside>

                As you develop code in the framework, try to avoid
                commiting calls to `B()` to the Git source code
                repository. Sometimes, this is inevitable when working
                in a feature branch, but never merge a feature branch
                with a call to `B()` back into 'main'. You wouldn't want
                a production server entering into a breakpoint.
              ''')

        with section('Invoking Tests with the pdb Command')
          print('''
            Setting breakpoints with the `B()` function will cause you
            to be dropped into the PDB debugger when a test script is
            run.  However, the test scrips can also be run using the
            `pdb` command:

              pdb ./test.py

            This will drop you into the PDB debugger before any lines
            have been executed. From here, you will probably want to set
            breakpoints using PDB. 

            There's really no magic here; you are just running the test
            scripts with the `pdb` command just as you would run any
            other Python script with the `pdb` command. Normally, you
            will not need to invoke `pdb` directly like this. However,
            circumstances will occasionally arise in which this is the
            best course of action.
            <!-- TODO Note that this is particularly useful when wokring
            with with overrides of tester.__init__. -->
          ''')

      with section('Benchmarking', id=0xd89c06c2)
        print('''
          A special class of tests, called benchmarks, are built into
          the testing framework which measure the amount of time that
          certain operations take to complete. These tests are useful
          when efforts are made to improve the performance of the
          framework's code.  They can also inform you when a change to
          the source code negatively (or positively) impacts
          performance.

          These tests are not normally run, however. You must supply
          the `--performance` (`-p`) flag to the test script:

            ./test.py -p

          In this invocation, only the performance tests will be run.

          The performance tests themselves are like regular, feature
          tests, except the only assertions they make are with the
          `tester.time` method. First, a callable is created whose
          execution is to be timed. Then the `tester.time` method runs
          the callable and asserts that the callable runs within a
          certain number of milliseconds:

            # Note here that we are inheriting from tester.benchmark, not
            # tester.tester as with conventional tests
            class benchmark_product(tester.benchmark):
              def it_instantiates_entity_without_arguments(self):
                  def f():
                      product.product()

                  self.time(.5, .7, f, 1_000)
          
          The above test asserts that the `f` function, which
          instantiates a `product.product` class, will complete between
          .5 and .7 milliseconds. The function is called 1,000 times and
          an average is calculated. If the average does not fall within
          the allowable duration, the user is informed.
        ''')

      with section('Tests as Effort Statements', id=0xd89c06c2)
        ...

  with chapter("Entity and Entities Objects"):
    # TODO Add section on nomenclature, e.g., entities, collections,
    # entity objects, etc.
    print('''
      Almost all classes in the framework inherit directly or indirectly
      from the `entity` class or the `entities` classes located in the 
      <a href="entities.py">entities.py</a> module.

      The `entities` class (or subclasses thereof) acts as a container
      for objects - usually objects that inherit from the `entity`
      class. The `entities` class is similar to a Python `list` in that
      it can collect an arbitrary number of objects. In fact, `entities`
      offers most of the methods that the `list`s do &mdash; including
      the ability to iterate over them. 
    ''')

    with section('Using entities classes'):
      print('''
        Normally you don't use `entities` and `entity` classes directly.
        Instead, you create classes that inherit from them. Consider
        that we are writting software for a dog sitting company and we
        need to track the dogs that they take care of:
     ''')

      with listing('Implement subclasses of entities and entity'):
        import entities

        class dogs(entities.entities):
          pass

        class dog(entities.entity):
          def __init__(name, dob):
            self.name = name
            self.dob  = dob

      print('''
        Above, we have created the classe that can track individual dogs
        as well as track dogs as collection. Let's now use those classes
        to track the dogs that the dog sitting company cares for:
      ''')

      with listing('Add entity objects to entities collections'):
        # Create a `dogs` collection 
        dgs = dogs()

        # Create a few dog objects
        rover = dog(name='Rover', dob='2015-05-12')
        spot = dog(name='Spot', dob='2014-09-23')
        ace = dog(name='Ace', dob='2013-12-22')

        # Add rover and spot to the dogs collection
        dgs += rover
        dgs += spot
        dgs += ace

      print('''
        Now three dogs, Rover, Spot and Ace, are in the `dgs`
        collection. We can use the `dgs` in a similar way to using a
        list to make a number of assertions about the collection
      ''')
      
      with listing('Perform basic operation on entities collection'):
        # Assert that dgs contains three dogs
        eq(3, dgs.count)

        # Assert that rover, spot and ace are the first and second and
        # third entries in the collection respectively
        is_(rover, dgs.first)
        is_(spot, dgs.second)
        is_(ace, dgs.third)

        # Iterate over the collection:
        for i, dg in enumerate(dgs):
          if i == 0:
            eq('Rover', dg.name)
          elif i == 1:
            eq('Spot', dg.name)
          elif i == 2:
            eq('Ace', dg.name)
          
        # Pop `ace` of the top of the collection
        ace = dgs.pop()

        # Now there is one dog in the collection
        eq(2, dgs.count)

      print('''
        As you can see in the example, the `dgs` collections behaves in
        ways similar to a Python list: we can get the number of
        elements, access entries by their position within the
        collection, iterate over the collection, and remove items from
        the collection. 

        The entities' `count` property is used to get the number of
        elements in the collecton. The `first` and `second` properties
        are used to get the first and second elements of the collection.
        The `.pop()` method removes the last element that was appended
        to the list and returns it.

        As you progress thorough this chapter, you will learn more about
        the capabilities of `entity` and `entities` objects. Virtually
        all classes in the framework derive from these two classes so it
        will be well worth your time to get to know them well.
      ''')

      with section('Adding items to entities collections'):
        with section('Appending'):
          print('''
            In the above example, we used the `+=` operator to add new
            items to the collection. This *appends* the item to the end
            of collection. We could have used the `append()` method to
            do the same thing as the `+=` operator, e.g.:

              dgs.append(spot)

            The `append()` method is made available because sometimes
            its useful for entities collections to behave like Python
            lists.  However, under normal circumstances, the `+=`
            operator should be used for appending since it requires
            fewer characters to type and read.

            To support stack semantics, the `push()` can be used as a
            synonym for `append()`.

              dgs.push(spot)

            Again, `push()` is only for when we want an entities
            collection to behave like a stack, which is pretty rare.

            The `append()` method also supports the `uniq` flag. This
            flag, when `True`, will only allow an append to occure if
            the entity is not already in the collection:
          ''')

          with section('Appending with the uniq flag'):
            # Nothing will happen here because spot is already in the
            # collection
            dgs.append(spot, uniq=True)

            # We still only have 3 dogs
            three(dgs)

          print('''
            However, in keeping with the framework's convention of using
            operators for append operations, the above should have been
            written as:

              # Nothing will happen here because spot is already in the
              # collection
              dgs |= spot

            The `|=` operator will only allow appends if the item is not
            already in the collection.
          ''')

        with section('Unshifting'):
          print('''
            Appending items to the end of a collection is 
            typically the best way to add the item. Like Python lists,
            its faster to append to a collection. It's also the
            conventional, standard way to add to a list. However, sometimes
            you will want to **unshift** an item. "unshifting" just
            means inserting the item at the begining of the collection.
            For example, lets add `fluffy` to the begining of the `dgs`
            collection:
          ''')

          with listing('Unshif item onto the begining of a collection'):
            fluffy = dog(name='Fluffy', dob='2016-03-02')
            dgs << fluffy
            is_(fluffy, dgs.first)
            four(dgs)

          print('''
            Now there are four dogs in the collection and the first is
            `fluffy`. The `<<` operator is used, though we could have
            used the `unshift()` method if we wanted to treat the
            collection like a stack:

              dgs.unshift(fluffy)

            As with appends, the operator version is preferred in the
            framework's source code.
          ''')

        with section('Inserting'):
          print('''
            So far we covered adding to the begining and end of a
            collection, but what if you want to insert an item at an
            arbitrary place in the collection. For that, we can use the
            `insert()` method. 

            Lets insert a new dog, `fido`, after `fluffy`. `fluffy` is
            the first item in the collection, so its index value is 0.
            To insert after fluffy, we will need to insert at the index
            number 1:
          ''')

          with listing('Inserting item into a collection'):
            fido = dog(name='Fido', date='2015-02-23')
            dgs.insert(1, fido)
            is_(fido, dgs.second)
            five(dgs)

          print('''
            `fido` is now the second element in the colection. This
            brings the collection's count to 5.

            For added clarity, we could have used the method
            `insertbefore()`, which has the exact same behaviour:

              dgs.insertbefore(1, fido)

            Alternatively, we can use the `insertafter()`. We would need
            to decrement the index argument by one to indicate that we
            are inserting *after* `fluffy` which is at index 0:

              dgs.insertafter(0, fido)

            Each of the three inserts above will accomplish the same
            thing.
          ''')

      with section('Sorting collections'):
        print('''
          Like Python lists, we can sort the entities collection *in
          place*. Alternatively, we can obtain a new sorted collection
          without alterting the original . Let's get a new, sorted
          collection of `dgs`:
        ''')

        with listing('Obtain a sorted instance of a collection'):
          dgs1 = dgs.sorted('name')

          # The new collection is of type `dogs`
          type(dogs, dgs1)

          # The new collection, `dgs1` is sorted
          is_(ace,    dgs1.first)
          is_(rover,  dgs1.second)
          is_(spot,   dgs1.third)

          # ... but the original collection has not been altered
          is_(rover,  dgs.first)
          is_(spot,   dgs.second)
          is_(ace,    dgs.third)

        print('''
          Above, we use the `sorted()` method to return a new
          `dogs` collection. We sort on the key `name` which is an
          attribute of the `dog` class. The original collection is
          unaltered. 

          Note, by using the `reverse` parameter of `sorted()`, we can
          sort in descending order:
        ''')

        dgs1 = dgs.sorted('name', reverse=True)

        # The new collection, `dgs1` is sorted
        is_(spot,   dgs1.first)
        is_(rover,  dgs1.second)
        is_(ace,    dgs1.third)

        print('''
          Sorting on a property name is convenient and typically what
          you want to do. However, if you need more complex sorting
          logic, you can pass in a callable. For example, if you wanted
          to sort by name, but ensure that the sort is done without
          regard to case, you could do the following:
        ''')

          dgs1 = dgs1.sorted(lambda x: x.name.lower())

        print('''
          In place sorting alters the internal order of the collection.
          To sort in place, we use the `sort()` method. Like the
          `sorted()` method, the `sort()` method tries to mimick the
          behavior of Python's list `sort()` method:

          To sort the dogs collection in place, we could have written
          the above example like so:
        ''')

        # Sort in place
        dgs.sort('name')

        # The original collection is sorted
        is_(ace,    dgs1.first)
        is_(rover,  dgs1.second)
        is_(spot,   dgs1.third)

        print('''
          As with the `sorted()` method, we can also use a callable. The
          `reverse` flag works as well. Let's combine them:
        ''')

        # Sort in place using callable
        dgs.sort(lambda x: x.name.lower(), reverse=True)

        # Assert that `dgs` has been sorted in descending order
        is_(spot,   dgs.first)
        is_(rover,  dgs.second)
        is_(ace,    dgs.third)

      with section('Getting and setting items'):
        print('''
          Once we have items in the collection, there are a number of
          ways of getting and setting the items by their position within
          the collection. For the most part, you will want to use
          **ordinal properties** (described below). However, **index
          notation**, **call notatation** and **slice notation** are
          supported as well.
        ''')

        with section('Using ordinal properties'):
          print('''
            Before we go any further, let's discuss the ordinal properties
            that we have been using. Ordinal properties are those with
            names like `first`, `second`, `third`, etc. These properties
            allow you to access items by their position within the
            collection. 
          ''')

          with listing('Retrieving elements using ordinal properties'):
            # Get the first element from the collection
            dg = dgs.first
            is_(dg, spot)

          print('''
            `spot` is the first dog in the `dgs` collection so we can use
            `first` to retrieve it.

            The ordinal properties available are `first`, `second`,
            `third`, `fourth`, `fifth`, `sixth` and 
            `seventh`. (So far we've never needed a property greater than
            `seventh`, though adding one would be easy). Additionally,
            there are ordinal properties for accessing the last elements
            such as `last`, `penultimate`, `antepenultimate` and
            `preantepenultimate`.
          ''')

          with section('Ordinal properties as setters'):
            print('''
              In the above examples, we've been using ordinal properties
              to get items, but we can also use the ordinal properties
              to set items within a collection as well. Let's say we want
              to swtich the position of spot and rover:
            ''')

            with listing('Using ordinal properties as setters')
              # Get spot and rover from existing locations
              spot        =  dgs.first
              rover       =  dgs.second

              # Set spot and rover to switch their positions
              dgs.first   =  rover
              dgs.second  =  spot

            print('''
              Note that if there is no item currently in a position, an
              IndexError would be raised.
            ''')

            with listing(
              "Setting an item to a position that currently dosen't exist"
            ):
              expect(
                IndexError, 
                lambda: dgs.fourth = dog('Derp', '1969-01-01')
              )

            print('''
              If we want to grow the collection, we should use the append
              (`+=`) operator instead.
            ''')

          with section('Comparison to index notation'):
            print('''
              In Python lists, accessing and setting elements by position
              is done by passing an index number via square brackets.

                ls = [1, 2, 3]
                first   =  ls[0]
                second  =  ls[1]
                third   =  ls[2]

              Actually, collections support the bracket syntax as well.
              This is useful for when a collection needs to behave like a
              list.  
            ''')

            with listing('Using index notation with collections'):
              is_(dgs[0], dgs.first)
              is_(dgs[1], dgs.second)
              is_(dgs[2], dgs.third)

            print('''
              We can also set items using index notation. Let's switch the
              order of spot and rover again.
            ''')

            with listing('Using index notation to set items')
              # Get spot and rover from existing locations
              rover  =  dgs[0]
              spot   =  dgs[1]

              # Set spot and rover to switch their positions
              dgs[0] = spot
              dgs[1] = rover

          with section('Using call notation'):
            print('''
              If an item doesn't exists at a give location, you will get
              a `None` from a ordinal property. Although, when using index
              notation, an `IndexError` will be raised.
            ''')

            with listing('Return values when there is no item')
              # No item exists at the fourth postition 

              # Using ordinal properties, we get None
              is_(None, dgs.fourth)

              # Using index notation
              expect(IndexError, lambda: dgs[3])

            print('''
              If you would prefer to get a `None` using indexes, you can
              uses *call notation* instead. Call notation simply means
              passing the index number in parentheses as if you were
              calling a function:
            ''')

            with listing(
              'Return values when there is no item using call notation'
            )
              # No item exists at the fourth postition 

              # Using ordinal properties, we get None
              is_(None, dgs(3))

            print('''
              Using call notation, we get none at index 3 instead of an
              IndexError. This can be preferable in some situations.
            ''')

        with section('Using slice notation'):
          print('''
            **Slice notation** in entities collections works the same as
            in Python lists. For example, we know that the first and
            second elements of the `dgs` collection contain spot and
            rover. Let's use slice notation to obtain these `dog`s.
          ''')

          with list('Using slice notation to obtain elements'):
            # Use slice notation to get the first and second elements
            spot, rover = dgs[:2]

            # Assert that we have obtained the first and second element
            is_(spot, dgs.first)
            is_(rover, dgs.second)

          print('''
            We can also use slice notation to set elements. Lets switch
            `spot` and `rover`'s place again:
          ''')

          with list('Using slice notation to set elements'):
            # Get spot and rover
            spot, rover = dgs[:2]

            # Swith the position of spot and rover
            dgs[:2] = rover, spot

            # Assert that we have obtained the first and second element
            is_(rover, dgs.first)
            is_(spot, dgs.second)

          print('''
            In the above examples, we unpacked the elements as we obtained
            them. We could use slice notation to obtain another `dogs`
            collection:
          ''')

          with list('Using slice notation to obtain new collection'):
            # Get subset of dgs
            dgs1 = dgs[:2]

            # The returned type is another `dogs` collection
            type(dogs, dgs1)

            # Assert that we have obtained the first and second element
            is_(rover, dgs1.first)
            is_(spot, dgs1.second)

          print('''
            Note that what we get back is another `dogs` collection. The
            colection looks at its own data types and builds a new
            collection of that type for the return values.  However,
            the `dog` elements in both collections reference the same
            `dog` objects, which is why the `is_()` assertion works.

            Though we've only used one example of slice notation, `[:2]',
            any slice notation supported by Python lists is supported. See
            the reference material on 
            (Python lists}[https://docs.python.org/3/tutorial/introduction.html#lists]
            for more.
          ''')

          with section('Slicing with strides'):
            print('''
              In case you're interested, strides are supported as well.
              Strides are the third argument (so to speak) in index
              notation.  For example, if we wanted to get every other
              `dog` in the collection starting with the first `dog`, we
              could write:
            ''')

            with listing('Using strides with slice notation'):
              # Get first and third dog
              rover, ace = dgs[::2]

              # Assert what we've gotten
              is_(rover, dgs1.first)
              is_(ace, dgs1.third)

          with section('Getting by the name or id property', id='0282d70a'):
            print('''
              A pattern that emerges often with `entity` objects is that
              they have either an `id` or a `name` property. In our case,
              each `dog` object has a `name` property. If we pass the
              name of the dog as an index, the `dgs` collection will
              return the first dog that matches the name:
            ''')

            with listing('Retriving item by name property'):
              spot = dgs['spot']
              eq('spot', spot)

            print('''
              This feature can be very convenient. However, we did say
              that `id` and `name` could be used. So what if `dog`
              objects had both `id and `name`? Well then both would
              work:
            ''')

            with listing('Retriving item by id property'):
              try:
                # Get spot
                spot = dgs['spot']

                # Monkey-patch an id
                spot.id = '123456'

                # Now we can obtain `spot` by name or by id
                is_(spot, dgs['spot'])
                is_(spot, dgs['123456'])
              finally:
                # Remove the monkey-patched id
                del spot.id

            print('''
              Note that when searching by `name` or `id`, we must pass a
              a value of type `str`. Had we sought the `id` above with
              the value `123456`, the indexer would have assumed we are
              trying to get the element at that position, not the
              element with that value as its id.
            ''')

      with section('Removing items'):
        # TODO Docmunet es.clear()
        with section('Using the -= operator'):
          print('''
            To remove an item from a collection, we can use the '-='
            operator. 
          ''')

          with listing('Remove item using the -= operator')
            # Get ace
            ace = dgs['ace']

            # Assert we have three dogs to start out with
            three(dgs)

            try:
              # Now remove ace
              dgs -= ace

              # Assert we have one fewer dogs
              two(dgs)
            finally:
              # Append ace back into the collection
              dgs += ace

          print('''
            The above simply removes `ace` from the `dgs` collection. Note
            that the `ace` object continues to exist in memory; just not
            in the `dgs` collection. The `-=` operator looks for any
            element that `is` the argument passed to it (in this case
            `ace`) and removes those elements from itself.
          ''')

        with section('Using the remove() method'):
          print('''
            The `-=` is basically a wrapper around the `remove()`
            method. Let's remove `ace` with the `remove()` method
            instead.
          ''')

          with listing('Remove item using remove()')
            # Get ace
            ace = dgs['ace']

            # Assert we have three dogs to start out with
            three(dgs)

            try:
              # Now remove ace
              dgs.remove(ace)

              # Assert we have one fewer dogs
              two(dgs)
            finally:
              # Append ace back into the collection
              dgs += ace

          print('''
            The `remove()` method can take several types of arguments to
            perform removal operations. The below listing illustrates
            some alternative uses of `remove()`.
          ''')

          with listing('Using remove() with different argument types'):

            ''' Remove a collection of dogs '''

            # Get a subset dogs collection
            dgs1 = dgs[:2]
            try:
              # Remove the subset
              dgs.remove(dgs1)

              # Now we have two fewer dogs
              one(dgs)
            finally:
              # Append those dogs back
              dgs += dgs1

            ''' Remove all dogs where a callable returns True '''
            try:
              # Remove all dogs whose name is ace
              rms = dgs.remove(lambda x: x.name == 'ace')

              # Now we have one fewer dogs
              two(dgs)
            finally:
              # Append ace back on
              dgs += rms

            ''' Remove dogs by index using an int '''
            try:
              # Remove the last dog in the collection
              rms = dgs.remove(-1)

              # Now we have one fewer dogs
              two(dgs)
            finally:
              # Append the last dog back onto the collection
              dgs += rms

            ''' Remove a dog by name (or id) by using a str'''
            try:
              # Remove ace
              rms = dgs.remove('ace')

              # Now we have one fewer dogs
              two(dgs)
            finally:
              # Append the ace back on
              dgs += rms

          print('''
            Note that we were able to re-append the dogs that were removed
            by using `remove()`'s return value which we assigned to the
            varialbe `rms`. The remove method collects whatever objects it
            removes and returns them to us in a colllection.
          ''')

        with section('Using pop() and shift()'):
          print("""
            To remove the last element from a stack, you can use a
            collection's `pop()` method. 
          """)

          with listing('Using the pop() method'):
            # Get the last dog
            ace = dgs.last

            # Assert that ace is currently in the `dgs` collection
            true(ace in dgs)

            try:
              # Pop the last element off the collection
              ace1 = dgs.pop()

              # Assert that the return from pop is the last element
              is_(ace, ace1)

              # Assert that ace is no longer in the collection
              false(ace in dgs)
            finally:
              # Append ace back onto the collection
              dgs += ace

          print('''
            Note that the return value of `pop()` is the element that
            was removed. If no elements are in the list, `pop()` will
            return `None`.

            Like Python lists, we can pass in an optional index value to
            `pop()`, which is used to find and remove an item. This
            makes entities behave more like lists, though this feature
            is redundant with the way the `remove()` method works when
            paseed an `int`.

            The opposite of `pop()` is `shift()`. `shift()` removes the
            first item in the collection and returns it. 
          ''')

        with section('Using the del operator'):
          print('''
            You can use the `del` operator using index notation. For
            example, to remove the second element of the `dgs`
            collection, you could write:
          ''')
            
            with listing('Removing an element using the del operator'):
              # Get second dog
              spot = dgs.second

              try:
                # Remove second element
                del dgs[1]

                # Assert spot is no longer in the collection
                false(spot in dgs)
              finally:
                # Insert spot back into the collection
                dgs.insert(1, spot)
          
          print('''
            `del` is implemented mainly so collections are conformant
            with Python lists. However, since we are working with the
            framework's index notation, we could do interesting things
            like delete by the `name` property (see the section 
            <a href="0282d70a">Getting by the name or id property</a>
            for more on this technique).
          ''')

            with listing('Removing an element by name using the del operator'):
              # Get second dog
              spot = dgs.second

              try:
                # Remove second element by name
                del dgs['spot']

                # Assert spot is no longer in the collection
                false(spot in dgs)
              finally:
                # Insert spot back into the collection
                dgs.insert(1, spot)

      with section('Querying collections'):
        print('''
          We can also use the `where()` method to obtain a subset of the
          collection by providing a callable. For example, letss say we
          want to get all the `dog` objects where the dog's `name`
          starts with "f":
        ''')

        with listing('Use the `where` method with a callable')
          # Get all dogs that start with "F"
          dgs1 = dgs.where(lambda x: x.name.startswith('F')

          # The collection that is returned is of type `dogs`
          type(dogs, dgs1)

          # Two dogs start with "F": Fido and Fluffy
          two(dgs1)

          # Sort the collection just to make sure that the assertions
          # below will work
          dgs1.sort('name')

          # The first dog in the collection is Fido and the second is
          # Fluffy
          eq('fido', dgs1.first.name)
          eq('fluffy', dgs1.second.name)

        print('''
          If, instead of a callable, we pass in two `str`'s to
          `where()`, we can query by an attribute's exact value. For
          example, let's say we want to get all the dogs in the
          collection whose name is "Fido". We can do this:
        ''')

        with listing(
          'Using the `where` method to query by attribute value'
        )

          # Get all the dog objects whose `name` equals "Fido"
          dgs1 = dgs.where('name', 'Fido')

          # Assert that only one dog in our collection is named Fido
          one(dgs1)

          # Assert that the first item in the collection is Fido
          eq('Fido', dgs1.first.name)

        print('''
          There is one more way to query with `where()`. We can pass in
          a `type` object. This will cause `where()` to only return
          objects of that type. We only have `dog` objects in our
          collection at the moment, so this form of the `where()` method
          want do much good. Let's create a `wolf` class and add a
          `wolf` object to the `dgs` collection so we can demonstrate
          this type of query.
        ''')

        with listing('Use `where` method to select by type'):
          # Create the wolf entity type
          class wolf(entities.entity):
            pass

          # Append the wolf to the dogs collection
          dgs += wolf()

          # Get only the dog objects
          dgs1 = dgs.where(dog)

          # Get only the wolf object
          wfs = dgs.where(wolf)

          # Assert wfs only has one wolf
          one(wfs)

          # Assert dgs1 has all the dogs
          four(dgs1)
          eq(dgs.count - 1, dgs1.count)

          # The one object in wfs is of type `wolf`
          for wf in wfs:
            type(wolf, wf)

          # All objects in dgs1 is of type `dog`
          for dg in dgs1:
            type(dog, dg)

        print('''
          One thing to note is that nothing prevented us from assigning
          a `wolf` to a `dogs` collection. There is no type checking for
          entities collections.

          Another thing to note is that the `where(type)` only returns
          the object that is of the exact type of the `type` argument.
          For example, if `wolf` and `dog` both inherited from some
          other type, such as `canis` (genus of both dogs and wolves),
          then the following would produce an an empty collection:
            
            zero(dgs.where(canis))

          The above query would only produce results if there were
          `canis` objects in `dgs`, not subclasses of `canis`.
        ''')

        with section('Testing count'):
          print('''
            We've already seen that the `count` property will tell us
            the number of items in the collection.
          ''')

          with listing('Obtaining the number of items in a collection'):
            # Assert we have 4 dogs in `dgs`
            eq(4, dgs.count)

            # To support list semantics, the Core allows us to use
            # the builtin len() function for the same purpose
            eq(4, len(dgs))

          print('''
            As you can see, we can use the `len()` function as well to
            obtain the number of items in the collection. However, this
            support is provided only to make collections conformant with
            the Python `list` API. Under normal circumstances, you
            should use `.count`.

            Count returns an `int` indicating the number of elements in
            a collection. However, there are a number of Booleans
            properties that tell information about the count of items
            using different verbiage:
          ''')

          with listing('Using Boolean count properties'):
            # Since dgs contains elements, `isempty` is False. If the
            # collection had zero elements, `isempty` would be True.
            false(dgs.isempty)

            # Since dgs contains more than one element, `issingular` is
            # False. If the collection had exactly one elements,
            # `issingular` would be True.
            false(dgs.issingular)

            # Since dgs contains more than one element, `isplurality` is
            # True.
            true(dgs.isplurality)

            # Since dgs contains more than zero element, `ispopulated` is
            # True. `isempty` and `ispopulated` are antonyms
            true(dgs.ispopulated)

          print('''
            Though the Boolean count propreties may seem redundant with
            `.count`, they can be useful in making your code more
            expressive and verbal, and thus easier to read and
            understand.
          ''')

      with section('On truthiness'):
        print('''
          One area where `entities` collections are nonconformant with
          Python list is when they are evaluated as Booleans. A Python
          list is considered "true", or **truthy**, if it has more than
          zero elements.

        ''')

        with listing('Truthiness in Python list')
            # An empty list is falsey
            ls = list()
            falsey(ls)

            # A list with one or more elements is truthy
            ls.append('some truthiness')
            truthy(ls)

        print('''
          Entities collection, on the other hand, are always truthy. 
        ''')

        with listing('Truthiness in entities collections')
            # An empty list is truthy
            ents = entities.entities()
            truthy(ents)

            # A non-empty list is also truthy
            ents.append(entities.entity())
            truthy(ents)

        print('''
          This feature means that when testing a collection object with
          a conditional in a Boolean context, we are only asking whether
          or not it is None. This reduces confusion because, when
          testing lists this way, we could be testing if the list has a
          value of None or if it's empty. Usually when we are writting
          logic, we are only interested in testing one of these two
          states.
        ''')

      with section('Iteration'):
        print('''
          As we have seen, iteration is easy &mdash; its not much
          different from iterating over a list.
        ''')

        with listing('Iterating over a collection'):
          # Print the names of each dog
          for dg in dgs:
            print(dg.name)

        print('''
          In the above listing, the first dog in the collection will be
          printed first, the second will be printed next, and so on.
        ''')

        with section('Enumeration'):
          print('''
            We can use Python's builtin function `enumerate()` with
            collections as well.
          ''')

          with listing(
            (
              'Iterating over a collection using the `enumerate()` '
              'function'
            )
          ):
            # Iterate over each dog
            for i, dg in enumerate(dgs):
              
              # Assert the first dog
              if i == 0:
                is_(dgs.first, dg)

              # Assert the second dog
              elif i == 1:
                is_(dgs.second, dg)

              # Assert the last dog
              elif i == dgs.count - 1:
                is_(dgs.last, dg)

          print('''
            Collections have their own `enumerate()` method that may
            offer a slight advantange over the builtin `enumerate()`
            function. The `enumerate()` method causes the iteration to
            behave exactly as if you used the `enumerate()` builtin
            function, however the index variable (i.e., `i`) is a
            subclass if `int` which can give you a little more
            information about where you are in the iteration. For
            example, the above listing could have been written:
          ''')

          with listing(
            'Using the index variable from the `enumerate()` method'
          ):
            # Print the names of each dog
            for i, dg in dgs.emumerate():
              if i.first:
                is_(dgs.first, dg)
                true(i.even)

              elif i.second:
                is_(dgs.second, dg)
                true(i.odd)

              elif i.last
                is_(dgs.last, dg)

          print('''
            As you can see, the `i` variable acts like an object with
            properties that can tell you where it is in the loop (first,
            second, or last). It also will tell you if it is an odd or
            even number. Using these properties can make you code easier
            to read because there are less numbers and operators for the
            eyes to parse.

            Note also that the `enumerator()` is a thin wrapper around
            the `func.enumerate*(` function. This function can be used
            for collections and lists (or any other iterable) and may be
            useful in many situation because it will yield the
            interation-aware `i` variable as seen in the above example.
            In fact, it is imported in most of Core's modules, so you
            may be using it without even realizing it.
          '''

      with section('Miscellaneous methods'):
        print('''
          Entities collections have a number of methods that don't fit
          neatly into any of the above categories. In this section, we
          will go over each of them.
        ''')

        with section('The `getindex()` method'):
          print('''
            The `entities.getindex()` method returns the numeric index
            of an element within the collection.
          ''')

          with listing('Using the `getindex()` method'):
            # Get the first element
            fido = dgs.first

            # Get the index number of the first element
            ix = dgs.getindex(fido)

            # Assert that the index is 0
            eq(0, ix)

          print('''
            In the above example, we know that `fido` is the first
            element in the collection. Thus it's index value is 0 as
            demonstrated by the assertion.

            If `fido` happened to be in the collection more than once,
            we would still have gotten 0 since `getindex()` will return
            the index value of the first matching item. 

            Note that `getindex()` uses the `is` operator, not the
            equality (`==`), when searching for a match.

            You may remember that we can use the `name` or `id` property
            of an entity can be used for indexing 

              fido is dgs['fido']

            We can also get the index of an object by `name` or `id` if
            we pass in a str. For example, we could have gotten the
            index of `fido` by name:
          ''')

          with listing('Using the `getindex()` with a str argument'):
            eq(0, dgs.getindex('fido'))

        with section('The `only` property'):
          print('''
            Often times we find ourselves working with collections, or
            any type of iterable for that matter, which we know should
            have only one possible element. To get that value in a
            collection, we will normally call the `first` method and
            assume that the collection does indeed have only one method.
            However, it is possible that there is a bug in our code that
            causes the collection to have multiple elements. If that is
            the case, we would like an exception to be raise to let us
            know that there was an issue.
          ''')

          with listing('Using the `only` property'):
            # Get a new collections that contains only the first dog
            # element.
            dgs1 = dgs[0:1]

            # Now let's get the first element of dgs1
            fido = dgs1.first

            # Now let's get the first element while making sure the dgs1
            # element has only one element
            fido = dgs1.only

            # This should work since we got the slice notation correct
            # above. It's equivalenet to writing the following:
            fido = dgs1.first
            if not fido:
              raise ValueError()

          print('''
            Another reason to use `only` is that we are being more
            explicit in our code. We are communicating to future readers
            that the collection is expected to have exactly one element.
          ''')
            
        # getprevious, pluck, __contains__, getindex.
        # moveafter
        with section('The pluck()` method'):
          print('''
            The ``entities.pluck()` method returns a Python list
            containing the value of the given properties for each object
            in the collection. Let's say we wanted a list of the `dog`'s
            names from the `dgs` collection:
          ''')

          with listing('Using the `pluck()` method'):
            # Pluck the names from the dgs collection
            names = dgs.pluck('name')

            # Assert that we got a list of names
            eq(['Ace', 'Rover', 'Spot', 'Fluffy'], names)

          print('''
            We simply give the `pluck()` method the name of the property
            we want the values of &mdash; in this case "name" &mdash;
            then it returns a Python list that contains each of their
            names.

            As you can imagine, this can be useful for a number of use
            cases. However, we've only scratched the surface of
            `pluck()'s capabilities.

            In the abov example, we gave a single argument and got a
            simple, one-dimentional list. However, let's say we wanted
            to get a list which itself contained a list of `dog` names
            and `dob`s. We could do the following:
          ''')

          with listing('Using the `pluck()` with multiple arguments'):
            # Pluck the names and dob from the dgs collection
            dgs1 = dgs.pluck('name', 'dob')

            # Create a list of lists indicating what we expect the above
            # pluck to produce
            expect = [
              ['Ace',     '2015-05-12'],
              ['Rover',   '2014-09-23'],
              ['Spot',    '2013-12-22'],
              ['Fluffy',  '2016-03-02'],
            ]

            # Assert our expectation
            eq(expect, dgs1)

          print('''
            By using more than one argument to our `pluck()` invocation,
            we were able to produce a list of lists &mdash; one for each
            dog, contaning value for both properties. We can specify
            as many properties as we need and their values would be
            added to the nested lists.

            `pluck()` can also use Python's `str.format` substitutions
            to create more expressive strings. For example, instead of
            the above list of list, we wanted to have the same data in a
            simple list of `str`'s formatted a certain way, we could
            have writtent
          ''')

          with listing(
            'Using formatted string literals with `pluck()`'
          ):
            # Pluck the names and dob from the dgs collection using
            # a formatted string literal
            dgs1 = dgs.pluck('Dog: {name} ({date})')

            # Create a list indicating what we expect the above
            # pluck to produce
            expect = [
              'Ace (born 2015-05-12)',
              'Rover (born 2015-09-23)',
              'Spot (born 2015-12-22)',
              'Fluffy (born 2016-03-03)',
            ]

            # Assert our expectation
            eq(expect, dgs1)

          print('''
            In the above listing, `pluck()` notices the `{` and `}`
            marks and creates a list of `str`'s based on the string
            literal passed in with the name of the properties
            substituted with their values.

            Substitutions like this are nice but what if we wanted the
            dog names above to be uppercased, lowercase, or have some
            other common conversion performed on them. For that, we have
            **conversion flags**. You may have used 
            <a href="https://docs.python.org/3/library/string.html#format-string-syntax">
              conversion flags
            </a>
            when using Python's `str.format` function. They are
            characters appendend after a `!` to indicate a type of
            conversion to be performed. For example, we could have used
            the `u` conversion flag to produces a list of dog names with
            all uppercased characters:
          ''')

          with listing(
            'Using conversion flags with `pluck()`'
          ):
            # Pluck the names and dob from the dgs collection using
            # a formatted string literal. Note the !u appended to the
            # property name.
            dgs1 = dgs.pluck('Dog: {name!u} ({date})')

            # Create a list indicating what we expect the above
            # pluck to produce. Note the uppercased names.
            expect = [
              'ACE (born 2015-05-12)',
              'ROVER (born 2015-09-23)',
              'SPOT (born 2015-12-22)',
              'FLUFFY (born 2016-03-03)',
            ]

            # Assert our expectation
            eq(expect, dgs1)

          print('''
            There are a few other character conversion flags that can be
            used:
          ''')

          with table('Supported character conversion flags'):
            '''
              flag  performs
              ----  --------
              u     Converts the string to all uppercase letters
              l     Converts the string to all lowercase letters
              c     Converts the string using str.capitalize
              t     Converts the string using str.title
              s     Strip the string of trailing whitespace
              r     Reverses the string
            '''

          print('''
            In addition to the above list, numbers can also be used to
            truncate fields:
          ''')

          with listing(
            'Using a numeric conversion flag to truncate fields '
            'with `pluck()`'
          ):
            # Pluck the names and dob from the dgs collection using
            # a formatted string literal. Note the !1 appended to the
            # property name.
            dgs1 = dgs.pluck('Dog: {name!1} ({date})')

            # Create a list indicating what we expect the above
            # pluck to produce. Note we are only getting the first
            # letter of the name because we used !1.
            expect = [
              'A (born 2015-05-12)',
              'R (born 2015-09-23)',
              'S (born 2015-12-22)',
              'F (born 2016-03-03)',
            ]

            # Assert our expectation
            eq(expect, dgs1)

          print('''
            A useful feature of the `pluck()` method is its ability
            to handle nested properties. The following is a contrived
            example of this feature:
          ''')

          with listing('Using nested properties with `pluck()`'):
            # Use a literal string to pluck the data type of the
            # property "name". The data type is available via the
            # __class__ dunder property.
            dgs1 = dgs.pluck(
              'Property: name; Type: {name.__class__}'
            );

            # We expect to get a str representation of the `str` class.
            expect = [
              "Property: name; Type: <class 'str'>",
              "Property: name; Type: <class 'str'>",
              "Property: name; Type: <class 'str'>",
              "Property: name; Type: <class 'str'>",
            ]

            # Assert our expectation
            eq(expect, dgs1)

          print('''
            Above, we are able to get the value of `name.__class__` for
            each of the `dog` objects in the collection. Since `name`
            would get substituted for an actual string, the `__class__`
            attribute would natually be the the `str` class. 

            Obviously this isn't a very good example of using nested
            properties with `pluck()`. This is because our `dogs` object
            model is very simple. We could imagine expanding the
            object-model such that we assign a `caretaker` entity to
            each dog.  In that case, we could use `pluck()` to obtain the
            `caretaker`'s name. For example:

              # Create a caretaker
              ct = caretaker()
              ct.name = 'Jerry'

              # Assign Jerry the caretaker to each dog
              for dg in dgs:
                dg.caretaker = ct

              # Get a list of string showing the dog and their
              # respective caretaker. In this example, they will all be
              # `jerry`.
              dgs1 = dgs.pluck(
                'Dog: {name}; Caretaker: {caretaker.name}
              );

            In this exmple, we create a `caretaker` named "Jerry" and
            assign him as the caretaker for each of the dogs. Using the
            nested property name is useful since the caretaker is an
            object, and we need the value of one of its properties. Note
            that there is no limit how deeply needed these property
            expressions can be.
          ''')

    with section('Entity classse'):
      print('''
        In the last section, we outlined the behaviors and properties of
        `entities` collections, but we haven't talked much about
        `entity` objects themselves. Unlike `entities` collections,
        `entity` objects don't have that many builtin features. (This is
        ironic because subclasses of `entity` encapsulate most of the
        business logic).  In this section, we will go over the features
        of that `entity` objects get for free.
      ''')

      with section('Adding entity objects together'):
        print('''
          We've seen how we can append `entity` objects to `entities`
          collections. However, we can use the `+` on `entity` objects
          to create new collections:
        ''')

        with listing('Adding entity objects together'):
          # Add two entity objects together. The result is a new
          # collection of dogs.
          dgs1 = spot + fluffy

          # The type of collection is the generic entities class.
          type(entities.entities, dgs1)

          # The addition resulted in a collection with two elements
          two(dgs1)

          # The first element is spot and the second is fluffy
          is_(dgs1.first, spot)
          is_(dgs1.first, fluffy)

        print('''
          In the above listing, we use the `+` operator to add to `dog`
          object together to produce a collection of dogs. The remaining
          lines assert the properties of the collection that was created
          as a result.
        ''')


    with section('Events'):
      print('''
        **Events** are actions that happen to an `entity` or `entities`
        object. Callables, such as methods and functions, can be
        *subscribed* to these events. This causes the callable to be
        invoked when the event occurs. When a callable is subscribed to
        an event, it is called an **event handler**.

        All `entity` and `entities` objects have a certain number of
        builtin events. For example, the ``entities`` class has an event
        called `onadd`. We can write an event handler to capture the
        moment after a `dog` gets added to the `dgs` collection.
      ''')

      with listing('Writing an event handler'):
        # Create a simple list to store any new dogs added
        added = list()

        # Create an event handler to capture the onadd event of dgs
        def dgs_onadd(src, eargs):
          # Append the dog object that was added
          added.append(eargs.entity)

        # Subscribe the dgs_onadd function to the dgs.onadd event. The
        # `onadd` event is available to the `dgs` collection because it
        # inherits from `entities`.
        dgs.onadd += dgs_onadd

        # Create a new dog `buddy`
        buddy = dog(name='Buddy', dob='2021-05-07') 

        # Add (append) buddy to the dgs collection. This will cause the
        # onadd event to be raised. Consequently, the dgs_onadd function
        # will be called since it is subscribed to that event.
        dgs += buddy

        # We can now prove that the dgs_onadd function was called by
        # asserting that one item was added to it
        one(added)

        # We will go further to assert that `buddy` was added
        is_(added[0], buddy)

      print('''
        Reading the comments in the listing, you can probably see what's
        happening. Basically, the `dgs_onadd` is being called when
        `buddy` is appended to the `dgs` collection.

        You may be wondering what the `src` and `eargs` parameters are
        doing in the event handler. These are standard parameters that
        all event handlers must have. The `src` paramterer is a
        reference to the object that raised the event. In this case,
        `src` would be a reference to the `dgs` collection since `dgs`
        was the object that internally raised the event.

        More import, however is the `eargs` parameter. *eargs* stands
        for *event arguments*. It is an object that contains data
        specific to the event being raised. In the above example,
        `eargs` would have been of type `entities.entityaddeventargs`.
        This class contains a property called `entity` which is a
        reference to the entity being added to the collection (i.e.,
        `buddy`). `entityaddeventargs`, like all event arguments
        classes, inherits from `entities.eventargs`.

        We used a function as the event handler in the above example.
        However, it's more common within the framework to use methods.
        You may be wonder if the `self` parameter required by Python
        methods causes an issues with the event handling since all event
        handlers require a strict `src` and `eargs` parameter as their
        signature.  The answer is that the `self` parameter causes no
        problem; you just add the `src` and `eargs` parameters after
        `self`. In the listing below, notice the class called `handler`.
        It's simply instantiated and its `onadd` method is subscribed to
        the `dgs`' `onadd` event. Nothing else needed to be changed
        &mdash; except, of course, that we needed to include `self` in
        the method signature.
      ''')

      with listing('Handling events with a method'):
        # Create a simple list to store any new dogs added
        added = list()

        # Create an event handling class to capture the onadd event of dgs
        class handler:

          # Create an event handling method
          def onadd(self, src, eargs):
            # Append the dog object that was added
            added.append(eargs.entity)
        
        hnd = handler()

        # Subscribe the hnd.onadd method to the dgs.onadd event. The
        # `onadd` event is available to the `dgs` collection because it
        # inherits from `entities`.
        dgs.onadd += hnd.onadd

        # Create a new dog `buddy`
        buddy = dog(name='Buddy', dob='2021-05-07') 

        # Add (append) buddy to the dgs collection. This will cause the
        # onadd event to be raised. Consequently, the hnd.onadd method
        # will be called since it is subscribed to that event.
        dgs += buddy

        # We can now prove that the hnd.onadd method was called by asserting
        # that one item was added to it
        one(added)

        # We will go further to assert that `buddy` was added
        is_(added[0], buddy)

      print('''
        Another thing to point out is that we use the `+=` operater to
        subscribe the callable.  This is important because a
        subscription is an *append* operation: We are appending the
        callable to the collection of callables that will be invoked
        whenever an item is added to `dgs`. We could create another
        event handler and append it to the `dgs.onadd` event and it
        would also be invoked when an item was added.

        `entities` and `entity` objects have a number of builtin events
        that may be useful to create event handlers in your code.  The
        tables below list events for the `entities` classes and `entity`
        classes respectively.
      ''')

      with table('List of events in the entities class'):
        '''
        **onadd** Fired when an item is added to the collection.

        **onaftervaluechange** Fired after a change is made to any
        attribute of any item in the collection.

        **onbeforeadd** Fired before an item is added to the collection.

        **onbeforevaluechange** Fired before a change is made to any
        attribute of any item in the collection.

        **oncountchange** Fire when the number of items in the
        collection changes.

        **onremove** Fired when an item is removed from the collection.
      ''')

      with table('List of events in the entity class'):
        '''
        **onaftervaluechange** Fired after a change is made to any
        attribute of the entity.

        **onbeforevaluechange** Fired before a change is made to any
        attribute of the entity.
      ''')

      print('''
        <aside>
          An effort is currently underway to standardize the naming of
          events such that there is always a **before** and **after**
          version of any event if needed. For example, the `onadd` event
          mentioned above should be named `onafteradd` to complement
          `onbeforeadd`. This distinction usually needs to be made with
          events, however, in some events, such as `oncountchange`, this
          would probably not be necessary.
        </aside>
      ''')

      with section('Creating events'):
        print('''
          Sometimes you will need to create your own event. Lets create
          an event that is raised whenever someone renames a dog. We
          will need to recreate the `dog` class to accomplish this.
        ''')

        with listing('Creating an event'):

          # Recreate the dog class to include implement the
          # onbeforenamechange and onafternamechange events
          class dog(entities.entity):
            def __init__(name, dob):
              # Use a private variable to store the dog's name
              self._name = None

              # Set the dog's name and dob
              self.name = name
              self.dob  = dob

              # Create the two events as attributes of the dog class
              self.onbeforenamechange = entities.event()
              self.onafternamechange = entities.event()

            @property
            def name(self):
              ''' Return the dog's name. 
              '''
              return self._name

            @name.setter
            def name(self, v):
              ''' Set the dogs name.
              '''
              # If we are changing the name...
              if v != self._name:

                # Create the event argument object to store the before
                # and after
                eargs = namechangeeventargs(
                  before = self.name, after = v
                )
                
                # Fire the onbeforenamechange
                self.onbeforenamechange(self, eargs)

                # Change the name
                self._name = v

                # Fire the onafternamechange
                self.onafternamechange(self, eargs)

          class namechangeeventargs(entities.eventargs):
            ''' An eventargs class to store the before and after values
            of the event. '''
            def __init__(self, before, after):
              self.before = before
              self.after = after

        print('''
          We've made the `name` attribute an `@property` so we can
          capture the moment a value is assigned to it. We've also
          created two `events` as class attributes in the constructor
          called `onbeforenamechange` and `onaftervaluechange`. In the
          `name`'s setter, we **fire** these events before and after the
          private variable `_name` is set. As you can see, all "firing"
          an event means is calling it as if it were a function. 

          We want to let any event handler that subscribes to this event
          know what the before and after values for `name` are, so we created
          a `eventargs` class called `namechangeeventargs`. This object
          will be received by the event handlers as the `eargs` argument.
          `self` is also passed when firing the event. It will be the
          `src` argument to any event handlers. In this case, it makes
          sense to pass the same `eargs` to both the before and after
          event.

          At this point, the `dog` class works as it did before. We
          don't need an event handler to subscribe to the events; an
          event can have zero or more subscribing event handlers. Let's
          subscribe to the `onafternamechange` to complete the example
          by creating a new `dog` and by giving the object a new `name`.
        ''')

          with listing('Subscribing to our custom event'):
            # Create a list to capture the changes observed by the event
            # handler
            changes = list()

            # Create the event handler
            def dgs_onafternamechange(src, eargs):

              # Append a tuple with the before and after name of the dog
              changes.append((eargs.before, eargs.after))

            # Create Duke. Oops, we named him Duck
            duke = dog(name='Duck', date='2020-05-20'))

            # Subscribe the handler to the event
            duke.onafternamechange += dgs_onafternamechange

            # Correct the name. Oops, wrong again
            duke.name = 'Duk'

            # Corret the name one more time
            duke.name = 'Duke'

            # Set our expectations for what the `changes` list will hold
            expect = [
              ('Duck', 'Duk')
              ('Duk ', 'Duke')
            ]

            # Assert our expectation
            eq(expect, changes)

          print('''
            The event handler `dgs_onafternamechange` captures the
            before and after name changes.  We use the `name` setter to
            change the name twice. Each change causes the event handler
            to append a tuple containing the before and after values. (A
            similar implementation for this functionality can be found
            in the ORM `entity`s).
          ''')

      with section('Closing thoughts on events'):
        print('''
          For lower-level framework code, event handlers are often used
          to effectively solve programming challanges which would be
          difficult or perhaps impossible to solve if event handling
          didn't exist.  For example, in the [ORM](#bceb89cf) code, the
          `onaftervaluechange` event is used to determine if a change to
          an `entity`'s property has caused it to become *dirty*, i.e.,
          no longer matching its corresponding record in the database.
          And at the UI level, in the [DOM](#22ee9373) code, a subtype
          of `event` called `dom.event` is used to handle user
          interaction with web pages.
        ''')
            
    with section('Validation'):
      print('''
        A key feature of both `entities` and `entity` classes is there
        ability to identify their internal state as **valid** or
        **invalid**. An invalid entity which reports one or more **broken
        rules**. A broken rule is an issue with a particular property of
        the object.

        Let's recreate the `dog` class again this time giving it a
        `brokenrules` property.
      ''')

      with listing('Creating a `brokenrules` property'):
        class dog(entities.entity):
          def __init__(name, dob):
            self.name = name
            self.dob  = dob

          @property
          def brokenrules(self):
            brs = entities.brokenrules()

            if not self.name:
              brs += entities.brokenrule(
                  msg='Dog must have name', prop='name'
              )

            if not self.dob:
              brs += entities.brokenrule(
                  msg='Dog must have dob', prop='dob'
              )

            return brs

      print('''
        In the above listing, we have the simplified version of the
        `dog` class that we started with. We have added a `brokenrules`
        property which tests the `dog`'s `name` and `dob` for
        truthyness. If either property is `None` or an empty string, a
        `brokerule` object is added to a `brokenrules` collection and
        the collection is returned (which is necessary for a proper
        implementation of a `brokenrules` property.). These rules
        essentially declare that if a `dog` does not have a truthy
        values for `name` and `dob`, it is not "valid".

        Let's see what the consequences are for creating an invalid dog:
      ''')

      with listing('Creating an entity with broken rules'):
        # Create a dog with None fore name and an empty string for its
        # dob.
        derp = dog(name=None, dob=str())

        # The `isvalid` property is False
        false(derp.isvalid)

        # We have two broken rules
        two(derp.brokenrules)

        # The first broken rule is for the name property
        br = derp.brokenrules.first
        eq('name', br.property)
        eq('Dog must have a name', br.message)

        # The second broken rule is for the dob property
        br = derp.brokenrules.second
        eq('dob', br.property)
        eq('Dog must have a dob', br.message)

      print('''
        In the above listing, we deliberately instantiate the `dog`
        object `derp` to have `None` as its `name` and an empty string for
        its `dob`. At this point, we've already broken both of our rules
        that we declared above in our `brokenrules` property. Thus
        the object must be in an *invalid* state. This is demonstrated by
        the fact that `derp`'s `isvalid` property is `Fales`. `isvalid`
        is a property of any `entity` or `entities` object and simply
        indicates whether the `brokenrules` collection returned by the
        `brokenrules` property is empty. Since it returns two broken
        rules, `derp.isvalid` must be `False`. 

        Moving on, we are later able to see programmaticaly what exactly
        is wrong with the object by examining `derp.brokenrules`. This
        can be useful information when debugging and logging. It can
        also help an end user determine what input they are giving to
        cause the data to be invalid &mdash; consider that a user may be
        entering in  the dog's data in a form and they forgot to provide
        a name or date-of-birth.  The messages in the `brokenrules`
        collection could be presented to the user to help them
        understand the issue which input fields they need to correct.

        Now lets append `derp` to the `dgs` collection and see what 
        consequences an invalid `entity` has on an `entities`
        collection. 
      ''')

      with listing('Creating an entity with broken rules'):
        # The `dgs` collection starts out as "valid"...
        true(dgs.isvalid)

        # ... because it has zero broken rules
        zero(dgs.brokenrules)

        try:
          # Add the dog with the broken rules
          dgs += derp

          # Adding an invalid item to the collecton causes the
          # collection to be "invalid"
          false(dgs.isvalid)

          # The collection now has two broken rules
          two(dgs.brokenrules)

          # The first broken rule is the dog's first broken rule
          is_(derp.brokenrules.first, dgs.brokenrules.first)

          # The second broken rule is the dog's second broken rule
          is_(derp.brokenrules.second, dgs.brokenrules.second)

        finally:
          # Remove derp from the collection
          dgs.remove(derp)

          # The `dgs` collection is valid again
          true(dgs.isvalid)
          zero(dgs.brokenrules)

      print('''
        In the above listing we see that the `dgs` collection starts out
        as "valid". When we add the invalid `derp` object to the
        collection, the collection becomes invalid. The `dogs`
        collection's `brokenrules` property looks at all the objects
        within the collection and collects any broken rules they have.
        It creates a new `brokenrules` collection and returns it to us.
        That is why we are able to get `derp`'s broken rules from
        `dgs.brokenrules`. So you can see that a business rule regarding
        collection is that: *A collection is invalid if any of its
        elements are invalid* (unless, of course, a collection's
        brokenrules property has been overridden to change this
        behavior).

        You will have notice that there are no real consequences to an
        `entity` or an `entities` collection being "invalid" other than
        that its `isvalid` will be `False` and the `brokenrules`
        property will return a non-empty collection. It's up to you as a
        programmer what should happen if an entity is invalid.
        Practically speaking, however, the validity of an `entity` or
        `entities` collection will only matter to you when you are
        working with ORM entity classes. When an ORM entity is invalid,
        its persistence logic will refuse to save the entity's data to
        the database. We will cover this topic later in the section on
        [ORM validity](#012b0632) in the [ORM](#bceb89cf) chapter.

    ''')

    with section('Reasons to use brokenrules'):
      print('''
        The `brokenrules` property of both `entity` and `entities`
        classes gives us a way to encapsulate all the validation rules
        of a given class. This is an important feature because without
        it, validation rules end up being scattered throughout the
        various layers of the application such as the user interface,
        entity classes and the data tier. This scattering makes it
        difficult to determine exactly what the current validation rules
        are for a given entity.  Scattered validation logic can also
        leads to contradictory and buggy validation rules which are
        difficult to maintain.

        Another important feature of entity validation is the consistent
        reporting of data issues it afforts us. For example, if we were
        to enforce the validation rule that a dog's name must not be
        null at the data tier (e.g., using the `NOT NULL` constraint in
        a `CREATE TABLE` statement), the user would likely get a strange
        MySQL exception were he or she to forget the dog's name. Or
        perhaps they would see nothing at all because the user interface
        logic doesn't report exceptions to the user. When the user
        interface uses entity and entities classes, it can learn exactly
        what issues there are with the data being submitted by the user,
        and can report them correctly and in a consistent way thus
        enhancing the user's experience.
      ''')

    with section('Indexes'):
      ...

    with section('Distinctions with the list interface', id='042d62d4'):
      # count/len(), es[0]/es.first, sort, sorted, enumerate

  with chapter("Configuration") as sec:
    ...

  with chapter("Using the Object-relational Mapper", id='bceb89cf') as sec:

    with section('Security'):

      with section('Authorization'):
        ...

      with section('Authentication'):
        ...

    with section('Validation', id='012b0632'):
      ...

    with section('Security'):
      ...

  with chapter('The General Entity Model') as sec:
    ...

  with chapter("Authoring DOM objects", id='22ee9373') as sec:
    ...

  with chapter("Robotic process automation") as sec:
    ...

  with chapter("Crust") as sec:
    with section('Running migrations') as sec:
      ...

  with chapter("Logging") as sec:
    ..

  with chapter("Third-party integration") as sec:
    ..

  with chapter("File system") as sec:
    ..

    
    
