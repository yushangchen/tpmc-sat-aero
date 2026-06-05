# TPMC-Sat-Aero

**TPMC-Sat-Aero** is a Python-based **Test Particle Monte Carlo (TPMC)** solver for rapid aerodynamic coefficient estimation of satellites, CubeSats, and deorbit drag-sail configurations in rarefied orbital flow conditions.

The solver is intended for **free-molecular** and **high-Knudsen-number** regimes, where intermolecular collisions are negligible and gas-surface interactions dominate the aerodynamic force. It tracks incident test particles, computes gas-surface momentum exchange, and estimates aerodynamic force, moment, and drag coefficients for arbitrary triangulated geometries.

This project is designed as a research-oriented tool for preliminary satellite aerodynamic analysis and future comparison with **Direct Simulation Monte Carlo (DSMC)** reference simulations.

---

## 1. Project Motivation

Aerodynamic drag is one of the dominant perturbation forces for satellites in Low Earth Orbit (LEO), especially for CubeSats, drag-sail systems, and very-low-Earth-orbit missions.

A common assumption in preliminary orbital lifetime analysis is to use a constant drag coefficient, such as:

```math
C_D = 2.2
```

However, the actual aerodynamic coefficient depends on:

- satellite geometry,
- attitude angle,
- gas-surface interaction model,
- atmospheric density and composition,
- orbital altitude,
- molecular speed ratio,
- Knudsen number,
- surface reflection properties.

DSMC can provide accurate rarefied-flow simulations but is computationally expensive. TPMC provides a faster alternative in the free-molecular regime by neglecting intermolecular collisions and focusing on particle-surface interactions.

The goal of this project is to provide a fast and flexible TPMC-based workflow for estimating aerodynamic coefficients and preparing reference cases for DSMC comparison.

---

## 2. Main Features

- Import arbitrary satellite geometry from STL files.
- Support triangulated surface meshes.
- Generate incoming test particles based on free-stream flow conditions.
- Compute particle-surface intersections.
- Model gas-surface momentum exchange.
- Support diffuse and specular reflection models.
- Estimate aerodynamic force and moment.
- Compute drag coefficient.
- Perform particle-number convergence tests.
- Export force, moment, coefficient, and particle-hit statistics.
- Suitable for CubeSat, drag-sail, and simplified spacecraft configurations.
- Designed for future DSMC reference validation.

The drag coefficient is defined as:

```math
C_D = \frac{F_D}{\frac{1}{2}\rho V_\infty^2 A_{ref}}
```

where:

- `F_D` is the aerodynamic force component opposite to the free-stream direction,
- `rho` is the atmospheric mass density,
- `V_inf` is the free-stream velocity,
- `A_ref` is the reference area.

---

## 3. Physical Assumptions

The current TPMC model is based on the following assumptions:

1. The flow is in the free-molecular or high-Knudsen-number regime.
2. Intermolecular collisions are neglected.
3. Test particles travel in straight-line trajectories before surface collision.
4. Gas-surface interaction dominates the momentum exchange.
5. The satellite geometry is treated as a triangulated surface mesh.
6. The incident flow is uniform.
7. The wall temperature is prescribed.
8. The aerodynamic coefficients are obtained from statistical averaging over many test particles.

This method is suitable when:

```math
Kn = \frac{\lambda}{L} \gg 1
```

where `lambda` is the molecular mean free path and `L` is the characteristic length of the satellite.

---

## 4. TPMC and DSMC Comparison Philosophy

TPMC and DSMC use different particle concepts.

In DSMC, one simulator particle represents many real gas molecules and the method includes molecular collisions inside computational cells.

In TPMC, particles are sampling particles used to estimate the momentum exchange between incoming gas molecules and the satellite surface.

Therefore, TPMC and DSMC should not be compared using identical particle numbers. Instead, both methods should be compared under identical physical conditions after each method has reached its own convergence criterion.

Recommended comparison procedure:

1. Use the same geometry.
2. Use the same atmospheric condition.
3. Use the same free-stream velocity.
4. Use the same attitude angle.
5. Use the same gas-surface interaction model.
6. Run TPMC particle-number convergence.
7. Run DSMC reference simulations at selected altitudes.
8. Compare the converged aerodynamic coefficients.

The relative difference can be evaluated as:

```math
\eta =
\frac{C_{D,\mathrm{TPMC}} - C_{D,\mathrm{DSMC}}}
{C_{D,\mathrm{DSMC}}}
\times 100\%
```

---

## 5. Recommended Repository Structure

The recommended repository structure is:

