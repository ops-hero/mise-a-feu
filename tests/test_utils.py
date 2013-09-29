import os
import unittest

from mise_a_feu.lib.utils import str2bool, get_config

class Str2BoolTestCase(unittest.TestCase):

    def test_conversion_to_true(self):
        self.assertEquals(str2bool(True), True)
        self.assertEquals(str2bool("True"), True)
        self.assertEquals(str2bool("true"), True)

    def test_conversion_to_false(self):
        self.assertEquals(str2bool(False), False)
        self.assertEquals(str2bool("False"), False)
        self.assertEquals(str2bool("false"), False)

    def test_other_case(self):
        with self.assertRaises(Exception):
            str2bool("dgsdgdf")
            str2bool(2)

class GetConfigTestCase(unittest.TestCase):

    def test_get_config(self):
        config_file = os.path.join(os.path.dirname(__file__), "..",
                                   "examples", "example_config.yml")
        config = get_config(config_file)
        self.assertEqual(["localhost"], config["hosts"])
        self.assertEqual(2, len(config["post_deployment"]))
