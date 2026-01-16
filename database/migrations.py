"""Dynamic database migrations using SQLAlchemy."""

from loguru import logger
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel


def run_migrations(engine: Engine):
    """Automatically detect and add missing columns from SQLModel definitions."""
    inspector = inspect(engine)

    # Get all tables from SQLModel metadata
    for table_name, table in SQLModel.metadata.tables.items():
        if table_name not in inspector.get_table_names():
            logger.info(
                f"Table '{table_name}' doesn't exist yet, will be created by create_all()"
            )
            continue

        # Get existing columns in the database
        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}

        # Check each column in the model
        for column in table.columns:
            if column.name not in existing_columns:
                logger.info(
                    f"Adding missing column '{column.name}' to table '{table_name}'"
                )

                # Determine column type
                col_type = column.type.compile(engine.dialect)
                nullable = "NULL" if column.nullable else "NOT NULL"
                default = ""

                if column.default is not None:
                    if hasattr(column.default, "arg"):
                        default = f" DEFAULT '{column.default.arg}'"
                    elif column.default.is_scalar:
                        default = f" DEFAULT {column.default.arg}"

                sql = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {col_type}{default}"

                with engine.connect() as conn:
                    conn.execute(text(sql))
                    conn.commit()

                logger.info(
                    f"Successfully added column '{column.name}' to '{table_name}'"
                )
            else:
                logger.debug(f"Column '{column.name}' already exists in '{table_name}'")
