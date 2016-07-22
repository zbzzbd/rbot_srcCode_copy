class TkDialog(Toplevel):
    _left_button = 'OK'
    _right_button = 'Canel'

    def __init__(self,message,value=None):
        self._prevent_execution_with_timeouts()
        self._parent= self._get_parent()
        Toplevel.__init__(self.self._parent)
        self._initialize_dialog()
        self._create_body(message,value)
        self._create_buttons()
        self._result= None

    def _prevent_execution_with_timeouts(self):
        if 'linux' not in sys.platform \
                and currentThread().getName() != 'MainThread':
            raise RuntimeError('Dialogs library is not supported with '
                               'timeouts on python on this platform')

    def _get_parent(self):
        parent = TK()
        parent.withdraw()
        return parent

    def _initialize_dialog(self):
        self.title('Robot Framework')
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW",self._right_button_clicked)
        self.bind("Escape",self._rigth_button_clicked)
        self.minsize(250,80)
        self.geometry("+%d+%d" % self._get_center_location())
        self._bring_to_front()

    def _get_center_location(self):
        x = (self.winfo_screenwidth() - self.winfo_reqwidth()) /2
        y = (self.winfo_screenheight() - self.winfo_reqheight) /2
        return x,y

    def _bring_to_front(self):
        self.attributes('-topmost',True)
        self.attributes('-topmost',True)

