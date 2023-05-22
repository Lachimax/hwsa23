import os

import numpy as np
import pandas as pd

from hwsa.attendee import Attendee
from hwsa.room import Room
import hwsa.utils as u


class Event:
    def __init__(self, **kwargs):
        self.output = "/home/"
        self.n_rooms = 40
        self.max_per_room = 4
        self.min_per_room = None
        self.attendees = []
        self.attendees_dict = {}
        self.rooms = []
        self.diets = {}
        self.genders = {}
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
        self.min_per_room = int(np.ceil(len(self.attendees) / self.n_rooms))

    def print_attendees(self, people: list = None, sort: bool = False):
        if people is None:
            people = self.attendees
        print("Attendees:")
        if sort:
            people.sort(key=lambda a: a.name_family)
        for person in people:
            print("\t", person, person.room, "Needs room:", person.needs_room())

    def find_name(self, name: str):
        for person in self.attendees:
            if person.loose_match(name):
                return person
        return None

    # def _generate_pairs(self):
    #     pairs = []
    #     for person in self.attendees:
    #         for person_other in self.attendees:
    #             if compatible_roommates(person, person_other):
    #                 pair = (person, person_other)
    #                 pair_reverse = (person_other, person)
    #                 if pair not in pairs and pair_reverse not in pairs:
    #                     pairs.append(pair)
    #     return pairs

    def _find_nominated(self):
        for person in self.attendees:
            if person.has_nominee():
                person.roommate_nominee_obj = self.find_name(person.roommate_nominee)

    def next_room(self):
        self.rooms.sort(key=lambda rm: rm.n_roommates())
        return self.rooms[0]

    def rooms_full(self):
        return list(
            filter(
                lambda r: r.full(),
                self.rooms
            )
        )

    def all_rooms_full(self):
        full = self.rooms_full()
        return len(full) >= self.n_rooms

    def get_roomless(self, people: list = None):
        if people is None:
            people = self.attendees
        return list(
            filter(
                lambda p: not p.has_room() and p.needs_room(),
                people
            )
        )

    def assign_nominated(self):
        # Use string nominee to assign Attendee object
        self._find_nominated()
        rooms = []
        roomless = self.get_roomless()
        for person in roomless:
            if person.has_room():
                room = person.room
            else:
                room = self.next_room()
            nominee = person.roommate_nominee_obj
            # Check if enough roommates have already been assigned to the person's room,
            # and if they have nominated each other
            if not room.full() and nominees_match(person, nominee):
                room.add_roommate(nominee)
            if room not in rooms:
                rooms.append(room)
        return rooms

    def add_gender(self, person: Attendee):
        if person.gender not in self.genders:
            self.genders[person.gender] = []
        self.genders[person.gender].append(person)

    def get_genders(self):
        for p in self.attendees:
            self.add_gender(p)
        return self.genders

    def assign_to_room(self, room, people: list):
        people = people.copy()
        while people and room.n_roommates() < self.min_per_room:
            room.add_roommate(people.pop())

    def assign_by_gender(self):
        self.get_genders()
        # First put the minimum people in empty rooms
        rooms = []
        for gender, people in self.genders.items():
            roomless = self.get_roomless(people)
            roomless.sort(key=lambda a: a.n_preferences())
            while roomless and not self.all_rooms_full():
                room = self.next_room()
                self.assign_to_room(room=room, people=roomless)
                roomless = self.get_roomless(people)
                if room not in rooms:
                    rooms.append(room)
        # Then, if there are still people roomless, assign them to rooms matching their gender
        roomless = self.get_roomless()
        for person in roomless:
            rooms_this = self.rooms.copy()
            rooms_this = list(filter(lambda r: r.single_gender() == person.gender, rooms_this))
            if rooms_this:
                room = rooms_this[0]
                room.add_roommate(person)
                if room not in rooms:
                    rooms.append(room)
        return rooms

    def assign_by_preference(self):
        roomless = self.get_roomless()
        rooms = []
        for person in roomless:
            rooms_this = self.rooms.copy()
            rooms_this = list(filter(lambda r: r.suitable_for(person), rooms_this))
            if rooms_this:
                room = rooms_this[0]
                room.add_roommate(person)
                if room not in rooms:
                    rooms.append(room)
        return rooms

    def allocate_roommates(self):

        # First pass: find people who have nominated each other as roommates and assign them to the same room.
        print("\nThe following rooms were assigned based on nominees:")
        nominated = self.assign_nominated()
        for r in nominated:
            print(f"{r}:")
            r.print_roommates()

        print("\nThe following attendees have nominated roommates but have not been assigned them:")
        nominee_failed = list(
            filter(
                lambda p: p.has_nominee() and p.roommate_nominee_obj not in p.roommates(),
                self.attendees
            )
        )
        for p in nominee_failed:
            nominee = self.find_name(p.roommate_nominee)
            add_str = ""
            if nominee is None:
                add_str = "; attendee not found"
            print("\t", str(p), f"(nominated {p.roommate_nominee}{add_str})")

        # Second pass: assign roomless people based on gender
        # Note: Even if someone has multiple or no preferences, have it try to assign to same gender first
        # But prioritise people with specified preferences, the fewer the earlier

        print("\nThe following rooms were assigned based on attendee gender:")
        gendered = self.assign_by_gender()
        for r in gendered:
            print(f"{r}:")
            r.print_roommates()

        # Third pass: assign still-roomless people based on listed preferences

        print("\nThe following rooms were assigned based on gender PREFERENCE:")
        preferred = self.assign_by_preference()
        for r in preferred:
            print(f"{r}:")
            r.print_roommates()

        print("\nAll rooms:")
        self.rooms.sort(key=lambda r: r.id)
        for r in self.rooms:
            if not r.empty():
                print(r)
                r.print_roommates()

        print("\nThe following attendees did not list their own gender in the 'comfortable with' field:")
        prefs_not_own = list(
            filter(
                lambda p: p.gender not in p.room_preferences and p.room_preferences,
                self.attendees
            )
        )
        for p in prefs_not_own:
            print("\t", p.room_str())

        print("\nThe following attendees have not been assigned rooms:")
        roomless = self.get_roomless()
        for p in roomless:
            print("\t", p.room_str())

        print()
        self.print_attendees()

        # Some statistics
        rooms_full = self.rooms_full()
        rooms_overfull = list(
            filter(
                lambda r: r.overfull(),
                rooms_full
            )
        )
        print("\nNumber of full rooms:")
        print(len(rooms_full))
        print("Number of rooms above capacity:")
        print(len(rooms_overfull))
        print("Max per room:")
        print(self.max_per_room)
        print("Min per room:")
        print(self.min_per_room)

    def add_diet(self, person: Attendee):
        if person.has_diet():
            if person.diet not in self.diets:
                self.diets[person.diet] = []
            self.diets[person.diet].append(person)

    def get_diets(self):
        for p in self.attendees:
            self.add_diet(p)
        return self.diets

    def show_diets(self):
        self.get_diets()
        print("Dietary Requirements:")
        diets_str = {}
        diets_n = {}
        for diet, people in self.diets.items():
            diets_str[diet] = list(map(lambda p: str(p), people))
            diets_n[diet] = len(diets_str[diet])
            print(f"\t{diet}: {len(people)}")
            for p in people:
                print("\t\t", p)

        diets_write = {
            "People": diets_str,
            "Numbers": diets_n
        }
        u.save_params(file=os.path.join(self.output, "diet.yaml"), dictionary=diets_write)
        return diets_write

    @classmethod
    def from_mq_xl(cls, path: str, **kwargs):
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

        event = Event(**kwargs)
        for row in xl_mod.iloc:
            person = Attendee.from_mq_xl_row(row=row)
            event.add_attendee(person=person)

        return event


def nominees_match(person_1: 'Attendee', person_2: 'Attendee'):
    # Sometimes Nones or nans will make it in here, for example if a person has no nominee, so we return False
    if not isinstance(person_1, Attendee) or not isinstance(person_2, Attendee):
        return False
    # Otherwise, we check if the nominees of the pair are each other
    return person_1.roommate_nominee_obj is person_2 and person_2.roommate_nominee_obj is person_1
