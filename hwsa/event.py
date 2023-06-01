import os

import numpy as np
import pandas as pd

from hwsa.attendee import Attendee
from hwsa.room import Room
import hwsa.utils as u


class Event:
    def __init__(self, **kwargs):
        self.output = "/home/"
        self.n_rooms = None
        self.max_per_room = None
        self.min_per_room = None
        self.attendees = []
        self.attendees_dict = {}
        self.room_numbers = []
        self.rooms = []
        self.diets = {}
        self.affiliations = {}
        self.genders = {}
        self.career_stages = {}
        self.accessibility = {}
        for key, value in kwargs.items():
            setattr(self, key, value)

        if not self.room_numbers:
            self.room_numbers = list(range(1, self.n_rooms + 1))

        if self.n_rooms is None:
            self.n_rooms = len(self.room_numbers)

        for n in self.room_numbers:
            self.rooms.append(
                Room(
                    id=n,
                    n_max=self.max_per_room
                )
            )

        self.log = []

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
            print(f"\t{person}, {person.room}, Needs room: {person.needs_room()}", )

    def find_name(self, name: str):
        if "(" in name and ")" in name:
            in_brackets = name[name.find("("):name.find(")") + 1]
            name.replace(in_brackets, "")
        while name.endswith(" "):
            name = name[:-1]

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
        with_nominees = []
        u.debug_print("All with successfully nominated roommates:")
        for person in self.attendees:
            if person.has_nominee():
                person.roommate_nominee_obj = self.find_name(person.roommate_nominee)
                if person.roommate_nominee_obj is not None:
                    with_nominees.append(person)
                    u.debug_print(f"\t{person.room_str()}")
        print()
        return with_nominees

    def next_room(self, rooms: list = None):
        if rooms is None:
            rooms = self.rooms.copy()
        rooms.sort(key=lambda rm: rm.n_roommates())
        return rooms.pop(0)

    def rooms_full(self):
        return list(
            filter(
                lambda r: r.full(),
                self.rooms
            )
        )

    def rooms_empty(self):
        return list(
            filter(
                lambda r: r.empty(),
                self.rooms
            )
        )

    def all_rooms_full(self):
        full = self.rooms_full()
        return len(full) >= self.n_rooms

    def get_roomless(self, people: list = None):
        if people is None:
            people = self.attendees
        people.sort(key=lambda a: a.n_preferences())
        return list(
            filter(
                lambda p: not p.has_room() and p.needs_room(),
                people
            )
        )

    def assign_nominated(self):
        # Use string nominee to assign Attendee object
        rooms = []
        people = self._find_nominated()
        print(f"\n{len(people)} attendees have nominated a roommate.")
        roomless = self.get_roomless(people)
        while roomless:
            person = roomless.pop(0)
            u.debug_print(f"{person.room_str()}: finding room...")
            u.debug_print(f"\tChecking if they have a room:")
            if person.has_room():
                room = person.room
                u.debug_print("\t\tTrue,", str(room))
            else:
                room = self.next_room()
                u.debug_print("\t\tFalse, getting next:", str(room))
            nominee = person.roommate_nominee_obj
            u.debug_print(f"\tFound nominated:", nominee.room_str())
            # Check if enough roommates have already been assigned to the person's room,
            # and if they have nominated each other
            u.debug_print(f"\tChecking if they have nominated eath other:", nominees_match(person, nominee))
            u.debug_print(f"\tChecking if person's room is full:", room.full())
            if not room.full() and nominees_match(person, nominee):
                room.add_roommate(person, override_suitable=True)
                room.add_roommate(nominee, override_suitable=True)
            if room not in rooms:
                rooms.append(room)
            if nominee in roomless:
                roomless.remove(nominee)
        return rooms

    def add_gender(self, person: Attendee):
        if person.gender not in self.genders:
            self.genders[person.gender] = []
        self.genders[person.gender].append(person)

    def get_genders(self):
        for p in self.attendees:
            self.add_gender(p)
        return self.genders

    def assign_to_room(self, room, people: list, make_copy: bool = False):
        if make_copy:
            people = people.copy()
        people.sort(key=lambda a: a.n_preferences(), reverse=True)
        while people and room.n_roommates() < self.min_per_room:
            room.add_roommate(people.pop())

    def assign_by_gender(self):
        self.get_genders()
        # First put the minimum people in empty rooms
        rooms = []
        u.debug_print("\nAssigning minimum number of people to empty rooms:")

        # The hullabaloo below is to alternate genders so that rooms get assigned fairly evenly between them
        roomless = self.get_roomless()
        i = 0
        gender_keys = tuple(self.genders.keys())
        while roomless and not self.all_rooms_full() and i < self.n_rooms:
            n = i % len(self.genders)
            gender = gender_keys[n]
            people_gender = self.get_roomless(self.genders[gender])
            room = self.next_room()
            # The function below also pops the person from the list, regardless of whether the allocation is successful.
            self.assign_to_room(room=room, people=people_gender)
            # roomless = self.get_roomless(people)
            if room not in rooms:
                rooms.append(room)
            i += 1
        u.debug_print("\nAssigning remaining people to gender-matching rooms:")
        # Then, if there are still people roomless, assign them to rooms matching their gender
        roomless = self.get_roomless()
        for person in roomless:
            room = self._assign_by_condition(
                person,
                lambda r: r.single_gender() == person.gender
            )
            if room not in rooms:
                rooms.append(room)
        return rooms

    def assign_by_preference(self):
        roomless = self.get_roomless()
        rooms = []
        for person in roomless:
            room = self._assign_by_condition(
                person,
                lambda r: r.suitable_for(person)
            )
            if room not in rooms:
                rooms.append(room)
        return rooms

    def _assign_by_condition(self, person, condition):
        attempts = 0
        rooms_this = self.rooms.copy()
        rooms_this = list(filter(condition, rooms_this))
        while not person.has_room() and rooms_this:
            room = self.next_room(rooms_this)
            u.debug_print(f"Searching for rooms for {person.room_str()}")
            u.debug_print("\t Rooms matching gender:", list((map(lambda r: r.id, rooms_this))))
            room.add_roommate(person)

            attempts += 1
            if not rooms_this:
                u.debug_print(f"Failed to find room for {person.room_str()}")
            return room

    def allocate_roommates(self):

        # First pass: find people who have nominated each other as roommates and assign them to the same room.
        nominated = self.assign_nominated()
        print("\nThe following rooms were assigned based on nominated roommates:")
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

        gendered = self.assign_by_gender()
        print("\nThe following rooms were assigned based on attendee gender:")
        if not gendered:
            print("None")
        for r in gendered:
            print(f"{r}:")
            r.print_roommates()

        # Third pass: assign still-roomless people based on listed preferences

        preferred = self.assign_by_preference()
        print("\nThe following rooms were assigned based on gender PREFERENCE:")
        if not preferred:
            print("None")
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
        if not prefs_not_own:
            print("None")
        for p in prefs_not_own:
            print("\t", p.room_str())

        print("\nThe following attendees have not been assigned rooms:")
        roomless = self.get_roomless()
        if not roomless:
            print("None")
        for p in roomless:
            print("\t", p.room_str())

        print()
        self.print_attendees(sort=True)

        # Some statistics
        rooms_full = self.rooms_full()
        rooms_overfull = list(
            filter(
                lambda r: r.overfull(),
                rooms_full
            )
        )
        print("\nNumber of attendees:")
        print(len(self.attendees))
        print("Number of full rooms:")
        print(len(rooms_full))
        print("Number of rooms above capacity:")
        print(len(rooms_overfull))
        print("Number of non-empty rooms:")
        print(self.n_rooms - len(self.rooms_empty()))
        print("Number of empty rooms:")
        print(len(self.rooms_empty()))
        print("Max per room:")
        print(self.max_per_room)
        print("Min per room:")
        print(self.min_per_room)

        print("\nNumber of people who have said that:")

        print("\tThey have nominated a roommate:", sum(map(lambda p: p.will_nominate == "now", self.attendees)))
        print("\tThey will nominate a roommate later:", sum(map(lambda p: p.will_nominate == "later", self.attendees)))
        print("\tThey need a roommate allocated:", sum(map(lambda p: p.will_nominate == "no", self.attendees)))

        self.write_rooms()
        self.write_attendee_table()

    def write_rooms(self):
        room_dict = {}
        for room in self.rooms:
            room_dict[room.id] = room.list_roommates()
        u.save_params(os.path.join(self.output, "rooms.yaml"), room_dict)

    def add_diet(self, person: Attendee):
        if person.has_diet():
            if person.diet not in self.diets:
                self.diets[person.diet] = []
            self.diets[person.diet].append(person)

    def add_affiliation(self, person: Attendee):
        if person.affiliation not in self.affiliations:
            self.affiliations[person.affiliation] = []
        self.affiliations[person.affiliation].append(person)

    def add_accessibility(self, person: Attendee):
        if isinstance(person.accessibility, str) :
            if person.accessibility not in self.accessibility:
                self.accessibility[person.accessibility] = []
            self.accessibility[person.accessibility].append(person)


    def add_stage(self, person: Attendee):
        if person.career_stage not in self.career_stages:
            self.career_stages[person.career_stage] = []
        self.career_stages[person.career_stage].append(person)

    def get_diets(self):
        for p in self.attendees:
            self.add_diet(p)
        return self.diets

    def get_stages(self):
        for p in self.attendees:
            self.add_stage(p)
        return self.diets

    def get_affiliations(self):
        for p in self.attendees:
            self.add_affiliation(p)
        return self.diets

    def get_accessibility(self):
        for p in self.attendees:
            self.add_accessibility(p)
        return self.accessibility

    def _show_property(self, property_dict: dict, output_name: str, show_all: bool = False):
        str_dict = {}
        numbers = {}
        property_list = list(property_dict.keys())
        property_list.sort()
        for property_name in property_list:
            people = property_dict[property_name]
            str_dict[property_name] = list(map(lambda p: str(p), people))
            numbers[property_name] = len(str_dict[property_name])
            print(f"\t{property_name}: {len(people)}")
            if show_all:
                for p in people:
                    print("\t\t", p)

        write_dict = {
            "People": str_dict,
            "Numbers": numbers
        }
        u.save_params(file=os.path.join(self.output, f"{output_name}.yaml"), dictionary=write_dict)
        return write_dict

    def show_stages(self, show_all: bool = False):
        self.get_stages()
        print("Career Stages:")
        return self._show_property(output_name="career_stages", show_all=show_all, property_dict=self.career_stages)

    def show_affiliations(self, show_all: bool = False):
        self.get_affiliations()
        print("Affiliations:")
        return self._show_property(output_name="affiliations", show_all=show_all, property_dict=self.affiliations)

    def show_diets(self, show_all: bool = True):
        self.get_diets()
        print("Dietary Requirements:")
        return self._show_property(output_name="diet", show_all=show_all, property_dict=self.diets)

    def show_accessibility(self, show_all: bool = True):
        self.get_accessibility()
        print("Accessibility Requirements:")
        return self._show_property(output_name="accessibility", show_all=show_all, property_dict=self.accessibility)


    def to_dataframe(self):
        attendee_dicts = list(map(lambda a: a.__dict__, self.attendees))
        df = pd.DataFrame.from_dict(data=attendee_dicts)
        return df

    def write_attendee_table(self):
        df = self.to_dataframe()
        df.to_csv(os.path.join(self.output, "attendees.csv"))

    def check_for_duplicates(self, show=True):
        possible = []
        confirmed = []
        self.attendees.sort(key=lambda p: p.name_family)
        for person in self.attendees:
            for other in self.attendees:
                if other is not person and other.loose_match(f"{person.name_given} {person.name_family}"):
                    if other.email == person.email:
                        confirmed.append((person, other))
                        self.attendees.remove(other)
                    else:
                        possible.append((person, other))

        if show:
            print("\nPossible duplicates:")
            if not possible:
                print("None")
            for p1, p2 in possible:
                print(f"\t{p1} of {p2}")

            print("\nConfirmed duplicates (removed automatically):")
            if not confirmed:
                print("None")
            for p1, p2 in confirmed:
                print(f"\t{p1} of {p2}")

        return possible, confirmed

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
    if person_1.roommate_nominee_obj is person_2:
        # Otherwise, we check if the nominees of the pair are each other
        if person_2.roommate_nominee_obj is person_1:
            return True
        # Sometimes only one will nominate the other; if the other has not nominated anyone, then we allow this to go through
        elif not person_2.has_nominee():
            return True
