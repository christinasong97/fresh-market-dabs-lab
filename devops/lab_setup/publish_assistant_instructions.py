# Databricks notebook source
# MAGIC %md
# MAGIC # Lab admin setup: publish Genie Code workspace instructions
# MAGIC
# MAGIC Run as a **workspace admin** (in Vocareum: from the workspace setup notebook, so every
# MAGIC provisioned workspace gets it). Copies the repo's `.assistant_workspace_instructions.md` to
# MAGIC `/Workspace/.assistant_workspace_instructions.md`, which Genie Code reads for every user.
# MAGIC An existing file is backed up first.

# COMMAND ----------

import base64
import os
from datetime import datetime

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.workspace import ImportFormat

dbutils.widgets.text("source_path", os.path.abspath("../../.assistant_workspace_instructions.md"))
dbutils.widgets.text("backup_folder", "/Workspace/Shared/fresh_market_dabs_lab_admin/backups")

TARGET = "/Workspace/.assistant_workspace_instructions.md"
source_path = dbutils.widgets.get("source_path")
backup_folder = dbutils.widgets.get("backup_folder")
w = WorkspaceClient()

# COMMAND ----------

try:
    existing = w.workspace.download(TARGET).read()
except Exception:
    existing = None

if existing is not None:
    w.workspace.mkdirs(backup_folder)
    backup = f"{backup_folder}/assistant_workspace_instructions_{datetime.now():%Y%m%d_%H%M%S}.md"
    w.workspace.import_(backup, content=base64.b64encode(existing).decode(), format=ImportFormat.AUTO, overwrite=True)
    print(f"Backed up existing instructions to {backup}")

with open(source_path, "rb") as f:
    content = f.read()
w.workspace.import_(TARGET, content=base64.b64encode(content).decode(), format=ImportFormat.AUTO, overwrite=True)
print(f"Published {len(content):,} characters to {TARGET}")
