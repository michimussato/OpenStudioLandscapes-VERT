import textwrap

import snakemd


def readme_feature(doc: snakemd.Document) -> snakemd.Document:

    # Some Specific information

    doc.add_heading(
        text="Official Resources",
        level=1,
    )

    # Logo

    doc.add_paragraph(
        snakemd.Inline(
            text=textwrap.dedent(
                """\
                Logo VERT\
                """
            ),
            image="https://github.com/user-attachments/assets/bf441748-0ec5-4c8a-b3e5-11301ee3f0bd",
            link="https://vert.sh",
        ).__str__()
    )

    doc.add_paragraph(
        text=textwrap.dedent(
            """\
            Official VERT-sh information here:\
            """
        )
    )

    doc.add_unordered_list(
        [
            "[Official Website](https://vert.sh/)",
            "[GitHub](https://github.com/VERT-sh/VERT)]",
        ]
    )

    # doc.add_horizontal_rule()

    return doc


if __name__ == "__main__":
    pass
