import re
import time
from robot.output  import LOGGER, Message
from robot.errors  import (ContinueForLoop,DataError,ExecutionFailed,ExecutionFailures,
                           ExitForLoop,PassExecution,ReturnFromKeyword
                           )
from robot  import utils
from robot.utils import asserts
from robot.variables  import is_var,is_list_var
from robot.running import Keyword,RUN_KW_REGISTER
from robot.running.context import EXECUTION_CONTEXTS
from robot.running.usererrorhandler import UserErrorHandler
from robot.version import get_version

if utils.is_jython:
    from java.lang  import String,Number


try:
    bin
except NameError:
    def bin(integer):
        if not isinstance(integer,(int,long)):
            raise TypeError
        if integer >= 0:
            prefix ='0b'
        else:
            prefix ='-0b'
            integer = abs(integer)
        bins = []
        while  integer >1:
            integer, remainder = divmod(integer,2)
            bins.append(str(remainder))
        bins.append(str(integer))
        return prefix +''.join(reversed(bins))

def run_keyword_variant(resolve):
    def decorator(method):
        RUN_KW_REGISTER.register_run_keyword('BuiltIn',method.__name__,resolve)
        return method
    return decorator

class Converter:

    def convert_to_integer(self,item,base=None):
        self._log_types(item)
        return self._convert_to_integer(item,base)

    def _convert_to_integer(self,orig,base=None):
        try:
            item = self._handle_java_numbers(orig)
            if base:
                return int(item,self._convert_to_integer(base))
            return int(item)
        except:
            raise RuntimeError(" '%s' cannot be converted to an integer:%s"
                               %(orig,utils.get_error_message()))

    def _handle_java_numbers(self,item):
        if not utils.is_jython:
            return item
        if isinstance(item,String):
            return utils.unic(item)
        if isinstance(item,Number):
            return item.doubleValue()
        return item
    def _get_base(self,item,base):
        if not isinstance(item,basestring):
            return item,base
        item = utils.normalize(item)
        if item.startswith(('-','+')):
            sign = item[0]
            item =item[1:]
        else:
            sign = ''
        base = {'0b':2,'0o':8,'0x': 16}

        if base or not item.startswith(tuple(bases)):
            return sign+item,base
        return sign+item[2:],bases[item[:2]]

    def convert_to_binary(self,item,base=None,prefix=None,length=None):
        return self._convert_to_bin_oct_hex(bin,item,base,prefix,length)

    def convert_to_hex(self,item,base=None,prefix=None,length=None,
                       lowsercase=False):
        return self._convert_to_bin_oct_hex(hex,item,base,prefix,length,lowsercase)

    def _convert_to_bin_oct_hex(self,method,item,base,prefix,length,lowsercase=False):
        self._log_types(item)
        ret = method(self._convert_to_integer(item,base)).upper()
        prefix= prefix or ''
        if ret[0] =='-':
            prefix ='-' +prefix
            ret = ret[1:]
        if len(ret) >1:
            prefix_length = {bin:2,oct:1,hex:2}[method]
            ret = ret[prefix_length:]
        if length:
            ret = ret.rjust(self._convert_to_integer(length),'0')

    def convert_to_number(self,item,precision=None):
        self._log_types(item)
        return self._convert_to_number(item,precision)

    def _convert_to_number(self,item,precision=None):
        number = self._convert_to_number_without_precision(item)
        if precision:
            number = round(number,self._convert_to_integer(precision))
            return number
    def _convert_to_number_without_precision(self,item):

        try:
            if utils.is_jython:
                item = self._handle_java_numbers(item)
            return float(item)
        except:
            error = utils.get_error_message()
            try:
                return float(self._convert_to_integer(item))
            except RuntimeError:
                raise RuntimeError("'%s  cannot be converted to a floating"
                                   "point number: %s" %(item,error))

    def convert_to_string(self,item):
        self._log_types(item)
        return self._convert_to_string(item)

    def _convert_to_string(self,item):
        return utils.unic(item)

    def convert_to_boolean(self,item):
        self._log_types(item)
        if isinstance(item,basestring):
            if utils.eq(item,'True'):
                return True
            if utils.eq(item,'False'):
                return False
        return bool(item)

    def create_list(self,*items):
        return list(items)

