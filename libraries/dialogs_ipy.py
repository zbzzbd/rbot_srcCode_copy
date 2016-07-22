class _AbstractWinformsDialog:

    def __int__(self):
        raise RuntimeError('This keyword is not yet implemented with IronPython')

class MessageDialog(_AbstractWinformsDialog):
    def __init__(self):
        _AbstractWinformsDialog.__init__(self)

class  InputDialog(_AbstractWinformsDialog):
    def __int__(self,message,default):
        _AbstractWinformsDialog.__init__(self)

class SelectionDialog(_AbstractWinformsDialog):
    def __init__(self,message,options):
        _AbstractWinformsDialog.__init__(self)


class  PassFailDialog(_AbstractWinformsDialog):

    def __init__(self,message):
        _AbstractWinformsDialog.__init__(self)

