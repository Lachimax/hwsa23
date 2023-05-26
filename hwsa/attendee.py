import numpy as np
import pandas as pd


# from hwsa.room import Room


class Attendee:
    def __init__(
            self,
            **kwargs
    ):
        self.id = None
        self.name_given = None
        self.name_family = None
        self.phone = None
        self.diet = None
        self.gender = None
        self.room_preferences = []
        self.roommate_nominee = None
        self.roommate_nominee_obj = None
        self.room = None
        self.registration_type = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if isinstance(self.phone, str):
            if self.phone.startswith("04"):
                self.phone = "+614" + self.phone[2:]
            if len(self.phone) == 12:
                p = self.phone
                self.phone = p[:3] + " " + p[3:6] + " " + p[6:9] + " " + p[9:12]

        while "No preference" in self.room_preferences:
            self.room_preferences.remove("No preference")

    def __str__(self):
        return f"{self.id} {self.name_given} {self.name_family}"

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def room_str(self):
        return f"{self} (gender {self.gender}; nominated {self.roommate_nominee}; room preferences {self.room_preferences})"

    def prefer_roommate(self, other: 'Attendee'):
        return not self.room_preferences or other.gender in self.room_preferences

    def n_preferences(self):
        if self.room_preferences:
            return len(self.room_preferences)
        else:
            return np.inf

    def loose_match(self, name: str):
        return name in str(self)

    def has_diet(self):
        return isinstance(self.diet, str) and self.diet != "No specific requirements"

    def has_nominee(self):
        return isinstance(self.roommate_nominee, str)

    def needs_room(self):
        return self.registration_type == "Attendance & Accommodation"

    def has_room(self):
        from hwsa.room import Room
        return isinstance(self.room, Room)

    def roommates(self):
        if self.has_room():
            return self.room.roommates
        else:
            return []

    def n_roommates(self):
        if not self.has_room():
            return 0
        return len(self.room.roommates)

    @classmethod
    def from_mq_xl_row(cls, row: 'pandas.core.series.Series'):
        other_str = "Marketing - Academic Career stage (other)"
        if other_str in row and isinstance(row[other_str], str):
            career = row[other_str]
        else:
            career = row["Marketing - Current Academic/Career Stage"]

        room_preferences = []
        research_types = []
        room_str = "Marketing - If we have to allocate you a roommate, who would you be comfortable sharing with?"
        research_str = "Marketing - Your Research/Thesis Technique"
        for name in row.index:
            if name.startswith(room_str) and isinstance(row[name], str):
                room_preferences.append((row[name]))
            if name.startswith(research_str) and isinstance(row[name], str):
                research_types.append(row[name])

        return Attendee(
            id=row.pop("ID"),
            title=row.pop("Title"),
            name_given=row.pop("First Name"),
            name_family=row.pop("Last Name"),
            phone=str(row.pop("Mobile Number")),
            email=row.pop("Primary Email"),
            diet=row.pop("Dietary Requirements"),
            career_stage=career,
            gender=row.pop("Marketing - Gender Identity"),
            room_preferences=room_preferences,
            roommate_nominee=row.pop("Marketing - Nominated roommate"),
            affiliation=row.pop("Marketing - Primary Affiliation"),
            research_types=research_types,
            research_topic=row.pop("Marketing - Your Research/Thesis Topic"),
            registration_type=row.pop("Registration Type - Name"),
            amount_outstanding=float(row.pop("Amount Outstanding")),
            amount_required=float(row.pop("Amount Required")),
            registered=pd.to_datetime(row.pop("Date Registered")),
            **row
        )
