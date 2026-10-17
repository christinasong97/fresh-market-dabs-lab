# Databricks notebook source
# MAGIC %md
# MAGIC # Lab setup (run once per workspace, as an admin)
# MAGIC
# MAGIC Creates everything the lab needs that lives **outside** the bundle. Safe to re-run.
# MAGIC
# MAGIC | Step | Creates |
# MAGIC |---|---|
# MAGIC | 1 | Catalogs `<prefix>_int`, `<prefix>_cert`, `<prefix>_prod`, plus grants for attendees |
# MAGIC | 2 | `landing.raw` volume in each catalog, with synthetic Fresh Market POS data |
# MAGIC | 3 | A named serverless SQL warehouse that every attendee can use |
# MAGIC | 4 | The hand-built legacy job `Job_02_PL_Store_KPI_Alerts` used in module 1 |
# MAGIC | 5 | Genie Code workspace instructions (`/Workspace/.assistant_workspace_instructions.md`) |
# MAGIC
# MAGIC Everything else (schemas, pipeline, jobs, dashboard, Genie space) is created by attendees when they
# MAGIC deploy the bundle.
# MAGIC
# MAGIC **Vocareum:** register this notebook as the workspace setup notebook.
# MAGIC **Free Edition:** open it from your Git folder and click **Run all**.

# COMMAND ----------

dbutils.widgets.text("catalog_prefix", "fresh_market_lab", "Catalog prefix")
dbutils.widgets.text("catalog_storage_root", "", "Storage root override (usually blank)")
dbutils.widgets.text("attendee_principal", "account users", "Attendee group (blank = skip grants)")
dbutils.widgets.text("cicd_service_principal", "", "CI/CD service principal app ID (blank = skip)")
dbutils.widgets.text("warehouse_name", "fresh_market_lab_warehouse", "SQL warehouse name")
dbutils.widgets.dropdown("stage_data", "auto", ["auto", "true", "false"], "Stage landing data (auto = only if missing)")

prefix = dbutils.widgets.get("catalog_prefix").strip()
storage_root = dbutils.widgets.get("catalog_storage_root").strip().rstrip("/")
attendees = dbutils.widgets.get("attendee_principal").strip()
cicd_sp = dbutils.widgets.get("cicd_service_principal").strip()
warehouse_name = dbutils.widgets.get("warehouse_name").strip()
stage_data = dbutils.widgets.get("stage_data")

catalogs = {t: f"{prefix}_{t}" for t in ("int", "cert", "prod")}

# COMMAND ----------

# MAGIC %md ## 1. Catalogs and grants

# COMMAND ----------


def grant(securable, privileges, principal):
    if principal:
        spark.sql(f"GRANT {', '.join(privileges)} ON {securable} TO `{principal}`")


def create_catalog(catalog, comment):
    """Create a catalog where the workspace keeps its other catalogs.

    Most workspaces (Vocareum, Free Edition) pick the storage automatically. Some shared metastores, like
    FEVM's, don't; there we reuse the storage of the workspace's default catalog, so nobody has to supply it.
    """
    if storage_root:
        spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}` MANAGED LOCATION '{storage_root}/{catalog}' COMMENT '{comment}'")
        return
    try:
        spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}` COMMENT '{comment}'")
    except Exception as e:  # noqa: BLE001 - only the "no default storage" case is handled below
        if "storage" not in str(e).lower():
            raise
        default_catalog = spark.sql("SELECT current_catalog()").first()[0]
        root = (spark.sql(f"DESCRIBE CATALOG EXTENDED `{default_catalog}`").where("info_name = 'Storage Root'").first() or [None, None])[1]
        if not root:
            raise RuntimeError(
                "This workspace has no default storage for new catalogs. Set the catalog_storage_root widget."
            ) from e
        spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}` MANAGED LOCATION '{root.rstrip('/')}/{catalog}' COMMENT '{comment}'")
        print(f"  (no default storage here; using {default_catalog}'s storage: {root})")


for target, catalog in catalogs.items():
    create_catalog(catalog, f"Fresh Market DABs lab: {target} target")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.landing COMMENT 'Upstream source data (not managed by the bundle)'")
    spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalog}`.landing.raw COMMENT 'POS landing zone'")

    # Attendees create their own dev_<name>_store_ops schema in int, and can read cert and prod.
    if target == "int":
        grant(f"CATALOG `{catalog}`", ["USE CATALOG", "CREATE SCHEMA"], attendees)
    else:
        grant(f"CATALOG `{catalog}`", ["USE CATALOG", "USE SCHEMA", "SELECT"], attendees)
    grant(f"SCHEMA `{catalog}`.landing", ["USE SCHEMA", "READ VOLUME"], attendees)

    # The CI/CD service principal deploys int, cert, and prod and owns what it creates.
    grant(f"CATALOG `{catalog}`", ["USE CATALOG", "CREATE SCHEMA"], cicd_sp)
    grant(f"SCHEMA `{catalog}`.landing", ["USE SCHEMA", "READ VOLUME"], cicd_sp)
    print(f"catalog ready: {catalog}")

