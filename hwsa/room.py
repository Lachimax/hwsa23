import os

from hwsa.attendee import Attendee
from hwsa.utils import debug_print, load_params


class Room:
    def __init__(self, **kwargs):
        self.roommates = []
        self.n_max = 2
        self.id = None
        self.event = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return f"Room {self.id}"

    def __hash__(self):
        return hash(str(self))

    def update_manual(self):
        debug_print(f"Attempting manual update for {self}...")
        if self.event is not None:
            manual_path = os.path.join(self.event.output, "rooms_manual", self.filename() + ".yaml")
            if os.path.isfile(manual_path):
                print(f"Manually setting roommates for {self}")
                yml = load_params(manual_path)
                roommates = yml["roommates"]
                for p_id in roommates:
                    if p_id in self.event.attendees_dict:
                        p = self.event.attendees_dict[p_id]
                        self.add_roommate(p, override_suitable=True)

    def print_roommates(self):
        for p in self.roommates:
            print("\t", p.room_str())

    def list_roommates(self):
        return list(
            map(
                lambda p: str(p),
                self.roommates
            )
        )

    def add_roommate(self, person: 'Attendee', override_suitable=False):
        # Check if the room is already full
        debug_print(f"\t Checking {self}")
        debug_print(f"\t\tChecking room capacity: {self.n_roommates()} / {self.n_max}", not self.full())
        if not self.full():
            # Check if it's a real person (None or nan will get passed here sometimes, and we don't want those piling up)
            debug_print("\t\tChecking if real person:", isinstance(person, Attendee))
            if isinstance(person, Attendee):
                # Check if room is compatible with person's preferences:
                debug_print("\t\tChecking if room is suitable:", self.suitable_for(person))
                if override_suitable or self.suitable_for(person):
                    person.room = self
                    # Check for duplicates and add the person to this list if not present
                    debug_print("\t\tChecking that person is not already in this room:", person not in self.roommates)
                    if person not in self.roommates:
                        self.roommates.append(person)
                        debug_print(f"\tAdding {person.room_str()} to {self} ({self.single_gender()})")

    def n_roommates(self):
        return len(self.roommates)

    def full(self):
        return self.n_roommates() >= self.n_max

    def empty(self):
        return self.n_roommates() == 0

    def overfull(self):
        """
        Shouldn't ever return True, but here for debug purposes.
        :return:
        """
        return self.n_roommates() > self.n_max

    def single_gender(self):
        if self.n_roommates() == 0:
            return True
        gender = self.roommates[0].gender
        for person in self.roommates:
            if person.gender != gender:
                return False
        return gender

    def suitable_for(self, person: 'Attendee'):
        for roommate in self.roommates:
            debug_print(f"\t\t\t Checking compatibility with {roommate.room_str()}:",
                        compatible_roommates(person, roommate))
            if not compatible_roommates(person, roommate):
                return False
        return True

    def to_yaml(self):
        a_dict = self.__dict__.copy()
        for key, value in a_dict.items():
            if not isinstance(value, (float, int, str)):
                value = str(value)
                a_dict[key] = value
        a_dict["roommates"] = list(map(lambda p: str(p), self.roommates))
        return a_dict

    def filename(self):
        return str(self).replace(" ", "_")


def compatible_roommates(person_1: 'Attendee', person_2: 'Attendee'):
    return person_1 is not person_2 and person_1.prefer_roommate(person_2) and person_2.prefer_roommate(
        person_1)
