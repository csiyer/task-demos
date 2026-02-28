import os
import numpy as np
import pandas as pd
from nilearn.glm.first_level import FirstLevelModel
from nilearn import image

def run_hcp_glm(subject_id, out_name, contrasts_to_run):
    """
    subject_id: The HCP ID (e.g., 100307)
    out_name: The output prefix (e.g., sub1)
    contrasts_to_run: List of contrast types (e.g., ['2bk-0bk', '2bk', '0bk'])
    """
    print(f"--- Processing Subject: {subject_id} ({out_name}) ---")
    
    # Paths
    base_path = f"/Users/chrisiyer/Downloads/{subject_id}/MNINonLinear/Results/tfMRI_WM_LR"
    func_img = os.path.join(base_path, "tfMRI_WM_LR_hp0_clean_rclean_tclean.nii.gz")
    mask_img = os.path.join(base_path, "brainmask_fs.2.nii.gz")
    ev_dir = os.path.join(base_path, "EVs")
    confounds_file = os.path.join(base_path, "Movement_Regressors.txt")
    output_dir = "/Users/chrisiyer/_Current/classes/task-demos/_analysis-fmri/images"
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
    confounds = pd.read_csv(confounds_file, sep='  ', engine='python', header=None)
    confounds.columns = [f'mot_{i}' for i in range(12)]

    # 3. Initialize & Run GLM
    model = FirstLevelModel(t_r=0.72,
                            mask_img=mask_img,
                            smoothing_fwhm=5,
                            standardize=True,
                            signal_scaling=0,
                            noise_model='ar1',
                            drift_model='cosine',
                            minimize_memory=False)

    print("Fitting model...")
    model.fit(func_img, events=events, confounds=confounds)
    design_columns = model.design_matrices_[0].columns

    # 4. Compute requested contrasts
    for con_type in contrasts_to_run:
        contrast_val = np.zeros(len(design_columns))
        
        if con_type == '2bk-0bk':
            # 2-Back minus 0-Back
            for i, col in enumerate(design_columns):
                if '2bk' in col:
                    contrast_val[i] = 1.0
                elif '0bk' in col:
                    contrast_val[i] = -1.0
        elif con_type == '2bk':
            # Mean activation during all 2-Back blocks
            for i, col in enumerate(design_columns):
                if '2bk' in col:
                    contrast_val[i] = 1.0
        elif con_type == '0bk':
            # Mean activation during all 0-Back blocks
            for i, col in enumerate(design_columns):
                if '0bk' in col:
                    contrast_val[i] = 1.0
        
        # Normalize weights so they average to 1/0 as appropriate
        n_pos = np.sum(contrast_val > 0)
        n_neg = np.sum(contrast_val < 0)
        if n_pos > 0: contrast_val[contrast_val > 0] /= n_pos
        if n_neg > 0: contrast_val[contrast_val < 0] /= n_neg

        print(f"Running Contrast: {con_type}")
        
        # Save Parameter Estimates (Effect Size)
        eff_map = model.compute_contrast(contrast_val, output_type='effect_size')
        out_file = os.path.join(output_dir, f"{out_name}_{con_type}_beta.nii.gz")
        eff_map.to_filename(out_file)
        print(f"Saved: {out_file}")

if __name__ == "__main__":
    # Subject 1 requirements: 2bk-0bk, 2bk, 0bk
    run_hcp_glm('100307', 'sub1', ['2bk-0bk', '2bk', '0bk'])
    
    # Subject 2 requirements: 2bk-0bk
    run_hcp_glm('100408', 'sub2', ['2bk-0bk'])