class  Verify:
    def  _set_and_remove_tags(self,tags):
        set_tags = [tag for tag in tags if not tag.startswith('-')]
        remove_tags= [tag[1:] for tag in tags if tag.startswith('-')]
        if remove_tags:
            self.remove_tags(*remove_tags)
        if set_tags:
            self.set_tags(*set_tags)

    def fail(self,msg=None,*tags):
        self._set_and_remove_tags(tags)
        raise AssertionError(msg) if msg else AssertionError()

    def fatal_error(self,msg=None):
        error = AssertionError(msg) if msg else AssertionError()
        error.ROBOT_EXIT_ON_FAILURE = True
        raise error

    def should_not_be_true(self,condition,msg=None):
        if not msg:
            msg="'%s' should not be true" %condition
            assert.fail_if(self._is_true(conditon),msg)

    def should_be_true(self,condition,msg=None):
        if not msg:
            msg="'%s' should be true " %condition
            assert.fail_unless(self._is_true(condition),msg)

    def should_be_equal(self,first,second,msg=None,values=True):
        self._log_types(first,second)
        self._should_be_equal(first,second,msg,values)

    def _should_be_equal(self,first,second,msg,values):
        assert.fail_unless_equal(first,second,msg,self._include_values(values))

    def _log_types(self,*args):
        msg= ['Argument types are:'] + [self._get_type(a) for a in args]
        self.log('\n'.join(msg))

    def _get_type(self,arg):
        if isinstance(arg,unicode):
            return "<type 'unicode'>"
        return str(type(arg))

    def _include_values(self,values):
        if isinstance(values,basestring):
            return values.lower() not in ['no values','false']
        return bool(values)


    def  should_not_be_equal(self,first,second,msg=None,values=True):
        self._log_types(first,second)
        self._should_not_be_equal(first,second,msg,values)

    def  should_not_be_equal_as_integers(self,first,second,msg=None,
                                         values=True,base=None
                                         ):
        self._log_types(first,second)
        self._should_be_equal(self._convert_to_integer(first,base),
                              self._convert_to_integer(second,base),
                              msg,values)

    def should_be_equal_as_numbers(self,first,second,msg=None, value=True,
                                    precision=6):

        self._log_types(first,second)
        first = self._convert_to_number(first,precision)
        second = self._convert_to_number(second,precision)
        self._should_not_be_equal(first,second,msg,values)


    def should_be_equal_as_numbers(self,first,second,msg=None,values=True,
                                   precision=6):
        self._log_types(first,second)
        first = self._convert_to_number(first,precision)
        second = self._convert_to_number(second,precision)
        self._should_be_equal(first,second,msg,values)

    def should_not_be_equal_as_strings(self,first,second,msg=None,values=True):
        self._log_types(first,second)
        first,second = [self._convert_to_string(i) for i in first,second]
        self._should_not_be_equal(first,second,msg,values)

    def should_be_equal_as_strings(self,first,second,msg=None,values=True):
        self._log_types(first,second)
        first,second = [self._convert_to_string(i) for i in first, second]
        self._should_be_equal(first,second,msg,values)

    def should_not_start_with(self,str1,str2,msg=None,values=True):
        msg= self._get_string_msg(str1,str2,msg,values,'starts with')
        asserts.fail_if(str1.startswith(str2),msg)

    def should_start_with(self,str1,str2,msg=None,values=True):
        msg = self._get_string_msg(str1,str2,msg,values,'does not start with')
        asserts.fail_unless(str1.startwith(str2),msg)

    def should_not_end_with(self,str1,str2,msg=None,values=True):
        msg = self._get_string_msg(str1,str2,msg=None,values=True):
        asserts.fail_unless(str1.endswith(str2),msg)

    def should_end_with(self,str1,str2,msg=None,values=True):
        msg = self._get_string_msg(str1,str2,msg,'does not end with')
        asserts.fail_unless(str1.endswith(str2),msg)

    def should_not_contain(self,item1,item2,msg=None,values=True):
        msg = self._get_string_msg(item1,item2,msg,values,'contains')
        asserts.fail_if(item2 in item1, msg)

    def should_contain(self,item1,item2,msg=None,values=True):
        msg = self._get_string_msg(item1,item2,msg,values,'does not contain')
        asserts.fail_unless(item2 in item1,msg)

    def should_contain_x_times(self,item1,item2,count,msg=None):
        if not msg:
            msg = "'%s' does not contain '%s' %s times"\
                    %(utils.unic(item1),utils.unic(item2),count)
            self.should_not_be_equal_as_integers(self.get_count(item1,item2),
                                                 count,msg,values=False)

    def get_count(self,item1,item2):
        if not hasattr(item1,'count'):
            try:
                item1 = list(item1)
            except:
                raise RuntimeError("Converting '%s' to list failed: %s"
                                   %(item1,utils.get_error_message()))
            count = item1.count(item2)
            self.log('Item found from the first item %d time%s'
                     %(count,utils.plural_or_not(count))
                     )
            return count
    def should_not_match(self,string,pattern,msg=None,values=True):
        msg = self._get_string_msg(string,pattern,msg,values,'matches')
        asserts.fial_if(self._matches(string,pattern),msg)

    def should_match(self,string,pattern,msg=None,values=True):
        msg = self._get_string_msg(string,pattern,msg,values,'does not match')
        asserts.fail_unless(self._matches(string,pattern),msg)

    def should_match_regexp(self,string,pattern,msg=None,values=True):
        msg = self._get_string_msg(string,pattern,msg,values,'does not match')
        res = re.search(pattern,string)
        asserts.fail_if_none(res,msg,False)
        match = res.group(0)
        groups = res.groups()
        if groups:
            return [match] + list(groups)
        return match
    def should_not_match_regexp(self,string,pattern,msg=None,values=True):
        msg = self._get_string_msg(string,pattern,msg,values,'matches')
        asserts.fail_unless_none(re.search(pattern,string),msg,False)

    def get_length(self,item):
        length = self._get_length(item)
        self.log('Length is %d'%length)
        return length
    def _get_length(self,item):
        try:return len(item)
        except:utils.RERAISED_EXCEPTIONS: raise
        except:
            try: return item.size()
            except: utils.RERAISED_EXCEPTIONS: raise
            except:
                try: return item.length
                except utils.RERAISED_EXCEPTIONS:raise
                excpet:
                    raise RuntimeError("Could not get length of '%s'" %item)

    def length_should_be(self,item,length,msg=None):
        length = self._convert_to_integer(item)
        actual = self.get_length(item)
        if actual != length:
            raise AssertionError(msg or "length of '%s' should be %d but is %d but is %d"
                                 %(item,length,actual))

    def should_be_empty(self,item,msg=None):
        if self.get_length(item) ==0:
            raise AssertionError(msg or "'%s' should not be empty" %item)

    def _get_string_msg(self,str1,str2,msg,values,delim):
        default="'%s' %s '%s'" % (utils.unic(str1),delim,utils.unic(str2))
        if not msg:
            msg = default
        elif values is True:
            msg ='%s:%s' %(msg,default)

        return msg