```text
tpmc-sat-aero/
│
├── README.md
├── LICENSE
├── requirements.txt
├── .gitignore
│
├── src/
│   └── tpmc_sat_aero/
│       ├── __init__.py
│       ├── main.py
│       ├── geometry.py
│       ├── particle.py
│       ├── surface.py
│       ├── gas_surface.py
│       ├── solver.py
│       ├── coefficients.py
│       └── utils.py
│
├── cases/
│   ├── cube_basic/
│   │   ├── config.yaml
│   │   └── geometry.stl
│   │
│   └── drag_sail/
│       ├── config.yaml
│       └── geometry.stl
│
├── examples/
│   ├── run_cube.py
│   ├── run_drag_sail.py
│   ├── convergence_test.py
│   ├── altitude_sweep.py
│   └── attitude_sweep.py
│
├── results/
│   └── README.md
│
└── docs/
    ├── methodology.md
    └── theory.md
```

If the current code structure is different, users can still follow the same workflow by modifying the paths in the configuration file.

---

## 6. Installation

### 6.1 Clone the Repository

```bash
git clone https://github.com/your-username/tpmc-sat-aero.git
cd tpmc-sat-aero
```

Replace `your-username` with your actual GitHub username.

---

### 6.2 Create a Python Virtual Environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run:

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

---

### 6.3 Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` has not been created yet, install the basic packages manually:

```bash
pip install numpy scipy pandas matplotlib trimesh pyyaml tqdm
```

Then generate `requirements.txt`:

```bash
pip freeze > requirements.txt
```

---

## 7. Input Files

A typical case requires two main input files:

1. Geometry file
2. Configuration file

---

### 7.1 Geometry File

The geometry should be provided as an STL file:

```text
geometry.stl
```

The STL file should satisfy the following requirements:

- The geometry should be watertight if possible.
- Surface normals should be consistently oriented.
- The geometry should be in SI units, preferably meters.
- The model should be centered around the intended reference point.
- Very small gaps or duplicated surfaces should be avoided.
- The reference area should be defined separately in the configuration file.

Example:

```text
cases/cube_basic/geometry.stl
```

---

### 7.2 Configuration File

The simulation settings are defined in a YAML file:

```text
config.yaml
```

Example:

```yaml
case_name: cube_basic

geometry:
  file: cases/cube_basic/geometry.stl
  length_unit: m
  reference_area: 0.01
  reference_length: 0.1
  center_of_mass: [0.0, 0.0, 0.0]

flow:
  altitude_km: 300
  density: 1.92e-11
  temperature: 976.0
  velocity: 7730.0
  direction: [-1.0, 0.0, 0.0]

gas:
  species: atomic_oxygen
  molecular_mass: 2.656e-26
  number_density: 6.51e14

surface:
  wall_temperature: 350.0
  reflection_model: diffuse
  accommodation_coefficient: 1.0
  diffuse_fraction: 1.0

simulation:
  number_of_particles: 100000
  random_seed: 42
  batch_size: 10000

output:
  directory: results/cube_basic
  save_particle_hits: true
  save_force_history: true
  save_summary_csv: true
```

---

## 8. Running a Simulation

### 8.1 Run a Basic Example

If the repository contains example scripts:

```bash
python examples/run_cube.py
```

or:

```bash
python examples/run_drag_sail.py
```

---

### 8.2 Run with a Configuration File

If the main solver supports command-line execution:

```bash
python src/tpmc_sat_aero/main.py --config cases/cube_basic/config.yaml
```

For a drag-sail case:

```bash
python src/tpmc_sat_aero/main.py --config cases/drag_sail/config.yaml
```

---

### 8.3 Recommended Workflow

The recommended TPMC workflow is:

```text
1. Prepare STL geometry.
2. Check geometry unit and orientation.
3. Define reference area and reference length.
4. Prepare atmospheric and flow conditions.
5. Define gas-surface interaction model.
6. Run a small particle-number test.
7. Run a full simulation.
8. Check force and coefficient convergence.
9. Export aerodynamic coefficients.
10. Compare with DSMC or analytical free-molecular results.
```

---

## 9. Output Files

A typical simulation will generate the following files:

```text
results/
└── cube_basic/
    ├── summary.csv
    ├── force_history.csv
    ├── moment_history.csv
    ├── coefficients.csv
    ├── particle_hits.csv
    └── convergence.png
```

---

### 9.1 Summary Output

Example `summary.csv`:

```csv
case_name,altitude_km,num_particles,Cd,Cl,Cy,Fx,Fy,Fz,Mx,My,Mz
cube_basic,300,100000,2.15,0.01,0.00,1.23e-6,2.0e-9,1.1e-8,0.0,0.0,0.0
```

---

### 9.2 Force Output

Example `force_history.csv`:

```csv
particle_count,Fx,Fy,Fz
10000,1.20e-6,2.3e-9,1.0e-8
20000,1.22e-6,2.1e-9,1.2e-8
30000,1.23e-6,2.0e-9,1.1e-8
```

---

### 9.3 Coefficient Output

The drag coefficient is computed as:

```math
C_D = \frac{F_D}{\frac{1}{2}\rho V_\infty^2 A_{ref}}
```

The drag force can be computed as:

```math
F_D =
\frac{1}{2}
\rho V_\infty^2 A_{ref} C_D
```

---

## 10. Particle-Number Convergence Test

Before using the result for scientific discussion, a particle-number convergence test is recommended.

Example particle numbers:

```text
1e4
5e4
1e5
5e5
1e6
```

Run:

```bash
python examples/convergence_test.py --config cases/cube_basic/config.yaml
```

or manually modify the `number_of_particles` value in `config.yaml`.

The convergence criterion can be defined as:

```math
\left|
\frac{C_D(N) - C_D(2N)}
{C_D(2N)}
\right| < 1\%
```

A suggested convergence table is:

| Number of particles | Drag coefficient | Difference |
|---:|---:|---:|
| 10,000 | 2.18 | - |
| 50,000 | 2.14 | 1.83% |
| 100,000 | 2.13 | 0.47% |
| 500,000 | 2.12 | 0.47% |
| 1,000,000 | 2.12 | 0.00% |

If the drag coefficient changes by less than 1%, the result can be considered statistically converged for preliminary aerodynamic analysis.

---

## 11. Altitude Sweep

For LEO satellite applications, TPMC can be used to rapidly evaluate aerodynamic coefficients at different altitudes.

Example altitude range:

```text
150 km to 500 km
```

Suggested interval:

```text
5 km or 10 km
```

Example workflow:

```bash
python examples/altitude_sweep.py --config cases/cube_basic/config.yaml --start 150 --end 500 --step 10
```

The output may include:

```text
results/altitude_sweep/Cd_vs_altitude.csv
results/altitude_sweep/Cd_vs_altitude.png
```

The final result can be used to build an altitude-dependent aerodynamic coefficient model:

```math
C_D = C_D(h)
```

which can be used for orbital lifetime prediction.

---

## 12. Attitude Sweep

The aerodynamic coefficient of a satellite depends strongly on attitude.

Example attitude angles:

```text
alpha = 0, 30, 60 deg
beta  = 0, 30, 60 deg
```

Suggested cases:

| Case | Angle of attack alpha | Sideslip angle beta |
|---|---:|---:|
| Case 00 | 0 deg | 0 deg |
| Case 03 | 0 deg | 30 deg |
| Case 06 | 0 deg | 60 deg |
| Case 30 | 30 deg | 0 deg |
| Case 33 | 30 deg | 30 deg |
| Case 36 | 30 deg | 60 deg |
| Case 60 | 60 deg | 0 deg |
| Case 63 | 60 deg | 30 deg |
| Case 66 | 60 deg | 60 deg |

Example command:

```bash
python examples/attitude_sweep.py --config cases/cube_basic/config.yaml
```

The output can be used to generate:

```text
Cd(alpha, beta)
Cl(alpha, beta)
Cm(alpha, beta)
```

---

## 13. DSMC Reference Validation

This project is intended to support future TPMC-DSMC comparison.

A recommended validation strategy is:

1. Run TPMC at many altitude points.
2. Run DSMC only at selected reference altitudes.
3. Compare converged aerodynamic coefficients.
4. Identify the altitude or Knudsen-number range where TPMC remains valid.

Example DSMC reference altitudes:

```text
125 km
150 km
185 km
200 km
250 km
300 km
450 km
```

The relative difference can be calculated as:

```math
\eta =
\frac{C_{D,\mathrm{TPMC}} - C_{D,\mathrm{DSMC}}}
{C_{D,\mathrm{DSMC}}}
\times 100\%
```

The comparison should be based on converged aerodynamic coefficients, not on identical particle numbers.

---

## 14. Example Research Use Case

A typical research use case is:

