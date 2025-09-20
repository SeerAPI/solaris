from functools import partial

from pydantic.json_schema import GenerateJsonSchema, JsonSchemaMode, model_json_schema

from solaris.analyze.model import ROOT_MARK, ROOT_MARK_KEY, is_base_general_model


class JsonSchemaGenerator(GenerateJsonSchema):
	def generate(self, schema, mode: JsonSchemaMode = 'serialization'):
		json_schema = super().generate(schema, mode)
		json_schema['$schema'] = self.schema_dialect
		return json_schema


class ShrinkOnlyNonRoot(JsonSchemaGenerator):
	def generate(self, schema, mode: JsonSchemaMode = 'serialization'):
		"""
		重写根级别 schema 生成，
		将非根模型的 BaseGeneralModel schema 省略为 $ref 引用
		"""
		cls = schema.get('cls')
		if is_base_general_model(cls):
			# 标记为根模型以输出完整 schema
			new_core_schema = schema.copy()
			new_core_schema[ROOT_MARK_KEY] = ROOT_MARK  # type: ignore
		else:
			new_core_schema = schema

		json_schema = super().generate(new_core_schema, mode)
		return json_schema


class ShrinkAll(JsonSchemaGenerator):
	def generate(self, schema, mode: JsonSchemaMode = 'serialization'):
		# schema.pop(ROOT_MARK_KEY, None) # 删除根标记
		json_schema = super().generate(schema, mode)
		return json_schema


model_json_schema = partial(
	model_json_schema,
	schema_generator=ShrinkOnlyNonRoot,
	mode='serialization',
)
