import re
import fnmatch
from robot.utils  import asserts
import BuiltIn


BUILTIN = BuiltIn.BuiltIn()


class DeprecatedBuiltIn:
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'

    integer = BUILTIN.convert_to_integer
    float = BUILTIN.convert_to_number
    string = BUILTIN.convert_to_string
    boolean = BUILTIN.convert_to_boolean
    list = BUILTIN.create_list

    equal = equals = fail_unless_equal = BUILTIN.should_be_equal
    not_equal = not_equals = fail_if_equal = BUILTIN.should_not_be_equal
    is_true= fail_unless = BUILTIN