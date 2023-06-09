from hwsa.event import Event
import hwsa.utils as utils

# TODO: prioritise people with specified preferences, the fewer the earlier

def main(
        p: str,
        o: str,
        d: bool,
        **kwargs
):
    utils.debug = d
    # Motel AC Units
    room_numbers_1 = list(range(25, 31)) + list(range(33, 49)) + [12, 67, 68]
    # Motel budget AC Units
    room_numbers_2 = list(range(79, 85))
    room_numbers = room_numbers_2 + room_numbers_1
    hwsa_2023 = Event.from_mq_xl(
        path=p,
        output=o,
        max_per_room=kwargs["n_max"],
        n_rooms=kwargs["n_rooms"],
        room_numbers=room_numbers
    )
    hwsa_2023.check_for_duplicates()
    print("\n\n")
    hwsa_2023.allocate_roommates()
    print("\n\n")
    hwsa_2023.show_affiliations()
    print("\n\n")
    hwsa_2023.show_stages()
    print("\n\n")
    hwsa_2023.show_diets()
    print("\n\n")
    hwsa_2023.show_accessibility()
    print("\n\n")
    hwsa_2023.show_genders()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Assigns rooms for attendees."
    )
    parser.add_argument(
        "-p",
        type=str,
        default="/home/lachlan/Data/hwsa/Comprehensive_report_final.xlsx",
        help="Path to Macquarie-generated XLSX of attendees"
    )
    parser.add_argument(
        "-o",
        type=str,
        default="/home/lachlan/Data/hwsa/",
        help="Output directory"
    )
    parser.add_argument(
        "--n_max",
        type=int,
        default=2,
        help="Max occupants per room"
    )
    parser.add_argument(
        "--n_rooms",
        type=int,
        default=40,
        help="Number of rooms"
    )

    parser.add_argument(
        "-d",
        action="store_true",
        help="Debug mode"
    )
    
    # parser.add_argument(
    #
    # )

    args = parser.parse_args()

    main(**args.__dict__)
