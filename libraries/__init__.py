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


























