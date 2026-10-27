from psychopy import visual, core, event, gui
from psychopy.hardware import keyboard
import random, csv, os

# ===== PARAMETERS =====
# Total duration: 6 blocks * 1 min = 6 min
# 1-back letters, 2-back letters, 1-back faces, 2-back faces, 1-back scenes, 2-back scenes

N_BY_BLOCK = [1, 2, 1, 2, 1, 2]
STIMTYPE_BY_BLOCK = ['letters','letters','faces','faces','scenes','scenes']
TRIAL_DURATION = 1.5 # seconds; total
STIM_DURATION = 1 # seconds; stimulus on screen
N_TRIALS_PER_BLOCK = 30
N_TARGETS_PER_BLOCK = 10

RESPONSE_KEY = 'space' 
STIMULI_DIR = '_stimuli'

# Get subject information
dlg = gui.Dlg(title="N-back Task")
dlg.addField('Name:')
dlg.show()
if not dlg.OK:
    core.quit()
subject_name = dlg.data[0]

# Update data file name
DATA_FILE = f'_data/nback/{subject_name}.csv'

# Stimuli definitions
stimuli = {
    'letters': ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Y', 'Z'],
    'faces': [os.path.join(STIMULI_DIR, f'faces/{i}.jpg') for i in range(60)],
    'scenes': [os.path.join(STIMULI_DIR, f'scenes/{i}.jpg') for i in range(60)]
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
                
            keys = kb.getKeys(keyList=[RESPONSE_KEY, 'escape'], waitRelease=False)
            for k in keys:
                time = k.rt
                key = k.name
                if key == 'escape':
                    core.quit()
                elif key == RESPONSE_KEY and resp_key is None:
                    resp_key = key
                    resp_rt = time
            
            # Short sleep to prevent CPU hogging
            core.wait(0.001)

        # Save trial data
        correct = (is_target and resp_key == RESPONSE_KEY) or (not is_target and resp_key is None)
        results.append({
            'subject_name': subject_name,
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
global_clock.reset()

for block_idx, (n, stim_type) in enumerate(zip(N_BY_BLOCK, STIMTYPE_BY_BLOCK)):

    # Instruction screen - Wait for space to begin
    instr_text.text = (f"Block {block_idx + 1}/{len(N_BY_BLOCK)}\n\n"
                      f"Task: {n}-BACK\n"
                      f"Stimuli: {stim_type.capitalize()}\n\n"
                      f"Press the '{RESPONSE_KEY.upper()}' key when the stimulus matches the one {n} trials ago.\n\n"
                      f"Press {RESPONSE_KEY.upper()} to start.")
    
    kb.clearEvents()
    while True:
        instr_text.draw()
        win.flip()
        keys = kb.getKeys(keyList=[RESPONSE_KEY, 'escape'], waitRelease=False)
        if 'escape' in [k.name for k in keys]:
            core.quit()
        if RESPONSE_KEY in [k.name for k in keys]:
            break
        core.wait(0.01)

    # run the task
    run_block(0, block_idx, n, stim_type, results)

# Save data
with open(DATA_FILE, 'w', newline='') as f:
    fieldnames = ['subject_name', 'run', 'block', 'trial', 'event_type', 'timestamp', 'n', 'stim_type', 'stimulus', 'is_target', 'resp_key', 'resp_rt', 'correct']
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