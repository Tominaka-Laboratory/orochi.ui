instruction = """
# General Instruction
## Instruction for Simulation:

1.  On the "**Files Tab**", under "Load data files", upload your **structure file** (e.g., "Ni.cif") to the `orochi.phase` module.
2.  Navigate to the "**Structure Tab**", then click "**Make Structure**" to apply the changes and update the displayed structure information.
3.  Click "**Refresh GUI**" to ensure all parameters and the 3D viewer are updated.
4.  Navigate to the "**Simulation Tab**" and adjust the desired **simulation parameters**.
5.  Click "**Simulate**" to run the PDF simulation and view the results.

---

## Instruction for Least Squares Fitting:

To perform a least squares fit, first complete steps **1-4** from the Simulation instructions above.

6.  On the "**Files Tab**", under "Load data files", upload your experimental **data file** (e.g., "Ni.gr") containing the G(r) data to the `least squares` module.
7.  Go to the "**Least Squares Tab**". **Select the parameters you wish to fit** by checking their corresponding boxes.
8.  Adjust any other **fitting parameters** on the "**Least Squares Tab**" as needed.
9.  Click "**Fit**" to start the least squares optimization process.

---

## Instruction for Bayesian Optimization:

To perform Bayesian optimization, first complete steps **1-4** from the Simulation instructions.

10. On the "**Files Tab**", under "Load data files", upload your experimental **data file** (e.g., "Ni.gr") containing the G(r) data to the `bayesian optimization` module.
11. Navigate to the "**Bayesian Optimization Tab**". **Select the parameters you wish to optimize** by checking their corresponding boxes.
12. Adjust any other **optimization parameters** on the "**Bayesian Optimization Tab**".
13. Click "**Fit**" to begin the Bayesian optimization.
14. To monitor the optimization progress and view detailed results, click "**Dashboard**" to open the Optuna dashboard in your web browser.

---

## Instruction for Saving & Loading Parameters:

The "**Files Tab**" allows you to manage the parameters of your Orochi modules.

* To **save** the current parameters of any Orochi module (e.g., phase, simulation, least squares, bayesian optimization), simply click the **"Save JSON Param Files" button** corresponding to that module. This will save the parameters to a JSON file in your **work directory**.
* To **load** previously saved parameters, under "Load JSON Param Files", click the **"File" input** corresponding to the module you want to update. Select the JSON parameter file from your computer to load its settings into the module.
"""

files = """
# Tips
This tab lets you load files into or save files from various Orochi modules.

* The **"Study Name"** defines a common identifier for your work, often used as a sample name.
* The **"Work Directory"** specifies the location for saving output files, such as execution logs.
* Orochi parameters can be **saved** as JSON files for each module. The **"Load JSON Param Files"** option allows you to import these saved settings, making it easy to resume or repeat experiments.
* Upload your **structure information** (e.g., `.cif` files) to the `orochi.phase` module to construct your model.
* For **fitting**, upload your **experimental data** (e.g., `.gr` files) to either the `least squares` or `bayesian optimization` modules.
"""

structure ="""
# Tips
This tab centralizes the structural information used for simulations.

Internally, Orochi manages the structure using its asymmetric unit (the smallest repeating unit). You can build a complete model based on your conditions by clicking the "**Make Structure**" button.

When making a structure, you can choose from the following constraints:
* **Spherical constraints**: Determine if the shape should be spherical (rather than spheroidal).
* **Lattice constraints**: Maintain the crystallographic lattice system.
* **Symmetry constraints**: Apply space group symmetry rules.

After making changes, click the "**Refresh GUI**" button to update the graphical interface.

You can set each variable's value, its **fitting range** (min & max), and enable/disable **fitting** using the checkbox.
"""

simulation = """
# Tips
This tab is for performing PDF simulations. It's highly recommended to review the simulator settings here before running a least squares fit.

The simulation uses the structural information defined in the "Structure Tab." The "**Refresh GUI**" button is useful for updating the GUI after an optimization run, but it's not necessary for just running a simulation.

* **rmin, rmax, rstep**: Define the simulation range and step size.
* **scale**: The intensity scaling parameter, typically set to 1.
* **qdamp, qbroad, delta1, delta2**: These are parameters consistent with those used in the PDFfit2 program, influencing the PDF broadening and peak shapes.
"""

least_squares = r"""
# Tips
This tab allows you to perform bounded least-squares fitting of PDF data.

It uses the structural information from the "Structure Tab" and simulation parameters from the "Simulation Tab" to define the forward simulation model. This model is fitted against experimental *G*(*r*) data using the bounded Levenberg-Marquardt / Trust Region Reflective algorithm.

* Key metrics (*R*<sub>w</sub>, *R*², reduced χ²) and refined parameter values (with ±1σ uncertainties) are reported directly on this tab after fitting.
* Full diagnostic reports and covariance details are available under the "Optimization Diagnostics" section.
"""

bayes = r"""
# Tips
This tab is for performing Bayesian optimization of structural and experimental parameters.

It uses Tree-Structured Parzen Estimator (TPE) sampling to globally explore parameter spaces without getting trapped in local minima.

* **n_trials**: Number of optimization trials (typically 100–500 for initial exploration).
* **n_jobs**: Number of parallel worker threads.
* Click **"Dashboard"** to launch the interactive Optuna web dashboard to inspect hyperparameter importance and objective histories.
* For Rietveld-grade convergence, you can follow Bayesian optimization with a least-squares fit.
"""

pixia = r"""
# Tips (`orochi.pixia` — 2D Image Integration)
This tab converts 2D X-ray detector images (TIFF, FPD, Imaging Plate) into 1D powder diffraction profiles *I*(2θ) and propagates the synthetic dummy-frame baseline *B*<sub>det</sub>(2θ).

* **rambda / energy**: Incident X-ray wavelength (Å) and photon energy (keV).
* **x0, y0, distance, tiltx, tilty**: Beam center coordinates (pixels), sample-to-detector distance (mm), and detector tilt angles (deg).
* **ttmin, ttmax, ttstep**: 1D azimuthal integration 2θ range and step size (deg).
* **outlier**: Relative threshold for rejecting single-crystal spots, cosmic rays, and defective pixels.
* Click **"Integrate 2D -> 1D"** to perform pixel corrections and azimuthal integration, or **"Calibrate Geometry"** to refine detector parameters against a standard ring pattern.
"""

pdfget = r"""
# Tips (`orochi.pdfget` — Total Scattering to PDF Reduction)
This tab transforms 1D total scattering profiles *I*(2θ) into the Faber-Ziman structure factor *S*(*Q*), reduced structure factor *F*(*Q*), and atomic pair distribution function *G*(*r*).

* **composition**: Chemical formula (e.g., `Ni`, `CeO2`, `RuO2`) used to evaluate atomic form factors *f*(*Q*, *E*) and Compton scattering *I*<sub>com</sub>(*Q*).
* **qmin, qmax, qstep**: Momentum transfer range and grid step (Å⁻¹).
* **fitmin, fitmax**: High-*Q* normalization window used for scaling coherent scattering and subtracting baseline contributions.
* **base_function_type**: Baseline basis function (`data` uses the dummy-frame baseline propagated from `orochi.pixia`; `flat`, `spline`, and `alss` provide analytical alternatives).
* Click **"Minimize Ripples"** to automatically tune [`fitmin`, `fitmax`] by minimizing unphysical sub-atomic ripples (*r* < *r*<sub>min,ripple</sub>), or **"Convert to PDF"** to compute *S*(*Q*), *F*(*Q*), and *G*(*r*) directly.
"""