"""This module houses a sphinx extension that generates documentation for Sample and Measurement classes defined in the specified apps."""

import os

import django
from django.apps import apps
from docutils import nodes
from sphinx.addnodes import desc, desc_content, desc_signature
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective
from sphinx.util.logging import getLogger

# from sphinx.util.docfields import Field, GroupedField
from fairdm.registry import registry

# from io import StringIO
# import markdown

logger = getLogger(__name__)


def generate_data_model_docs(app: Sphinx):
    docs_dir = app.srcdir
    out_dir = os.path.join(docs_dir, "data_models")
    os.makedirs(out_dir, exist_ok=True)

    # Create index.md
    index_path = os.path.join(out_dir, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Data Models\n\n")
        f.write("```{toctree}\n")
        f.write(":maxdepth: 1\n\n")
        f.write("samples\n")
        f.write("measurements\n")
        f.write("```\n")

    # Create samples.md
    samples_path = os.path.join(out_dir, "samples.md")
    with open(samples_path, "w", encoding="utf-8") as f:
        f.write("# Sample types\n\n")
        for config in registry.samples:
            f.write(f"```{{autodjango-model}} {config['full_name']}\n```\n\n")

    # Create measurements.md
    measurements_path = os.path.join(out_dir, "measurements.md")
    with open(measurements_path, "w", encoding="utf-8") as f:
        f.write("# Measurement types\n\n")
        for config in registry.measurements:
            f.write(f"```{{autodjango-model}} {config['full_name']}\n```\n\n")


class AutoDjangoModelDirective(SphinxDirective):
    required_arguments = 1  # e.g., 'myapp.MyModel'

    def build_field_description(self, field):
        """Return a list of sphinx field description nodes."""
        desc_node = desc()
        desc_node["domain"] = "py"
        desc_node["objtype"] = "attribute"

        sig = desc_signature("", "")
        sig += nodes.Text(f"{field.name} ({field.verbose_name.title()}): {field.__class__.__name__}")
        desc_node += sig

        content = desc_content()

        if getattr(field, "base_units", None):
            para = nodes.paragraph()
            para += nodes.strong(text="Units: ")
            para += nodes.Text(field.base_units)
            content += para

        if field.help_text:
            content += nodes.paragraph(text=field.help_text)

        desc_node += content

        return desc_node

    def build_fields(self, model_fields):
        section = nodes.section()
        section["ids"].append(nodes.make_id("fields"))
        section += nodes.title(text="Declared Fields")
        section += nodes.paragraph(text="The following fields are declared in this data model.")
        for field in model_fields:
            field = self.build_field_description(field)
            section.append(field)
        return section

    def _get_ordered_fields(self, model):
        """Order fields based on the include/exclude logic"""
        fields_by_name = {f.name: f for f in model._meta.get_fields() if hasattr(f, "verbose_name")}
        include_fields = model.config.get_flat_fields()

        if include_fields:
            ordered_fields = [fields_by_name[f] for f in include_fields if f in fields_by_name]
        else:
            # Automatically order: uuid first (if not excluded), then rest alphabetically
            sorted_field_names = sorted(f for f in fields_by_name)
            ordered_fields = [fields_by_name[f] for f in sorted_field_names]

        return ordered_fields

    def build_table_header(self, col_titles):
        """Build the header row of the table"""
        thead = nodes.thead()
        header_row = nodes.row()
        for title in col_titles:
            entry = nodes.entry()
            entry += nodes.paragraph(text=title)
            header_row += entry
        thead += header_row
        return thead

    def build_table_row(self, cells):
        """Build a row of the table"""
        row = nodes.row()
        for cell_text in cells:
            entry = nodes.entry()
            entry += nodes.paragraph(text=cell_text)
            row += entry
        return row

    def build_table_body(self, ordered_fields):
        """Build the body of the table"""
        tbody = nodes.tbody()
        for field in ordered_fields:
            # validators = getattr(field, "validators", [])
            # val_text = ", ".join(v.__class__.__name__ for v in validators)
            cells = [
                field.name,
                field.help_text,
            ]

            tbody += self.build_table_row(cells)
        return tbody

    def build_model_metadata_section(self, metadata):
        section = nodes.section()
        section["ids"].append(nodes.make_id(metadata["verbose_name"]))

        # Title (H2)
        title_node = nodes.title(text=metadata["verbose_name"])
        section += title_node

        config = metadata.get("config", {})

        # Description
        description = getattr(config, "description", None)
        if description:
            section += nodes.paragraph(text=description)

        # Keywords
        keywords = getattr(config, "keywords", None)
        if keywords:
            keyword_text = "<strong>Keywords</strong>: " + ", ".join(keywords)
            para = nodes.paragraph()
            para += nodes.raw("", keyword_text, format="html")
            section += para

        return section

    def build_table(self, ordered_fields):
        """Build the table for the model"""
        col_titles = ["field", "description"]
        table = nodes.table()
        tgroup = nodes.tgroup(cols=len(col_titles))
        table += tgroup

        for _ in col_titles:
            tgroup += nodes.colspec(colwidth=1)

        tgroup += self.build_table_header(col_titles)
        tgroup += self.build_table_body(ordered_fields)

        return table

    def run(self):
        if not apps.ready:
            django.setup()

        model_path = self.arguments[0]
        try:
            app_label, model_name = model_path.split(".")
        except ValueError:
            return [nodes.paragraph(text=f"❌ Invalid model path: '{model_path}'")]

        model = apps.get_model(app_label, model_name)
        if model is None:
            return [nodes.paragraph(text=f"❌ Could not load model: '{model_path}'")]

        # Fetch metadata from registry
        metadata = registry.get_model(model)

        # Build model metadata (heading, description, keywords)
        section = self.build_model_metadata_section(metadata)

        # Get ordered fields using helper
        ordered_fields = self._get_ordered_fields(model)

        section.append(self.build_fields(ordered_fields))
        # field_nodes = self.build_field_descriptions(ordered_fields)
        # for node in field_nodes:
        # section += node
        # # Table setup
        # col_titles = ["Field", "Verbose Name", "Help Text", "Type", "Validators"]
        # table = nodes.table()
        # tgroup = nodes.tgroup(cols=len(col_titles))
        # table += tgroup

        # for _ in col_titles:
        #     tgroup += nodes.colspec(colwidth=1)

        # tgroup += self.build_table_header(col_titles)
        # tgroup += self.build_table_body(ordered_fields)

        # Append table to metadata section
        # section.append(self.build_table(ordered_fields))

        return [section]


def setup(app):
    app.add_config_value("autodjango_model_apps", [], "env")  # Custom config in conf.py
    app.add_directive("autodjango-model", AutoDjangoModelDirective)
    app.connect("builder-inited", generate_data_model_docs)
    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

    # print(content)
    # print(type(content))

    # Return a literal block node with the content
    # literal = nodes.literal_block(content, content)
    # literal["language"] = "markdown"  # Syntax highlighting for Markdown
    # return [literal]
    # Inject raw Markdown content