```text
Objective:
Estimate the drag coefficient of a CubeSat with and without a deployed drag sail.

Method:
1. Import CubeSat STL geometry.
2. Define orbital altitude and atmospheric conditions.
3. Run TPMC particle-number convergence.
4. Compute Cd for the no-sail case.
5. Compute Cd for the deployed-sail case.
6. Compare the increase in drag force.
7. Select several altitudes for DSMC reference validation.
8. Use Cd(h) for orbital lifetime analysis.
```

---

## 15. Known Limitations

The current TPMC solver has the following limitations:

- It does not model intermolecular collisions.
- It is not suitable for dense transitional flows.
- It does not solve the full Boltzmann equation.
- Accuracy decreases when the Knudsen number becomes small.
- Complex multiple reflections may require sufficient particle sampling.
- The result depends on the gas-surface interaction model.
- Surface roughness, contamination, and material properties are not fully modeled unless specified.
- Thermal re-emission models may need further development.

For transitional flow regimes, DSMC should be used as a reference or replacement method.

---

## 16. Recommended Validity Range

TPMC is generally suitable for:

```math
Kn \gg 1
```

It may still be useful as a preliminary estimator when:

```math
Kn > 10
```

For:

```math
0.1 < Kn < 10
```

DSMC is recommended because intermolecular collisions become important.

For:

```math
Kn < 0.1
```

continuum or slip-flow methods may be more appropriate, depending on the flow condition.

---

## 17. Troubleshooting

### Problem 1: STL file cannot be loaded

Possible causes:

- Wrong file path.
- STL file is corrupted.
- STL file uses unexpected units.
- Required package `trimesh` is not installed.

Try:

```bash
pip install trimesh
```

Check the geometry path in `config.yaml`.

---

### Problem 2: The drag coefficient is extremely large or small

Possible causes:

- Wrong reference area.
- Wrong density.
- Wrong velocity.
- Geometry unit is incorrect.
- Flow direction is incorrectly defined.
- Surface normals are inconsistent.

Check:

```yaml
geometry:
  reference_area: 0.01
  length_unit: m

flow:
  density: 1.92e-11
  velocity: 7730.0
  direction: [-1.0, 0.0, 0.0]
```

---

### Problem 3: Result changes strongly with particle number

Possible causes:

- Too few particles.
- Complex geometry causes low hit rate.
- Insufficient sampling of multiple reflections.
- Large concave regions require more particles.

Try increasing:

```yaml
simulation:
  number_of_particles: 1000000
```

---

### Problem 4: The simulation is slow

Possible solutions:

- Reduce particle number for preliminary tests.
- Use batch processing.
- Simplify the STL geometry.
- Remove unnecessary small geometric features.
- Use vectorized intersection routines.
- Consider future acceleration using C++, Numba, or GPU.

---

## 18. Development Plan

Planned future developments include:

- DSMC reference-case comparison.
- Altitude-dependent aerodynamic coefficient database.
- Attitude-dependent force and moment database.
- Improved gas-surface interaction models.
- Support for mixed atmospheric species.
- Multiple-reflection tracking.
- GPU acceleration.
- C++ backend for particle tracing.
- Coupling with orbital decay analysis.
- Validation against published DSMC and free-molecular-flow results.

---

## 19. Citation

If you use this code in academic work, please cite this repository.

Recommended citation format:

```text
Chen, Y.-H. TPMC-Sat-Aero: A Test Particle Monte Carlo Tool for Satellite Aerodynamic Coefficient Estimation. GitHub repository, 2026.
```

BibTeX:

```bibtex
@misc{chen2026tpmcsataero,
  author       = {Chen, Yu-Hsiang},
  title        = {TPMC-Sat-Aero: A Test Particle Monte Carlo Tool for Satellite Aerodynamic Coefficient Estimation},
  year         = {2026},
  howpublished = {\url{https://github.com/your-username/tpmc-sat-aero}},
  note         = {GitHub repository}
}
```

---

## 20. License

This project is released under the MIT License.

Users are allowed to use, modify, and distribute the code, provided that the original copyright notice and license are retained.

See the `LICENSE` file for details.

---

## 21. Author

**Yu-Hsiang Chen**  
Department of Aeronautics and Astronautics  
National Cheng Kung University  
Taiwan

Research interests:

- Rarefied gas dynamics
- DSMC and TPMC methods
- Satellite aerodynamics
- CubeSat deorbit analysis
- Experimental fluid mechanics
- Bluff-body aerodynamics

---

## 22. Disclaimer

This code is developed for academic and research purposes. The results should be verified carefully before being used for engineering design, mission analysis, or publication.

For transitional rarefied flows or low-altitude orbital conditions, DSMC or other higher-fidelity methods should be used for validation.
