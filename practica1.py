
"""
Example:
    $ python practica1.py "web, www" "en la web encuentras todo lo que necesitas"
      Found: web between (6, 9)
"""

from argparse import ArgumentParser
import re


def find(regex, text):
    "To Do"
    pass


def parse_args():
    """Parse command line arguments"""
    parser = ArgumentParser(description="""Word recognition using Regular
                                        Expressions and Deterministic Finite
                                        Automata""")
    parser.add_argument("regex",
                        default=None,
                        metavar="<regex>",
                        help="regular expression"
                        )
    parser.add_argument("text",
                        default=None,
                        metavar="<text>",
                        help="text"
                        )
    args = parser.parse_args()
    return args.regex, args.text


def use_re(regex, text):
    """Use this method to test if the output of find(r,t) is correct"""
    regex = regex.replace(',', '|')
    found = re.finditer(regex, text)
    return [(x.start(), x.end(), x.group()) for x in found]


if __name__ == '__main__':
    regex, text = parse_args()
    found = use_re(regex, text)
    print found
