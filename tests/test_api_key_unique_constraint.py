from sqlalchemy import UniqueConstraint
from app.models import ApiKey


def test_api_key_has_unique_constraint_on_key_hash():
    # Verify model declares a UniqueConstraint for `key_hash`.
    table = ApiKey.__table__
    # check column-level unique flag first
    if table.c.key_hash.unique:
        return

    # otherwise check table constraints for UniqueConstraint(['key_hash'])
    for c in table.constraints:
        if isinstance(c, UniqueConstraint) and list(c.columns.keys()) == ["key_hash"]:
            return

    raise AssertionError("ApiKey model must declare UniqueConstraint on 'key_hash'")
