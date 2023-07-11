import os.path

import numpy as np
import pandas as pd

import hwsa.utils as u

# from hwsa.room import Room

affiliation_aliases = {
    "Curtin Institute of Radio Astronomy": "Curtin University",
    "Curtin Institue of Radio Astronomy": "Curtin University",
    "Curtin University - Curtin Institute of Radio Astronomy": "Curtin University",
    "ICRAR-UWA": "University of Western Australia",
    "ICRAR/UWA": "University of Western Australia",
    "Macquarrie University": "Macquarie University",
    "Research School of Astronomy & Astrophysics, ANU": "Australian National University",
    "Research School of Astronomy and Astrophysics, ANU": "Australian National University",
    "School of Physics - University of Melbourne": "University of Melbourne",
    "School of Physics, University of Melbourne": "University of Melbourne",
    "Swinburne University": "Swinburne University of Technology",
    "SWINBURNE UNIVERSITY OF TECHNOLOGY": "Swinburne University of Technology",
    "Sydney University": "University of Sydney",
    "University of Melbourne School of Physics": "University of Melbourne",
    "University of Melbourne, School of Physics": "University of Melbourne",
    "UNSW": "University of New South Wales",
    "UNSW Canberra": "University of New South Wales",
    "Unviversity of New South Wales": "University of New South Wales",
}


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
        self.will_nominate = None
        self.room = None
        self.registration_type = None
        self.affiliation = None
        self.email = None
        self.career_stage = None
        self.accessibility = None
        self.event = None
        self.title = None
        self.loc = False

        for key, value in kwargs.items():
            if value not in (np.nan, "na"):
                if isinstance(value, str):
                    value = value.replace("\n", "")
                setattr(self, key, value)

        if not isinstance(self.diet, str) or self.diet == "No specific requirements":
            self.diet = None

        self.affiliation_entered = None

        if isinstance(self.affiliation, str):
            self.affiliation_entered = self.affiliation
            if self.affiliation.startswith("The "):
                self.affiliation = self.affiliation.replace("The ", "")
            if "\n" in self.affiliation:
                self.affiliation = self.affiliation.replace("\n", "")
            while self.affiliation.endswith(" "):
                self.affiliation = self.affiliation[:-1]
        if self.affiliation in affiliation_aliases:
            self.affiliation = affiliation_aliases[self.affiliation]

        if isinstance(self.will_nominate, str):
            self.will_nominate = {
                "No roommate nomination. Please allocate one to me.": "no",
                "Nominate a roommate": "now",
                "Will nominate someone later": "later"
            }[self.will_nominate]

        if isinstance(self.phone, str):
            if self.phone.startswith("04"):
                self.phone = "+614" + self.phone[2:]
            if len(self.phone) == 12:
                p = self.phone
                self.phone = p[:3] + " " + p[3:6] + " " + p[6:9] + " " + p[9:12]

        while "No preference" in self.room_preferences:
            self.room_preferences.remove("No preference")

        self.update_manual()

        self.name_str = str(self)

    def __str__(self):
        return f"{self.id} {self.name_given} {self.name_family}"

    def __eq__(self, other):
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def full_name(self):
        return f"{self.name_given} {self.name_family}"

    def update_manual(self):
        if self.event is not None:
            manual_path = os.path.join(self.event.output, "attendees_manual", self.filename() + ".yaml")
            if os.path.isfile(manual_path):
                self.__dict__.update(u.load_params(manual_path))

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
        if name in str(self):
            return True
        if self.name_family in name and self.name_given in name:
            return True
        return False

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

    def to_yaml(self):
        a_dict = self.__dict__.copy()
        for key, value in a_dict.items():
            if not isinstance(value, (float, int, str, list)):
                value = str(value)
                a_dict[key] = value
        return a_dict

    def generate_roommate_email(self, template: str, rm_line=None, no_rm_line=None, output_dir: str = None):
        if self.room is None:
            return
        if rm_line is None:
            rm_line = "You have been assigned a room with {rms}"
        if no_rm_line is None:
            no_rm_line = "You have been assigned a room to yourself (simply because of odd numbers)."

        roommate_str = ""
        n_roommates = len(self.room.roommates) - 1
        for i, person in enumerate(self.room.roommates):
            if person is not self:
                name = person.full_name()
                if i == n_roommates - 1:
                    if n_roommates > 1:
                        roommate_str += f"and {name}."
                    else:
                        roommate_str += f"{name}."
                else:
                    roommate_str += f"{name}, "
        while roommate_str.endswith(" "):
            roommate_str = roommate_str[:-1]
        roommate_str = roommate_str[:-1] + "."
        if not roommate_str:
            rm_line = no_rm_line
        else:
            rm_line = rm_line.format(rms=roommate_str)

        my_name = self.full_name()
        if self.title is not None:
            my_name = self.title + " " + my_name

        email = template.format(name=my_name, roommate_line=rm_line)
        email = self.email + "\n\n" + email

        if output_dir is None:
            output_dir = os.path.join(self.event.output, "roommate_emails")
            u.mkdir_check(output_dir)
        output = os.path.join(output_dir, self.filename())
        with open(output, "w") as file:
            file.write(email)

        return email

    def filename(self):
        return str(self).replace(" ", "_")

    @classmethod
    def from_yaml(cls, path: str):
        _, filename = os.path.split(path)
        yaml = u.load_params(path)
        return Attendee(**yaml)

    @classmethod
    def from_mq_xl_row(cls, row: 'pandas.core.series.Series', event=None):
        other_str = "Marketing - Academic Career stage (other)"
        if other_str in row and isinstance(row[other_str], str):
            career = row.pop(other_str)
            row.pop("Marketing - Current Academic/Career Stage")
        else:
            career = row.pop("Marketing - Current Academic/Career Stage")

        room_preferences = []
        research_types = []
        room_str = "Marketing - If we have to allocate you a roommate, who would you be comfortable sharing with?"
        research_str = "Marketing - Your Research/Thesis Technique"
        for name in row.index:
            if name.startswith(room_str) and isinstance(row[name], str):
                room_preferences.append(row.pop(name))
            if name.startswith(research_str) and isinstance(row[name], str):
                research_types.append(row.pop(name))

        other_research_string = "Marketing - Other Research/Thesis Technique"
        research_types.append(row.pop(other_research_string))

        loc = False
        if "LOC" in row and row["LOC"] == "Y":
            loc = True

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
            will_nominate=row.pop("Marketing - Would you like to nominate a roommate?"),
            affiliation=row.pop("Marketing - Primary Affiliation"),
            other_affiliations=row.pop("Marketing - Other Affiliations (if applicable)"),
            research_types=research_types,
            research_topic=row.pop("Marketing - Your Research/Thesis Topic"),
            other_research_topic=row.pop("Marketing - Other Research/Thesis Topic"),
            registration_type=row.pop("Registration Type - Name"),
            amount_outstanding=float(row.pop("Amount Outstanding")),
            amount_required=float(row.pop("Amount Required")),
            registered=pd.to_datetime(row.pop("Date Registered")),
            accessibility=row.pop("Marketing - Accessibility"),
            loc=loc,
            event=event,
            **row
        )
