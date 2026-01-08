"""N-back Task - PsychoPy Implementation"""
from psychopy import visual, core, event, gui
import random, csv, os

# ===== PARAMETERS =====
N_TRIALS_PER_BLOCK = 30
FIXATION_DURATION = 0.5
STIM_DURATION = 1
ITI_DURATION = 0.5
TARGET_PROPORTION = 0.3
DATA_FILE = './_data/nback.csv'
# ======================

# Get subject ID
dlg = gui.Dlg(title="N-back Task")
dlg.addField('Subject ID:')
dlg.addField('N (1, 2, or 3):')
dlg.show()
if not dlg.OK:
    core.quit()
subject_id = dlg.data[0]
n = int(dlg.data[1])

# Setup
win = visual.Window([800, 600], color='white')
fixation = visual.TextStim(win, text='+', color='black', height=0.1)
stim = visual.TextStim(win, text='', color='black', height=0.2)
feedback = visual.TextStim(win, text='', color='black', height=0.06)

# Stimuli
letters = ['B', 'C', 'D', 'F', 'G', 'H', 'J', 'K']

# Generate sequence with target proportion
sequence = []
for i in range(N_TRIALS_PER_BLOCK):
    # randomly assign to trials to be repetitions or not
    if i >= n and random.random() < TARGET_PROPORTION:
        # Target trial - repeat letter from n positions back
        letter = sequence[i - n]
    else:
        # Non-target - pick different letter
        if i >= n:
            letter = random.choice([l for l in letters if l != sequence[i - n]])
        else:
            letter = random.choice(letters)
    sequence.append(letter)


# Instructions
instruction_text = """
    N-back Task\n\n
    Press SPACE when the current letter matches\n
    the letter from {n} position(s) back\n\n
    Press ESC at any time to quit\n
    Press SPACE to begin"""
instructions = visual.TextStim(win, text= instruction_text, color='black', height=0.05, wrapWidth=1.5)
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])

# Run trials
results = []
for trial in range(N_TRIALS_PER_BLOCK):
    # Fixation
    fixation.draw()
    win.flip()
    core.wait(FIXATION_DURATION)
    
    # Show letter
    stim.text = sequence[trial]
    stim.draw()
    win.flip()
    
    # Get response
    clock = core.Clock()
    keys = event.waitKeys(maxWait=STIM_DURATION, keyList=['space', 'escape'], timeStamped=clock)
    
    if keys and keys[0][0] == 'escape':
        break
    
    response = keys is not None and keys[0][0] == 'space'
    is_target = trial >= n and sequence[trial] == sequence[trial - n]
    
    if response: # space bar was pressed, this is correct if trial is target trial
        correct = is_target
        rt = keys[0][1] if keys else None
    else: # space bar not pressed, this is correct if trial is non-target trial
        correct = not is_target
        rt = None
    
    results.append({
        'subject_id': subject_id,
        'n': n,
        'trial': trial,
        'stimulus': sequence[trial],
        'is_target': int(is_target),
        'response': int(response),
        'correct': int(correct),
        'rt': rt
    })
    
    # Brief inter-trial interval
    core.wait(ITI_DURATION)

# Save results (append to shared file)
file_exists = os.path.isfile(DATA_FILE)
with open(DATA_FILE, 'a', newline='') as f:
    fieldnames = ['subject_id', 'n', 'trial', 'stimulus', 'is_target', 'response', 'correct', 'rt']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    if not file_exists:
        writer.writeheader()
    writer.writerows(results)

# End
end_text = visual.TextStim(win, text='Task complete!\n\nPress SPACE to exit', color='black', height=0.08)
end_text.draw()
win.flip()
event.waitKeys(keyList=['space'])
win.close()
core.quit()