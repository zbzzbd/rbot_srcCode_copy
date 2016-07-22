class _SwingDialog(object):

    def __init__(self,pane):

        self._pane= pane
    def show(self):
        self._show_dialog(self._pane)

    def _show_dialog(self,pane):
        dialog = pane.createDialog(None,'Robot Framework')
        dialog.setModal(False)
        dialog.setAlwaysOnTop(True)
        dialog.show()
        while dialog.isShowing():
            time.sleep(0.2)
        dialog.dispose()

    def _get_value(self,pane):
        value = pane.getInputValue()
        return value if value != UNINTIVALIZED_VALUE else None


class WrappedOptionPane(JOptionPane):
    def getMaxCharactersPerLineCount(self):
        return 120

class  MessageDialog(_SwingDialog):
    def __int__(self,message):
        pane = WrappedOptionPane(message,PLAIN_MESSAGE,DEFAULT_OPTION)
        _SwingDialog.__inint__()

class InputDialog(_swingDialog):

    def __init__(self,message,default):
        pane = WrappedOptionPane(message,PLAIN_MESSAGE,OK_CANCEL_OPTION)
        pane.setWantsInput(True)
        pane.setInitialSelectionValue(default)
        _SwingDialog.__init__(self,pane)

class SelectionDialog(_SwingDialog):
    def __init__(self,message,options):
        pane = WrappedOptionPane(message,PLAIN_MESSAGE,OK_CANCEL_OPTION)
        pane.setWantsInput(True)
        pane.setSelectionValues(options)
        _SwingDialog.__init__(self,pane)

class PassFailDialog(_SwingDialog):
    def __init__(self,message):
        pane = WrappedOptionPane(message,PLAIN_MESSAGE,YES_NO_OPTION,None,['PASS','FAIL'],'PASS')
        _SwingDialog.__init__(self,pane)

    def _get_value(self,pane):
        return pane.getValue() == 'PASS'


