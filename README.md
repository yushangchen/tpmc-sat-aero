# TPMC-SAT-AERO

A Python-based rarefied aerodynamic analysis platform for CubeSat and small-satellite applications.  
This project supports both **TPMC** (Test Particle Monte Carlo) and **FMF** (Free Molecular Flow) styles of analysis using STL-based geometry, per-face surface models, standardized atmosphere interfaces, batch workflows, convergence reports, and aerodynamic database export.

---

## Overview

This repository was developed to move beyond a single-case rarefied aerodynamic prototype and toward a reusable engineering workflow for CubeSat-class spacecraft.

The platform is designed for:

- rarefied aerodynamic force and moment analysis
- attitude-dependent drag database generation
- TPMC / FMF comparison
- CubeSat surface-property studies
- future integration with orbit lifetime, ADCS, and mission analysis workflows

The current version is no longer only a solver. It is a **solver + workflow + reporting + database generation platform**.

---

## Current Status

**Current status: V2 core platform completed**

This means the project already supports:

- STL-based geometry analysis
- switchable **TPMC** and **FMF** solver modes
- per-face surface classification and surface-property assignment
- standardized atmosphere providers
- batch sweeps with parallel execution
- checkpoint / resume
- convergence and quality reports
- benchmark workflows
- aerodynamic database export

---

## What Was Added in V2

Compared with the initial prototype, the current version includes the following major upgrades.

### 1. Dual Solver Modes: TPMC and FMF

The framework now supports two aerodynamic modes:

- **TPMC**
  - particle tracing with repeated wall interaction
  - suitable for cases where re-impact or multi-bounce behavior may matter

- **FMF**
  - first-impact-only fast mode
  - suitable for quick free-molecular screening and simple convex-body cases

The user can switch solver behavior without changing the overall workflow structure.

---

### 2. Standardized Atmosphere Interface

Atmospheric input is no longer tied to one hard-coded file format.

The current framework supports:

- **manual atmosphere input**
- **NRLMSIS text output**
- **table-based CSV atmosphere input**

This makes the platform easier to extend toward future providers such as `pymsis` or other external atmosphere sources.

---

### 3. Batch Workflow and Parallel Execution

The project now supports batch case generation and parallel execution.

Typical sweeps include:

- altitude sweep
- yaw / pitch / roll sweep
- particle-number sweep
- solver-mode sweep

The platform also supports:

- case-level parallel execution
- checkpoint / resume
- structured run folders
- automatic post-processing

---

### 4. Surface Model Framework

A per-face surface framework has been implemented.

Different regions of the spacecraft can use different:

- gas-surface interaction model
- wall temperature
- material behavior assumptions

Typical surface categories include:

- body
- solar panel
- antenna
- drag sail
- ram-facing face
- wake-facing face

---

### 5. Generic Surface Map Generator

A generic surface classification tool is included.

It can generate `face_surface_map.csv` automatically based on:

- face normal direction
- centroid position
- centroid bounding boxes
- half-space rules
- area filters

This is especially useful for CubeSat-like geometries where the general structure is repeated from mission to mission.

---

### 6. Convergence and Quality Reporting

The platform now includes automated numerical reporting features such as:

- convergence summaries
- relative-error reports
- batch result CSV files
- plots
- quality flags
- preferred-case selection for downstream database use

---

### 7. Aerodynamic Database Export

The project can now export structured aerodynamic datasets from batch runs.

This allows the user to generate:

- all-case databases
- preferred-case databases
- metadata summaries

These outputs can later be used for:

- interpolation
- mission-level analysis
- TPMC / FMF comparison
- future integration with orbit tools

---

## Version Notes

### V1
- initial STL-based TPMC prototype
- single-case execution
- basic GSI framework
- basic atmosphere import

### V2
- TPMC / FMF switchable solver modes
- standardized atmosphere provider interface
- batch manager
- checkpoint / resume
- benchmark workflow
- generic surface map generator
- convergence reports
- aerodynamic database export

