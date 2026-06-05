# TPMC-Sat-Aero

**TPMC-Sat-Aero** is a Python-based **Test Particle Monte Carlo (TPMC)** code for rapid aerodynamic force and coefficient estimation of simple satellite geometries in rarefied orbital flow.

The current version is organized as a research prototype. It reads an STL geometry, applies optional scaling and attitude rotation, samples incident particles from an NRLMSIS-based atmosphere file, performs particle-surface interaction modeling, and outputs force, moment, and aerodynamic coefficients.

---

## 1. Current Project Status

This repository is currently in the **research-prototype stage**.

The present code focuses on:

- STL-based geometry loading
- Cube test-case analysis
- face-to-surface mapping
- NRLMSIS atmosphere-file input
- incident particle sampling
- particle tracing
- gas-surface interaction modeling
- aerodynamic force and moment tallying
- drag, side-force, lift, and moment coefficient output

The code is not yet packaged as an installable Python module. The present workflow is script-based.

---

## 2. Current Repository Structure

The current repository structure is:

```text
tpmc-sat-aero/
│
├── README.md
├── LICENSE
├── .gitignore
│
└── TPMC/
    │
    ├── main.py
    ├── build_cube_face_map.py
    ├── testcube.STL
    ├── face_surface_map.csv
    ├── nrlmsis_output.txt
    ├── tpmc_results.csv
    ├── tpmc_stl_single_run.csv
    ├── desktop.ini
    │
    ├── geometry/
    │   ├── loader.py
    │   ├── primitives.py
    │   ├── transform.py
    │   ├── desktop.ini
    │   └── __pycache__/
    │
    └── physics/
        ├── atmosphere_nrlmsis.py
        ├── coefficients.py
        ├── gsi.py
        ├── inflow.py
        ├── intersect.py
        ├── particle_force_contribution.py
        ├── reference.py
        ├── reflection.py
        ├── source.py
        ├── surface_model.py
        ├── tally.py
        ├── tracer.py
        ├── desktop.ini
        └── __pycache__/
```

### Folder Description

| Path | Purpose |
|---|---|
| `TPMC/main.py` | Main execution script for the STL-based TPMC single-run case |
| `TPMC/build_cube_face_map.py` | Utility script for generating a cube face-to-surface mapping CSV |
| `TPMC/testcube.STL` | Example cube geometry |
| `TPMC/face_surface_map.csv` | Face index to surface-name mapping table |
| `TPMC/nrlmsis_output.txt` | Atmospheric input data generated from NRLMSIS |
| `TPMC/tpmc_stl_single_run.csv` | Output file from the STL single-run case |
| `TPMC/geometry/` | Geometry loading, primitive handling, and attitude transformation |
| `TPMC/physics/` | Atmosphere, inflow, tracing, reflection, GSI, force, moment, and coefficient models |

---

## 3. Program Architecture

The code is divided into two major internal modules:

```text
geometry/  -> geometry loading and coordinate transformation
physics/   -> physical modeling and TPMC particle calculation
```

### 3.1 Geometry Module

The `geometry` module handles STL import, mesh scaling, mesh recentering, bounding-box evaluation, and attitude transformation.

Current files:

```text
TPMC/geometry/
├── loader.py
├── primitives.py
└── transform.py
```

Typical responsibilities:

- load STL geometry
- compute mesh normals
- compute bounding box
- recenter geometry
- scale geometry
- rotate geometry by yaw, pitch, and roll

---

### 3.2 Physics Module

The `physics` module handles atmospheric properties, inflow particle sampling, surface models, particle tracing, reflection models, force contribution, and coefficient calculation.

Current files:

```text
TPMC/physics/
├── atmosphere_nrlmsis.py
├── coefficients.py
├── gsi.py
├── inflow.py
├── intersect.py
├── particle_force_contribution.py
├── reference.py
├── reflection.py
├── source.py
├── surface_model.py
├── tally.py
└── tracer.py
```

Typical responsibilities:

- read NRLMSIS atmosphere data
- select atmospheric state at target altitude
- sample species from atmospheric composition
- compute incident molecular flux
- generate source-plane particles
- trace particles toward the geometry
- handle particle-surface interaction
- compute force and moment contribution
- compute aerodynamic coefficients

---

## 4. Physical Model

The present TPMC model assumes a rarefied orbital flow condition where intermolecular collisions are negligible.

The basic assumptions are:

1. Gas molecules are represented by sampled test particles.
2. Incoming particles are sampled from a source plane upstream of the body.
3. Particles move in straight lines before impact.
4. Particle-surface interaction is modeled through the gas-surface interaction model.
5. Total force and moment are obtained by summing momentum exchange from all sampled particles.
6. Aerodynamic coefficients are calculated from the accumulated force and moment.

The drag coefficient is defined as:

```math
C_D = \frac{F_D}{q_\infty A_{ref}}
```

where:

```math
q_\infty = \frac{1}{2}\rho_\infty V_\infty^2
```

and:

- `F_D` is the drag force
- `rho_inf` is the atmospheric mass density
- `V_inf` is the free-stream velocity
- `A_ref` is the reference area

---

## 5. Gas-Surface Interaction

The current code supports surface-dependent gas-surface interaction settings through the surface model.

The surface model is built in `main.py` by the function:

```python
build_surface_model(face_map_csv)
```

In the current cube test case, different cube faces can be assigned different surface names:

```text
x_minus
x_plus
y_minus
y_plus
z_minus
z_plus
default
```

These surface names are connected to gas-surface interaction models such as:

```text
diffuse
cll
```

The face-to-surface relationship is stored in:

```text
TPMC/face_surface_map.csv
```

---

## 6. Input Files

The current workflow uses three major input files:

```text
TPMC/testcube.STL
TPMC/nrlmsis_output.txt
TPMC/face_surface_map.csv
```

### 6.1 STL Geometry

Current example geometry:

```text
TPMC/testcube.STL
```

The geometry is loaded in `main.py` through:

```python
stl_path = r"G:\我的雲端硬碟\TPMC\testcube.stl"
```

Before running the code on a different computer, this path must be changed to the local path of the STL file.

Example relative-path version:

```python
stl_path = r"testcube.STL"
```

or:

```python
stl_path = str(Path(__file__).resolve().parent / "testcube.STL")
```

---

### 6.2 NRLMSIS Atmosphere File

Current atmosphere input file:

```text
TPMC/nrlmsis_output.txt
```

The file is read in `main.py` through:

```python
atmosphere_path = r"G:\我的雲端硬碟\TPMC\nrlmsis_output.txt"
```

Before running on a different computer, change it to:

```python
atmosphere_path = r"nrlmsis_output.txt"
```

or:

```python
atmosphere_path = str(Path(__file__).resolve().parent / "nrlmsis_output.txt")
```

---

### 6.3 Face Surface Map

Current face-surface map:

```text
TPMC/face_surface_map.csv
```

The file maps each STL face index to a surface name.

Example format:

```csv
face_index,surface_name
0,x_minus
1,x_minus
2,x_plus
3,x_plus
```

In `main.py`, the current hard-coded path is:

```python
face_map_csv = r"G:\我的雲端硬碟\TPMC\face_surface_map.csv"
```

Before running on a different computer, change it to:

```python
face_map_csv = r"face_surface_map.csv"
```

or:

```python
face_map_csv = str(Path(__file__).resolve().parent / "face_surface_map.csv")
```

---

## 7. Installation

### 7.1 Clone the Repository

```bash
git clone https://github.com/yushangchen/tpmc-sat-aero.git
cd tpmc-sat-aero
```

### 7.2 Create a Python Virtual Environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

#### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 7.3 Install Required Packages

The current code uses common scientific Python packages.

Install the basic packages:

```bash
pip install numpy scipy pandas matplotlib trimesh
```

If additional packages are required by later versions, install them according to the import error message.

A recommended `requirements.txt` can be generated by:

```bash
pip freeze > requirements.txt
```

---

## 8. How to Run the Current Code

The current version is script-based. The main working directory should be:

```text
tpmc-sat-aero/TPMC/
```

Move into the TPMC folder:

```bash
cd TPMC
```

---

### 8.1 Step 1: Check or Generate the Face Surface Map

If `face_surface_map.csv` already exists, this step can be skipped.

To regenerate the cube face-surface map:

```bash
python build_cube_face_map.py
```

This script reads the cube STL file, classifies each face according to its surface normal direction, and writes:

```text
face_surface_map.csv
```

The generated surface names are:

```text
x_minus
x_plus
y_minus
y_plus
z_minus
z_plus
```

---

### 8.2 Step 2: Edit User Settings in `main.py`

Open:

```text
TPMC/main.py
```

Find the section:

```python
# ===== user settings =====
```

Edit the following parameters:

