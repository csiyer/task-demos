from psychopy import visual, core, event, gui
from psychopy.hardware import keyboard
import random, csv, os

# ===== PARAMETERS =====
# goal is 6 runs of 5 mins each = 30 mins
# + 15 mins other scans = 45 mins total
# each run = 30s rest/instructions + 2 mins task + 30s rest + 2 mins task = 5 mins
# runs: letter 1-back, letter 2-back, face 1-back, face 2-back, scene 1-back, scene 2-back

N_BY_RUN = [1, 2, 1, 2, 1, 2]
STIMTYPE_BY_RUN = ['letters','letters','faces','faces','scenes','scenes']
REST_DURATION = 30 # seconds
TRIAL_DURATION = 2 # seconds; total
STIM_DURATION = 1.5 # seconds; stimulus on screen
N_BLOCKS_PER_RUN = 2
N_TRIALS_PER_BLOCK = 60 # 2 mins at 2s per trial
N_TARGETS_PER_BLOCK = 20 # 1/3 of trials are targets

RESPONSE_KEY = 'space' 
SCANNER_TRIGGER = 't' # the scanner trigger pulse

DATA_FILE = 'nback_data_mri.csv'
STIMULI_DIR = '_stimuli'

# Stimuli definitions
stimuli = {
    'letters': ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z'],
    'faces': [os.path.join(STIMULI_DIR, f'face{i}.jpg') for i in range(60)],
    'scenes': [os.path.join(STIMULI_DIR, f'scene{i}.jpg') for i in range(60)]
}
# ======================

# Setup
win = visual.Window([1024, 768], color='black', fullscr=True, units='height')
win.mouseVisible = False

# Fix: Restore missing stimuli definitions
fixation = visual.TextStim(win, text='+', color='white', height=0.1)
text_stim = visual.TextStim(win, text='', color='white', height=0.2)
image_stim = visual.ImageStim(win, size=(0.5, 0.5))
instr_text = visual.TextStim(win, text='', color='white', height=0.05, wrapWidth=0.8)

# Global clock for absolute timing
global_clock = core.Clock()
rest_clock = core.Clock()
kb = keyboard.Keyboard()

def run_block(run_idx, block_idx, n, stim_type, results):
    # Generate trial sequence for this block
    is_targets = [True] * N_TARGETS_PER_BLOCK + [False] * (N_TRIALS_PER_BLOCK - N_TARGETS_PER_BLOCK - n)
    random.shuffle(is_targets)
    is_targets = [False] * n + is_targets # add 'n' non-target trials at the start
    
    block_stimuli = []
    for i in range(N_TRIALS_PER_BLOCK):
        is_target = is_targets[i]
        if is_target:
            current_stim = block_stimuli[i - n]
        else:
            # Pick a stim that isn't the one n-back
            if i >= n:
                current_stim = random.choice([s for s in stimuli[stim_type] if s != block_stimuli[i-n]])
            else:
                current_stim = random.choice(stimuli[stim_type])
        block_stimuli.append(current_stim)
        
        # Trial Timing
        trial_start_time = global_clock.getTime()
        
        # Show Stimulus
        if stim_type == 'letters':
            text_stim.text = current_stim
            text_stim.draw()
        else:
            image_stim.image = current_stim
            image_stim.draw()
        win.flip()
        
        # Wait for response for the duration of the trial
        resp_key = None
        resp_rt = None
        
        trial_clock = core.Clock()
        stim_on = True
        while trial_clock.getTime() < TRIAL_DURATION:
            # Handle stimulus disappearance at 1.5s (fixed duration)
            if stim_on and trial_clock.getTime() >= STIM_DURATION:
                win.flip() # Blank screen
                stim_on = False
                
            keys = kb.getKeys(keyList=[RESPONSE_KEY, SCANNER_TRIGGER, 'escape'], waitRelease=False)
            for k in keys:
                time = k.rt
                key = k.name
                if key == 'escape':
                    core.quit()
                elif key == SCANNER_TRIGGER:
                    # Log trigger if needed, but don't count as response
                    results.append({
                            'run': run_idx + 1, 'block': block_idx + 1,'trial': -1, # Trigger log
                            'event_type': 'trigger', 'timestamp': global_clock.getTime(),
                            'n': n, 'stim_type': stim_type, 'stimulus': '', 'is_target': -1, 
                            'resp_key': '', 'resp_rt': time, 'correct': -1
                        })
                elif key == RESPONSE_KEY and resp_key is None:
                    resp_key = key
                    resp_rt = time
            
            # Short sleep to prevent CPU hogging
            core.wait(0.001)

        # Save trial data
        correct = (is_target and resp_key == RESPONSE_KEY) or (not is_target and resp_key is None)
        results.append({
            'run': run_idx + 1,
            'block': block_idx + 1,
            'trial': i + 1,
            'event_type': 'trial',
            'timestamp': trial_start_time,
            'n': n,
            'stim_type': stim_type,
            'stimulus': current_stim,
            'is_target': int(is_target),
            'resp_key': resp_key if resp_key else '',
            'resp_rt': resp_rt if resp_rt else '',
            'correct': int(correct)
        })
 

