import os
import numpy as np
import pandas as pd
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image

def run_hcp_glm(subject_id):
    print(f"--- Processing Subject: {subject_id} ---")
    
    # Paths
    base_path = f"/Users/chrisiyer/Downloads/{subject_id}/MNINonLinear/Results/tfMRI_WM_LR"
    func_img = os.path.join(base_path, "tfMRI_WM_LR_hp0_clean_rclean_tclean.nii.gz")
    mask_img = os.path.join(base_path, "brainmask_fs.2.nii.gz")
    ev_dir = os.path.join(base_path, "EVs")
    confounds_file = os.path.join(base_path, "Movement_Regressors.txt")
    output_dir = "/Users/chrisiyer/_Current/classes/task-demos/individual_maps"
    os.makedirs(output_dir, exist_ok=True)

    # 1. Load Timing (EVs)
    conditions = ['0bk_body', '0bk_faces', '0bk_places', '0bk_tools', 
                  '2bk_body', '2bk_faces', '2bk_places', '2bk_tools']
    
    all_events = []
    for cond in conditions:
        ev_file = os.path.join(ev_dir, f"{cond}.txt")
        if os.path.exists(ev_file) and os.path.getsize(ev_file) > 0:
            data = pd.read_csv(ev_file, sep='\t', names=['onset', 'duration', 'weight'])
            data['trial_type'] = cond
            all_events.append(data)
    
    events = pd.concat(all_events).sort_values('onset')

    # 2. Load Confounds (Movement)
    # HCP movement file has 12 columns (6 motion, 6 derivatives)
    confounds = pd.read_csv(confounds_file, sep='  ', engine='python', header=None)
    confounds.columns = [f'mot_{i}' for i in range(12)]

    # 3. Initialize & Run GLM
    # TR is 0.72s for HCP
    model = FirstLevelModel(t_r=0.72,
                            mask_img=mask_img,
                            smoothing_fwhm=5,
                            standardize=True,
                            signal_scaling=0,
                            noise_model='ar1',
                            drift_model='cosine',
                            minimize_memory=False)

    print("Fitting model (this may take a minute)...")
    model.fit(func_img, events=events, confounds=confounds)

    # 4. Compute Contrast: 2-Back vs 0-Back
    # Create a contrast vector by averaging all 2pk and 0pk conditions
    design_columns = model.design_matrices_[0].columns
    contrast_val = np.zeros(len(design_columns))
    
    # +1 for all 2bk, -1 for all 0bk
    for i, col in enumerate(design_columns):
        if '2bk' in col:
            contrast_val[i] = 1.0
        elif '0bk' in col:
            contrast_val[i] = -1.0
            
    print(f"Contrast Vector: {dict(zip(design_columns, contrast_val))}")

    z_map = model.compute_contrast(contrast_val, output_type='z_score')
    
    # 5. Save output
    out_file = os.path.join(output_dir, f"sub-{subject_id}_2bk-0bk_zstat.nii.gz")
    z_map.to_filename(out_file)
    print(f"Saved: {out_file}")

if __name__ == "__main__":
    subjects = ['100307', '100408']
    for sub in subjects:
        try:
            run_hcp_glm(sub)
        except Exception as e:
            print(f"Error processing {sub}: {e}")
