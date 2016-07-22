from robot.errors import DataError
from robot.model import SuiteVisitor
from robot.result import ExecutionResult
from robot.utils  import get_error_message

class GatherFailedTests(SuiteVisitor):

    def __int__(self):
        self.tests = []


    def visit_test(self,test):
        if not test.passed:
            self.tests.append(test.longname)

    def visit_keyword(self,kw):
        pass


def gather_failed_tests(output):
    if output.upper() =='NONE':
        return []
    gatherer = GatherFailedTests()
    try:
        ExecutionResult(output).suite.visit(gatherer)
        if not gatherer.tests:
            raise DataError('All test passed')
    except:
        raise DataError("Collection failed tests from '%s'"
                        %(output,get_error_message)
                        )
    return  gatherer.tests


