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

        * **Feature enhancements** Any feature added to carapacian
          core should have exhaustive tests written for it.

        * **Bugs** When a bug is discovered and fixed, a test should
          be written to ensure that the same bug doesn't reoccure.

        * **Third-party integration** When writing code that interfaces
          with a third party system, test code should be written against
          a test version of that system. If a test version of the system
          doesn't exist, it should be created. This approach is favored
          over the more conventional technique of mocking because test
          systems more accurately represent the real thing. See the
          section, 'Test systems vs mocking' for more.
        
        * **DOM testing** Test should be written to ensure the validity
          of HTML pages as well as their AJAX interactions to ensure the
          user interface behaves as expected. See the section DOM
          Testing for more.

        Whether you're adding a feature to the ORM, creating a nwe web
        page, or writing backend code to interact with a third-party
        service, everything in the framework begins and ends with a
        battery of automated tests.
      ''')

    with section("tester"):
      print("""
        Included with the framework is a module called, simply enough,
        `tester.py`. It has most of the features that you may be familiar
        with from other test framworks, such as Python's builtin
        `unittest`. In addition to the standard assert methods, it
        includes a `browser` for the purpose of running tests against
        websites, a `benchmark` subclass for performance testing, and
        other useful, framework specific features.
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
        In the above example, we have a rather contrived `tester` class called
        `int_tester` designed to test the behavior of Python `int`
        objects. Within this class, we have a test method called
        `it_assigns`. It's job is to ensure that integer assignments
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
          for `eq()` in Python's `unittest` is `assertEquals()'. This is
          because, when you are in a test method, shorter/abbreviated
          assertion methods are easy to spot since they are used so
          frequently. It also make writting exhaustive batteries of
          tests easier since less time is spent typing assertion method
          names.

          <aside>
            As of this writting, there are still methods that are named
            using the old, more verbose convention which are prefixed
            with the string 'assert'. For example, there is an
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

    with section('Mocks, Stubs, Fakes and Dummy Objects'):
      print('''
        Tests in Carapacian Core try to be as realistic as possible. One key
        example of this is database interaction: When you test a persistence
        operations, such as a call to the `save()` method of an ORM entity, a
        connection to a real MySQL database is used to issue a real
        query (assuming your environment's configurations is correctly
        set up). This is in constrast to the technique, sometimes
        employed of using a **fake**, in-memory database for testing.
        Using a database environment for testing that is equivelent to
        the production environment is necessary for catching database
        issue during testing before deploying to production.

        End-to-end testing is employed when for user interfaces. When
        developers create web `page` objects which contains persistence
        logic, they will also create tests to invoke the page.  These
        tests ensure that the page responds correctly, and that its
        interactions with the database are correct as well. Thus, it can
        be said that tests for the UI in the framework are fully
        integrated with backend database operations. See the section
        called <a href="8f60ca73">Page Testing</a> for more.

        This can also be said of backend operations involving third
        party services. When selecting a third party services, such as
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
        that provides a test environment, a web site should be created
        within the framework that behaves in a way that the production
        services is understood to behave. Tests should interact with
        that website to ensure framework logic is behaving correctly.
      ''')
      
    with section('Integration, regression or unit tests'):
      print('''
        The goal of automated testing in the framework is to ensure that
        the feature that the framework purports to have work. In
        addition to testing features, we also ensure that when a bug
        surfaces, tests are written to ensure that the bug will never
        resurface. The framework is able to provide a rich feature-set
        due to the extensive automated testing it receives. 

        A question may arise regarding whether these are unit tests. A
        unit tests is an automated test that sections (units) of source
        behave as expected. However, as stated above, we are interested
        in ensuring that features work as expected; not sections, thus
        the term "unit test" would be inappropriate for these tests.

        However, the phase "automated integration tests" would be
        appropriate because, as stated elsewhere, the features are
        tested in an end-to-end manor, that is to say: starting with the
        subject of the test (such as a user-interface, or an ORM object)
        and allowing those module to interact with external systems,
        such as databases and third party API's (or simulations only
        when necessary).

        Additionally, the phrase "automated regression tests" may be
        appropriate as well. Regression testing is defined by Wikipedia
        as the:

        > [R]e-running functional and non-functional tests to ensure that
        > previously developed and tested software still performs after
        > a change. If not, that would be called a regression.

        As stated, the Goal of the framework's tests is to ensure
        features continue to work, and that bugs are not allowed to
        resurface. Given that, we can also call the tests regression
        tests. 

        For the most part, there is no need to be specific, though. The
        tests can usually just be refered to as "automated tests" with
        out qualification.
      ''')

    with section('Page Testing', 0x8f60ca73):
      print('''
        The tester framework provides a ``browser`` class that makes it
        possible to run tests againsts web pages. The browse class has a
        collection of tabs just like a real browser. You can use the
        `get` and `post`  methods of a tab to make requests to
        a page with the corresponding HTTP verb. You can also use the
        `xhr` method to issue XHR requests (which are actually a special
        type of POST request).

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

        # Test the status of the respons
        self.status(200, res)

        # Ensure the tab contains within its internal DOM
        # a link to the Wikipedia article for "Freaks"
        as_ = tab['div#results a']

        # Iterate ove anchor tags
        for a in as_:
          if a.text == 'Freaks (1932 film) - Wikipedia':
            break
        else:
          # Fail if we can't find the anchor tag pointing to Freaks.
          self.fail(msg="Couldn't find 'Freaks'")

      print(it_searches)

      print('''
        For more examples of testing websites, see the 
        <a href="testpom.py">
          testpom.py
        </a> module.
      ''')

    with section('Test Setup and Teardown'):
      ...

    with section('How the Framework uses Tests'):
      print('''
        The general pattern for creating tests in the framework is to
        create a test module for each module. In the test module, a
        `tester` class should be created for each class in in the
        regular module. 

        For example, the <a href="order.py">order.py</a> module contains
        the logic to manage sales orders, purchase orders, and the like.
        It has a corresponding test module called <a
        href="testorder.py">testorder.py</a>. Within this module, are
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
        line:

          ./testproduct.py

        This will run all the tests in that module and print out any
        failures. To run only a particular class in a module, simply
        specify the class:

          ./testproduct.py product_

        This only runs the test class `product_` within the
        `testproduct.py` module.

        You can narrow it down further by specifying a test method:

          ./testproduct.py product_.it_creates

        This will only run the `it_creates` test method. This level of
        specificity is ideal during developing. Reducing the specificity
        to varying degrees is useful for making sure your logic changes
        don't introduce butterfly effects in the code. 

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
              debugger, it is more than worth you time learning its
              simple command-line interface.

              The `B` method is available in virtually any module in the
              framework. It is imported n moste modules from the 
              <a href="dbg.py">dbg.py</a> module:

                from dbg import B

              It's a simple wrapper to PDB's `set_trace` method.
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
                  conditional and otherwise. PDB's breakpoints can be
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

      with section('Benchmarking')
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

    
    
