import os
import six
import unittest
import tempfile
from tests.baseclass import ParserTest

from pykickstart import constants
from pykickstart.errors import KickstartError

class Base_Include(ParserTest):
    def setUp(self):
        ParserTest.setUp(self)

        (handle, self._path) = tempfile.mkstemp(prefix="include-", text=True)
        ks = self.includeKS
        if six.PY3:
            ks = ks.encode('utf-8')

        os.write(handle, ks)
        os.close(handle)

    def tearDown(self):
        ParserTest.tearDown(self)
        os.unlink(self._path)

class Include_Packages_TestCase(Base_Include):
    ks = """
%%packages
%%include %s
-packageB
%%end
"""

    includeKS = """
packageA
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks % self._path)

        self.assertEqual(len(self.handler.packages.packageList), 1)
        self.assertEqual(len(self.handler.packages.excludedList), 1)

class Include_Commands_TestCase(Base_Include):
    ks = """
rootpw 123456
%%include %s
text
"""

    includeKS = """
autopart
clearpart --all
zerombr
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks % self._path)

        self.assertEqual(self.handler.rootpw.password, "123456")
        self.assertEqual(self.handler.displaymode.displayMode, constants.DISPLAY_MODE_TEXT)
        self.assertTrue(self.handler.autopart.autopart)
        self.assertEqual(self.handler.clearpart.type, constants.CLEARPART_TYPE_ALL)
        self.assertTrue(self.handler.zerombr.zerombr)

class Include_Whole_Script_TestCase(Base_Include):
    ks = """
%%include %s
"""

    includeKS = """
%pre
ls /tmp
%end
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks % self._path)
        self.assertEqual(len(self.handler.scripts), 1)

        # Verify the script defaults.
        script = self.handler.scripts[0]
        self.assertEqual(script.interp, "/bin/sh")
        self.assertFalse(script.inChroot)
        self.assertEqual(script.lineno, 2)
        self.assertFalse(script.errorOnFail)
        self.assertEqual(script.type, constants.KS_SCRIPT_PRE)

        # Also verify the body, which is the most important part.
        self.assertEqual(script.script.rstrip(), "ls /tmp")

class Include_Post_TestCase(Base_Include):
    ks = """
%%post
%%include %s
%%end
"""

    includeKS = """
ls /tmp
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks % self._path)
        self.assertEqual(len(self.handler.scripts), 1)

        # Verify the script defaults.
        script = self.handler.scripts[0]
        self.assertEqual(script.interp, "/bin/sh")
        self.assertTrue(script.inChroot)
        self.assertEqual(script.lineno, 2)
        self.assertFalse(script.errorOnFail)
        self.assertEqual(script.type, constants.KS_SCRIPT_POST)

        # Also verify the body, which is the most important part.
        self.assertEqual(script.script.rstrip(), "ls /tmp")

class Include_Pre_TestCase(Base_Include):
    ks = """
%%pre
%%include %s
%%end
"""

    includeKS = """
ls /tmp
"""

    def runTest(self):
        self.parser.readKickstartFromString(self.ks % self._path)
        self.assertEqual(len(self.handler.scripts), 1)

        # Verify the script defaults.
        script = self.handler.scripts[0]
        self.assertEqual(script.interp, "/bin/sh")
        self.assertFalse(script.inChroot)
        self.assertEqual(script.lineno, 2)
        self.assertFalse(script.errorOnFail)
        self.assertEqual(script.type, constants.KS_SCRIPT_PRE)

        # Also verify the body, which is the most important part.
        self.assertEqual(script.script.rstrip(), "ls /tmp")

class Include_URL_TestCase(Base_Include):
    ks = """
%%include %s
"""

    includeKS = """
%pre
ls /tmp
%end
"""

    def setUp(self):
        super(Include_URL_TestCase, self).setUp()

        server = six.moves.BaseHTTPServer.HTTPServer(('127.0.0.1', 0), six.moves.SimpleHTTPServer.SimpleHTTPRequestHandler)
        httpd_port = server.server_port
        self._httpd_pid = os.fork()
        if self._httpd_pid == 0:
            os.chdir(os.path.dirname(self._path))
            server.serve_forever()

        self._url = 'http://127.0.0.1:%d/%s' % (httpd_port, os.path.basename(self._path))

    def tearDown(self):
        super(Include_URL_TestCase, self).tearDown()

        import signal
        os.kill(self._httpd_pid, signal.SIGTERM)

    def runTest(self):
        self.parser.readKickstartFromString(self.ks % self._url)
        self.assertEqual(len(self.handler.scripts), 1)

        # Verify that the script body came through
        script = self.handler.scripts[0]
        self.assertEqual(script.script.rstrip(), "ls /tmp")

class Include_Bad_URL_TestCase(Include_URL_TestCase):
    def runTest(self):
        # Add some garbage to the end of the URL and ensure it breaks
        self.assertRaisesRegexp(KickstartError, "Error accessing URL",
                self.parser.readKickstartFromString, self.ks % (self._url + "-garbage"))

if __name__ == "__main__":
    unittest.main()
