def pretty_list(in_: list, conjunction: str):
    return f' {conjunction} '.join(
        i for i in (', '.join(in_[:-1]), in_[-1],) if i)
