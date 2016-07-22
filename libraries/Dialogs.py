import sys

if sys.platform.startswith('java'):
    from dialogs_jy import MessageDialog,PassFailDialog,InputDialog,SelectionDialog
elif sys.platform == 'cli':
    from dialogs_ipy import MessageDialog,PassFailDialog,InputDialog,SelectionDialog
else:
    from dialogs_py import MessageDialog,PassFailDialog,InputDialog,SelectionDialog

try:
    from robot.version import get_version
except ImportError:
    __version__ = '<unknown>'
else:
    __version__ = get_version()

__all__ = ['execute_manual_step','get_value_from_user',
           'get_selection_from_user','pause_execution']

def pause_execution(message='test execution paused.Press OK to continue.'):
    """
    Pauses test execution until user clikc ok button.
    message is the message shown in the dialog
    """
    MessageDialog(message).show()

def execute_manual_step(messgae,default_error=''):
    if not PassFailDialog(messgae).show():
        msg = get_value_from_user('Give error message:',default_error)
        raise AssertionError(msg)

def get_value_from_user(message,default_value=''):

    """
    Pauses test execution and asks user to input a value. Input value is returned by the keyword

    'Message' is the instruction shown in the input field . Selection 'Canel' fails the keyword
    Example:
        | ${value}= | get value from user | enter new value | deafault_value=1
        |Do something  | ${value}|
    """
    return _validate_user_input(InputDialog(message,default_value))

def get_selection_from_user(message,*values):
    """
    pauses test execution and asks user to select a  value
    'message' is the instruction shown in the dialog and 'values' are
    the options given to the user.selecting 'canel' fails the keyword
    """
    return _validate_user_input(SelectionDialog(message,values))


def _validate_user_input(dialog):
    value = dialog.show()
    if value is None:
        raise RuntimeError('No value provided by user.')
    return value