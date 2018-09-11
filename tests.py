import unittest
from slackbot import parse_direct_mention


class TestUM(unittest.TestCase):

    def test_mention(self):
        self.assertNotEqual(parse_direct_mention(
            "<@UCNEH0ZU3> hello"), (None, None))

    def test_no_mention(self):
        self.assertEqual(parse_direct_mention(
            "@eBot hello"), (None, None))


if __name__ == '__main__':
    unittest.main()
