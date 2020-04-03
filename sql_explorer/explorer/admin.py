from django.contrib import admin
from sqlalchemy import create_engine
from sqlalchemy.engine.reflection import Inspector

from sqlalchemy.sql.sqltypes import INTEGER, VARCHAR, TEXT, FLOAT, BOOLEAN, DATE
from sqlalchemy.dialects.postgresql.base import TIMESTAMP
from django_admin_listfilter_dropdown.filters import DropdownFilter

from explorer.models import FieldSchema, ModelSchema

engine = create_engine('postgresql://postgres:password@0.0.0.0:5436/app')
insp = Inspector.from_engine(engine)

column_mapping = {
    VARCHAR: 'character',
    TEXT: 'text',
    INTEGER: 'integer',
    FLOAT: 'float',
    BOOLEAN: 'boolean',
    DATE: 'date',
    TIMESTAMP: 'date'
}

schemas = {}

for schema in insp.get_schema_names():
    if schema in ['pg_toast', 'pg_temp_1', 'pg_toast_temp_1', 'pg_catalog', 'information_schema', 'public']:
        continue

    schemas[schema] = {}
    for table in insp.get_table_names(schema=schema):
        columns = insp.get_columns(table, schema=schema)
        schemas[schema][table] = [{'name': x['name'], 'data_type': column_mapping[type(x['type'])]} for x in columns if x != 'id']

try:
    for schema, tables in schemas.items():
        for table_name, columns in tables.items():
            try:
                model = ModelSchema.objects.get(name=table_name)
            except ModelSchema.DoesNotExist:
                model = ModelSchema.objects.create(name=table_name)

            for column in columns:
                if column['name'] == 'id':
                    continue
                try:
                    field = FieldSchema.objects.get(name=column['name'])
                except FieldSchema.DoesNotExist:
                    field = FieldSchema.objects.create(
                        name=column['name'], data_type=column['data_type']
                    )

                try:
                    model.add_field(field)
                except:
                    pass

            Model = model.as_model()
            Model._meta.db_table = schema + '"."' + Model._meta.db_table.replace('explorer_', '')

            Admin = type(table_name, (admin.ModelAdmin,), dict(
                list_filter=tuple([(x.name,DropdownFilter) for x in Model._meta.fields if x.name != 'id']),
                list_display=tuple([x.name for x in Model._meta.fields if x.name != 'id']),
                search_fields=tuple([x.name for x in Model._meta.fields if x.name != 'id'])
            ))
            admin.site.register(Model, Admin)

except:
    pass
