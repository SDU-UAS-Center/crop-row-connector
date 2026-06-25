.. _using-as-library:

========================
Using as a Library
========================

Integrating crop-row-connector Into Your Code
==============================================

The *crop-row-connector* can be used as a Python library in your own applications, enabling you to build custom interfaces for farmers and agricultural technicians.

Basic Usage
===========

Minimal Example
---------------

The simplest way to use the library:

.. code-block:: python

    from crop_row_connector import combine_crop_rows

    # Create processor
    ccr = combine_crop_rows.Combine_crop_rows()

    # Configure parameters
    ccr.angle_tolerance = 0.1
    ccr.distance_tolerance = 0.12

    # Run connection
    ccr.main("row_data.csv", "vegetation_points.csv")

This loads data, connects rows, and saves results to console output.

Capturing Output Files
----------------------

To retrieve the results, specify output paths:

.. code-block:: python

    from crop_row_connector import combine_crop_rows
    from pathlib import Path

    ccr = combine_crop_rows.Combine_crop_rows()
    ccr.angle_tolerance = 0.1
    ccr.distance_tolerance = 0.12
    ccr.vegetation_threshold = 127

    # Set output paths
    ccr.output_path_connected_crop_rows = "connected_rows.csv"
    ccr.output_path_vegetation_points = "vegetation.csv"

    # Run
    ccr.main("row_data.csv", "vegetation_points.csv")

    # Results are now in the CSV files
    print("Connected rows saved to connected_rows.csv")

Advanced Usage Patterns
=======================

Error Handling
--------------

Handle common errors gracefully:

