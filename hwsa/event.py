import pandas as pd

from hwsa.attendee import Attendee


class Event:
    def __init__(self, **kwargs):
        self.n_rooms = 40
        self.attendees = []
        for key, value in kwargs.items():
            setattr(self, key, value)

    def add_attendee(self, person: Attendee):
        self.attendees.append(person)

    def _generate_pairs(self):
        pass

    def allocate_roommates(self):
        # Even if someone has multiple preferences, have it prefer their own gender
        pass

    @classmethod
    def from_mq_xl(cls, path: str):
        if not path.endswith(".xlsx"):
            path += ".xlsx"
        xl = pd.read_excel(path)

        true_names = []
        for name_1 in xl:
            name_2 = xl[name_1][0]
            if "Value - Value" in name_2:
                true_names.append(name_1)
            else:
                true_names.append(name_2)

        xl_mod = xl.drop(0)
        xl_mod.columns = true_names

        xl_mod.to_csv(
            path.replace(".xlsx", ".csv")
        )

        event = Event()
        for row in xl_mod.iloc:
            person = Attendee.from_mq_xl_row(row=row)
            event.add_attendee(person=person)

        return event