# COMMAND ----------

# MAGIC %md ## 2. Landing data

# COMMAND ----------



def has_landing_data(catalog):
    try:
        return len(dbutils.fs.ls(f"/Volumes/{catalog}/landing/raw/pos_transactions")) > 0
    except Exception:  # noqa: BLE001 - folder doesn't exist yet
        return False


missing = [c for c in catalogs.values() if stage_data == "true" or (stage_data == "auto" and not has_landing_data(c))]
if missing:
    dbutils.notebook.run("./stage_landing_data", 1800, {"catalogs": ",".join(missing)})
    print(f"landing data staged: {', '.join(missing)}")
else:
    print("landing data already present, skipped")

# COMMAND ----------

# MAGIC %md ## 3. SQL warehouse

# COMMAND ----------

from databricks.sdk import WorkspaceClient  # noqa: E402
from databricks.sdk.service import iam, jobs, sql, workspace  # noqa: E402

w = WorkspaceClient()

existing = next((wh for wh in w.warehouses.list() if wh.name == warehouse_name), None)
if existing:
    warehouse_id = existing.id
    print(f"warehouse exists: {warehouse_name} ({warehouse_id})")
else:
    warehouse_id = w.warehouses.create(
        name=warehouse_name,
        cluster_size="Small",
        min_num_clusters=1,
        max_num_clusters=4,
        auto_stop_mins=10,
        enable_serverless_compute=True,
        warehouse_type=sql.CreateWarehouseRequestWarehouseType.PRO,
    ).response.id
    print(f"warehouse created: {warehouse_name} ({warehouse_id})")

w.permissions.update(
    "warehouses",
    warehouse_id,
    access_control_list=[iam.AccessControlRequest(group_name="users", permission_level=iam.PermissionLevel.CAN_USE)]
    + ([iam.AccessControlRequest(service_principal_name=cicd_sp, permission_level=iam.PermissionLevel.CAN_USE)] if cicd_sp else []),
)

# COMMAND ----------

# MAGIC %md ## 4. Legacy job (module 1 starting point)

# COMMAND ----------

import base64  # noqa: E402
import os  # noqa: E402

LEGACY_FOLDER = "/Workspace/Shared/fresh_market_dabs_lab_legacy"
LEGACY_NOTEBOOK = f"{LEGACY_FOLDER}/Job_02_Store_KPI_Alerts"
LEGACY_JOB = "Job_02_PL_Store_KPI_Alerts"

# In a Git folder the legacy .py file is a notebook, so read it through the workspace API.
exported = w.workspace.export(f"{os.getcwd()}/legacy/Job_02_Store_KPI_Alerts", format=workspace.ExportFormat.SOURCE)
source = base64.b64decode(exported.content).decode().replace("fresh_market_lab_int", catalogs["int"])

w.workspace.mkdirs(LEGACY_FOLDER)
w.workspace.import_(
    LEGACY_NOTEBOOK,
    content=base64.b64encode(source.encode()).decode(),
    format=workspace.ImportFormat.SOURCE,
    language=workspace.Language.PYTHON,
    overwrite=True,
)

settings = jobs.JobSettings(
    name=LEGACY_JOB,
    description="Store KPI alerts. Runs after Job_01_PL_Store_Sales_Load. Owner: Jane Doe (INT only).",
    email_notifications=jobs.JobEmailNotifications(on_failure=["jane.doe@example.com"]),
    schedule=jobs.CronSchedule(
        quartz_cron_expression="0 30 6 * * ?", timezone_id="America/Detroit", pause_status=jobs.PauseStatus.PAUSED
    ),
    tasks=[jobs.Task(task_key="Task_01_Store_KPIs", notebook_task=jobs.NotebookTask(notebook_path=LEGACY_NOTEBOOK))],
)
legacy = next(iter(w.jobs.list(name=LEGACY_JOB)), None)
if legacy:
    w.jobs.reset(job_id=legacy.job_id, new_settings=settings)
    legacy_id = legacy.job_id
else:
    legacy_id = w.jobs.create(
        name=settings.name,
        description=settings.description,
        email_notifications=settings.email_notifications,
        schedule=settings.schedule,
        tasks=settings.tasks,
    ).job_id
w.permissions.update(
    "jobs",
    str(legacy_id),
    access_control_list=[iam.AccessControlRequest(group_name="users", permission_level=iam.PermissionLevel.CAN_VIEW)],
)
print(f"legacy job ready: {LEGACY_JOB} ({legacy_id})")

# COMMAND ----------

# MAGIC %md ## 5. Genie Code workspace instructions

# COMMAND ----------

print(dbutils.notebook.run("./publish_assistant_instructions", 300, {}) or "instructions published")

# COMMAND ----------

# MAGIC %md ## Done
# MAGIC Attendees can now create a Git folder from the lab repo, switch to `lab/start`, and deploy the `dev` target.

# COMMAND ----------

print(f"catalogs: {', '.join(catalogs.values())}")
print(f"warehouse: {warehouse_name} ({warehouse_id})")
print(f"legacy job: {LEGACY_JOB} ({legacy_id})")