# Main Experiment Loop
results = []
for run_idx, (n, stim_type) in enumerate(zip(N_BY_RUN, STIMTYPE_BY_RUN)):

    # wait for scan to begin and trigger to come
    instr_text.text = f"Run {run_idx + 1}/{len(N_BY_RUN)}: Waiting for scanner..."
    instr_text.draw()
    win.flip()
    kb.clearEvents()
    keys = kb.waitKeys(keyList=[SCANNER_TRIGGER, 'escape'])
    if 'escape' in [k.name for k in keys]:
        core.quit()
    run_start_time = global_clock.getTime()
    results.append({
        'run': run_idx + 1, 'block': 0, 'trial': 0,
        'event_type': 'run_start', 'timestamp': run_start_time,
        'n': n, 'stim_type': stim_type, 'stimulus': '',
        'is_target': -1, 'resp_key': '', 'resp_rt': 0, 'correct': -1
    })

    for block_idx in range(N_BLOCKS_PER_RUN):
        # 30s instructions, 2min block, 30s rest, 2 min block

        # rest period / instructions
        if block_idx == 0:
            instr_text.text = f"Task: {n}-BACK\nStimuli: {stim_type.capitalize()}\n\nPress the button when the stimulus matches the one {n} trials ago.\n\n(Press button to skip 30s rest and begin block)"
        else:
            instr_text.text = f"30-second rest\n\n(Press button to skip and begin next block)"
        rest_clock.reset()
        while rest_clock.getTime() < REST_DURATION:
            instr_text.draw()
            win.flip()
            # Capture keyboard events
            keys = kb.getKeys(keyList=[RESPONSE_KEY, SCANNER_TRIGGER, SCANNER_TRIGGER.upper(), 'escape'], waitRelease=False)
            exit_rest = False
            for k in keys:
                key = k.name
                time = k.rt
                if key == 'escape':
                    core.quit()
                elif key == SCANNER_TRIGGER:
                    results.append({
                        'run': run_idx + 1, 'block': block_idx + 1, 'trial': -1,
                        'event_type': 'trigger_rest', 'timestamp': global_clock.getTime(),
                        'n': n, 'stim_type': stim_type, 'stimulus': '',
                        'is_target': -1, 'resp_key': '', 'resp_rt': time, 'correct': -1
                    })
                elif key == RESPONSE_KEY:
                    exit_rest = True
            if exit_rest:
                break
        
        # 2s fixation
        fix_clock = core.Clock()
        while fix_clock.getTime() < 2:
            fixation.draw()
            win.flip()
            keys = kb.getKeys(keyList=[SCANNER_TRIGGER, 'escape'], waitRelease=False)
            for k in keys:
                key = k.name
                time = k.rt
                if key == 'escape':
                    core.quit()
                elif key == SCANNER_TRIGGER:
                    results.append({
                        'run': run_idx + 1, 'block': block_idx + 1, 'trial': -1,
                        'event_type': 'trigger_fixation', 'timestamp': global_clock.getTime(),
                        'n': n, 'stim_type': stim_type, 'stimulus': '',
                        'is_target': -1, 'resp_key': '', 'resp_rt': time, 'correct': -1
                    })

        # run the task
        run_block(run_idx, block_idx, n, stim_type, results)
    
    # Save data
    with open(DATA_FILE, 'w', newline='') as f:
        fieldnames = ['run', 'block', 'trial', 'event_type', 'timestamp', 'n', 'stim_type', 'stimulus', 'is_target', 'resp_key', 'resp_rt', 'correct']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

# Final Screen
instr_text.text = "Experiment Complete!\n\nThank you."
instr_text.draw()
win.flip()
core.wait(5)
win.close()
core.quit()