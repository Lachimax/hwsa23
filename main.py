from hwsa.event import Event


# TODO: Output all results
# TODO: Get list of room numbers and assign from that
# TODO: prioritise people with specified preferences, the fewer the earlier

def main(
        p: str,
        o: str,
        **kwargs
):
    hwsa_2023 = Event.from_mq_xl(path=p, output=o, max_per_room=kwargs["n_max"], n_rooms=kwargs["n_rooms"])
    hwsa_2023.allocate_roommates()
    print("\n\n")
    hwsa_2023.show_diets()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Assigns rooms for attendees."
    )
    parser.add_argument(
        "-p",
        type=str,
        default="/home/lachlan/Documents/hwsa/Comprehensive report_d0836c81-5fb7-48c7-9e47-9338326a5831.xlsx",
        help="Path to Macquarie-generated XLSX of attendees"
    )
    parser.add_argument(
        "-o",
        type=str,
        default="/home/lachlan/Documents/hwsa/",
        help="Output directory"
    )
    parser.add_argument(
        "--n_max",
        type=int,
        default=4,
        help="Max occupants per room"
    )
    parser.add_argument(
        "--n_rooms",
        type=int,
        default=40,
        help="Number of rooms"
    )
    # parser.add_argument(
    #
    # )

    args = parser.parse_args()

    main(**args.__dict__)
