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
        tests, the framework would likely be unmaintainable.  Virtually
        everything gets tested in the framework including:

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

    with section('Test systems vs mocking'):
      ...

    with section('DOM Testing'):
      ...

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

  with chapter("Using the Object-relational Mapper") as sec:
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

    
    
