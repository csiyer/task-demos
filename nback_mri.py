from psychopy import visual, core, event, gui
from psychopy.hardware import keyboard
import random, csv, os
"""
EXPERIMENT TIMELINE
6 runs of 7 mins each = 42 mins
    + 5 mins T1 + 2 mins fieldmaps + 1 min extra = 50 minutes total

Run 1: letters
    10s instructions (skippable)
    82s 1-back 
    rest (avg = 20s)
    82s 2-back
    rest (avg = 20s)
    82s 1-back
    rest (avg = 20s)
    82s 2-back
    rest (avg = 20s)
Run 2: letters
    Same but N goes 2-1-2-1
Run 3: faces
    Same as run 1
Run 4: faces
    Same as run 2
Run 5: scenes
    Same as run 1
Run 6: scenes
    Same as run 2
"""

# ===== PARAMETERS =====
STIMTYPE_BY_RUN = ['letters', 'letters', 'faces', 'faces', 'scenes', 'scenes']
RUN_N_ORDERS = [[1, 2, 1, 2], [2, 1, 2, 1]] # toggle 2vs1back ordering each run
INSTRUCTIONS_DURATION = 10 
INTER_BLOCK_RESTS = [17, 19, 21, 23] # Shuffled inter-block and final rests
TRIAL_DURATION = 2.0
STIM_DURATION = 1.5 
N_TRIALS_PER_BLOCK = 41 # 82 seconds
N_TARGETS_PER_BLOCK = 14 # about 1/3 of stimuli are targets
RESPONSE_KEY = 'space'
SCANNER_TRIGGER = 't' 
DATA_FILE = 'nback_data_mri.csv'
STIMULI_DIR = '_stimuli'

# Define stimuli
stimuli = {
    'letters': ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z'],
    'faces': [os.path.join(STIMULI_DIR, f'face{i}.jpg') for i in range(60)],
    'scenes': [os.path.join(STIMULI_DIR, f'scene{i}.jpg') for i in range(60)]
}

# Setup psychopy stuff
win = visual.Window([1024, 768], color='black', fullscr=True, units='height')
win.mouseVisible = False
fixation = visual.TextStim(win, text='+', color='white', height=0.1)
text_stim = visual.TextStim(win, text='', color='white', height=0.2)
image_stim = visual.ImageStim(win, size=(0.5, 0.5))
instr_text = visual.TextStim(win, text='', color='white', height=0.05, wrapWidth=0.8)
global_clock = core.Clock()
rest_clock = core.Clock()
kb = keyboard.Keyboard()

def execute_block(run_idx, block_idx, n, stim_type, results):
    """Executes a single 82-second block of N-back."""

    # Generate sequence of targets (target cannot be in first 'n' trials)
    is_targets = [True] * N_TARGETS_PER_BLOCK + [False] * (N_TRIALS_PER_BLOCK - N_TARGETS_PER_BLOCK - n)
    random.shuffle(is_targets)
    is_targets = [False] * n + is_targets
    
    block_stimuli = []
    for i in range(N_TRIALS_PER_BLOCK):
        is_target = is_targets[i]
        if is_target:
            current_stim = block_stimuli[i - n]
        else:
            if i >= n:
                # Pick a stim that isn't the n-back match
                available = [s for s in stimuli[stim_type] if s != block_stimuli[i-n]]
                current_stim = random.choice(available)
            else:
                current_stim = random.choice(stimuli[stim_type])
        block_stimuli.append(current_stim)
        
        trial_start_time = global_clock.getTime()
        
        # Draw Stimulus
        if stim_type == 'letters':
            text_stim.text = current_stim
            text_stim.draw()
        else:
            image_stim.image = current_stim
            image_stim.draw()
        win.flip()
        
        resp_key = None
        resp_rt = None
        trial_clock = core.Clock()
        stim_on = True
        
        # Trial Loop (Fixed 2.0s)
        while trial_clock.getTime() < TRIAL_DURATION:
            if stim_on and trial_clock.getTime() >= STIM_DURATION:
                win.flip() # Offset stimulus at 1.5s
                stim_on = False
                
            keys = kb.getKeys(keyList=[RESPONSE_KEY, SCANNER_TRIGGER, 'escape'], waitRelease=False)
            for k in keys:
                if k.name == 'escape': core.quit()
                elif k.name == SCANNER_TRIGGER:
                    results.append({'run': run_idx+1, 'block': block_idx+1, 'event_type': 'trigger', 'timestamp': global_clock.getTime()})
                elif k.name == RESPONSE_KEY and resp_key is None:
                    resp_key = k.name
                    resp_rt = k.rt
            core.wait(0.001)

        # Log Data
        correct = (is_target and resp_key == RESPONSE_KEY) or (not is_target and resp_key is None)
        results.append({
            'run': run_idx + 1, 'block': block_idx + 1, 'trial': i + 1,
            'event_type': 'trial', 'timestamp': trial_start_time,
            'n': n, 'stim_type': stim_type, 'stimulus': current_stim,
            'is_target': int(is_target), 'resp_key': resp_key if resp_key else '',
            'resp_rt': resp_rt if resp_rt else '', 'correct': int(correct)
        })


