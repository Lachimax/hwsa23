from hwsa.event import Event


def main(
        p: str,
        o: str,
        **kwargs
):
    hwsa_2023 = Event.from_mq_xl(path=p, output=o)
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
    # parser.add_argument(
    #
    # )

    args = parser.parse_args()

    main(**args.__dict__)
