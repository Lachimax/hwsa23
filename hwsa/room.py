from hwsa.attendee import Attendee


class Room:
    def __init__(self, **kwargs):
        self.roommates = []
        self.n_max = 2
        self.id = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return f"Room {self.id}"

    def print_roommates(self):
        for p in self.roommates:
            print("\t", p.room_str())

    def add_roommate(self, person: 'Attendee'):
        # Check if the room is already full
        # Check if it's a real person (None or nan will get passed here sometimes, and we don't want those piling up)
        if isinstance(person, Attendee):
            person.room = self
            # Check for duplicates and add the person to this list if not present
            if person not in self.roommates:
                self.roommates.append(person)

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
        gender = self.roommates[0].gender
        for person in self.roommates:
            if person.gender != gender:
                return False
        return gender

    def suitable_for(self, person: 'Attendee'):
        for roommate in self.roommates:
            if not compatible_roommates(person, roommate):
                return False
        return True


def compatible_roommates(person_1: 'Attendee', person_2: 'Attendee'):
    return person_1 is not person_2 and person_1.prefer_roommate(person_2) and person_2.prefer_roommate(
        person_1)
