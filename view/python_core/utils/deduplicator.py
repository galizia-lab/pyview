import typing
import re


def dedupilicate(value: str, existing_values: typing.Iterable[str]):
    """
    If <value> is present in <existing_value>, returns '<value>(1)'. If '<value>(1)' is present in <existing_values>,
    returns '<value>(2)' and so on. A typical use would run <value> through this function and then append it to
    <existing_values>.
    :param value: str
    :param existing_values: an iterable of strings
    :return: str
    """

    reccurances = []
    for existing_label in existing_values:

        if value == existing_label:
            reccurances.append(1)

        re_match = re.match(f"{value}\((.*)\)", existing_label)
        if re_match:
            current_reccurance = int(re_match.group(1))
            reccurances.append(current_reccurance + 1)

    if len(reccurances) == 0:
        return value
    else:
        return f"{value}({max(reccurances)})"