#!/bin/sh
# Migrate, then serve. The app no longer creates its own schema, so this is the step
# that brings a new database up and an existing one forward.
#
# Failing hard here is deliberate: serving against a schema that does not match the
# code produces confusing errors at query time, which is worse than not starting.
set -e

if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    echo "running migrations..."
    alembic upgrade head
fi

exec "$@"
