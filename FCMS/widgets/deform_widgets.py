import html

from deform.widget import Widget, CheckboxWidget
from colander import null


class BootstrapSwitch(CheckboxWidget):
    template = "bootstrap.pt"