```python
stl_path = r"G:\我的雲端硬碟\TPMC\testcube.stl"
atmosphere_path = r"G:\我的雲端硬碟\TPMC\nrlmsis_output.txt"
face_map_csv = r"G:\我的雲端硬碟\TPMC\face_surface_map.csv"

target_alt_km = 500.0
scale_factor = 0.001

yaw_deg = 0.0
pitch_deg = 0.0
roll_deg = 0.0

n_particles = 50000
seed = 42
```

For GitHub users, it is recommended to change the three file paths to local relative paths:

```python
base_dir = Path(__file__).resolve().parent

stl_path = str(base_dir / "testcube.STL")
atmosphere_path = str(base_dir / "nrlmsis_output.txt")
face_map_csv = str(base_dir / "face_surface_map.csv")
```

---

### 8.3 Step 3: Edit Reference Quantities

In `main.py`, edit:

```python
ref = ReferenceConfig(
    A_ref=1.0e-4,
    L_ref=1.0e-2,
    ref_point_body=np.array([0.0, 0.0, 0.0]),
    drag_axis_body=np.array([1.0, 0.0, 0.0]),
    side_axis_body=np.array([0.0, 1.0, 0.0]),
    lift_axis_body=np.array([0.0, 0.0, 1.0]),
)
```

Meaning:

| Parameter | Meaning |
|---|---|
| `A_ref` | Reference area |
| `L_ref` | Reference length |
| `ref_point_body` | Moment reference point in body coordinates |
| `drag_axis_body` | Drag-axis direction in body coordinates |
| `side_axis_body` | Side-force-axis direction in body coordinates |
| `lift_axis_body` | Lift-axis direction in body coordinates |

For the current cube example:

```python
A_ref = 1.0e-4
L_ref = 1.0e-2
```

which corresponds to a 10 mm × 10 mm reference area and a 10 mm reference length.

---

### 8.4 Step 4: Edit Free-Stream Velocity

The current free-stream bulk velocity is defined as:

```python
bulk_velocity_world = np.array([7500.0, 0.0, 0.0])
```

This means the incoming gas flow is aligned with the positive x-direction in the world frame.

The magnitude is:

```text
7500 m/s
```

---

### 8.5 Step 5: Run the Main TPMC Simulation

Run:

```bash
python main.py
```

The terminal will print:

```text
=== STL TPMC Single Run (NRLMSIS Atmosphere + Surface Model) ===
```

and show:

- selected atmosphere altitude
- surface model information
- particle hit ratio
- bounce count
- geometry size
- atmospheric density
- temperature
- species number densities
- force components
- moment components
- aerodynamic coefficients

---

## 9. Output

The current main script writes:

```text
TPMC/tpmc_stl_single_run.csv
```

This output includes:

- STL path
- atmosphere path
- target altitude
- selected atmosphere altitude
- scale factor
- attitude angle
- particle number
- hit count
- hit ratio
- total bounces
- average bounces per hit
- bounding-box size
- source-plane area
- force components
- moment components
- atmospheric density
- dynamic pressure
- reference area
- reference length
- drag force
- side force
- lift force
- drag coefficient
- side-force coefficient
- lift coefficient
- moment coefficients
- species number densities

Important output columns include:

```text
Fx, Fy, Fz
Mx, My, Mz
F_drag, F_side, F_lift
Cd, Cy, Cl
Cmx, Cmy, Cmz
rho_inf, T_inf, q_inf
n_O, n_N2, n_O2, n_He, n_Ar, n_H, n_N
```

---

## 10. Typical Current Workflow

The present recommended workflow is:

```text
1. Put STL file into TPMC folder.
2. Prepare or update nrlmsis_output.txt.
3. Generate face_surface_map.csv if needed.
4. Edit file paths in main.py.
5. Set target altitude.
6. Set attitude angles.
7. Set reference area and reference length.
8. Set number of particles.
9. Run main.py.
10. Check terminal output.
11. Open tpmc_stl_single_run.csv.
12. Repeat with different altitude, attitude, or particle number.
```

---

## 11. Particle-Number Convergence Test

For scientific use, the number of TPMC particles should be tested.

Suggested particle numbers:

```text
10000
50000
100000
500000
1000000
```

Change:

```python
n_particles = 50000
```

to different values and run:

```bash
python main.py
```

Compare the resulting drag coefficient:

```text
Cd
```

A practical convergence criterion is:

```math
\left|
\frac{C_D(N) - C_D(2N)}
{C_D(2N)}
\right| < 1\%
```

