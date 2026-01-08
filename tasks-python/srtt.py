"""Serial Reaction Time Task - PsychoPy Implementation"""
from psychopy import visual, core, event, gui
import random, csv, os

# ===== PARAMETERS =====
REPEATED_PATTERN = [0, 2, 1, 3, 2, 0, 0, 3]
N_PATTERN_REPS = 8
N_RANDOM_TRIALS = 16 # slowness on random trials at the end will show that the pattern was learned
ITI_DURATION = 0.2
DATA_FILE = './_data/srtt.csv'
# ======================

# Get subject ID
dlg = gui.Dlg(title="Serial Reaction Time Task")
dlg.addField('Subject ID:')
dlg.show()
if not dlg.OK:
    core.quit()
subject_id = dlg.data[0]

# Setup
win = visual.Window([800, 600], color='white')

# Create 4 boxes for target locations
box_positions = [(-0.3, 0), (-0.1, 0), (0.1, 0), (0.3, 0)]
boxes = [visual.Rect(win, width=0.15, height=0.15, pos=pos, lineColor='black', lineWidth=2) 
         for pos in box_positions]
highlight = visual.Rect(win, width=0.15, height=0.15, fillColor='blue', lineColor='black', lineWidth=2)

# Keys to press for each
keys_list = ['f', 'g', 'h', 'j']

# Instructions
instruction_text = """
    Serial Reaction Time Task\n\n
    Place your fingers on the F, G, H, and J keys\n
    Press the key where the blue box appears:\n
    F = left, G = middle-left, H = middle-right, J = right\n\n
    Press ESC at any time to quit\n
    Press SPACE to begin"""
instructions = visual.TextStim(win, text= instruction_text, color='black', height=0.05, wrapWidth=1.5)
instructions.draw()
win.flip()
event.waitKeys(keyList=['space'])

# Create trial sequence
# start with the pattern repeated N times
# then add some random trials at the end to show that the participant gets worse
sequence = REPEATED_PATTERN * N_PATTERN_REPS 
random_numbers = random.choices(range(0,4), k=N_RANDOM_TRIALS)
sequence += random_numbers

# run the trials
results = []
for trial, target_idx in enumerate(sequence):
    # Show boxes
    for box in boxes:
        box.draw()
    
    # Highlight target
    highlight.pos = box_positions[target_idx]
    highlight.draw()
    win.flip()
    
    # Get response
    clock = core.Clock()
    keys = event.waitKeys(keyList=keys_list + ['escape'], timeStamped=clock)
    if keys[0][0] == 'escape':
        break
    
    response_key = keys[0][0]
    rt = keys[0][1]
    response_idx = keys_list.index(response_key)
    correct = response_idx == target_idx
    
    # Determine if trial is from pattern or random
    if trial < len(REPEATED_PATTERN) * N_PATTERN_REPS:
        trial_type = 'pattern'
    else:
        trial_type = 'random'
    
    results.append({
        'subject_id': subject_id,
        'trial': trial,
        'target_position': target_idx,
        'response_position': response_idx,
        'correct': int(correct),
        'rt': rt,
        'trial_type': trial_type
    })
    
    # Brief ITI - clear highlight
    for box in boxes:
        box.draw()
    win.flip()
    core.wait(ITI_DURATION)

# Save results (append to shared file)
file_exists = os.path.isfile(DATA_FILE)
with open(DATA_FILE, 'a', newline='') as f:
    fieldnames = ['subject_id', 'trial', 'target_position', 'response_position', 'correct', 'rt', 'trial_type']
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