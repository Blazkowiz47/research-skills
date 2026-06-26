# Research Skills

Shared Codex and Claude skills for Sushrut/Mobai research workflows.

## Install

Clone this repository, then install the skills into both agents:

```sh
git clone git@github.com:Blazkowiz47/research-skills.git ~/1Projects/research-skills
cd ~/1Projects/research-skills
./install.sh
```

The installer uses symlinks by default. After that, updates are just:

```sh
cd ~/1Projects/research-skills
git pull
```

Useful install variants:

```sh
./install.sh --target codex
./install.sh --target claude
./install.sh --method copy --force
./install.sh --skill create-dl-project
./install.sh --skill reuse-dl-component
```

## Skills

### `create-dl-project`

Scaffold a new `dl-core` experiment project with `uv`, a chosen Torch version, and one backend:

- `core`: no external tracker
- `azure`: Azure extension wiring
- `mlflow`: local MLflow wiring
- `wandb`: Weights & Biases wiring

Example prompt:

```text
Use $create-dl-project to create a new dl-core experiment project.
```

### `reuse-dl-component`

Copy a same-named local `dataset` or `metric_manager` component from one `dl-core` experiment repo to another. The helper runs `dl-core add` in the destination first, so the generated package exports stay aligned, then copies the source module over the generated file.

Example prompt:

```text
Use $reuse-dl-component to copy the ArcfaceDataset dataset from /home/ubuntu/1Projects/old_project to /home/ubuntu/1Projects/new_project.
```

For now, this skill intentionally supports same-name reuse only. Renaming requires manually checking decorators, class names, imports, and config references.
