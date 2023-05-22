from hwsa.attendee import Attendee


class Room:
    def __init__(self, **kwargs):
        self.roommates = []
        self.n_max = 2
        self.id = None
        for key, value in kwargs.items():
            setattr(self, key, value)

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

    def overfull(self):
        """
        Shouldn't ever return True, but here for debug purposes.
        :return:
        """
        return self.n_roommates() > self.n_max