def execute_run(run_idx, stim_type, run_n_order, results):
    """Handles the full task/run cycle."""
    rests = list(INTER_BLOCK_RESTS)
    random.shuffle(rests)

    # 1. Initial Instructions (10s, skippable by button press)
    first_n = run_n_order[0]
    rest_clock.reset()
    while rest_clock.getTime() < INSTRUCTIONS_DURATION:
        instr_text.text = f"RUN {run_idx+1}: {stim_type.upper()}\n\nNext: {first_n}-back\n\nStarting in {int(INSTRUCTIONS_DURATION - rest_clock.getTime())} seconds...\n\n(Press button to start immediately)"
        instr_text.draw()
        win.flip()
        keys = kb.getKeys(keyList=[RESPONSE_KEY, 'escape'], waitRelease=False)
        if 'escape' in [k.name for k in keys]: core.quit()
        if RESPONSE_KEY in [k.name for k in keys]: break

    # 2. task-rest-task-rest cycle
    for block_idx, n in enumerate(run_n_order):
        # Task (82s)
        execute_block(run_idx, block_idx, n, stim_type, results)

        # Rest (20s)
        rest_duration = rests[block_idx]
        rest_clock.reset()
        while rest_clock.getTime() < rest_duration:
            # Show n-back for the NEXT block during rest, unless it's the final wrap-up
            if block_idx < len(run_n_order) - 1:
                next_n = run_n_order[block_idx + 1]
                instr_text.text = f"REST\n\nNext: {next_n}-back\n({int(rest_duration - rest_clock.getTime())}s)"
            else:
                instr_text.text = f"REST\n\nRun complete.\n({int(rest_duration - rest_clock.getTime())}s)"
            
            instr_text.draw()
            win.flip()
            if 'escape' in [k.name for k in kb.getKeys(keyList=['escape'])]: core.quit()


# ===== MAIN EXPERIMENT LOOP =====
results = []
for run_idx, stim_type in enumerate(STIMTYPE_BY_RUN):
    # Wait for Trigger
    instr_text.text = f"RUN {run_idx+1}/6: {stim_type.upper()}\n\nWaiting for scanner..."
    instr_text.draw()
    win.flip()
    
    kb.clearEvents()
    keys = kb.waitKeys(keyList=[SCANNER_TRIGGER, 'escape'])
    if 'escape' in [k.name for k in keys]: core.quit()
    
    results.append({'run': run_idx + 1, 'event_type': 'run_start', 'timestamp': global_clock.getTime(), 'stim_type': stim_type})
    this_run_n_order = RUN_N_ORDERS[run_idx % 2] # (1-2-1-2 or 2-1-2-1)
    execute_run(run_idx, stim_type, this_run_n_order, results)
    
    # Save data after every run
    with open(DATA_FILE, 'w', newline='') as f:
        fieldnames = ['run', 'block', 'trial', 'event_type', 'timestamp', 'n', 'stim_type', 'stimulus', 'is_target', 'resp_key', 'resp_rt', 'correct']
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(results)

# Final Screen
instr_text.text = "Experiment Complete!\n\nThank you."
instr_text.draw()
win.flip()
core.wait(5)
win.close()
core.quit()