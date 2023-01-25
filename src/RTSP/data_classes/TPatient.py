from myUtils.utils import priority_to_number
from dataclasses import dataclass

@dataclass
class TPatient():
    index: int
    treatmentID: str
    patID: str
    careplan: str
    priority: int    
    noSections: int
    admissionDay: int
    releaseDay: int
    dueDay: int
    duration: int
    TWMin: int
    TWMax: int

    @staticmethod
    def parsePatient(_index, _treatmentId, _patID, _careplan, _pri, _noSec, _admission, _realease, _dueDay, _dur, _twmin, _twmax) -> 'TPatient':
        if (isinstance(_pri, int) == False):
            if (_pri[0] == 'P'):  #
                _pri = priority_to_number(_pri)
            else:
                _pri = int(_pri)
        p = TPatient(int(_index),  _treatmentId, _patID, _careplan, int(_pri),
                     int(_noSec), int(_admission), int(_realease),int(_dueDay),int(_dur),int(_twmin),int(_twmax))
        return p

    def __str__(self):
        s = ''
        if(self.isPalliative()):
            s = s + 'P'
        else:
            s = s + 'C'
        s = s + str(self.index)
        return s

    def isPalliative(self):
        if(self.priority == 1 or self.priority == 2):
            return True
        return False