---

## Solver Philosophy

This project is intended to bridge the gap between:

- a simple academic prototype, and
- a reusable engineering aerodynamic platform

The design goal is not merely to compute one coefficient once, but to generate reusable aerodynamic information for CubeSat systems in a structured and repeatable way.

---

## Overall Workflow Logic

The aerodynamic workflow can be summarized as follows.

### Step 1. Load Geometry
- import STL
- rescale geometry
- recenter geometry
- rotate according to yaw / pitch / roll

### Step 2. Assign Surface Types
- load `face_surface_map.csv`
- assign each face to a surface type
- attach local GSI and wall-temperature settings

### Step 3. Load Atmosphere
- use atmosphere provider
- obtain total density, temperature, and species number densities

### Step 4. Build Source Plane
- create upstream source plane
- sample incident particle origins on the plane

### Step 5. Sample Incident Particles
- choose gas species according to incident flux weighting
- generate inflow velocity using bulk velocity + thermal spread

### Step 6. Trace Particle
- in **TPMC**, continue through multiple reflections
- in **FMF**, stop after the first wall interaction

### Step 7. Apply Gas-Surface Interaction
- use per-face local GSI model
- compute post-collision outgoing velocity

### Step 8. Accumulate Force and Moment
- convert particle momentum exchange into force contribution
- accumulate total force and moment

### Step 9. Compute Aerodynamic Coefficients
- drag / side / lift
- moment coefficients
- save case outputs, plots, reports, and database entries

---

## Project Structure

A simplified project structure is shown below.

```text
TPMC/
├─ main.py
├─ geometry/
│  ├─ loader.py
│  ├─ transform.py
│  └─ ...
├─ physics/
│  ├─ gsi.py
│  ├─ inflow.py
│  ├─ tracer.py
│  ├─ fmf.py
│  ├─ intersect.py
│  ├─ tally.py
│  ├─ surface_model.py
│  └─ ...
├─ atmosphere/
│  ├─ __init__.py
│  ├─ base.py
│  ├─ providers.py
│  └─ factory.py
├─ tpmc_v2/
│  ├─ case_schema.py
│  ├─ case_manager.py
│  ├─ checkpoint.py
│  ├─ rotation_grid.py
│  ├─ plotter.py
│  ├─ convergence_report.py
│  ├─ benchmarks.py
│  ├─ aerodynamic_database.py
│  └─ solver_adapter.py
├─ build_surface_map_generic.py
├─ export_aero_database.py
├─ run_batch.py
├─ run_benchmarks.py
├─ run_fmf_batch.py
├─ surface_map_config.json
├─ face_surface_map.csv
└─ nrlmsis_output.txt
```

---

## Module Responsibilities

### `geometry/`
Responsible for:

- STL loading
- mesh scaling
- recentering
- geometric rotation
- bounding-box extraction

### `physics/`
Core aerodynamic physics:

- inflow sampling
- gas-surface interaction models
- ray / triangle intersection
- TPMC particle tracing
- FMF first-impact tracing
- force / moment accumulation
- aerodynamic coefficient evaluation

### `atmosphere/`
Standardized atmosphere interface:

- provider base class
- manual atmosphere provider
- NRLMSIS text provider
- table CSV provider
- factory builder

### `tpmc_v2/`
Engineering workflow layer:

- case definition
- batch manager
- checkpoint system
- plotting
- convergence report
- benchmark definitions
- aerodynamic database export

---

## TPMC vs FMF

The platform supports both TPMC and FMF because they serve different purposes.

### TPMC
TPMC is used when repeated wall interaction matters.

It is better suited for:

- more complex geometry
- possible multi-bounce trajectories
- higher-fidelity aerodynamic evaluation

### FMF
FMF is used as a fast approximation under free-molecular assumptions.

