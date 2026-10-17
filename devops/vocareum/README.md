# Delivering this lab on Vocareum

Vocareum provisions shared workspaces (about 50 attendees each) and runs our setup automatically.

| Vocareum setting | Points to | What happens |
|---|---|---|
| `workspace_setup` | `devops/lab_setup/00_lab_setup` | Runs once per workspace, as an admin: catalogs and grants, landing data, `fresh_market_lab_warehouse`, the legacy job, Genie Code instructions |
| `content.entry` | `00_START_HERE` | The first notebook attendees land on: DABs overview, setup (a no-op once `workspace_setup` has run), and an environment check |

## Build the course content

1. Clone the [Field Driven Enablement Labs](https://go/field-driven-enablement-labs) template course (never build from scratch).
2. Build `content.zip` with one root folder named `fresh_market_dabs_lab` containing:
   - `00_START_HERE.py`
   - `.assistant_workspace_instructions.md`
   - `devops/lab_setup/` (all four files, including `legacy/`)
3. Upload `config.json` (this folder) and `content.zip` with a fresh `manifest.mf` GUID.
4. Set **users per workspace** to about 50 (serverless event guidance).
5. Before the event: open one workspace with **Enter as Admin** and run `00_START_HERE` as a test attendee.

## Run `00_lab_setup` with these widget values

| Widget | Vocareum value |
|---|---|
| `catalog_prefix` | `fresh_market_lab` (must match the catalogs in `databricks.yml`) |
| `catalog_storage_root` | blank (default storage) |
| `attendee_principal` | `account users` |
| `cicd_service_principal` | blank (only the instructor workspace needs one) |
| `warehouse_name` | `fresh_market_lab_warehouse` |

## To confirm with the Vocareum team (#field-driven-labs-vocareum)

- Genie Code agent mode is enabled in the workspaces.
- `workspace_setup` runs with permission to write `/Workspace/.assistant_workspace_instructions.md`.
- Outbound access to github.com for Git folders (attendees clone the public repo).
- Whether the workspaces have an IP access list (decides whether GitHub-hosted runners can deploy in module 5).
