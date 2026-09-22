#[pyo3::pymodule]
mod _native {
    use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2};
    use pyo3::{Bound, Python, pyfunction};

    #[pyfunction]
    fn merge_points_removing_overlap<'py>(
        py: Python<'py>,
        connected_crop_rows: PyReadonlyArray2<f64>,
        points_in_rows: PyReadonlyArray2<f64>,
        row_information: PyReadonlyArray2<f64>,
        tolerance: f64,
        num_threads: usize,
    ) -> Bound<'py, PyArray2<f64>> {
        // Run the computation without holding the GIL; the readonly array
        // views are safe to read from other threads.
        let c = connected_crop_rows.as_array();
        let p = points_in_rows.as_array();
        let r = row_information.as_array();
        let result =
            py.detach(|| crate::rust_fn::multithreaded_merging(c, p, r, tolerance, num_threads));
        result.into_pyarray(py)
    }
}

mod rust_fn {
    use numpy::ndarray::{Array2, ArrayView1, ArrayView2, Axis, s};
    use rayon::prelude::*;
    use std::collections::HashMap;

    /// Point in the plane.
    type Pt = [f64; 2];

    pub fn determine_points_relations(
        row1: ArrayView1<f64>,
        row2: ArrayView1<f64>,
    ) -> (Pt, Pt, Pt, Pt) {
        /*
        Given two lines with start and end point calculates which point on each line is
        closest and farthest to the opposite line.

        Row layout: [row_number, x_start, y_start, x_end, y_end, x_mid, y_mid].
        */
        let r1: [Pt; 3] = [[row1[1], row1[2]], [row1[3], row1[4]], [row1[5], row1[6]]];
        let r2: [Pt; 3] = [[row2[1], row2[2]], [row2[3], row2[4]], [row2[5], row2[6]]];

        let mut max_dist = 0.0;
        let mut pair = (0, 0);
        for (i, a) in r1.iter().enumerate() {
            for (j, b) in r2.iter().enumerate() {
                let d = ((a[0] - b[0]).powi(2) + (a[1] - b[1]).powi(2)).sqrt();
                if d > max_dist {
                    max_dist = d;
                    pair = (i, j);
                }
            }
        }

        let row_1_far = r1[pair.0];
        let row_2_far = r2[pair.1];
        let row_1_close = if pair.0 == 0 { r1[1] } else { r1[0] };
        let row_2_close = if pair.1 == 0 { r2[1] } else { r2[0] };

        (row_1_far, row_2_far, row_1_close, row_2_close)
    }

    pub fn point_projection_of_p_onto_line(point: &Pt, l_close: &Pt, l_far: &Pt) -> Pt {
        /*
        Projects a point onto the line created by l_close and l_far
        */
        let v_line = [l_far[0] - l_close[0], l_far[1] - l_close[1]];
        let v_pc = [point[0] - l_close[0], point[1] - l_close[1]];
        let dot_vpc = v_pc[0] * v_line[0] + v_pc[1] * v_line[1];
        let dot_line = v_line[0] * v_line[0] + v_line[1] * v_line[1];
        let scale = dot_vpc / dot_line;
        [
            l_close[0] + scale * v_line[0],
            l_close[1] + scale * v_line[1],
        ]
    }

    pub fn remove_points_past_center(
        center: &Pt,
        line_end: &Pt,
        points_in_rows: ArrayView2<f64>,
        selected: &[usize],
        tolerance: f64,
    ) -> Vec<usize> {
        /*
        Removes points between the center and the end of a line if the center is on the line.

        `selected` holds indices into `points_in_rows`; only the kept indices are returned.
        */
        // Distance between center and line end does not depend on the points;
        // compute it once instead of per point.
        let distance =
            ((center[0] - line_end[0]).powi(2) + (center[1] - line_end[1]).powi(2)).sqrt();

        selected
            .iter()
            .copied()
            .filter(|&i| {
                let r = points_in_rows.row(i);
                let x = r[2];
                let y = r[3];

                if distance < tolerance {
                    !x.is_nan() && !y.is_nan()
                } else if center[0] < line_end[0] && center[1] < line_end[1] {
                    (x <= center[0] + tolerance && y <= center[1] + tolerance)
                        || (x >= line_end[0] + tolerance && y >= line_end[1] + tolerance)
                } else if center[0] < line_end[0] && center[1] > line_end[1] {
                    (x <= center[0] + tolerance && y >= center[1] - tolerance)
                        || (x >= line_end[0] + tolerance && y <= line_end[1] - tolerance)
                } else if center[0] > line_end[0] && center[1] > line_end[1] {
                    (x >= center[0] - tolerance && y >= center[1] - tolerance)
                        || (x <= line_end[0] - tolerance && y <= line_end[1] - tolerance)
                } else {
                    (x >= center[0] - tolerance && y <= center[1] + tolerance)
                        || (x <= line_end[0] - tolerance && y >= line_end[1] + tolerance)
                }
            })
            .collect()
    }