It is useful for:

- quick evaluation
- convex-body cases
- large batch sweeps
- preliminary aerodynamic screening

For simple convex geometries, FMF and TPMC may give nearly identical results.  
For concave or re-impact-sensitive geometries, the difference becomes more important.

---

## Atmosphere Interface

The current atmosphere framework supports the following provider types.

### 1. Manual Atmosphere
Useful for direct testing or controlled comparison cases.

Example:
```python
atmosphere_config = {
    "type": "manual",
    "rho_total_kg_m3": 2.3e-13,
    "temperature_K": 912.0,
    "exospheric_temperature_K": 912.0,
    "lat_deg": 55.0,
    "lon_deg": 45.0,
    "species_number_density_m3": {
        "O": 8.063e12,
        "He": 1.024e12,
        "N2": 1.211e11
    }
}
```

### 2. NRLMSIS Text Output
Useful for current mission-style rarefied atmosphere analysis.

Example:
```python
atmosphere_config = {
    "type": "nrlmsis_txt",
    "filepath": r"G:\我的雲端硬碟\TPMC\nrlmsis_output.txt",
}
```

### 3. Table CSV Provider
Useful for custom atmosphere tables or preprocessed databases.

Example:
```python
atmosphere_config = {
    "type": "table_csv",
    "filepath": r"path\to\atmosphere_table.csv",
}
```

---

## Surface Mapping

Surface classification is separated from the main solver.

### Inputs
- STL geometry
- `surface_map_config.json`

### Outputs
- `face_surface_map.csv`
- `face_surface_debug.csv`

### Supported rule types
- dominant-axis rules
- normal-cone rules
- centroid-box rules
- half-space rules
- area-range rules

This makes it possible to reuse the same solver for many CubeSat geometries while only modifying the mapping rules.

---

## Installation

### Recommended Environment
- Python 3.10+ or newer
- NumPy
- Matplotlib
- trimesh
- optional: scipy, depending on geometry processing configuration

### Basic Installation

```bash
pip install numpy matplotlib trimesh scipy
```

