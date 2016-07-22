from robot.api import logger
from robot.utils import plural_or_not ,seq2str,seq2str2,unic
from robot.utils.asserts import assert_equals
from robot.version import get_version

class  List:
    def convert_to_list(self,item):
        return list(item)

    def append_to_list(self,list_,*values):

        for value in values:
            list_.append(value)

    def insert_into_list(self,list_,index,value):
        list_.insert(self._index_to_int(index),value)


    def combine_lists(self,*lists):
        ret = []
        for item in lists:
            ret.extend(item)
        return ret

    def set_list_value(self,list_,index,value):
        try:
            list_[self._index_to_int(index)] = value
        except IndexError:
            self._index_error(list_,index)

    def remove_values_from_list(self,list_,*values):

        """
        removes all occurences of given values from list
        it is not an error is a value does not exist in the list all

        example:
        remove values from list    ${L4}   a | c |e|f
        """
        for value in values:
            while value in list_:
                list_.remove(value)

    def remove_from_list(self,list_,index):
        """
        remove and returns the value spcified with an 'index' from 'list'
        index  '0' means the first position  '1' the second and so on
        simalarly, '-1' is the last position, '-2' the second last,and so on
        Using an index that does not exist on the exsit on the list causes an error
        The index can be either an integer or a string that can be converted
        to an integer
        example:
        ${x} =  |remove from list |${L2} |0|
        =>${x}='a'
        -${L2} =['b']
        """
        try:
            return list_.pop(self._index_to_int(index))
        except  IndexError:
            self._index_error(list_,index)

    def remove_duplicates(self,list_):
        """
        returns a list without duplicates based on given 'list'
        create and returns a new listr that contains all items in the given
        list so that one item can appear only once.Order of the items in
        the new list is the same as in the original except for missing
        duplicates ,.Number of the removed duplicates is logged
        """
        ret =[]

        for item in list_:
            if item not in ret:
                ret.append(item)
        removed  = len(list_)-len(ret)
        logger.info('%d duplicate%s removed.' %(removed,plural_or_not(removed)))
        return ret

    def get_from_list(self,list_,index):
        """
        returns the value specified with an 'index' from list
        the given list is nerver alerted by this keyword
        index '0' means the first position.'1' the second ,and so on
        similarly, '-1' is the last position, '-2' the second last ,and so on
        using an index can be either an integer or  a string that can be converted to an integer
        exmaples
        |${x} = |get from list |${L1} |0|  #L5[0]

        """


        try:
            return list_[self._index_to_int(index)]
        except IndexError:
            self._index_error(list_,index)

    def get_slice_from_list(self,list_,start=0,end=None):
        """
        returns a slice of the gieven list between 'start' and 'end' indexes
        the given list is never altered by this keyword
        """
        start = self._index_to_int(start,True)
        if end is not None:
            end= self._index_to_int(end)

        return list_[start:end]

    def count_values_in_list(self,list_,value,start=0,end=None):
        """
        returns the number of occurrences of the given value in list the search can be narrowed
        to the 'start'  and 'end' indexed having the sanme semantics in the 'get slice from list'
        keyword .The given list is never altered by this keyword

        example:
         ${x}=| Count values In List |${L3} |b|
         =>
         -${x} = 1
         - ${L3} is not changed
        """
        return self.get_slice_from_list(list_,start,end).count(value)

    def get_index_from_list(self,list_,value,start=0,end=None):
        if start == '':
            start =0
        list_ = self.get_slice_from_list(list_,start,end)
        try:
            return int(start) +list_.index(value)
        except  ValueError:
            return -1

    def copy_list(self,list_):
        """
        returns a copy of the given list.
        the given list is never altered by this keyword
        """
        return list_[:]

    def reverse_list(self,list_):
        """
        reverse the given list in place.
        note that the given list is changed and nothing is returned. use 'copy list' first if you need to keep also
        the original order
        |reverse list |${L3} |
        """
        list_.reverse()

    def sort_list(self,list_):
        """
        sorts the given list in place.
        the strings art sorted alphabetically an d the numbers numerically
        note that the given list is changed and nothing is returned .Use 'copy list' first if you need to keep also
        the original order
        ${L} = [2,1,'a','c','b']
        |sort list |${L}
        =>
        - ${L} = [1,2,'a','b','c']

        """
        list_.sort()

    def list_should_contain_value(self,list_,value,msg=None):
        """
        fails if the 'value' is not found from list.

        if msg is not given. the default error message "[a|b|c]  does not contain the value 'x'" is shown in case of
        a failure.Otherwise.the given 'msg' is used in case of a failure

        """

        default ="%s contains value '%s'" %(seq2str(list_),value)
        _verify_condition(vlaue not in list_,default,msg)

    def  list_should_not_contain_duplicates(self,list_,msg=None):
        """
        fails if any element in the 'list' is found from it more that were found
        from the 'list' multiple times .but it can be overriden by giving
        a custom 'msg' .All multiple times found items and their counts are also logged

        this keyword works with all iterables that can be converted to a list
        the original iterable is never altered

        """
        if not isinstance(list_,list):
            list_= list(list_)
        dupes = []
        for item in list_:
            if item not in dupes:
                count = list_.count(item)
                if count >1:
                    logger.info(" '%s' found %d times" %(item,count))
                    dupes.append(item)
        if dupes:
            raise AssertionError(msg or '%s found multiple times' %seq2str(dupes))

    def lists_should_be_equal(self,list1,list2,msg=None,values=True,names=None):
        len1 = len(list1)
        len2 = len(list2)
        default = 'lengths are different: %d != %d' %(len1,len2)
        _verify_condition(len1 == len2, default,msg,values)
        names = self._get_list_index_name_mapping(names,len1)
        diffs = list(self._yield_list_diffs(list1,list2,names))
        default = 'Lists are different:\n' + '\n'.join(diffs)
        _verify_condition(diffs == [],default,msg,values)

    def _get_list_index_name_mapping(self,names,list_length):
        if not names:
            return {}
        if isinstance(names,dict):
            return dict((int(index),names[index]) for index in names)
        return dict(zip(range(list_length),names))

    def _yield_list_diffs(self,list1,list2,names):
        for index, (item1,item2) in enumerate(zip(list1,list2)):
            name = '(%s)' % names[index] if index in names else ''
            try:
                assert_equals(item1,item2,msg='Index %d%s' %(index,name))
            except AssertionError, err:
                yield unic(err)

    def list_should_contain_sub_list(self,list1,list2,msg=None,values=True):
        """
        fails if not all the elements in list2, are found in list1
        the order of values and the number of values are not taken into account
        see the use of 'msg' and 'values' from the 'Lists should be equal keyword'
        """
        diffs = ', '.join(unic(item) for item in list2 if item not in list1)
        default = 'Folling values were not found form first list:'+ diffs
        _verify_condition(diffs == '',default,msg,values)

    def log_list(self,list_,level='INFO'):
        """
        logs the length and contents of the 'list' using given 'level'.
        Valid levels aer TRACE,DEBUG,INFO(defalt), and WARN
        if you only want to the length,use keyword 'Get length' from the BuiltIn library.
        """
        logger.write('\n'.join(self._log_list(list_)),level)

    def _log_list(self,list_):
        if not list_:
            yield 'List is empty'
        elif len(list_) == 1:
            yield 'List has one item:\n%s' %list_[0]
        else:
            yield 'List length is %d and it contains folling items:'%len(list_)
            for index,item in enumerate(list_):
                yield '%s:%s' %(index,item)

    def _index_to_int(self,index,empty_to_zero=False):
        if empty_to_zero and not index:
            return 0
        try:
            return int(index)
        except ValueError:
            raise ValueError("cannot convert index '%s' to an integer" %index)

    def _index_error(self,list_,index):
        raise IndexError('Given index %s is out of the range 0-%d'
                         %(index,len(list_)-1))