class Variables:
    def get_variables(self):
        return utils.NormalizedDict(self._variables.current,ignore='_')

    @run_keyword_variant(resolve=0)
    def get_variable(self,name,defalut=None):
        try:
            return self._variables.replace_scalar(defalut)

    def log_variables(self,level='INFO'):
        variables = self.get_variable()
        for name in sorted(variables.keys(),key=lambda s: s.lower()):
            msg = utils.format_assign_message(name,variables[name],
                                         cut_long=False)
            self.log(msg,level)

    @run_keyword_variant(resolve=0)
    def variable_should_exist(self,name,msg=None):
        name = self._get_var_name(name)
        msg = self._variable.replace_string(msg) if msg \
            else "Variable %s does not exist" %name
        asserts.fail_unless(name in self._variables,msg)

    @run_keyword_variant(resolve=0)
    def variable_should_not_exist(self,name,msg=None):
        name =self._get_var_name(name)
        msg = self._variables.replace_string(msg) if msg  \
            else "Variable %s exists" %name
        asserts.fail_if(name in self._variables,msg)

    def replace_variables(self,text):

        """
        replaces variables in the given text with their current
        values. if the text contains undefined  variables ,this
        keyword fails.if the given 'text' contains only a single
        variable ,its value is retruned as-is and it can be any object ,otherwise this keyword
        always return a string


        """
        return self._variables.replace_scalar(text)

    def set_variable(self,*values):
        if len(values) ==0:
            return ''
        elif len(values) ==1:
            return values[0]
        else :
            return list(values)

    @run_keyword_variant(resolve=0)
    def set_test_variable(self,name,*values):
        """
        makes a variable avaliable everywhere within the scope of the current test
        scope of the currently executed testcase,for example ,if you set a variable in a user
        keyword.it is available both in the test case level and also in all other user keywords
        used in the current test.other test cases will not see variables set with this keyword.
        see 'Set suite vairbale' for more information and examples

        """
        name = self._get_var_name(name)
        value = self._get_var_value(name,values)
        self._variables.set_test(name,value)
        self._log_set_variable(name,value)

    @run_keyword_variant(resolve=0)
    def set_suite_variable(self,name,*values):
        name= self._get_var_name(name)
        value = self._get_var_value(name,values)
        self._variables.set_suite(name,value)
        self._log_set_variable(name,value)

    @run_keyword_variant(resolve=0)
    def set_global_variable(self,name,*values):
        name = self._get_var_name(name)
        value = self._get_var_value(name,values)
        self._variiables.set_global(name,value)
        self._log_set_variable(name,value)

    def _get_var_name(self,orig):
        name = self._resolve_possible_variable(orig)
        try:
            return self._unescape_variable_if_needed(name)
        except ValueError:
            raise RuntimeError("Invalid variable syntax '%s'" %orig)

    def _resolve_possible_variable(self,name):
        try:
            resolved = self._variables[name]
            return self._unescape_variable_if_needed(resolved)
        except (KeyError, ValueError,DataError):
            return name

    def _unescape_variable_if_needed(self,name):
        if not (isinstance(name,basestring) and len(name) >1):
            raise ValueError
        if name.startswith('\\'):
            name = name[1:]
        elif name[0] in ['$','@'] and name[1] != '{':
            name ='%s{%s}' %(name[0],name[1:])
        if is_var(name):
            return name

        name = '%s{%s}' %(name[0],self.replace_variables(name[2:-1]))
        if is_var(name):
            return name
        raise ValueError

    def _get_var_value(self,name,values):
        if not values:
            return self._variables[name]
        values = self._variables.replace_list(values)
        if len(values) ==1 and name[0]=='$':
            return values[0]
        return list(values)

    def _log_set_variable(self,name,value):
        self.log(utils.format_assign_message(name,value))