---

## 12. Altitude Sweep

The current code performs one altitude per run.

To perform an altitude sweep manually:

1. Open `main.py`.
2. Change:

```python
target_alt_km = 500.0
```

3. Run:

```bash
python main.py
```

4. Save or rename the output CSV.
5. Repeat for another altitude.

Suggested altitude points:

```text
125 km
150 km
185 km
200 km
250 km
300 km
450 km
500 km
```

Future versions may include an automatic altitude-sweep script.

---

## 13. Attitude Sweep

The current attitude is controlled by:

```python
yaw_deg = 0.0
pitch_deg = 0.0
roll_deg = 0.0
```

To perform an attitude sweep manually, change these values and rerun:

```bash
python main.py
```

Example cases:

| Case | yaw | pitch | roll |
|---|---:|---:|---:|
| Case 000 | 0 | 0 | 0 |
| Case yaw30 | 30 | 0 | 0 |
| Case pitch30 | 0 | 30 | 0 |
| Case roll30 | 0 | 0 | 30 |

Future versions may include an automatic attitude-sweep script.

---

## 14. Important Notes for Current Version

### 14.1 Hard-Coded Paths

The current version of `main.py` uses hard-coded local Windows paths.

Before another user can run the code, the paths must be changed.

Recommended improvement:

```python
base_dir = Path(__file__).resolve().parent

stl_path = str(base_dir / "testcube.STL")
atmosphere_path = str(base_dir / "nrlmsis_output.txt")
face_map_csv = str(base_dir / "face_surface_map.csv")
```

### 14.2 `desktop.ini` and `__pycache__`

The repository currently contains files that are usually not needed for source-code sharing:

```text
desktop.ini
__pycache__/
```

It is recommended to remove these from the repository and keep them ignored by `.gitignore`.

Recommended `.gitignore` entries:

```gitignore
__pycache__/
*.pyc
desktop.ini
.venv/
*.log
```

### 14.3 Case Configuration

The current version does not yet use an external YAML or JSON configuration file.

Simulation settings are currently edited directly in:

```text
TPMC/main.py
```

Future versions may move these settings into:

```text
config.yaml
```

or:

```text
config.json
```

---

## 15. Known Limitations

The current version has the following limitations:

- Script-based workflow.
- File paths are still hard-coded in `main.py`.
- No automatic parameter sweep script yet.
- No formal package installation.
- No external configuration file yet.
- No unit-test framework yet.
- No automatic DSMC comparison yet.
- No graphical post-processing script yet.
- TPMC does not model intermolecular collisions.
- Accuracy decreases when the flow enters the transitional regime.

---

## 16. Future Development Plan

Planned future improvements include:

- Replace hard-coded paths with relative paths.
- Add `requirements.txt`.
- Add automatic altitude sweep.
- Add automatic attitude sweep.
- Add particle-number convergence script.
- Add result plotting scripts.
- Add configuration-file input.
- Add example cases.
- Add DSMC reference comparison.
- Add more gas-surface interaction models.
- Add GPU or C++ acceleration for particle tracing.
- Add documentation for equations and validation.

---

## 17. Suggested Citation

If you use this code in academic work, please cite:

```text
Chen, Y.-H. TPMC-Sat-Aero: A Python-based Test Particle Monte Carlo Tool for Satellite Aerodynamic Coefficient Estimation. GitHub repository, 2026.
```

BibTeX:

```bibtex
@misc{chen2026tpmcsataero,
  author       = {Chen, Yu-Hsiang},
  title        = {TPMC-Sat-Aero: A Python-based Test Particle Monte Carlo Tool for Satellite Aerodynamic Coefficient Estimation},
  year         = {2026},
  howpublished = {\url{https://github.com/yushangchen/tpmc-sat-aero}},
  note         = {GitHub repository}
}
```

---

## 18. Author

**Yu-Hsiang Chen**  
Department of Aeronautics and Astronautics  
National Cheng Kung University  
Taiwan

Research interests:

- Rarefied gas dynamics
- TPMC and DSMC methods
- Satellite aerodynamics
- CubeSat deorbit analysis
- Experimental fluid mechanics

---

## 19. License

This project is released under the MIT License.

See the `LICENSE` file for details.

---

## 20. Disclaimer

This code is developed for academic and research purposes.

The results should be verified before being used for engineering design, mission analysis, or publication. For transitional rarefied flows or low-altitude orbital conditions, DSMC or other higher-fidelity methods should be used for validation.
