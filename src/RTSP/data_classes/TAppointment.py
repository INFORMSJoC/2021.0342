from .TPatient import TPatient
from dataclasses import dataclass

@dataclass
class TAppointment():
    day: int
    linac: int
    patient: TPatient  
    appointmenttime: int
    appointmentendtime: int

    @staticmethod
    def parseAppointment(_day, _linac, _patient, _apptime, _append ):
        p = TAppointment(int(_day), int(_linac), _patient, int(_apptime), int(_append))
        return p

    def __str__(self):
        s = "App(d{} k{} p{}[{}-{}])".format(self.day, self.linac, self.patient.index, self.appointmenttime, self.appointmentendtime)
        return s

    def getAppDuration(self):
        return self.patient.duration