class RunKeyword:
    #if you use any of these run keyword variants from another library,
    #should register those keyword with 'register_run_keyword' method.see
    #the documentation of that method at the end of this file.there are also
    #other run kyeword variant keywords in builtIn which can also be seen
    #at the end of this file

        def run_keyword(self,name,*args):
            """
            because the name of the keyword to execute is given as an argument
            is can be a vairbale and thus set dynamically,e.g.form a return value
            of another keyword or the command line
            """
            if not isinstance(name,basestring):
                raise RuntimeError('Keyword name must be a string')
            kw = Keyword(name,list(args))
            return kw.run(self._context)

        def run_keywords(self,*keywords):

            errors =[]
            for kw,args in self._split_run_keywords(list(keywords)):
                try:
                    self.run_keyword(kw,*args)
                except ExecutionFailed,err:
                    errors.extend(err.get_errors())
                    if not err.can_continue(self._context.in_teardown):
                        break
            if errors:
                raise ExecutionFailures(errors)


        def _split_run_keywords(self,keywords):
            if 'AND' not in keywords:
                for name in self._variables.replace_list(keywords):
                    yield name, ()
            else:
                for name,args in self._splist_run_keywords_from_and(keywords):
                    yield name,args

        def _split_run_keywords_from_and(self,keywords):
            while 'AND' in keywords:
                index = keywords.index('AND')
                yield  self._resolve_run_keywords_name_and_args(keywords[:index])
        def _resolve_run_keywords_name_and_args(self,kw_call):
            kw_call = self._variables.replace_list(kw_call,replace_until=1)
            if not kw_call:
                raise DataError('Incorrect use of AND')
            return kw_call[0],kw_call[1:]

        def run_keyword_if(self,condition,name,*args):
            args,branch = self._split_elif_or_else_branch(args)
            if self._is_true(condition):
                return self.run_keyword(name,*args)
            return branch()

        def _split_elif_or_else_branch(self,args):
            if 'ELSE IF ' in args:
                args,branch = self._split_branch(args,'ELSE IF ',2,
                                                 'condition and keyword')
                return args,lambda: self.run_keyword_if(*branch)
            if 'ELSE' in args:
                args, branch = self._split_branch(args,'ELSE',1,'keyword')
                return args,lambda: self.run_keyword(*branch)
            return args, lambda:None
        def _split_branch(self,args,control_word,required,required_error):
            index = list(args).index(control_word)
            branch = self._variables.replace_list(args[index+1:],required)
            if len(branch) < required:
                raise DataError('%s requires %s' %(control_word,required_error))
            return args[:index],branch

        def run_keyword_unless(self,condition,name,*args):
            if not self._is_true(condition):
                return self.run_keyword(name,*args)

        def run_keyword_and_ignore_error(self,name,*args):
            """
            run the given keyword with given arguments and ignores possible error.
            this keyword returns two values,so that the first is either 'PASS'
            or 'FAIL',depending on the status of executed keyword.the second value
            is  either the return value of the keyword or the receied error message

            """
            try:
                return 'PASS',self.run_keyword(name,*args)
            except ExecutionFailed, err:
                if err.dont_continue:
                    raise
                return 'FAIL',unicode(err)

        def run_keyword_and_return_status(self,name,*args):
            status,_ = self.run_keyword_and_ignore_error(name,*args)
            return status =='PASS'

        def run_keyword_and_continue_on_failure(self,name,*args):
            try:
                return self.run_keyword(name,*args)
            except  ExecutionFailed,err:
                if not err.dont_continue:
                    err.continue_on_failure = True
                raise err

        def run_keyword_and_expect_error(self,expected_error,name,*args):
            try:
                self.run_keyword(name,*args)
            except ExecutionFailed,err:
                if err.dont_continue:
                    raise
            else:
                raise AssertionError("Ecpected error '%s' did not occur"
                                     % expected_error)
            if not self._matches(unicode(err),expected_error):
                raise AssertionError("Expected error '%s' but got '%s'"
                                     % (expected_error,err))
            return unicode(err)



        def repeat_keyword(self,times,name,*args):
            times = utils.normalize(str(times))
            if times.endswith('times'):
                times = times[:-5]
            elif times.endswith('x'):
                times = times[:-1]
            times = self._convert_to_integer(times)
            if times <=0:
                self.log("Keyword '%s repeat zero times" %name)
            for i in xrange(times):
                self.log("Repeating keyword,round %d/%d" %(i+1,times))
                self.run_keyword(name,*args)

        def wait_until_keyword_succeeds(self,timeout,retry_interval,name,*args):
            """
            waits until the specitied keyword succeeds or the given timeout expiress
            'name' and 'args' define the keyword that is executed
            similarly as with 'run keyword'.if the specified keyword does not succeed within 'timeout'
            this keyword fails. 'retry_interval' is the time to ait before trying to run the keyword
            again after the previous run has failed
            """
            timeout = utils.timestr_to_secs(timeout)
            retry_interval = utils.timestr_to_secs(retry_interval)
            maxtime = time.time() + timeout
            error = None
            while not error
                try:
                    return self.run_keyword(name,*args)
                except ExecutionFailed, err:
                    if err.dont_continue:
                        raise
                    if time.time() >maxtime:
                        error = unicode(err)
                    else:
                        time.sleep(retry_interval)
                    raise AssertionError("timeout %s exceeded. The last error was : %s"
                                         %(utils.secs_to_timestr(timeout),error))

        def set_variable_if(self,condition,*value):
            """
                set variable based on the given condition.The basic usage is giving a condition
                and two values.The given condtion is first evaluated the same way as with the
                shoule be true keyword. if condition is true,then the first value is retruned
                and otherwise the second value is returned.the second value van also be omitted
                in which case it has a default value None,This usage is illustrated in the
                examples below ,where '${rc}' is assumed to be zero

            """
            values = self._verify_values_for_set_variable_if(list(values))
            if self._is_true(condition):
                return self._variables.replace_scalar(values[0])
            values = self._verify_values_for_set_variable_if(values[1:],True)
            if len(values) ==1:
                return self._variables.replace_scalar(values[0])
            return self.run_keyword('BuiltIn.Set Variable If',*values[0:])

        def _verity_values_for_set_variable_if(self,values,default=False):
            if not values:
                if default:
                    return [None]
                raise RuntimeError('At least one value is required')
            if is_list_var(values[0]):
                values[:1] =[utils.escape(item) for item in
                             self._variables[values[0]]]
                return self._verity_values_for_set_variable_if(values)
            return values

        def run_keyword_if_test_failed(self,name,*args):
            """
            runs the given keyword with the given arguemnts,if the test failed
            this keyword can only be used in a test teardown.Trying to use it anywhere
            else results in an error
            otherwise ,this keyword works exactly like 'Run kyeword',see its documentation
            for more details
            """
            test = self._get_test_in_teardown('Run Keyword If Test Failed')
            if not test.passed:
                return self.run_keyword(name,*args)

        def run_keyword_if_test_passed(self,name,*args):
            test = self._get_test_in_teardown('Run Keyword If Test Passed')
            if test.passed:
                return self.run_keyword(name,*args)

        def run_keyword_if_timeout_occurred(self,name,*args):
            self._get_test_in_teardown('Run Keyword If Timeout Occurred')
            if self._context.timeout_occurred:
                return self.run_keyword(name,*args)

        def _get_test_in_teardown(self,kwname):
            ctx = self._context
            if ctx.test and ctx.in_test_teardown:
                return ctx.test
            raise RuntimeError(" Keyword '%s' can only be used in test teardown"
                               % kwname)

        def run_keyword_if_all_critical_test_passed(self,name,*args):
            """
            Runs the given keyword with the given arguments ,if all critical tests passed
            this keyword can only be used in suite teardown. Trying to use it in any other
            palce will result in an error

            otherwise ,this keyword works exactly like 'run kyeword',see its documentation for more details

            """
            suite = self._get_suite_in_teardown('Run Keyword If all Critical Tests Passed'
                                                )
            if suite.statistics.critical.failed == 0:
                return self.run_keyword(name,*args)

        def run_keyword_if_any_critical_tests_failed(self,name,*args):
            suite = self._get_suite_in_teardown('Run Keyword If Any Critical Tests Failed')
            if suite.statistics.critical.failed >0:
                return self.run_keyword(name,*args)

        def run_keyword_if_all_tests_passed(self,name,*args):
            suite = self._get_suite_in_teardown('Run Keyword if all tests passed')
            if suite.statistics.all.failed == 0:
                return self.run_keyword(name,*args)

        def run_keyword_if_any_tests_failed(self,name,*args):
            suite = self._get_suite_in_teardown('run keyword if any tests failed')
            if suite.statistics.failed > 0:
                return self.run_keyword(name,*args)

        def _get_suite_in_teardown(self,kwname):
            if not self._context.in_suite_teardown:
                raise RuntimeError("Keyword '%s' can only be used in suite teardown"
                                   % kwname)
            return self._context.in_suite



