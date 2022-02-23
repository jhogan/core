#!/usr/bin/python3
# vim: set et ts=4 sw=4 fdm=marker

########################################################################
# Copyright (C) Jesse Hogan - All Rights Reserved                      #
# Unauthorized copying of this file, via any medium is strictly        #
# prohibited                                                           #
# Proprietary and confidential                                         #
# Written by Jesse Hogan <jessehogan0@gmail.com>, 2022                 #
########################################################################

import tester
import logs
from dbg import B
class test_logs(tester.tester):
    def it_writes_to_log_using_methods(self):
        # Since this goes to syslogd, a user will need to verify that
        # these messages were successfully logged.
        recs = []
        def onlog(src, eargs):
            recs.append(eargs.record.message)

        l = logs.log()

        l.onlog += onlog

        l.debug('mDEBUG')
        self.assertTrue('mDEBUG' in recs)
        self.assertCount(1, recs)

        l.info('mINFO')
        self.assertTrue('mINFO' in recs)
        self.assertCount(2, recs)

        l.warning('mWARNING')
        self.assertTrue('mWARNING' in recs)
        self.assertCount(3, recs)

        l.error('mERROR')
        self.assertTrue('mERROR' in recs)
        self.assertCount(4, recs)

        l.critical('mCRITICAl')
        self.assertCount(5, recs)

        self.assertTrue('mCRITICAl' in recs)
        try:
            raise Exception('derp')
        except:
            l.exception('mEXCEPTION')
            self.assertTrue('mEXCEPTION' in recs)
            self.assertCount(6, recs)

        recs = []
        def onlog1(src, eargs):
            recs.append(eargs.record.message)

        # Reinstantiate log and perform a similar test to those above.
        # Since the underlying `logger`` returned by the builtin Python
        # ``logging`` module always return the same logger object, we
        # want to make sure it is cleared out such that it's not
        # accumulating callbacks with each instantiation. In that case,
        # the below code would cause both onlog and onlog1 to be invoked
        # leading to superflous records in recs.
        l = logs.log()

        l.onlog += onlog

        l.debug('mDEBUG')
        self.assertTrue('mDEBUG' in recs)
        self.assertCount(1, recs)

    def it_writes_to_log_using_functions(self):
        logs.debug('fDEBUG')
        logs.info('fINFO')
        logs.warning('fWARNING')
        logs.error('fERROR')
        logs.critical('fCRITICAL')

if __name__ == '__main__':
    tester.cli().run()
