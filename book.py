# vim: set et ts=2 sw=2 fdm=marker

# Copyright (C) Jesse Hogan - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly
# prohibited
# Proprietary and confidential
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022

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
                If the first argument to `B` is falsy, Python won't
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
    print('''
      Almost all classes in the framework inherit directly or indirectly
      from the `entity` class or the `entities` classes located in the 
      <a href="entities.py">entities.py</a> module.

      The `entities` class (or subclasses thereof) acts as a container
      for objects - usually objects that inherit from the `entity`
      class. The `entities` class is similar to a Python `list` in that
      it can collect an arbitrary number of objects. In fact, `entities`
      offers most the methods that that `list`s do including the ability
      to iterate over them. 
    ''')

    with section('Using entities classes'):
      print('''
        Normally you don't use these classes directly. Instead, you
        create classes that inherit from them. Consider that we are
        writting software for a dog sitting company and we need to track
        the dogs that they take care of:
     ''')


      import entities

      class dogs(entities.entities):
        pass

      class dog(entities.entity):
        def __init__(name, dob):
          self.name = name
          self.dob  = dob

      print('''
        Above, we have created the classe that can track individual dogs
        as well track dogs as collection (at least in memory). Let's now
        use those classes to track the dogs that the dog sitting company
        cares for:
      ''')

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
        Now three dogs, Rover and Spot, are in the `dgs` collection. We
        can use the `dgs` in a similar way to using a list to make a
        number of assertions about the collection
      ''')
      
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
        the capabilities of entity and entities objects. Virtually all
        classes in the framework derive from these two classes so it
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

          with listing('Push item onto the begining of a collection'):
            fluffy = dog(name='Fluffy', date='2016-03-02')
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
          `dogs` collection. We sort one the key `name` which is an
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

      with section('Ordinal properties'):
        print('''
          Before we go any further, let's discuss the ordinal properties
          that we have been using. Ordinal properties are those with
          names like `first`, `second`, `third`, etc. These properties
          allow you to access the items it the collection by their
          position within the collection. 
        ''')

        with listing('Retrieving elements using ordinal properties'):
          # Get the first element from the collection
          dg = dgs.first
          is_(dg, spot)

        print('''
          `spot` is the first dog in the collection so we can use
          `first` to retrieve it.

          The properties available are `first` through `seventh`. So far
          we've never needed a property greater than `seventh` though it
          would be easy to add.
        ''')

        with section('Comparison to index notation'):
          print('''
            In Python lists, this is done
            by passing an index number via square brackets.

              ls = [1, 2, 3]
              one = ls[0]

            Actually, collections support the bracket syntax as well.
            However, it is felt that by using property names instead of
            special characters, the framework's source code is more
            readable, so we use the ordinal properties. Eitherway, we
            can use the index notation to demonstrate the way the
            properties work:
          ''')


      with section('Removing items'):
        # __delitem__
        ...

      with section('Moving items'):
        ...

      with section('Querying collections'):
        # .where(), __contains__, .getcount()
        ...

      with section('Testing count'):
        # .count, .isempty. issingular, isplurality, ispopulated
        ...

      with section('Iteration'):
        ...

      with section('Indexing with Integers and Slices'):
        # __setitem__, __getitem__, __call__
        ...

      with section('Miscellaneous'):
        # getindex, getprevious, only, pluck
        ...

      with section("When entities collections aren't Quite like list")
        ...

        with section("When entities Classes are Truthy")
          ...

    with section('Persistence'):
      ...

    with section('Events'):
      ...

    with section('Validation'):
      ...

    with section('Indexes'):
      ...

    with section('Distinctions with the list interface', id='042d62d4'):
      # count/len(), es[0]/es.first, sort, sorted, enumerate

    with section('Entity classse'):
      # Go over the small amount of functionality in entities.entity
      ...


  with chapter("Configuration") as sec:
    ...

  with chapter("Using the Object-relational Mapper") as sec:

    with section('Security'):

      with section('Authorization'):
        ...

      with section('Authentication'):
        ...

    with section('Validation'):
      ...

    with section('Security'):
      ...

  with chapter('The General Entity Model') as sec:
    ...

  with chapter("Authoring DOM objects") as sec:
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

    
    
