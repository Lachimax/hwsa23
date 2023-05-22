import pandas as pd

from hwsa.attendee import Attendee
from hwsa.room import Room


class Event:
    def __init__(self, **kwargs):
        self.n_rooms = 40
        self.max_per_room = 2
        self.attendees = []
        self.attendees_dict = {}
        self.rooms = []
        for key, value in kwargs.items():
            setattr(self, key, value)

        for i in range(self.n_rooms):
            self.rooms.append(
                Room(
                    id=i + 1,
                    n_max=self.max_per_room
                )
            )

    def add_attendee(self, person: Attendee):
        self.attendees.append(person)
        self.attendees_dict[str(person)] = person

    def find_name(self, name: str):
        for person in self.attendees:
            if person.loose_match(name):
                return person
        return None

    def _generate_pairs(self):
        pairs = []
        for person in self.attendees:
            for person_other in self.attendees:
                if compatible_roommates(person, person_other):
                    pair = (person, person_other)
                    pair_reverse = (person_other, person)
                    if pair not in pairs and pair_reverse not in pairs:
                        pairs.append(pair)
        return pairs

    def _find_nominated(self):
        for person in self.attendees:
            if person.has_nominee():
                person.roommate_nominee_obj = self.find_name(person.roommate_nominee)

    def next_room(self):
        self.rooms.sort(key=lambda rm: rm.n_roomates())
        return self.rooms[0]

    def _assign_nominated(self):
        # Use string nominee to assign Attendee object
        self._find_nominated()
        for person in self.attendees:
            if person.has_room():
                room = person.room
            else:
                room = self.next_room()
            nominee = person.roommate_nominee_obj
            # Check if enough roommates have already been assigned to the person's room,
            # and if they have nominated each other
            if not room.full() and nominees_match(person, nominee):
                room.add_roommate(nominee)

    def allocate_roommates(self):
        # Even if someone has multiple preferences, have it prefer their own gender

        pairs = self._generate_pairs()
        print("\nThe following compatible pairs were generated:")
        for pair in pairs:
            print(f"{pair[0]}, {pair[1]}")

        # First pass: find people who have nominated each other as roommates and assign them to the same room.
        print("\n The following rooms were assigned based on nominees:")
        self._assign_nominated()
        nominated = list(
            filter(
                lambda p: p.n_roommates() > 1,
                self.attendees
            )
        )
        for p in nominated:
            print(str(p), ",", str(p.roommate))

        # Second pass: assign roomless people based on gender preferences
        roomless = list(
            filter(
                lambda p: not p.has_room(),
                self.attendees
            )
        )

        print("\nThe following attendees did not list their own gender in the 'comfortable with' field:")
        prefs_not_own = list(
            filter(
                lambda p: p.gender not in p.room_preferences and "No preference" not in p.room_preferences,
                self.attendees
            )
        )
        for p in prefs_not_own:
            print(str(p))

        print("\nThe following attendees have nominated roommates but have not been assigned them.")
        nominee_failed = list(
            filter(
                lambda p: p.has_nominee and not p.roommate is p.roommate_nominee,
                self.attendees
            )
        )
        for p in nominee_failed:
            print(str(p), f"(nominated {p.roommate_nominee}, assigned {p.roommate})")

        rooms_full = list(
            filter(
                lambda r: r.full(),
                self.rooms
            )
        )
        rooms_overfull = list(
            filter(
                lambda r: r.overfull(),
                rooms_full
            )
        )
        print("\n Number of full rooms:")
        print(len(rooms_full))
        print("Number of rooms above capacity:")
        print(len(rooms_overfull))

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

def compatible_roommates(person_1: 'Attendee', person_2: 'Attendee'):
    return person_1 is not person_2 and person_1.prefer_roommate(person_2) and person_2.prefer_roommate(person_1)


def nominees_match(person_1: 'Attendee', person_2: 'Attendee'):
    # Sometimes Nones or nans will make it in here, for example if a person has no nominee, so we return False
    if not isinstance(person_1, Attendee) or not isinstance(person_2, Attendee):
        return False
    # Otherwise, we check if the nominees of the pair are each other
    return person_1.roommate_nominee_obj is person_2 and person_2.roommate_nominee_obj is person_1