class Dictionary:
    def create_dictionary(self,*key_value_pairs,**items):
        """
        creates and returns a dictionary based on given items.
        giving items as 'key_value_pairs' means giving keys and values
        as separate arguments
        """
        if len(key_value_pairs)%2 !=0:
            raise ValueError("create dictionary failed. there should be"
                             "an even number of key-value-pairs")
        return self.set_to_dictionary({},*key_value_pairs,**items)

    def set_to_dictionary(self,dictionary,*key_value_pairs,**items):
        """
        adds the given 'key_value_pairs' and 'items' to the 'dictionary'
        see 'create dictionary' for information about giving items.
        example:
        |set to dictionary | ${d1} | key |value
        =>
        -${d1} ={'a':1,'key':'value'}
        """
        if len(key_value_pairs) %2 !=0:
            raise ValueError("Adding data to a dictionary failed.There"
                             "should be an even number of key-value-pairs.")
        for i in range(0,len(key_value_pairs),2):
            dictionary[key_value_pairs[i]] = key_value_pairs[i+1]
        dictionary.update(items)
        return dictionary
    def remove_from_dictionary(self,dictionary,*keys):
        """
        removes the given 'keys' from the 'dictionary' if the given 'key' cannot be found from 'dictionary',
        it is ignored
        example:
        |Remove from Dictionary | ${d3} |b|x|y
        =>
        -${d3} = {'a':1,'c':3}
        """
        for key in keys:
            if key in dictionary:
                value = dictionary.pop(key)
                logger.info("removed item with key '%s' and value '%s'" %(key,value))
            else:
                logger.info("Key '%s' not found" %(key))

    def keep_in_dictionary(self,dictionary,*keys):
        """
        keeps the given keys in the dictionary and removes all other
        if the given 'key' cannot found from the 'dictionary',it is ignored
        """
        remove_keys = [k for k in dictionary if k not in keys]
        self.remove_from_dictionary(dictionary,*remove_keys)

    def copy_dictionary(self,dictionary):
        """
        returns a copy of the given dictionary.
        the given dictionary is never altered by this keyword
        """
        return dictionary.copy()

    def get_dictionary_keys(self,dictionary):
        """
        returns 'keys' of the given 'dictionary'
        'keys' are returned in sorted order .the given 'dictionary' is never
        altered by this keyword

        Example:
            |${keys} = | get dictionary keys |${d3}
            =>
            -${keys} = ['a','b','c']
        """
        return sorted(dictionary)

    def get_dictionary_values(self,dictionary):
        """
        returns values of the given dictionary
        values are returned sorted according to keys. the given dictionary is never altered by
        this keyword
        example:
        |${keys} | get dictionary keys |${d3}
        =>
        -${keys} = ['a','b','c']
        """
        return [dictionary[k] for k in self.get_dictionary_keys(dictionary)]

    def get_dictionary_items(self,dictionary):
        """
        returns items sordted by keys .the given 'dictionary' is not altered by this keyword
        Example:
            |${items}= |get dictionary items |${d3}|
            =>
            -${items} = ['a',1,'b',2,'c',3]
        """
        ret = []
        for key in self.get_dictionary_keys(dictionary):
            ret.extend((key,dictionary[key]))
        return ret

    def get_from_dictionary(self,dictionary,key):
        """
        returns a value from the given 'dictionary' based on the given 'key'
        if the given 'key' cannot be found from the 'dictionary' ,this keyword fails
        the given 'key' cannot be found from the 'dictionary' ,this keyword fails
        the given dictionary is never altered by this keyword

        """
        try:
            return dictionary[key]
        except  KeyError:
            raise RuntimeError("Dictionary does not contain key '%s'" %key)

    def dictionary_should_contain_key(self,dictionary,key,msg=None):
        """
        fails if 'key' is not found from 'dicionary'
        see 'List Should Contain Value' for an expalanation of msg
        the given dictionary is never altered by this keyword
        """
        default = "Dictionary does not contain key'%s'" %key
        _verify_condition(dictionary.has_key(key),default,msg)

    def dictionary_should_not_contain_key(self,dictionary,key,msg=None):
        """
        fails if 'key' is found from dictionary
        see 'List should contain value' for an expalnation of 'msg'
        the given dictionary is never altered by this keyword
        """
        default = "Dictionary contains key '%s'" %key
        _verify_condition(not dictionary.has_key(key),default,msg)

    def dictionary_should_contain_item(self,dictionary,key,value,msg=None):
        """
        An item of 'key' /'value' must b e found in a 'dictionary'.
        value is converted to unicode for comparison
        see 'lists should be equal' for an explanation of 'msg'.  The given dictionary
        is never altered by this keyword

        """
        self.dictionary_should_contain_key(dictionary,key,msg)
        actual,expected = unicode(dictionary[key]),unicode(value)
        default ="Value of dictionary key '%s' does not match '%s'!='%s'" %(key,actual,expected)
        _verify_condition(actual == expected,default,msg)

    def dictionary_shoule_contain_value(self,dictionary,value,msg=None):
        """
         fails if 'value' is not found from dictionary, see 'list should contain value' for explanation of
         'msg' the given dictionary is never altered by this keyword.
        """
        default = "Dictionary does not contain value '%s'"%value
        _verify_condition(value in dictionary.values(),default,msg)

    def dictionary_should_not_contain_value(self,dictionary,value,msg=None):
        """
        fails if value is found from 'dictionary' see 'List'
        """
        default = "Dictionary contains value '%s'" %value
        _verify_condition(not value in dictionary.values(),default,msg)

    def dictionaries_should_be_equal(self,dict1,dict2,msg=None,values=True):
        """
        fails if the given dictionaries are not equal.
        First the equality of dictionaries keys is checked and after that all the key value pairs.If
        there are differences between the values ,those are listed in the error message.
        see 'List Should Be Equal' for an explanation of msg. the given dictionaries are never altered by this keyword
        """
        keys = self._keys_should_be_equal(dict1,dict2,msg,values)
        self._key_values_should_be_equal(keys,dict1,dict2,msg,values)

    def dictionary_should_contain_sub_dictionary(self,dict1,dict2,msg=None,values=True):
        """
        Fails unless all items in 'dictionaries'
        """
        keys = self.get_dictionary_keys(dict2)
        diffs = [unic(k) for k in keys if k not in dict1]
        default = "Following keys missing from first dictionary:%s" \
                 %','.join(diffs)
        _verify_condition(diffs == [],default,msg,values)
        self._key_values_should_be_equal(keys,dict1,dict2,msg,values)

    def log_dictionary(self,dictionary,level='INFO'):
        logger.write('\n'.join(self.log_dictionary(dictionary)),level)


    def _log_dictionary(self,dictionary):
        if not dictionary:
            yield 'Dictionary is empty '
        elif len(dictionary) ==1:
            yield 'Dictionary has one item'
        else:
            yield 'Dictionary size is %d and it contains following items:'%len(dictionary)
        for key in self.get_dictionary_keys(dictionary):
            yield '%s: %s' %(key,dictionary[key])

    def _keys_should_be_equal(self,dict1,dict2,msg,values):
        keys1 = self.get_dictionary_keys(dict1)
        keys2 = self.get_dictionary_keys(dict2)
        miss1 = [unic(k) for k in keys2 if k not in dict1]
        miss2 = [unic(k) for k in keys1 if k not in dict2]
        error = []
        if miss1:
            error += ['Following keys missing from first dictionary: %s'
                      % ','.join(miss1)]
        if miss2:
            error += ['Folling keys missing from second dictionary: %s'
                    % ','.join(miss2)]
        _verify_condition(error == [], '\n'.join(error),msg,values)
        return keys1

    def _key_values_should_be_equal(self,keys,dict1,dict2,msg,values):
        diffs = list(self._yield_dict_diffs(keys,dict1,dict2))
        default = 'Following keys have diffrernt values:\n'+ '\n'.join(diffs)
        _verify_condition(diffs ==[],default,msg,values)

    def _yield_dict_diffs(self,keys,dict1,dict2):
        for key in keys:
            try:
                assert_equals(dict1[key],dict2[key],msg='Key %s' %(key,))
            except AssertionError,err:
                yield unic(err)


class  Collection(_List, _Dictionary):
    """
    A test library providing keywords for handling lists and dictionaries.
    'collections' is Robot Framework's standard lists and idctionaries. this library
    has keywords ,for example,for modifying and getting values from lists and dictionaries and for verifying their
    contents
    folling keywords from the BuiltIn library can also be used with lists and dictionaries:


    """
    ROBOT_LIBRARY_SCOPE = 'GLOBAL'
    ROBOT_LIBRARY_VERSION = get_version()

def _verify_condition(condition,default_msg,given_msg,include_default=False):
    if not condition:
        if not given_msg:
            raise AssertionError(default_msg)
        if _include_default_message(include_default):
            raise AssertionError(given_msg +'\n'+default_msg)
        raise AssertionError(given_msg)

def _include_default_message(include):
    if isinstance(include,basestring):
        return include.lower() not in  ['no values','false']
    return bool(include)


