class Control:
    def continue_for_loop(self):
        self.log("continuing for loop form the next interation")
        raise ContinueForLoop()

    def continue_for_loop_if(self,condition):
        if self._is_true(condition):
            self.continue_for_loop()

    def exit_for_loop(self):
        self.log("Exiting for loop altogether.")
        raise ExitForLoop()

    def exit_for_loop_if(self,condition):
        if self._is_true(condition):
            self.exit_for_loop()

    @run_keyword_variant(resolve=0)
    def return_from_keyword(self,*return_values):
        self.log('return form the encolosing user keyword.')
        raise ReturnFromKeyword(return_values)

    @run_keyword_variant(resolve=1)
    def return_from_keyword_if(self,condition,*return_values):
        if self._is_true(condition):
            self.return_from_keyword(*return_values)

    def pass_execution(self,message,*tags):
        message = message.strip()
        if not message:
            raise RuntimeError('Message cannot be empty')
        self._set_and_remove_tags(tags)
        log_message,level = self._get_logged_test_message_nad_level(message)
        self.log('Execution passed with message:\n%s' %log_message,level)
        raise PassExecution(message)
    @run_keyword_variant(resolve=1)
    def pass_execution_if(self,condition,message,*tags):
        if self._is_true(condition):
            message = [self._variable.replace_string(tag) for tag in tags]
            self.pass_execution(message,*tags)

