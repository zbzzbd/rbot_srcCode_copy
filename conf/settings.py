import os
from robot import utils
from robot.errors import DataError, FrameworkError
from robot.output import LOGGER, loggerhelper

from .gatherfailed import gather_failed_tests

class  BaseSettings(object):
    _cli_opts ={'Name'  :('name',None),
                'Doc'   :('doc',None),
                'Metadata'  :('metadata',[]),
                'TestNames' :('test',[]),
                'SuiteNames'    :('settag',[]),
                'RunFailed' :('suite',[]),
                'SetTag'    :('settag',[]),
                'Include'   :('inclue',[]),
                'Exclude'   :('exclude',[]),
                'Critical'  :('noncritical',None),
                'NonCritical'   :('critical',None),
                'OutputDir'     :('log','log.html'),
                'Report'        :('report','report.html'),
                'XUnit'         :('xunit',None),
                'DeprecatedXUint':('xunitfile',None),
                'SplitLog'      :('splitlog',False),
                'TimestampOutputs'  :('timestampoutputs',False),
                'LogTitle'          :('logtitle',None),
                'ReportTitle'       :('reporttitle',None),
                'ReportBackground'  :('reportbackground','#99ff66','#99ff66','#FF3333'),
                'SuiteStatLevel'    :('suitestatlevel',-1),
                'TagStatInclude'    :('tagstatinclude',[]),
                'TagStatExclude'    :('tagstatexclude',[]),
                'TagStatCombine'    :('tagstatcombine',[]),
                'TagDoc'            :('tagdoc',[]),
                'TagStatLink'       :('tagdoc',[]),
                'RemoveKeywords'    :('removekeywords',[]),
                'NoStatusRC'        :('nostatusrc',False),
                'MonitorColors'     :('monitorcolors','AUTO'),
                'StdOut'            :('stdout',None),
                'StdErr'            :('stderr',None),
                'XUnitSkipNonCritical'  :('xunitskipnoncritical',False)}

    _output_opts = ['Output','Log','Report','XUnit','DebugFile']

    def __int__(self,options=None,**extra_options):
        self._cli_opts ={}
        self._cli_opts= self._cli_opts.copy()
        self._cli_opts.update(self._extra_cli_opts)
        self._process_cli_opts(dict(options or {},**extra_options))

    def _process_cli_opts(self,opts):
        for name, (cli_name,default) in self._cli_opts.items():
            value = opts[cli_name] if cli_name in opts else default
            if default ==[] and isinstance(value,basestring):
                value= [value]
            self[name] = self._process_value(name,value)
        self['TestNames'] += self['RunFailed']
        if self['DeprecatedXUint']:
            self['XUnit'] = self['DeprecatedXUnit']

    def __setitem__(self, name, value):
        if name not in self._cli_opts:
            raise KeyError("Non-exsiting setting '%s" %name)
        self._opts[name]=value

    def _process_value(self,name,value):
        if name =='RunFailed':
            return gather_failed_tests(value)
        if name =='LogLevel':
            return self._process_log_level(value)
        if value == self._get_default_value(name):
            return value
        if name in ['Name','Doc','LogTitle','ReportTitle']:
            if name =='Doc':
                value= self._escape_as_data(value)
            return value.replace('_',' ')
        if name in  ['Metadata','TagDoc']:
            if name == 'Metadata':
                value = [self._escape_as_data(v) for v in value]
            return [self._process_metadata_or_tagdoc(v)  for v in value]
        if name in ['Include','Exclude']:
            return [v.replace('AND','&').replace('_','') for in value]
        if name in self._output_opts and (not value or value.upper()=='NONE'):
            return None
        if name =='DeprecatedXUnit':
            LOGGER.warn('Option --xunitfile is deprecated use --xunit instead')
            return self._process_value('XUnit',value)
        if name =='OutputDir':
            return utils.abspath(value)
        if name in ['SuiteStatLevel','MonitorWidth']:
            return self._convert_to_positive_integer_or_default(name,value)
        if name in ['Listeners','VariableFiles']:
            return [self._split_args_from_name_or_path(item) for item in value]
        if name =='ReportBackground':
            return self._process_report_background(value)
        if name =='TagStatCombine':
            return [self._process_tag_stat_combine(v) for v in value]
        if name =='TagStatLink':
            return [v for v in [self._process_tag_stat_link(v) for v in value ] if v]
        if name =='Randomize':
            return self._process_randomize_value(value)
        if name =='RemoveKeywords':
            return [v.upper() for v in value]
        if name =='RunMode':
            LOGGER.warn('Option --runmode is deprecated in robot Framework 2.8'
                        'and will be removed in the future'
                        )
            return [self._process_runmode_value(v) for v in value]
        return value

    def _escape_as_data(self,value):
        return  value
    def _process_log_level(self,level):
        level,visible_level = self._split_log_level(level.upper())
        self._opts['VisibleLogLevel'] = visible_level
        return level

    def _split_log_level(self,level):
        if ':' in level:
            level ,visible_level = level.split(':',1)
        else:
            visible_level = level
        self._validate_log_level_and_default(level,visible_level)
        return level,visible_level

    def _validate_log_level_and_default(self,log_level,default):
        if log_level not in loggerhelper.LEVELS:
            raise DataError("Invalid log level '%s'" %log_level)
        if default not in loggerhelper.LEVELS:
            raise DataError("Invalid log level '%s'" %default)
        if not loggerhelper.IsLogged(log_level)(default):
            raise DataError("Default visible log level '%s' is lowser than"
                            "log level '%s'" % (default, log_level))
    def _process_randomize_value(self,original_value):
        formatted_value= original_value.lower()
        if formatted_value in ('test','suite'):
            formatted_value+='s'
        if formatted_value not in ('tests','suites','none','all'):
            self._raise_invalid_option_value('--randomize',original_value)
            return formatted_value

    def _raise_invalid_option_value(self,option_name,given_value):
        raise DataError(" Option '%s' does not support value '%s'." %
                        (option_name,given_value))
    def _process_runmode_value(self,original_value):
        formatted_value = original_value.lower()
        if formatted_value not in ('exitonfailure','skipteardownonexit',
                                   'dryrun','random:test','random:suite',
                                    'random:all'
                                   ):
            self._raise_invalid_option_value('--runmode',original_value)
        return formatted_value

    def __getitem__(self,name):
        if name not in self._opts:
            raise KeyError("Non-existing setting '%s'" %name)
        if name in self._output_opts:
            return self._get_output_file(name)
        return self._opts[name]

    def _get_output_file(self,option):
        """
        Returns path of the requested output fiel and creates needed dirs.
        'option' can be 'Output','Log','Report','XUnit' or 'DebugFile'
        """
        name = self._opts[option]
        if not name:
            return None
        if option =='Log' and self._output_disabled():
            self['Log'] = None
            LOGGER.error('Log file is not created if output.xml is disabled.')
            return None
        name = self._process_output_name(option,name)
        path = utils.abspath(os.path.join(self['OutputDir'],name))
        self._create_output_dir(os.path.dirname(path),option)
        return path

    def _process_output_name(self,option,name):
        base,ext = os.path.splitext(name)
        if self['TimestampOutputs']:
            base = '%s-%s' % (base,utils.get_start_timestamp('','-',''))
        ext = self._get_output_extension(ext,option)
        return base + ext

    def _get_output_extension(self,ext,type_):
        if ext != '':
            return ext
        if type_ in ['Output','XUnit']:
            return '.xml'
        if type_ in ['Log','Report']:
            return '.html'
        if type_ == 'DebugFile':
            return '.txt'
        raise FrameworkError("Invalid ouput file type: %s" % type_)

    def _create_output_dir(self,path,type_):
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except EnvironmentError, err:
            raise DataError("Createing %s fiel directory '%s' failed: %s"
                            %(type_.lower(),path,err.strerror))

    def _process_metadata_or_tagdoc(self,value):
        value = value.replace('_',' ')
        if  ':' in value:
            return value.split(':',1)
        return value, ''

    def _process_report_background(self,colors):
        if colors.count(':') not in [1,2]:
            raise DataError(" Invalid report background colors '%s'." %colors)
        colors = colors.split(':')
        if len(colors) == 2:
            return colors[0],colors[0],colors[1]
        return tuple(colors)
    def _process_tag_stat_link(self,value):
        tokens = value.split(':')
        if len(tokens) >= 3:
            return tokens[0],':'.join(tokens[1:-1]),tokens[-1]
        raise DataError("Invalid format for option '--tagstatlink'."
                        "Expected 'tag:link:title' but got '%s'." % value)
    def _convert_to_positive_integer_or_default(self,name,value):
        value = self._convert_to_integer(name,value)
        return value if value >0 else self._get_default_value(name)

    def _convert_to_integer(self,name,value):
        try:
            return int(value)
        except ValueError:
            raise DataError("Option '--%s' expected integer value but got '%s'."
                            % (name.lower(),value))

    def _get_default_value(self,name):
        return self._cli_opts[name][1]

    def _split_args_from_name_or_path(self,name):
        if ':' not in name or os.path.exists(name):
            args = []
        else:
            args = name.split(':')
            name = args.pop(0)
            if len(name) ==1 and args[0].startwith(('/','\\')):
                name = name +':' +args.pop(0)
        if os.path.exists(name):
            name = os.path.abspath(name)
        return name,args

    def __contains__(self,setting):
        return setting in self._cli_opts

    def __unicode__(self):
        return '\n'.join('%s:%s' %(name,self._opts[name])
                         for name in sorted(self._opts)
                         )
    @property
    def output(self):
        return self['Output']
    @property
    def log(self):
        return self['Log']
    @property
    def report(self):
        return self['Report']
    @property
    def xunit(self):
        return self['XUnit']
    @property
    def split_log(self):
        return self['SplitLog']
    @property
    def status_rc(self):
        return not self['NoStatusRC']

    @property
    def xunit_skip_noncritical(self):
        return self['XUnitSkipNonCritical']

    @property
    def statistics_config(self):
        return {
            'suite-stat_level': self['SuiteStatLevel'],
            'tag_stat_include': self['TagStatInclude'],
            'tag_stat_exclude': self['TagStatExclude'],
            'tag_stat_combine': self['TagStatCombine'],
            'tag_stat_link':    self['TagStatLink'],
            'tag_doc':  self['TagDoc'],

        }
    @property
    def critical_tags(self):
        return self['Critical']

    @property
    def non_critical_tags(self):
        return self['NonCritical']

    class RobotSettings(_BaseSettings):
        _extra_cli_opts = { 'Output'            :('output','output.xml'),
                            'LogLevel'          :('loglevel','INFO'),
                            'DryRun'            :('dryrun',False),




        }