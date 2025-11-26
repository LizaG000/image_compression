import os
import sys
from loguru import logger

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, BASE_DIR)

import asyncio
from logging.config import fileConfig
from typing import cast
from sqlalchemy import Connection
from sqlalchemy import pool
from sqlalchemy import text
from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.config import get_config
from src.infra.postgres.tables import *
from src.infra.postgres.schemas import enabled_pg_schemas


cfg = get_config()

# получение alembic конфига
config = context.config
# загружает и применяет настройки логирования
fileConfig(cast(str, config.config_file_name))

# загружает строку подключения к бд, если она пустая
if len(config.get_section(config.config_ini_section)['sqlalchemy.url']) == 0:  # type: ignore[index]
    config.set_main_option(
        'sqlalchemy.url',
        cfg.database.dsn,
    )
logger.info(config.get_section(config.config_ini_section)['sqlalchemy.url'])
# хранит в себе модели
target_metadata = BaseDBModel.metadata
# хранит в себе имена схем
target_schemas = list(target_metadata._schemas)

version_schema = '__alembic_schema'

# проверка всех схем на наличие
for schema in target_schemas:
    if schema not in enabled_pg_schemas:
        raise Exception(
            'Add new schema(s) in enable_schemas or fix schema name typo in detected table(s)',
        )

# если объект не схема, 
# то включает его в миграцию, 
# а если схема, то проверяет, 
# есть ли он в списке схем
def include_name(name, type_, parent_names) -> bool:
    if type_ == 'schema':
        return name in enabled_pg_schemas
    return True

def include_object(object, name, type_, reflected, compare_to):
    return not (type_ == 'table' and object.schema not in enabled_pg_schemas)

# удаляют пустые миграции
def process_revision_directives(context, revision, directives):
    if config.cmd_opts.autogenerate:
        script = directives[0]
        for upgrade_ops in script.upgrade_ops_list:
            if upgrade_ops.is_empty():
                directives[:] = []

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        echo=True,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
        dialect_opts={'paramstyle': 'named'},
        template_args={'enabled_pg_schemas': enabled_pg_schemas},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
        version_table_schema=version_schema,
        include_name=include_name,
        process_revision_directives=process_revision_directives,
        template_args={'enabled_pg_schemas': enabled_pg_schemas},
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    if configuration is None:
        raise ValueError(
            f'Not found configuration by ini section {config.config_ini_section!r}'
        )
    connectable = async_engine_from_config(
        configuration=configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Создаем схему версии
        await connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS {version_schema}'))
        for schema in enabled_pg_schemas:
            await connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
        await connection.commit()
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())