If you use a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install numpy matplotlib trimesh scipy
```

---

## Quick Start

### 1. Single Case Run
Edit `main.py` and set:

- geometry path
- atmosphere config
- `solver_mode = "tpmc"` or `"fmf"`

Then run:

```bash
python main.py
```

---

### 2. Generate Surface Map
Prepare `surface_map_config.json`, then run:

```bash
python build_surface_map_generic.py
```

This will generate:

- `face_surface_map.csv`
- `face_surface_debug.csv`

---

### 3. TPMC Batch Run
Run:

```bash
python run_batch.py
```

This generates:

- batch results
- plots
- convergence reports
- aerodynamic database

---

### 4. Benchmark Run
Run:

```bash
python run_benchmarks.py
```

This executes a predefined benchmark suite for regression testing.

---

### 5. FMF Batch Run
Run:

```bash
python run_fmf_batch.py
```

This generates FMF batch outputs in a separate run directory.

---

### 6. Export Aerodynamic Database
Run:

```bash
python export_aero_database.py
```

This exports standardized database files from batch outputs.

---

## Typical Output Files

### Single-case outputs
- `tpmc_stl_single_run.csv`
- `stl_single_run_fmf.csv`
- similar case-level CSV outputs

### Batch outputs
Inside folders such as:

- `runs_v2/`
- `runs_fmf_v1/`
- `runs_benchmarks/`

Typical contents include:

- `batch_results.csv`
- `case_results/*.json`
- `checkpoints/*.json`
- `plots/*.png`
- `reports/*.csv`
- `reports/*.md`
- `database/*.csv`
- `database/*.json`

---

## Aerodynamic Database

The platform can export structured aerodynamic databases containing fields such as:

- solver mode
- geometry ID
- surface model ID
- atmosphere ID
- altitude
- latitude / longitude
- yaw / pitch / roll
- particle count
- force and moment coefficients
- force components
- species densities
- convergence quality indicators

This makes the output suitable for later use in:

- aerodynamic interpolation
- system-level analysis
- CubeSat drag database generation
- TPMC / FMF comparison workflows

---

## Benchmark Philosophy

Benchmarks are used to ensure that future code updates do not silently break the platform.

The benchmark workflow is intended to support:

- regression testing
- solver validation
- TPMC / FMF comparison on controlled cases
- future extension to more complicated geometries

---

## Current Strengths

The current version is already strong in the following areas:

- reusable workflow structure
- standardized atmosphere interface
- modular solver design
- switchable TPMC / FMF modes
- automated reporting
- database-oriented output
- CubeSat-oriented surface classification logic

---

## Current Limitations

Although the platform has become much more complete, the current version still has several limitations.

### Physics and modeling limitations
- GSI parameters are still user-defined rather than fully calibrated
- wall temperature is prescribed rather than solved from thermal balance
- TPMC / FMF comparison has mainly been tested on simple benchmark geometries
- atmosphere interpolation is still basic
- surface chemistry effects are not yet modeled
- orbit propagation and SRP are outside the current aerodynamic core

### Engineering limitations
- run folders can become large if all generated outputs are kept
- dynamic load balancing inside a single large case is not yet implemented
- GitHub repository should usually track source code rather than generated run folders

---

## Future Directions

The next development stage will focus on refinement, comparison, and real-geometry application.

### 1. Real Satellite Geometry Workflow
- apply the platform to actual CubeSat STL models
- refine generic surface classification templates
- generate mission-specific aerodynamic databases

### 2. TPMC / FMF Comparison Workflow
- direct paired comparison
- quantify solver differences by altitude and attitude
- identify regimes where FMF can replace TPMC with acceptable accuracy

### 3. Better Atmosphere Support
- more flexible atmosphere providers
- improved interpolation
- easier support for external atmosphere models

### 4. Database-Oriented Engineering Workflow
- cleaner aerodynamic database schema
- easier interpolation and export
- more direct connection to orbit / ADCS tools

### 5. Improved Surface Physics
- better GSI parameter calibration
- material-specific surface models
- future thermal coupling possibilities

### 6. More Advanced Parallel Strategy
- possible future load-balancing strategy
- further scalability for large geometry or large-batch campaigns

---

## Recommended Git Tracking Policy

For a cleaner repository, it is recommended to track:

- source code
- configuration files
- small sample data
- README and documentation

And to **exclude generated run folders**, for example:

- `runs_v2/`
- `runs_fmf_v1/`
- `runs_benchmarks/`

These are reproducible outputs and usually do not need to be committed.

---
## Author

**Yu-Hsiang Chen**  
Ph.D. Student, Department of Aeronautics and Astronautics, National Cheng Kung University (NCKU)  
Research focus: rarefied aerodynamics, CubeSat aerodynamic modeling, TPMC / FMF methods, and aerodynamic database generation

---

## Maintainer

**Yu-Hsiang Chen**  
GitHub: [yushangchen](https://github.com/yushangchen)

---

## Contact

For questions, suggestions, collaboration, or bug reports, please use one of the following channels:

- GitHub Issues
- GitHub Discussions (if enabled)
- Email: `your_email_here`

---

## Citation

If you use this repository in academic work, technical reports, or derived software, please cite it as:

```text
Yu-Hsiang Chen, TPMC-SAT-AERO: A Python-based rarefied aerodynamic analysis platform for CubeSat applications, GitHub repository, 2026.


## Final Note

This project is intended to serve both as:

- a research tool for rarefied aerodynamic investigation, and
- an engineering workflow for CubeSat aerodynamic database generation

The current V2 version establishes the core platform.  
Future work will focus on solver comparison, real mission geometry, and stronger integration with system-level spacecraft analysis.

---