class Misc:
    def no_operation(self):
        """does absolutely nothing"""

    def sleep(self,time_,reason=None):
        seconds = utils.timestr_to_secs(time_)
        if seconds <0:
            seconds =0
        self._sleep_in_parts(seconds)
        self.log('Slept %s' %utils.secs_to_timestr(seconds))
        if reason:
            self.log(reason)

    def _sleep_in_parts(self,seconds):
        endtime = time.time() + float(seconds)
        while True:
            remaining = endtime - time.time()
            if remaining <= 0:
                break
            time.sleep(min(remaining,0.5))

    def catenate(self,*items):
        if not items:
            return ''
        items = [utils.unic(item) for item in items]
        if items[0].startswith('SEPARATOR='):
            sep = items[0][len('SEPARATOR='):]
            items = items[1:]
        else:
            sep=''
        return sep.join(items)

    def log(self,message,level="INFO"):
        LOGGER.log_message(Message(message,level))

    def log_many(self,*message):
        for msg in messages:
            self.log(msg)

    @run_keyword_variant(resolve=0)
    def comment(self,*mesage):
        pass

    def set_log_level(self,level):
        try:
            old = self._context.output.set_log_level(level)
        except DataError, err:
            raise RuntimeError(unicode(err))
        self._namespace.variables.set_global('${LOG_LEVEL}',level.upper())
        self.log('Log level changed from %s from %s to %s' %(old,level.upper()))
        return old


    @run_keyword_variant(resolve=0)
    def import_library(self,name,*args):
        try:
            self._namespace.import_library(name,list(args))
        except DataError,err:
            raise RuntimeError(unicode(err))

    @run_keyword_variant(resolve=0)
    def import_variables(self,path,*args):
        try:
            self._namespace.import_variables(path,list(args),overwrite=True)
        except DataError,err:
            raise RuntimeError(unicode(err))

    @run_keyword_variant(resolve=0)
    def import_resource(self,path):
        try:
            self._namespace.import_resource(path)
        except DataError(unicode(err))


    def set_library_search_order(self,*libraries):
        old_order = self._namespace.library_search_order
        self._namespace.library_search_order = libraries
        return old_order

    def keyword_should_exist(self,name,msg=None):
        """
        fails unless the given keyword exists in the cuttent scope
        fails also if there are more than on  keywords with the same name
        works both with the short name and the full name
        the default error message can be overridden with the 'msg' :argument
        """
        try:
            handler = self._namespace._get_handler(name)
            if not handler:
                raise DataError("No keyword with name '%s' found." % name)
            if isinstance(handler,UserErrorHandler):
                handler.run()
        except DataError, err:
            raise AssertionError(msg or unicode(err))

    def get_time(self,format='timestamp',time_='NOW'):
        return utils.get_time(format,utils.pase_time(time_))


    def evaluate(self,expression,modules=None):
        modules = modules.replace(' ','').split(',') if modules else []
        namespace = dict((m, __import__(m)) for m in modules if m !='')
        try:
            return eval(expression,namespace)
        except:
            raise RuntimeError("evaluating expression '%s' failed: %s"
                               %(expression,utils.get_error_message()))

    def call_method(self,object,method_name,*args):
        """
        calls the named method of the given object with the returned and can be
        assigned to a variable.Keyword fails both if the object does not have a method
        with the given name or if execting the method raises an exception
        """
        try:
            method = getattr(object,method_name)
        except AttributeError:
            raise RuntimeError("Object '%s' does not have method '%s'"
                               %(object,method_name))
        return method(*args)

    def regexp_escape(self,*patterns):
        if len(patterns) ==0:
            return ''
        if len(patterns) ==1:
            return re.escape(patterns[0])
        return [re.escape(p) for p in patterns]

    def set_test_messge(self,messgae,append=False):
        test = self._namespace.test
        if not test:
            raise RuntimeError(" 'Set Test Message' keyword cannot be used in "
                               "suite setup or teardown")
        test.message= self._get_possibly_appended_value(test.message,messgae,append)
        message,level = self._get_logged_test_messge_and_level(test.message)
        self.log('set test message to :\n%s' % message ,level)

    def _get_possibly_appended_value(self,initial,new,append):
        if not isinstance(new,unicode):
            new = utils.unic(new)
        return '%s %s' %(initial,new) if append and initial else new

    def _get_logged_test_message_and_level(self,message):
        if message.startwith('*HTML*'):
            return message[6:].lstrip(), 'HTML'
        return message,'INFO'

    def set_test_documentation(self,doc,append=False):
        test = self._namespace.test
        if not test:
            raise RuntimeError(" 'set test documentation' keyword cannot be used in "
                               "suite setup or teardown")
        test.doc = self._get_possibly_appended_value(test.doc,doc,append)
        self._variables.set_test('${TEST_DOCUMENTATION}',test.doc)
        self.log('Set test documentation to:\n%s' %test.doc)

    def set_suite_documentation(self,doc,append=False,top=False):
        ns = self._get_namespace(top)
        suite=ns.suite
        suite.doc= self._get_possibly_appended_value(suite.doc,doc,append)
        ns.variables.set_suite('${SUITE_DOCUMENTATION}',suite.doc)
        self.log('Set suite documentaion to:\n%s' %suite.doc)

    def set_suite_metadata(self,name,value,append=False,top=False):
        if not isinstance(name,unicode):
            name = utils.unic(name)
        ns = self._get_namespace(top)
        metadata = ns.suite.metadata
        metadata[name] = self._get_possibly_appended_value(metadata.get(name,''), value,append)
        ns.variables.set_suite('${SUITE_METADATA}',metadata.copy())
        self.log("Set suite metadata '%s' to value '%s'. " % (name,metadata[name]))

    def set_tags(self,*tags):
        ctx = self._context
        if ctx.test:
            ctx.test.tags.add(tags)
            ctx.variables.set_test('@{TEST_TAGS}',list(ctx.test.tags))
        elif not ctx.in_suite_teardown:
            ctx.cuit.set_tags(tags,persist=True)
        else:
            raise RuntimeError(" 'set tags' cannot be used in suite teardown.")
        self.log('set tags%s %s.' %(utils.plural_or_not(tags),
                                    utils.seq2str(tags)))

    def remove_tags(self,*tags):
        ctx = self._context
        if ctx.test:
            ctx.test.tags.remove(tags)
            ctx.variables.set_test('@{TEST-tags}',list(ctx.test.tags))
        elif not ctx.in_suite_teardown:
            ctx.suite.set_tags(remove=tags,persist=True)
        else:
            raise RuntimeError("'remove tags' cannot be used in suite teardown.")
        self.log('removed tag%s' %(utils.plural_or_not(tags)))

    def get_library_instance(self,name):
        try:
            return self._namespace.get_library_instance(name)
        except DataError,err:
            raise RuntimeError(unicode(err))


class BuiltIn(_Verify,_Converter,_Variables,_RunKeyword,_Control,_Misc):

    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()

    @property
    def _context(self):
        return EXECUTION_CONTEXTS.current

    @property
    def _namespace(self):
        return self._context.namespace

    @property
    def _get_namespace(self,top=False):
        ctx = EXECUTION_CONTEXTS.top if top else EXECUTION_CONTEXTS.current
        return ctx.namespace

    @property
    def _variables(self):
        return self._namespace.variables


    def _matches(self,string,pattern):
        matcher = utils.Matcher(pattern,caseless=False,spaceless=False)
        return matcher.match(string)
    def _is_true(self,condition):
        if isinstance(condition,basestring):
            condition = self.evaluate(condition,modules='os,sys')
        return bool(condition)

def register_run_keyword(library,keyword,args_to_process=None):
    RUN_KW_REGISTER.register_run_keyword(library,keyword,args_to_process)

for name in [attr for attr in dir(_RunKeyword) if not attr.startswith('_')]:
    register_run_keyword('BuiltIn',getattr(_RunKeyword,name))
del name,attr





















