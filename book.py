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
          frameworks. For example, The equivalent assertion methods for
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

  with chapter("Entity and entities objects", id='64baaf7a'):
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

    with section('Using entities classes', id='eca3195f'):
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
        as well as track dogs as collection . Let's now use those
        classes to track the dogs that the dog sitting company cares
        for:
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
        Now three `dog` objects, `rover`, `spot` and `ace, are in the
        `dgs` collection (note that the word 'collection" is used
        interchangably with the phrase "entities object") We can use the
        `dgs` in a similar way to using a list to make a number of
        assertions about the collection:
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

            with listing('Retrieving item by name property'):
              spot = dgs['spot']
              eq('spot', spot)

            print('''
              This feature can be very convenient. However, we did say
              that `id` and `name` could be used. So what if `dog`
              objects had both `id and `name`? Well then both would
              work:
            ''')

            with listing('Retrieving item by id property'):
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
            # above. It's equivalent to writing the following:
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
        `entity` objects don't have that many builtin features (this is
        ironic because subclasses of `entity` typically encapsulate a
        large amount of business logic).  In this section, we will go
        over the features of that `entity` objects get for free.
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

          An alternative to the `+` operator is to use the `add()`
          method. For example, we could have created the `dgs1`
          collection above by writing:

            dgs1 = spot.add(fluffy)

          However, it's preferable to use the `+` operator since it
          allows for a more concise and readable coding style.

          `entity` objects, along with `entities` collections, also
          support [events](#26508ecd) and 
          [encapsulated validation](#4210bceb), which we will cover in
          upcoming sections.
        ''')


    with section('Events', id='26508ecd1'):
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
            
    with section('Validation', id='4210bceb1'):
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
      # TODO
      ...

    with section('How to use entities classes'):
      # TODO
      ...

  with chapter("Configuration", id="f7d18852"):
    print('''
      This chapter will deal with the process of configuring the Core
      Framework for a given environment. 

      Two files govern the configuration of the framework's environment:
      [configuration.py](configuration.py) and [config.py](config.py).
      `configuration.py` is tracked by Git. It contains a
      `configuration` class which exposes a base configuration.

      The second file, `config.py`, is not tracked by Git because it
      contains sensitive information (such as database passwords) that
      should never be commited to the source code repository. The
      `config.py` file contains a class called `config` which inherits
      directly from the aforementioned `configuration` class. The
      framework code interfaces with the `config` class to get
      basic configuration data about the environment. The `config` class
      overrides properties from `configuration` to provide sensitive
      information to the framework, and to provide custom configuration
      that are appropriate for a given environment. Since we do not
      track `config.py`, you may not have it even if you have cloned the
      repository. You may need to reach out to a work colleague or
      manager for a copy.

      The `configuration` base class contains configuration for logging
      to syslog, Boolean properties such as `inproduction` and
      `indevelopment` to flag to the framework code which type of
      environment its in, and an `accounts` property` which return a
      collection of accounts data (used for logging into databases and
      the like). As mentioned above, the `config` class is used to
      override these properties to provide sensitive and
      environment-specific configurations.

      To access a configuration value, simply instantiate the `config`
      class and read its property. For example, to determine which
      environment we are in, we can do the following.
    ''')

    with listing('Reading configuration values'):
      from config import config
      cfg = config()

      eq('development', cfg.environment)
      true(cfg.indevelopment)
      false(cfg.inproduction)

    print('''
      The above code tells us that the current environment the framework
      is in is *development* and not production. This knowledge can
      obviously be useful for a number of use cases. For example, we
      would want to ensure that integration tests aren't run in a
      production environment (in fact, there is code in
      [tester.py](tester.py) to do just that.
    ''')

  with chapter("Using the object-relational mapper", id='bceb89cf'):
    with section('Introduction'):
      ...

    with section('Defining classes'):
      print('''
        In the chapter on [entities](#64baaf7a), we created a `dogs`
        collection and an `dog` object. Though these classes could
        manage data about dogs, they could not persist that data to a
        database. Let's recreate those classes to be ORM class.
      ''')

      with listing('Creating a ORM class'):
        # Import the orm module
        import orm
        from datetime import date

        # Create the dogs collection this time inheriting from
        # orm.entities instead of entities.entities
        class dogs(orm.entities):
          pass

        # Create the dog entity this time inheriting from
        # orm.entity instead of entities.entity
        class dog(orm.entity):
          name = str
          dob = date

      print('''
        There are a number of things to point out here. First is that
        the classes inherit from the [orm](orm.py) entities classes
        instead of the [entities](entities.py) classes.

        As you can see, we are defining the attributes of `dog` and
        assigning them data types: the `dog`'s name is going to be of
        type `str` and the `dob` will be of type `date`. Now we can
        instantiate the dog class and assign values to its `name` and
        `dob` attributes.
      ''')

      with listing('Assigning values to entity attributes'):
        # Create a new dog entity
        lassie = dog()

        # Note that the str attributes defaults to an empty string while
        # the date data type defaults to None.
        empty(lassie.name)
        none(lassie.dob)

        # Assign the attributes
        lassie.name = 'Lassie'
        lassie.dob = date(1938, 12, 17)

        # Assert that the assignments took place
        eq('Lassie', lassie.name)
        eq(date(1938, 12, 17), lassie.dob)

      print('''
        The `name` defaults to an empty string while the `dob` defaults
        to `None`. We make assignments to the attributes then assert
        that the assignments worked correctly.

        <aside>
        At this point you are probably wondering at the class's
        definition. Let's take another look at it:

          class dog(orm.entity)
            name = str
            dob = date

        Given that definition, it would seem that the `name` property
        would default to `str` and `dob` would default to `date`.

        When the `class dog(orm.entity)` statement is executed by
        Python, the *metaclass* for the `orm.entity` base-class is
        invoked. This code reads the body of the `dog` class as defined
        above and maps `name` and `dob` to internal structures. Then,
        the metaclass removes these assignments, but retains the
        information they provided.  Assigning values to the attributes
        requires the ORM to use the internal structure to store and
        retrieve the correct data, even though the attributes seem to
        behave as simple Python attributes.
        </aside>

        In addition to the attributes we've defined on the class, there
        are several default attributes we get for free. Every ORM entity
        class has an **`id`** attribute which can be used to retrieve or
        set a unique identifier for the object. Let's take a look at
        this attribute in action:
      ''')

      with listing('The `id` attribute'):
        from uuid import uuid4
        dg = dog()
        type(uuid, dg.id)

      print('''
        From the listing above, we can tell that the value returned from
        the ``id`` property is of type `uuid4`. We can also see that the
        id has already been generated for us (otherwise, `dg.id` would
        be of type `NoneType)`. So there is no need to set the `id`, and
        in general, you should accept the id that is generated. 

        If you are familiar with UUID's, you will have guessed that the
        value returned is a random, 16 bytes value. These values are so
        large that that they are virtually guarenteed to not repeat
        themselves thus they make excellent identifiers for entity
        objects. Later, we will see that the `id`'s value is used as the
        primary key when the entity is stored in the database.

        ORM entity objects also contain a **`createdat`** and
        **`updatedat`** property. The `createdat` contains the datetime
        that the entity was first saved to the database. The
        `updatedat` property contains the datetime that the entity was
        last modified in the database.
      ''')

      with listing('The `id` attribute'):
        dg = dog()
        none(dg.createdat)
        none(dg.updatedat)

      print('''
        As you can see in the listing, when we first create the `dog`
        object, its `createdat` and `updatedat` attributes are both
        `None`. This is because we haven't saved them to the database
        yet. When we cover persistence later in this chapter, we will
        see that these attributes will return datetime values when we
        save entity objects to the database.

        ORM entity object also come with a `proprietor` and `owner`
        attribute. These will be covered in detail in the
        [Security](#ea38ee04) section later in this chapter. In short:
        the `proprietor` attribute is a reference to the *party*
        (such as a company or organization) that legally owns the
        record. The `owner` attribute is a reference to the *user*
        account that created the record. 
      ''')

    with section('Class complements', id='547592d9'):
      print('''
        Unlike regular `entity` classes, ORM entity classes need a
        complementary `entities` class. If we declared `dog` without a
        `dogs` entities class, or vice-versa, we would get an error.

        The ORM automaticaly tries to find the complement by guessing
        what the plural name of the class would be and discovering it
        through Python's reflexion facilities. 

        Entity complements are necessary for internal ORM functionality.
        However, we are able to see what the ORM has decided the
        complement is:
      ''')

      with listing('Getting entity compliments'):
        # The dog class knows its corresponding collection class
        is_(dog.orm.entities, dogs)

        # A dog objects knows its corresponding collection class
        is_(dog().orm.entities, dogs)

        # A dogs collection class knows its corresponding entity class
        is_(dogs.orm.entity, dog)

        # A dogs collection object knows its corresponding entity class
        is_(dogs().orm.entity, dog)

      print('''
        Even though our class declarations never denote an
        association between `dog` and `dogs`, we can see that the two
        classes, or objects created therefrom, know about each
        other.

        In the above code, we introduce the `orm` attribute that all ORM
        classes and objects have. We will discuss this attribute more in
        [The `orm` attribute](#e7a9db8e) section below.

        Core Framework usually correctly discovers the complements of ORM
        classes by using the
        [inflect](https://pypi.org/project/inflect/) library to
        determine the plural of an `entity` class's name. In cases where
        `inflect` doesn't do the right thing, you can override it by
        assigning an `entities` attribute in the `entity`'s class
        declaration:
      ''')

      with listing('Forcing an entities complement'):
        # Create a collection of viruses insisting the proper spelling
        # is "virii".
        with virii(orm.entities):
          pass

        with virus(orm.entity):
          # Cause `virii` to be the `virus`'s collection class
          entities = virii

          # Create some ORM attributes
          name = str
          discovered = date

        # The virus class knows its corresponding collection class
        is_(virus.orm.entities, virii)

        # A virii collection class knows its corresponding entity class
        is_(virii.orm.entity, virus)

    with section('The `orm` attribute', id='e7a9db8e')
      print('''
        In the above code listings we can see that entity and entities
        classes, along with the objects created from those classes, have
        an `orm` attribute. The `orm` attribute allows us to access
        lower-level properties and behaviors of the ORM. 

        Normally when writing or using entities, you will not use the
        `orm` attribute. However, its features can be useful for certain
        types of programming tasks like writting automated tests. The
        `orm` attribute can be useful for debugging, and can help
        workaround bugs in the ORM.

        As you progress through this chapter, you will see the `orm`
        attribute used to demonstrate various things. However, remember
        that it was designed for use by the Core Framework; it was
        not intended for use by entity class designers or users of those
        classes. It just so happens that it provides a nice way to learn
        about certain aspects of entities. Of course, some of the
        members of the `orm` attribute should be considered private and
        not be used unless you really know what you are doing. After you
        have read this chapter, you should have an understanding about
        which ones are safe to use.
      ''')

    with section('Creating the `dog` table'):
      print('''
        So far, we've create the `dog` entity class, instantiated it and
        assigned values to its properties. However, the whole point of
        having ORM objects is so we can persist their data to a
        database &mdash; so let's do just that.

        <aside class="note">
          If you want to follow along with the upcoming example, you
          will want to make sure your environment is configured
          correctly for database access. Read the chapter
          [Configuration](#f7d18852) for assistance.
        </aside>

        The first thing we will need to do is to create a table to
        hold the records for the dogs. Since ORM entity class contain
        the complete data definitions for the entity, the ORM is used to
        create the table for us. Let's first have a look at the `CREATE
        TABLE` statement the ORM will issues to the database:
      ''')

      with listing('Generate a CREATE TABLE statement'):
        # Create a string that contains the CREATE TABLE statement
        expect = self.dedent('''
          CREATE TABLE `main_dogs`(
              `id` binary(16) primary key,
              `proprietor__partyid` binary(16),
              `owner__userid` binary(16),
              `createdat` datetime(6),
              `updatedat` datetime(6),
              `name` varchar(255),
              `dob` date,
              INDEX proprietor__partyid_ix (proprietor__partyid),
              INDEX owner__userid_ix (owner__userid)
          ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        ''')

        # The `orm.createtable` attribute returns the CERATE TABLE
        # statement for the entity
        eq(expect, dog.orm.createtable)

      print('''
        In addition to the `name` and `dob` columns, the ORM will create a
        number of other standard columns that correspond to the
        entity object's attributes described above such as `id`,
        `createdat` and `updatedat`. 

        Note that `name` is defined as a `varchar(255)`. Since we
        defined `name` as a `str` in its class definition, the ORM has
        translated this into what it belives is the closest MySQL
        equivalent. A similar translation was made for `dob`s data
        type: The ORM translated the Python class `datetime.date` to the
        MySQL data type `date`. 

        The `id` field is a binary field that stores 16 bytes of binary
        data.  As you will remember from the above discussion on entity
        `id` attributes, their values are UUID's. Since all UUID's are
        16 bytes, the primary key is a `binary(16)` which the ORM will
        use to store the id's value. You can also see that with the
        `proprietor__partyid` and `owner__userid` fields, a `binary(16)`
        field is used because these fields will be used to store the
        id's of those entities being referenced. Indexes are created on
        these fields to allow for fast lookups on these reference
        fields.

        So now that we know what `CREATE TABLE` statement the ORM will
        send to the database to create the table, lets cause the ORM to
        do just that:
      ''')

      with listing(
        'Issue the `CREATE TABLE` statement to the database'
      ):
        dog.orm.recreate()

      print('''
        The `recreate()` method first drops any table that exists then
        creates the table using whatever is returned from
        `orm.createtable`. 

        <aside class="note">
          Normally as a programmer, you won't need to know how to create
          tables except in rare circumstances. Table creation and
          modification are usually done by the `crust` command. See the
          section [Running migrations](#8c9baa57) in the
          [Crust](#0227a7b7) chapter.
        </aside>

        Now that the table exists in the database, we are able to
        create a new `dog1 object and save it to the database.
      ''')

      with listing('Persist an ORM entity'):
        # Run in an overridden context to avoid accessibility methods
				with orm.override():

          # Create and save and retrieve dog as root user
					with orm.sudo():
            # Instantiate and set attribute values
						d = dog()
						d.name = 'Rex'
						d.dob = 'Jun 10, 1998'

            # Assert the builtin attributes createdat and updatedat
            none(d.createdat)
            none(d.updatedat)

            # Save the new dog to the database
						d.save()

            # Load the saved dog from the database back into a new dog
            # object `d1`
            d1 = dog(d.id)

          # Make assertions about the d and d1 objects
          eq('Rex', d.name)
          eq('Rex', d1.name)

          eq(primative.date('Jun 10, 1998'), d.dob)
          eq(primative.date('Jun 10, 1998'), d1.dob)

          eq(d.id, d1.id)

          # Assert the builtin attributes createdat and updatedat
          type(primative.datetime, d.createdat)
          type(primative.datetime, d.updatedat)

          eq(d.createdat, d1.createdat)
          eq(d.updatedat, d1.updatedat)
          
          # updatedat and createdat are equal to each other when entity is
          # created.
          eq(d.updatedat, d.createdat)

        print('''
          The first line puts the persistence code in an `override`
          context. This line can be ignored for the most part. It simply
          causes the persistence code to ignore accessibility methods
          which will be covered in the [Authorization](#54014644) section
          in the [Security](#ea38ee04) chapter.

          The next `with` statments sets the user to `root`. The ORM
          demands that a user be set before we can persist entity objects.
          Again, this will be covered later in the
          [Authorization](#54014644) section in the [Security](#ea38ee04)
          chapter.

          Once we are finally in a valid context, we can instantiate a `dog`
          object and set its attributes. The `createdat` and `updatedat`
          attributes are `None' beore we save the `dog` to the database.
          Calling the `dog`s `save()` method causes a record to be created
          in the `dog`'s table. The attribute values we set are saved to
          the `name` and `dob` fields of the table. The `createdat` and
          `updatedat` attributes will contain a datetime equal to the
          moment the `dog` was saved.

          After the object has been saved, we are able to retrieve the
          object from the database. We do this by passing the `id` to the
          entity class's constructor. The resulting object, `d1`, should
          be equivalent to the original `d`, as we assert at the end of
          the listing.
        ''')

      with section('Behind the scenes: inserting and retrieving'):
        print('''
          As you may have guessed, when we called the `save()` method, the
          ORM constructed an `INSERT` statement based on `d`'s attributes
          and sent it to the database. You can view the `INSERT` statement
          that the ORM will send by calling by using the 'getinsert`
          method:

            sql, args = d.orm.mappings.getinsert()

          The `sql` variable above will have the *parameterized* `INSERT`
          statement:

            INSERT INTO main_dogs (
              `id`, `proprietor__partyid`, `owner__userid`, 
              `createdat`, `updatedat`, `name`, `dob`
            ) VALUES (_binary %s, %s, %s, %s, %s, %s, %s);

          The `%s` placeholders are replaced by the elements in `args`
          list.

          When we retrieved the `dog` object via the constructor, the ORM
          built an `SELECT` statement, sent it to the database, and
          populated the attributes of `d1` with the results. We can get
          the `SELECT` statement using the `orm`'s `select` property:

            sql, args = d.orm.select

          Like the `INSERT` statement, the `sql` variable will hold a
          parameterized query like the one below:

            SELECT * FROM main_dogs WHERE id = _binary %s

          The `%s` placeholder will be replaced with the first element of
          `args`, which will be a binary representation of the `dog`'s
          id.

          Later in the chapter, when we modify the `dog` entity and
          delete it, we will see that the ORM creates and issues
          `UPDATE` and `DELETE` statements respectively to the database
          similar to the ones above.
      ''')

      with section('Updating an entity'):
        print('''
          So far, we've seen how to use a simple entity to save and
          retrieve its data to and from a database. Next we will
          demonstrate how to update the entity's values in the database.
          After that, we will learn how to delete the entity's record.. Let's take
          our `dog` object `d` and change the value for its `name`
          attribute. Then we will persist the changes to the database.
        ''')

        with listing('Update an entity'):

          # Adjust the security context so we can successfully update
          # the dog
          with orm.override(), orm.sudo():

            # Update the dog name
            d.name = 'Patches'

            # Persist the dog
            d.save()

            # Get a reloaded instance of the dog
            d1 = d.orm.reloaded()

            # Assert that the reloaded dog matches the original dog
            eq(d.id, d1.id)
            eq(d.name, d1.name)

            # This assertion proves that the entity was successfully
            # updated in the database
            eq('Patches', d1.name)

          print('''
            As in the prior example, you can ignore the `with` statement.
            We will cover security in the [Security](#ea38ee04) chapter.

            The next line changes the `dog`'s `name` attribute. As in the
            prior example, we call the entity`s `save()` method. The
            `save()` method issues an `UPDATE` statement to the database
            that changes the database record's `name` field to "Patches".

            The rest of the listing demonstrates that the record was
            actually updated in the database. The next line introduces the
            `orm.reloaded()` method. This method issues a `SELECT` query
            to the database to reload the entity by its primary key. It is
            identical to writing:
                
                d1 = dog(d.id)

            Once we have a reloaded version of the dog objects, we can
            demonstrate that its attributes match the original `dog`
            object `d`, and that the reloaded version's `name` is
            "Patches". This proves the `save()` method successfully
            changed the entity's record in the database.
          ''')

      with section('Behind the scenes: updating'):
        print('''
          Because we had already saved the `dog` object in a prior
          listing, the dog object new it was no longer a **new** entity.
          Thus, calling the `save()` method would not result in another
          `INSERT` statement being sent to the database. However, since
          its `name` attribute had been saved, the object entered into a
          **dirty** state. An entity enters into a dirty state whenever
          it detects that its attributes' values don't all equal the
          values in its corresponding record in the database. (We will
          cover the *new* and *dirty* persistence variables later in the
          section called [Behind the scenes: persistence
          varibles](#45e881e3)). Since the `dog` object knew it was
          dirty, it issued an `UPDATE` statement to the database to
          change the `name` field to "Patches". You can get the `UPDATE`
          statement by calling the `dog`'s `getupdate()` method:

            sql, args = d.orm.mappings.getupdate()

          The `sql` variable above will have a parameterized `UPDATE`
          statement. 

            UPDATE main_dogs
            SET 
              `proprietor__partyid` = %s, 
              `owner__userid` = _binary %s, 
              `createdat` = %s, 
              `updatedat` = %s, 
              `name` = %s,
              `dob` = %%s
            WHERE id = _binary %s;

          The `%s` placeholders will be replace by the values in
          `args` before being sent to the database. Though each of the
          `dog`'s fields are in the `SET` clause, it's the `name` field
          that matters since that has the new value. The `updatedat`
          field will be set to the current timestamp to indicate when
          the record was last updated.
        ''')

      with section('Deleting an entity'):
        print('''
          As you would probably expect, the ORM allows us to easily
          delete an entity permanently from the database.
        '''

        with listing('Deleting an entity'):
          # Adjust the security context so we can successfully delete
          # the dog
          with orm.override(), orm.sudo():

            # Delete the dog from the database
            d.delete()

            # Import the db module
            import db

            # Attempting to load the deleted record results in a
            # db.RecordNotFoundError exception
            expect(db.RecordNotFoundError, d.orm.reloaded)

        print('''
          As you can see, deleting an entity is as simple as calling
          its `delete()` method. We can prove that the database record
          was successfully deleted by trying to reload it. We `expect`
          a `db.RecordNotFoundError` to be raised when an attempt is
          made to reload it. Though the record is deleted, the `d`
          entity object still exists in memory unaltered, so you are
          able to interogates its attributes if you need to. You can
          even resave it if you want.
        ''')

        with aside('Soft deletes', id='2b7b0ae4'):
          '''
          You may expect the ORM to support a "soft delete" option
          where the ORM allow you to call a delete method which sets a
          flag on the record that marks it as 'deleted' without
          actually removing the record from the database. Soft deletes
          are not currently supported by the ORM.  Regardless, you
          should ensure that you database's disaster recovery plan is
          robust enough to allow for the recovery of mistakenly
          deleted data in a timely manner.  You are, of course, free
          to implement an archive flag on the entity if you want.
          '''

      with section('Behind the scenes: deleting'):
        print('''
          The `delete()` method markes the dog object for deletion (by
          setting the `d.orm.ismarkedfordeletion` persistence variable
          to True, then immediately calls the `save()` method:

            def delete(self):
                self.orm.ismarkedfordeletion = True
                self.save()

          Using a flag to mark the entity for deletion allows for
          defered deletion which may be useful in some situations. Note
          that marking an entity for deletion is not a soft delete (see
          the [aside on soft deletes](#2b7b0ae4); setting the
          `ismarkedfordeletion` does nothing more than flag the `save()`
          method to issue a `DELETE` statement to the database when
          called.

          The `DELETE` statement that is used can be obtained from the
          `getdelete()` method:

            sql, args = d.orm.mappings.getdelete()

          The `sql` varible will contain the parameterized `DELETE`
          statement:

            DELETE FROM main_dogs WHERE id = _binary %s;

          The first element of the `args` varible will contain the
          primary key of the `dog` being deleted.
        ''')

      with section(
        'Behind the scenes: persistence state varibles', id='45e881e3'
      ):
        print('''
          In the above sections, we touched on entity **persistence state
          variables**. In this section, we will delve deeper in to see how
          they work.

          Persistence variable are attributes of an entity's `orm`
          object. There are three persistence state `isnew`, `isdirty`
          and `ismarkedfordeletion`. 

          When we first instantiate an entity, it will be in a *new*
          state:

            d = dog()
						d.name = 'Rex'
						d.dob = 'Jun 10, 1998'
            true(d.orm.isnew)

          The *new* state implies that the entity has no corresponding
          record in the database. Thus, a call to the `save()` method
          will cause an `INSERT` statement to be issued to the database.
          If the `INSERT` succeeds, the `isnew` flag will be set to
          `False:

            d.save()
            false(d.orm.isnew)

          Now that the `isnew` variable is `False`, any subsequent calls
          to `save()` will involve no interaction with the database.
          However, when we change an attribute's value, the ORM will
          notice the change and cause the `isdirty` flag to be True:

            false(d.orm.isdirty)
            d.name = 'Patches'
            true(d.orm.isdirty)

          Now when we call `save()`, the ORM will note that the entity
          is dirty and *not* new, and will consequently issue an
          `UPDATE` statement to the database to update the corresponding
          record with the modified values:

            d.save()
            false(d.orm.isdirty)

          Finally, there is the *marked-for-deletion* state indicated
          by the `orm` object`s `ismarkedfordeletion` flag. This is a
          simple flag that, when set to `True`, causes a call to
          `save()` to delete entity's corresponding record:

            d.orm.ismarkedfordeletion = True
            d.save()
            expect(db.RecordNotFoundError, d.orm.reloaded)

          Above, the `save()` method observes that `ismarkedfordeletion`
          is `True` and consequently issues a `DELETE` statement to the
          database to delete the entity's corresponding record in the
          database. Note, however, that the `delete()` method can do the
          above job as well:
            
            d.delete()
            expect(db.RecordNotFoundError, d.orm.reloaded)
        ''')

      with section('The save() method'):
        print('''
          As we have seen, the `save()` method of an entity class
          *persists* the entity to the database, i.e., it issues an
          `INSERT`, `UPDATE` or `DELETE` statement, or no statement at
          all, depending on the values of the persistence variables.

          Normally the `save()` method is called without any parameters,
          however it is possible to pass in zero or more entity objects
          to have them saved as well. Considere the following:
        ''')

        with listing():
          # Create three dogs
          d = dog()
          d.name = 'Rex'

          d1 = dog()
          d.name = 'Bandit'

          d2 = dog()
          d.name = 'Benji'

          # Save the dogs
          d.save(d1, d2)

          # Assert that the dogs made it to the database
          expect(None, d.orm.reloaded)
          expect(None, d1.orm.reloaded)
          expect(None, d2.orm.reloaded)

        print('''
          In the above listing, we create the `dog` "Rex", "Bandit" and
          "Benji", then we save "Rex" passing to its `save()` method
          "Bandit" and "Benji". Each `dog` will be saved to the
          database; that is to say, each `dog` will have their `save()`
          method called.

          The `save()` operation performed in an **atomic transaction**:
          that is to say: if there is an exception raised during any
          part of the saving process, any changes that were made to the
          dataase during the save will be rolled back. An exception can
          happen at any time during the save process and can result from
          from anything from a network problem or invalid data in the
          entity.
        ''')

      with section('ORM data types'):
        print('''
          As you have seen, defining an attributes type is rather
          simple. Types in the ORM behave as much like Python
          types as possible in order to make using them easy for the
          developer.  For example, to define an attribute, we use a
          reference to the builtin Python class `str` instead of
          creating a new, ORM-specific reference (such as `orm.string`).
          Additionally, attributes defined as `str` default to empty
          strings because that is the default for a Python `str`.

          The simplicity of the typing system, so far, would seem to
          ignore the need to define typical database constraints such as
          a maximum length given to the `varchar` type, or the precision
          and scale of a float. On the contrary, these additional
          parameters can be defined during class definition. It turns
          out, however, that they are almost never needed because the
          default constraints are sufficient. Consider that under most
          circumstances, you just want your variable to be a string,
          integer, decimal or Boolean.  However, when the need arises to
          provide additional constaints to the data types (for example,
          to improved performence) that capability does exist.
        ''')

        with section ('`str` attributes'):
          
          with listing('Example'):
            
            class persons(orm.entities):
              pass

            class person(orm.entity):
              # Declare a str called `name`
              name = str

              # Declare a `phone` number property that must be at least
              # 7 characters, and can be a maximum of 9.
              number = str, 7, 9

            per = person()

            ''' Test the name property '''
            # Defaults to an empty string
            empty(per.name)

            # Bothe `name` and `number` are emtpy str's by default so
            # the `per` objects starts life as invalid.
            invalid(per)

            # Assign a sting to the name attribute with surrounding
            # whitespace.
            per.name = '   Peter Griffin    '

            # Note that the surrounding whitespace is removed
            eq('Peter Griffin', per.name)

            # The str() function is used to convert non-str values 
            per.name = 123

            eq('123', per.name)
            type(str, per.name)

            ''' Test the number property '''

            # Defaults to an empty string
            empty(per.phone)

            # Set the phone number property to a valid value
            per.number = 2053921  # 7 characters

            # Notice the conversion to a str value
            eq('2053921', per.number)
            type(str, per.number)

            # Now that the attributes are non-empty str, `per` is valid
            valid(per)

            # Make `per` invalid again by assigning an invalid sting to
            # `number`
            per.number = 1234567890  # 10 characters; to short
            invalid(per)
            
            per.number = 123456  # 6 characters; too short
            invalid(per)

            per.number = 123456789  # 9 characters; just right
            valid(per)
        print('''
          `str` attributes can contain (and reliabily persist) any
          string of unicode character. By default, `str` attributes are
          empty strings (`''`).  Like all types, `str` attributes can be
          set to `None` which will be saved to the database as `null`.  

          By default, a `varchar(255)` column will be created for `str`
          attributes in the entity's database table. If we declare the
          maximum character to be more than 4000, the database type
          becomes a `longtext`. If the number of maximum characters is
          below 4000 and the minimum number of characters equals the
          maximum number of characters, a database type of `char` is
          used.  In the listing abavo, we can see how a developers can
          specify the minimum and maximum value. However, if you want a
          fixed-length string, it is recommended you use the
          [chr](#fe56ed82) type-alias instead. If you want to store
          really long strings of text, such as for a user's bio, or a
          blog entry, it is recommend that you use the `text`
          pseudotypes](#0822acc6) instead of specify a large maximum.

          Notably, `str` attributes automatically strip any surrounding
          whitespace in a string they are assigned. This is virtually
          always what you want (except for rare cases, such as with a
          password). This makes it possible to accept user input which
          may have accidental whitespace at the begining or end without
          having to remember to call `str.strip` yourself before
          assigning it to the attribute. Currently, there is no way to
          disable this automatic stripping (although it shouldn't be
          difficult to develop a way, possibly with the use of a context
          manager).

          `str` attributes use the `str()` function to convert non-`str`
          Python data types to `str` data types. For example, if we
          assign an integer to a `str` attribute, it will immediately be
          converted to a `str`. `str` attributes always return a value
          of type `str` no matter what they are assigned (unless, of
          course, the attribute's value is `None`).

          `str` attributes must, by default, contain at least 1
          character for their entity object to be considered valid
          (`.isvalid`) (even though `str` attributes default to empty).
          This is because empty `str` attributes are rarely meaningful
          and are often synonymous with `None` (`null') values. If you
          intend to indicate that there is no value for a given
          `str` attribute (e.g., because a  user has chosen to leave a
          field blank in the user interface), it is recommended that you
          set the attribute to `None`. In cases where you do need to
          have the option of assiging a `str` attribute both empty
          `str`'s and `None` values, just specify a minimum value of 0.

          Since the database type for a `str` attribute is, by default,
          `varchar(255)`, you would be correct in guessing that 255 is
          the maximum number of characters the attribute can have in
          order for the entity to be considered valid. As you can see in
          the listing above, we can change the minimum and maximum size
          for a `str` attributes in the declaration: It's rare that you
          would need to specify the size of the `str` attribute,
          however. If you need a an attribute that can contain more text
          than 255, you should consider a [text](#0822acc6) attribute
          instead.
        ''')

        with section ('`chr` attributes', id='fe56ed82')
          print('''
            Occasionally, you will want an attribute that can only
            contain a fixed-width string. A fixed-width string is one
            where the only valid value is one that contains an exact
            number of  pre-declared characters.  In that case, the `chr`
            attribute is handy.
          ''')

          with listing('`chr` example'):
            class debits(orm.entities):
              pass

            class debit(orm.entity):
              """ Represents a debit card.
              """

              # The pin number for the debit card
              pin = chr(4)

            dbt = debit()

            # Assign the pin a number
            dbt.pin = 12345

            # Note that the pin gets converted to a str
            eq('12345', dbt.pin)

            # However, the pin number must be exactly 4 characters so
            # this debit card is "invalid"
            invalid(dbt)

            # Assign the pin attribute a valid number
            dbt.pin = 1234

            # Now the entity is valid
            valid(per)

          print('''
            In the above example, a `debit` card class is declared with
            a `pin` number that must be exactly 4 characters. Since pin
            numbers (at least in this example) must be 4 characters,
            using `chr(4)` is a convenient choice to enforce this
            constraint. Anything more or less that 4 characters would
            make the `debit` card entity invalid.

            Since `chr` types are fixed-width unicode strings, they are
            stored as `char` types in the database.

            Note that `chr` types are considered alias-types since they
            are just a shorthand for declaring a fixed with `str`
            attribute. For example, the above `debit` card class could
            have been written:

              class debit(orm.entity)
                pin = str, 4, 4

            As far as the ORM is concerned, the above notation is
            equivalent to using `chr(4)'. However, by using the `chr`
            alias-type, we are better able to express the fact that
            `pin` numbers are fixed-width &mdash; and we can do so with
            fewer characters.
          ''')

        with section ('`text` attributes', id='0822acc6'):
          print('''
            The `text` data type is similar to the `str` data type but
            is useful for situations where the attribute needs to store
            large amounts of text. `text` attributes are good for things
            like user bio's, blog posts, news articles, etc.

            `text` attributes must have at least one character and a
            maximum of 65,535 characters. If the attribute contains an
            empty str, its entity is considered invalid. If you need to
            indicate that there is no text for the attribute, assign the
            `None` value to it. 

            `text` attributes are stored in MySQL `longtext` columns in
            the database.

            `text` attributes are alias-types: using the `text` data
            type is equivelent to using:
              
              str 1, 65_535

            Though most types are denoted by builtin Python types (e.g.,
            the `str` ORM type is denoted by the Python `str` type),
            `text` types are denoted by referencing the internal `orm`
            class `orm.text`.
          ''')

          with listing('Using `text` attributes'):
            
            # Create a person entity
            class person(orm.entity):
              # Create a text attribute
              bio = orm.text

            per = person()

            # 65535 is a valid number of characters
            per.bio = 'X' * 65535
            valid(per)

            # Any more characters and the person becomes invalid
            per.bio += 'X'
            invalid(per)

        with section ('bool` attributes'):
          print('''
            `bool` attributes are used to store `True`/`False` values.
            They are also nullable, meaning you can assign a value of
            `None` to them.

            Like the Python `bool` types, `bool` attributes default to
            `False`.

            The MySQL database type for `bool` attributes is `bit`.
          ''')

          with listing('Using `bool` attributes'):
            # Create a person entity
            class person(orm.entity):
              # Create a bool field
              active = bool

            per = person()

            false(per.active)

            per.active = True

            true(per.active)

            per.active = None

            none(per.active)

        with section ('`int` attributes'):
          print('''
            `int` data type are used when there is a need to store a
            non-decimal, numeric value.

            By default, their database columns are of `INT SIGNED`. This
            means that any number equal to or greater than
            -2_147_483_648 and less than or equal to 2_147_483_647 is a
            valid value. However, it is possible to change the minimum
            and maximun value in which case the database type will
            change accordingly. For example, if you declare an `int` as
            follows:

              class myclass(orm.entity):
                myattr = int, -128, 127

            The underlying database type will be a `TINYINT` because a
            database field declared as such could hold an integer
            between -128 and 127. The ORM tries to find the smallest
            database type for a given range of values when deciding upon
            an integer-based data type. The ORM will may choose between
            `TINYINT`, `SMALLINT`, MEDIUMINT`, `INT` and `BIGINT`.
            Additionally, it will only cause them to be `SIGNED` if the
            range allows for a negative value, otherwise they will be
            declared as `UNSIGNED`. This may be important information
            when trying to find ways to improve the performance of the
            database. However, as an ORM user, it shouldn't concern you
            much since the only thing that will matter when programming
            ORM entity objects will be the range of allowable values.
            Typically, you can start with a regular `int` remembering to
            resist the temptation to optimize prematurely.
          ''')

          with listing('Using `int` attributes'):

            class person(orm.entity):
              age = int

            per = person()

            # 44 is a valid `int`
            per.age = 44
            valid(per)

            # -2_147_483_648-1 would be invalid
            per.age = -2_147_483_648 - 1
            invalid(per)

        with section ('`float` attributes'):
          print('''
            `float` attributes represent floating-point numbers. They
            are similar to Python `float`s but conform to MySQL
            `DOUBLE`s since that is their underlying database type.

            The `DOUBLE`s have a default precision of 12 and a default
            scale of 2. If needed these values can be change using the
            following notation:

              class myentity(orm.entity):
                myflt = float, 13, 3

            Above, `myflt` has a precision of 13 and a scale of 3.

            `floats` are useful in scientific applications but can cause
            problems in business applications due to the fact that they
            store approximate values but not exact value. You can easily
            see this problem by multipling .3 by 3 in the Python REPL:

              >>> .3 * 3
              0.8999999999999999

            Due to the lack of precision, you don't get the .9 you would
            expect. Consequently, `float`s are never used by the GEM.
            [`Decimal`](#794f2ac1) data types are preferred since they
            don't have this precision problem.
          ''')

          with listing('Using `float` attributes'):
            class person(orm.entity):
              weight = float

            per = person()

            # Assign a valid floating-point number
            per.weight = 166.66
            eq(166.66, per.weight)
            valid(per)

        with section ('`Decimal` attributes', id'794f2ac1'):
          print('''
            The `Decimal` data type is used to store numeric values that
            can contain decimal point. Unlike the `float` data type, the
            `Decimal` data type presevers exact precision. `Decimal`
            types are used whenever precision needs to be preserve, for
            example, when money is invoved.

            The underlying database type for `Decimal` values is
            `DECIMAL(12,2)` (a precision of 12 and a scale of 2).
            Consequently, numbers between -999,9999,999.99' and 
            9,999,999,999.99' are valid.

            If the precision or scale needs to be change, the following
            syntax can be used:

              import decimal
              class myentity(orm.entity):
                mydec = decimal.Decimal, 14, 3

            Above, we have declared `mydec` to have a precision of 14
            and a scale of 3.

            As you can see in the above example, the `Decimal` types are
            denoted by the `Decimal` class in the `decimal` module. This
            is also the Python type that is used to store the actual
            value in memory. It's convential to `import` `Decimal` as an
            alias:

              from decimal import Decimal as dec

            This way we can use `dec` to denote the `Decimal` type.
            Thus the above example should have been written.

              from decimal import Decimal as dec

              class myentity(orm.entity):
                mydec = dec, 14, 3
            
            Though the attribute always returns a `decimal.Decimal`
            Python type, you can assign Python `str`s, `int`'s or `floats`
            to the attributes. Internally, it will convert these values
            using the `decimal.Decimal` constructor after stringifying
            them first.

              decimal.Decimal(str(x))
          ''')

          with listing('Using `float` attributes'):
            from decimal import Decimal as dec
            class person(orm.entity):
              weight = dec

            per = person()

            # Set with an int
            per.weight = 166

            # Returns a Decimal value of 166
            eq(dec('166'), per.weight)

            # Always returns a Decimal type
            type(dec, per.weight)

            # Set with a float
            per.weight = 166.66
            eq(dec('166.66'), per.weight)
            type(dec, per.weight)

            # Set with a str
            per.weight = '167.66'
            eq(dec('167.66'), per.weight)
            type(dec, per.weight)

            # Set with another Decimal
            per.weight = dec(168.66)
            eq(dec('168.66'), per.weight)
            type(dec, per.weight)

        with section ('`bytes` attributes'):
          print('''
            The `bytes` data type is analogous to the Python's native
            `bytes` data type. This type contains a string of binary
            values (or a sequence of integers depending on how you like
            to think about it). Thus the `bytes` data type is used when
            there is a need to store binary values.

            By default, the database type for `bytes` is
            `VARBINARY(255)', thus a maximum of 255 bytes are allowed by
            default. This can be change using the following syntax:

              class myentity(orm.entity):
                mybytes = bytes, 1, 10

            In the above code, `mybytes` will be able to contain 1 to 10
            bytes. Any more or less would make a `myentity` invalid.

            If the `bytes` attribute is declared to have a minimum and
            maximum which is equal to one another, then the `BINARY`
            database type will be used. For example, if `mybytes` were
            redeclared as:

              class myentity(orm.entity):
                mybytes = bytes, 10, 10

            The database type would be `BINARY(10)`
          ''')

          with listing('Using `bytes` attributes'):
            from uuid import uuid4, UUID
            class person(orm.entity):
              # A univeral identifier for a person (note that this would
              # be redundent with the person's `id` property)
              uuid = bytes 16, 16

            # Assign a binary representation of a UUID
            per.uuid = uuid4().bytes

            type(UUID, per.uuid)
            type(UUID, per.id)

          print('''
            In the above code, we add a `uuid` field to capture a
            UUID for the `person`. The `.bytes` property of the UUID
            object gives us a 16 byte binary value. Note that this is
            pretty much equivelent to how the `id` attributes already
            work, except for the fact that the `id` attribute is
            assigned a UUID on entity creation.
          ''')

        with section ('`date` attributes'):
          print('''
            The `date` attribute is used for date values which do not
            require a time component. `date` attributes default to
            `None`.`date` attributes are stored in MySQL as `DATE` data
            types thus a valid date can be between between '1000-01-01'
            to '9999-12-31'. This is convenient because it means that
            the ORM is free of any Y2K or Y38 problems (at least not for
            a really long time).

            A nice feature of the `date` attribute is that it can parse
            date stings (using the
            [dateutile.parser](https://dateutil.readthedocs.io/en/stable/parser.html)
            class). This means than reasonably unabigious date string
            formats, such as "2006/01/01", "Jan 2, 2001" will be parsed
            intelligently without the need for a format string.
          ''')

          with listing('Using `date` attributes'):
            import primative
            from datetime import date

            class person(orm.entity):
              dob = date

            per = person()
            
            # Assign the dob using a string
            per.dob = '2006-01-01'

            # A `primative.date` type is always returned (unless the
            # value is None)
            self.type(primative.date, per.dob)
            self.eq(primative.date(2006, 1, 1), per.dob)

            # However, the returned value will also be equivalent to a
            # regular Python `date` object with the same date
            # parameters 
            elf.eq(date(2006, 1, 1), per.dob)


            # We can also assign a `date` object or a `primative.date`
            # object.
            per.dob = primative.date(2006, 1, 2)

            # The above assertions will still work with the new value
            self.type(primative.date, per.dob)
            self.eq(primative.date(2006, 1, 2), per.dob)
            self.eq(date(2006, 1, 2), per.dob)

          print('''
            As you can see, the return type is the framework`s own date
            object `primative.date`. However, since this is just a
            subclass of Python's `date` class, either can be used to
            evaluate the return value.
          ''')

        with section ('`datetime` attributes'):
          print('''
            `datetime` attributes are used whenever you need to store a
            precices date and time together. They are based on Python's
            `datetime` class. `datetime` attributes default
            to `None` and can store up to 6 digits of microsecond
            precision. They have a range of '1000-01-01
            00:00:00' to '9999-12-31 23:59:59'. Their database data type
            is `DATETIME` which imposes this range (Python's `datetime`
            can be as low as 1 CE). This expansive range ensures that
            datetime values are not prone to the Y2038 bug (using
            MySQL's `TIMESTAMP` data type currently would make
            applications using the ORM subject to the Y2038 problem).

            An important feature of `datetime` attributes is that they
            are always UTC. If the attribute is set to a datetime object
            that has no time zone information, the UTC time zone will be
            added. If the datetime has a non-UTC time zone, the value
            will be converted to UTC and the UTC time zone will be added
            to the value. (Note that time zones aren't stored in the
            database, they are just assumed to be UTC.) Through this,
            the ORM always stores datetime values as UTC. Of course, the
            end user will usually want want to work with datetimes in
            their own time zone. It is up to the user interface's logic
            to capture the user's time zone so that time zone aware
            datetimes are given to the ORM.  Likewise, when presenting a
            datetime to the user, the user interface logic must make
            sure that the datetime is converted to the user's local time
            zone from UTC (if necessary).  
          ''')

        with section ('`timespan` attributes', id='39672a76'):
          print('''
            Oftentimes when writing entity classes, you will need to
            declare a **begin** and **end** datetimes. For example, a
            `user` class may have a `begin` and `end` field which
            indicate when the user is active.

              class user(orm.entity):
                  # The date the user became active
                  begin = datetime

                  # The date the user became inactive
                  end = datetime

            This basic need to indicate a general time range for an
            entity is so common that the framework provides a shorthand
            that can do the above with only one attribute declaration
            instead of two:
          ''')

          with listing('Using the `timespan` attribute'):
            from orm import timespan

            class user(orm.entity):
              # A timesspan to indicate when the user account was active
              active = timespan

          print('''
            The above declaration of `user` is equivalent to the
            original declaration in that we still get `begin` and `end`
            datetime attributes.
          ''')

          with listing('Demonstrating the `timespan` attribute'):
            
            usr = user()
            usr.begin = '2001-01-01 10:10 PM'
            usr.end = '2012-12-12 12:12 PM'
            type(primative.datetime, usr.begin)
            type(primative.datetime, usr.end)

          print('''
            The name `active` doesn't really matter to much at this
            point. We still get the `begin` and `end` attributes.

            `timespan` attributes can also tell us if a given date
            falls within this date range. Since we declared the name of
            the `timespan` to be `active`, we can ask whether on not a
            given datetime falls within the `span`.
          ''')

          with listing(
            'Demonstrating the `in` operator with the '
            '`timespan` attribute'
          ):
            true('2010-10-10' in usr.active)
            fals('2020-10-10' in usr.active)
            
          print('''
            Usually, an entity will need only one timespan. However, if
            you need multiple timespans, you can add a `prefix` to
            additional timespans attributes:
          ''')

          with listing('Using multiple timespans'):
            class user(orm.entity):
              # A timesspan to indicate when the user account was active
              active = timespan

              # A timespan to indicate when the user subscribed to the
              # for-pay services
              subscribed = timespan(prefix='subscribed')

            usr = user()

            # Set the datetime range for when the user was *active*
            usr.begin = '2001-01-01 10:10 PM'
            usr.end = '2012-12-12 12:12 PM'

            # Set the datetime range for when the user was *subscribe*
            usr.subscribedbegin = '2001-02-01 10:10 PM'
            usr.subscribedend = '2012-12-12 12:12 PM'

          print('''
          The above syntax works fine, but an even better way to access
          the attributes would be like the following
          ''')

          with listing('Using the timespan attribute'):
            # Set the datetime range for when the user was *active*
            usr.active.begin = '2001-01-01 10:10 PM'
            usr.active.end = '2012-12-12 12:12 PM'

            # Set the datetime range for when the user was *subscribe*
            usr.subscribed.begin = '2001-02-01 10:10 PM'
            usr.subscribed.begin = '2012-12-12 12:12 PM'

          print('''
            The above takes advantage of the fact that the timespans can
            be distinguished by the attribute names (i.e., `active` and
            `subscribed`)

            The prefix is still needed because the ORM wants to ensure
            that the less verbose notation works. Note that a `suffix`
            parameter is available which can be used to append a suffix
            to the end of the attribute name. Thus, had we used `suffix`
            instead of `prefix`, the attributes would have been
            `usr.beginsubscribed` and usr.endsubscribed'.
          ''')

        with section ('`datespan` attributes'):
          print('''
            The `datespan` attribute works just like the timespan
            attribute except that the `begin` and `end` attributes that
            are provided are of type `date` instead of `datetime`
            &mdash; thus `datespan`s don't store time information; only
            dates. See the section on [`timespan attributes`](#39672a76)
            for more.
          ''')

          with listing('Using datespan'):
            from orm import datespan

            class user(orm.entity):
              # A datespan to indicate when the user account was active
              active = datespan

              # A datespan to indicate when the user subscribed to the
              # for-pay services
              subscribed = datespan(prefix='subscribed')

            usr = user()

            # Set the date range for when the user was *active*
            usr.active.begin = '2001-01-01'
            usr.active.end = '2012-12-12'
            eq(primative.date(2001, 01, 01), usr.active.end)
            eq(primative.date(2012, 12, 12), usr.active.end)

            # Set the date range for when the user was *subscribe*
            usr.subscribed.begin = '2001-02-01'
            usr.subscribed.end = '2012-12-12'
            eq(primative.date(2001, 02, 01), usr.subscribed.end)
            eq(primative.date(2012, 12, 12), usr.subscribed.end)

    with section('Using ORM entities collections'):
        with section(
          'Collecting and saving with ORM entities collections'
        ):
          print('''
            So far we have worked with individual entity objects. As you may
            remember from the [Class complement](#547592d9) section, each
            entity class requires a corresponding entities collection class.
            Earlier, we had created a `dogs` collection class to serve as
            the complement to the `dog` entity class. We can use that class
            to collect `dog` entity objects and use the collection's
            `save()` method to save all the collected objects.
          ''')

            with listing():
              # Create a dogs collection
              ds = dogs()

              # Create and collect three dog entity objects
              ds += dog()
              ds.last.name = 'Rex'

              ds += dog()
              ds.last.name = 'Bandit'

              ds += dog()
              ds.last.name = 'Benji'

              # Save the dogs
              ds.save()

              # Assert that the dogs made it to the database
              for d in ds:
                expect(None, d.orm.reloaded)

          print('''
            This listing is similar to the one before except this time,
            instead of using variables to store the `dog` instances, we
            append them to a collection. We access the last appended `dog`
            via the `last` attribute of the collection to set its `name`
            attribute. Instead of saving each dog one-by-one, we can
            simply call the `save()` method on the `dogs` entities
            collection. 

            Like the previous listing, this `save()` operation will be
            performed in an atomic transaction so that, if there is an
            exception at any point in the saving process, the entire
            transaction will rollback, and the code that calls `save()`
            will have the opportunity to `except` the `Exception`, e.g.,:
              
              try:
                  ds.save()
              except Exception as ex:
                  # Find out what went wrong
                  ...

            In the listing, each `dog` was *new*, and therefore a `save()`
            would have resulted in three `INSERT`s to the database.  However,
            it is important to remember that, calling the `save()` on the
            collection calls the `save()` method on each of the entity objects
            in the collection. Thus, calling `save()` on a collection could
            end up being a mixture of `INSERT`s, `UPDATE`s and `DELETE`s being
            sent to the database depending on the persistence state of the
            given entity object.  Also, calling `save()` on an entity
            collection could result in no database interaction if the entity's
            persistence state indicates that nothing should be done.

            The `dogs` class is an entities collection class which means
            it inherits from `orm.entities` which  inherits from
            `entities.entities` which we discussed at length in the [Using
            entities classses](#eca3195f) section of the [Entity and
            entities objects](#64baaf7a) chapter. Thus, `orm.entities`
            classes inherits the rich feature-set of `entities.entities`
            with some of those features being overridden to suit the
            needs of ORM collection classes. In this section, we will
            discuss these features in detail.

          ''')

        with section('Querying with collection entities'):
          print('''
            One of the most powerful feature of ORM entities is that they can
            query the database through their constructor. As we've seen: 
            passing no arguments to the entities constructor does nothing
            more than provide us with an empty collection object. However,
            through the constructor we are able to specify arguments that
            are used to generate a `SELECT` statement which will be sent to
            the database. The results from the `SELECT` will be used to
            populate the collection.

            Though we will see that we can give full Boolean expressions
            (similar to `WHERE` clauses) to the constructor, let's start
            with what is perhaps the simplest type of query: a simple
            equality test:
          ''')

          with listing('Performing a simple equality query'):
            # Query the database for all dogs that have the name "Rex"
            dgs = dogs('name', 'Rex')

            # Assert that only one was found
            one(dgs)

            # Assert that its name is indeed Rex
            eq('Rex', dgs.only.name)

        print('''
          From a previous listing, we had saved a `dog` to the database
          that we named "Rex". The above construction of the `dogs`
          collection searches for any `dog` in the `dogs` table with the
          name of "Rex". The SQL it generates is similar to:

            SELECT *
            FROM dogs
            WHERE name = 'Rex';

          Since there is only one `dog` with that name, the collection
          ends up containing only one dog object which we access through
          the `only` attribute. Had there been more `dogs` named "Rex",
          we would have ended up with more `dog` objects in the
          collection.

          Of coures, the filter criteria of queries need to be much more
          expressive than the above two-argument form would allow.
          However, since simple equality tests like this are pretty
          common, the two-argument form is provided by the ORM as a
          convenience. Below we will cover more expressive ways to query
          entities.  These forms are more verbose but also more powerful.

          Note that interaction with the database to load entities does
          not occure during instantiation but rather when an attribute
          is called on the the entities collection. So, in the above
          listing, the line:

            dgs = dogs('name', 'Rex')

          doesn't actually cause a `SELECT` to be sent to the database.
          It mearly constructs the collection with the parameters that
          will be used in the `WHERE` clause.  It's the following line,
          in the above example, that actually causes the `SELECT`
          statement to be sent to the database:

            one(dgs)

          This is because `one()` will call an attribute of the
          collection (i.e., `dgs.count`). This is refered to as
          **defered execution**. The ORM uses defered execution 
          to support sorting which will be cover later in the
          [Sorting](#9141f618) section &mdash; although you may find
          it useful for certain performance optimization strategies
          &mdash; such as contructing multiple collections then later
          loading only a subset of them based some condition.

          You can explicitly load an entities collection by calling
          `orm.collect()` on it: 

            dgs = dogs('name', 'Rex')
            dgs.orm.collect()

          However, this is rarely necessary and would be functionally
          equivalent to calling any other attribute on it.

          Lets rewrite the above listing to use the more the Boolean
          expression query form:
        ''')

        with listing(
          'Using a Boolean expression for a simple equality query'
        ):
          # Query the database for all dogs that have the name "Rex"
          dgs = dogs("name = %s", 'Rex')

          # Assert that only one was found
          one(dgs)

          # Assert that its name is indeed Rex
          eq('Rex', dgs.only.name)

      print('''
        This listing does the same thing as the prior listing, however
        here we are using a Boolean expression (the kind of thing you
        would use in a `WHERE` clause). 

        In this query, a placeholder (%s) is used to seperate the value
        "Rex" from the query string.  This is an important feature to
        prevent against SQL injection attacts, particularly when the
        data being replaced is a variable which contains user input.

        We can use as many placeholders and their corresponding values
        as wee need. For example, we could change the query to search
        for any dog whose name is "Rex" or "Bandit" like this:
      ''')

        with listing(
          'Using a Boolean expression for multiple equality tests'
        ):
          # Query the database for all dogs that have the name "Rex"
          dgs = dogs("name = %s or name = %s", 'Rex', 'Bandit')

          # Assert that only one was found
          two(dgs)

          # Sort the dogs based on name
          dgs.sort('name')

          # Assert that its name is indeed Rex
          eq('Bandit', dgs.first.name)
          eq('Rex'   , dgs.Second.name)

        print('''
          The above construction produces a query similar to this SQL:

            SELECT *
            FROM dogs
            WHERE name = 'Rex' or name = 'Bandit';

          In this construction, we have two placeholders (%s)
          which will be substituted for the two values: 'Rex' and
          'Bandit'. We can add as many placeholders and corresponding
          substitution values as we like.

          Note that we are able to use the in-memory `sort()` derived
          from the `entities.entities` base class to sort the `dog`
          elements by name. This allows us to make assertions about
          which element is which. Without the call to `sort()`, the
          order of the elements would be indeterminate.

          The Boolean expressions we are able to use for construction
          are similar to the the `WHERE` clauses used in SQL, however
          they are not identical. The framework parses the queries
          (which it calls "predicates") and stores them in internal data
          structures which are later used to generate actual 'WHERE'
          clause arguments. 

          That being said, the syntax is nearly identical to the type of
          expressions you would give to a `WHERE` clause. All the
          standard comparative operator are supported. Also, using
          paranthesis to nest expressions works. However, you shouldn't
          expect MySQL function such as `TRIM()` or `LENGTH()` to work
          nor should you expect non-comparative operators, such as
          those used in arthmatic expessions, to work.

          If you want to see the SQL that the entities collection will
          produce, you can `print` out the collection's `where` object.

            dgs = dogs('name IN (%s, %s)', ('Rex', 'Bandit'))

          In this example, we used the IN operator which you will be
          familiar with from SQL. Let's see what SQL the ORM will
          issue to the database for this query. If we print the `where`
          object:

            print(dgs.orm.where)

          we will receive the following output.

            name IN (%s, %s)
            ['Rex', 'Bandit']

          The first line contains the SQL. As you can see, the SQL
          matches our query expression exactly. The second line contains
          our arguments. for the parameterized SQL of the first line.
          To see the entire SQL statement, you can use:

            print(*dgs.orm.select)

          This will give us the entire select statement:

						SELECT
								`t_d`.id AS `t_d.id`,
								`t_d`.proprietor__partyid AS `t_d.proprietor__partyid`,
								`t_d`.owner__userid AS `t_d.owner__userid`,
								`t_d`.createdat AS `t_d.createdat`,
								`t_d`.updatedat AS `t_d.updatedat`,
								`t_d`.name AS `t_d.name`,
								`t_d`.dob AS `t_d.dob`
						FROM main_dogs AS `t_d`
						WHERE (`t_d`.name IN (%s, %s)) ['Rex', 'Bandit']

          Here we can see the `WHERE` clause in the context of the full
          `SELECT` statement.
        ''')

        with section('Using the conjunctive-kwargs form'):
          print('''
            We can also use the conjunctive-kwargs form. This is where we
            pass in one or more keyword arguments to form a chain of
            conjunctive (AND) tests. For example, we can use this form to
            search for dogs named "Rex":
          ''')

          with listing(
            'Using the conjunctive-kwargs form'
          ):
            # Query the database for all dogs that have the name "Rex"
            dgs = dogs(name = 'Rex')

            # Assert that only one was found
            one(dgs)

            # Assert that its name is indeed Rex
            eq('Rex', dgs.only.name)

          print('''
            As you can see, we are using Python's kwargs notation to
            express a query for `dogs` named "Rex". In this example, we
            are denote only one equality test, so there isn't any
            conjoining going on. Let's look for `dogs` named "Rex" and who
            have a `dob` of None.
          ''')

          with listing(
            'Using the conjunctive-kwargs form with multiple kwargs'
          ):
            # Query the database for all dogs that have the name "Rex"
            dgs = dogs(name = 'Rex', dob = None)

            # Assert that only one was found
            one(dgs)

            # Assert that its name is indeed Rex
            eq('Rex', dgs.only.name)

          print('''
            Above we get search for all the `dogs` with a name of "Rex"
            and a `dob` of None. Since we didn't specify a date when we
            created "Rex", it will default to None (or `null` in the
            database). Thus, we will receive the same "Rex" `dog` as
            before from the `only` property. 

            The SQL generated by this construction looks like this:

              SELECT *
              FROM dogs
              WHERE name = 'Rex' AND dob is null;

            The conjuntive-kwargs form is nice because it requires fewer
            characters ("name" and "dob" don't need to be in quotes).
            However, it's a bit of a hack because we are using Python's
            kwargs in a tricky way. Thus, the only comparative operator we
            can use is Python's assignment (=) operator. Don't expect
            other comparative operators to work. For example, the
            following won't work:

              dgs = dogs(name != 'Rex')

              dgs = dogs(name < 'Rex')

              dgs = dogs(dob is None)
          ''')

      with section('Sorting', id='9141f618'):
        ...

    with section('Debugging ORM entities'):
      print('''
        When it isn't clear why the ORM is behaving in a certain way, it
        is often useful to look under the hood and see what SQL is being
        sent to the database. You have already seen the methods that get
        the `INSERT`, `SELECT`, `UPDATE` and `DELETE` statement:

            sql, args = d.orm.getinsert()
            sql, args = d.orm.select
            sql, args = d.orm.mappings.getupdate()
            sql, args = d.orm.mappings.getdelete()

        Each of the above returns a tuple where the first element is a
        parameterized SQL statement and the second element is a list of
        arguments used to replace the placeholders (`%s`) in the
        parameterized SQL.

        These can be useful, but they don't tell you the actual SQL that
        is being sent the database when a given ORM operation is
        invoked. Whenever the ORM interacts with the database, it
        chronicles the SQL to the `db.chronicles` singleton. This
        object keeps track of the last 20 SQL statements that were sent
        to the database (or whatever `db.chronicler.getinstance().max`
        equals). You can view these statements with a line like the
        following:

          import db
          print(db.chronicler.getinstance().chronicles)

        However, this technique is a little imprecise since it doesn't
        tell us exactly which chronicled SQL statements correspond to
        which lines were executed. A better way is to use the
        `snapshot()` context manager to see what SQL a particular line
        of Python is causing to be sent to the database:

          d = dog()
          d.name = 'Rex'
          d.dob = 'Jun 10, 1998'

          with db.chronicler.snapshot():
            d.save()

        In the above example, the `INSERT` statement resulting from the
        `save()` method will be printed to `stdout`. Obviously, the
        snapshot() should only be used when debugging and the line
        should be remove altogether before merging a feature branch
        into 'main'. If for some reason you don't want the SQL to be
        printed to stdout, you can suppress this behaviour and still
        capture the SQL being sent to the database by passing `False` to
        the `snapshot` method:

          with db.chronicler.snapshot(False) as chrs:
            d.save()

            # chrs is a chronicler object
            type(db.chronicler, chrs)

            # We can stringify a chronicler object to get the SQL
            # statements as a string.
            sql_statements = str(chrs)
      ''')

    with section('Relationships'):

      with section('One-to-many relationships'):
        print('''
          Defining a one-to-many relationship between to classes is
          pretty straightforward. Let's say that we are building an
          order entry system. In the system, we want to model customers
          and sales orders. Each customer can have zero or more sales
          orders. Lets define those class and the one-to-many
          relationship between them:
        ''')

        with listing('Defining a one-to-many relationship'):
          ''' Define the collection classes first. '''
          class customers(orm.entities):
            """ Represents a collection of customers.
            """

          class orders(orm.entities):
            """ Represents a collection of orders.
            """

          ''' Define the entity classes '''
          class customer(orm.entity):
            """ Represents person who can place orders.
            """
            # The customer's names
            firstname = str
            lastname = str

            # This line establishes the relationship.
            orders = orders

          class order(orm.entity):
            """ Represents a sales order
            """
            # The date and time the order was placed
            placed = datetime

            # Will be True if order is canceled
            canceled = bool

        print('''
          Above we have created a `customer` and `order` entity along
          with their collection complements. Importantly, we defined the
          collections first. This allows us to reference the `orders`
          collection class from the `customer` class definition:

            class customer(orm.entity):
              ...
              orders = orders

          With this line, the ORM can see that we want the `customer`
          entity to have an attribute called `orders` which contains a
          collection of `order` objects thus establishing the
          one-to-many relationship between the two objects.

          Note that this object model will need a `lineitem` entity as
          well as a `product` entity in order for us to represent a real
          order. We will create those entity classes later. For now, we
          will just focus on the one-to-many relatioship between
          `customers` and `orders`.

          Now that we have our classes defined, lets write some code
          that creates a `customer` with some orders associated with it.
        ''')

        with listing('Using a one-to-many relationship'):
          # Ensure that the tables are created in the database
          customer.orm.recreate()
          orders.orm.recreate()

          # Override the security context
          with orm.override(), orm.sudo()

            # Create the customer
            cust = customer()
            cust.firstname = 'Johnny'
            cust.lastname = 'Rotten'

            # Create two order objects
            ord = order()
            ord1 = order()

            # Assert that the order objects have no customer associated
            # with them
            none(ord.customer)
            none(ord1.customer)

            # Append each order to the customers collection of orders.
            cust.orders += ord
            cust.orders += ord1

            # By appending the orders to the customer's order
            # collection, each order knows its customer via the
            # `customer` property.
            is_(cust, ord.customer)
            is_(cust, ord1.customer)

        print('''
          First we run the `orm.recreate()` method to issue the `CREATE
          TABLE` commands to the database so there will be database
          tables to save the entity objects to. The `with` statement
          sets up the security context &mdash; however, you can ignore
          this for now.

          Next we create a `customer` object and assign some values to
          its attributes. Then we create two `orders` objects. Because
          of the one-to-many relationship we defined in the class
          definitions, `customer` objects will expose an `orders`
          attributes which returns the `customer`'s own collection of
          `orders`. We used this collection to append our two `order`
          objects to it using the `+=` operator thus associating the
          `orders` with the `customer`. 

          The collection objects on the *many* side of a one-to-many
          relationship are called **constituent**. The object on the
          *one* side is called the **composite**. So in this example,
          the ``orders`` are *constiuents* of the `customer`, while the
          `customer` is a *composite* of each of the `order` objects.

          Now that the `orders` have been appended, the `customer`
          object has access to them through its `orders` collection.
          Also, as we assert above, the `order` object have access to
          the `customer` object they have been assigned to through their
          `customer` property. The ORM is able to infer the need for a
          `customer` property here because it knows that `order` is on
          the *many* of a one-to-many relationship.

          At this point, we have 3 new objects: the `customer` and its
          two `orders`. However, they are not in the database yet. Let's
          save them now.
        ''')

        with listing('Saving an object and its constiuents'):

          # Override the security context
          with orm.override(), orm.sudo()
            
            # Save the customer object along with its constituents,
            # i.e., the two order objects.
            cust.save()

            # Reload the customer from the database
            cust1 = cust.orm.reloaded()

          # Sort the orders of the original customer by id
          cust.orders.sort('id')

          # Sort the orders of the reloaded customer by id
          cust1.orders.sort('id')


          # Assert the reloaded customer, and its orders, match the
          # original 
          eq(cust.id, cust1)
          eq(cust.orders.first.id, cust1.orders.first.id)
          eq(cust.orders.second.id, cust1.orders.second.id)
          two(cust.orders)

        print('''
          Conveniently, all we needed to do to save the customer and its
          constituents (i.e., its `order` objects), was to call `save()` on
          the `cust` object. This results in `INSERT` statements being
          sent to the database to persist all three objects. 

          The `INSERT`s are performed in an atomic transaction so if any
          of them fail, the entire transaction will be rolled back and
          the exception that caused the problem will be raised.

          Later in the listing, we reload the `customer` entity from the
          database. As we've seen in prior example, we can use this
          technique to prove that the `customer` object made it to the
          database. However, what's novel above this example is that the
          reloaded `cust1` object contains reloaded `orders`.  (as we
          assert in the final lines of the listing). 

          Importantly, the `customer`'s `orders` collection is
          lazy-loaded. That is to say, when we reloaded the `customer`
          object, the `orders` objecs were not loaded (they may have not
          been needed). It's only when `cust1.orders` is called that the
          `order` entities are actually loaded from the database. When
          they are loaded, they are memoized meaning additional calls to
          `cust1.orders` will not result in database activity because
          the `orders` have been cached in memory.

          In the above example, all the mutations were `INSERT`s.
          However, they could have been any mixture of the other
          mutations, viz. `UPDATE` and `DELETE`. To demonstrate, the
          following listing will `UPDATE` the `customer` object,
          `INSERT` a new order, and `DELETE` an existing `order`.
        ''')

        with listing('Update an object and its constiuents'):
          # Change the attributes of the customer (i.e., `UPDATE`)
          cust.firstname = 'John'
          cust.lastname = 'Lydon'

          # Get a reference to the customer's orders collection
          ords = cust.orders

          # Remove the first order from the colection causing it to be
          # marked for deletion (i.e., DELETE). Assign the removed order
          # to `rmord`.
          rmord = ords.pop()

          # Assert that rmord is marked for deletion as a consequence of
          # the pop()
          true(rmord.orm.ismarkedfordeletion)

          # Instantiate a new order object and append it to the
          # customer's collection of orders (i.e., INSERT)
          ords += order()

          # Override the security context
          with orm.override(), orm.sudo()
            # Save the customer object. This will UPDATE the customer,
            # DELETE its first order, and INSERT a new order for the
            # customer.
            cust.save()

            # Reload the customer from the database
            cust1 = cust.orm.reloaded()

          # Sort the orders of the original customer by id
          cust.orders.sort('id')

          # Sort the orders of the reloaded customer by id
          cust1.orders.sort('id')

          # Assert the reloaded customer, and its orders, match the
          # original 
          eq('John', cust1.firstname)
          eq('Lydon', cust1.lastname)

          # Assign the reloaded customer orders to `ords1' to make the
          # forthcoming lines shorter
          ords1 = cust1.orders

          # Assert the removed order was not reloaded since it was
          # deleted.
          false(rmord.id in ords1.pluck('id'))

          # Assert that the reloaded orders match the non-deleted orders
          # from the original collection
          eq(ords.first.id, ords1.first.id)
          eq(ords.second.id, ords1.second.id)

          # Assert there isn't a third order lingering around
          two(ords)

        print('''
          In the above listing, we take the original `customer` object
          and change its attributes. Then we remove (`.pop()`)  the
          last `order` off the 'customer`'s collection of `orders`. Not
          only does this have the effect of removing the order from the
          collection, but it also marks the order for deletion. Next we
          append an `order` to the `customer`'s `orders` collection.

          However, no database interaction happens until we call the
          `save()` method on `cust`. At that point, the `customer` is
          `UPDATE`ed, the removed order is `DELETE`ed, and the newly
          appenderd `order` is `INSERT`ed all in an atomic transaction.

          Later, we reload the `customer` and assert that the reloaded
          version contains the updates as well as the new `order`. We
          also assert that the removed order is not in the reloaded
          `orders` collection.

          Note that any operation that removes an object from a an ORM
          collection (e.g., `.remove()`, `shift()`, `del`, `-=`) marks
          it for deletion. Likewise, any append apperation (e.g.,
          `.append()`, `unshift()`, `<<`, `+=`, `|=`) would have
          resulted in the object being `INSERT`ed into the database
          (assuming it was a new object, i.e., `orm.isnew is True`).
          Regardless, its `save()` method will be called to ensure it is
          persisted.

          We can see that the ORM provides us a convenient way to modify
          and persist all objects involed in a one-to-many relationship.
          So far we've only dealt with a one-to-many relatioship of a
          single depth. However, relationships can be set up with an
          n-level of depth and an invocation of the `save()` method will
          ensure that all objects in the hierarchy are persisted.

          Let's create a line item collection so we can add
          products to our orders. We will recreate the `order` entity so
          we can establish a one-to-many relationship between it and the
          line items collection:
        ''')

        from decimal import Decimal as dec
        with listing('Add a lineitem entity'):
          class lineitems(orm.entities):
            """ A collection of line items of an order.
            """

          class lineitem(orm.entity):
            """ A line item in an `order`.
            """
            product   =  str
            price     =  dec
            quantity  =  int

          # Recreate the order class
          class order(orm.entity):
            """ Represents a sales order
            """
            # The date and time the order was placed
            placed = datetime

            # Will be True if order is canceled
            canceled = bool

            # Establish the one-to-many relationship between orders and
            # line items.
            lineitems = lineitems

        print('''
          Above we have create a `lineitem` entity which will store the
          product's that a user has ordered. 

          (Normally, a product would be its own entity, but since we
          haven't discussed many-to-many relationships yet, we will just
          be satisfied with a simple `str` to represent which product is
          ordered.)

          In the final line of the listing, we inform the ORM that
          `order` and `lineitems` have one-to-many relationship with
          each other.

          Let's create a new `customer`, add an `order` to it, and this time
          we will include `lineitems`
        ''')

        with listing('Persisting n-levels deap'):
          # Create the lineitem table
          lineitem.orm.recreate()

          # Override the security context
          with orm.override(), orm.sudo()

            # Create the customer
            cust = customer()
            cust.firstname = 'Jay'
            cust.lastname = 'Leno'

            # Create the order
            ord = order()

            # Create the line items
            ord.lineitems += lineitem(
              quantity  =  1,
              price     =  3_957_348.92
              product   = '1928 Bentley Speed 6'
            )

            ord.lineitems += lineitem(
              quantity  =  1,
              price     =  12_154_788.79
              product   = 'McLaren F1'
            )

            # Make the orders collection the customer's orders
            # collection
            cust.orders = ords

            # Save the customer, the order and the order's lineitems
            cust.save()

            # Reload the customer from the database
            cust1 = cust.orm.reloaded()

            # The final lines assert that the reloaded customer matches
            # the original.
            eq(cust.id, cust1.id)

            eq(cust.orders.first.id, cust1.orders.first.id)

            # Get the lineitems for the original customer and the
            # reloaded customer.
            lis = cust.orders.first.lineitems
            lis1 = cust1.orders.first.lineitems

            # Assert that each line item matechs
            for li, li1 in zip(lis.sorted('id'), lis1.sorted('id')):
              eq(li.id,        li1.id)
              eq(li.price,     li1.price)
              eq(li.quantity,  li1.quantity)
              eq(li.product,   li1.product)

        print('''
          In the above listing, Jay Leno is ording a couple of extra
          cars for his collection. The important thing to note is that
          the line, `cust.save()`, `INSERT`'s the customer, its
          order and the order's two `lineitems`. This gives us a
          demonstration of a 3-level deep persistence operation &mdash;
          though, no matter how deep the hierarchy of entity objects
          get, atomic persistence operations will continue to work.

          In the remaining lines, we assert that all four reconds made
          it to the database and that we were able to retrieve them.
        ''')

        with section('Saving constituents'):
          print('''
            In the above example, we have been saving the composite
            (i.e., the `cust` object`) and allowing the persistence to
            propagate down to its constituents. However, if we call
            `save()` on a constituent, an attempt will be made to
            persist its composite as well. Take the following code for
            example:
          ''')

          with listing('Saving composites by saving constituent'):
            # Override the security context
            with orm.override(), orm.sudo()

              # Create the customer
              cust = customer()
              cust.firstname = 'Stewie'
              cust.lastname = 'Griffin'

              # Create two order objects
              ord = order()
              ord1 = order()

              # Append each order to the customers collection of orders
              cust.orders += ord
              cust.orders += ord1

              # Save ord1. This will result in `cust` being saved, as
              # well as `ord`.
              ord1.save()

              # Reload ord1 and assign to ord1_0
              ord1_0 = ord1.orm.reloaded()

              # Get the reloaded order's customer composite and assign
              # to cust1. Note that this customer object is a reloaded
              # verision of `cust` because it comes from the reloaded
              # ord1_0.
              cust1 = ord1_0.customer

              # Assert that the reloaded customer matches the original
              # customer.
              eq(cust.id, cust1.id)
              eq(cust.firstname, cust1.firstname)
              eq(cust.lastname, cust1.lastname)

              # Assert that the reloaded ord1 matches the original ord1
              eq(ord1.id, ord1_0.id)

              # Assert that the reloaded customer's orders collection
              # containes the original `ord` object.
              true(cust.orders.first.id in cust1.orders.pluck('id'))

          print('''
            The above listing is similar to the other example we have
            seen so far. However, instead of calling `save()` on the
            `cust` object, i.e., the *composite*, we are call `save()`
            on one of the `order` objects (`ord1`). Since the ORM knows
            that the `cust` is the composite of `ord1`, an attempt
            is made to persist (i.e., call its `save()` method) `cust`
            as well.  This, in turn has the effect of persisting the
            other `order` (`ord`) since it is a constituent of `cust`

            Note also that when we reload `ord1`, we are able to access
            its composite `.customer`. Retrieving a composite from a
            newly loaded entity is a feature we haven't seen yet. For
            the sake of clarity, this composite is a freshly loaded
            `customer` since `ord1_0` is freshly loaded (i.e., it's not
              derived from an in-memory cache somewhere). Also, it is
            lazy-loaded: the database interaction to retrieve the data
            for the composite is performed only when `.customer` is
            called. That being said, it is a composite and you should
            expect it to behave like any other composite in terms of
            attribute access, persistence state management, and any
            future persistence operations.

            Once `ord1` has been reloaded, the final part of the listing
            demonstrates, through assertion, that the `customer` and its
            two `orders` were successfully saved to the database and
            subsequently reloaded back into new entity objects.

            Normally, you will call `save()` on the highest level
            composite and allow the persistence to propagated down to
            the constituents since this is a more intuitive approach to
            writing persistence logic. However, it's important to know
            that the ORM is keeping track of these hierarchies and will
            try to persist upwards as well as downwards.
          ''')

      with section('Recursive relationships'):
        ...
        
      with section('Many-to-many relationships (or associations)'):
        print('''
          Many-to-many relationships between entities are established
          and supported by **associations**. `association` objects are a
          special type of `orm.entity'. They act as a bridge between two
          other entity objects. Like regular entity classes, association
          classes map to an associative table in the database. Like
          association entities, this table links the tables of the two
          entity classes.

          Let's see an example of how we can use an association class to
          model movies and the many-to-many relatioship they have with
          people.
        ''')

        with listing('An simple object model that uses association'):
          ''' Create the person entity '''
          class persons(orm.entities):
            pass

          class person(orm.entity):
            # The name of the person
            name = str

          ''' Create the movie entity '''
          class movies(orm.entities):
            pass

          class movie(orm.entity):
            # The name of the movie
            name = str

          ''' Create the movie_person association entity '''
          class movie_persons(orm.associations):
            pass

          class movie_person(orm.association):
            # The `person` side of the relatioship
            persons = persons

            # The `movies` side of the relatioship
            movies = movies

            # The role a person plays in the creation of the movie
            role = str

        print('''
          In the above listing, we've established two simple entity
          classes: `person` and `movie`. Note that within their
          declaration there is nothing to suggest that they have a
          many-to-many relatioship with one another.

          The listing ends with the declaration of the `movie_person`
          association. Notice that it shares a lot in common with
          regulare `entity` classes. First, it needs a pluralized form
          (`movie_persons`) which inherits from the `orm.associations`,
          while the singular form (`movie_person`) inherits from
          `orm.association`. It also contains within it a declaration of
          a primative attribute (`role`) as well as the two collection
          classes `persons` and `movies`. These last two  declaration
          establish the many-to-many relatioship between `movies` and
          `person`. 

          Let's use these classe to record the relationships people had
          with *Monty Python and the Holy Grail*.
        ''')

        with listing(
          'Using an object model that contains an association'
        ):
          # Ensure the tables exists and are empty
          person.orm.recreate()
          movie.orm.recreate()
          movie_person.orm.recreate()

          # Create the movie object
          mov = movie(name="Monty Python and the Holy Grail")

          # Create two person objects
          chapman = person(name='Graham Chapman')
          cleese  = person(name='John Cleese')

          # `mov.movie_persons` returns a `movie_persons` association
          # collection
          type(movie_persons, mov.movie_persons)

          # Create an association (movie_person) where chapman is the
          # person and his role is 'actor'. Append it to the movie's
          # `movie_persons` collection of associations.
          mov.movie_persons += movie_person(
            person = chapman, role='actor'
          )

          # Assert that the new association's `person` attribute is
          # indeed chapman. Also note that its `movie` attribute is
          # `mov` even though we did not explicitly make the assignment.
          # The append operation was smart enough to do that for us.
          is_(chapman, mov.movie_persons.last.person)
          is_(mov, mov.movie_persons.last.movie)

          # Add another association stating that cleese was an "actor"
          # in `mov` as wel.
          mov.movie_persons += movie_person(
            person = cleese, role='actor'
          )

          # Save `mov`. Persistent operations propogate so this will
          # have effect of saving `mov` and its two constinuents
          # association (movie_persons) as well as the associated
          # `person` entity objects `chapman` and `clees`.
          mov.save()

          # Reload the movie. This should give us a movie object that
          # will have its own associations loaded from the database.
          mov1 = mov.orm.reloaded()

          # Assert the movie was correctly reloaded
          eq(mov.id, mov1.id)
          eq(mov.name, mov1.name)

          # Assert the two associations were loaded
          two(mov.movie_persons)

          # Sort the association collection by its persons' names in
          # situ
          mov.movie_persons.sort('person.name')

          # Assert that the association objects contain the correct
          # person objects.
          eq(chapman.id, mov1.movie_persons.first.person.id)
          eq(cleese.id, mov1.movie_persons.second.person.id)

        print('''
          Above we have created a `movie` object, `mov`, to represent
          *Monty Python and the Holy Grail*. The first think to note is
          that it provides us with a `movie_persons` attribute. This
          attribute, unsurprisingly, returns an association of type
          `movie_persons`. It is this collection where we append
          `association` objects. 

          The `association` objects we append are assigned a reference
          to the `person` entity of the association as well as a value
          for the `role`. We don't need to specify the `movie` entity in
          the association's construction.  It will be added for us when
          the association is appended to `mov.movie_person`.
          
          Later in the listing, we call the `save()` method on the `mov`
          object. In addition to saving the `movie`, the association
          objects are saved as well as well as the `person` objects they
          reference. As always, these mutations are done in an atomic
          transaction.

          The listing ends with the movie object being reloaded. We are
          able to compare it to the original movie object that was
          saved thus proving that the movie made it to the database. We
          are also able to reload the movie's associations and the
          entity objects (person and movie) that they reference.
          Assertions are made to prove this happened successfully.
        ''')

        with section('Reflexive associations'):
          ...

      with section('Many-to-one relationships'):


    with section('Custom properties'):
      ...

    with section('Indexes'):
        with section('Full text indexes'):
            ...

    with section('Imperitive attributes'):
      ...


    with section('Testing ORM entities'):
      ...

    with section('ORM events'):
      ...

    with section('Inheritance'):
      ...

    with section('Retrieving data'):

      with section('Joins')
        ...

      with section('Eager loading')
        ...

    with section('Streaming'):
      ...

    with section('Security', id='ea38ee04'):

      with section('Authorization', id='54014644'):
        ...

      with section('Authentication'):
        ...

    with section('Validation', id='012b0632'):
      ...

  with chapter('The General Entity Model') as sec:
    ...

  with chapter("Authoring DOM objects", id='22ee9373') as sec:
    ...

  with chapter("Robotic process automation") as sec:
    ...

  with chapter("Crust", id='0227a7b7'):
    with section('Running migrations', id='8c9baa57'):
      ...

  with chapter("Logging") as sec:
    ..

  with chapter("Third-party integration") as sec:
    ..

  with chapter("File system") as sec:
    ..

    
    