.. code-block:: python

    from crop_row_connector import combine_crop_rows
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    try:
        ccr = combine_crop_rows.Combine_crop_rows()
        ccr.angle_tolerance = 0.1
        ccr.distance_tolerance = 0.12

        ccr.main("row_data.csv", "vegetation_points.csv")
        logger.info("Crop row connection completed successfully")

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
    except ValueError as e:
        logger.error(f"Invalid parameter or data: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)

Batch Processing Multiple Fields
---------------------------------

Process multiple fields with the same parameters:

.. code-block:: python

    from pathlib import Path
    from crop_row_connector import combine_crop_rows

    def process_field(field_name, row_file, points_file, output_dir):
        """Process a single field and save results."""
        ccr = combine_crop_rows.Combine_crop_rows()

        # Configure for all fields
        ccr.angle_tolerance = 0.1
        ccr.distance_tolerance = 0.12
        ccr.vegetation_threshold = 127

        # Set output paths
        output_path = Path(output_dir) / field_name
        output_path.mkdir(parents=True, exist_ok=True)

        ccr.output_path_connected_crop_rows = str(output_path / "connected_rows.csv")
        ccr.output_path_vegetation_points = str(output_path / "vegetation.csv")

        print(f"Processing {field_name}...")
        ccr.main(row_file, points_file)
        print(f"Completed {field_name}")

    # Process multiple fields
    fields = [
        ("field_2024_north", "north_rows.csv", "north_points.csv"),
        ("field_2024_south", "south_rows.csv", "south_points.csv"),
        ("field_2024_east", "east_rows.csv", "east_points.csv"),
    ]

    for field_name, rows_file, points_file in fields:
        process_field(field_name, rows_file, points_file, "results/")

Iterating Over Results
----------------------

After processing, load and analyze the results:

.. code-block:: python

    import pandas as pd
    from crop_row_connector import combine_crop_rows

    # Run connection
    ccr = combine_crop_rows.Combine_crop_rows()
    ccr.angle_tolerance = 0.1
    ccr.distance_tolerance = 0.12
    ccr.output_path_connected_crop_rows = "connected_rows.csv"

    ccr.main("row_data.csv", "vegetation_points.csv")

    # Load and analyze results
    connected_rows = pd.read_csv("connected_rows.csv")

    # Count how many rows connected to others
    rows_with_connections = connected_rows[connected_rows['con_1_tile'].notna()]
    print(f"Connected rows: {len(rows_with_connections)}")

    # Find rows with multiple connections
    multi_connection_rows = connected_rows[connected_rows['con_3_tile'].notna()]
    print(f"Rows with 3+ connections: {len(multi_connection_rows)}")

    # Group by connected row index
    for crop_row_id in connected_rows['row_index'].unique():
        segments = connected_rows[connected_rows['row_index'] == crop_row_id]
        print(f"Crop row {crop_row_id}: {len(segments)} segments across tiles")

Parameter Optimization Loop
----------------------------

Systematically test different parameters:

.. code-block:: python

    from crop_row_connector import combine_crop_rows
    import pandas as pd

    def run_with_parameters(distance_tol, angle_tol):
        """Run connection with specific parameters."""
        ccr = combine_crop_rows.Combine_crop_rows()
        ccr.angle_tolerance = angle_tol
        ccr.distance_tolerance = distance_tol
        ccr.output_path_connected_crop_rows = f"results_{distance_tol}_{angle_tol}.csv"

        ccr.main("row_data.csv", "vegetation_points.csv")

        # Count connections for comparison
        results = pd.read_csv(ccr.output_path_connected_crop_rows)
        connected = results[results['con_1_tile'].notna()]

        return {
            'distance_tol': distance_tol,
            'angle_tol': angle_tol,
            'total_rows': len(results),
            'connected_rows': len(connected),
            'connection_rate': len(connected) / len(results) if len(results) > 0 else 0
        }

    # Test parameter combinations
    results = []
    for distance_tol in [0.08, 0.10, 0.12, 0.15]:
        for angle_tol in [0.08, 0.10, 0.12]:
            result = run_with_parameters(distance_tol, angle_tol)
            results.append(result)

    # Create summary table
    summary = pd.DataFrame(results)
    print(summary)
    print("\nBest parameter (highest connection rate):")
    best = summary.loc[summary['connection_rate'].idxmax()]
    print(f"distance_tol={best['distance_tol']}, angle_tol={best['angle_tol']}")

Building a Web Service
======================

Creating an HTTP API endpoint for crop row connection:

.. code-block:: python

    from flask import Flask, request, jsonify, send_file
    from crop_row_connector import combine_crop_rows
    import tempfile
    import os

    app = Flask(__name__)

    @app.route('/connect_rows', methods=['POST'])
    def connect_rows():
        """API endpoint for crop row connection."""
        try:
            # Receive files
            row_file = request.files['rows']
            point_file = request.files['points']

            # Extract parameters from request
            distance_tolerance = float(request.form.get('distance_tolerance', 0.12))
            angle_tolerance = float(request.form.get('angle_tolerance', 0.1))

            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as tmpdir:
                # Save uploaded files
                rows_path = os.path.join(tmpdir, "rows.csv")
                points_path = os.path.join(tmpdir, "points.csv")
                output_path = os.path.join(tmpdir, "connected_rows.csv")

                row_file.save(rows_path)
                point_file.save(points_path)

                # Process
                ccr = combine_crop_rows.Combine_crop_rows()
                ccr.angle_tolerance = angle_tolerance
                ccr.distance_tolerance = distance_tolerance
                ccr.output_path_connected_crop_rows = output_path

                ccr.main(rows_path, points_path)

                # Return result file
                return send_file(
                    output_path,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name='connected_rows.csv'
                )

        except Exception as e:
            return jsonify({'error': str(e)}), 400

    if __name__ == '__main__':
        app.run(debug=False, port=5000)

**Client usage**:

.. code-block:: python

    import requests

    files = {
        'rows': open('row_data.csv', 'rb'),
        'points': open('points.csv', 'rb'),
    }
    data = {
        'distance_tolerance': 0.12,
        'angle_tolerance': 0.1,
    }

    response = requests.post('http://localhost:5000/connect_rows',
                            files=files, data=data)

    if response.status_code == 200:
        with open('results.csv', 'wb') as f:
            f.write(response.content)

Building a GUI Application
===========================

Simple desktop application using tkinter:

.. code-block:: python

    import tkinter as tk
    from tkinter import filedialog, messagebox
    from crop_row_connector import combine_crop_rows
    import threading

    class CropRowConnectorGUI:
        def __init__(self, root):
            self.root = root
            self.root.title("Crop Row Connector")
            self.root.geometry("600x400")

            # File selection
            tk.Label(root, text="Row Data File:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
            self.row_file_var = tk.StringVar()
            tk.Entry(root, textvariable=self.row_file_var, width=40).grid(row=0, column=1, padx=10, pady=5)
            tk.Button(root, text="Browse", command=self.select_row_file).grid(row=0, column=2, padx=5, pady=5)

            tk.Label(root, text="Points Data File:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
            self.points_file_var = tk.StringVar()
            tk.Entry(root, textvariable=self.points_file_var, width=40).grid(row=1, column=1, padx=10, pady=5)
            tk.Button(root, text="Browse", command=self.select_points_file).grid(row=1, column=2, padx=5, pady=5)

            # Parameters
            tk.Label(root, text="Distance Tolerance (m):").grid(row=2, column=0, sticky="w", padx=10, pady=5)
            self.distance_var = tk.DoubleVar(value=0.12)
            tk.Scale(root, from_=0.05, to=0.5, resolution=0.01,
                    variable=self.distance_var, orient=tk.HORIZONTAL).grid(row=2, column=1, padx=10, pady=5)

            tk.Label(root, text="Angle Tolerance (rad):").grid(row=3, column=0, sticky="w", padx=10, pady=5)
            self.angle_var = tk.DoubleVar(value=0.1)
            tk.Scale(root, from_=0.05, to=0.3, resolution=0.01,
                    variable=self.angle_var, orient=tk.HORIZONTAL).grid(row=3, column=1, padx=10, pady=5)

            # Process button
            tk.Button(root, text="Process", command=self.process,
                     bg="green", fg="white", width=20).grid(row=4, column=0, columnspan=3, pady=20)

            # Status
            self.status_var = tk.StringVar(value="Ready")
            tk.Label(root, textvariable=self.status_var).grid(row=5, column=0, columnspan=3, pady=10)

        def select_row_file(self):
            file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
            if file:
                self.row_file_var.set(file)

        def select_points_file(self):
            file = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
            if file:
                self.points_file_var.set(file)

        def process(self):
            if not self.row_file_var.get() or not self.points_file_var.get():
                messagebox.showerror("Error", "Please select both input files")
                return

            # Run in background thread to prevent UI freeze
            thread = threading.Thread(target=self._run_process)
            thread.start()

        def _run_process(self):
            try:
                self.status_var.set("Processing...")
                self.root.update()

                ccr = combine_crop_rows.Combine_crop_rows()
                ccr.angle_tolerance = self.angle_var.get()
                ccr.distance_tolerance = self.distance_var.get()

                # Ask for output path
                output_file = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")]
                )

                if output_file:
                    ccr.output_path_connected_crop_rows = output_file
                    ccr.main(self.row_file_var.get(), self.points_file_var.get())
                    self.status_var.set(f"Complete! Saved to {output_file}")
                    messagebox.showinfo("Success", "Processing complete!")

            except Exception as e:
                self.status_var.set("Error during processing")
                messagebox.showerror("Error", str(e))

    if __name__ == '__main__':
        root = tk.Tk()
        app = CropRowConnectorGUI(root)
        root.mainloop()

Integration with Data Pipelines
================================

Using with Pandas for data preprocessing/postprocessing:

.. code-block:: python

    import pandas as pd
    from crop_row_connector import combine_crop_rows

    def preprocess_data(row_data_path):
        """Clean and validate input data before processing."""
        df = pd.read_csv(row_data_path)

        # Remove duplicate rows
        df = df.drop_duplicates()

        # Validate required columns
        required = ['tile_number', 'angle', 'row', 'x_start', 'y_start', 'x_end', 'y_end']
        if not all(col in df.columns for col in required):
            raise ValueError(f"Missing required columns: {required}")

        # Remove invalid rows
        df = df[(df['x_start'] != df['x_end']) | (df['y_start'] != df['y_end'])]

        return df

    def postprocess_results(results_path):
        """Analyze and enrich results."""
        df = pd.read_csv(results_path)

        # Count segments per connected row
        df['num_segments'] = df.groupby('row_index')['row_index'].transform('count')

        # Count connections per segment
        df['num_connections'] = (
            df[['con_1_tile', 'con_2_tile', 'con_3_tile', 'con_4_tile']]
            .notna().sum(axis=1)
        )

        return df

    # Full pipeline
    row_data = preprocess_data("raw_rows.csv")
    row_data.to_csv("clean_rows.csv", index=False)

    ccr = combine_crop_rows.Combine_crop_rows()
    ccr.angle_tolerance = 0.1
    ccr.distance_tolerance = 0.12
    ccr.output_path_connected_crop_rows = "connected.csv"

    ccr.main("clean_rows.csv", "points.csv")

    results = postprocess_results("connected.csv")
    print(results.head())
    print(f"Average segments per connected row: {results['num_segments'].mean():.1f}")
    print(f"Average connections per segment: {results['num_connections'].mean():.1f}")

Troubleshooting Library Usage
=============================

**ImportError: No module named 'crop_row_connector'**

Install the package in your Python environment:

.. code-block:: bash

    pip install crop-row-connector

Or if developing locally:

.. code-block:: bash

    cd /path/to/crop-row-connector
    pip install -e .

**Memory Issues with Large Fields**

For very large fields, process in regions:

.. code-block:: python

    def process_field_regions(row_file, points_file, region_size=100):
        """Process large field in manageable regions."""
        df_rows = pd.read_csv(row_file)

        # Group tiles into regions
        for region_id, region_df in enumerate(df_rows.groupby(df_rows.index // region_size)):
            region_rows = f"region_{region_id}_rows.csv"
            region_df[1].to_csv(region_rows, index=False)

            # Process this region
            ccr = combine_crop_rows.Combine_crop_rows()
            ccr.main(region_rows, points_file)

**Slow Performance**

Optimize with parallelization:

.. code-block:: python

    import os
    from crop_row_connector import combine_crop_rows

    ccr = combine_crop_rows.Combine_crop_rows()
    ccr.max_workers = os.cpu_count()  # Use all available cores
    ccr.main(row_file, points_file)