    /// Lookup indexes shared by all merge tasks (built once, read concurrently).
    struct MergeIndex {
        /// (tile, row) -> indices into `points_in_rows`, in original order.
        points_by_tile_row: HashMap<(usize, usize), Vec<usize>>,
        /// (tile, row) bits -> first index into `row_information` (exact f64 match).
        info_by_tile_row_bits: HashMap<(u64, u64), usize>,
        /// (tile, row) as usize -> first index into `row_information`.
        info_by_tile_row_usize: HashMap<(usize, usize), usize>,
    }

    impl MergeIndex {
        fn build(points_in_rows: ArrayView2<f64>, row_information: ArrayView2<f64>) -> Self {
            let mut points_by_tile_row: HashMap<(usize, usize), Vec<usize>> =
                HashMap::with_capacity(points_in_rows.nrows());
            for (i, r) in points_in_rows.axis_iter(Axis(0)).enumerate() {
                points_by_tile_row
                    .entry((r[0] as usize, r[1] as usize))
                    .or_default()
                    .push(i);
            }

            let mut info_by_tile_row_bits: HashMap<(u64, u64), usize> =
                HashMap::with_capacity(row_information.nrows());
            let mut info_by_tile_row_usize: HashMap<(usize, usize), usize> =
                HashMap::with_capacity(row_information.nrows());
            for (i, r) in row_information.axis_iter(Axis(0)).enumerate() {
                info_by_tile_row_bits
                    .entry((r[0].to_bits(), r[4].to_bits()))
                    .or_insert(i);
                info_by_tile_row_usize
                    .entry((r[0] as usize, r[4] as usize))
                    .or_insert(i);
            }

            MergeIndex {
                points_by_tile_row,
                info_by_tile_row_bits,
                info_by_tile_row_usize,
            }
        }
    }

    fn merge_points_removing_overlap(
        index: &MergeIndex,
        points_in_rows: ArrayView2<f64>,
        row_information: ArrayView2<f64>,
        tolerance: f64,
        row_segment: ArrayView1<f64>,
    ) -> Vec<usize> {
        /*
        Takes a single row and removes points which overlap with other rows it is connected to.

        Returns indices into `points_in_rows`, in original order.
        */
        let tile_number = row_segment[1] as usize;
        let tile_row = row_segment[2] as usize;

        let mut selected: Vec<usize> = index
            .points_by_tile_row
            .get(&(tile_number, tile_row))
            .cloned()
            .unwrap_or_default();

        let row_idx = *index
            .info_by_tile_row_usize
            .get(&(tile_number, tile_row))
            .unwrap();
        let row_full = row_information.row(row_idx);
        let row = row_full.slice(s![4..]);

        for i in 0..4 {
            if row_segment[3 + i * 2].is_nan() {
                break;
            }
            let connected_tile_n = row_segment[3 + i * 2];
            let connected_row_n = row_segment[4 + i * 2];
            // The lookup key matches by exact bit pattern to preserve the
            // original `r[0] == connected_tile_n` float comparison semantics.
            let connected_idx = *index
                .info_by_tile_row_bits
                .get(&(connected_tile_n.to_bits(), connected_row_n.to_bits()))
                .unwrap();
            let connected_row_full = row_information.row(connected_idx);
            let connected_row = connected_row_full.slice(s![4..]);

            let (row_1_far, _, row_1_close, row_2_close) =
                determine_points_relations(row, connected_row);

            let center_of_ends = [
                (row_1_close[0] + row_2_close[0]) / 2.0,
                (row_1_close[1] + row_2_close[1]) / 2.0,
            ];

            let point_proj =
                point_projection_of_p_onto_line(&center_of_ends, &row_1_close, &row_1_far);

            selected = remove_points_past_center(
                &point_proj,
                &row_1_close,
                points_in_rows,
                &selected,
                tolerance,
            );
        }
        selected
    }

    pub fn multithreaded_merging(
        connected_crop_rows: ArrayView2<f64>,
        points_in_rows: ArrayView2<f64>,
        row_information: ArrayView2<f64>,
        tolerance: f64,
        num_threads: usize,
    ) -> Array2<f64> {
        /*
        Merging the points in points_in_rows based on the information from connected_crop_rows.
        This is handled in a multithreaded manner.
        */

        // Build a dedicated pool so `num_threads` is actually honored, and run
        // the parallel work through it. Results are collected with input order
        // preserved (no shared-mutex accumulation).
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(num_threads)
            .build()
            .unwrap();

        let index = MergeIndex::build(points_in_rows, row_information);

        let merged: Vec<Vec<usize>> = pool.install(|| {
            (0..connected_crop_rows.nrows())
                .into_par_iter()
                .map(|i| {
                    let row_segment = connected_crop_rows.row(i);
                    merge_points_removing_overlap(
                        &index,
                        points_in_rows,
                        row_information,
                        tolerance,
                        row_segment,
                    )
                })
                .collect()
        });

        // Stack the selected rows back into an Array2 (one flat copy).
        let ncols = points_in_rows.ncols();
        let nrows: usize = merged.iter().map(|v| v.len()).sum();
        if nrows == 0 {
            return Array2::<f64>::zeros((0, ncols));
        }

        let mut flat: Vec<f64> = Vec::with_capacity(nrows * ncols);
        for seg in &merged {
            for &i in seg {
                flat.extend(points_in_rows.row(i).iter().copied());
            }
        }
        Array2::from_shape_vec((nrows, ncols), flat).unwrap()
    }
}
